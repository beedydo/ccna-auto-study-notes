"""Mock Meraki Dashboard API v1 for the T18 lab (Python stdlib only).

Run:  python3 labs/T18/mock_meraki.py        -> http://127.0.0.1:8118/api/v1

Response bodies follow the shapes in the Meraki API v1 reference
(developer.cisco.com/meraki/api-v1). Data and the API key are fake.

What it imitates:
  - auth:        Authorization: Bearer <key>  or  X-Cisco-Meraki-API-Key: <key>; else 401
  - hierarchy:   /organizations -> /organizations/{orgId}/networks
                 -> /networks/{networkId}/devices -> /networks/{networkId}/clients
  - lookup:      /devices/{serial}, /devices/{serial}/clients,
                 /organizations/{orgId}/clients/search?mac=
  - pagination:  perPage + startingAfter, RFC 5988 Link header (rel=first / next / prev)
                 (links are base-relative here; the real API sends absolute URLs)
  - rate limit:  10 requests per second per organisation -> 429 + Retry-After: 1
                 (simplified: the real API also allows a short burst on top)
"""
import json
import os
import re
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

HOST, PORT = "127.0.0.1", int(os.environ.get("MOCK_PORT", "8118"))
BASE = f"http://{HOST}:{PORT}/api/v1"
VALID_KEYS = {os.environ.get("MOCK_MERAKI_KEY", "0123456789abcdef0123456789abcdef01234567")}
RATE_PER_SEC = 10

ORGS = [
    {"id": "549236", "name": "DevNet Sandbox", "url": "https://n149.meraki.com/o/-t35Mb/manage/organization/overview",
     "api": {"enabled": True}, "licensing": {"model": "co-term"},
     "cloud": {"region": {"name": "North America"}}, "management": {"details": []}},
]

def _net(nid, name, types, tz="Asia/Singapore"):
    return {"id": nid, "organizationId": "549236", "name": name, "productTypes": types,
            "timeZone": tz, "tags": [], "enrollmentString": None,
            "url": f"https://n149.meraki.com/{name}/n/abc/manage/usage/list", "notes": "",
            "isBoundToConfigTemplate": False}

NETWORKS = [
    _net("L_646829496481105433", "SG-HQ", ["appliance", "switch", "wireless", "camera"]),
    _net("L_646829496481105434", "SG-Branch-01", ["appliance", "wireless"]),
    _net("L_646829496481105435", "SG-Branch-02", ["appliance", "wireless"]),
    _net("L_646829496481105436", "TY-Lab", ["switch"], "Asia/Tokyo"),
    _net("L_646829496481105437", "NY-Office", ["appliance", "switch", "wireless"], "America/New_York"),
]

def _dev(serial, name, model, mac, lan_ip, net_id, fw):
    return {"name": name, "lat": 1.2834, "lng": 103.8607, "serial": serial, "mac": mac, "model": model,
            "address": "1 Raffles Place, Singapore", "notes": "", "lanIp": lan_ip, "tags": [],
            "networkId": net_id, "firmware": fw, "floorPlanId": None,
            "url": f"https://n149.meraki.com/SG-HQ/n/abc/manage/nodes/new_list/{serial}"}

HQ = "L_646829496481105433"
DEVICES = [
    _dev("Q2KY-8TRB-6LQA", "HQ-MX68", "MX68", "e0:55:3d:10:42:01", None, HQ, "wired-18-211"),
    _dev("Q2HP-3WCD-7KZE", "HQ-MS120-01", "MS120-8LP", "e0:55:3d:22:17:5a", "10.10.1.2", HQ, "switch-16-8"),
    _dev("Q3AB-9XJM-2VDN", "HQ-MR36-Lobby", "MR36", "0c:8d:db:6f:01:c4", "10.10.1.21", HQ, "wireless-29-7"),
    _dev("Q2FV-5MNP-4GHT", "HQ-MV12-Door", "MV12WE", "0c:8d:db:91:3e:77", "10.10.1.31", HQ, "camera-4-18"),
]

def _client(cid, mac, ip, desc, user, vlan, serial, dev_name, conn, ssid=None, port=None, os_="Windows 11"):
    return {"id": cid, "mac": mac, "ip": ip, "ip6": None, "ip6Local": None, "description": desc,
            "firstSeen": 1791504000, "lastSeen": 1791590400, "manufacturer": "Dell" if conn == "Wired" else "Apple",
            "os": os_, "user": user, "vlan": vlan, "namedVlan": None, "ssid": ssid, "switchport": port,
            "wirelessCapabilities": "802.11ax - 2.4 and 5 GHz" if ssid else None, "smInstalled": False,
            "recentDeviceMac": None, "recentDeviceSerial": serial, "recentDeviceName": dev_name,
            "recentDeviceConnection": conn, "status": "Online", "usage": {"sent": 13824, "recv": 61440},
            "notes": None, "groupPolicy8021x": None, "adaptivePolicyGroup": None,
            "deviceTypePrediction": None, "pskGroup": None}

CLIENTS = {HQ: [
    _client("k1a2b3c", "f8:4d:89:01:aa:10", "10.10.10.21", "bob-laptop", "bob", "10",
            "Q2HP-3WCD-7KZE", "HQ-MS120-01", "Wired", port="3"),
    _client("k2b3c4d", "f8:4d:89:01:aa:11", "10.10.10.22", "beedy-laptop", "beedy", "10",
            "Q2HP-3WCD-7KZE", "HQ-MS120-01", "Wired", port="4"),
    _client("k3c4d5e", "a4:83:e7:5c:02:3f", "10.10.20.51", "Bob's iPhone", None, "20",
            "Q3AB-9XJM-2VDN", "HQ-MR36-Lobby", "Wireless", ssid="Corp-WiFi", os_="iOS"),
    _client("k4d5e6f", "a4:83:e7:5c:02:40", "10.10.20.52", "Meeting-Room-iPad", None, "20",
            "Q3AB-9XJM-2VDN", "HQ-MR36-Lobby", "Wireless", ssid="Corp-WiFi", os_="iPadOS"),
    _client("k5e6f7a", "00:1b:63:84:45:e6", "10.10.30.10", "printer-l2", None, "30",
            "Q2HP-3WCD-7KZE", "HQ-MS120-01", "Wired", port="7", os_=None),
    _client("k6f7a8b", "3c:22:fb:9d:10:aa", "10.10.20.77", "guest-android", None, "20",
            "Q3AB-9XJM-2VDN", "HQ-MR36-Lobby", "Wireless", ssid="Guest", os_="Android"),
    _client("k7a8b9c", "00:0c:29:4f:8e:35", "10.10.1.50", "nas01", None, "1",
            "Q2HP-3WCD-7KZE", "HQ-MS120-01", "Wired", port="8", os_="Linux"),
]}

NET_TO_ORG = {n["id"]: n["organizationId"] for n in NETWORKS}
SERIAL_TO_ORG = {d["serial"]: "549236" for d in DEVICES}
window = {}   # orgId -> [window_start, count]


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def version_string(self):
        return "MockMeraki/1.0"

    def log_message(self, *args):
        pass

    def send(self, code, body=None, headers=None):
        data = json.dumps(body).encode() if body is not None else b""
        self.send_response(code)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        if data:
            self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def api_key(self):
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[len("Bearer "):]
        return self.headers.get("X-Cisco-Meraki-API-Key")

    def rate_limited(self, org_id):
        """Fixed 1-second window per organisation."""
        now = time.monotonic()
        start, count = window.get(org_id, (now, 0))
        if now - start >= 1.0:
            start, count = now, 0
        count += 1
        window[org_id] = (start, count)
        return count > RATE_PER_SEC

    def paged(self, path, items, params, default_per_page, max_per_page):
        """Return one page of items plus an RFC 5988 Link header, Meraki style."""
        per_page = int(params.get("perPage", [default_per_page])[0])
        if not 3 <= per_page <= max_per_page:
            return None, {"errors": [f"'perPage' must be between 3 and {max_per_page}"]}
        ids = [i["id"] for i in items]
        start = 0
        if "startingAfter" in params:
            token = params["startingAfter"][0]
            start = ids.index(token) + 1 if token in ids else 0
        page = items[start:start + per_page]
        keep = {k: v[0] for k, v in params.items() if k not in ("startingAfter", "endingBefore")}
        keep["perPage"] = per_page
        # Real API: absolute https://api.meraki.com/api/v1/... links. The mock sends paths
        # relative to the base URL, because the SDK only follows absolute links on *.meraki.com.
        url = lambda extra: f"{path}?{urlencode({**keep, **extra})}"
        links = [f"<{url({'startingAfter': '0'})}>; rel=first"]
        if start + per_page < len(items):
            links.append(f"<{url({'startingAfter': page[-1]['id']})}>; rel=next")
        if start > 0:
            links.append(f"<{url({'endingBefore': page[0]['id']})}>; rel=prev")
        return page, {"Link": ", ".join(links)}

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.removeprefix("/api/v1")
        params = parse_qs(parsed.query)

        if self.api_key() not in VALID_KEYS:
            return self.send(401, {"errors": ["Invalid API key"]})

        # find which org this call is charged to (rate limit is per organisation)
        m = re.match(r"^/(organizations|networks|devices)/([^/]+)", path)
        org_id = None
        if m:
            kind, ident = m.groups()
            org_id = {"organizations": ident, "networks": NET_TO_ORG.get(ident),
                      "devices": SERIAL_TO_ORG.get(ident)}[kind]
        if org_id and self.rate_limited(org_id):
            return self.send(429, {"errors": ["API rate limit exceeded for organization"]},
                             {"Retry-After": "1"})

        if path == "/organizations":
            return self.send(200, ORGS)

        m = re.match(r"^/organizations/([^/]+)/networks$", path)
        if m:
            if m.group(1) not in {o["id"] for o in ORGS}:
                return self.send(404, {"errors": ["Organization not found"]})
            nets = [n for n in NETWORKS if n["organizationId"] == m.group(1)]
            page, extra = self.paged(path, nets, params, 1000, 100000)
            return self.send(200 if page is not None else 400, page if page is not None else extra,
                             extra if page is not None else None)

        m = re.match(r"^/organizations/([^/]+)/clients/search$", path)
        if m:
            if "mac" not in params:
                return self.send(400, {"errors": ["'mac' must be specified"]})
            mac = params["mac"][0].lower()
            for net_id, clients in CLIENTS.items():
                for c in clients:
                    if c["mac"] == mac:
                        net = next(n for n in NETWORKS if n["id"] == net_id)
                        rec = {k: c[k] for k in ("ip", "ip6", "description", "firstSeen", "lastSeen", "os",
                                                 "user", "vlan", "ssid", "switchport", "wirelessCapabilities",
                                                 "smInstalled", "recentDeviceMac", "status")}
                        rec["network"] = net
                        return self.send(200, {"clientId": c["id"], "mac": c["mac"],
                                               "manufacturer": c["manufacturer"], "records": [rec]})
            return self.send(404, {"errors": ["Client not found"]})

        m = re.match(r"^/networks/([^/]+)/devices$", path)
        if m:
            if m.group(1) not in NET_TO_ORG:
                return self.send(404, {"errors": ["Network not found"]})
            return self.send(200, [d for d in DEVICES if d["networkId"] == m.group(1)])

        m = re.match(r"^/networks/([^/]+)/clients$", path)
        if m:
            if m.group(1) not in NET_TO_ORG:
                return self.send(404, {"errors": ["Network not found"]})
            clients = CLIENTS.get(m.group(1), [])
            for field in ("mac", "ip"):                       # partial-or-full match filters
                if field in params:
                    clients = [c for c in clients if params[field][0].lower() in c[field]]
            page, extra = self.paged(path, clients, params, 10, 5000)
            return self.send(200 if page is not None else 400, page if page is not None else extra,
                             extra if page is not None else None)

        m = re.match(r"^/devices/([^/]+)/clients$", path)
        if m:
            clients = [c for cl in CLIENTS.values() for c in cl if c["recentDeviceSerial"] == m.group(1)]
            return self.send(200, [{"usage": c["usage"], "id": c["id"], "description": c["description"],
                                    "mac": c["mac"], "ip": c["ip"], "user": c["user"], "vlan": c["vlan"],
                                    "switchport": c["switchport"], "dhcpHostname": c["description"],
                                    "mdnsName": None} for c in clients])

        m = re.match(r"^/devices/([^/]+)$", path)
        if m:
            dev = next((d for d in DEVICES if d["serial"] == m.group(1)), None)
            return self.send(200, dev) if dev else self.send(404, {"errors": ["Device not found"]})

        return self.send(404, {"errors": ["Not found"]})


if __name__ == "__main__":
    print(f"Mock Meraki Dashboard API on {BASE}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
