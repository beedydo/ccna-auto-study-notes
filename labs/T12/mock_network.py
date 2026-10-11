"""Mock network for the T12 lab: three switches + one controller (Python stdlib only).

Run:  python3 labs/T12/mock_network.py        -> http://127.0.0.1:18012

One process plays four boxes. Each one has its own path prefix (a real network
would use one hostname per box, e.g. https://sw1/restconf/...):

  /sw1  /sw2   Catalyst 9300 switches, IOS XE   (device-level APIs)
  /sw3         Nexus 9300 switch, NX-OS          (device-level APIs)
  /ctrl        a generic SDN controller          (controller-level API)

Device-level, per switch:
  GET   /swN/cli?cmd=<show command>     plain CLI text, as an SSH session would print it
                                        (stand-in for Netmiko/Paramiko send_command)
  GET   /swN/restconf/data/openconfig-interfaces:interfaces
  PATCH /swN/restconf/data/openconfig-interfaces:interfaces/interface=<name>/config
        media type application/yang-data+json, body {"openconfig-interfaces:config": {...}}
        values are checked against the model (boolean, string); a bad value -> 400 +
        ietf-restconf:errors and NOTHING in the request is applied

Controller-level (a teaching stand-in: real controllers have their own paths, see T19/T20/T22):
  GET   /ctrl/api/v1/devices            network-wide inventory
  POST  /ctrl/api/v1/intents            {"intent": "disable-unused-ports", "site": "SG-HQ"} -> 202 + taskId
  GET   /ctrl/api/v1/tasks/<taskId>     what the controller pushed southbound to each device

Test helper:  POST /_mock/reset  puts every port back to its starting state.
Auth: HTTP Basic on every box (user/password from T12_USER / T12_PASS).
"""
import base64
import copy
import json
import os
import re
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

HOST, PORT = "127.0.0.1", int(os.environ.get("T12_PORT", "18012"))
USER = os.environ.get("T12_USER", "admin")
PASS = os.environ.get("T12_PASS", "C1sco12345")
YANG_JSON = "application/yang-data+json"
OC = "openconfig-interfaces"


def _port(name, oper, desc=""):
    return {"name": name,
            "config": {"name": name, "type": "iana-if-type:ethernetCsmacd", "description": desc, "enabled": True},
            "state": {"name": name, "type": "iana-if-type:ethernetCsmacd", "description": desc, "enabled": True,
                      "admin-status": "UP", "oper-status": oper}}


START = {
    "sw1": {"site": "SG-HQ", "platform": "C9300-48P", "os": "IOS XE 17.9.4", "mgmt": "10.10.20.11",
            "ports": [_port("GigabitEthernet1/0/1", "UP", "uplink core1"), _port("GigabitEthernet1/0/2", "UP", "bob-laptop"),
                      _port("GigabitEthernet1/0/3", "DOWN"), _port("GigabitEthernet1/0/4", "DOWN")]},
    "sw2": {"site": "SG-HQ", "platform": "C9300-24T", "os": "IOS XE 17.9.4", "mgmt": "10.10.20.12",
            "ports": [_port("GigabitEthernet1/0/1", "UP", "uplink core1"), _port("GigabitEthernet1/0/2", "DOWN"),
                      _port("GigabitEthernet1/0/3", "UP", "printer-l2")]},
    "sw3": {"site": "SG-HQ", "platform": "N9K-C93180YC-FX3", "os": "NX-OS 10.3(4a)", "mgmt": "10.10.20.13",
            "ports": [_port("Ethernet1/1", "UP", "uplink core1"), _port("Ethernet1/2", "DOWN"), _port("Ethernet1/3", "DOWN")]},
}
DEVICES = copy.deepcopy(START)
TASKS = {}


def cli_text(dev, cmd):
    """Render the port table the way each OS prints it (two different layouts)."""
    d = DEVICES[dev]
    if d["os"].startswith("IOS XE") and cmd == "show ip interface brief":
        rows = ["Interface              IP-Address      OK? Method Status                Protocol"]
        for p in d["ports"]:
            st = p["state"]["oper-status"].lower()
            status = "administratively down" if not p["config"]["enabled"] else st
            rows.append(f"{p['name']:<22} unassigned      YES unset  {status:<21} {st}")
        return "\n".join(rows) + "\n"
    if d["os"].startswith("NX-OS") and cmd == "show interface brief":
        rows = ["-" * 80,
                "Ethernet        VLAN    Type Mode   Status  Reason                   Speed     Port",
                "Interface                                                                    Ch #",
                "-" * 80]
        for p in d["ports"]:
            short = p["name"].replace("Ethernet", "Eth")
            st = p["state"]["oper-status"].lower()
            reason = "none" if st == "up" else ("Administratively down" if not p["config"]["enabled"] else "Link not connected")
            rows.append(f"{short:<15} 1       eth  access {st:<7} {reason:<24} auto(D)   --")
        return "\n".join(rows) + "\n"
    return f"% Invalid input detected at '^' marker.\n"


def rc_error(tag, path, msg, etype="application"):
    return {"ietf-restconf:errors": {"error": [
        {"error-type": etype, "error-tag": tag, "error-path": path, "error-message": msg}]}}


def apply_config(dev, ifname, cfg):
    """Validate the whole edit against the model first, then apply it (all or nothing)."""
    port = next((p for p in DEVICES[dev]["ports"] if p["name"] == ifname), None)
    if port is None:
        return 404, rc_error("invalid-value", f"/{OC}:interfaces/interface[name='{ifname}']", "uri keypath not found")
    rules = {"description": str, "enabled": bool, "name": str, "type": str}
    for leaf, value in cfg.items():
        path = f"/{OC}:interfaces/interface[name='{ifname}']/config/{leaf}"
        if leaf not in rules:
            return 400, rc_error("unknown-element", path, f"unknown leaf '{leaf}'")
        if not isinstance(value, rules[leaf]):
            want = "boolean" if rules[leaf] is bool else "string"
            return 400, rc_error("invalid-value", path, f"invalid value '{value}' for type {want}")
    for leaf, value in cfg.items():            # nothing was changed until every leaf passed
        port["config"][leaf] = value
        if leaf in ("description", "enabled"):
            port["state"][leaf] = value
        if leaf == "enabled":
            port["state"]["admin-status"] = "UP" if value else "DOWN"
    return 204, None


def run_intent(body):
    """The controller translates one intent into per-device southbound RESTCONF edits."""
    if body.get("intent") != "disable-unused-ports":
        return 400, {"error": "unsupported intent", "supported": ["disable-unused-ports"]}
    site = body.get("site")
    targets = [n for n, d in DEVICES.items() if d["site"] == site]
    if not targets:
        return 400, {"error": f"unknown site '{site}'"}
    actions = []
    for dev in targets:
        for p in DEVICES[dev]["ports"]:
            if p["state"]["oper-status"] == "DOWN" and p["config"]["enabled"]:
                cfg = {"description": "UNUSED (ctrl intent)", "enabled": False}
                code, _ = apply_config(dev, p["name"], cfg)
                actions.append({"device": dev, "protocol": "RESTCONF", "method": "PATCH",
                                "interface": p["name"], "result": code})
    task_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"t12-task-{len(TASKS) + 1}"))   # repeatable IDs for the lab
    TASKS[task_id] = {"taskId": task_id, "intent": body["intent"], "site": site, "status": "SUCCESS",
                      "devices": len(targets), "southbound": actions}
    return 202, {"taskId": task_id, "url": f"/ctrl/api/v1/tasks/{task_id}"}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def version_string(self):
        return "MockNet/1.0"

    def log_message(self, *args):
        pass

    def send(self, code, body=None, ctype="application/json"):
        data = b"" if body is None else (body.encode() if isinstance(body, str) else json.dumps(body).encode())
        self.send_response(code)
        if data:
            self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def authed(self):
        want = "Basic " + base64.b64encode(f"{USER}:{PASS}".encode()).decode()
        if self.headers.get("Authorization") == want:
            return True
        self.send(401, {"error": "authentication failed"})
        return False

    def body(self):
        n = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(n) if n else b"{}"
        return json.loads(raw or b"{}")

    def route(self, method):
        url = urlparse(self.path)
        path = url.path
        if method == "POST" and path == "/_mock/reset":
            DEVICES.clear(); DEVICES.update(copy.deepcopy(START)); TASKS.clear()
            return self.send(204)
        if not self.authed():
            return
        m = re.match(r"^/(sw[1-3])(/.*)$", path)
        if m:
            return self.device(method, m.group(1), m.group(2), url.query)
        if path.startswith("/ctrl/api/v1/"):
            return self.controller(method, path[len("/ctrl/api/v1/"):])
        self.send(404, {"error": "no such box"})

    def device(self, method, dev, rest, query):
        if method == "GET" and rest == "/cli":
            cmd = parse_qs(query).get("cmd", [""])[0]
            return self.send(200, cli_text(dev, cmd), "text/plain")
        base = f"/restconf/data/{OC}:interfaces"
        if method == "GET" and rest == base:
            ports = [copy.deepcopy(p) for p in DEVICES[dev]["ports"]]
            return self.send(200, {f"{OC}:interfaces": {"interface": ports}}, YANG_JSON)
        m = re.match(rf"^{re.escape(base)}/interface=([^/]+)/config$", rest)
        if method == "PATCH" and m:
            if self.headers.get("Content-Type") != YANG_JSON:
                return self.send(415, rc_error("invalid-value", rest, f"Content-Type must be {YANG_JSON}", "protocol"), YANG_JSON)
            ifname = unquote(m.group(1))       # GigabitEthernet1%2F0%2F3 -> GigabitEthernet1/0/3
            cfg = self.body().get(f"{OC}:config", {})
            code, err = apply_config(dev, ifname, cfg)
            return self.send(code, err, YANG_JSON)
        self.send(404, rc_error("invalid-value", rest, "uri keypath not found"), YANG_JSON)

    def controller(self, method, rest):
        if method == "GET" and rest == "devices":
            inv = [{"hostname": n, "site": d["site"], "platform": d["platform"], "softwareVersion": d["os"],
                    "managementIp": d["mgmt"], "reachability": "Reachable",
                    "portsDown": sum(p["state"]["oper-status"] == "DOWN" for p in d["ports"]),
                    "portsAdminDown": sum(not p["config"]["enabled"] for p in d["ports"])}
                   for n, d in DEVICES.items()]
            return self.send(200, {"response": inv})
        if method == "POST" and rest == "intents":
            code, body = run_intent(self.body())
            return self.send(code, body)
        m = re.match(r"^tasks/([0-9a-f-]+)$", rest)
        if method == "GET" and m and m.group(1) in TASKS:
            return self.send(200, TASKS[m.group(1)])
        self.send(404, {"error": "not found"})

    def do_GET(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")

    def do_PATCH(self):
        self.route("PATCH")


if __name__ == "__main__":
    print(f"T12 mock network on http://{HOST}:{PORT}  (sw1 sw2 sw3 ctrl)")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
