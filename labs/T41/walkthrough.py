"""T41 reference program: one app request's journey, box by box.

    client -> DNS -> firewall -> WAF -> load balancer / reverse proxy -> app servers

Run:  python3 labs/T41/walkthrough.py
It starts labs/T41/stack.py in the same process (Python stdlib only, Linux loopback addresses).
"""
import http.client
import json
import socket
import struct
import threading
import time

import stack

CLIENT_IP = "127.0.0.10"      # our laptop
BLOCKED_IP = "127.0.0.66"     # on the firewall blocklist (rule 1)


def dns_query(name, qtype=1):
    """Send one DNS query (type A by default) over UDP. Return (rcode, [IPs], TTL)."""
    qname = b"".join(bytes([len(label)]) + label.encode() for label in name.split(".")) + b"\0"
    query = struct.pack("!HHHHHH", 0x4141, 0x0100, 1, 0, 0, 0) + qname + struct.pack("!HH", qtype, 1)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1)
    sock.sendto(query, (stack.DNS_ADDR, stack.PORT))
    reply = sock.recv(512)
    sock.close()
    rcode = {0: "NOERROR", 3: "NXDOMAIN"}[reply[3] & 0x0F]
    count = struct.unpack("!H", reply[6:8])[0]
    pos, ips, ttl = 12 + len(qname) + 4, [], None
    for _ in range(count):
        _, _, _, ttl, rdlen = struct.unpack("!HHHLH", reply[pos:pos + 12])
        ips.append(socket.inet_ntoa(reply[pos + 12:pos + 12 + rdlen]))
        pos += 12 + rdlen
    return rcode, ips, ttl


class CachingResolver:
    """Client-side cache (like the OS or browser): reuse an answer until its TTL runs out."""

    def __init__(self):
        self.cache = {}

    def resolve(self, name):
        hit = self.cache.get(name)
        if hit and hit[0] > time.time():
            return hit[1], f"from cache, {hit[0] - time.time():.0f} s of TTL left"
        _, ips, ttl = dns_query(name)
        self.cache[name] = (time.time() + ttl, ips)
        return ips, f"from DNS server, TTL {ttl}"


def get(vip, path, headers=None, source=CLIENT_IP, timeout=1):
    """HTTP GET to a VIP from a chosen source IP. Return (response, body)."""
    conn = http.client.HTTPConnection(vip, stack.PORT, timeout=timeout, source_address=(source, 0))
    conn.request("GET", path, headers={"Host": "app.t41.lab", **(headers or {})})
    resp = conn.getresponse()
    body = resp.read()
    conn.close()
    return resp, body


def served_by(vip, path="/api/hello", headers=None):
    resp, body = get(vip, path, headers, timeout=3)
    return json.loads(body)["served_by"] if resp.status == 200 else f"{resp.status} {resp.reason}"


def main():
    s = stack.build_stack()
    api, apps, fw = s["pools"]["api"], s["apps"], s["door"].firewall

    print("== 1. DNS: name -> VIP (round robin, GSLB failover, TTL) ==")
    for _ in range(2):
        print("query app.t41.lab A   ->", *dns_query("app.t41.lab"))
    print("query nope.t41.lab A  ->", *dns_query("nope.t41.lab"))
    resolver = CachingResolver()
    print("client resolves       ->", *resolver.resolve("app.t41.lab"))
    s["dns"].site_up["127.0.41.2"] = False
    print("GSLB: site B 127.0.41.2 fails its health check, DNS stops handing it out")
    print("DNS server now says   ->", *dns_query("app.t41.lab"))
    print("client resolves       ->", *resolver.resolve("app.t41.lab"), " <- stale: still lists site B")
    time.sleep(stack.DNS_TTL)
    print(f"after {stack.DNS_TTL} s TTL expiry  ->", *resolver.resolve("app.t41.lab"))
    s["dns"].site_up["127.0.41.2"] = True
    vip = resolver.resolve("app.t41.lab")[0][0]
    print("VIP to use:", vip)

    print("\n== 2. Firewall: L3/L4 rules, first match wins, implicit deny, stateful ==")
    packets = [
        ("internet -> VIP web port",      "203.0.113.5", 50000, "127.0.41.1", stack.PORT),
        ("internet -> VIP SSH",           "203.0.113.5", 50001, "127.0.41.1", 22),
        ("web tier -> app tier",          "10.41.1.10",  40000, "10.41.2.20", 8443),
        ("app tier -> DB tier",           "10.41.2.20",  40001, "10.41.3.30", 5432),
        ("DB reply -> app (same flow)",   "10.41.3.30",  5432,  "10.41.2.20", 40001),
        ("DB opens new conn -> app",      "10.41.3.30",  41000, "10.41.2.20", 8443),
        ("web tier -> DB (skips a tier)", "10.41.1.10",  40002, "10.41.3.30", 5432),
    ]
    for label, src, sport, dst, dport in packets:
        verdict, why = fw.check("tcp", src, sport, dst, dport)
        print(f"{label:31} tcp {src}:{sport} -> {dst}:{dport:<5}  {verdict.upper():6} ({why})")
    for source in (BLOCKED_IP, CLIENT_IP):
        try:
            resp, _ = get(vip, "/api/hello", source=source)
            print(f"real GET from {source:21} -> {resp.status} {resp.reason}")
        except OSError as err:
            print(f"real GET from {source:21} -> {type(err).__name__}: no reply, the packet was dropped")

    print("\n== 3. WAF: L7 inspection of the HTTP request ==")
    for path in ["/api/search?q=router",
                 "/api/search?q=%27%20OR%201%3D1--",
                 "/api/search?q=%3Cscript%3Ealert(1)%3C/script%3E"]:
        resp, body = get(vip, path)
        print(f"GET {path:48} -> {resp.status} {body.decode() if resp.status != 200 else resp.reason}")

    print("\n== 4. Load balancer: one VIP, many servers ==")
    api.rr_index = 0
    print("round robin       :", " ".join(served_by(vip) for _ in range(6)))
    api.algorithm, apps[0].weight = "weighted", 2
    picks = [served_by(vip) for _ in range(8)]
    print("weighted 2:1:1    :", " ".join(picks), " counts", {a.name: picks.count(a.name) for a in apps})
    api.algorithm, apps[0].weight = "least_conn", 1
    slow = []
    threads = [threading.Thread(target=lambda: slow.append(served_by(vip, "/api/slow"))) for _ in range(2)]
    for t in threads:
        t.start()
        time.sleep(0.2)
    print("least connections : 2 slow requests in flight, then fast ones go to",
          served_by(vip), served_by(vip))
    for t in threads:
        t.join()
    print("                    the slow ones were served by", " ".join(slow))

    print("\n== 5. Health checks: failed servers leave the pool ==")
    api.algorithm, api.rr_index = "round_robin", 0
    print("health check      :", api.health_check())
    apps[1].stop()
    print("app2 crashes")
    print("health check      :", api.health_check())
    print("round robin       :", " ".join(served_by(vip) for _ in range(4)))
    apps[0].stop()
    apps[2].stop()
    print("app1 and app3 crash too")
    print("health check      :", api.health_check())
    print("GET /api/hello    :", served_by(vip))
    for app in apps:
        app.start()
    print("all three restarted")
    print("health check      :", api.health_check())

    print("\n== 6. Session persistence (sticky cookie) ==")
    api.rr_index = 0
    resp, body = get(vip, "/api/hello")
    cookie = resp.getheader("Set-Cookie")
    print(f"first request     : {json.loads(body)['served_by']}, LB sets Set-Cookie: {cookie}")
    print("with the cookie   :", " ".join(served_by(vip, headers={"Cookie": cookie}) for _ in range(3)))
    apps[0].stop()
    print("app1 crashes; health check:", api.health_check())
    print("with the cookie   :", served_by(vip, headers={"Cookie": cookie}), " <- moved: app1's session is gone")
    apps[0].start()
    api.health_check()

    print("\n== 7. Reverse proxy: hide backends, path routing, cache, compression ==")
    conn = http.client.HTTPConnection("127.0.42.1", stack.PORT, timeout=1, source_address=(CLIENT_IP, 0))
    conn.request("GET", "/api/hello")
    direct = conn.getresponse()
    print(f"direct to app1    : Server: {direct.getheader('Server')}  body {direct.read().decode()}")
    resp, body = get(vip, "/api/hello")
    print(f"through the proxy : Server: {resp.getheader('Server')}  Via: {resp.getheader('Via')}")
    print(f"                    body {body.decode()}")
    for path in ["/static/app.css", "/static/app.css", "/admin"]:
        resp, body = get(vip, path)
        print(f"GET {path:16}  -> {resp.status} {resp.reason:10} X-Cache: {resp.getheader('X-Cache')}"
              f"  {len(body)} bytes")
    resp, body = get(vip, "/static/app.css", headers={"Accept-Encoding": "gzip"})
    print(f"GET /static/app.css + Accept-Encoding: gzip -> Content-Encoding: {resp.getheader('Content-Encoding')}"
          f"  {len(body)} bytes")


if __name__ == "__main__":
    main()
