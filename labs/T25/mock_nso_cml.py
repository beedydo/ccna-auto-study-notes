"""Mock NSO RESTCONF + CML REST API for the T25 lab (stdlib + PyYAML).

Run:  python3 labs/T25/mock_nso_cml.py      -> http://127.0.0.1:8125
  NSO part: /restconf/...   (real NSO: http://<nso>:8080/restconf, Basic auth)
  CML part: /api/v0/...     (real CML: https://<cml>/api/v0, Bearer JWT)

It models just enough of each product to teach the exam ideas:
  NSO: CDB vs device copy, check-sync / sync-from / sync-to, dry-run=native per NED,
       all-or-nothing commit, FASTMAP (service remembers what it created), rollback ids.
  CML: authenticate -> import YAML -> start -> converge -> nodes -> pyATS testbed -> stop/wipe/delete.
Response shapes follow the NSO and CML docs where known; see "To verify" in the T25 note.
Credentials are fake, for this local mock only.
"""
import base64
import json
import re
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, unquote, urlparse

import yaml

HOST, PORT = "127.0.0.1", 8125
NSO_USER, NSO_PASS = "admin", "admin"
CML_USER, CML_PASS = "admin", "T25-mock-pass"
CML_TOKEN = "eyJhbGciOiJIUzI1NiJ9.t25-mock.jwt"

# ---------------------------------------------------------------- NSO state
DEVICES = {
    "ios0":   {"address": "10.10.20.51", "type": "cli",     "ned": "cisco-ios-cli-6.106"},
    "xr0":    {"address": "10.10.20.52", "type": "cli",     "ned": "cisco-iosxr-cli-7.61"},
    "junos0": {"address": "10.10.20.53", "type": "netconf", "ned": "juniper-junos-nc-4.17"},
}
# Each config = {"loopbacks": {id: ipv4}, "extra": [lines]}
cdb = {name: {"loopbacks": {}, "extra": []} for name in DEVICES}         # NSO's copy
real = {name: {"loopbacks": {}, "extra": []} for name in DEVICES}        # what the box runs
real["ios0"]["extra"].append("ntp server 10.10.20.99")                   # out-of-band CLI change
services = {}       # name -> service data as sent
owned = {}          # FASTMAP bookkeeping: name -> {device: (id, ipv4)}
next_rollback = [10002]

# ---------------------------------------------------------------- CML state
labs = {}
converge_polls = {}


def junos_rpc(unit_xml):
    return ('<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="1">\n'
            '  <edit-config xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">\n'
            '    <target><candidate/></target>\n'
            '    <config>\n'
            '      <configuration xmlns="http://xml.juniper.net/xnm/1.1/xnm">\n'
            '        <interfaces><interface><name>lo0</name>\n'
            f'          {unit_xml}\n'
            '        </interface></interfaces>\n'
            '      </configuration>\n'
            '    </config>\n'
            '  </edit-config>\n'
            '</rpc>\n')


def native(device, op, lo_id, ipv4=None):
    """Render what the device's NED would send: CLI for CLI NEDs, edit-config for NETCONF."""
    ned = DEVICES[device]["ned"]
    if ned.startswith("cisco-ios-cli"):
        if op == "delete":
            return f"no interface Loopback{lo_id}\n"
        return f"interface Loopback{lo_id}\n ip address {ipv4} 255.255.255.255\nexit\n"
    if ned.startswith("cisco-iosxr-cli"):
        if op == "delete":
            return f"no interface Loopback{lo_id}\n"
        return f"interface Loopback{lo_id}\n ipv4 address {ipv4} 255.255.255.255\nexit\n"
    if op == "delete":
        return junos_rpc(f'<unit nc:operation="delete"><name>{lo_id}</name></unit>')
    return junos_rpc(f"<unit><name>{lo_id}</name><family><inet><address>"
                     f"<name>{ipv4}/32</name></address></inet></family></unit>")


def plan(name, new_service):
    """FASTMAP: run the mapping again for the new service state, diff against what the
    service owned last time. Returns {device: [(op, id, ipv4)]}."""
    before = owned.get(name, {})
    after = {}
    if new_service is not None:
        for dev in new_service["device"]:
            after[dev] = (new_service["id"], new_service["ipv4"])
    ops = {}
    for dev in sorted(set(before) | set(after), key=list(DEVICES).index):
        if dev in before and dev not in after:
            ops[dev] = [("delete", before[dev][0], None)]
        elif dev in after and before.get(dev) != after[dev]:
            if dev in before and before[dev][0] != after[dev][0]:
                ops[dev] = [("delete", before[dev][0], None)]
            ops.setdefault(dev, []).append(("create", *after[dev]))
    return ops, after


def in_sync(dev):
    return cdb[dev] == real[dev]


def nso_error(tag, message):
    return {"ietf-restconf:errors": {"error": [
        {"error-type": "application", "error-tag": tag, "error-message": message}]}}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def version_string(self):
        return "MockNSO-CML/1.0"

    def log_message(self, *args):
        pass

    def send(self, code, body=None, headers=None, content_type="application/yang-data+json"):
        data = b""
        if body is not None:
            data = body.encode() if isinstance(body, str) else json.dumps(body, indent=2).encode()
        self.send_response(code)
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        if data:
            self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length).decode() if length else ""

    # ------------------------------------------------------------ routing
    def route(self, method):
        url = urlparse(self.path)
        path, query = unquote(url.path), parse_qs(url.query, keep_blank_values=True)
        if path == "/health":
            return self.send(200, {"status": "ok"}, content_type="application/json")
        if path.startswith("/restconf"):
            return self.nso(method, path, query)
        if path.startswith("/api/v0"):
            return self.cml(method, path, query)
        return self.send(404, {"error": "not found"}, content_type="application/json")

    def do_GET(self): self.route("GET")
    def do_POST(self): self.route("POST")
    def do_PUT(self): self.route("PUT")
    def do_PATCH(self): self.route("PATCH")
    def do_DELETE(self): self.route("DELETE")

    # ------------------------------------------------------------ NSO
    def nso(self, method, path, query):
        auth = self.headers.get("Authorization", "")
        expected = "Basic " + base64.b64encode(f"{NSO_USER}:{NSO_PASS}".encode()).decode()
        if auth != expected:
            return self.send(401, {"ietf-restconf:errors": {"error": [
                {"error-type": "protocol", "error-tag": "access-denied"}]}})
        data = "/restconf/data"

        if method == "GET" and path == f"{data}/tailf-ncs:devices/device":
            return self.send(200, {"tailf-ncs:device": [
                {"name": n, "address": d["address"], "device-type": {d["type"]: {"ned-id": d["ned"]}}}
                for n, d in DEVICES.items()]})

        if method == "POST" and path == f"{data}/tailf-ncs:devices/check-sync":
            return self.send(200, {"tailf-ncs:output": {"sync-result": [
                {"device": n, "result": "in-sync" if in_sync(n) else "out-of-sync"} for n in DEVICES]}})

        m = re.fullmatch(rf"{data}/tailf-ncs:devices/device=([\w-]+)/(sync-from|sync-to|check-sync)", path)
        if method == "POST" and m:
            dev, action = m.groups()
            if dev not in DEVICES:
                return self.send(404, nso_error("invalid-value", f"device {dev} not found"))
            if action == "sync-from":
                cdb[dev] = json.loads(json.dumps(real[dev]))     # read the box into CDB
            elif action == "sync-to":
                real[dev] = json.loads(json.dumps(cdb[dev]))     # push CDB to the box
            else:
                return self.send(200, {"tailf-ncs:output": {
                    "result": "in-sync" if in_sync(dev) else "out-of-sync"}})
            return self.send(200, {"tailf-ncs:output": {"result": True}})

        m = re.fullmatch(rf"{data}/tailf-ncs:devices/device=([\w-]+)/config/"
                         r"tailf-ned-cisco-ios:interface/Loopback=(\d+)", path)
        if method == "GET" and m:
            dev, lo_id = m.group(1), int(m.group(2))
            ip = cdb.get(dev, {}).get("loopbacks", {}).get(lo_id)
            if ip is None:
                return self.send(404, nso_error("invalid-value", "uri keypath not found"))
            return self.send(200, {"tailf-ned-cisco-ios:Loopback": [{"name": str(lo_id), "ip": {
                "address": {"primary": {"address": ip, "mask": "255.255.255.255"}}}}]})

        # ---- services: create (POST /data), replace (PUT), delete (DELETE)
        if method == "POST" and path == data:
            svc = json.loads(self.body())["loopback:loopback"][0]
            if svc["name"] in services:
                return self.send(409, nso_error("data-exists", "object already exists"))
            return self.commit(svc["name"], svc, query, created=True)
        m = re.fullmatch(rf"{data}/loopback:loopback=([\w-]+)", path)
        if m and method == "PUT":
            svc = json.loads(self.body())["loopback:loopback"][0]
            return self.commit(m.group(1), svc, query)
        if m and method == "DELETE":
            if m.group(1) not in services:
                return self.send(404, nso_error("invalid-value", "uri keypath not found"))
            return self.commit(m.group(1), None, query)
        if m and method == "GET":
            if m.group(1) not in services:
                return self.send(404, nso_error("invalid-value", "uri keypath not found"))
            return self.send(200, {"loopback:loopback": [services[m.group(1)]]})
        return self.send(404, nso_error("invalid-value", "uri keypath not found"))

    def commit(self, name, svc, query, created=False):
        """One NSO transaction: FASTMAP plan -> out-of-sync check -> dry-run or apply all."""
        ops, after = plan(name, svc)
        for dev in ops:                                  # all-or-nothing: check every device first
            if not in_sync(dev):
                return self.send(409, nso_error(
                    "in-use", f"Network Element Driver: device {dev}: out of sync"))
        if "dry-run" in query:
            return self.send(200, {"dry-run-result": {"native": {"device": [
                {"name": dev, "data": "".join(native(dev, *op) for op in dev_ops)}
                for dev, dev_ops in ops.items()]}}})
        for dev, dev_ops in ops.items():                 # apply to CDB and device together
            for op, lo_id, ipv4 in dev_ops:
                for store in (cdb[dev], real[dev]):
                    if op == "delete":
                        store["loopbacks"].pop(lo_id, None)
                    else:
                        store["loopbacks"][lo_id] = ipv4
        if svc is None:
            services.pop(name, None)
            owned.pop(name, None)
        else:
            services[name], owned[name] = svc, after
        headers, body = {}, None
        if query.get("rollback-id") == ["true"]:
            body = {"tailf-restconf:result": {"rollback": {"id": next_rollback[0]}}}
            next_rollback[0] += 1
        if created:
            headers["Location"] = f"/restconf/data/loopback:loopback={name}"
            return self.send(201, body, headers)
        return self.send(200 if body else 204, body, headers)

    # ------------------------------------------------------------ CML
    def cml(self, method, path, query):
        if method == "POST" and path == "/api/v0/authenticate":
            creds = json.loads(self.body() or "{}")
            if (creds.get("username"), creds.get("password")) != (CML_USER, CML_PASS):
                return self.send(403, {"description": "Authentication failed!"},
                                 content_type="application/json")
            return self.send(200, json.dumps(CML_TOKEN), content_type="application/json")
        if self.headers.get("Authorization") != f"Bearer {CML_TOKEN}":
            return self.send(401, {"description": "No authorization token provided."},
                             content_type="application/json")

        if method == "POST" and path == "/api/v0/import":
            topo = yaml.safe_load(self.body())
            lab_id = str(uuid.UUID(int=0x25))
            labs[lab_id] = {"title": query.get("title", [topo["lab"]["title"]])[0],
                            "state": "DEFINED_ON_CORE", "nodes": topo["nodes"]}
            converge_polls[lab_id] = 0
            return self.send(200, {"id": lab_id, "warnings": []}, content_type="application/json")

        m = re.fullmatch(r"/api/v0/labs/([\w-]+)(?:/(\w+))?", path)
        if not m or m.group(1) not in labs:
            return self.send(404, {"description": "Lab not found"}, content_type="application/json")
        lab_id, action = m.groups()
        lab = labs[lab_id]
        if method == "PUT" and action in ("start", "stop", "wipe"):
            lab["state"] = {"start": "STARTED", "stop": "STOPPED", "wipe": "DEFINED_ON_CORE"}[action]
            converge_polls[lab_id] = 0
            return self.send(204)
        if method == "GET" and action == "state":
            return self.send(200, json.dumps(lab["state"]), content_type="application/json")
        if method == "GET" and action == "check_if_converged":
            converge_polls[lab_id] += 1
            done = lab["state"] != "STARTED" or converge_polls[lab_id] >= 3   # boots on 3rd poll
            return self.send(200, json.dumps(done), content_type="application/json")
        if method == "GET" and action == "nodes":
            node_state = {"STARTED": "BOOTED", "STOPPED": "STOPPED"}.get(lab["state"], "DEFINED_ON_CORE")
            return self.send(200, [{"id": n["id"], "label": n["label"],
                                    "node_definition": n["node_definition"], "state": node_state}
                                   for n in lab["nodes"]], content_type="application/json")
        if method == "GET" and action == "pyats_testbed":
            os_map = {"iosv": "ios", "iosxrv9000": "iosxr"}
            lines = ["testbed:", f"  name: {lab['title']}", "devices:"]
            for n in lab["nodes"]:
                lines += [f"  {n['label']}:", f"    os: {os_map.get(n['node_definition'], 'linux')}",
                          "    connections:", "      a:", "        protocol: telnet",
                          "        proxy: terminal_server", f"        command: open /{lab_id}/{n['id']}/0"]
            return self.send(200, "\n".join(lines) + "\n", content_type="application/yaml")
        if method == "DELETE" and action is None:
            if lab["state"] != "DEFINED_ON_CORE":
                return self.send(400, {"description": "Lab must be stopped and wiped first"},
                                 content_type="application/json")
            del labs[lab_id]
            return self.send(204)
        return self.send(405, {"description": f"{method} not allowed"}, content_type="application/json")


if __name__ == "__main__":
    HTTPServer((HOST, PORT), Handler).serve_forever()
