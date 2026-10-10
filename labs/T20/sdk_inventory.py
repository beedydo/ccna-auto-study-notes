"""T20 SDK version: the same inventory + command runner + client lookup with dnacentersdk.

pip install dnacentersdk
Live sandbox (default):  python3 labs/T20/sdk_inventory.py
Local mock:              bash labs/T20/run_lab.sh labs/T20/sdk_inventory.py

The SDK does the token call and the X-Auth-Token header for you.
"""
import json
import os
import time

import urllib3
from dnacentersdk import DNACenterAPI, ApiError

urllib3.disable_warnings()

api = DNACenterAPI(base_url=os.environ.get("DNAC_URL", "https://sandboxdnac2.cisco.com"),
                   username=os.environ.get("DNAC_USER", "devnetuser"),
                   password=os.environ.get("DNAC_PASS", "Cisco123!"),
                   verify=False)                      # SDK gets the token; re-gets it once on a 401

devices = api.devices.get_device_list()              # GET /dna/intent/api/v1/network-device
for dev in devices.response:                         # dot access works (MyDict) as well as ["key"]
    print(dev.hostname, dev.managementIpAddress, dev.id)

sw1 = api.devices.get_device_list(hostname="sw1").response[0]    # snake_case kwarg -> ?hostname=
run = api.command_runner.run_read_only_commands_on_devices(
    commands=["show version | include uptime"], deviceUuids=[sw1.id])   # 202 + taskId
for _ in range(10):
    task = api.task.get_task_by_id(task_id=run.response.taskId).response
    if task.get("endTime") or task.get("isError"):
        break
    time.sleep(1)
print("task done, isError =", task.isError, "progress =", task.progress)
file_id = json.loads(task.progress)["fileId"]
print("file", file_id)

try:
    client = api.clients.get_client_detail(mac_address="00:1e:13:a5:b9:40").detail
    print(client.hostName, "on", client.clientConnection, client.port, "VLAN", client.vlanId)
except ApiError as err:                              # non-2xx -> ApiError
    print("client-detail:", err.status_code, err.response.json()["response"]["message"])
