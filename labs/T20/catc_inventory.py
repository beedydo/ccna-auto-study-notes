"""T20 reference program: Catalyst Center (DNA Center) Intent API with requests.

Live sandbox (default):  python3 labs/T20/catc_inventory.py
Local mock:              bash labs/T20/run_lab.sh

1 token -> 2 inventory -> 3 health + topology -> 4 command runner (async task) -> 5 client discovery
"""
import json
import os
import time

import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings()                      # sandbox has a self-signed cert (verify=False below)

BASE_URL = os.environ.get("DNAC_URL", "https://sandboxdnac2.cisco.com")
USER = os.environ.get("DNAC_USER", "devnetuser")          # public DevNet sandbox defaults
PASSWORD = os.environ.get("DNAC_PASS", "Cisco123!")
CLIENT_MACS = os.environ.get("CLIENT_MACS", "00:1e:13:a5:b9:40,a4:83:e7:2c:11:9f").split(",")
INTENT = "/dna/intent/api/v1"                   # every Intent API path starts here
COMMAND = "show version | include uptime"


def get_token():
    """Step 1: the ONLY call that sends username/password (HTTP Basic). Returns the token."""
    resp = requests.post(f"{BASE_URL}/dna/system/api/v1/auth/token",
                         auth=HTTPBasicAuth(USER, PASSWORD), verify=False, timeout=30)
    resp.raise_for_status()                     # 401 here = wrong username/password
    return resp.json()["Token"]                 # capital T


def intent(method, path, token, **kwargs):
    """Every other call: Intent API base path + token in the X-Auth-Token header."""
    headers = {"X-Auth-Token": token, "Content-Type": "application/json",
               "Accept": "application/json"}
    resp = requests.request(method, BASE_URL + INTENT + path, headers=headers,
                            verify=False, timeout=30, **kwargs)
    print(f"  {method} {resp.request.path_url} -> {resp.status_code}")
    return resp


def wait_for_task(token, task_id, interval=1, attempts=10):
    """Step 4b: poll GET /task/{taskId} until it has an endTime, or isError is true."""
    for _ in range(attempts):
        task = intent("GET", f"/task/{task_id}", token).json()["response"]
        if task.get("isError"):
            raise RuntimeError(f"task failed: {task.get('failureReason')}")
        if task.get("endTime"):                 # finished
            return task
        print(f"    still running: progress={task.get('progress')!r}")
        time.sleep(interval)
    raise TimeoutError(f"task {task_id} not finished after {attempts} polls")


def main():
    print("== 1. Authenticate ==")
    token = get_token()
    print(f"  POST /dna/system/api/v1/auth/token -> Token {token[:20]}... (valid 60 min)")

    print("\n== 2. Inventory ==")
    devices = intent("GET", "/network-device", token).json()["response"]
    for dev in devices:
        print(f"    {dev['hostname']:4} {dev['managementIpAddress']:13} {dev['platformId']:13} "
              f"IOS-XE {dev['softwareVersion']:12} {dev['role']:7} {dev['reachabilityStatus']}")
    one = intent("GET", "/network-device", token, params={"hostname": "sw1"}).json()["response"]
    print(f"    filter ?hostname=sw1 -> {len(one)} device, id {one[0]['id']}")

    print("\n== 3. Health and topology ==")
    for site in intent("GET", "/site-health", token).json()["response"]:
        print(f"    {site['siteName'].strip()}: network health {site['networkHealthAverage']}%, "
              f"{site['numberOfNetworkDevice']} devices")
    topo = intent("GET", "/topology/physical-topology", token).json()["response"]
    names = {node["id"]: node["label"] for node in topo["nodes"]}
    for link in topo["links"]:
        if "1/0/" in link["startPortName"]:     # skip the Gi0/0 management mesh
            print(f"    {names[link['source']]} {link['startPortName']} <-> "
                  f"{names[link['target']]} {link['endPortName']} ({link['linkStatus']})")

    print("\n== 4. Command runner (asynchronous) ==")
    resp = intent("POST", "/network-device-poller/cli/read-request", token,
                  json={"commands": [COMMAND], "deviceUuids": [one[0]["id"]]})
    task_id = resp.json()["response"]["taskId"]           # 202 Accepted: work not done yet
    print(f"    taskId {task_id}")
    task = wait_for_task(token, task_id)
    file_id = json.loads(task["progress"])["fileId"]       # progress is a JSON *string*
    output = intent("GET", f"/file/{file_id}", token).json()
    for result in output:                                  # one entry per device
        answers = result["commandResponses"]               # SUCCESS / FAILURE / BLOCKLISTED
        for cmd, text in answers["SUCCESS"].items():
            print(f"    SUCCESS {cmd!r}: {text.splitlines()[1]}")
        for cmd, reason in answers["BLOCKLISTED"].items():
            print(f"    BLOCKLISTED {cmd!r}: {reason}")

    print("\n== 5. Client discovery ==")
    for mac in CLIENT_MACS:
        resp = intent("GET", "/client-detail", token, params={"macAddress": mac})
        if resp.status_code != 200:
            print(f"    {mac}: {resp.json()['response']['message']}")
            continue
        client = resp.json()["detail"]
        health = {h["healthType"]: h["score"] for h in client["healthScore"]}
        where = client["port"] or f"SSID {client['ssid']}"
        print(f"    {client['hostName']} {client['hostIpV4']} {client['hostType']}: "
              f"{client['connectedDevice'][0]['type']} {client['clientConnection']} {where}, "
              f"VLAN {client['vlanId']}, health {health['OVERALL']}/10")


if __name__ == "__main__":
    main()
