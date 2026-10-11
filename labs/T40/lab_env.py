"""T40 lab environment: fake "network path" services on 127.0.0.1 for diagnosing app connectivity.

Ports (base = T40_BASE_PORT, default 18140):
  base+0  APP       HTTP JSON API (adds T40_DELAY_MS of fake WAN latency per request)
  base+1  CLOSED    nothing listens -> the OS answers SYN with RST -> "connection refused"
  base+2  FILTERED  accept queue is kept full, so the kernel silently drops new SYNs -> "timed out"
                    (same symptom as a firewall/ACL that drops)
  base+3  PROXY     corporate forward proxy: needs Proxy-Authorization (Basic) or answers 407;
                    forwards plain HTTP and tunnels HTTPS with CONNECT
  base+4  TLS-APP   HTTPS API whose certificate is signed by "Corp TLS Inspection CA"
                    (what you see when a proxy re-signs traffic) -> verify fails unless you trust that CA

Python stdlib + the openssl CLI only.  Run:  python3 labs/T40/lab_env.py   (Ctrl+C to stop)
"""
import base64
import gzip
import json
import os
import select
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = int(os.environ.get("T40_BASE_PORT", "18140"))
APP, CLOSED, FILTERED, PROXY, TLS_APP = BASE, BASE + 1, BASE + 2, BASE + 3, BASE + 4
DELAY = int(os.environ.get("T40_DELAY_MS", "40")) / 1000          # fake one-way-ish WAN delay per request
PROXY_USER = os.environ.get("T40_PROXY_USER", "labuser")
PROXY_PASS = os.environ.get("T40_PROXY_PASS", "labpass")
PROXY_SRC = os.environ.get("T40_PROXY_SRC", "127.0.0.2")         # source IP the proxy uses upstream
CERT_DIR = os.environ.get("T40_CERT_DIR", os.path.join(tempfile.gettempdir(), "t40-certs"))

DEVICES = [{"id": i, "hostname": f"edge{i}", "mgmt_ip": f"10.10.20.{100 + i}",
            "role": "edge", "os": "iosxe", "serial": f"FDO2{i:04d}X1Y"} for i in range(1, 21)]


class AppHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    disable_nagle_algorithm = True                      # so timings show only the fake delay

    def log_message(self, *args):                       # keep the console quiet
        pass

    def send_json(self, status, obj):
        body = json.dumps(obj).encode()
        headers = {"Content-Type": "application/json"}
        if "gzip" in self.headers.get("Accept-Encoding", ""):
            body = gzip.compress(body)
            headers["Content-Encoding"] = "gzip"
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        time.sleep(DELAY)                                # every request pays the round-trip cost
        path = urllib.parse.urlsplit(self.path).path
        if path == "/health":
            self.send_json(200, {"status": "ok"})
        elif path == "/whoami":                          # what the server (and its logs) see as the client
            self.send_json(200, {"seen_client": f"{self.client_address[0]}:{self.client_address[1]}",
                                 "x_forwarded_for": self.headers.get("X-Forwarded-For")})
        elif path == "/api/v1/devices":                  # bulk: one call returns everything
            self.send_json(200, {"response": DEVICES, "total": len(DEVICES)})
        elif path.startswith("/api/v1/devices/"):        # chatty: one call per device
            dev_id = int(path.rsplit("/", 1)[1])
            match = [d for d in DEVICES if d["id"] == dev_id]
            self.send_json(200 if match else 404, match[0] if match else {"error": "not found"})
        elif path == "/api/v1/slow-report":              # server takes 3 s: read timeout demo
            time.sleep(3)
            self.send_json(200, {"report": "done"})
        else:
            self.send_json(404, {"error": "not found"})


def pipe(a, b):
    """Copy bytes both ways until one side closes (the CONNECT tunnel)."""
    socks = [a, b]
    while True:
        readable, _, _ = select.select(socks, [], [], 10)
        if not readable:
            return
        for s in readable:
            data = s.recv(65536)
            if not data:
                return
            (b if s is a else a).sendall(data)


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def authorised(self):
        expected = "Basic " + base64.b64encode(f"{PROXY_USER}:{PROXY_PASS}".encode()).decode()
        if self.headers.get("Proxy-Authorization") == expected:
            return True
        body = b'{"error": "proxy authentication required"}'
        self.send_response(407, "Proxy Authentication Required")
        self.send_header("Proxy-Authenticate", 'Basic realm="corp-proxy"')
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        return False

    def do_CONNECT(self):                                # HTTPS through a proxy = CONNECT host:port tunnel
        if not self.authorised():
            return
        host, port = self.path.rsplit(":", 1)
        upstream = socket.create_connection((host, int(port)), timeout=5)
        self.send_response(200, "Connection established")
        self.end_headers()
        pipe(self.connection, upstream)
        upstream.close()
        self.close_connection = True

    def do_GET(self):                                    # plain HTTP through a proxy = absolute URI
        if not self.authorised():
            return
        target = urllib.parse.urlsplit(self.path)
        upstream = socket.create_connection((target.hostname, target.port or 80), timeout=10,
                                            source_address=(PROXY_SRC, 0))   # proxy's own address, like NAT
        path = target.path + (f"?{target.query}" if target.query else "")
        lines = [f"GET {path} HTTP/1.1", f"Host: {target.netloc}", "Connection: close",
                 f"X-Forwarded-For: {self.client_address[0]}"]
        for name in ("Accept", "Accept-Encoding", "User-Agent"):
            if self.headers.get(name):
                lines.append(f"{name}: {self.headers[name]}")
        upstream.sendall(("\r\n".join(lines) + "\r\n\r\n").encode())
        reply = b""
        while chunk := upstream.recv(65536):
            reply += chunk
        upstream.close()
        self.connection.sendall(reply)
        self.close_connection = True


def make_certs():
    """Create a private 'inspection' CA and a server cert for localhost/127.0.0.1 signed by it."""
    os.makedirs(CERT_DIR, exist_ok=True)
    ca_key, ca_crt = os.path.join(CERT_DIR, "corp-ca.key"), os.path.join(CERT_DIR, "corp-ca.pem")
    srv_key, srv_csr = os.path.join(CERT_DIR, "server.key"), os.path.join(CERT_DIR, "server.csr")
    srv_crt, ext = os.path.join(CERT_DIR, "server.pem"), os.path.join(CERT_DIR, "san.ext")
    if os.path.exists(srv_crt):
        return srv_crt, srv_key
    run = lambda *cmd: subprocess.run(cmd, check=True, capture_output=True)
    run("openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "30", "-keyout", ca_key,
        "-out", ca_crt, "-subj", "/O=Corp/CN=Corp TLS Inspection CA")
    run("openssl", "req", "-newkey", "rsa:2048", "-nodes", "-keyout", srv_key, "-out", srv_csr,
        "-subj", "/CN=localhost")
    with open(ext, "w") as f:
        f.write("subjectAltName=DNS:localhost,IP:127.0.0.1\n")
    run("openssl", "x509", "-req", "-in", srv_csr, "-CA", ca_crt, "-CAkey", ca_key, "-CAcreateserial",
        "-days", "30", "-out", srv_crt, "-extfile", ext)
    return srv_crt, srv_key


def serve(server):
    threading.Thread(target=server.serve_forever, daemon=True).start()


def main():
    serve(ThreadingHTTPServer(("127.0.0.1", APP), AppHandler))

    filtered = socket.socket()                           # listen(0) + one parked client = full queue
    filtered.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    filtered.bind(("127.0.0.1", FILTERED))
    filtered.listen(0)
    parked = socket.create_connection(("127.0.0.1", FILTERED))   # never accepted

    serve(ThreadingHTTPServer(("127.0.0.1", PROXY), ProxyHandler))

    try:
        crt, key = make_certs()
        tls = ThreadingHTTPServer(("127.0.0.1", TLS_APP), AppHandler)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(crt, key)
        tls.socket = ctx.wrap_socket(tls.socket, server_side=True)
        serve(tls)
    except (OSError, subprocess.CalledProcessError) as err:
        print(f"TLS-APP disabled (openssl missing?): {err}", file=sys.stderr)

    print(f"T40 lab up: APP {APP} | CLOSED {CLOSED} | FILTERED {FILTERED} | PROXY {PROXY} | "
          f"TLS-APP {TLS_APP} | CA {os.path.join(CERT_DIR, 'corp-ca.pem')}", flush=True)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        parked.close()


if __name__ == "__main__":
    main()
