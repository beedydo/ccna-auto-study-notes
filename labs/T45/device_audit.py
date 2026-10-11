"""T45 reference script: find unreachable devices in Catalyst Center and resync them.

Shape of almost every Cisco API script on the exam:
  imports -> constants -> auth -> API call functions -> parse/loop -> act -> output
Run against the local mock:  bash labs/T45/run_lab.sh
"""
import json
import os
import time

import requests

# ---- constants: where, who, how ----------------------------------------------
BASE_URL = os.environ.get("DNAC_URL", "http://127.0.0.1:18045")
USERNAME = os.environ.get("DNAC_USER", "devnetuser")
PASSWORD = os.environ.get("DNAC_PASS", "Cisco123!")
VERIFY_TLS = os.environ.get("DNAC_VERIFY", "false").lower() == "true"
PAGE_SIZE = int(os.environ.get("DNAC_PAGE_SIZE", "3"))   # real API max is 500


def get_token():
    """[1] AUTH: POST user:pass as Basic auth, read the token from the JSON body."""
    url = f"{BASE_URL}/dna/system/api/v1/auth/token"
    resp = requests.post(url, auth=(USERNAME, PASSWORD), verify=VERIFY_TLS, timeout=10)
    resp.raise_for_status()                       # 401 stops here, with a clear error
    return resp.json()["Token"]                   # key is "Token", capital T


def get_devices(headers):
    """[2] REQUEST: GET every device, one page at a time (offset is 1-based)."""
    url = f"{BASE_URL}/dna/intent/api/v1/network-device"
    devices, offset = [], 1
    while True:
        params = {"offset": offset, "limit": PAGE_SIZE}
        resp = requests.get(url, headers=headers, params=params, verify=VERIFY_TLS, timeout=10)
        resp.raise_for_status()
        page = resp.json()["response"]            # the list sits under "response"
        devices.extend(page)
        if len(page) < PAGE_SIZE:                 # short page = last page
            return devices
        offset += PAGE_SIZE


def sync_devices(headers, device_ids):
    """[4] ACT: ask Catalyst Center to resync these devices; returns a task id."""
    url = f"{BASE_URL}/dna/intent/api/v1/network-device/sync"
    resp = requests.put(url, headers=headers, params={"forceSync": "false"},
                        data=json.dumps(device_ids), verify=VERIFY_TLS, timeout=10)
    resp.raise_for_status()                       # 202 Accepted = queued, not finished
    return resp.json()["response"]["taskId"]


def wait_for_task(headers, task_id):
    """[5] CONFIRM: poll the task until it has an endTime."""
    url = f"{BASE_URL}/dna/intent/api/v1/task/{task_id}"
    for _ in range(10):
        task = requests.get(url, headers=headers, verify=VERIFY_TLS, timeout=10).json()["response"]
        print(f"    task {task_id[:8]}: {task['progress']}")
        if "endTime" in task:
            return not task["isError"]
        time.sleep(1)
    return False


def main():
    token = get_token()
    headers = {
        "X-Auth-Token": token,                    # Catalyst Center header, not "Authorization"
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    devices = get_devices(headers)
    print(f"Found {len(devices)} devices")

    # [3] PARSE: loop over the list, pick fields, filter
    unreachable = []
    for device in devices:
        print(f"  {device['hostname']:<14} {device['managementIpAddress']:<13} "
              f"{device['platformId']:<15} {device['reachabilityStatus']}")
        if device["reachabilityStatus"] != "Reachable":
            unreachable.append(device)

    if not unreachable:
        print("All devices reachable, nothing to do")
        return
    print(f"Resyncing {len(unreachable)}: {', '.join(d['hostname'] for d in unreachable)}")
    task_id = sync_devices(headers, [d["id"] for d in unreachable])
    ok = wait_for_task(headers, task_id)
    print("Resync finished OK" if ok else "Resync failed or timed out")


if __name__ == "__main__":
    main()
