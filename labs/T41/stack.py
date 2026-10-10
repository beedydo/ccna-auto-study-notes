"""T41 lab stack: DNS -> firewall -> WAF -> load balancer / reverse proxy -> app servers, all on loopback.

Every box from blueprint 4.9 is a small, real network service (Python stdlib only, Linux loopback):

  DNS server     UDP 127.0.0.1:18041     app.t41.lab -> two site VIPs, round robin, TTL, GSLB failover
  Front door     TCP 127.0.41.1:18041    site A VIP  (firewall + WAF + LB + reverse proxy in one box,
                 TCP 127.0.41.2:18041    site B VIP   like an F5 / NGINX / AWS ALB with AWS WAF attached)
  App servers    TCP 127.0.42.1-3:18041  app1, app2, app3     (pool "api",    path /api/*)
  Static server  TCP 127.0.42.11:18041   static1              (pool "static", path /static/*)

Run it on its own for the dig/curl drill:  python3 labs/T41/stack.py
walkthrough.py imports it and drives every concept step by step.
"""
import gzip
import http.client
import http.server
import ipaddress
import json
import os
import re
import socket
import ssl
import struct
import threading
import time
from urllib.parse import unquote_plus, urlsplit

PORT = int(os.environ.get("T41_PORT", "18041"))      # TCP = the VIPs and backends, UDP = the DNS server
DNS_ADDR = "127.0.0.1"
SITE_VIPS = ["127.0.41.1", "127.0.41.2"]              # site A, site B
DNS_TTL = 3                                           # seconds; real apps use 60-300 (AWS ELB: 60)


# ---------------------------------------------------------------- firewall (L3/L4)
FW_RULES = [  # (action, protocol, source, destination, destination port); first match wins
    ("deny",   "ip",  "127.0.0.66/32", "0.0.0.0/0",     "any"),  # 1 blocklisted client
    ("permit", "tcp", "0.0.0.0/0",     "127.0.41.0/24", PORT),   # 2 anyone -> VIPs, web port only
    ("permit", "tcp", "10.41.1.0/24",  "10.41.2.0/24",  8443),   # 3 web tier -> app tier
    ("permit", "tcp", "10.41.2.0/24",  "10.41.3.0/24",  5432),   # 4 app tier -> DB tier (PostgreSQL)
]                                                                # (implicit deny ip any any)


class Firewall:
    """Ordered ACL, first match wins, implicit deny. Stateful: replies to a permitted flow pass."""

    def __init__(self, rules):
        self.rules = rules
        self.state = set()            # established flows: (proto, src, sport, dst, dport)

    def check(self, proto, src, sport, dst, dport):
        if (proto, dst, dport, src, sport) in self.state:          # reverse of a known flow
            return "permit", "established (state table)"
        for n, (action, r_proto, r_src, r_dst, r_port) in enumerate(self.rules, start=1):
            if r_proto not in ("ip", proto):
                continue
            if ipaddress.ip_address(src) not in ipaddress.ip_network(r_src):
                continue
            if ipaddress.ip_address(dst) not in ipaddress.ip_network(r_dst):
                continue
            if r_port not in ("any", dport):
                continue
            if action == "permit":
                self.state.add((proto, src, sport, dst, dport))
            return action, f"rule {n}"
        return "deny", "implicit deny"


# ---------------------------------------------------------------- WAF (L7, HTTP only)
WAF_RULES = [
    ("SQL injection",        re.compile(r"'\s*(or|and)\s|union\s+select|;\s*drop\s|--", re.I)),
    ("cross-site scripting", re.compile(r"<\s*script|javascript:|onerror\s*=", re.I)),
]


def waf_check(raw_path):
    """Return the attack name if the decoded path + query matches a WAF rule, else None."""
    decoded = unquote_plus(raw_path)
    for name, pattern in WAF_RULES:
        if pattern.search(decoded):
            return name
    return None


# ---------------------------------------------------------------- backend servers
class _Quiet(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request, client_address):
        pass                                          # dropped / reset connections are expected here


def _backend_handler(name):
    class Handler(http.server.BaseHTTPRequestHandler):
        server_version = f"{name}-httpd/1.0"          # the header a reverse proxy should hide

        def version_string(self):
            return self.server_version

        def log_message(self, *args):
            pass

        def _send(self, code, body, ctype="application/json", extra=None):
            data = body.encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            for key, value in (extra or {}).items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            url = urlsplit(self.path)
            if url.path == "/health":
                return self._send(200, '{"status": "ok"}')
            if url.path == "/static/app.css":
                css = "".join(f".row-{i} {{ margin: 0; padding: 4px; color: #1d1d1f; }}\n" for i in range(40))
                return self._send(200, css, "text/css", {"Cache-Control": "max-age=60"})
            if url.path.startswith("/api/"):
                if url.path == "/api/slow":
                    time.sleep(1.5)
                return self._send(200, json.dumps({
                    "served_by": name,
                    "peer_ip": self.client_address[0],                  # who opened the TCP connection
                    "x_forwarded_for": self.headers.get("X-Forwarded-For"),  # the real client
                }))
            return self._send(404, '{"error": "not found"}')

    return Handler


class Backend:
    def __init__(self, name, host, weight=1):
        self.name, self.host, self.port, self.weight = name, host, PORT, weight
        self.up = True          # health-check verdict
        self.active = 0         # open requests right now (least connections)
        self.current = 0        # smooth weighted round robin counter
        self.server = None

    def start(self):
        self.server = _Quiet((self.host, self.port), _backend_handler(self.name))
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()


# ---------------------------------------------------------------- load balancer
class Pool:
    """A server pool (AWS: target group) with a balancing algorithm and health checks."""

    def __init__(self, name, backends, algorithm="round_robin"):
        self.name, self.backends, self.algorithm = name, backends, algorithm
        self.rr_index = 0
        self.lock = threading.Lock()

    def pick(self, sticky=None):
        with self.lock:
            healthy = [b for b in self.backends if b.up]
            if not healthy:
                return None
            for b in healthy:
                if b.name == sticky:                  # session persistence (cookie)
                    return b
            if self.algorithm == "least_conn":
                return min(healthy, key=lambda b: b.active)
            if self.algorithm == "weighted":          # smooth weighted round robin (as NGINX does it)
                total = sum(b.weight for b in healthy)
                for b in healthy:
                    b.current += b.weight
                best = max(healthy, key=lambda b: b.current)
                best.current -= total
                return best
            choice = healthy[self.rr_index % len(healthy)]   # plain round robin
            self.rr_index += 1
            return choice

    def health_check(self):
        """Active health check: GET /health on every member; 200 = UP, anything else = DOWN."""
        for b in self.backends:
            try:
                conn = http.client.HTTPConnection(b.host, b.port, timeout=0.5)
                conn.request("GET", "/health")
                b.up = conn.getresponse().status == 200
                conn.close()
            except OSError:
                b.up = False
        return " ".join(f"{b.name}={'UP' if b.up else 'DOWN'}" for b in self.backends)


# ---------------------------------------------------------------- front door (firewall + WAF + LB + reverse proxy)
class FrontDoor:
    ROUTES = [("/api/", "api"), ("/static/", "static")]       # path-based routing
    HIDE = {"server", "date", "connection", "content-length", "transfer-encoding"}

    def __init__(self, firewall, pools):
        self.firewall, self.pools = firewall, pools
        self.cache = {}                                       # path -> (expires, headers, body)
        self.servers = []

    def start(self):
        door = self

        class Handler(http.server.BaseHTTPRequestHandler):
            server_version = "t41-proxy"                      # replaces every backend's Server header
            protocol_version = "HTTP/1.1"

            def version_string(self):
                return self.server_version

            def log_message(self, *args):
                pass

            def handle(self):
                vip, src = self.server.server_address[0], self.client_address
                verdict, why = door.firewall.check("tcp", src[0], src[1], vip, PORT)
                if verdict == "deny":
                    time.sleep(2)                             # drop: send nothing, client times out
                    return
                super().handle()

            def reply(self, code, body, headers):
                self.send_response(code)
                for key, value in headers:
                    self.send_header(key, value)
                self.send_header("Via", "1.1 t41-proxy")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                attack = waf_check(self.path)
                if attack:
                    return self.reply(403, f'{{"error": "blocked by WAF: {attack}"}}'.encode(),
                                      [("Content-Type", "application/json")])
                pool = next((door.pools[p] for prefix, p in door.ROUTES if self.path.startswith(prefix)), None)
                if pool is None:
                    return self.reply(404, b'{"error": "no route"}', [("Content-Type", "application/json")])

                cached = door.cache.get(self.path)
                if cached and cached[0] > time.time():
                    headers, body = cached[1] + [("X-Cache", "HIT")], cached[2]
                else:
                    cookie = self.headers.get("Cookie", "")
                    sticky = cookie.split("T41_STICKY=")[1].split(";")[0] if "T41_STICKY=" in cookie else None
                    backend = pool.pick(sticky)
                    if backend is None:
                        return self.reply(503, b'{"error": "no healthy backend"}',
                                          [("Content-Type", "application/json")])
                    backend.active += 1
                    try:
                        conn = http.client.HTTPConnection(backend.host, backend.port, timeout=5)
                        conn.request("GET", self.path, headers={
                            "Host": self.headers.get("Host", ""),
                            "X-Forwarded-For": self.client_address[0],
                            "X-Forwarded-Proto": "https" if isinstance(self.connection, ssl.SSLSocket) else "http"})
                        resp = conn.getresponse()
                        body = resp.read()
                        conn.close()
                    except OSError:
                        backend.up = False                    # passive health check
                        return self.reply(502, b'{"error": "bad gateway"}',
                                          [("Content-Type", "application/json")])
                    finally:
                        backend.active -= 1
                    headers = [(k, v) for k, v in resp.getheaders() if k.lower() not in door.HIDE]
                    if pool.name == "api":
                        headers.append(("Set-Cookie", f"T41_STICKY={backend.name}"))
                    max_age = re.search(r"max-age=(\d+)", resp.getheader("Cache-Control", ""))
                    if max_age:
                        door.cache[self.path] = (time.time() + int(max_age.group(1)), headers, body)
                        headers = headers + [("X-Cache", "MISS")]
                if "gzip" in self.headers.get("Accept-Encoding", "") and len(body) > 200:
                    body = gzip.compress(body, mtime=0)
                    headers = headers + [("Content-Encoding", "gzip")]
                self.reply(200, body, headers)

        self.Handler = Handler                                # reused by tls_offload.py
        for vip in SITE_VIPS:
            server = _Quiet((vip, PORT), Handler)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            self.servers.append(server)


# ---------------------------------------------------------------- DNS server (authoritative, UDP)
class DnsServer:
    """Authoritative for t41.lab. Answers A queries for app.t41.lab with every healthy site VIP,
    rotating the order on each query (DNS round robin). Removing a site = GSLB failover."""

    def __init__(self):
        self.records = {"app.t41.lab": list(SITE_VIPS)}
        self.site_up = {vip: True for vip in SITE_VIPS}
        self.rotation = 0
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((DNS_ADDR, PORT))

    def start(self):
        threading.Thread(target=self._serve, daemon=True).start()

    def _serve(self):
        while True:
            data, addr = self.sock.recvfrom(512)
            try:
                self.sock.sendto(self.answer(data), addr)
            except (IndexError, struct.error):
                pass

    def answer(self, query):
        qid, flags = struct.unpack("!HH", query[:4])
        labels, i = [], 12
        while query[i]:
            labels.append(query[i + 1:i + 1 + query[i]].decode().lower())
            i += 1 + query[i]
        qtype = struct.unpack("!H", query[i + 1:i + 3])[0]
        question = query[12:i + 5]
        name = ".".join(labels)
        answers = []
        if name in self.records:
            rcode = 0                                                  # NOERROR
            if qtype == 1:                                             # A
                ips = [ip for ip in self.records[name] if self.site_up[ip]]
                if ips:
                    k = self.rotation % len(ips)
                    ips = ips[k:] + ips[:k]
                    self.rotation += 1
                answers = ips
        else:
            rcode = 3                                                  # NXDOMAIN
        header = struct.pack("!HHHHHH", qid, 0x8400 | (flags & 0x0100) | rcode, 1, len(answers), 0, 0)
        body = b"".join(struct.pack("!HHHLH", 0xC00C, 1, 1, DNS_TTL, 4) + socket.inet_aton(ip)
                        for ip in answers)
        return header + question + body


# ---------------------------------------------------------------- build everything
def build_stack():
    apps = [Backend("app1", "127.0.42.1"), Backend("app2", "127.0.42.2"), Backend("app3", "127.0.42.3")]
    static = [Backend("static1", "127.0.42.11")]
    for b in apps + static:
        b.start()
    pools = {"api": Pool("api", apps), "static": Pool("static", static)}
    door = FrontDoor(Firewall(FW_RULES), pools)
    door.start()
    dns = DnsServer()
    dns.start()
    return {"apps": apps, "pools": pools, "door": door, "dns": dns}


if __name__ == "__main__":
    stack = build_stack()
    print(f"DNS on udp/{DNS_ADDR}:{PORT}; VIPs {', '.join(SITE_VIPS)} on tcp/{PORT}; Ctrl-C to stop", flush=True)
    try:
        while True:                                       # active health checks every 2 s
            for pool in stack["pools"].values():
                pool.health_check()
            time.sleep(2)
    except KeyboardInterrupt:
        pass
