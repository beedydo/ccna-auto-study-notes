"""T18 reference program, part 2: the same walk with the Meraki Python SDK.

    pip install meraki
Default target is the local mock (python3 labs/T18/mock_meraki.py).
For the real cloud: unset MERAKI_BASE_URL and export MERAKI_DASHBOARD_API_KEY=<your key>
"""
import os

import meraki

BASE_URL = os.environ.get("MERAKI_BASE_URL", "http://127.0.0.1:8118/api/v1")
API_KEY = os.environ.get("MERAKI_DASHBOARD_API_KEY", "0123456789abcdef0123456789abcdef01234567")

dashboard = meraki.DashboardAPI(
    api_key=API_KEY,              # omit it and the SDK reads MERAKI_DASHBOARD_API_KEY itself
    base_url=BASE_URL,            # default https://api.meraki.com/api/v1
    suppress_logging=True,        # no log file / console noise for the demo
    wait_on_rate_limit=True,      # default: on 429, sleep Retry-After and retry
    maximum_retries=3,
)


def main():
    print("== 1. Organizations ==")
    orgs = dashboard.organizations.getOrganizations()
    org_id = orgs[0]["id"]
    print(f"    {len(orgs)} org: {org_id} {orgs[0]['name']}")

    print("\n== 2. Networks: total_pages trap ==")
    first = dashboard.organizations.getOrganizationNetworks(org_id, perPage=3)
    every = dashboard.organizations.getOrganizationNetworks(org_id, perPage=3, total_pages="all")
    print(f"    default total_pages=1 -> {len(first)} networks")
    print(f"    total_pages='all'     -> {len(every)} networks")
    net_id = next(n["id"] for n in every if n["name"] == "SG-HQ")

    print("\n== 3. Devices ==")
    for d in dashboard.networks.getNetworkDevices(net_id):
        print(f"    {d['serial']}  {d['model']}")

    print("\n== 4. Clients (all pages) ==")
    clients = dashboard.networks.getNetworkClients(net_id, timespan=86400, perPage=3, total_pages="all")
    print(f"    {len(clients)} clients; first: {clients[0]['description']} on {clients[0]['recentDeviceName']}")

    print("\n== 5. Where is 10.10.10.21? ==")
    hit = dashboard.networks.getNetworkClients(net_id, ip="10.10.10.21")[0]
    switch = dashboard.devices.getDevice(hit["recentDeviceSerial"])
    print(f"    {hit['mac']} -> {switch['name']} ({switch['model']}) port {hit['switchport']}")

    print("\n== 6. Rate limit: 12 fast calls, SDK retries 429 for you ==")
    for _ in range(12):
        dashboard.networks.getNetworkDevices(net_id)
    print("    12/12 returned; no 429 reached this code")

    print("\n== 7. Errors surface as meraki.APIError ==")
    try:
        dashboard.organizations.getOrganizationNetworks("999999")
    except meraki.APIError as err:
        print(f"    status={err.status} reason={err.reason} message={err.message}")


if __name__ == "__main__":
    main()
