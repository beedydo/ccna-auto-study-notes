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
