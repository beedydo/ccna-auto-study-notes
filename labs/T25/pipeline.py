"""T25 reference program: test a change in CML, then roll it out with NSO.

Stage 1 (CML, blueprint 5.3): build a throwaway twin of the network from topology.yaml,
         boot it, hand it to the tests, tear it down.
Stage 2 (NSO, blueprint 3.2 / 5.6): push one "anycast loopback" service to three
         vendors' devices as ONE transaction, with sync checks, dry-run and FASTMAP.

Start the mock first:  python3 labs/T25/mock_nso_cml.py   (or: bash labs/T25/run_lab.sh)
Real targets: set CML_URL / CML_USER / CML_PASS and NSO_URL / NSO_USER / NSO_PASS.
"""
import json
import os
import pathlib
import time

import requests

CML_URL = os.environ.get("CML_URL", "http://127.0.0.1:18025")      # real CML: https://<cml-host>
CML_USER = os.environ.get("CML_USER", "admin")
CML_PASS = os.environ.get("CML_PASS", "T25-mock-pass")
NSO_URL = os.environ.get("NSO_URL", "http://127.0.0.1:18025")      # real NSO: http://<nso-host>:8080
NSO_USER = os.environ.get("NSO_USER", "admin")
NSO_PASS = os.environ.get("NSO_PASS", "admin")
TOPOLOGY = pathlib.Path(__file__).with_name("topology.yaml")
YANG_JSON = "application/yang-data+json"


def show(resp, body=True):
    """Print one request/response pair in a compact form."""
    req = resp.request
    print(f">>> {req.method} {req.url.replace(CML_URL, '').replace(NSO_URL, '')}")
    print(f"<<< {resp.status_code} {resp.reason}")
    if "Location" in resp.headers:
        print(f"    Location: {resp.headers['Location']}")
    if body and resp.text:
        try:
            print("    " + json.dumps(resp.json()).replace("\n", "\n    "))
        except ValueError:
            print("    " + resp.text.strip().replace("\n", "\n    "))
    return resp


def show_dry_run(resp):
    """dry-run=native returns, per device, exactly what the NED would send."""
    print(f">>> {resp.request.method} {resp.request.url.replace(NSO_URL, '')}")
    print(f"<<< {resp.status_code} {resp.reason}")
    for dev in resp.json()["dry-run-result"]["native"]["device"]:
        print(f"    --- {dev['name']} ---")
        print("    " + dev["data"].rstrip().replace("\n", "\n    "))


# ------------------------------------------------------------------ stage 1: CML
def cml_test_stage():
    cml = requests.Session()
    cml.verify = False                                    # CML ships a self-signed cert

    token = show(cml.post(f"{CML_URL}/api/v0/authenticate",
                          json={"username": CML_USER, "password": CML_PASS})).json()
    cml.headers["Authorization"] = f"Bearer {token}"      # JWT on every later call

    lab_id = show(cml.post(f"{CML_URL}/api/v0/import", params={"title": "T25-ci-twin"},
                           data=TOPOLOGY.read_text())).json()["id"]
    show(cml.put(f"{CML_URL}/api/v0/labs/{lab_id}/start"))
    while not show(cml.get(f"{CML_URL}/api/v0/labs/{lab_id}/check_if_converged")).json():
        time.sleep(0.2)                                   # real labs take minutes; poll ~5 s
    show(cml.get(f"{CML_URL}/api/v0/labs/{lab_id}/nodes", params={"data": "true"}))
    show(cml.get(f"{CML_URL}/api/v0/labs/{lab_id}/pyats_testbed"))
    print("    ... CI job now runs its pyATS tests against this testbed (T44) ...")

    for action in ("stop", "wipe"):                       # must stop + wipe before delete
        show(cml.put(f"{CML_URL}/api/v0/labs/{lab_id}/{action}"))
    show(cml.delete(f"{CML_URL}/api/v0/labs/{lab_id}"))


# ------------------------------------------------------------------ stage 2: NSO
def nso_deploy_stage():
    nso = requests.Session()
    nso.auth = (NSO_USER, NSO_PASS)                       # NSO RESTCONF: HTTP Basic
    nso.headers.update({"Accept": YANG_JSON, "Content-Type": YANG_JSON})
    data = f"{NSO_URL}/restconf/data"
    devices = f"{data}/tailf-ncs:devices"
    service = {"loopback:loopback": [{"name": "T25-LO100", "device": ["ios0", "xr0", "junos0"],
                                      "id": 100, "ipv4": "10.100.0.1"}]}
    svc_url = f"{data}/loopback:loopback=T25-LO100"

    print("\n-- managed devices: one NED per vendor/protocol --")
    show(nso.get(f"{devices}/device?fields=name;address;device-type"))

    print("\n-- is CDB the same as each box? --")
    show(nso.post(f"{devices}/check-sync"))

    print("\n-- commit while ios0 is out of sync: whole transaction refused --")
    show(nso.post(data, json=service))
    show(nso.get(svc_url))                                # 404: nothing was created anywhere

    print("\n-- pull the box's config into CDB, then re-check --")
    show(nso.post(f"{devices}/device=ios0/sync-from"))
    show(nso.post(f"{devices}/check-sync"))

    print("\n-- dry-run: what each NED would send, nothing committed --")
    show_dry_run(nso.post(data, json=service, params={"dry-run": "native"}))

    print("\n-- commit for real: one transaction, three devices --")
    show(nso.post(data, json=service, params={"rollback-id": "true"}))
    show(nso.get(f"{devices}/device=ios0/config/tailf-ned-cisco-ios:interface/Loopback=100"))

    print("\n-- FASTMAP: drop junos0 from the service; NSO works out the minimal change --")
    smaller = {"loopback:loopback": [{**service["loopback:loopback"][0], "device": ["ios0", "xr0"]}]}
    show_dry_run(nso.put(svc_url, json=smaller, params={"dry-run": "native"}))
    show(nso.put(svc_url, json=smaller))

    print("\n-- FASTMAP: delete the service; NSO removes exactly what it created --")
    show_dry_run(nso.delete(svc_url, params={"dry-run": "native"}))
    show(nso.delete(svc_url))
    show(nso.get(f"{devices}/device=ios0/config/tailf-ned-cisco-ios:interface/Loopback=100"))


if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings()          # quiet the self-signed-cert warning
    print("== Stage 1: CML - test the change on a simulated twin ==")
    cml_test_stage()
    print("\n== Stage 2: NSO - deploy the change as one transaction ==")
    nso_deploy_stage()
