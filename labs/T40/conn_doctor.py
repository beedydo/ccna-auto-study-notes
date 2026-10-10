"""T40 reference program: diagnose app connectivity layer by layer, then measure network constraints.

Start the fake network first:  python3 labs/T40/lab_env.py
Then in another terminal:      python3 labs/T40/conn_doctor.py
Or both in one go:             bash labs/T40/run_lab.sh

Needs: requests (in the Docker lab image).
"""
import os
import socket
import time

import requests

HOST = os.environ.get("T40_HOST", "127.0.0.1")
BASE = int(os.environ.get("T40_BASE_PORT", "18040"))
APP, CLOSED, FILTERED, PROXY, TLS_APP = BASE, BASE + 1, BASE + 2, BASE + 3, BASE + 4
PROXY_USER = os.environ.get("T40_PROXY_USER", "labuser")
PROXY_PASS = os.environ.get("T40_PROXY_PASS", "labpass")
CORP_CA = os.environ.get("T40_CA", "/tmp/t40-certs/corp-ca.pem")

direct = requests.Session()
direct.trust_env = False            # ignore HTTP(S)_PROXY / REQUESTS_CA_BUNDLE from the shell: we test each path explicitly


def check_dns(name):
    """Layer 1 of the ladder: does the name resolve? (VPN split-DNS problems fail here.)"""
    try:
        addrs = sorted({ai[4][0] for ai in socket.getaddrinfo(name, None, type=socket.SOCK_STREAM)})
        print(f"  DNS  {name:<18} -> {', '.join(addrs)}")
    except socket.gaierror as err:
        print(f"  DNS  {name:<18} -> FAIL ({err.strerror}) => DNS problem, not the network path")


def check_port(port, timeout=2):
    """TCP handshake only, like `nc -zv host port`. Classifies OPEN / REFUSED / TIMEOUT."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    start = time.monotonic()
    try:
        sock.connect((HOST, port))
        verdict = "OPEN     -> SYN, SYN-ACK: something is listening"
    except ConnectionRefusedError:
        verdict = "REFUSED  -> RST came back: host reachable, port closed / service down"
    except (socket.timeout, TimeoutError):
        verdict = "TIMEOUT  -> no reply at all: firewall/ACL dropping, or no route"
    finally:
        sock.close()
    print(f"  TCP  {HOST}:{port:<6} {verdict} ({time.monotonic() - start:.1f}s)")


def diagnose(exc):
    """Map a requests exception to the likely network cause (the exam's 'symptom -> cause')."""
    if isinstance(exc, requests.exceptions.ProxyError):
        return "proxy unreachable or refused the tunnel (407 on CONNECT): check proxy URL/credentials"
    if isinstance(exc, requests.exceptions.SSLError):
        return "TLS verify failed: TLS-inspecting proxy? trust the corporate CA (verify=...)"
    if isinstance(exc, requests.exceptions.ConnectTimeout):
        return "no SYN-ACK: firewall drop, wrong route, or VPN tunnel down"
    if isinstance(exc, requests.exceptions.ReadTimeout):
        return "connected, but server too slow: raise read timeout or fix the server"
    if isinstance(exc, requests.exceptions.ConnectionError):
        return "refused or DNS failure: read the inner error"
    return "unknown"


def http(label, method, url, **kwargs):
    kwargs.setdefault("timeout", (2, 5))                  # (connect, read) seconds
    try:
        resp = direct.request(method, url, **kwargs)
        extra = f" Proxy-Authenticate: {resp.headers['Proxy-Authenticate']}" if resp.status_code == 407 else ""
        print(f"  {label:<34} -> {resp.status_code} {resp.reason}{extra}")
        return resp
    except requests.exceptions.RequestException as exc:
        print(f"  {label:<34} -> {type(exc).__name__}: {diagnose(exc)}")
        return None


def proxies(with_auth):
    cred = f"{PROXY_USER}:{PROXY_PASS}@" if with_auth else ""
    url = f"http://{cred}{HOST}:{PROXY}"
    return {"http": url, "https": url}                    # proxy URL is http:// even for https targets


def main():
    app = f"http://{HOST}:{APP}"

    print("== 1. DNS ==")
    check_dns("localhost")
    check_dns("api.corp.invalid")                          # internal name your resolver can't see

    print("\n== 2. Transport port: open vs refused vs filtered ==")
    for port in (APP, CLOSED, FILTERED):
        check_port(port)

    print("\n== 3. HTTP timeouts: connect vs read ==")
    http("GET filtered port", "GET", f"http://{HOST}:{FILTERED}/health")
    http("GET closed port", "GET", f"http://{HOST}:{CLOSED}/health")
    http("GET slow report (read timeout 1s)", "GET", f"{app}/api/v1/slow-report", timeout=(2, 1))

    print("\n== 4. Proxy: 407, then credentials ==")
    http("HTTP via proxy, no creds", "GET", f"{app}/whoami", proxies=proxies(False))
    seen = http("HTTP via proxy, with creds", "GET", f"{app}/whoami", proxies=proxies(True))
    mine = http("HTTP direct (no proxy)", "GET", f"{app}/whoami")
    if seen is not None and mine is not None:
        print(f"    server log, direct   : {mine.json()}")
        print(f"    server log, via proxy: {seen.json()}  <- source rewritten, like NAT/PAT")

    print("\n== 5. HTTPS through the proxy (CONNECT) + TLS inspection ==")
    tls = f"https://{HOST}:{TLS_APP}/health"
    http("HTTPS via proxy, no creds", "GET", tls, proxies=proxies(False))
    http("HTTPS via proxy, default CAs", "GET", tls, proxies=proxies(True))
    http("HTTPS via proxy, verify=corp-ca", "GET", tls, proxies=proxies(True), verify=CORP_CA)

    print("\n== 6. Network constraints: latency x round trips, bytes on the wire ==")
    start = time.monotonic()
    for dev_id in range(1, 21):                                         # chatty: 20 round trips
        direct.get(f"{app}/api/v1/devices/{dev_id}", timeout=(2, 5))
    chatty = time.monotonic() - start
    start = time.monotonic()
    bulk = direct.get(f"{app}/api/v1/devices", timeout=(2, 5))           # one round trip
    one = time.monotonic() - start
    print(f"  20 x GET /devices/{{id}}: {chatty:.2f}s   1 x GET /devices: {one:.2f}s  "
          f"({len(bulk.json()['response'])} devices)")
    plain = direct.get(f"{app}/api/v1/devices", headers={"Accept-Encoding": "identity"}, timeout=(2, 5))
    zipped = direct.get(f"{app}/api/v1/devices", headers={"Accept-Encoding": "gzip"},
                        timeout=(2, 5), stream=True)
    wire = len(zipped.raw.read())                                       # bytes before requests decodes them
    print(f"  body size: identity {len(plain.content)} B, gzip {wire} B "
          f"(Content-Encoding: {zipped.headers.get('Content-Encoding')})")


if __name__ == "__main__":
    main()
