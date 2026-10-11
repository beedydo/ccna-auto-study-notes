---
id: T40
title: "App connectivity + network constraints"
owner: Bob
blueprint: "6.8, 6.9"
primary_domain: D6
cbt_coverage: "Partial"
status: drafted   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-19
teach_back: 2026-10-20
cross_study: 2026-10-23
---

# T40 · App connectivity + network constraints

> Owner: **Bob** · Blueprint: **6.8, 6.9** · CBT coverage: **Partial** · Learn by 2026-10-19 · Teach-back 2026-10-20

![T40 at a glance: where an app call breaks on the path, the diagnostic ladder, constraints and the symptom-to-fix table](../assets/T40/00-overview.png)

*Read the top panel left to right as the path an API call takes (App → VPN → proxy → firewall → NAT → server), one failure point per box. The middle strip is the diagnostic ladder in order. Bottom: constraints (6.9) and the exam's symptom → cause → fix table. Numbered items are steps or lab examples; red boxes are exam traps.*

## TL;DR (teach-back card)

- **Read the failure mode, not just "it failed".** Instant `Connection refused` = RST = host is reachable but nothing listens. Hang then `timed out` = silent drop (firewall/ACL, no route, missing NAT). `407` = the **proxy** wants credentials. `CERTIFICATE_VERIFY_FAILED` only on the corp network = TLS inspection, so trust the corp CA.
- **Walk the ladder bottom-up:** DNS (`nslookup`/`dig`) → reachability (`ping`) → path (`traceroute`) → TCP port (`nc -zv` / `telnet`) → HTTP (`curl -v`) → server listener (`ss -ltn`). Stop at the first rung that fails.
- **6.9 = latency × round trips.** A chatty script with 20 calls at 40 ms RTT took 0.92 s in the lab; one bulk call took 0.05 s. Fix latency with fewer round trips (batch, cache), bandwidth with compression (gzip 2349 B → 337 B), and jitter/loss for voice/video with QoS.
- **Trap:** VPN "connects but large transfers hang" is MTU/PMTUD, not a dead tunnel. Fix it by clamping the MSS (`ip tcp adjust-mss 1360`) or lowering the tunnel MTU. Also, `verify=False` is never the exam's right answer for TLS inspection.

## Concepts

Every section below explains one part of the same lab, so read it once first.

- `labs/T40/lab_env.py` builds a fake network path on `127.0.0.1` with the Python standard library and the `openssl` CLI:

  | Port | Role | What it simulates |
  |---|---|---|
  | `18140` | APP | HTTP JSON API that adds `T40_DELAY_MS` (default 40 ms) to every request |
  | `18141` | CLOSED | nothing listens, so the kernel answers SYN with RST |
  | `18142` | FILTERED | accept queue kept full, so the kernel **silently drops** new SYNs (same symptom as a firewall drop) |
  | `18143` | PROXY | corporate forward proxy: `407` without `Proxy-Authorization`, forwards HTTP, tunnels HTTPS with `CONNECT`, and connects upstream **from `127.0.0.2`** |
  | `18144` | TLS-APP | HTTPS API whose cert is issued by `Corp TLS Inspection CA` (what a TLS-inspecting proxy presents) |

- `labs/T40/conn_doctor.py` (below) is the **reference program**. It's a diagnostic client that walks the ladder (DNS → TCP → HTTP → proxy → TLS), then measures two constraints.
- To run both: `bash labs/T40/run_lab.sh`. It starts the fake network, waits for it, runs the client, then stops everything.
- Ports are `18140 + n` and can be moved with `T40_BASE_PORT`. Proxy credentials come from `T40_PROXY_USER` / `T40_PROXY_PASS` (lab defaults `labuser` / `labpass`).

**`labs/T40/conn_doctor.py`**

```python
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
BASE = int(os.environ.get("T40_BASE_PORT", "18140"))
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
```

**Real output** (`bash labs/T40/run_lab.sh`, Linux, Python 3.10, requests 2.34.2):

```text
== 1. DNS ==
  DNS  localhost          -> 127.0.0.1
  DNS  api.corp.invalid   -> FAIL (Name or service not known) => DNS problem, not the network path

== 2. Transport port: open vs refused vs filtered ==
  TCP  127.0.0.1:18140  OPEN     -> SYN, SYN-ACK: something is listening (0.0s)
  TCP  127.0.0.1:18141  REFUSED  -> RST came back: host reachable, port closed / service down (0.0s)
  TCP  127.0.0.1:18142  TIMEOUT  -> no reply at all: firewall/ACL dropping, or no route (2.0s)

== 3. HTTP timeouts: connect vs read ==
  GET filtered port                  -> ConnectTimeout: no SYN-ACK: firewall drop, wrong route, or VPN tunnel down
  GET closed port                    -> ConnectionError: refused or DNS failure: read the inner error
  GET slow report (read timeout 1s)  -> ReadTimeout: connected, but server too slow: raise read timeout or fix the server

== 4. Proxy: 407, then credentials ==
  HTTP via proxy, no creds           -> 407 Proxy Authentication Required Proxy-Authenticate: Basic realm="corp-proxy"
  HTTP via proxy, with creds         -> 200 OK
  HTTP direct (no proxy)             -> 200 OK
    server log, direct   : {'seen_client': '127.0.0.1:49704', 'x_forwarded_for': None}
    server log, via proxy: {'seen_client': '127.0.0.2:56715', 'x_forwarded_for': '127.0.0.1'}  <- source rewritten, like NAT/PAT

== 5. HTTPS through the proxy (CONNECT) + TLS inspection ==
  HTTPS via proxy, no creds          -> ProxyError: proxy unreachable or refused the tunnel (407 on CONNECT): check proxy URL/credentials
  HTTPS via proxy, default CAs       -> SSLError: TLS verify failed: TLS-inspecting proxy? trust the corporate CA (verify=...)
  HTTPS via proxy, verify=corp-ca    -> 200 OK

== 6. Network constraints: latency x round trips, bytes on the wire ==
  20 x GET /devices/{id}: 0.92s   1 x GET /devices: 0.05s  (20 devices)
  body size: identity 2349 B, gzip 337 B (Content-Encoding: gzip)
```

### T40.01 · NAT issues

**Must cover:**

- [x] Private address not reachable from outside without static NAT/port forwarding
- [x] Return traffic and logging show translated addresses

**Notes:**

- **Inbound.** RFC 1918 addresses (`10/8`, `172.16/12`, `192.168/16`) aren't routed on the internet. An outside client can only reach `10.1.1.10:443` if the edge has a **static NAT** (1:1) or **port forward** (static PAT, `public:443 → private:443`) rule.
  - No rule: the SYN to the public IP hits the edge and is dropped. The client sees a **timeout**, not a refusal.
  - Classic symptom: "works from inside the LAN, fails from the internet" (or from a cloud webhook sender, see [T43](../bee/T43-webhooks.md)).
- **Outbound / logs.** With source NAT/PAT (and with proxies), the server sees the **translated** source, not the real client.
  - Lab: `server log, direct` shows `127.0.0.1:…`; `server log, via proxy` shows `127.0.0.2:…` plus `x_forwarded_for: '127.0.0.1'`. The proxy's own address replaced the client's, exactly as PAT does.
  - Consequences: allow-lists must permit the **NAT/public** IP. Per-client rate limits treat every user behind one PAT address as **one** client. Logs need `X-Forwarded-For` (HTTP proxies/LBs only; plain NAT adds no header) to recover the real IP.
  - Return traffic must come back through the **same** NAT device, which holds the translation state. Asymmetric routing around it breaks the session.
- NAT itself (inside local/global, PAT) is 6.6 theory, covered in [T37](T37-transport-ports-ip-services.md). Here the exam asks you to **diagnose**.

![Inbound static NAT / port forward decision](../assets/T40/01-nat-inbound.png)

*No inbound rule = dropped = timeout. With a rule, the destination is rewritten to the private IP. The server log shows whatever source address survived the NAT.*

### T40.02 · Port blocking

**Must cover:**

- [x] Firewall/ACL blocking: timeout (dropped) vs connection refused (closed port)
- [x] Test with nc -zv host port, curl -v, telnet host port

**Notes:**

- The blueprint wording is "Transport Port blocked". The question to answer is whether the TCP handshake completes. `check_port()` in the program classifies the three outcomes:

  | Outcome | On the wire | `nc -zv` | `curl` | `requests` | Meaning |
  |---|---|---|---|---|---|
  | **Open** | SYN → SYN-ACK | `succeeded!` | continues to HTTP | response | something listens |
  | **Refused** | SYN → **RST** | `Connection refused` | `curl: (7)` | `ConnectionError` | host reachable, port closed / service down / bound to another IP |
  | **Timeout** | SYN → nothing | `timed out` | `curl: (28)` | `ConnectTimeout` | firewall/ACL **drop**, no route, missing NAT, host down |

- **Reject vs drop.** A firewall can also *reject*: it sends a RST or an ICMP admin-prohibited back. That fails fast and can look like "refused". Drop (silence) is the common default on internet-facing firewalls.
- **Tools** (full commands in [Examples](#2-cli-drill-labst40cli_drillsh)):
  - `nc -zv -w 2 10.1.1.10 443`: `-z` = handshake only, send no data; `-v` = verbose; `-w 2` = 2 s timeout.
  - `telnet 10.1.1.10 443`: `Connected to …` = open. Hangs on `Trying…` = dropped. `Connection refused` = closed.
  - `curl -v https://10.1.1.10/`: the `*` lines show `Trying…`, `Connected to…`, then the TLS handshake and the `>` / `<` HTTP lines. **Where the output stops tells you the layer.**
- Ports to know (6.7, [T37](T37-transport-ports-ip-services.md)): SSH 22, Telnet 23, HTTP 80, HTTPS 443, NETCONF **830**, RESTCONF 443. A NETCONF script that times out on 830 while SSH 22 works = ACL allows 22, not 830.

![Refused vs timeout on the wire](../assets/T40/02-refused-vs-timeout.png)

*Refused = an RST came back quickly. Timeout = the SYN went into a black hole and the client retransmitted until it gave up.*

### T40.03 · Proxy issues

**Must cover:**

- [x] Corporate proxy required for outbound HTTP(S): set HTTP_PROXY/HTTPS_PROXY or requests proxies={}
- [x] Proxy auth failures (407), TLS inspection breaking cert checks

**Notes:**

- **Symptom of a missing proxy:** the corporate network blocks direct outbound 80/443, so a script that ignores the proxy **times out** connecting to `api.meraki.com` while the browser (which has the proxy configured) works.
- **Three ways to set it:**
  - `requests` per call: `proxies={"http": "http://proxy:3128", "https": "http://proxy:3128"}`. See `proxies()` in the program.
    - The dict **key** is the scheme of the **target** URL. The **value** is the proxy URL, usually `http://` even for HTTPS targets.
  - Environment variables, read by `requests` (when `trust_env=True`, the default) and by curl: `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`, `ALL_PROXY`.
    - curl only honours **lowercase** `http_proxy` (a CGI security rule); the others work in either case.
  - curl: `--proxy http://proxy:3128` (`-x`), `--proxy-user user:pass` (`-U`), `--noproxy '*'`.
- **`NO_PROXY`** = a comma-separated list of hosts or domains that bypass the proxy, e.g. `NO_PROXY=127.0.0.1,.corp.local,10.0.0.0/8`. Internal controllers (Catalyst Center, vManage) usually go **direct**. Sending them to the internet proxy gives timeouts or `403`s from the proxy.
- **407 Proxy Authentication Required** (RFC 9110 §15.5.8): the **proxy**, not the server, wants credentials. It sends `Proxy-Authenticate`, and the client answers with the `Proxy-Authorization` header.
  - Fix: `http://user:pass@proxy:3128` in the proxy URL, or `curl --proxy-user`.
  - Plain HTTP: `requests` returns a response with `status_code == 407` (section 4 of the output).
  - HTTPS: the 407 arrives on the `CONNECT`, so `requests` raises **`ProxyError: … Tunnel connection failed: 407`** and there's no response object (section 5).
- **HTTPS through a proxy = `CONNECT host:443`.** The proxy opens a TCP tunnel and answers `200 Connection established`, then TLS runs through the tunnel.
- **TLS inspection** (SSL decryption): the proxy terminates TLS and re-signs the site's cert with a **corporate CA**. Browsers trust that CA (pushed by IT); your Python venv / Docker container uses `certifi` and does **not**.
  - Symptom: `SSLError … CERTIFICATE_VERIFY_FAILED … unable to get local issuer certificate` (curl: `(60) SSL certificate problem`), **only** on the corporate network.
  - Right fix: trust the CA. Use `verify="/path/corp-ca.pem"`, `REQUESTS_CA_BUNDLE=/path/corp-ca.pem`, or `curl --cacert`. Wrong fix: `verify=False` / `curl -k`, which disables checking for every server.
- **`trust_env`.** The program sets `direct.trust_env = False` so a shell `HTTPS_PROXY` can't silently reroute its "direct" tests. That's also a diagnostic: if a script works with `trust_env=False` and fails without it, an env proxy is the cause.

![Proxy 407, CONNECT and TLS inspection](../assets/T40/03-proxy-flow.png)

*The 407 and the re-signed certificate both come from the proxy. The API server is fine the whole time.*

![Animated: HTTPS through a corporate proxy, one call per frame](../assets/T40/09-proxy-journey.gif)

*Steps: CONNECT without credentials → proxy 407 → ProxyError in the app → CONNECT with Proxy-Authorization → 200 Connection established → cert issued by Corp TLS Inspection CA → SSLError → trust corp-ca.pem → GET /health 200. It fixes the misconception that "407 / CERTIFICATE_VERIFY_FAILED means the API server is broken".*

### T40.04 · VPN issues

**Must cover:**

- [x] Split vs full tunnel routes; DNS resolution through the tunnel; MTU/fragmentation; overlapping subnets

**Notes:**

- **Split vs full tunnel**

  | | Split tunnel | Full tunnel |
  |---|---|---|
  | Routes in tunnel | only corp prefixes (e.g. `10.0.0.0/8`) | `0.0.0.0/0` (everything) |
  | Internet traffic | direct via home ISP | via corp: proxy + firewall rules apply |
  | Typical break | corp prefix **missing** from the split list → traffic to it goes to the ISP → timeout | public SaaS/API now hits the corp proxy → `407` / TLS inspection / blocked |
  | Check | `ip route get 10.1.1.10` (Linux), `route print` (Windows): which interface? | same, plus test with and without proxy |

- **DNS through the tunnel (split DNS).** Internal names (`api.corp.local`) exist only on the corp DNS server that the VPN pushes.
  - Symptom: `nslookup api.corp.local` → NXDOMAIN / `Name or service not known` (section 1: `api.corp.invalid`), while `ping 10.1.1.10` by IP works.
  - Cause: the laptop is still asking the home/ISP resolver. Fix the VPN DNS settings, or query the corp server directly: `nslookup api.corp.local 10.0.0.53`.
- **MTU / fragmentation.** IPsec/GRE headers add tens of bytes, so a 1500-byte packet no longer fits. TCP sets DF (Don't Fragment), so the router drops it and should return ICMP "fragmentation needed".
  - If that ICMP is filtered: **PMTUD black hole**. Small packets work (ping, SSH login, TLS handshake), but large responses or file transfers **hang**.
  - Test: `ping -M do -s 1472 host` (Linux; 1472 + 8 ICMP + 20 IP = 1500). Windows: `ping -f -l 1472 host`. Lower `-s` until it passes; that gives you the path MTU.
  - Fix on the tunnel interface: `ip mtu 1400` and `ip tcp adjust-mss 1360` (Cisco's common example values; size them for your real overhead).
- **Overlapping subnets.** The home LAN is `192.168.1.0/24` and so is the corp subnet behind the VPN. Routing uses longest prefix match. With an equal `/24`, the laptop's directly connected route normally wins, so traffic to "corp" `192.168.1.10` stays on the home LAN.
  - Fixes: renumber, push more-specific routes, or NAT the overlapping range on the VPN head-end.

![Split vs full tunnel, split DNS, overlap](../assets/T40/04-vpn-tunnel.png)

*Split tunnel sends only corp prefixes into the tunnel, so internal names also need corp DNS. Full tunnel sends everything, so corp proxy rules now apply. Overlap means the local route wins.*

![MTU and PMTUD black hole](../assets/T40/05-mtu-blackhole.png)

*Small packets get through and large ones vanish when the ICMP "fragmentation needed" can't reach the sender. Clamp the MSS.*

### T40.05 · Diagnostic tools

**Must cover:**

- [x] ping, traceroute, nslookup/dig, curl -v, ss/netstat

**Notes:**

- Use them in ladder order and stop at the first failure:

  | Tool | Layer / question | Read the output |
  |---|---|---|
  | `nslookup name` · `dig +short name` | DNS: does the name resolve, to what? | `NXDOMAIN` / no answer = DNS. Wrong IP = stale record / split DNS |
  | `ping -c 3 host` | L3 reachability + RTT + loss | loss % and `rtt min/avg/max/mdev` (mdev ≈ jitter). No reply ≠ down: ICMP may be blocked |
  | `traceroute host` (Windows `tracert`) | L3 path: where does it stop? | last responding hop = where it dies. `* * *` = hop doesn't answer / filtered |
  | `nc -zv host port` · `telnet host port` | L4: does the TCP handshake complete? | `succeeded` / `refused` / `timed out` (T40.02) |
  | `curl -v URL` | L7: TLS + HTTP exchange | `*` = connection/TLS info, `>` = sent, `<` = received. Add `-x` for a proxy, `--cacert` for a CA |
  | `ss -tlnp` · `netstat -an` | on the **server**: what is listening, on which IP? | `127.0.0.1:8080` = local only. `0.0.0.0:8080` = all interfaces. Missing = service down |

- `ss` flags: `-t` TCP, `-u` UDP, `-l` listening, `-n` numeric, `-p` process (needs root for other users' processes).
- `dig +short` prints only the answer; `nslookup` is the cross-platform one (Windows too).
- Lab rule of thumb: `check_dns()` = rung 1, `check_port()` = rung 4 and `http()` = rung 5. The drill in [Examples §2](#2-cli-drill-labst40cli_drillsh) runs the CLI versions against the same ports.

![Diagnostic ladder](../assets/T40/06-diag-ladder.png)

*Bottom-up. A port timeout sends you to firewall/NAT/routes; a refusal sends you to the server's listener.*

### T40.06 · Network constraints (6.9)

**Must cover:**

- [x] Bandwidth, latency, jitter, packet loss and their effect on apps (timeouts, slow chatty APIs, poor voice/video)
- [x] Mitigations: QoS, caching, fewer round trips, compression

**Notes:**

- **Definitions** (exam-level):
  - **Bandwidth**: capacity in bits/s. Limits **bulk** transfers (backups, image pushes, large JSON). Saturation causes queueing, which shows up as extra latency and drops.
  - **Latency**: one-way or round-trip delay (RTT). Every request/response pays at least one RTT, and new connections also pay TCP + TLS handshake RTTs.
  - **Jitter**: variation in latency. Hurts real-time **voice/video** (choppy audio, frozen video). Barely matters to batch APIs.
  - **Packet loss**: TCP retransmits and backs off, so throughput drops and requests stall or time out. UDP media just has gaps.
- **Effect on automation code:**
  - **Chatty APIs**: total time ≈ calls × RTT. Section 6: 20 × `GET /devices/{id}` = **0.92 s** vs 1 × `GET /devices` = **0.05 s** at 40 ms per call. With `T40_DELAY_MS=150` it was **3.16 s** vs **0.15 s**. More bandwidth changes neither number.
  - **Timeouts**: high latency or loss turns into `ReadTimeout` / `ConnectTimeout`. Set realistic `timeout=(connect, read)` values and retry with backoff ([T11](../bee/T11-python-requests-scripting.md)). `requests` has **no default timeout**.
- **Mitigations:**

  | Problem | Fix |
  |---|---|
  | latency × many calls | **fewer round trips**: bulk/batch endpoints, filters (`?role=edge`), bigger page size, reuse the TCP/TLS session (`requests.Session` keep-alive), run calls in parallel |
  | repeated reads | **caching**: local cache, `ETag` / `If-None-Match` → `304` ([T07](../bee/T07-rest-fundamentals-http-codes.md)) |
  | bandwidth | **compression**: `Accept-Encoding: gzip`. Lab: 2349 B → **337 B**. Also request only the fields you need |
  | jitter / loss for voice & video | **QoS**: classify/mark (DSCP EF for voice), priority/low-latency queue, shaping; jitter buffers on endpoints |
  | loss on the link | fix the physical/RF issue; retries with backoff on the app side |

![Chatty vs bulk over a 40 ms path](../assets/T40/07-chatty-vs-bulk.png)

*Same data: 20 round trips vs 1. Latency multiplies by the number of calls; compression shrinks the bytes, not the round trips.*

### T40.07 · Exam angle

**Must cover:**

- [x] Diagnose the cause from symptoms; pick the fix

**Notes:**

- `diagnose()` in the program is this table written as code:

  | Symptom in the question | Likely cause | Pick this fix |
  |---|---|---|
  | `Connection refused`, instantly | service down, wrong port, bound to `127.0.0.1` | start/fix the service, correct the port, `ss -tlnp` |
  | hangs, then `timed out` / `ConnectTimeout` | firewall/ACL drop, no route, missing NAT, VPN route missing | open the port in the ACL, fix route / split-tunnel list |
  | works inside LAN, not from internet | no inbound static NAT / port forward | add the NAT rule + firewall permit |
  | allow-listed IP still blocked | traffic leaves via a PAT/proxy address | allow-list the NAT/public IP |
  | browser works, script times out on corp LAN | script not using the proxy | set `HTTPS_PROXY` / `proxies=` |
  | `407` | proxy needs credentials | `http://user:pass@proxy:port` / `--proxy-user` |
  | `CERTIFICATE_VERIFY_FAILED` only on corp network | TLS inspection CA not trusted | `verify=corp-ca.pem` / `REQUESTS_CA_BUNDLE` |
  | internal hostname fails on VPN, IP works | split DNS not applied | use the VPN-pushed DNS server |
  | VPN up, small requests OK, large hang | MTU / PMTUD black hole | lower MTU, `ip tcp adjust-mss` |
  | corp subnet unreachable on VPN from home only | overlapping subnet with home LAN | renumber / more-specific route / NAT |
  | slow over WAN, many small calls | latency × round trips | batch, cache, fewer calls |
  | voice/video choppy, data fine | jitter/loss | QoS |

![Symptom to fix triage](../assets/T40/08-symptom-triage.png)

*One symptom, one fix. Yellow = misconfiguration, red = silent-drop style faults; blue = the answer to pick.*

## Exam traps

- **Refused ≠ blocked.** Refused (RST) proves the host is reachable and the path is open; the service isn't listening. A firewall drop gives a **timeout**. (A firewall *reject* can also fail fast; the exam usually means drop.)
- **Ping OK ≠ app OK.** ICMP working says nothing about TCP 443/830. ICMP failing doesn't mean the host is down either: many firewalls block echo. Test the actual port with `nc -zv` / `telnet`.
- **`407` vs `401`.** 407 = proxy auth (`Proxy-Authenticate` / `Proxy-Authorization`). 401 = server auth (`WWW-Authenticate` / `Authorization`). New API tokens won't fix a 407.
- **HTTPS via proxy uses `CONNECT`.** In `requests`, a 407 there is a `ProxyError` exception, not a response.
- **TLS inspection fix = trust the corp CA** (`verify=path`, `REQUESTS_CA_BUNDLE`, `--cacert`), not `verify=False` / `-k`.
- **Proxy dict keys = target scheme.** `{"https": "http://proxy:3128"}`: the proxy URL is usually `http://` even for HTTPS targets. Setting only `HTTPS_PROXY` leaves `http://` URLs going direct (the lab's env demo shows this).
- **`NO_PROXY`** for internal controllers. Otherwise internal calls go to the internet proxy and fail.
- **Split DNS:** IP works, name fails → DNS, not routing.
- **MTU:** "SSH login works, `show tech` / file copy hangs over VPN" → MTU/MSS, not ACL.
- **6.9:** latency-bound problems are fixed by **fewer round trips**, not more bandwidth. Jitter matters most for **voice/video** → QoS.
- **`traceroute` shows the L3 path**, not whether a TCP port is open. `nc -zv` / `telnet` don't send HTTP, so they can't show a `4xx`.

## Examples

### 1. Run the reference program

Local (needs Python 3 + `requests` + `openssl`):

```bash
python3 -m venv /tmp/t40-venv
/tmp/t40-venv/bin/pip install requests
PYTHON=/tmp/t40-venv/bin/python bash labs/T40/run_lab.sh
```

Docker lab container (from the repo root):

```bash
docker build --tag ccna-auto-lab:latest --file labs/Dockerfile labs/
docker run --rm --volume "$(pwd)":/work ccna-auto-lab:latest bash labs/T40/run_lab.sh
```

Or run the fake network in one terminal and the client in another:

```bash
python3 labs/T40/lab_env.py
```

```bash
T40_CA=/tmp/t40-certs/corp-ca.pem python3 labs/T40/conn_doctor.py
```

### 2. CLI drill (`labs/T40/cli_drill.sh`)

```bash
#!/usr/bin/env bash
# T40 CLI drill: the exam's diagnostic tools against the fake network from lab_env.py.
# Run with the lab up:  bash labs/T40/run_lab.sh labs/T40/cli_drill.sh
set -u
H=127.0.0.1
P="${T40_BASE_PORT:-18140}"
CA="${T40_CA:-/tmp/t40-certs/corp-ca.pem}"
export no_proxy='' NO_PROXY=''             # use only the proxies we name on the command line
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy

step() { printf '\n$ %s\n' "$*"; "$@" 2>&1; }

echo "== 0. Name and path: dig / nslookup / ping with DF bit =="
step dig +short localhost
step nslookup api.corp.invalid
step ping -c 2 -M do -s 1472 $H

echo; echo "== 1. Is the port open? (nc = TCP handshake only) =="
step nc -zv -w 2 $H $P
step nc -zv -w 2 $H $((P + 1))
step nc -zv -w 2 $H $((P + 2))

echo; echo "== 2. curl -v: where does it stop? =="
step curl -sSv --max-time 3 http://$H:$((P + 1))/health
step curl -sSv --connect-timeout 2 http://$H:$((P + 2))/health

echo; echo "== 3. Proxy: 407 then --proxy-user =="
step curl --silent --include --proxy http://$H:$((P + 3)) http://$H:$P/whoami
step curl --silent --proxy http://$H:$((P + 3)) --proxy-user labuser:labpass http://$H:$P/whoami

echo; echo "== 4. HTTPS via proxy: TLS inspection CA =="
step curl --silent --show-error --proxy http://labuser:labpass@$H:$((P + 3)) https://$H:$((P + 4))/health
step curl --silent --show-error --proxy http://labuser:labpass@$H:$((P + 3)) --cacert "$CA" https://$H:$((P + 4))/health

echo; echo "== 5. Who is listening locally? =="
printf '\n$ ss -ltn | grep 1804\n'
if command -v ss > /dev/null; then ss -ltn | grep 1804; else echo "ss not installed (Docker lab: apt-get install iproute2)"; fi
```

Run it: `bash labs/T40/run_lab.sh labs/T40/cli_drill.sh`. Real output:

```text
== 0. Name and path: dig / nslookup / ping with DF bit ==

$ dig +short localhost
127.0.0.1

$ nslookup api.corp.invalid
Server:		127.0.0.53
Address:	127.0.0.53#53

** server can't find api.corp.invalid: NXDOMAIN


$ ping -c 2 -M do -s 1472 127.0.0.1
PING 127.0.0.1 (127.0.0.1) 1472(1500) bytes of data.
1480 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.013 ms
1480 bytes from 127.0.0.1: icmp_seq=2 ttl=64 time=0.034 ms

--- 127.0.0.1 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1030ms
rtt min/avg/max/mdev = 0.013/0.023/0.034/0.010 ms

== 1. Is the port open? (nc = TCP handshake only) ==

$ nc -zv -w 2 127.0.0.1 18140
Connection to 127.0.0.1 18140 port [tcp/*] succeeded!

$ nc -zv -w 2 127.0.0.1 18141
nc: connect to 127.0.0.1 port 18141 (tcp) failed: Connection refused

$ nc -zv -w 2 127.0.0.1 18142
nc: connect to 127.0.0.1 port 18142 (tcp) timed out: Operation now in progress

== 2. curl -v: where does it stop? ==

$ curl -sSv --max-time 3 http://127.0.0.1:18141/health
*   Trying 127.0.0.1:18141...
* connect to 127.0.0.1 port 18141 failed: Connection refused
* Failed to connect to 127.0.0.1 port 18141 after 0 ms: Connection refused
* Closing connection 0
curl: (7) Failed to connect to 127.0.0.1 port 18141 after 0 ms: Connection refused

$ curl -sSv --connect-timeout 2 http://127.0.0.1:18142/health
*   Trying 127.0.0.1:18142...
* After 2000ms connect time, move on!
* connect to 127.0.0.1 port 18142 failed: Connection timed out
* Connection timeout after 2001 ms
* Closing connection 0
curl: (28) Connection timeout after 2001 ms

== 3. Proxy: 407 then --proxy-user ==

$ curl --silent --include --proxy http://127.0.0.1:18143 http://127.0.0.1:18140/whoami
HTTP/1.1 407 Proxy Authentication Required
Server: BaseHTTP/0.6 Python/3.10.12
Date: Sat, 10 Oct 2026 12:35:39 GMT
Proxy-Authenticate: Basic realm="corp-proxy"
Content-Type: application/json
Content-Length: 42

{"error": "proxy authentication required"}
$ curl --silent --proxy http://127.0.0.1:18143 --proxy-user labuser:labpass http://127.0.0.1:18140/whoami
{"seen_client": "127.0.0.2:58173", "x_forwarded_for": "127.0.0.1"}
== 4. HTTPS via proxy: TLS inspection CA ==

$ curl --silent --show-error --proxy http://labuser:labpass@127.0.0.1:18143 https://127.0.0.1:18144/health
curl: (60) SSL certificate problem: unable to get local issuer certificate
More details here: https://curl.se/docs/sslcerts.html

curl failed to verify the legitimacy of the server and therefore could not
establish a secure connection to it. To learn more about this situation and
how to fix it, please visit the web page mentioned above.

$ curl --silent --show-error --proxy http://labuser:labpass@127.0.0.1:18143 --cacert /tmp/t40-certs/corp-ca.pem https://127.0.0.1:18144/health
{"status": "ok"}
== 5. Who is listening locally? ==

$ ss -ltn | grep 1804
LISTEN 0      5               127.0.0.1:18144      0.0.0.0:*          
LISTEN 0      5               127.0.0.1:18143      0.0.0.0:*          
LISTEN 1      0               127.0.0.1:18142      0.0.0.0:*          
LISTEN 0      5               127.0.0.1:18140      0.0.0.0:*          
```

- Read the `LISTEN` rows: `18142` shows `Recv-Q 1` / `Send-Q 0` because its accept queue (backlog 0) is full. That's how the lab fakes a silent drop.

### 3. Proxy settings from the environment (`labs/T40/env_proxy_demo.py`)

`requests` reads `HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY` / `REQUESTS_CA_BUNDLE` by default (`trust_env=True`):

```python
"""T40: how requests picks up proxy/CA settings from the environment (trust_env=True, the default).

Run with the lab up, changing only the env vars, e.g.:
  HTTPS_PROXY=http://127.0.0.1:18143 python3 labs/T40/env_proxy_demo.py
"""
import requests

for url in ("http://127.0.0.1:18140/health", "https://127.0.0.1:18144/health"):
    try:
        r = requests.get(url, timeout=(2, 5))
        print(f"{url} -> {r.status_code} {r.text}")
    except requests.exceptions.RequestException as exc:
        print(f"{url} -> {type(exc).__name__}: ...{str(exc)[-112:]}")   # tail holds the real cause
```

Start the lab (`python3 labs/T40/lab_env.py`), then in another shell run each line. Real output:

```text
$ HTTPS_PROXY=http://127.0.0.1:18143 python3 labs/T40/env_proxy_demo.py
http://127.0.0.1:18140/health -> 200 {"status": "ok"}
https://127.0.0.1:18144/health -> ProxyError: ...roxyError('Unable to connect to proxy', OSError('Tunnel connection failed: 407 Proxy Authentication Required')))

$ HTTP_PROXY=http://127.0.0.1:18143 HTTPS_PROXY=http://labuser:labpass@127.0.0.1:18143 python3 labs/T40/env_proxy_demo.py
http://127.0.0.1:18140/health -> 407 {"error": "proxy authentication required"}
https://127.0.0.1:18144/health -> SSLError: ...: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1007)')))

$ HTTP_PROXY=http://labuser:labpass@127.0.0.1:18143 HTTPS_PROXY=http://labuser:labpass@127.0.0.1:18143 REQUESTS_CA_BUNDLE=/tmp/t40-certs/corp-ca.pem python3 labs/T40/env_proxy_demo.py
http://127.0.0.1:18140/health -> 200 {"status": "ok"}
https://127.0.0.1:18144/health -> 200 {"status": "ok"}

$ HTTP_PROXY=http://127.0.0.1:18143 HTTPS_PROXY=http://127.0.0.1:18143 NO_PROXY=127.0.0.1 REQUESTS_CA_BUNDLE=/tmp/t40-certs/corp-ca.pem python3 labs/T40/env_proxy_demo.py
http://127.0.0.1:18140/health -> 200 {"status": "ok"}
https://127.0.0.1:18144/health -> 200 {"status": "ok"}
```

- Run 1: only `HTTPS_PROXY` is set, so the `http://` URL went **direct** (200) and only the HTTPS call hit the proxy's 407.
- Run 2: plain-HTTP 407 is a **response**; HTTPS gets past the proxy and then fails TLS verification.
- Run 4: `NO_PROXY` bypasses the proxy completely, even though the proxy URLs have no credentials.

### 4. Break it on purpose

Each edit was run against the lab; the result shown is real.

| Edit | Result |
|---|---|
| `T40_DELAY_MS=150 bash labs/T40/run_lab.sh` | `20 x GET /devices/{id}: 3.16s   1 x GET /devices: 0.15s`: chatty cost scales with RTT, bulk barely moves |
| In `main()`, change the slow-report call to `timeout=(2, 5)` | `GET slow report (read timeout 5s)  -> 200 OK` after 3.0 s. The server was slow, not broken |
| Remove `proxies=proxies(True)` credentials (use `proxies(False)`) on the `verify=corp-ca` call | same `ProxyError` as the no-creds line: the 407 hits before TLS starts |
| Drop `verify=CORP_CA` from the last HTTPS call | `SSLError` (the "default CAs" line) |
| `export HTTPS_PROXY=http://127.0.0.1:18143` and set `direct.trust_env = True` | the "direct" HTTPS calls start failing with `ProxyError`: an env proxy silently reroutes traffic |

### 5. Real network drills (run on your own laptop / jump host)

These need a real path, so no output is pasted here. Swap in your own hosts.

```bash
# Path MTU through a VPN: lower -s until it passes (1472 = 1500-byte packet)
ping -c 3 -M do -s 1472 10.1.1.10
ping -c 3 -M do -s 1372 10.1.1.10

# Which interface/tunnel is used for a destination? (split-tunnel check)
ip route get 10.1.1.10

# Split DNS: ask the default resolver, then the corp DNS server explicitly
nslookup api.corp.local
nslookup api.corp.local 10.0.0.53

# Path and port to a DevNet sandbox
traceroute -n sandbox-iosxe-latest-1.cisco.com
nc -zv -w 3 sandbox-iosxe-latest-1.cisco.com 830
curl -sSv --max-time 5 --output /dev/null https://sandbox-iosxe-latest-1.cisco.com/restconf/
```

## Practice questions

**Q1.** A script calls `https://10.20.1.5:8443/api` and fails **instantly** with `ConnectionRefusedError`. `ping 10.20.1.5` works. What is the most likely cause?

A. An ACL on the path drops TCP 8443
B. The API service isn't listening on 8443 on that host
C. The proxy needs credentials
D. MTU mismatch on the path

<details><summary>Answer</summary>

**B.** An instant refusal is a TCP RST from the host, so the path is open and nothing listens on that port. An ACL drop (A) gives a timeout.

</details>

**Q2.** From the corporate LAN, `requests.get("https://api.meraki.com/api/v1/organizations", headers=h, timeout=10)` raises `ConnectTimeout`. The same URL works in the browser on the same PC. What should you change?

A. Add `verify=False`
B. Increase the timeout to 60
C. Pass the corporate proxy, e.g. `proxies={"https": "http://proxy.corp:3128"}` or set `HTTPS_PROXY`
D. Change the API key

<details><summary>Answer</summary>

**C.** The browser uses the configured proxy; the script tries to go direct and the firewall drops it. TLS (A) and auth (D) never start, and a longer timeout (B) just waits longer.

</details>

**Q3.** After you add the proxy, the call returns `407 Proxy Authentication Required`. Which header is the client missing?

A. `Authorization`
B. `Proxy-Authorization`
C. `X-Cisco-Meraki-API-Key`
D. `WWW-Authenticate`

<details><summary>Answer</summary>

**B.** 407 comes from the proxy, which sends `Proxy-Authenticate`; the client must answer with `Proxy-Authorization` (e.g. `http://user:pass@proxy:3128`). `Authorization` / API keys are for the server.

</details>

**Q4.** On the corp network only, a Python script gets `SSLError: CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate` for every HTTPS API. At home it works. What is the best fix?

A. `verify=False` on every call
B. Switch to `http://`
C. Point `verify=` (or `REQUESTS_CA_BUNDLE`) at the corporate inspection CA certificate
D. Ask the API vendor to renew their certificate

<details><summary>Answer</summary>

**C.** A TLS-inspecting proxy re-signs certificates with a corporate CA that `certifi` doesn't include. Trust that CA. `verify=False` (A) removes protection against every server; the vendor's cert (D) is fine.

</details>

**Q5.** An engineer on a split-tunnel VPN can `ping 10.50.0.20` but `curl https://dnac.corp.local` fails with `Could not resolve host`. What is the cause?

A. The ACL blocks TCP 443
B. The VPN doesn't route 10.50.0.0/16
C. The laptop isn't using the corporate DNS server for `corp.local` (split DNS)
D. The MTU is too small

<details><summary>Answer</summary>

**C.** The IP is reachable, so the route works (not B), and a port block (A) can't cause a name-resolution error. The internal name only exists on the corp DNS server pushed by the VPN.

</details>

**Q6.** Over a site-to-site IPsec tunnel, SSH logins to a router work, but `show running-config` output freezes partway and SCP transfers hang. Which fix addresses the most likely cause?

A. `ip tcp adjust-mss 1360` on the tunnel interface
B. Permit TCP 22 in the ACL
C. Add a static NAT for the router
D. Enable QoS for voice

<details><summary>Answer</summary>

**A.** Small packets pass and large ones vanish: an MTU/PMTUD black hole caused by IPsec overhead. Clamp the MSS (and/or lower `ip mtu`). Port 22 is clearly open already (B).

</details>

**Q7.** A script collects data from 500 devices with one REST call per device across a 120 ms WAN link. It takes over a minute; link utilisation stays under 5%. Which **two** changes help most? (Choose two.)

A. Upgrade the link from 100 Mb/s to 1 Gb/s
B. Use a bulk endpoint that returns many devices per call
C. Reuse one `requests.Session` (keep-alive) and run requests in parallel
D. Mark the traffic DSCP EF
E. Disable TLS certificate verification

<details><summary>Answer</summary>

**B and C.** The script is latency-bound (calls × RTT), not bandwidth-bound (utilisation < 5%). Fewer round trips (B) and fewer handshakes plus concurrency (C) cut the time. More bandwidth (A) doesn't; EF (D) is for voice.

</details>

**Q8.** Put these steps in the order you'd use to troubleshoot "my script can't reach `https://api.corp.local/v1/health`":

1. `curl -v https://api.corp.local/v1/health`
2. `nslookup api.corp.local`
3. `nc -zv api.corp.local 443`
4. `ping api.corp.local`

<details><summary>Answer</summary>

**2 → 4 → 3 → 1.** Name, then L3 reachability, then the L4 port, then the L7 HTTP/TLS exchange. Stop at the first rung that fails.

</details>

## Study aids

| Aid | Type | Title | Est. min | Resource |
|---|---|---|---|---|
| T40.1 | Video | Describe Network Elements that Impact Applications | 23 | CBT module |
| T40.2 | Top-up | Diagnose NAT, blocked port, proxy, VPN issues | 30 | Own notes |

- Skip / low priority: n/a
- Top-up T40.2 (blueprint 6.8, proxy and VPN diagnosis): this note's T40.03 + T40.04, the GIF, and Examples §2–§3. CBT coverage is title-matched only (the video title doesn't name proxy/VPN diagnosis).

## Sources

- Cisco 200-901 CCNAAUTO v1.1 exam topics (exact 6.8 / 6.9 wording): https://learningcontent.cisco.com/documents/marketing/exam-topics/200-901-CCNAAUTO_v.1.1.pdf
- Requests advanced usage (proxies, env vars, `REQUESTS_CA_BUNDLE`, `verify`, connect/read timeouts, no default timeout): https://requests.readthedocs.io/en/latest/user/advanced/
- Everything curl, proxy environment variables (lowercase `http_proxy`, `NO_PROXY`, `--noproxy`): https://everything.curl.dev/usingcurl/proxies/env.html
- RFC 9110 HTTP Semantics (§9.3.6 CONNECT, §11.7.1 Proxy-Authenticate, §11.7.2 Proxy-Authorization, §15.5.8 407): https://www.rfc-editor.org/rfc/rfc9110.html
- Cisco, Troubleshoot DMVPN Issues (MTU/MSS: `ip mtu 1400`, `ip tcp adjust-mss 1360`): https://www.cisco.com/c/en/us/support/docs/security/dynamic-multipoint-vpn-dmvpn/111976-dmvpn-troubleshoot-00.html
- Diagrams: Mermaid sources in `assets/T40/*.mmd` (rendered `.png` next to each).
- Architecture diagrams: HTML sources `assets/T40/01-nat-inbound.html`, `assets/T40/04-vpn-tunnel.html` (shared kit `assets/_arch/`).
- Overview image: HTML source `assets/T40/00-overview.html`, rendered to `assets/T40/00-overview.png`.
- Animation: `assets/T40/09-proxy-journey-anim.html`, rendered to `assets/T40/09-proxy-journey.gif`.

## To verify

- ⚠ verify: the lab was run on Linux (Python 3.10, requests 2.34.2, curl, OpenBSD `nc`). It was **not run inside the Docker lab image**: Docker wasn't available in the drafting environment. The image has `curl`, `nc`, `dig` and `ping`, but **no `ss` (iproute2) or `traceroute`**. `cli_drill.sh` prints a hint instead of failing when `ss` is missing.
- ⚠ verify: the "filtered" port is simulated with a full accept queue (Linux drops SYNs when the backlog is full). This is a Linux kernel behaviour; on macOS the result may differ.
- ⚠ verify: TLS inspection is simulated by the API server's own cert being issued by a private "Corp TLS Inspection CA". The lab proxy does a plain `CONNECT` tunnel; it doesn't do real MITM re-signing.
- ⚠ verify: Examples §5 (real path MTU, split DNS, DevNet sandbox `nc`/`curl`) were **not run** against a live network, so no output is shown. The sandbox host name changes; check developer.cisco.com/sandbox.
- ⚠ verify: MSS/MTU values (`1360` / `1400`) are Cisco's common examples; the right numbers depend on the actual tunnel overhead.
- ⚠ verify: the overlapping-subnet behaviour ("connected route wins on an equal prefix") depends on the VPN client (some clients install more-specific or higher-priority routes, or block local-LAN access).
- CBT "Describe Network Elements that Impact Applications": depth of proxy/VPN coverage is unconfirmed (title-matched only).
