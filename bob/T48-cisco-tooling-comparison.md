---
id: T48
title: "Cisco platforms side by side (auth, API style, gotchas)"
owner: Bob
blueprint: "3.1-3.6, 3.9"
primary_domain: D3
cbt_coverage: "None"
status: drafted   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-31
teach_back: 2026-11-01
cross_study: 2026-11-04
---

# T48 · Cisco platforms side by side (auth, API style, gotchas)

> Owner: **Bob** · Blueprint: **3.1-3.6, 3.9** · CBT coverage: **None** · Learn by 2026-10-31 · Teach-back 2026-11-01

![T48 at a glance: five login styles plus two odd ones, who manages what, API style and naming, Python entry points, and the exam's clue-to-platform map](../assets/T48/00-overview.png)

*The matrix at the top is the whole note: find the platform's row, read across (what you send · how long it lasts · the trap). The three cards below it are T48.01, T48.03 · T48.04 and T48.07. The bottom strip is T48.08, clue → platform. Red = exam traps, grey = exact syntax, blue = the platform to pick.*

## TL;DR (teach-back card)

- **Five login styles, plus two odd ones.** Basic on every call (IOS XE RESTCONF, NX-API CLI, NSO, ISE ERS, Secure Endpoint, CUCM, Webex xAPI) · static key (Meraki, Webex) · login → token header (FMC, Catalyst Center, FDM, CML, XDR, Secure Connect) · login → cookie (ACI, NX-API REST, SD-WAN Manager, UCSM) · signed request (Intersight). Odd ones: Malware Analytics' `api_key` parameter, and NETCONF/pyATS, which aren't HTTP at all.
- **Three platforms do something unexpected with the token.** SD-WAN needs a cookie **plus** an `X-XSRF-TOKEN` header, UCSM puts its cookie **in the XML body**, and FMC / Catalyst Center use custom **headers** (`X-auth-access-token`, `X-Auth-Token`), not `Authorization`.
- **Success is not success.** SD-WAN, UCSM and ACI can return `200` with a failure inside; FMC `201`, Catalyst Center `202` and a NETCONF candidate `<ok/>` mean "accepted, not live"; XDR and Malware Analytics analyse but never block.
- **Trap:** `Authorization: Bearer` names no platform. 6 of the 24 use it (Meraki, Webex, FDM, CML, XDR, Secure Connect), and FMC and Catalyst Center are **not** among them.

## Concepts

All eight concepts are covered by **one table of requests**, built by one script.

- `labs/T48/auth_side_by_side.py` is the **reference program**. It builds the first request each platform expects (31 requests, 24 platforms, 7 groups) with `requests.Request(...).prepare()` and prints them grouped by login style. It sends nothing, so there is no mock and no network. Placeholders only (`apiuser`, `apipass`, `<token>`).
- `labs/T48/check_drift.py` ties the program to the platform notes. Each request has a **marker** (a path, header or parameter). The check fails if the marker is missing from the request the program builds, or from the sibling note T12-T25 / T42 that owns that platform. If a platform note changes, T48 has to change with it.
- `labs/T48/run_lab.sh` runs both. `labs/T48/session_demo.py` is the T48.07 `Session` demo (Examples 4).
- Nothing here ran against a live product (see To verify). T48 adds no new platform facts: every endpoint, header and lifetime comes from the sibling note named in the `note` column of the program's `Step`s.

**`labs/T48/auth_side_by_side.py`**

```python
#!/usr/bin/env python3
"""T48: the first request each Cisco platform expects, built offline and printed side by side.

No network and no devices: requests.Request(...).prepare() builds the exact method, URL,
headers and body without sending anything. Placeholders only (apiuser / apipass / <token>).

  python3 labs/T48/auth_side_by_side.py                  # all platforms, grouped by login style
  python3 labs/T48/auth_side_by_side.py --only fmc,aci   # filter by key (see KEYS in the output)
  python3 labs/T48/auth_side_by_side.py --list           # the keys --only accepts

Needs: requests.
"""
import argparse
import base64
import hashlib
import sys
from collections import namedtuple

import requests

USER, PASS = "apiuser", "apipass"
AUTH = (USER, PASS)
TOKEN = "<token>"
JSON = {"Accept": "application/json", "Content-Type": "application/json"}
SHOW = ("Authorization", "X-auth-access-token", "X-Auth-Token", "X-XSRF-TOKEN", "Cookie",
        "SOAPAction", "Date", "Digest")

# key = short filter name, note = the sibling note that owns the detail, marker = the string
# check_drift.py looks for in that note, so this file cannot drift from the notes.
Step = namedtuple("Step", "group key label note method prepared marker")
A, B, C, D, E, F, G = (
    "A. Basic auth on EVERY call (no login step)",
    "B. Static key, sent on every call (no login step)",
    "C. Login call -> token -> header",
    "D. Login call -> cookie (+ a second token)",
    "E. No login: sign every request",
    "F. Key as a parameter",
    "G. Not HTTP",
)


def req(method, url, **kw):
    return requests.Request(method, url, **kw).prepare()


STEPS = [
    # ---- A. Basic on every call
    Step(A, "iosxe", "IOS XE RESTCONF", "T16", "GET", req(
        "GET", "https://iosxe.example/restconf/data/ietf-interfaces:interfaces", auth=AUTH,
        headers={"Accept": "application/yang-data+json"}), "/restconf/data/ietf-interfaces:interfaces"),
    Step(A, "nxapi-cli", "NX-OS NX-API CLI", "T17", "POST", req(
        "POST", "https://nxos.example/ins", auth=AUTH, json={"ins_api": {
            "version": "1.0", "type": "cli_show", "chunk": "0", "sid": "1",
            "input": "show version", "output_format": "json"}}), "/ins"),
    Step(A, "nso", "NSO RESTCONF", "T25", "GET", req(
        "GET", "http://nso.example:8080/restconf/data/tailf-ncs:devices/device", auth=AUTH,
        headers={"Accept": "application/yang-data+json"}), "tailf-ncs:devices/device"),
    Step(A, "ise", "ISE ERS", "T23", "GET", req(
        "GET", "https://ise.example:9060/ers/config/networkdevice", auth=AUTH,
        headers={"Accept": "application/json"}), "/ers/config/networkdevice"),
    Step(A, "se", "Secure Endpoint", "T23", "GET", req(
        "GET", "https://api.amp.cisco.com/v1/computers", auth=("<client-id>", "<api-key>")), "/v1/computers"),
    Step(A, "axl", "CUCM AXL (SOAP)", "T21", "POST", req(
        "POST", "https://cucm.example:8443/axl/", auth=AUTH,
        headers={"Content-Type": "text/xml", "SOAPAction": '"CUCM:DB ver=14.0 getPhone"'},
        data='<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
             'xmlns:ns="http://www.cisco.com/AXL/API/14.0"><soapenv:Body><ns:getPhone>'
             '<name>SEP001122334455</name></ns:getPhone></soapenv:Body></soapenv:Envelope>'),
         'SOAPAction: "CUCM:DB ver='),
    Step(A, "uds", "CUCM UDS (end user)", "T21", "GET", req(
        "GET", "https://cucm.example:8443/cucm-uds/user/jkam/devices", auth=("jkam", "<end-user-pw>"),
        headers={"Accept": "application/xml"}), "/cucm-uds/"),
    Step(A, "xapi-http", "Webex device xAPI (HTTP)", "T42", "POST", req(
        "POST", "https://roomkit.example/putxml", auth=AUTH, headers={"Content-Type": "text/xml"},
        data="<Command><Audio><Volume><Set><Level>30</Level></Set></Volume></Audio></Command>"), "/putxml"),
    # ---- B. Static key
    Step(B, "meraki", "Meraki Dashboard", "T18", "GET", req(
        "GET", "https://api.meraki.com/api/v1/organizations",
        headers={"Authorization": "Bearer <key>"}), "Authorization: Bearer <key>"),
    Step(B, "webex", "Webex (bot / integration token)", "T42", "GET", req(
        "GET", "https://webexapis.com/v1/people/me", headers={"Authorization": "Bearer <token>"}),
         "webexapis.com/v1"),
    # ---- C. Login -> token -> header
    Step(C, "fmc", "FMC: 1 login", "T23", "POST", req(
        "POST", "https://fmc.example/api/fmc_platform/v1/auth/generatetoken", auth=AUTH),
         "generatetoken"),
    Step(C, "fmc", "FMC: 2 use", "T23", "GET", req(
        "GET", "https://fmc.example/api/fmc_config/v1/domain/DOMAIN_UUID/object/networks",
        headers={"X-auth-access-token": TOKEN}), "X-auth-access-token"),
    Step(C, "fdm", "FDM: 1 login", "T23", "POST", req(
        "POST", "https://ftd.example/api/fdm/latest/fdm/token", headers=JSON,
        json={"grant_type": "password", "username": USER, "password": PASS}), "/fdm/token"),
    Step(C, "fdm", "FDM: 2 use", "T23", "GET", req(
        "GET", "https://ftd.example/api/fdm/latest/object/networks",
        headers={"Authorization": f"Bearer {TOKEN}"}), "/api/fdm/latest/object/networks"),
    Step(C, "xdr", "XDR: 1 login (client credentials)", "T23", "POST", req(
        "POST", "https://visibility.amp.cisco.com/iroh/oauth2/token", auth=("<client-id>", "<secret>"),
        headers={"Accept": "application/json"}, data={"grant_type": "client_credentials"}),
         "/iroh/oauth2/token"),
    Step(C, "xdr", "XDR: 2 use", "T23", "POST", req(
        "POST", "https://visibility.amp.cisco.com/iroh/iroh-inspect/inspect",
        headers={"Authorization": f"Bearer {TOKEN}", **JSON}, json={"content": "203.0.113.66"}),
         "/iroh/iroh-inspect/inspect"),
    Step(C, "umbrella", "Secure Connect / Umbrella: 1 login", "T23", "POST", req(
        "POST", "https://api.umbrella.com/auth/v2/token", auth=("<key>", "<secret>"),
        data={"grant_type": "client_credentials"}), "/auth/v2/token"),
    Step(C, "catc", "Catalyst Center: 1 login", "T20", "POST", req(
        "POST", "https://catc.example/dna/system/api/v1/auth/token", auth=AUTH),
         "/dna/system/api/v1/auth/token"),
    Step(C, "catc", "Catalyst Center: 2 use", "T20", "GET", req(
        "GET", "https://catc.example/dna/intent/api/v1/network-device",
        headers={"X-Auth-Token": TOKEN}), "X-Auth-Token"),
    Step(C, "cml", "CML: 1 login", "T25", "POST", req(
        "POST", "https://cml.example/api/v0/authenticate", json={"username": USER, "password": PASS}),
         "/api/v0/authenticate"),
    Step(C, "cml", "CML: 2 use", "T25", "GET", req(
        "GET", "https://cml.example/api/v0/labs", headers={"Authorization": f"Bearer {TOKEN}"}),
         "/api/v0/labs"),
    # ---- D. Login -> cookie
    Step(D, "aci", "ACI APIC: 1 login", "T19", "POST", req(
        "POST", "https://apic.example/api/aaaLogin.json",
        json={"aaaUser": {"attributes": {"name": USER, "pwd": PASS}}}), "aaaLogin.json"),
    Step(D, "aci", "ACI APIC: 2 use", "T19", "GET", req(
        "GET", "https://apic.example/api/class/fabricNode.json", headers={"Cookie": f"APIC-cookie={TOKEN}"}),
         "APIC-cookie"),
    Step(D, "nxapi-rest", "NX-API REST: 1 login", "T17", "POST", req(
        "POST", "https://nxos.example/api/aaaLogin.json",
        json={"aaaUser": {"attributes": {"name": USER, "pwd": PASS}}}), "aaaLogin.json"),
    Step(D, "sdwan", "SD-WAN Manager: 1 login", "T22", "POST", req(
        "POST", "https://manager.example:8443/j_security_check",
        data={"j_username": USER, "j_password": PASS}), "/j_security_check"),
    Step(D, "sdwan", "SD-WAN Manager: 2 token", "T22", "GET", req(
        "GET", "https://manager.example:8443/dataservice/client/token",
        headers={"Cookie": "JSESSIONID=<session>"}), "/client/token"),
    Step(D, "sdwan", "SD-WAN Manager: 3 use", "T22", "GET", req(
        "GET", "https://manager.example:8443/dataservice/device",
        headers={"Cookie": "JSESSIONID=<session>", "X-XSRF-TOKEN": "<xsrf>"}), "X-XSRF-TOKEN"),
    Step(D, "ucsm", "UCS Manager: 1 login (XML)", "T24", "POST", req(
        "POST", "https://ucsm.example/nuova", headers={"Content-Type": "text/xml"},
        data=f'<aaaLogin inName="{USER}" inPassword="{PASS}"/>'), "/nuova"),
    Step(D, "ucsm", "UCS Manager: 2 use (cookie in the BODY)", "T24", "POST", req(
        "POST", "https://ucsm.example/nuova", headers={"Content-Type": "text/xml"},
        data='<configResolveClass cookie="<outCookie>" classId="computeBlade"/>'), "configResolveClass"),
    # ---- E. Sign every request
    Step(E, "intersight", "Intersight", "T24", "GET", req(
        "GET", "https://intersight.com/api/v1/compute/PhysicalSummaries?$top=1",
        headers={
            "Date": "Sun, 18 Oct 2026 09:00:00 GMT",
            "Digest": "SHA-256=" + base64.b64encode(hashlib.sha256(b"").digest()).decode(),
            "Authorization": 'Signature keyId="<key-id>",algorithm="hs2019",'
                             'headers="(request-target) host date digest",signature="<signed with your private key>"',
        }), "Signature keyId"),
    # ---- F. Key as a parameter
    Step(F, "sma", "Malware Analytics", "T23", "GET", req(
        "GET", "https://panacea.threatgrid.com/api/v2/samples/SAMPLE_ID/state", params={"api_key": "API_KEY"}),
         "api_key"),
]
# G has no HTTP request to prepare; it is printed as text.
NOT_HTTP = [
    ("netconf", "IOS XE / NX-OS NETCONF", "ssh -p 830 apiuser@iosxe.example -s netconf    # SSH login, then <hello> (T15)"),
    ("pyats", "pyATS / Genie", "testbed.yaml (credentials, os, connections) -> device.connect()    # SSH/telnet, no API (T44)"),
]


def show(step):
    p = step.prepared
    print(f"  {step.label:<44} {p.method:<4} {p.url}")
    for name in SHOW:
        value = p.headers.get(name)
        if not value:
            continue
        note = ""
        if name == "Authorization" and value.startswith("Basic "):
            note = f"   (= {base64.b64decode(value[6:]).decode()})"
        print(f"  {'':<44}      {name}: {value}{note}")
    if p.body:
        body = p.body if isinstance(p.body, str) else p.body.decode()
        print(f"  {'':<44}      body: {body[:96]}{'...' if len(body) > 96 else ''}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma-separated keys, e.g. fmc,aci")
    ap.add_argument("--list", action="store_true", help="print keys only")
    args = ap.parse_args()
    wanted = set(args.only.split(",")) if args.only else None
    if args.list:
        for k in sorted({s.key for s in STEPS} | {k for k, *_ in NOT_HTTP}):
            print(k)
        return 0

    seen_groups, count, platforms = [], 0, set()
    for s in STEPS:
        if wanted and s.key not in wanted:
            continue
        if s.group not in seen_groups:
            seen_groups.append(s.group)
            print(f"\n== {s.group}")
        show(s)
        count += 1
        platforms.add(s.key)
    if not wanted or wanted & {k for k, *_ in NOT_HTTP}:
        seen_groups.append(G)
        print(f"\n== {G}")
        for key, name, text in NOT_HTTP:
            if not wanted or key in wanted:
                print(f"  {name:<44} {text}")
                platforms.add(key)
    noun = "group" if len(seen_groups) == 1 else "groups"
    print(f"\n{count} requests built for {len(platforms)} platforms, {len(seen_groups)} {noun}, nothing sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Output of `bash labs/T48/run_lab.sh` (real, 124 lines; the lines after the groups are the drift check):

```text
== A. Basic auth on EVERY call (no login step)
  IOS XE RESTCONF                              GET  https://iosxe.example/restconf/data/ietf-interfaces:interfaces
                                                    Authorization: Basic YXBpdXNlcjphcGlwYXNz   (= apiuser:apipass)
  NX-OS NX-API CLI                             POST https://nxos.example/ins
                                                    Authorization: Basic YXBpdXNlcjphcGlwYXNz   (= apiuser:apipass)
                                                    body: {"ins_api": {"version": "1.0", "type": "cli_show", "chunk": "0", "sid": "1", "input": "show vers...
  NSO RESTCONF                                 GET  http://nso.example:8080/restconf/data/tailf-ncs:devices/device
                                                    Authorization: Basic YXBpdXNlcjphcGlwYXNz   (= apiuser:apipass)
  ISE ERS                                      GET  https://ise.example:9060/ers/config/networkdevice
                                                    Authorization: Basic YXBpdXNlcjphcGlwYXNz   (= apiuser:apipass)
  Secure Endpoint                              GET  https://api.amp.cisco.com/v1/computers
                                                    Authorization: Basic PGNsaWVudC1pZD46PGFwaS1rZXk+   (= <client-id>:<api-key>)
  CUCM AXL (SOAP)                              POST https://cucm.example:8443/axl/
                                                    Authorization: Basic YXBpdXNlcjphcGlwYXNz   (= apiuser:apipass)
                                                    SOAPAction: "CUCM:DB ver=14.0 getPhone"
                                                    body: <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns="http://www...
  CUCM UDS (end user)                          GET  https://cucm.example:8443/cucm-uds/user/jkam/devices
                                                    Authorization: Basic amthbTo8ZW5kLXVzZXItcHc+   (= jkam:<end-user-pw>)
  Webex device xAPI (HTTP)                     POST https://roomkit.example/putxml
                                                    Authorization: Basic YXBpdXNlcjphcGlwYXNz   (= apiuser:apipass)
                                                    body: <Command><Audio><Volume><Set><Level>30</Level></Set></Volume></Audio></Command>

== B. Static key, sent on every call (no login step)
  Meraki Dashboard                             GET  https://api.meraki.com/api/v1/organizations
                                                    Authorization: Bearer <key>
  Webex (bot / integration token)              GET  https://webexapis.com/v1/people/me
                                                    Authorization: Bearer <token>

== C. Login call -> token -> header
  FMC: 1 login                                 POST https://fmc.example/api/fmc_platform/v1/auth/generatetoken
                                                    Authorization: Basic YXBpdXNlcjphcGlwYXNz   (= apiuser:apipass)
  FMC: 2 use                                   GET  https://fmc.example/api/fmc_config/v1/domain/DOMAIN_UUID/object/networks
                                                    X-auth-access-token: <token>
  FDM: 1 login                                 POST https://ftd.example/api/fdm/latest/fdm/token
                                                    body: {"grant_type": "password", "username": "apiuser", "password": "apipass"}
  FDM: 2 use                                   GET  https://ftd.example/api/fdm/latest/object/networks
                                                    Authorization: Bearer <token>
  XDR: 1 login (client credentials)            POST https://visibility.amp.cisco.com/iroh/oauth2/token
                                                    Authorization: Basic PGNsaWVudC1pZD46PHNlY3JldD4=   (= <client-id>:<secret>)
                                                    body: grant_type=client_credentials
  XDR: 2 use                                   POST https://visibility.amp.cisco.com/iroh/iroh-inspect/inspect
                                                    Authorization: Bearer <token>
                                                    body: {"content": "203.0.113.66"}
  Secure Connect / Umbrella: 1 login           POST https://api.umbrella.com/auth/v2/token
                                                    Authorization: Basic PGtleT46PHNlY3JldD4=   (= <key>:<secret>)
                                                    body: grant_type=client_credentials
  Catalyst Center: 1 login                     POST https://catc.example/dna/system/api/v1/auth/token
                                                    Authorization: Basic YXBpdXNlcjphcGlwYXNz   (= apiuser:apipass)
  Catalyst Center: 2 use                       GET  https://catc.example/dna/intent/api/v1/network-device
                                                    X-Auth-Token: <token>
  CML: 1 login                                 POST https://cml.example/api/v0/authenticate
                                                    body: {"username": "apiuser", "password": "apipass"}
  CML: 2 use                                   GET  https://cml.example/api/v0/labs
                                                    Authorization: Bearer <token>

== D. Login call -> cookie (+ a second token)
  ACI APIC: 1 login                            POST https://apic.example/api/aaaLogin.json
                                                    body: {"aaaUser": {"attributes": {"name": "apiuser", "pwd": "apipass"}}}
  ACI APIC: 2 use                              GET  https://apic.example/api/class/fabricNode.json
                                                    Cookie: APIC-cookie=<token>
  NX-API REST: 1 login                         POST https://nxos.example/api/aaaLogin.json
                                                    body: {"aaaUser": {"attributes": {"name": "apiuser", "pwd": "apipass"}}}
  SD-WAN Manager: 1 login                      POST https://manager.example:8443/j_security_check
                                                    body: j_username=apiuser&j_password=apipass
  SD-WAN Manager: 2 token                      GET  https://manager.example:8443/dataservice/client/token
                                                    Cookie: JSESSIONID=<session>
  SD-WAN Manager: 3 use                        GET  https://manager.example:8443/dataservice/device
                                                    X-XSRF-TOKEN: <xsrf>
                                                    Cookie: JSESSIONID=<session>
  UCS Manager: 1 login (XML)                   POST https://ucsm.example/nuova
                                                    body: <aaaLogin inName="apiuser" inPassword="apipass"/>
  UCS Manager: 2 use (cookie in the BODY)      POST https://ucsm.example/nuova
                                                    body: <configResolveClass cookie="<outCookie>" classId="computeBlade"/>

== E. No login: sign every request
  Intersight                                   GET  https://intersight.com/api/v1/compute/PhysicalSummaries?$top=1
                                                    Authorization: Signature keyId="<key-id>",algorithm="hs2019",headers="(request-target) host date digest",signature="<signed with your private key>"
                                                    Date: Sun, 18 Oct 2026 09:00:00 GMT
                                                    Digest: SHA-256=47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU=

== F. Key as a parameter
  Malware Analytics                            GET  https://panacea.threatgrid.com/api/v2/samples/SAMPLE_ID/state?api_key=API_KEY

== G. Not HTTP
  IOS XE / NX-OS NETCONF                       ssh -p 830 apiuser@iosxe.example -s netconf    # SSH login, then <hello> (T15)
  pyATS / Genie                                testbed.yaml (credentials, os, connections) -> device.connect()    # SSH/telnet, no API (T44)

31 requests built for 24 platforms, 7 groups, nothing sent.

== Drift check against bob/T12-T25 and T42
✓ IOS XE RESTCONF                              T16 has '/restconf/data/ietf-interfaces:interfaces'
✓ NX-OS NX-API CLI                             T17 has '/ins'
✓ NSO RESTCONF                                 T25 has 'tailf-ncs:devices/device'
✓ ISE ERS                                      T23 has '/ers/config/networkdevice'
✓ Secure Endpoint                              T23 has '/v1/computers'
✓ CUCM AXL (SOAP)                              T21 has 'SOAPAction: "CUCM:DB ver='
✓ CUCM UDS (end user)                          T21 has '/cucm-uds/'
✓ Webex device xAPI (HTTP)                     T42 has '/putxml'
✓ Meraki Dashboard                             T18 has 'Authorization: Bearer <key>'
✓ Webex (bot / integration token)              T42 has 'webexapis.com/v1'
✓ FMC: 1 login                                 T23 has 'generatetoken'
✓ FMC: 2 use                                   T23 has 'X-auth-access-token'
✓ FDM: 1 login                                 T23 has '/fdm/token'
✓ FDM: 2 use                                   T23 has '/api/fdm/latest/object/networks'
✓ XDR: 1 login (client credentials)            T23 has '/iroh/oauth2/token'
✓ XDR: 2 use                                   T23 has '/iroh/iroh-inspect/inspect'
✓ Secure Connect / Umbrella: 1 login           T23 has '/auth/v2/token'
✓ Catalyst Center: 1 login                     T20 has '/dna/system/api/v1/auth/token'
✓ Catalyst Center: 2 use                       T20 has 'X-Auth-Token'
✓ CML: 1 login                                 T25 has '/api/v0/authenticate'
✓ CML: 2 use                                   T25 has '/api/v0/labs'
✓ ACI APIC: 1 login                            T19 has 'aaaLogin.json'
✓ ACI APIC: 2 use                              T19 has 'APIC-cookie'
✓ NX-API REST: 1 login                         T17 has 'aaaLogin.json'
✓ SD-WAN Manager: 1 login                      T22 has '/j_security_check'
✓ SD-WAN Manager: 2 token                      T22 has '/client/token'
✓ SD-WAN Manager: 3 use                        T22 has 'X-XSRF-TOKEN'
✓ UCS Manager: 1 login (XML)                   T24 has '/nuova'
✓ UCS Manager: 2 use (cookie in the BODY)      T24 has 'configResolveClass'
✓ Intersight                                   T24 has 'Signature keyId'
✓ Malware Analytics                            T23 has 'api_key'

31/31 requests match their platform note.
```

### T48.01 · Platform map

**Must cover:**

- [x] Say what each Cisco platform manages and where its API lives (controller, cloud, one device, one app)
- [x] Tell a controller API from a device API from a library
- [x] Give the old name once: Catalyst Center (DNA Center), SD-WAN Manager (vManage), Secure Endpoint (AMP), Malware Analytics (Threat Grid)

![Architecture: your script, four kinds of door, and the platforms behind them](../assets/T48/01-architecture.png)

*Pick the door first. Cloud APIs have one public URL per product. A controller has one API for many devices. A device has its own API. The blue links are the only ones your code makes.*

**Notes:**

- **Four kinds of door, one question: "how many things does this API manage, and where does it run?"**
  - **Controller** = one API in front of many devices. You talk to the controller, never to the devices.
  - **Cloud** = a vendor-hosted API with one public URL. You still hold a key or token.
  - **One device** = the box's own API. Nothing else is managed through it.
  - **App server** = an application with an API (ISE, CUCM), not a network device.
  - **Library** = no API at all: code you import to drive a device (`ncclient`, pyATS).
- **Controller API ≠ device API.** Catalyst Center manages many IOS XE devices. IOS XE RESTCONF manages one. Same router, two APIs, two auth schemes.
- Old names, once: Catalyst Center (DNA Center), SD-WAN Manager (vManage), SD-WAN Controller (vSmart), SD-WAN Validator (vBond), Secure Endpoint (AMP), Secure Malware Analytics (Threat Grid), Secure Firewall Management Center (FMC, Firepower Management Center), Secure Connect (built on Umbrella).

| Platform | Kind | API lives at | Detail |
|---|---|---|---|
| Catalyst Center (DNA Center) | controller | `https://<catc>/dna/…` | T20 |
| SD-WAN Manager (vManage) | controller | `https://<manager>:8443/dataservice/…` | T22 |
| ACI APIC | controller | `https://<apic>/api/…` | T19 |
| FMC | controller (firewalls) | `/api/fmc_config/v1/domain/{DOMAIN_UUID}/…` | T23 |
| NSO | controller (multi-vendor) | `http://<nso>:8080/restconf/data/…` | T25 |
| UCS Manager (UCSM) | controller (one UCS domain) | `https://<ucsm>/nuova` | T24 |
| CML | controller (lab) | `https://<cml>/api/v0/…` | T25 |
| Meraki Dashboard | cloud | `https://api.meraki.com/api/v1/…` | T18 |
| Intersight | cloud | `https://intersight.com/api/v1/…` | T24 |
| Webex | cloud | `https://webexapis.com/v1/…` | T42 |
| XDR | cloud | `https://visibility.amp.cisco.com/iroh/…` | T23 |
| Secure Connect (Umbrella) | cloud | `https://api.umbrella.com/…` | T23 |
| Secure Endpoint (AMP) | cloud | `https://api.amp.cisco.com/v1/…` | T23 |
| Malware Analytics (Threat Grid) | cloud | `https://panacea.threatgrid.com/api/v2/…` | T23 |
| IOS XE RESTCONF | one device | `/restconf/data/…` | T16 |
| NX-OS NX-API CLI | one device | `/ins` | T17 |
| NX-API REST | one device | `/api/…` | T17 |
| FDM | one device (FTD) | `/api/fdm/latest/…` | T23 |
| Webex device xAPI | one device | `/putxml` | T42 |
| ISE ERS | app server | `https://<ise>:9060/ers/config/…` | T23 |
| CUCM AXL | app server | `https://<cucm>:8443/axl/` | T21 |
| CUCM UDS | app server | `https://<cucm>:8443/cucm-uds/…` | T21 |
| NETCONF | library (`ncclient`) | SSH `:830`, `netconf` subsystem | T15 |
| pyATS / Genie | library | `testbed.yaml`, SSH/telnet | T44 |

### T48.02 · Auth families

**Must cover:**

- [x] Name the five login styles: Basic on every call, static key, login then token header, login then cookie, signed request
- [x] Place each platform in one family
- [x] Know the odd ones: Malware Analytics api_key parameter, UCSM cookie in the XML body, SD-WAN cookie plus X-XSRF-TOKEN

![Three login families as a sequence: token header, cookie, cookie plus XSRF](../assets/T48/05-auth-families.png)

*Left to right is the family, top to bottom is the call order. Only the FMC / Catalyst Center column puts the token in a custom header; the cookie columns need a `Session`; SD-WAN needs one extra `GET /dataservice/client/token`.*

**Notes:**

- **The family is set by what you store between calls.** That decides your code's shape: a loop of independent calls, or a `Session` that remembers.
- The program's groups A-G are the families. `A` and `B` store nothing; `C` and `D` store a token or cookie; `E` stores nothing and signs; `F` and `G` are the odd ones.

| Group | Style | Platforms | Send | Stored |
|---|---|---|---|---|
| A | Basic on **every** call | IOS XE RESTCONF, NX-API CLI, NSO, ISE ERS, Secure Endpoint, CUCM AXL / UDS, Webex xAPI | `Authorization: Basic <base64 user:pass>` | nothing |
| B | Static key | Meraki, Webex (bot / integration token) | `Authorization: Bearer <key>` | nothing |
| C | Login → token → **header** | FMC, Catalyst Center, FDM, CML, XDR, Secure Connect | FMC `X-auth-access-token` · Catalyst Center `X-Auth-Token` · others `Authorization: Bearer` | token |
| D | Login → **cookie** | ACI, NX-API REST, SD-WAN Manager, UCSM | ACI / NX-API REST `Cookie: APIC-cookie=…` · SD-WAN `JSESSIONID` + `X-XSRF-TOKEN` · UCSM `cookie="…"` in the body | cookie |
| E | Sign every request | Intersight | `Date`, `Digest`, `Authorization: Signature keyId=…` | nothing |
| F | Key as a parameter | Malware Analytics | `?api_key=…` | nothing |
| G | Not HTTP | NETCONF (SSH `:830`), pyATS / Genie | SSH login, then `<hello>` / `device.connect()` | session |

- **The odd ones.**
  - Malware Analytics: the key is a **query parameter** (`api_key`), not a header.
  - UCSM: `aaaLogin` returns `outCookie`, and every later request puts it **in the XML body** (`cookie="<outCookie>"`), not in a header.
  - SD-WAN: three calls. `POST /j_security_check` (cookie `JSESSIONID`), `GET /dataservice/client/token` (returns the XSRF token), then every call carries both. A POST without `X-XSRF-TOKEN` is the one that gets `403`.
  - FMC and Catalyst Center: the token is in a **custom header**, not `Authorization`.
  - Secure Endpoint and Secure Connect: both look like "key + secret", but Secure Endpoint **is** Basic on every call (client ID : API key), while Secure Connect swaps key + secret for a Bearer token first.
- **"Bearer" alone names no platform.** 6 of 24 use it: Meraki, Webex, FDM, CML, XDR, Secure Connect. The header **name** names the platform for FMC (`X-auth-access-token`), Catalyst Center (`X-Auth-Token`), SD-WAN (`X-XSRF-TOKEN`), ACI (`APIC-cookie`).

### T48.03 · API style and payload

**Must cover:**

- [x] Match each platform to REST/JSON, RESTCONF, NETCONF, SOAP/XML, XML over HTTP, CLI-in-JSON
- [x] Give the Content-Type or Accept value that goes with each style
- [x] Say which are single-endpoint (NX-API /ins, UCSM /nuova, AXL /axl/)

**Notes:**

| Style | Platforms | Header values | Shape |
|---|---|---|---|
| REST / JSON | Meraki, Catalyst Center, SD-WAN Manager, FMC, FDM, XDR, Secure Connect, Secure Endpoint, ISE ERS, Malware Analytics, CML, Intersight, Webex, ACI, NX-API REST | `Accept: application/json`, `Content-Type: application/json` | many URLs, one per resource, verbs = HTTP methods |
| RESTCONF | IOS XE, NSO | `Accept: application/yang-data+json` | YANG path in the URL (`/restconf/data/ietf-interfaces:interfaces`) |
| NETCONF | IOS XE, NX-OS (via `ncclient`) | none: SSH `:830`, XML RPCs | `<get-config>`, `<edit-config>`, `<commit>` |
| SOAP / XML | CUCM AXL | `Content-Type: text/xml`, `SOAPAction: "CUCM:DB ver=14.0 getPhone"` | one URL, the operation is in the XML body and the header |
| XML over HTTP | UCSM, Webex device xAPI, CUCM UDS | `Content-Type: text/xml` (UCSM, xAPI), `Accept: application/xml` (UDS) | UCSM and xAPI: one URL, method in the XML |
| CLI-in-JSON | NX-API CLI | JSON body `{"ins_api": {"type": "cli_show", "input": "show version", …}}` | CLI text goes in, structured JSON comes out |

- **Single-endpoint platforms:** NX-API CLI `/ins`, UCSM `/nuova`, CUCM AXL `/axl/`, Webex device xAPI `/putxml`. The URL never changes; **the body** says what to do.
- **Multi-URL platforms:** everything REST / RESTCONF. The URL names the resource and the HTTP method says what to do with it.
- ISE ERS needs `Accept: application/json`, otherwise it replies in XML.
- ACI and NX-API REST are REST with the **format in the URL suffix** (`.json` / `.xml`), not in a header.

### T48.04 · Addressing objects

**Must cover:**

- [x] Know how each platform names a thing: UUID, serial, DN/class, YANG path, SEP name, organizationId
- [x] Say what the first call is to find the ID you need

**Notes:**

- **Every platform has a first call that returns the ID the next call needs.** Exam questions give you the second call with a blank.

| Platform | How a thing is named | First call to find the ID |
|---|---|---|
| Meraki | `organizationId` → `networkId` → device `serial` | `GET /organizations`, then `/organizations/{id}/networks` |
| FMC | `DOMAIN_UUID` in the path, then the object's UUID | `generatetoken` reply **headers** give `DOMAIN_UUID`; `GET …/object/networks` gives object ids |
| Catalyst Center | device `id` (UUID), async `taskId` | `GET /dna/intent/api/v1/network-device`; commands return `response.taskId` |
| ACI, NX-API REST, UCSM | **DN** (`sys/chassis-1/blade-1`) + **class** (`fabricNode`, `computeBlade`) | class query: `GET /api/class/fabricNode.json`, `configResolveClass`; by DN: `GET /api/mo/<dn>.json` |
| Intersight | `Moid` + `ObjectType` | `GET /api/v1/compute/PhysicalSummaries` |
| SD-WAN Manager | `deviceId` (the system IP) | `GET /dataservice/device` |
| CUCM AXL | object name (`SEP001122334455`) | `getPhone` with `<name>` |
| CUCM UDS | user id | `GET /cucm-uds/user/{id}/devices` |
| IOS XE, NSO | **YANG path** (`ietf-interfaces:interfaces/interface=GigabitEthernet1`, `tailf-ncs:devices/device`) | `GET /restconf/data/<module>:<container>` |
| CML | lab id | `GET /api/v0/labs` |
| ISE ERS | UUID, or a `filter=mac.EQ.<mac>` lookup | `GET /ers/config/networkdevice` |
| Secure Endpoint | connector GUID (not hostname) | `GET /v1/computers` |
| Malware Analytics | sample id | `POST /api/v2/samples` returns it, then `/samples/{id}/state` |
| XDR | an observable (`{"content": "203.0.113.66"}`) | `POST /iroh/iroh-inspect/inspect` extracts observables from free text |
| Webex | `roomId`, `personId` | `GET /v1/rooms`, `GET /v1/people/me` |

- **DN vs YANG path vs UUID** is the exam's usual "how do I address it" confusion: ACI / UCSM use a **dotted tree path** (DN), RESTCONF / NETCONF use a **YANG module path**, everything else uses an **ID**.

### T48.05 · Token and session lifetimes

**Must cover:**

- [x] Quote the lifetime and refresh rule per platform (FMC 30 min / 3 refreshes, XDR 600 s, Secure Connect 3600 s, APIC cookie, Catalyst Center token)
- [x] Say which have no lifetime because nothing is stored (Basic, static key, signed)

**Notes:**

| Platform | What is stored | Lifetime | Refresh |
|---|---|---|---|
| FMC | `X-auth-access-token` + `X-auth-refresh-token` | 30 min ⚠ | refresh with **both** tokens, at most **3** times, then `generatetoken` again |
| Catalyst Center | `X-Auth-Token` | 60 min | log in again; `dnacentersdk` re-fetches once on a `401` |
| XDR | Bearer | 600 s ⚠ | none (client credentials): request a new token |
| Secure Connect | Bearer | 3600 s | none: request a new token |
| FDM | Bearer | reply carries `expires_in` | read it, don't hard-code it |
| ACI, NX-API REST | `APIC-cookie` | `refreshTimeoutSeconds` = 600 on the sandbox ⚠ | `GET /api/aaaRefresh.json` returns a new token and cookie |
| NX-API CLI | optional `nxapi_auth` cookie | `Max-Age=600` | log in again; the Basic header works every time |
| UCSM | `outCookie` | `outRefreshPeriod="600"` ⚠ | `aaaRefresh`; end with `aaaLogout` |
| SD-WAN Manager | `JSESSIONID` + XSRF token | 24 h session, 30 min idle ⚠ | log in again |
| Webex | Bearer | personal token **12 h**; bot long-lived; integration ~14 days, refresh ~90 days ⚠ | integration: `POST /v1/access_token` with a refresh token |
| Meraki | static key | none stored by the platform | you regenerate the key |
| Basic-on-every-call platforms | nothing | none | none |
| Intersight | nothing | none (a fresh signature per request) | none |

- **No lifetime = nothing stored.** Basic (group A), static key (B), signed (E) and the `api_key` parameter (F) have no login, so no expiry and no refresh. The only way they "expire" is that you revoke or rotate the credential.
- **Rate limit is not lifetime.** Meraki is 10 requests/s per organisation, then `429` + `Retry-After`. FMC also rate-limits (120/min, 10 connections ⚠).

### T48.06 · Success is not success

**Must cover:**

- [x] Spot HTTP 200 with a failure inside (SD-WAN login, UCSM, ACI missing DN)
- [x] Spot 'accepted, not done' (Catalyst Center 202 task, FMC deploy, NSO commit)
- [x] Spot analysers that do not enforce (XDR, Malware Analytics)

**Notes:**

| You see | What it means | What to check |
|---|---|---|
| SD-WAN login → `200` | a bad password still returns `200` with an HTML login page | `Content-Type` / body; did a `JSESSIONID` cookie come back? |
| UCSM → `200` | the XML body carries `errorCode` / `errorDescr` | parse the body for `errorCode` |
| ACI → `200`, `"totalCount": "0"` | the DN does not exist, or nothing matched | `totalCount` in the body |
| FMC → `201` | the object is saved but **not deployed** to the firewalls | `POST …/deployment/deploymentrequests` (`202`) |
| Catalyst Center → `202` | the job was accepted; `response.taskId` is a ticket | `GET /dna/intent/api/v1/task/{taskId}` until `endTime`; check `isError` |
| NETCONF candidate `<ok/>` | edit staged, not live | `<commit>` |
| NSO commit | one transaction across many devices; all or nothing | `check-sync`, `commit dry-run` before; a refused commit changes nothing |
| XDR / Malware Analytics → `200` | it **analysed**; nothing was blocked | the enforcing product acts (Secure Endpoint isolates, ISE quarantines, FMC blocks) |
| Meraki SDK list → 1 page | `total_pages=1` is the default | `total_pages="all"` |
| ISE ERS → XML | no `Accept: application/json` | send the header |
| Meraki → `429` | rate limit | wait `Retry-After` seconds, retry |

- **Rule:** `200` means "the server answered", not "it worked". For SD-WAN, UCSM and ACI the answer is **in the body**. For FMC, Catalyst Center and NETCONF it's a **second call**.
- **The drift check has the same weakness:** it matches a marker by substring, so `…/devices/devices` still passes for `tailf-ncs:devices/device`. A green check means "present", not "exactly right".

### T48.07 · Python entry points

**Must cover:**

- [x] Match platform to its SDK or library: meraki, requests, ncclient, pyATS, Intersight SDK
- [x] Know that a login helper (Session) belongs in a script for cookie and token platforms, not for Basic or static key

![The Session rule, offline](../assets/T48/05-auth-families.png)

*Same picture as T48.02: the stored cookie is what makes a `Session` necessary. See Examples 4 for the three prepared requests side by side.*

**Notes:**

| Platform | Python entry point | Note |
|---|---|---|
| Meraki | `meraki` · `meraki.DashboardAPI(key)` | `total_pages="all"` for every page |
| Catalyst Center | `dnacentersdk` · `DNACenterAPI` | logs in lazily, retries once on `401` |
| UCSM | `ucsmsdk` · `UcsHandle(...).login()` | |
| Intersight | `intersight` | signing is built in (`HttpSigningConfiguration`) |
| CML | `virl2_client` | |
| NETCONF | `ncclient` · `ncclient.manager.connect()` | XML in, XML out |
| Webex | `webexpythonsdk` (formerly `webexteamssdk`) | |
| pyATS / Genie | pyATS, `testbed.yaml`, `device.connect()` | SSH / telnet, parses CLI output |
| FMC, FDM, ACI, SD-WAN Manager, ISE, XDR, Secure Connect, Secure Endpoint, Malware Analytics, IOS XE RESTCONF, NSO, NX-API, CUCM, xAPI | `requests` | no SDK in the blueprint |

- **`requests.Session()` is the rule for groups C and D.** It stores the login cookie (ACI, NX-API REST, SD-WAN) and the headers you set once (`session.headers.update({"X-Auth-Token": token})`), so you log in once and every later call carries them.
- **Not for A and B.** Basic is sent on every call with `auth=(user, pass)`, and a static key is one header. A `Session` does no harm, but it isn't needed.
- A plain `requests.get()` after an ACI login **forgets the cookie** → `403` (T19). `labs/T48/session_demo.py` shows it without a network.
- **Library vs SDK vs plain HTTP:** `meraki`, `dnacentersdk`, `ucsmsdk` wrap one platform's REST API. `ncclient` and pyATS aren't REST at all. Everything else is `requests`.

### T48.08 · Exam angle: pick the platform

**Must cover:**

- [x] From a scenario, pick the platform
- [x] From a header or URL, name the platform
- [x] Order login, use and refresh calls for a given family

![Decision flow: from a clue to the platform](../assets/T48/04-pick-platform.png)

*Start at the top with what the question gives you (a header, a URL, a job) and follow the answer. Blue = the platform to pick.*

**Notes:**

| Clue | Platform |
|---|---|
| `X-auth-access-token` | FMC |
| `X-Auth-Token`, `/dna/intent/api/v1/…` | Catalyst Center (DNA Center) |
| `APIC-cookie`, `/api/aaaLogin.json`, DN | ACI APIC (or NX-API REST on one switch) |
| `JSESSIONID` + `X-XSRF-TOKEN`, `/dataservice` | SD-WAN Manager (vManage) |
| `/nuova`, `aaaLogin`, `outCookie` | UCS Manager |
| `Authorization: Signature keyId=…`, `Digest` | Intersight |
| `?api_key=`, sandbox, threat score | Malware Analytics (Threat Grid) |
| `/ins`, `ins_api`, `cli_show` | NX-API CLI |
| `SOAPAction`, `/axl/` | CUCM AXL |
| `organizationId`, `Authorization: Bearer`, `429`, `Retry-After` | Meraki |

**Call order per family:**

| Family | Order |
|---|---|
| A. Basic | call, call, call (credentials every time) |
| B. Static key | call, call, call (key every time) |
| C. Token header | **login** → read the token (FMC: response **headers**; Catalyst Center: body `["Token"]`) → **use** with the header → on `401`, log in again (FMC: refresh up to 3 times first) |
| D. Cookie | **login** (a `Session` keeps the cookie) → **use** → refresh before the timeout. SD-WAN: login → `GET /client/token` → use with both. UCSM: login → use with the cookie in the body |
| E. Signed | build `Date` + `Digest` → sign → send; every call |
| F. Parameter | add `api_key` to every call |
| G. SSH | connect → `<hello>` (NETCONF) → `<lock>` → `<edit-config>` → `<commit>` → `<unlock>` |
| FMC full run | `generatetoken` → read headers → use → `deploymentrequests` |

- **Header → platform beats Bearer → platform.** `Authorization: Bearer` gives you six candidates; `X-Auth-Token` gives you one.
- **Jobs, not words:** "rules on many firewalls" → FMC, "one firewall, no manager" → FDM, "NAC, 802.1X, quarantine" → ISE, "isolate a laptop" → Secure Endpoint, "sandbox" → Malware Analytics, "correlate across products" → XDR, "all the switches in the fabric" → ACI, "branch WAN overlay" → SD-WAN Manager, "many vendors, one transaction" → NSO.

## Exam traps

- **"Bearer" names no platform.** Six of 24: Meraki, Webex, FDM, CML, XDR, Secure Connect. FMC (`X-auth-access-token`) and Catalyst Center (`X-Auth-Token`) are **not** Bearer.
- **FMC `X-auth-access-token` ≠ Catalyst Center `X-Auth-Token`.** Different spelling, different platform. FMC reads the token from the **response headers** of `generatetoken` (`204`, empty body); Catalyst Center reads it from the **body** (`["Token"]`, capital T).
- **FMC vs FDM:** FMC = many firewalls, header token, `/api/fmc_config/…`. FDM = one firewall, Bearer token, `/api/fdm/latest/…`.
- **FMC `201` ≠ live.** `POST …/deployment/deploymentrequests` (`202`) pushes it to the firewalls.
- **Catalyst Center `202` = a task, not a result.** Poll `GET /dna/intent/api/v1/task/{taskId}`.
- **SD-WAN login returns `200` on failure** (HTML login page). Success = a `JSESSIONID`. POST needs `X-XSRF-TOKEN` from `GET /dataservice/client/token`, or `403`.
- **UCSM cookie goes in the XML body,** and errors come back as `200` with `errorCode`.
- **ACI missing DN = `200` with `totalCount 0`,** not `404`. A plain `requests.get()` after login forgets the cookie → `403`.
- **Intersight has no login and no token:** each request is signed (`Date`, `Digest`, `Authorization: Signature keyId=…`).
- **Malware Analytics' key is a query parameter** (`api_key`), not a header. It analyses and never blocks, and it's async: poll `state`.
- **XDR is orchestration, not enforcement.** Its token request is a **form** body (`grant_type=client_credentials`), 600 s, no refresh token.
- **Secure Endpoint = Basic (client ID : API key). Secure Connect = key + secret → Bearer.** Opposite behaviours for look-alike credentials.
- **ISE ERS = port 9060, Basic every call, `Accept: application/json`.** Without it, XML.
- **Webex personal token = 12 h.** A script that "worked yesterday" and gets `401` today needs a bot token or integration.
- **Meraki SDK returns page 1 unless `total_pages="all"`.** 10 requests/s per org, then `429` + `Retry-After`.
- **RESTCONF `PUT` replaces the whole resource;** a leaf you leave out is deleted. Use `PATCH` to merge (T16).
- **NETCONF candidate `<ok/>` is not live until `<commit>`.** NSO is all-or-nothing; use `check-sync` and `dry-run`.

## Examples

### 1. Run the reference program

```bash
python3 -m pip install requests
bash labs/T48/run_lab.sh
```

In the lab container (`requests` is already in the image):

```bash
docker build --tag ccna-auto-lab:latest --file labs/Dockerfile labs/
docker run --rm --volume "$(pwd)":/work --workdir /work ccna-auto-lab:latest bash labs/T48/run_lab.sh
```

- Nothing is sent, so there's nothing to point at a real product. The output is the table in Concepts.

### 2. Pick two platforms, or list the keys

```bash
python3 labs/T48/auth_side_by_side.py --only fmc,catc
```

```text
== C. Login call -> token -> header
  FMC: 1 login                                 POST https://fmc.example/api/fmc_platform/v1/auth/generatetoken
                                                    Authorization: Basic YXBpdXNlcjphcGlwYXNz   (= apiuser:apipass)
  FMC: 2 use                                   GET  https://fmc.example/api/fmc_config/v1/domain/DOMAIN_UUID/object/networks
                                                    X-auth-access-token: <token>
  Catalyst Center: 1 login                     POST https://catc.example/dna/system/api/v1/auth/token
                                                    Authorization: Basic YXBpdXNlcjphcGlwYXNz   (= apiuser:apipass)
  Catalyst Center: 2 use                       GET  https://catc.example/dna/intent/api/v1/network-device
                                                    X-Auth-Token: <token>

4 requests built for 2 platforms, 1 group, nothing sent.
```

```bash
python3 labs/T48/auth_side_by_side.py --list
```

```text
aci
axl
catc
cml
fdm
fmc
intersight
iosxe
ise
meraki
netconf
nso
nxapi-cli
nxapi-rest
pyats
sdwan
se
sma
ucsm
uds
umbrella
webex
xapi-http
xdr
```

- FMC and Catalyst Center are both "login → token → header", but the **header names differ**.

### 3. Break it on purpose

Save a copy first (`cp labs/T48/auth_side_by_side.py /tmp/keep.py`), edit `labs/T48/auth_side_by_side.py`, run `bash labs/T48/run_lab.sh`, then copy the saved file back (`cp /tmp/keep.py labs/T48/auth_side_by_side.py`). The file is new, so `git checkout` can't restore it. The results below are the real output of `check_drift.py`.

| # | Edit | Result | Lesson |
|---|---|---|---|
| 1 | In the NSO step, change the URL `…/restconf/data/tailf-ncs:devices/device` to `…/restconf/data/tailf-ncs:devices` | `✗ NSO RESTCONF` then `the program's request has no 'tailf-ncs:devices/device'` and `30/31 requests match their platform note.` (exit 1) | the program can't drift from the note without the check noticing |
| 2 | In the Meraki step, change `{"Authorization": "Bearer <key>"}` to `{"X-Auth-Token": "<key>"}` | `✗ Meraki Dashboard` then `the program's request has no 'Authorization: Bearer <key>'` and `30/31 requests match their platform note.` | Meraki is Bearer; `X-Auth-Token` would be a different platform |
| 3 | In the Malware Analytics step, change `params={"api_key": "API_KEY"}` to `params={"key": "API_KEY"}` | `✗ Malware Analytics` then `the program's request has no 'api_key'` and `30/31 requests match their platform note.` | the parameter name is part of the API |
| 4 | Change the NSO URL to `…/tailf-ncs:devices/devices` | still `31/31`: the marker `tailf-ncs:devices/device` is a substring of `devices/devices` | a substring match proves "present", not "exact" |

Edit 4 is a weakness of `check_drift.py`, not a feature. It's listed in To verify.

### 4. Why a cookie platform needs a Session (`labs/T48/session_demo.py`)

```python
#!/usr/bin/env python3
"""T48.07: why cookie and token platforms need a requests.Session(), and Basic ones do not.

Builds requests offline (nothing is sent). A Session keeps the login cookie and adds it to
every later request; plain requests.Request(...) forgets it.

  python3 labs/T48/session_demo.py
"""
import requests

URL = "https://apic.example/api/class/fabricNode.json"

# Pretend the aaaLogin.json reply already set this cookie on the session.
s = requests.Session()
s.cookies.set("APIC-cookie", "<token>", domain="apic.example")

with_session = s.prepare_request(requests.Request("GET", URL))
plain = requests.Request("GET", URL).prepare()
basic = requests.Request("GET", "https://ise.example:9060/ers/config/networkdevice",
                         auth=("apiuser", "apipass")).prepare()

print("ACI, Session   :", with_session.headers.get("Cookie"))
print("ACI, plain     :", plain.headers.get("Cookie"))
print("ISE, plain     :", basic.headers.get("Authorization", "")[:12] + "...", "(no Session needed)")
```

```bash
python3 labs/T48/session_demo.py
```

```text
ACI, Session   : APIC-cookie=<token>
ACI, plain     : None
ISE, plain     : Basic YXBpdX... (no Session needed)
```

- ACI: the `Session` adds `Cookie: APIC-cookie=<token>`; the plain request has none, so the APIC would answer `403`.
- ISE: Basic is built into each call, so no `Session` is needed.

## Practice questions

**Q1.** Complete the code so that the script gets a Catalyst Center token and lists devices.

```python
resp = requests.post("https://catc.example/dna/system/api/v1/auth/token",
                     auth=(user, password), verify=False)
token = resp.json()["Token"]
devs = requests.get("https://catc.example/dna/intent/api/v1/network-device",
                    headers={"__________": token}, verify=False)
```

<details><summary>Answer</summary>

**`X-Auth-Token`.** Catalyst Center takes the token in its own header, not `Authorization: Bearer`. FMC's is `X-auth-access-token`. (T48.02, T48.08)
</details>

**Q2.** A script logs in to SD-WAN Manager with `POST /j_security_check`, gets `200` and a `JSESSIONID`, then `POST`s a change and gets `403`. What is missing?
A. A Bearer token from `/auth/v2/token`  B. The `X-XSRF-TOKEN` header from `GET /dataservice/client/token`  C. An `APIC-cookie`  D. A `DOMAIN_UUID`

<details><summary>Answer</summary>

**B.** SD-WAN Manager needs a cookie **and** an XSRF token. A POST without `X-XSRF-TOKEN` is rejected with `403`. The other options are Secure Connect, ACI and FMC. (T48.02)
</details>

**Q3.** Which platform has no login call, no token and no key sent on the request, and instead signs each request with `Date`, `Digest` and `Authorization: Signature keyId=…`?
A. Meraki  B. Catalyst Center  C. Intersight  D. UCS Manager

<details><summary>Answer</summary>

**C.** Intersight signs every request. Meraki sends a static Bearer key, Catalyst Center logs in for an `X-Auth-Token`, UCSM logs in for an `outCookie`. (T48.02, T48.05)
</details>

**Q4.** A script posts a UCSM request to `/nuova`, gets `200 OK` and reports success, but nothing changed. Why?

<details><summary>Answer</summary>

UCSM answers `200` even when the request failed. The failure is in the XML body as `errorCode` / `errorDescr`. Parse the body. The same pattern: SD-WAN login (`200` + HTML page) and ACI (`200`, `totalCount 0` for a missing DN). (T48.06)
</details>

**Q5.** Put the FMC calls in order: (a) `POST …/deployment/deploymentrequests` (b) `POST /api/fmc_platform/v1/auth/generatetoken` (c) `POST` the new rule with `X-auth-access-token` (d) read `X-auth-access-token` and `DOMAIN_UUID` from the response headers.

<details><summary>Answer</summary>

**b, d, c, a.** Log in with Basic, read the token and domain from the **headers**, make the change (`201`), then deploy (`202`). Without (a) the firewalls don't change. (T48.06, T48.08)
</details>

**Q6.** A script uploads a suspicious file to a sandbox, passes the key as `?api_key=…`, and polls until the state is `succ`. Which platform?
A. Secure Endpoint  B. XDR  C. Malware Analytics (Threat Grid)  D. ISE

<details><summary>Answer</summary>

**C.** A sandbox with an `api_key` parameter is Malware Analytics. Secure Endpoint uses Basic auth, XDR a Bearer token, ISE Basic on port 9060. Malware Analytics only analyses; blocking is done by the enforcing product. (T48.02, T48.06)
</details>

**Q7.** A Webex script used a token copied from the developer portal. It worked yesterday, and returns `401` this morning. What is the likely cause and the fix?

<details><summary>Answer</summary>

A personal access token expires after **12 hours**. Use a bot token (long-lived) or an integration (OAuth, refreshable). (T48.05)
</details>

**Q8.** A request carries `Authorization: Bearer abc123`. Which statement is correct?
A. It must be Meraki  B. It must be FMC  C. It must be Catalyst Center  D. It could be any of Meraki, Webex, FDM, CML, XDR or Secure Connect

<details><summary>Answer</summary>

**D.** Six of the 24 platforms use Bearer. FMC uses `X-auth-access-token` and Catalyst Center `X-Auth-Token`, so neither is Bearer. The header **name** (or the URL) names the platform, not the word Bearer. (T48.02, T48.08)
</details>

## Study aids

None. T48 is a synthesis note: `data/study-aids.csv` has no T48 rows and there is no CBT video for it. The material is T12-T25 and T42, with the study aids listed in each of those notes.

## Sources

- Overview image: HTML source `assets/T48/00-overview.html`, rendered to PNG (see `assets/README.md`). Diagrams: Mermaid sources in `assets/T48/04-*.mmd`, `05-*.mmd`. Architecture diagram: HTML source `assets/T48/01-architecture.html` (shared kit `assets/_arch/`).
- T48 adds no new platform facts: the links below are the official sources already used in the sibling notes, picked for auth, API style and lifetimes. Each sibling note lists the rest.
- Meraki: https://developer.cisco.com/meraki/api-v1/authorization/ · https://developer.cisco.com/meraki/api-v1/rate-limit/ · https://developer.cisco.com/meraki/api-v1/pagination/
- Catalyst Center (DNA Center) authentication and Get Task by ID: https://developer.cisco.com/docs/catalyst-center/authentication · https://developer.cisco.com/docs/catalyst-center/get-task-by-id
- SD-WAN Manager (vManage) API authentication (session, `X-XSRF-TOKEN`, 24 h / 30 min idle) and API Cross-Site Request Forgery Prevention: Cisco Catalyst SD-WAN documentation on developer.cisco.com/docs/sdwan
- ACI APIC REST API configuration guide (`aaaLogin`, `APIC-cookie`, `aaaRefresh`); UCS Manager XML API Programmer's Guide (`/nuova`, `aaaLogin`, `outRefreshPeriod`); Intersight API authentication: https://developer.cisco.com/docs/intersight/
- RESTCONF RFC 8040: https://www.rfc-editor.org/rfc/rfc8040 · NETCONF RFC 6241: https://www.rfc-editor.org/rfc/rfc6241 · NETCONF over SSH RFC 6242: https://www.rfc-editor.org/rfc/rfc6242
- Secure Firewall Management Center REST API Quick Start Guide 7.7 (`generatetoken`, `X-auth-access-token`, 30 min, 3 refreshes): https://www.cisco.com/c/en/us/td/docs/security/firepower/770/API/REST/secure_firewall_management_center_rest_api_quick_start_guide_770/Connecting_With_A_Client.html
- FTD REST API authentication (FDM): https://www.cisco.com/c/en/us/td/docs/security/firepower/ftd-api/guide/ftd-rest-api/auth-ftd-rest-api.html
- ISE: https://developer.cisco.com/identity-services-engine · Secure Endpoint: https://developer.cisco.com/docs/secure-endpoint/overview · Malware Analytics (Threat Grid): https://developer.cisco.com/threat-grid · XDR OAuth2 client credentials: https://developer.cisco.com/docs/cisco-xdr/oauth2-client-credentials-scripts · Secure Connect / Umbrella: https://developer.cisco.com/docs/cloud-security/quick-start
- CUCM AXL: https://developer.cisco.com/docs/axl/ · UDS: https://developer.cisco.com/docs/user-data-services/
- Webex: https://developer.webex.com/docs/getting-started · https://developer.webex.com/docs/understanding-oauth-flow-of-webex-integration · https://developer.webex.com/docs/bots · device xAPI: https://roomos.cisco.com/doc/TechDocs/xAPI
- Platform notes this one summarises: [T12](T12-automation-foundations-controller-vs-device.md) · [T15](T15-netconf.md) · [T16](T16-restconf.md) · [T17](T17-iosxe-nxos-device-apis.md) · [T18](T18-meraki.md) · [T19](T19-aci.md) · [T20](T20-catalyst-center-dna-center.md) · [T21](T21-collaboration-cucm-axl-uds.md) · [T22](T22-catalyst-sd-wan.md) · [T23](T23-security-platforms.md) · [T24](T24-compute-ucs-manager-intersight.md) · [T25](T25-nso-cisco-modeling-labs.md) · [T42](T42-webex-webex-devices.md) · [T44](../bee/T44-pyats-genie.md)
- Python `requests` (`Request`, `prepare()`, `Session`): https://requests.readthedocs.io/en/latest/user/advanced/#session-objects
- Cisco 200-901 v1.1 exam topics (3.1-3.6, 3.9): https://learningcontent.cisco.com/documents/marketing/exam-topics/200-901-CCNAAUTO_v.1.1.pdf

## To verify

- ⚠ **Nothing ran against a live product.** `labs/T48/auth_side_by_side.py` builds requests and sends nothing. Every endpoint, header and lifetime is taken from the sibling notes, which ran against mocks or the DevNet sandboxes. Their own To verify lists apply here too.
- ⚠ **Lifetimes:** FMC 30 min / 3 refreshes and rate limit; XDR 600 s (a Cisco doc example); APIC and UCSM 600 s (sandbox / guide values); Webex integration ~14 days and refresh ~90 days; SD-WAN 24 h / 30 min idle. Confirm against the version you study.
- ⚠ **ISE ERS port 9060 vs 443:** 9060 is the classic port; ISE 3.1+ also serves ERS on 443.
- ⚠ **SD-WAN `X-XSRF-TOKEN`:** which methods require it. T22 says a POST without it is `403`. The program sends it on a `GET`; confirm what each method needs.
- ⚠ **Intersight signature details:** `hs2019`, the signed header list and the `Date` format are modelled in the program. The Intersight SDK builds them for you, and T24's own `rsa-sha256` source differs by key version. Not exercised here.
- ⚠ **UCSM error codes** (`errorCode` 551 / 552) are from the Programmer's Guide and the CIMC doc; the program doesn't use them.
- ⚠ **pyATS / Genie** (`testbed.yaml`, `device.connect()`) and the SDK names (`dnacentersdk`, `ucsmsdk`, `intersight`, `virl2_client`, `webexpythonsdk`) were not run here.
- ⚠ **`check_drift.py` matches markers by substring** (Examples 3, edit 4). `…/devices/devices` passes for `tailf-ncs:devices/device`. A green check means "present".
- ⚠ **Python 3.10.** The lab was run on the system Python 3.10.12, so it uses no nested same-quote f-strings. The urllib3 / chardet `RequestsDependencyWarning` on this machine is environmental; `run_lab.sh` hides it.
- ⚠ **Docker command not run.** The lab image wasn't built in this session. The program needs only `requests`, which is already in the image.
- ⚠ Blueprint 3.1-3.6 and 3.9 wording is paraphrased in `data/blueprint-map.csv`; check it in the Cisco PDF.
