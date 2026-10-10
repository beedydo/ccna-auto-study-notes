"""T18 reference program, part 1: walk the Meraki hierarchy with plain `requests`.

    org -> networks -> devices -> clients -> "where is this client plugged in?"

Default target is the local mock (python3 labs/T18/mock_meraki.py).
For the real cloud:  export MERAKI_BASE_URL=https://api.meraki.com/api/v1
                     export MERAKI_DASHBOARD_API_KEY=<your key>
"""
import os
import time

import requests

BASE_URL = os.environ.get("MERAKI_BASE_URL", "http://127.0.0.1:8118/api/v1")
API_KEY = os.environ.get("MERAKI_DASHBOARD_API_KEY", "0123456789abcdef0123456789abcdef01234567")

session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {API_KEY}",        # v1 standard; X-Cisco-Meraki-API-Key also works
    "Accept": "application/json",
})


def meraki_get(path, params=None, max_retries=3):
    """GET one URL; on 429 sleep for Retry-After seconds and try again."""
    url = path if path.startswith("http") else BASE_URL + path
    for attempt in range(1, max_retries + 1):
        resp = session.get(url, params=params, timeout=30)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", "1"))
            print(f"    429 Too Many Requests -> Retry-After: {wait}s (attempt {attempt})")
            time.sleep(wait)
            continue
        resp.raise_for_status()                    # 401/404/400 -> requests.HTTPError
        return resp
    raise RuntimeError(f"still rate-limited after {max_retries} tries: {url}")


def get_all_pages(path, params=None):
    """Follow the Link header (rel=next) until there is no next page."""
    items, resp = [], meraki_get(path, params)
    pages = 1
    items.extend(resp.json())
    while "next" in resp.links:                    # requests parses the Link header for us
        resp = meraki_get(resp.links["next"]["url"])   # next URL already has perPage + startingAfter
        items.extend(resp.json())
        pages += 1
    print(f"    {path}: {len(items)} items in {pages} page(s)")
    return items


def find_client(org_id, net_id, mac=None, ip=None):
    """3.9.c client discovery: MAC -> org-wide search; IP -> filter the network's clients."""
    if mac:
        hit = meraki_get(f"/organizations/{org_id}/clients/search", params={"mac": mac}).json()
        rec = hit["records"][0]
        return {"id": hit["clientId"], "network": rec["network"]["name"], "ip": rec["ip"],
                "vlan": rec["vlan"], "switchport": rec["switchport"], "ssid": rec["ssid"]}
    clients = meraki_get(f"/networks/{net_id}/clients", params={"ip": ip, "timespan": 86400}).json()
    c = clients[0]
    return {"id": c["id"], "mac": c["mac"], "device": c["recentDeviceName"],
            "serial": c["recentDeviceSerial"], "vlan": c["vlan"], "switchport": c["switchport"],
            "ssid": c["ssid"]}


def main():
    print("== 1. Auth: wrong header name ==")
    bad = requests.get(BASE_URL + "/organizations", headers={"X-API-Key": API_KEY}, timeout=30)
    print(f"    {bad.status_code} {bad.reason}: {bad.json()}")

    print("\n== 2. Organizations ==")
    orgs = meraki_get("/organizations").json()
    org_id = orgs[0]["id"]
    print(f"    org {org_id} = {orgs[0]['name']}")

    print("\n== 3. Networks (paginated, perPage=3) ==")
    networks = get_all_pages(f"/organizations/{org_id}/networks", params={"perPage": 3})
    for n in networks:
        print(f"    {n['id']}  {n['name']:<13} {','.join(n['productTypes'])}")
    net_id = next(n["id"] for n in networks if n["name"] == "SG-HQ")

    print("\n== 4. Devices in SG-HQ (identified by serial) ==")
    for d in meraki_get(f"/networks/{net_id}/devices").json():
        print(f"    {d['serial']}  {d['model']:<10} {d['name']:<15} lanIp={d['lanIp']}")

    print("\n== 5. Clients in SG-HQ (last 24 h, perPage=3) ==")
    clients = get_all_pages(f"/networks/{net_id}/clients", params={"timespan": 86400, "perPage": 3})
    for c in clients:
        where = f"port {c['switchport']}" if c["switchport"] else f"SSID {c['ssid']}"
        print(f"    {c['mac']}  {c['ip']:<12} {c['description']:<18} -> {c['recentDeviceName']} {where}")

    print("\n== 6. Find one client ==")
    print(f"    by MAC: {find_client(org_id, net_id, mac='a4:83:e7:5c:02:3f')}")
    by_ip = find_client(org_id, net_id, ip="10.10.10.21")
    print(f"    by IP:  {by_ip}")
    sw = meraki_get(f"/devices/{by_ip['serial']}").json()
    print(f"    -> plugged into {sw['model']} {sw['name']} port {by_ip['switchport']}, VLAN {by_ip['vlan']}")

    print("\n== 7. Rate limit: 12 fast calls against one org ==")
    time.sleep(1.1)                                # start with a fresh 1-second budget
    for _ in range(12):
        meraki_get(f"/networks/{net_id}/devices")
    print("    all 12 succeeded (the 429s were retried after Retry-After)")


if __name__ == "__main__":
    main()
