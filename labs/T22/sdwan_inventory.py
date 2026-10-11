"""T22 reference program: SD-WAN Manager (vManage) login, inventory and health report.

Live DevNet sandbox (default):  python3 labs/T22/sdwan_inventory.py
Offline mock:                   bash labs/T22/run_lab.sh
Read-only: the POSTs below are queries (statistics, alarms); nothing is created or changed.
"""
import os
import sys
from collections import Counter

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # sandbox cert is self-signed

SCHEME = os.environ.get("SDWAN_SCHEME", "https")
HOST = os.environ.get("SDWAN_HOST", "sandbox-sdwan-2.cisco.com")
PORT = os.environ.get("SDWAN_PORT", "443")            # on-prem default is 8443; the sandbox uses 443
USER = os.environ.get("SDWAN_USER", "devnetuser")     # public DevNet sandbox defaults, env vars win
PASSWORD = os.environ.get("SDWAN_PASS", "RG!_Yw919_83")

BASE = f"{SCHEME}://{HOST}:{PORT}"                    # login and logout live at the root
API = f"{BASE}/dataservice"                           # every REST resource lives under /dataservice

NEW_NAME = {"vmanage": "SD-WAN Manager", "vsmart": "SD-WAN Controller",
            "vbond": "SD-WAN Validator", "vedge": "WAN Edge"}   # API device-type -> current name


def login(session):
    """Step 1: form POST to /j_security_check. Success = empty body + JSESSIONID cookie."""
    resp = session.post(f"{BASE}/j_security_check",
                        data={"j_username": USER, "j_password": PASSWORD})  # data= -> form-encoded
    if resp.status_code != 200 or resp.text.strip():     # a FAILED login is also HTTP 200, with a body
        sys.exit(f"Login failed: HTTP {resp.status_code}, body: {resp.text.strip()[:60]!r}")
    print(f"1. POST /j_security_check -> {resp.status_code}, empty body, "
          f"JSESSIONID cookie stored: {'JSESSIONID' in session.cookies}")


def get_xsrf_token(session):
    """Step 2: GET the XSRF token (plain text body) and send it on every later request."""
    resp = session.get(f"{API}/client/token")
    resp.raise_for_status()
    session.headers["X-XSRF-TOKEN"] = resp.text
    print(f"2. GET /dataservice/client/token -> {resp.status_code}, "
          f"{len(resp.text)}-char token, now sent as X-XSRF-TOKEN")


def get(session, path, params=None):
    """GET /dataservice<path> and return the "data" list (the "header" key is column metadata)."""
    resp = session.get(f"{API}{path}", params=params)
    resp.raise_for_status()
    if "json" not in resp.headers.get("Content-Type", ""):   # dead session -> 200 + HTML login page
        sys.exit(f"GET {path}: HTTP {resp.status_code} but HTML, not JSON (session expired?)")
    return resp.json()["data"]


def query(session, path, hours=1, size=5):
    """POST a read-only query body (statistics/alarms APIs take filters in a JSON body)."""
    body = {"query": {"condition": "AND", "rules": [{"value": [str(hours)], "field": "entry_time",
                                                      "type": "date", "operator": "last_n_hours"}]},
            "size": size}
    return session.post(f"{API}{path}", json=body)       # json= -> Content-Type: application/json


def main():
    session = requests.Session()        # keeps the JSESSIONID cookie and our headers for every call
    session.verify = False              # skip TLS checks (like curl -k) for the self-signed cert
    session.trust_env = False           # else a REQUESTS_CA_BUNDLE env var overrides verify=False

    print("== Authenticate ==")
    login(session)
    get_xsrf_token(session)

    print("\n== 3. Inventory: GET /dataservice/device ==")
    devices = get(session, "/device")
    print(f"{'host-name':<13}{'device-type':<12}{'= current name':<19}{'system-ip':<13}{'site':<6}{'reach':<11}version")
    for d in devices:
        print(f"{d['host-name']:<13}{d['device-type']:<12}{NEW_NAME[d['device-type']]:<19}"
              f"{d['system-ip']:<13}{d['site-id']:<6}{d['reachability']:<11}{d['version']}")

    print("\n== 4. Health: GET /dataservice/device/monitor + /device/counters ==")
    status = {d["system-ip"]: d["status"] for d in get(session, "/device/monitor")}
    for c in get(session, "/device/counters"):
        print(f"{c['system-ip']:<13}status={status[c['system-ip']]:<8}"
              f"control={c['number-vsmart-control-connections']}/{c['expectedControlConnections']}  "
              f"omp_up={c.get('ompPeersUp', '-')}  bfd_up={c.get('bfdSessionsUp', '-')}")

    edge = next(d for d in devices if d["device-type"] == "vedge")
    print(f"\n   Control connections of {edge['host-name']} "
          f"(GET /dataservice/device/control/connections?deviceId={edge['system-ip']}):")
    for c in get(session, "/device/control/connections", params={"deviceId": edge["system-ip"]}):
        print(f"   {c['local-color']:<13}-> {c['peer-type']:<8}{c['peer-host-name']:<14}{c['protocol']} {c['state']}")

    print("\n== 5. Statistics: POST /dataservice/statistics/interface (query body) ==")
    resp = query(session, "/statistics/interface", hours=1, size=3)
    for row in resp.json()["data"]:
        print(f"{row['host_name']:<7}{row['interface']:<18}{row['oper_status']:<5}"
              f"tx_octets={row['tx_octets']}  rx_errors={row['rx_errors']}")

    print("\n== 6. Alarms: GET /dataservice/alarms/count, then a POST query without the token ==")
    print(f"alarm count: {get(session, '/alarms/count')[0]}")
    resp = session.post(f"{API}/alarms", json={"size": 1},
                        headers={"X-XSRF-TOKEN": None})          # None drops the Session header
    print(f"POST /alarms WITHOUT X-XSRF-TOKEN -> {resp.status_code} {resp.text.strip()[:110]}")
    resp = query(session, "/alarms", hours=24, size=5)
    print(f"POST /alarms WITH    X-XSRF-TOKEN -> {resp.status_code}, {len(resp.json()['data'])} alarms in last 24 h")

    print("\n== 7. Templates: GET /dataservice/template/device + /template/feature ==")
    device_templates = get(session, "/template/device")
    print(f"device templates: {len(device_templates)} "
          f"({sum(t['factoryDefault'] for t in device_templates)} factory default)")
    for t in device_templates:
        if not t["factoryDefault"]:
            print(f"  {t['templateName']:<18}{t['deviceType']:<15}{t['configType']:<10}attached={t['devicesAttached']}")
    feature_templates = get(session, "/template/feature")
    top = Counter(t["templateType"] for t in feature_templates).most_common(3)
    print(f"feature templates: {len(feature_templates)}, top types: {top}")

    print("\n== 8. Log out: POST /logout ==")
    resp = session.post(f"{BASE}/logout", params={"nocache": "1"}, allow_redirects=False)
    print(f"POST /logout -> {resp.status_code} (redirect to {resp.headers.get('Location', '-').split('?')[0]})")
    resp = session.get(f"{API}/device")
    print(f"GET /dataservice/device after logout -> {resp.status_code}, "
          f"Content-Type: {resp.headers.get('Content-Type')}  <- login page, not data")


if __name__ == "__main__":
    main()
