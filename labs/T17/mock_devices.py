"""Mock Nexus (NX-API CLI + NX-API REST) and IOS XE (RESTCONF) devices for the T17 lab.

Python stdlib only. Two fake devices, one process:
    NX-OS  "sbx-n9kv"  http://127.0.0.1:18443   /ins  (NX-API CLI)   /api/...  (NX-API REST / DME)
    IOS XE "csr1"      http://127.0.0.1:18444   /restconf/data/...  (RESTCONF, see T16)

Real devices use HTTPS on 443. The mock uses plain HTTP so no certificates are needed.
Response shapes follow the Cisco NX-API CLI / NX-API REST docs; see the T17 note's Sources.
Both "APIs" read and write ONE shared state, the way NX-OS keeps one DME database
behind every interface. Credentials below are fake, for this local mock only.
"""
import base64
import json
import re
import secrets
import threading
from urllib.parse import unquote
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from xml.sax.saxutils import escape

HOST = "127.0.0.1"
NXOS_PORT, IOSXE_PORT = 18443, 18444
USER, PASSWORD = "admin", "Admin_1234!"
REST_TOKENS = set()          # NX-API REST tokens handed out by aaaLogin

# ---------- one shared state = the DME ----------
HOSTNAME = "sbx-n9kv"
interfaces = {               # DME l1PhysIf objects, keyed by DME id (lower-case "eth1/1")
    f"eth1/{n}": {"id": f"eth1/{n}", "descr": "", "adminSt": "up", "mtu": "1500",
                  "mode": "access", "layer": "Layer2"} for n in range(1, 6)
}
interfaces["eth1/1"]["descr"] = "to-server1"
oper = {"eth1/1": "up", "eth1/2": "up", "eth1/3": "down", "eth1/4": "down", "eth1/5": "up"}
vlans = {1: "default", 10: "SERVERS"}        # DME l2BD objects: vlan id -> name


def cli_name(dme_id):                        # "eth1/5" -> "Ethernet1/5"
    return "Ethernet" + dme_id[3:]


def dme_id(cli):                             # "ethernet1/5", "Eth1/5", "e1/5" -> "eth1/5"
    m = re.fullmatch(r"(?i)e(?:th(?:ernet)?)?\s*(\d+/\d+)", cli.strip())
    return f"eth{m.group(1)}" if m else None


# ---------- NX-API CLI: show commands -> structured bodies ----------
def show(cmd):
    """Return (body_dict, ascii_text) or raise ValueError for an unknown command."""
    cmd = " ".join(cmd.split()).lower()
    if cmd == "show version":
        body = {"header_str": "Cisco Nexus Operating System (NX-OS) Software",
                "bios_ver_str": "", "nxos_ver_str": "10.3(3)", "host_name": HOSTNAME,
                "chassis_id": "Nexus9000 C9300v Chassis", "kern_uptm_days": 12,
                "kern_uptm_hrs": 4, "kern_uptm_mins": 31, "rr_reason": "Unknown"}
        text = (f"Cisco Nexus Operating System (NX-OS) Software\n  NXOS: version 10.3(3)\n"
                f"  cisco Nexus9000 C9300v Chassis\n  Device name: {HOSTNAME}\n")
        return body, text
    if cmd == "show switchname":
        return {"hostname": HOSTNAME}, HOSTNAME + "\n"
    if cmd == "show interface brief":
        rows = [{"interface": "mgmt0", "state": "up", "ip_addr": "10.10.20.95",
                 "speed": "1000", "mtu": "1500"}]
        for i in interfaces.values():
            rows.append({"interface": cli_name(i["id"]), "vlan": "1", "type": "eth",
                         "portmode": "access", "state": oper[i["id"]],
                         "state_rsn_desc": "none" if oper[i["id"]] == "up" else "Link not connected",
                         "speed": "1000" if oper[i["id"]] == "up" else "auto", "ratemode": "D"})
        text = "".join(f"{r['interface']:<14}{r['state']}\n" for r in rows)
        return {"TABLE_interface": {"ROW_interface": rows}}, text
    if cmd == "show vlan brief":
        rows = [{"vlanshowbr-vlanid": v, "vlanshowbr-vlanid-utf": str(v),
                 "vlanshowbr-vlanname": n, "vlanshowbr-vlanstate": "active",
                 "vlanshowbr-shutstate": "noshutdown"} for v, n in sorted(vlans.items())]
        text = "".join(f"{v:<5}{n:<33}active\n" for v, n in sorted(vlans.items()))
        return {"TABLE_vlanbriefxbrief": {"ROW_vlanbriefxbrief": rows}}, text
    m = re.fullmatch(r"show running-config interface (\S+)", cmd)
    if m and dme_id(m.group(1)) in interfaces:
        i = interfaces[dme_id(m.group(1))]
        text = (f"\n!Command: show running-config interface {cli_name(i['id'])}\n\n"
                f"version 10.3(3) Bios:version\n\ninterface {cli_name(i['id'])}\n")
        if i["descr"]:
            text += f"  description {i['descr']}\n"
        return None, text                    # running-config has no structured (JSON) form
    raise ValueError(cmd)


def configure(commands, context=None):
    """Apply config commands in order (context-sensitive, like a real CLI session).
    Returns the context (current interface / vlan) so a caller can carry it on."""
    for raw in commands:
        cmd = " ".join(raw.split())
        low = cmd.lower()
        if low in ("configure terminal", "conf t", "end"):
            continue
        if m := re.fullmatch(r"interface (\S+)", low):
            context = ("intf", dme_id(m.group(1)))
            if context[1] not in interfaces:
                raise ValueError(cmd)
        elif m := re.fullmatch(r"vlan (\d+)", low):
            context = ("vlan", int(m.group(1)))
            vlans.setdefault(context[1], f"VLAN{int(m.group(1)):04d}")
        elif m := re.fullmatch(r"no vlan (\d+)", low):
            vlans.pop(int(m.group(1)), None)
        elif low.startswith("description ") and context and context[0] == "intf":
            interfaces[context[1]]["descr"] = cmd.split(" ", 1)[1]
        elif low.startswith("name ") and context and context[0] == "vlan":
            vlans[context[1]] = cmd.split(" ", 1)[1]
        else:
            raise ValueError(cmd)
    return context


CLI_ERROR = "% Invalid command at '^' marker.\n"


# ---------- NX-API REST: DME objects ----------
def mo_l1(i):
    return {"l1PhysIf": {"attributes": {**i, "dn": f"sys/intf/phys-[{i['id']}]"}}}


def mo_bd(vid):
    return {"l2BD": {"attributes": {"dn": f"sys/bd/bd-[vlan-{vid}]", "fabEncap": f"vlan-{vid}",
                                    "id": str(vid), "name": vlans[vid]}}}


def lookup_dn(dn, target):
    """Return the imdata list for /api/mo/<dn> with query-target self|children."""
    if dn == "sys":
        top = {"topSystem": {"attributes": {"dn": "sys", "name": HOSTNAME,
                                            "serial": "9N3KD63KWT0", "systemUpTime": "12:04:31:07.000"}}}
        kids = [{"interfaceEntity": {"attributes": {"dn": "sys/intf"}}},
                {"bdEntity": {"attributes": {"dn": "sys/bd"}}}]
        return kids if target == "children" else [top]
    if dn == "sys/intf":
        return ([mo_l1(i) for i in interfaces.values()] if target == "children"
                else [{"interfaceEntity": {"attributes": {"dn": "sys/intf"}}}])
    if dn == "sys/bd":
        return ([mo_bd(v) for v in sorted(vlans)] if target == "children"
                else [{"bdEntity": {"attributes": {"dn": "sys/bd"}}}])
    if m := re.fullmatch(r"sys/intf/phys-\[(eth\d+/\d+)\]", dn):
        return [mo_l1(interfaces[m.group(1)])] if m.group(1) in interfaces else []
    if m := re.fullmatch(r"sys/bd/bd-\[vlan-(\d+)\]", dn):
        return [mo_bd(int(m.group(1)))] if int(m.group(1)) in vlans else []
    return []                                # unknown DN: empty imdata, not a 404


CLASSES = {"l1PhysIf": lambda: [mo_l1(i) for i in interfaces.values()],
           "l2BD": lambda: [mo_bd(v) for v in sorted(vlans)],
           "topSystem": lambda: lookup_dn("sys", "self")}


def apply_mo(dn, body):
    """POST = create or update (merge) the object at dn, children included."""
    if m := re.fullmatch(r"sys/intf/phys-\[(eth\d+/\d+)\]", dn):
        attrs = body.get("l1PhysIf", {}).get("attributes", {})
        interfaces[m.group(1)].update({k: v for k, v in attrs.items() if k in ("descr", "adminSt", "mtu")})
        return
    if dn == "sys/bd":
        for child in body.get("bdEntity", {}).get("children", []):
            attrs = child["l2BD"]["attributes"]
            vid = int(attrs["fabEncap"].split("-")[1])
            if attrs.get("status") == "deleted":
                vlans.pop(vid, None)
            else:
                vlans[vid] = attrs.get("name", f"VLAN{vid:04d}")
        return
    raise KeyError(dn)


def rest_error(code, text):
    return {"totalCount": "1", "imdata": [{"error": {"attributes": {"code": str(code), "text": text}}}]}


# ---------- IOS XE RESTCONF (one resource, for contrast; T16 has the full story) ----------
IOSXE_GI1 = {"ietf-interfaces:interface": {
    "name": "GigabitEthernet1", "description": "MANAGEMENT INTERFACE - DON'T TOUCH ME",
    "type": "iana-if-type:ethernetCsmacd", "enabled": True,
    "ietf-ip:ipv4": {"address": [{"ip": "10.10.20.48", "netmask": "255.255.255.0"}]}, "ietf-ip:ipv6": {}}}


def to_xml(tag, value):
    if isinstance(value, dict):
        return f"<{tag}>" + "".join(to_xml(k, v) for k, v in value.items()) + f"</{tag}>"
    if isinstance(value, list):
        return "".join(to_xml(tag, v) for v in value)
    return f"<{tag}>{escape(str(value))}</{tag}>"


class Base(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def version_string(self):
        return "nginx"

    def send(self, code, body=None, ctype="application/json", headers=None):
        data = b"" if body is None else (body if isinstance(body, str) else json.dumps(body)).encode()
        self.send_response(code)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        if data:
            self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        n = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(n).decode() if n else ""

    def basic_ok(self):
        auth = self.headers.get("Authorization", "")
        good = "Basic " + base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()
        return auth == good

    def cookie(self, name):
        for part in self.headers.get("Cookie", "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == name:
                return v
        return None


class NXOS(Base):
    # ---- NX-API CLI: everything is POST /ins ----
    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/ins":
            return self.nxapi_cli()
        if path == "/api/aaaLogin.json":
            return self.aaa_login()
        if path.startswith("/api/mo/"):
            return self.rest("POST", path)
        self.send(404, {"error": "not found"})

    def do_GET(self):
        path = self.path.split("?")[0]
        if path.startswith("/api/mo/") or path.startswith("/api/class/"):
            return self.rest("GET", path)
        if path == "/ins":
            return self.send(405, {"error": "NX-API CLI accepts POST only"}, headers={"Allow": "POST"})
        self.send(404, {"error": "not found"})

    def do_DELETE(self):
        self.rest("DELETE", self.path.split("?")[0])

    def nxapi_cli(self):
        if not (self.basic_ok() or self.cookie("nxapi_auth") == "mock-nxapi-session"):
            return self.send(401, "<html><body>401 Authorization Required</body></html>", "text/html",
                             {"WWW-Authenticate": 'Basic realm="Secure Zone"'})
        session = {"Set-Cookie": "nxapi_auth=mock-nxapi-session; Max-Age=600"}   # 600 s, fixed
        ctype = self.headers.get("Content-Type", "").split(";")[0]
        raw = self.body()
        if ctype == "application/json-rpc":
            return self.json_rpc(json.loads(raw), session)
        if ctype == "application/json":
            req = json.loads(raw)["ins_api"]
        elif ctype == "application/xml":
            req = {t: (re.search(f"<{t}>(.*?)</{t}>", raw, re.S) or [None, ""])[1]
                   for t in ("version", "type", "chunk", "sid", "input", "output_format")}
        else:
            return self.send(415, {"error": f"unsupported Content-Type '{ctype}'"})
        outputs, http = self.run_ins(req)
        fmt = req.get("output_format", "json")
        if fmt == "xml":
            xml = ('<?xml version="1.0"?>\n<ins_api><type>%s</type><version>%s</version><sid>eoc</sid>'
                   '<outputs>%s</outputs></ins_api>' % (req["type"], req["version"],
                                                         "".join(to_xml("output", o) for o in outputs)))
            return self.send(http, xml, "text/xml", session)
        reply = {"ins_api": {"type": req["type"], "version": req["version"], "sid": "eoc",
                             "outputs": {"output": outputs[0] if len(outputs) == 1 else outputs}}}
        self.send(http, reply, "application/json", session)

    def run_ins(self, req):
        """ins_api: commands in one string, separated by ' ;'. Returns (outputs, http_status)."""
        cmds = [c.strip() for c in req["input"].split(" ;") if c.strip()]
        kind = req["type"]
        if kind == "cli_conf":                # config needs context: one output for all commands
            try:
                configure(cmds)
                return [{"body": {}, "code": "200", "msg": "Success"}], 200
            except ValueError as bad:
                return [{"code": "400", "msg": "CLI execution error",
                         "clierror": f"{bad}\n{CLI_ERROR}"}], 400
        outputs, status = [], 200
        for cmd in cmds:
            try:
                structured, text = show(cmd)
                if kind == "cli_show" and structured is None:
                    outputs.append({"input": cmd, "code": "501", "msg": "Structured output unsupported"})
                    status = 400
                    continue
                body = structured if kind == "cli_show" else text
                outputs.append({"input": cmd, "body": body, "code": "200", "msg": "Success"})
            except ValueError:
                outputs.append({"input": cmd, "code": "400", "msg": "Input CLI command error",
                                "clierror": CLI_ERROR})
                status = 400
        return outputs, status

    def json_rpc(self, calls, session):
        """JSON-RPC 2.0: one object per command; method cli or cli_ascii."""
        replies, status, context = [], 200, None
        for call in calls:
            cmd, rid = call["params"]["cmd"], call["id"]
            try:
                if cmd.lower().startswith("show"):
                    structured, text = show(cmd)
                    result = {"msg": text} if call["method"] == "cli_ascii" or structured is None \
                        else {"body": structured}
                else:                        # config commands keep context across the array
                    context = configure([cmd], context)
                    result = None
                replies.append({"jsonrpc": "2.0", "result": result, "id": rid})
            except (ValueError, KeyError):
                replies.append({"jsonrpc": "2.0", "error": {"code": -32602, "message": "Invalid params",
                                "data": {"msg": CLI_ERROR}}, "id": rid})
                status = 500
                break                         # NX-API stops at the first failing command
        self.send(status, replies[0] if len(replies) == 1 else replies, "application/json-rpc", session)

    # ---- NX-API REST (DME) ----
    def aaa_login(self):
        attrs = json.loads(self.body() or "{}").get("aaaUser", {}).get("attributes", {})
        if (attrs.get("name"), attrs.get("pwd")) != (USER, PASSWORD):
            return self.send(401, rest_error(401, "Authentication failed"))
        token = secrets.token_urlsafe(24)
        REST_TOKENS.add(token)
        reply = {"imdata": [{"aaaLogin": {"attributes": {
            "token": token, "refreshTimeoutSeconds": "600", "userName": USER, "remoteUser": "false"}}}]}
        self.send(200, reply, headers={"Set-Cookie": f"APIC-cookie={token}; Path=/; HttpOnly"})

    def rest(self, method, path):
        if self.cookie("APIC-cookie") not in REST_TOKENS:
            return self.send(403, rest_error(403, "Need a valid webtoken cookie (named APIC-cookie)"))
        query = dict(p.split("=", 1) for p in self.path.partition("?")[2].split("&") if "=" in p)
        m = re.fullmatch(r"/api/(mo|class)/(.+)\.(json|xml)", unquote(path))
        if not m:
            return self.send(400, rest_error(400, "malformed URI"))
        kind, name, _ = m.groups()
        if method == "GET":
            data = (CLASSES.get(name, lambda: [])() if kind == "class"
                    else lookup_dn(name, query.get("query-target", "self")))
            return self.send(200, {"totalCount": str(len(data)), "imdata": data})
        if method == "POST" and kind == "mo":
            try:
                apply_mo(name, json.loads(self.body()))
            except (KeyError, ValueError):
                return self.send(400, rest_error(400, f"cannot apply payload to dn {name}"))
            return self.send(200, {"totalCount": "0", "imdata": []})
        if method == "DELETE" and kind == "mo":
            if bd := re.fullmatch(r"sys/bd/bd-\[vlan-(\d+)\]", name):
                vlans.pop(int(bd.group(1)), None)
                return self.send(200, {"totalCount": "0", "imdata": []})
            return self.send(400, rest_error(400, f"cannot delete dn {name}"))
        self.send(405, rest_error(405, "method not allowed"))


class IOSXE(Base):
    def do_GET(self):
        if not self.basic_ok():
            return self.send(401, {"ietf-restconf:errors": {"error": [
                {"error-type": "protocol", "error-tag": "access-denied"}]}}, "application/yang-data+json")
        if self.path == "/restconf/data/ietf-interfaces:interfaces/interface=GigabitEthernet1":
            return self.send(200, IOSXE_GI1, "application/yang-data+json")
        self.send(404, {"ietf-restconf:errors": {"error": [
            {"error-type": "application", "error-tag": "invalid-value"}]}}, "application/yang-data+json")


if __name__ == "__main__":
    servers = [ThreadingHTTPServer((HOST, NXOS_PORT), NXOS), ThreadingHTTPServer((HOST, IOSXE_PORT), IOSXE)]
    for srv in servers[1:]:
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f"NX-OS  mock on http://{HOST}:{NXOS_PORT}  (/ins, /api/...)")
    print(f"IOS XE mock on http://{HOST}:{IOSXE_PORT} (/restconf/...)")
    servers[0].serve_forever()
