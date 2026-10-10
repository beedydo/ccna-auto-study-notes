"""Mock Catalyst Center (DNA Center) Intent API for the T20 lab (Python stdlib only).

Run:  python3 labs/T20/mock_catc.py          -> http://127.0.0.1:8443
Then: DNAC_URL=http://127.0.0.1:8443 python3 labs/T20/catc_inventory.py
(or just: bash labs/T20/run_lab.sh)

Device, site, topology and command-runner data were copied from the DevNet
always-on sandbox (sandboxdnac2.cisco.com, Oct 2026). The two clients are made up,
because the sandbox has no clients. Response shapes follow the Catalyst Center
API reference. Credentials are the public DevNet sandbox defaults.
"""
import base64
import json
import re
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST, PORT = "127.0.0.1", 8443
USERS = {"devnetuser": "Cisco123!"}
TOKEN = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.mock-catc-token.c2lnbmF0dXJl"
INTENT = "/dna/intent/api/v1"


def device(n, ip, serial, mac, dev_id):
    return {
        "hostname": f"sw{n}", "managementIpAddress": ip, "platformId": "C9KV-UADP-8P",
        "softwareVersion": "17.12.1prd9", "softwareType": "IOS-XE", "family": "Switches and Hubs",
        "role": "ACCESS", "reachabilityStatus": "Reachable", "serialNumber": serial,
        "macAddress": mac, "series": "Cisco Catalyst 9000 Series Virtual Switches",
        "type": "Cisco Catalyst 9000 UADP 8 Port Virtual Switch", "managementState": "Managed",
        "id": dev_id, "instanceUuid": dev_id,
    }


DEVICES = [
    device(1, "10.10.20.175", "CML12345UAD", "52:54:00:02:19:54", "6b3dc2dd-a26f-4807-97eb-9d316b22fa83"),
    device(2, "10.10.20.176", "CML12345", "52:54:00:07:29:d0", "f0eb8382-1dae-4212-bbf4-c08f17b3417e"),
    device(3, "10.10.20.177", "CML12345ABC", "52:54:00:05:77:13", "fe048e81-1f22-49f7-9eac-ac06119c635d"),
    device(4, "10.10.20.178", "CML54321", "52:54:00:0f:1c:07", "ffde3775-f30c-411e-9a96-f435d2b834e5"),
]
BY_ID = {d["id"]: d for d in DEVICES}

SITE_HEALTH = [{
    "siteName": " All Sites", "siteId": "", "siteType": "area",
    "healthyNetworkDevicePercentage": 100, "numberOfNetworkDevice": 4,
    "networkHealthAverage": 100, "networkHealthAccess": 100, "healthyClientsPercentage": 50,
    "numberOfClients": 2, "numberOfWiredClients": 1, "numberOfWirelessClients": 1,
}]

LINKS = [  # (source, port, target, port) from the sandbox physical topology
    ("sw2", "GigabitEthernet1/0/1", "sw4", "GigabitEthernet1/0/2"),
    ("sw1", "GigabitEthernet0/0", "sw3", "GigabitEthernet0/0"),
    ("sw3", "GigabitEthernet0/0", "sw4", "GigabitEthernet0/0"),
    ("sw3", "GigabitEthernet1/0/1", "sw4", "GigabitEthernet1/0/1"),
    ("sw1", "GigabitEthernet0/0", "sw4", "GigabitEthernet0/0"),
    ("sw2", "GigabitEthernet0/0", "sw4", "GigabitEthernet0/0"),
    ("sw2", "GigabitEthernet0/0", "sw3", "GigabitEthernet0/0"),
    ("sw1", "GigabitEthernet1/0/3", "sw2", "GigabitEthernet1/0/2"),
    ("sw1", "GigabitEthernet1/0/1", "sw3", "GigabitEthernet1/0/2"),
    ("sw1", "GigabitEthernet0/0", "sw2", "GigabitEthernet0/0"),
]
ID_BY_NAME = {d["hostname"]: d["id"] for d in DEVICES}

CLIENTS = {  # client-detail by MAC (made up; field names from the API reference)
    "00:1e:13:a5:b9:40": {
        "hostName": "printer-l2", "hostMac": "00:1e:13:a5:b9:40", "hostIpV4": "10.10.30.21",
        "hostType": "WIRED", "connectionStatus": "CONNECTED", "vlanId": 30, "ssid": None,
        "port": "GigabitEthernet1/0/5", "clientConnection": "sw1", "location": "Global/SJC/Floor-2",
        "connectedDevice": [{"type": "SWITCH", "name": "sw1", "mac": "52:54:00:02:19:54",
                             "id": "6b3dc2dd-a26f-4807-97eb-9d316b22fa83", "mgmtIp": "10.10.20.175"}],
        "healthScore": [{"healthType": "OVERALL", "reason": "", "score": 10},
                        {"healthType": "ONBOARDED", "reason": "", "score": 4},
                        {"healthType": "CONNECTED", "reason": "", "score": 6}],
    },
    "a4:83:e7:2c:11:9f": {
        "hostName": "jdoe-laptop", "hostMac": "a4:83:e7:2c:11:9f", "hostIpV4": "10.10.40.57",
        "hostType": "WIRELESS", "connectionStatus": "CONNECTED", "vlanId": 40, "ssid": "CORP-WIFI",
        "port": None, "clientConnection": "AP-F2-01", "location": "Global/SJC/Floor-2",
        "connectedDevice": [{"type": "AP", "name": "AP-F2-01", "mac": "70:69:5a:51:4e:a0",
                             "id": "8d0e0f5c-3a33-4d43-9b55-2c1f0c8f0b11", "mgmtIp": "10.10.20.201"}],
        "healthScore": [{"healthType": "OVERALL", "reason": "Poor RSSI", "score": 3},
                        {"healthType": "ONBOARDED", "reason": "", "score": 4},
                        {"healthType": "CONNECTED", "reason": "Poor RSSI", "score": 1}],
    },
}

BLOCKED = ("conf", "configure", "write", "reload", "copy", "delete")
tasks, files = {}, {}
IDS = uuid.UUID("01a125ac-2597-71d6-ab94-c7744eb46889")      # deterministic ids per run


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def version_string(self):
        return "webserver"

    def log_message(self, *args):
        pass

    def send(self, code, body=None, content_type="application/json;charset=UTF-8"):
        data = b"" if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
        self.send_response(code)
        if data:
            self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or b"{}")

    def route(self, method):
        path, _, query = self.path.partition("?")
        params = dict(p.split("=", 1) for p in query.split("&") if "=" in p)
        params = {k: v.replace("%3A", ":").replace("%3a", ":") for k, v in params.items()}

        if path == "/dna/system/api/v1/auth/token" and method == "POST":
            return self.auth()
        if not path.startswith(INTENT):
            return self.send(404, {"message": "Not Found"})
        if self.headers.get("X-Auth-Token") != TOKEN:          # no/expired/wrong token
            return self.send(401, {"message": "Unauthorized"})
        sub = path[len(INTENT):]

        if sub == "/network-device" and method == "GET":
            found = [d for d in DEVICES
                     if all(str(d.get(k)) == v for k, v in params.items() if k in d)]
            return self.send(200, {"response": found, "version": "1.0"})
        if sub == "/network-device/count" and method == "GET":
            return self.send(200, {"response": len(DEVICES), "version": "1.0"})
        if sub == "/site-health" and method == "GET":
            return self.send(200, {"response": SITE_HEALTH})
        if sub == "/topology/physical-topology" and method == "GET":
            return self.topology()
        if sub == "/client-detail" and method == "GET":
            return self.client_detail(params)
        if sub == "/network-device-poller/cli/read-request" and method == "POST":
            return self.command_runner()
        match = re.fullmatch(r"/task/([0-9a-f-]+)", sub)
        if match and method == "GET":
            return self.task(match.group(1))
        match = re.fullmatch(r"/file/([0-9a-f-]+)", sub)
        if match and method == "GET":
            if match.group(1) not in files:
                return self.send(404, {"response": {"errorCode": "NOT_FOUND", "message": "File not found"}})
            return self.send(200, json.dumps(files[match.group(1)]).encode(), "application/octet-stream")
        return self.send(404, {"response": {"errorCode": "NOT_FOUND", "message": f"No API at {path}"}})

    def auth(self):
        try:
            scheme, b64 = self.headers.get("Authorization", "").split(" ", 1)
            user, pwd = base64.b64decode(b64).decode().split(":", 1)
        except ValueError:
            return self.send(401)
        if scheme != "Basic" or USERS.get(user) != pwd:
            return self.send(401)                               # real API: 401, empty body
        return self.send(200, {"Token": TOKEN}, "application/json")

    def topology(self):
        nodes = [{"id": d["id"], "label": d["hostname"], "ip": d["managementIpAddress"],
                  "family": d["family"], "role": d["role"], "nodeType": "device"} for d in DEVICES]
        links = [{"source": ID_BY_NAME[a], "startPortName": ap, "target": ID_BY_NAME[b],
                  "endPortName": bp, "linkStatus": "up"} for a, ap, b, bp in LINKS]
        return self.send(200, {"response": {"nodes": nodes, "links": links}, "version": "1.0"})

    def client_detail(self, params):
        mac = params.get("macAddress", "").lower()
        if not mac:
            return self.send(400, {"response": {"errorCode": "Bad Request", "message": "macAddress is required"}})
        if mac not in CLIENTS:
            return self.send(404, {"response": {"errorCode": 1005, "message": "Entity not found",
                                                "detail": "Entity not found"}})
        return self.send(200, {"detail": CLIENTS[mac], "connectionInfo": {}, "topology": {}})

    def command_runner(self):
        req = self.body()
        commands, uuids = req.get("commands", []), req.get("deviceUuids", [])
        if not commands or not uuids:
            return self.send(400, {"response": {"errorCode": "Bad Request",
                                                "message": "commands and deviceUuids are required"}})
        n = len(tasks)
        task_id, file_id = str(uuid.uuid5(IDS, f"task{n}")), str(uuid.uuid5(IDS, f"file{n}"))
        results = []
        for dev_id in uuids:
            name = BY_ID.get(dev_id, {}).get("hostname", "unknown")
            ok, blocked = {}, {}
            for cmd in commands:
                if cmd.split()[0] in BLOCKED:
                    blocked[cmd] = "The command is on the blocked list and is not supported"
                else:
                    ok[cmd] = f"{cmd}\n{name} uptime is 1 week, 4 days, 22 hours, 0 minutes\n{name}#"
            results.append({"deviceUuid": dev_id,
                            "commandResponses": {"SUCCESS": ok, "BLOCKLISTED": blocked, "FAILURE": {}}})
        files[file_id] = results
        tasks[task_id] = {"polls": 0, "fileId": file_id}
        return self.send(202, {"response": {"taskId": task_id, "url": f"/api/v1/task/{task_id}"},
                               "version": "1.0"})

    def task(self, task_id):
        if task_id not in tasks:
            return self.send(404, {"response": {"errorCode": "NOT_FOUND",
                                                "message": "No task corresponding to the id was found"}})
        task = tasks[task_id]
        task["polls"] += 1
        body = {"id": task_id, "serviceType": "Command Runner Service", "username": "devnetuser",
                "isError": False, "startTime": 1791633401239}
        if task["polls"] < 2:                                   # first poll: still running
            body["progress"] = "CLI Runner request creation"
        else:                                                   # then: done, progress holds fileId
            body.update(endTime=1791633401604, progress=json.dumps({"fileId": task["fileId"]}))
        return self.send(200, {"response": body, "version": "1.0"})

    def do_GET(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")


if __name__ == "__main__":
    print(f"Mock Catalyst Center on http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
