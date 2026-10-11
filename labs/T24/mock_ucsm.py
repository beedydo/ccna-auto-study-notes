"""Mock UCS Manager XML API for the T24 lab (Python stdlib only).

Run:  python3 labs/T24/mock_ucsm.py        -> POST XML to http://127.0.0.1:8124/nuova

Method names, attributes and error codes follow the Cisco UCS Manager XML API
Programmer's Guide. Data, serials and the password are fake.

What it imitates:
  - one endpoint:  every call is an HTTP POST of an XML document to /nuova
  - auth:          aaaLogin (inName/inPassword) -> outCookie, outRefreshPeriod="600"
                   wrong password -> errorCode="551"; bad/missing cookie -> errorCode="552"
                   aaaRefresh -> new cookie; aaaLogout -> cookie invalidated
  - queries:       configResolveClass (classId + optional <inFilter><eq .../>),
                   configResolveDn, configResolveDns, inHierarchical="true" returns children
                   unknown DN -> success with an EMPTY <outConfig/> (not an error)
  - config:        configConfMos with status="created" / "deleted" for lsServer
                   (service profiles) under org-root; duplicate create -> errorCode="103"
"""
import os
import secrets
import time
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST, PORT = "127.0.0.1", int(os.environ.get("MOCK_UCSM_PORT", "8124"))
USERS = {os.environ.get("MOCK_UCSM_USER", "ucspe"): os.environ.get("MOCK_UCSM_PASS", "ucspe")}
VERSION = "4.2(3d)"
SESSIONS = {}   # cookie -> username


def mo(cls, **attrs):
    return {"class": cls, "attrs": attrs}


# The management information tree (MIT): dn -> managed object. Parent = dn minus its last RN.
MIT = {}
for item in [
    mo("topSystem", dn="sys", name="UCS-SG-DC1", address="10.10.20.40", mode="cluster",
       currentTime="2026-10-10T12:00:00.000"),
    mo("networkElement", dn="sys/switch-A", id="A", model="UCS-FI-6454", serial="FDO23410ABC",
       oobIfIp="10.10.20.41", operability="operable"),
    mo("networkElement", dn="sys/switch-B", id="B", model="UCS-FI-6454", serial="FDO23410ABD",
       oobIfIp="10.10.20.42", operability="operable"),
    mo("firmwareRunning", dn="sys/mgmt/fw-system", deployment="system", type="system", version=VERSION),
    mo("equipmentChassis", dn="sys/chassis-1", id="1", model="UCSB-5108-AC2", serial="FOX2341P1AB",
       operState="operable"),
    mo("computeBlade", dn="sys/chassis-1/blade-1", chassisId="1", slotId="1", model="UCSB-B200-M5",
       serial="FLM2341001A", numOfCpus="2", numOfCores="40", totalMemory="393216",
       operPower="on", operState="ok", association="associated", availability="unavailable",
       assignedToDn="org-root/ls-ESX-01"),
    mo("computeBlade", dn="sys/chassis-1/blade-2", chassisId="1", slotId="2", model="UCSB-B200-M5",
       serial="FLM2341001B", numOfCpus="2", numOfCores="40", totalMemory="393216",
       operPower="on", operState="ok", association="associated", availability="unavailable",
       assignedToDn="org-root/ls-ESX-02"),
    mo("computeBlade", dn="sys/chassis-1/blade-3", chassisId="1", slotId="3", model="UCSB-B200-M6",
       serial="FLM2341001C", numOfCpus="2", numOfCores="64", totalMemory="524288",
       operPower="off", operState="unassociated", association="none", availability="available",
       assignedToDn=""),
    mo("adaptorUnit", dn="sys/chassis-1/blade-1/adaptor-1", id="1", model="UCSB-MLOM-40G-04",
       serial="FCH2341AB01", operState="operable"),
    mo("computeRackUnit", dn="sys/rack-unit-1", id="1", model="UCSC-C220-M5SX", serial="WZP2341001R",
       numOfCpus="2", numOfCores="32", totalMemory="262144", operPower="on", operState="ok",
       association="associated", availability="unavailable", assignedToDn="org-root/ls-SQL-01"),
    mo("orgOrg", dn="org-root", name="root", descr=""),
    mo("lsServer", dn="org-root/ls-ESX-template", name="ESX-template", type="updating-template",
       uuid="derived", identPoolName="UUID-POOL", bootPolicyName="BOOT-SAN", hostFwPolicyName="FW-4.2",
       srcTemplName="", assocState="unassociated", pnDn="", operState="unassociated"),
    mo("lsServer", dn="org-root/ls-ESX-01", name="ESX-01", type="instance",
       uuid="1b4e28ba-2fa1-11d2-0001-0025b5000001", identPoolName="UUID-POOL", bootPolicyName="BOOT-SAN",
       hostFwPolicyName="FW-4.2", srcTemplName="ESX-template", assocState="associated",
       pnDn="sys/chassis-1/blade-1", operState="ok"),
    mo("lsServer", dn="org-root/ls-ESX-02", name="ESX-02", type="instance",
       uuid="1b4e28ba-2fa1-11d2-0001-0025b5000002", identPoolName="UUID-POOL", bootPolicyName="BOOT-SAN",
       hostFwPolicyName="FW-4.2", srcTemplName="ESX-template", assocState="associated",
       pnDn="sys/chassis-1/blade-2", operState="ok"),
    mo("lsServer", dn="org-root/ls-SQL-01", name="SQL-01", type="instance",
       uuid="1b4e28ba-2fa1-11d2-0001-0025b5000003", identPoolName="UUID-POOL", bootPolicyName="BOOT-LOCAL",
       hostFwPolicyName="FW-4.2", srcTemplName="", assocState="associated",
       pnDn="sys/rack-unit-1", operState="ok"),
    mo("vnicEther", dn="org-root/ls-ESX-01/ether-eth0", name="eth0", addr="00:25:B5:A0:00:01",
       switchId="A", identPoolName="MAC-POOL-A"),
    mo("vnicFc", dn="org-root/ls-ESX-01/fc-vhba0", name="vhba0", addr="20:00:00:25:B5:A0:00:01",
       switchId="A", identPoolName="WWPN-POOL-A"),
]:
    MIT[item["attrs"]["dn"]] = item

NEXT_UUID = [4]


def children(dn):
    return [m for d, m in MIT.items() if d.rsplit("/", 1)[0] == dn and d != dn]


def to_elem(m, hierarchical):
    el = ET.Element(m["class"], m["attrs"])
    if hierarchical:
        for child in children(m["attrs"]["dn"]):
            el.append(to_elem(child, True))
    return el


def matches(m, flt):
    """Support the simple property filters <eq>, <ne>, <wcard> inside <inFilter>."""
    if flt is None or len(flt) == 0:
        return True
    cond = flt[0]
    value = m["attrs"].get(cond.get("property"), "")
    if cond.tag == "eq":
        return value == cond.get("value")
    if cond.tag == "ne":
        return value != cond.get("value")
    if cond.tag == "wcard":
        import re
        return re.search(cond.get("value"), value) is not None
    return True


def error(method, cookie, code, descr):
    return ET.Element(method, {"cookie": cookie, "response": "yes", "errorCode": str(code),
                               "invocationResult": "unidentified-fail", "errorDescr": descr})


def handle(req):
    method = req.tag
    cookie = req.get("cookie", "")

    if method == "aaaLogin":
        user, pwd = req.get("inName"), req.get("inPassword")
        if USERS.get(user) != pwd:
            return error(method, "", 551, "Authentication failed")
        new = f"{int(time.time())}/{secrets.token_hex(4)}-{secrets.token_hex(2)}-{secrets.token_hex(2)}" \
              f"-{secrets.token_hex(2)}-{secrets.token_hex(6)}"
        SESSIONS[new] = user
        return ET.Element(method, {"cookie": "", "response": "yes", "outCookie": new,
                                   "outRefreshPeriod": "600", "outPriv": "admin,read-only",
                                   "outDomains": "UCS-SG-DC1", "outChannel": "noencssl",
                                   "outEvtChannel": "noencssl", "outSessionId": "web_49111_A",
                                   "outVersion": VERSION, "outName": user})

    if method == "aaaRefresh":
        old = req.get("inCookie", "")
        if old not in SESSIONS:
            return error(method, old, 552, "Authorization required")
        user = SESSIONS.pop(old)
        new = f"{int(time.time())}/{secrets.token_hex(4)}-refreshed"
        SESSIONS[new] = user
        return ET.Element(method, {"cookie": "", "response": "yes", "outCookie": new,
                                   "outRefreshPeriod": "600", "outPriv": "admin,read-only"})

    if method == "aaaLogout":
        SESSIONS.pop(req.get("inCookie", ""), None)
        return ET.Element(method, {"cookie": "", "response": "yes", "outStatus": "success"})

    if cookie not in SESSIONS:
        return error(method, cookie, 552, "Authorization required")

    hier = req.get("inHierarchical", "false") in ("true", "yes")
    resp = ET.Element(method, {"cookie": cookie, "response": "yes"})

    if method == "configResolveClass":
        cls = req.get("classId")
        out = ET.SubElement(resp, "outConfigs")
        for m in MIT.values():
            if m["class"] == cls and matches(m, req.find("inFilter")):
                out.append(to_elem(m, hier))
        return resp

    if method == "configResolveDn":
        resp.set("dn", req.get("dn"))
        out = ET.SubElement(resp, "outConfig")
        if req.get("dn") in MIT:                       # unknown DN -> empty outConfig, still success
            out.append(to_elem(MIT[req.get("dn")], hier))
        return resp

    if method == "configResolveDns":
        out = ET.SubElement(resp, "outConfigs")
        unresolved = ET.SubElement(resp, "outUnresolved")
        for dn_el in req.iter("dn"):
            dn = dn_el.get("value")
            if dn in MIT:
                out.append(to_elem(MIT[dn], hier))
            else:
                ET.SubElement(unresolved, "dn", {"value": dn})
        return resp

    if method == "configConfMos":
        out = ET.SubElement(resp, "outConfigs")
        for pair in req.iter("pair"):
            for el in pair:
                dn, status = el.get("dn"), el.get("status", "")
                if el.tag != "lsServer" or not dn.startswith("org-root/ls-"):
                    return error(method, cookie, 101, f"this mock only configures lsServer, got {el.tag}")
                if "deleted" in status:
                    MIT.pop(dn, None)
                    for d in [d for d in MIT if d.startswith(dn + "/")]:
                        MIT.pop(d)
                    ET.SubElement(ET.SubElement(out, "pair", {"key": dn}), "lsServer",
                                         {"dn": dn, "status": "deleted"})
                    continue
                if "created" in status and "modified" not in status and dn in MIT:
                    return error(method, cookie, 103, "can't create; object already exists.")
                attrs = {k: v for k, v in el.attrib.items() if k != "status"}
                base = MIT.get(dn, {"attrs": {}})["attrs"]
                tmpl = MIT.get("org-root/ls-" + attrs.get("srcTemplName", ""), {"attrs": {}})["attrs"]
                new = {**{k: tmpl.get(k, "") for k in ("identPoolName", "bootPolicyName", "hostFwPolicyName")},
                       **base, **{k: v for k, v in attrs.items() if v != ""}}
                new.setdefault("type", "instance")
                if not base:
                    new["uuid"] = f"1b4e28ba-2fa1-11d2-0001-0025b50000{NEXT_UUID[0]:02d}"
                    NEXT_UUID[0] += 1
                new.update(assocState="unassociated", pnDn="", operState="unassociated")
                MIT[dn] = {"class": "lsServer", "attrs": new}
                ET.SubElement(ET.SubElement(out, "pair", {"key": dn}), "lsServer", {**new, "status": "created"})
        return resp

    return error(method, cookie, 101, f"mock does not implement {method}")


class Handler(BaseHTTPRequestHandler):
    server_version = "MockUCSM/1.0"

    def do_POST(self):
        if self.path != "/nuova":
            self.send_response(404)
            self.end_headers()
            return
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            reply = handle(ET.fromstring(body))
        except ET.ParseError as exc:
            reply = error("error", "", 101, f"XML parse error: {exc}")
        data = ET.tostring(reply)
        self.send_response(200)                          # the XML API answers 200 even for errors
        self.send_header("Content-Type", "text/xml")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    print(f"Mock UCS Manager XML API on http://{HOST}:{PORT}/nuova")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
