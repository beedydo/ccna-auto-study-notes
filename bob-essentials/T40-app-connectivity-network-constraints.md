# T40 · App connectivity + network constraints: essentials

> Blueprint 6.8, 6.9 · Full note: [bob/T40-app-connectivity-network-constraints.md](../bob/T40-app-connectivity-network-constraints.md) · Teach-back 2026-11-01

## In one picture
![T40 at a glance: where an app call breaks on the path, the diagnostic ladder, constraints and the symptom-to-fix table](../assets/T40/00-overview.png)
*Read the top panel left to right as the path an API call takes (App → VPN → proxy → firewall → NAT → server), then the diagnostic ladder in the middle, then the symptom → cause → fix table at the bottom.*

## The big idea
An API call from a script crosses the same boxes you already troubleshoot every day: VPN, proxy, firewall, NAT, and finally the server. The exam gives you **one symptom** (an error message, a hang, a slow run) and asks you to name the box that caused it and pick the fix. Think of it like reading a `show` output: the exact wording of the failure (instant refusal, slow timeout, `407`, certificate error) tells you which layer broke. Blueprint 6.9 adds the "network constraints" angle: why a script is slow (latency × round trips), not just why it fails.

## What you need to know

### 1. Read the failure mode: refused vs timeout
- The first question is always whether the TCP handshake completed, because that splits "server problem" from "path problem".
- An instant **connection refused** means the host sent back a **TCP RST**: the host is reachable and the path is open, but nothing is listening on that port.
- A hang that ends in **timed out** means the SYN got no reply at all: a firewall or ACL **dropped** it silently, there is no route, NAT is missing, or the host is down.
- A firewall can also **reject** (send an RST or ICMP admin-prohibited), which fails fast and can look like "refused", but on the exam "blocked by a firewall" usually means a silent drop and a timeout.

| Outcome | On the wire | `nc -zv` | `curl` | Python `requests` | Meaning |
|---|---|---|---|---|---|
| **Open** | SYN → SYN-ACK | `succeeded!` | continues to HTTP | a response | something listens |
| **Refused** | SYN → **RST** | `Connection refused` | `curl: (7)` | `ConnectionError` | host reachable, port closed / service down / bound to another IP |
| **Timeout** | SYN → nothing | `timed out` | `curl: (28)` | `ConnectTimeout` | firewall/ACL drop, no route, missing NAT, host down |

![Refused vs timeout on the wire](../assets/T40/02-refused-vs-timeout.png)
*Refused = an RST came back quickly; timeout = the SYN went into a black hole and the client retried until it gave up.*

- In `requests` there are two timeouts: a **ConnectTimeout** means no SYN-ACK came back, while a **ReadTimeout** means the connection worked but the server was too slow to answer.
- Know the ports: SSH 22, Telnet 23, HTTP 80, HTTPS 443, NETCONF **830**, RESTCONF 443. If a NETCONF script times out on 830 while SSH on 22 works, the ACL allows 22 but not 830.

### 2. NAT problems
- Private **RFC 1918** addresses (`10/8`, `172.16/12`, `192.168/16`) are not routed on the internet, so an outside client can only reach a private server if the edge has a **static NAT** (1:1) or a **port forward** (static PAT, `public:443 → private:443`).
- Without that inbound rule, the SYN to the public IP is dropped at the edge, so the outside client sees a **timeout**, not a refusal.
- The classic symptom is "it works from inside the LAN but fails from the internet", which also hits cloud webhook senders trying to reach you.
- With source NAT/PAT (and with proxies), the server sees the **translated** source address, not the real client.
- That has three knock-on effects: an allow-list must permit the **NAT/public IP**, a per-client rate limit treats everyone behind one PAT address as **one client**, and the real client IP is only recoverable from **`X-Forwarded-For`** if an HTTP proxy or load balancer added it (plain NAT adds no header).
- Return traffic must come back through the **same NAT device**, because that device holds the translation state; asymmetric routing around it breaks the session.

![Inbound static NAT / port forward decision](../assets/T40/01-nat-inbound.png)
*No inbound rule means dropped means timeout; with a rule, the destination is rewritten to the private IP.*

### 3. Proxy problems: 407 and TLS inspection
- Many corporate networks block direct outbound 80/443 and force traffic through a **forward proxy**, so a script that ignores the proxy **times out** while the browser (which has the proxy configured) works fine.
- You can give the script the proxy in three ways: `proxies={"http": "http://proxy:3128", "https": "http://proxy:3128"}` in `requests`, the environment variables `HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY`, or `curl --proxy http://proxy:3128`.
- In the `proxies` dict, the **key** is the scheme of the **target** URL, and the **value** is the proxy URL, which is usually `http://` even for HTTPS targets.
- **`NO_PROXY`** lists hosts that should go direct (for example `NO_PROXY=127.0.0.1,.corp.local,10.0.0.0/8`); internal controllers such as Catalyst Center usually belong there, otherwise the internet proxy gets the request and it fails.
- **407 Proxy Authentication Required** means the **proxy**, not the API server, wants credentials. The proxy sends `Proxy-Authenticate`, and the client must answer with the **`Proxy-Authorization`** header (for example `http://user:pass@proxy:3128` or `curl --proxy-user user:pass`).
- For HTTPS, the client first asks the proxy to open a tunnel with **`CONNECT host:443`**. If that gets a 407, `requests` raises a **`ProxyError`** exception instead of returning a response.
- **TLS inspection** means the proxy decrypts traffic and re-signs every site's certificate with a **corporate CA**. Browsers trust that CA because IT pushed it, but a Python venv or Docker container does not.
- The symptom is `CERTIFICATE_VERIFY_FAILED ... unable to get local issuer certificate` (curl: `(60) SSL certificate problem`) **only on the corporate network**.
- The right fix is to trust the corporate CA with `verify="/path/corp-ca.pem"`, `REQUESTS_CA_BUNDLE=/path/corp-ca.pem` or `curl --cacert`. The wrong fix is `verify=False` / `curl -k`, which turns off checking for every server.

```python
requests.get(url, proxies={"https": "http://user:pass@proxy.corp:3128"}, verify="/path/corp-ca.pem", timeout=(2, 5))
```
*Plain reading: send HTTPS through the corporate proxy with credentials, trust the corp CA, and give up after 2 s to connect or 5 s waiting for data.*

![Animated: HTTPS through a corporate proxy, one call per frame](../assets/T40/09-proxy-journey.gif)
*CONNECT without credentials → 407 → add Proxy-Authorization → certificate from the corp CA fails → trust corp-ca.pem → 200; the API server was fine the whole time.*

### 4. VPN problems: routes, DNS, MTU, overlap
- A **split tunnel** sends only corporate prefixes (for example `10.0.0.0/8`) into the VPN, while a **full tunnel** sends everything (`0.0.0.0/0`) through the corporate network.

| | Split tunnel | Full tunnel |
|---|---|---|
| Internet traffic | goes direct via the home ISP | goes via corp, so the corp proxy and firewall rules apply |
| Typical break | a corp prefix is **missing** from the split list, so that traffic goes to the ISP and times out | a public SaaS/API now hits the corp proxy, giving `407`, TLS inspection errors or blocks |
| Check | `ip route get 10.1.1.10` (Linux) or `route print` (Windows) to see which interface is used | same, plus test with and without the proxy |

- **Split DNS** is when internal names like `api.corp.local` exist only on the corporate DNS server that the VPN pushes. If the laptop still asks the home resolver, `nslookup` returns NXDOMAIN while `ping` to the IP works. Fix the VPN DNS settings or query the corp server directly with `nslookup api.corp.local 10.0.0.53`.
- **MTU / PMTUD black hole**: IPsec/GRE headers make a 1500-byte packet too big, and TCP sets **DF** (Don't Fragment), so the router drops it and should send ICMP "fragmentation needed". If that ICMP is filtered, small packets work (ping, SSH login, TLS handshake) but large transfers **hang**.
- Test the path MTU with `ping -M do -s 1472 host` on Linux (1472 + 8 ICMP + 20 IP = 1500) or `ping -f -l 1472 host` on Windows, lowering the size until it passes.
- Fix it on the tunnel interface with `ip mtu 1400` and `ip tcp adjust-mss 1360` (Cisco's common example values; size them to your real overhead ⚠ verify).
- **Overlapping subnets**: if the home LAN and a corp subnet are both `192.168.1.0/24`, the laptop's directly connected route normally wins on an equal prefix, so "corp" traffic stays on the home LAN ⚠ verify (depends on the VPN client). Fix by renumbering, pushing more-specific routes, or NAT on the VPN head-end.

![MTU and PMTUD black hole](../assets/T40/05-mtu-blackhole.png)
*Small packets get through and large ones vanish when the ICMP "fragmentation needed" can't reach the sender; clamp the MSS.*

### 5. The diagnostic ladder
- Work **bottom-up** and stop at the first rung that fails, exactly like layered troubleshooting on a router.

| Rung | Tool | Question | How to read it |
|---|---|---|---|
| 1 DNS | `nslookup name` · `dig +short name` | does the name resolve, and to what? | NXDOMAIN = DNS problem; wrong IP = stale record or split DNS |
| 2 Reachability | `ping -c 3 host` | L3 reachability, RTT, loss | `mdev` ≈ jitter; no reply does not prove the host is down, because ICMP may be blocked |
| 3 Path | `traceroute host` (Windows `tracert`) | where does the path stop? | the last responding hop is where it dies; `* * *` = hop doesn't answer |
| 4 Port | `nc -zv -w 2 host 443` · `telnet host 443` | does the TCP handshake complete? | succeeded / refused / timed out |
| 5 HTTP | `curl -v URL` | TLS + HTTP exchange | `*` = connection/TLS info, `>` = sent, `<` = received; where it stops tells you the layer |
| 6 Server | `ss -tlnp` · `netstat -an` (on the server) | what is listening, on which IP? | `127.0.0.1:8080` = local only; `0.0.0.0:8080` = all interfaces; missing = service down |

![Diagnostic ladder](../assets/T40/06-diag-ladder.png)
*A port timeout sends you to firewall/NAT/routes; a refusal sends you to the server's listener.*

### 6. Network constraints (6.9): bandwidth, latency, jitter, loss
- **Bandwidth** is capacity in bits per second, and it limits **bulk** transfers such as backups, image pushes or very large JSON.
- **Latency** is the delay (usually round-trip time, **RTT**), and every request pays at least one RTT, plus extra RTTs for new TCP and TLS handshakes.
- **Jitter** is the variation in latency, and it mainly hurts **voice and video** (choppy audio, frozen video); batch APIs barely notice it.
- **Packet loss** makes TCP retransmit and slow down, so requests stall or time out, while UDP media just has gaps.
- A "chatty" script's total time is roughly **number of calls × RTT**. In Bob's lab, 20 single-device GETs at 40 ms took **0.92 s**, while one bulk GET took **0.05 s**; more bandwidth changes neither number.
- `requests` has **no default timeout**, so always set `timeout=(connect, read)` and retry with backoff.

| Problem | Fix |
|---|---|
| latency × many calls | **fewer round trips**: bulk endpoints, filters, bigger page size, reuse a `requests.Session` (keep-alive), run calls in parallel |
| repeated reads of the same data | **caching** (`ETag` / `If-None-Match` → `304`) |
| bandwidth | **compression** with `Accept-Encoding: gzip` (lab: 2349 B → 337 B), and ask only for the fields you need |
| jitter / loss for voice and video | **QoS**: classify and mark (DSCP EF for voice), priority queue, shaping |

![Chatty vs bulk over a 40 ms path](../assets/T40/07-chatty-vs-bulk.png)
*Same data, 20 round trips vs 1: latency multiplies by the number of calls, and compression shrinks bytes, not round trips.*

### 7. Exam angle: symptom → cause → fix

| Symptom in the question | Likely cause | Pick this fix |
|---|---|---|
| `Connection refused`, instantly | service down, wrong port, bound to `127.0.0.1` | start/fix the service, correct the port, check `ss -tlnp` |
| hangs, then `timed out` | firewall/ACL drop, no route, missing NAT, VPN route missing | open the port, fix the route or split-tunnel list |
| works inside the LAN, not from the internet | no inbound static NAT / port forward | add the NAT rule and a firewall permit |
| allow-listed IP still blocked | traffic leaves via a PAT/proxy address | allow-list the NAT/public IP |
| browser works, script times out on the corp LAN | script isn't using the proxy | set `HTTPS_PROXY` or `proxies=` |
| `407` | proxy needs credentials | `http://user:pass@proxy:port` or `--proxy-user` |
| `CERTIFICATE_VERIFY_FAILED` only on corp network | TLS inspection CA not trusted | `verify=corp-ca.pem` / `REQUESTS_CA_BUNDLE` |
| internal hostname fails on VPN, IP works | split DNS not applied | use the VPN-pushed DNS server |
| VPN up, small requests OK, large ones hang | MTU / PMTUD black hole | lower MTU, `ip tcp adjust-mss` |
| corp subnet unreachable on VPN from home only | overlapping subnet with the home LAN | renumber, more-specific route, or NAT |
| slow over WAN with many small calls | latency × round trips | batch, cache, fewer calls |
| voice/video choppy, data fine | jitter/loss | QoS |

## Exam traps (the ones that catch people)
- It looks like "refused means the firewall blocked it", but it's actually the opposite: a refusal (RST) proves the path is open and the service isn't listening, while a firewall drop gives a **timeout**.
- It looks like "ping works so the app should work", but ICMP says nothing about TCP 443 or 830; test the real port with `nc -zv` or `telnet`. And a failed ping doesn't prove the host is down, because many firewalls block echo.
- It looks like a `407` is an API auth problem, but it's actually the **proxy** asking for credentials (`Proxy-Authorization`); a `401` is the server asking (`Authorization`), and a new API token will never fix a 407.
- It looks like `verify=False` fixes the certificate error, but the exam's right answer for TLS inspection is to **trust the corporate CA** (`verify=path`, `REQUESTS_CA_BUNDLE`, `--cacert`).
- It looks like a dead tunnel when "VPN connects but large transfers hang", but it's actually **MTU/PMTUD**; clamp the MSS (`ip tcp adjust-mss 1360`) or lower the tunnel MTU.
- It looks like a routing problem when "the IP works but the name fails" on VPN, but it's actually **split DNS**.
- It looks like more bandwidth will speed up a slow script, but a script with many small calls is **latency-bound**, so the fix is fewer round trips; jitter matters mostly for voice/video, which is QoS.
- It looks like setting `HTTPS_PROXY` covers everything, but `http://` URLs still go direct unless `HTTP_PROXY` is set too.

## Quick self-check
<details><summary>Q1. A script fails instantly with "Connection refused" to 10.20.1.5:8443, and ping to the host works. What's wrong?</summary>The API service isn't listening on 8443. An instant refusal is an RST from the host, so the path is open; an ACL drop would give a timeout.</details>

<details><summary>Q2. On the corp LAN a script gets ConnectTimeout to api.meraki.com, but the browser on the same PC works. What do you change?</summary>Give the script the corporate proxy (`proxies={"https": "http://proxy.corp:3128"}` or `HTTPS_PROXY`). The browser uses the proxy; the script tries to go direct and gets dropped.</details>

<details><summary>Q3. After adding the proxy you get 407. Which header is missing?</summary>`Proxy-Authorization`. The 407 comes from the proxy, not the API server.</details>

<details><summary>Q4. Over an IPsec tunnel, SSH login works but `show running-config` freezes partway. What's the fix?</summary>`ip tcp adjust-mss 1360` (and/or lower `ip mtu`) on the tunnel. Small packets pass, large ones vanish: an MTU/PMTUD black hole.</details>

<details><summary>Q5. A script polls 500 devices one call each over a 120 ms WAN, takes over a minute, and link use is under 5%. Name two fixes.</summary>Use a bulk endpoint, and reuse one `requests.Session` with parallel requests. It's latency-bound (calls × RTT), so a bigger link won't help.</details>

## Cheat lines to say out loud
- "Refused = RST = server; timeout = silence = path."
- "Ladder bottom-up: DNS, ping, traceroute, port, curl, listener. Stop at the first broken rung."
- "407 is the proxy, 401 is the server. Trust the corp CA, never `verify=False`."
- "VPN up but big stuff hangs? MTU. Clamp the MSS."
- "Slow script = calls × RTT. Fewer calls, not more bandwidth. Choppy voice = QoS."
