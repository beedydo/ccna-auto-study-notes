"""T12 reference program: one job, done three ways.

    Job: "at site SG-HQ, shut every unused (oper-status DOWN) switch port and label it UNUSED"

    1-2  screen-scrape CLI text vs read a YANG model (why model-driven)
    3    the programmability stack inside one request
    4    the model validates a bad edit before anything is applied
    5    device-level: the script talks to every switch itself
    6-7  controller-level: one intent to the controller, which programs the switches

Default target is the local mock (python3 labs/T12/mock_network.py).
"""
import os
import re
from urllib.parse import quote

import requests

BASE = os.environ.get("T12_BASE_URL", "http://127.0.0.1:18012")
AUTH = (os.environ.get("T12_USER", "admin"), os.environ.get("T12_PASS", "C1sco12345"))
YANG_JSON = "application/yang-data+json"
OC_IF = "openconfig-interfaces:interfaces"

SWITCHES = {                                   # what a device-level script must know itself
    "sw1": {"os": "iosxe", "cli": "show ip interface brief"},
    "sw2": {"os": "iosxe", "cli": "show ip interface brief"},
    "sw3": {"os": "nxos", "cli": "show interface brief"},
}
IOSXE_ROW = re.compile(r"^(\S+)\s+\S+\s+YES\s+\S+\s+(up|down|administratively down)\s+(up|down)\s*$")

calls = {"n": 0}
session = requests.Session()
session.auth = AUTH
session.hooks["response"].append(lambda r, *a, **k: calls.__setitem__("n", calls["n"] + 1))


def scrape_ports(dev):
    """T12.02 the old way: send a show command, regex the text."""
    text = session.get(f"{BASE}/{dev}/cli", params={"cmd": SWITCHES[dev]["cli"]}, timeout=10).text
    return [(m.group(1), m.group(3)) for line in text.splitlines() if (m := IOSXE_ROW.match(line))]


def model_ports(dev):
    """T12.02 the model-driven way: GET the OpenConfig model, read keys out of JSON."""
    r = session.get(f"{BASE}/{dev}/restconf/data/{OC_IF}", headers={"Accept": YANG_JSON}, timeout=10)
    r.raise_for_status()
    return [(i["name"], i["state"]["oper-status"], i["config"]["enabled"]) for i in r.json()[OC_IF]["interface"]]


def patch_port(dev, ifname, config):
    """RESTCONF merge on one interface's config container. '/' in the key must be %2F."""
    url = f"{BASE}/{dev}/restconf/data/{OC_IF}/interface={quote(ifname, safe='')}/config"
    return session.patch(url, json={"openconfig-interfaces:config": config},
                         headers={"Content-Type": YANG_JSON, "Accept": YANG_JSON}, timeout=10)


def main():
    session.post(f"{BASE}/_mock/reset", timeout=10)

    print("== 1. Screen-scraping: one regex, two operating systems ==")
    for dev in ("sw1", "sw3"):
        ports = scrape_ports(dev)
        print(f"    {dev} ({SWITCHES[dev]['os']:<5}) '{SWITCHES[dev]['cli']}' -> {len(ports)} ports parsed {ports[:2]}")

    print("\n== 2. Model-driven: same code, same model, every switch ==")
    for dev in SWITCHES:
        ports = model_ports(dev)
        print(f"    {dev} ({SWITCHES[dev]['os']:<5}) -> {len(ports)} ports {[(n, s) for n, s, _ in ports[:2]]}")

    print("\n== 3. The stack inside one request ==")
    r = patch_port("sw1", "GigabitEthernet1/0/2", {"description": "bob-laptop"})
    print(f"    {r.request.method} {r.request.path_url}")
    print("    model    : openconfig-interfaces (YANG)")
    print(f"    encoding : JSON   (Content-Type: {r.request.headers['Content-Type']})")
    print(f"    protocol : RESTCONF -> {r.status_code} {r.reason}")
    print("    transport: HTTP here; HTTPS on a real switch")

    print("\n== 4. Validation: the model rejects a bad value, nothing is applied ==")
    r = patch_port("sw1", "GigabitEthernet1/0/3", {"description": "UNUSED", "enabled": "no"})
    err = r.json()["ietf-restconf:errors"]["error"][0]
    print(f"    {r.status_code} {err['error-tag']}: {err['error-message']}")
    gi3 = next(p for p in model_ports("sw1") if p[0] == "GigabitEthernet1/0/3")
    print(f"    GigabitEthernet1/0/3 after the failed edit: enabled={gi3[2]} (description not changed either)")

    print("\n== 5. Device-level: the script loops over every switch itself ==")
    calls["n"] = 0
    for dev in SWITCHES:
        for name, oper, enabled in model_ports(dev):
            if oper == "DOWN" and enabled:
                r = patch_port(dev, name, {"description": "UNUSED (script)", "enabled": False})
                print(f"    {dev} PATCH {name:<22} -> {r.status_code}")
    print(f"    HTTP calls made by the script: {calls['n']}")

    session.post(f"{BASE}/_mock/reset", timeout=10)
    print("\n== 6. Controller-level: one intent, the controller does the southbound work ==")
    calls["n"] = 0
    r = session.post(f"{BASE}/ctrl/api/v1/intents", json={"intent": "disable-unused-ports", "site": "SG-HQ"}, timeout=10)
    print(f"    POST /ctrl/api/v1/intents -> {r.status_code} {r.reason}, taskId {r.json()['taskId'][:8]}...")
    task = session.get(BASE + r.json()["url"], timeout=10).json()
    print(f"    task {task['status']}: {len(task['southbound'])} ports changed on {task['devices']} devices")
    for a in task["southbound"]:
        print(f"      southbound {a['protocol']} {a['method']} {a['device']} {a['interface']:<22} -> {a['result']}")
    print(f"    HTTP calls made by the script: {calls['n']}")

    print("\n== 7. Network-wide view from the controller ==")
    for d in session.get(f"{BASE}/ctrl/api/v1/devices", timeout=10).json()["response"]:
        print(f"    {d['hostname']}  {d['platform']:<17} {d['softwareVersion']:<15} portsAdminDown={d['portsAdminDown']}")


if __name__ == "__main__":
    main()
