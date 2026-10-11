"""T16 reference program: one RESTCONF session against an IOS XE device.

Discover the root, read interfaces (whole list, one entry, one leaf, filtered),
create / merge / replace / delete a loopback, trigger the common errors, then save.

Mock device:  bash labs/T16/run_lab.sh      (starts labs/T16/mock_restconf.py first)
Real device:  RESTCONF_HOST=<ip-or-name> RESTCONF_USER=<user> RESTCONF_PASS=<pass> \
              python3 labs/T16/restconf_client.py
"""
import json
import os
from urllib.parse import quote

import requests
import urllib3

HOST = os.environ.get("RESTCONF_HOST", "127.0.0.1:9443")
AUTH = (os.environ.get("RESTCONF_USER", "admin"), os.environ.get("RESTCONF_PASS", "C1sco12345"))
BASE = f"https://{HOST}/restconf"                      # API root (found via host-meta)
IFACES = f"{BASE}/data/ietf-interfaces:interfaces"     # <module>:<container>
HEADERS = {"Accept": "application/yang-data+json",     # what I want back
           "Content-Type": "application/yang-data+json"}  # what I am sending

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # self-signed cert


def iface_url(name):
    """List entry URI: list=key, with '/' in the key percent-encoded as %2F."""
    return f"{IFACES}/interface={quote(name, safe='')}"


def show(r, pretty=False):
    """Print request line, status line, key headers and the body."""
    print(f"\n>>> {r.request.method} {r.request.url}")
    print(f"<<< {r.status_code} {r.reason}")
    for name in ("Content-Type", "Location", "WWW-Authenticate"):
        if name in r.headers:
            print(f"    {name}: {r.headers[name]}")
    if r.text:
        if pretty or "json" not in r.headers.get("Content-Type", ""):
            print("    " + r.text.strip().replace("\n", "\n    "))
        else:
            print("    " + json.dumps(r.json(), separators=(",", ":")))
    return r


LOOPBACK = {"ietf-interfaces:interface": {
    "name": "Loopback100",
    "description": "Created by RESTCONF",
    "type": "iana-if-type:softwareLoopback",
    "enabled": True,
    "ietf-ip:ipv4": {"address": [{"ip": "10.255.100.1", "netmask": "255.255.255.255"}]},
}}


def main():
    print("== 1. Discover the API root ==")
    show(requests.get(f"https://{HOST}/.well-known/host-meta", verify=False))
    show(requests.get(BASE, auth=AUTH, headers=HEADERS, verify=False))
    show(requests.get(IFACES, headers=HEADERS, verify=False))        # 401: forgot auth=

    print("\n== 2. Read (GET) ==")
    r = show(requests.get(iface_url("GigabitEthernet1"), auth=AUTH, headers=HEADERS, verify=False),
             pretty=True)
    gi1 = r.json()["ietf-interfaces:interface"]
    print(f"    -> parsed: {gi1['name']} ip={gi1['ietf-ip:ipv4']['address'][0]['ip']} "
          f"oper={gi1['oper-status']}")
    show(requests.get(IFACES + "?fields=interface(name;enabled)", auth=AUTH, headers=HEADERS, verify=False))
    show(requests.get(iface_url("GigabitEthernet2") + "?content=nonconfig",
                      auth=AUTH, headers=HEADERS, verify=False))
    show(requests.get(iface_url("GigabitEthernet2") + "/description",
                      auth=AUTH, headers=HEADERS, verify=False))
    show(requests.get(iface_url("GigabitEthernet2"), auth=AUTH, verify=False,
                      headers={"Accept": "application/yang-data+xml"}))

    print("\n== 3. Create (POST to the parent) ==")
    show(requests.post(IFACES, auth=AUTH, headers=HEADERS, json=LOOPBACK, verify=False))   # 201
    show(requests.post(IFACES, auth=AUTH, headers=HEADERS, json=LOOPBACK, verify=False))   # 409

    print("\n== 4. Update: PATCH merges, PUT replaces ==")
    patch = {"ietf-interfaces:interface": {"name": "Loopback100", "description": "Merged by PATCH"}}
    show(requests.patch(iface_url("Loopback100"), auth=AUTH, headers=HEADERS, json=patch, verify=False))
    show(requests.get(iface_url("Loopback100"), auth=AUTH, headers=HEADERS, verify=False))
    put = {"ietf-interfaces:interface": {"name": "Loopback100", "type": "iana-if-type:softwareLoopback",
                                         "enabled": False}}
    show(requests.put(iface_url("Loopback100"), auth=AUTH, headers=HEADERS, json=put, verify=False))
    show(requests.get(iface_url("Loopback100"), auth=AUTH, headers=HEADERS, verify=False))
    put["ietf-interfaces:interface"]["name"] = "Loopback101"
    show(requests.put(iface_url("Loopback101"), auth=AUTH, headers=HEADERS, json=put, verify=False))

    print("\n== 5. Errors you must recognise ==")
    bad = {"ietf-interfaces:interface": {"name": "Loopback100", "enabled": "yes"}}
    show(requests.patch(iface_url("Loopback100"), auth=AUTH, headers=HEADERS, json=bad, verify=False))
    show(requests.post(IFACES, auth=AUTH, json=LOOPBACK, verify=False,
                       headers={"Accept": "application/yang-data+json", "Content-Type": "application/json"}))
    show(requests.get(iface_url("Loopback100"), auth=AUTH, verify=False,
                      headers={"Accept": "application/json"}))
    show(requests.get(f"{IFACES}/interface=GigabitEthernet1/0/1", auth=AUTH, headers=HEADERS, verify=False))
    show(requests.get(iface_url("GigabitEthernet1/0/1"), auth=AUTH, headers=HEADERS, verify=False))

    print("\n== 6. Delete, then save ==")
    show(requests.delete(iface_url("Loopback101"), auth=AUTH, headers=HEADERS, verify=False))   # 204
    show(requests.delete(iface_url("Loopback101"), auth=AUTH, headers=HEADERS, verify=False))   # 404
    show(requests.post(f"{BASE}/operations/cisco-ia:save-config", auth=AUTH, headers=HEADERS, verify=False))


if __name__ == "__main__":
    main()
