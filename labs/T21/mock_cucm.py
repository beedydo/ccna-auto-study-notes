"""Mock CUCM (Unified CM) for the T21 lab: AXL (SOAP), UDS (REST/XML) and RisPort70 (SOAP).

Python stdlib only. Serves HTTPS with a self-signed cert, like a real CUCM on :8443.
Run:  bash labs/T21/run_lab.sh            (creates the cert, starts this, runs the client)
Or:   python3 labs/T21/mock_cucm.py CERT.pem KEY.pem

Shapes follow the AXL / UDS / RisPort70 developer guides on developer.cisco.com, trimmed
to the tags the lab uses. Users and passwords below are fake, for this local mock only.
"""
import base64
import os
import ssl
import sys
import uuid
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

HOST, PORT = "127.0.0.1", int(os.environ.get("CUCM_PORT", "8443"))
AXL_VERSION = "14.0"
AXL_NS = f"http://www.cisco.com/AXL/API/{AXL_VERSION}"
SOAP_ENV = "http://schemas.xmlsoap.org/soap/envelope/"
RIS_NS = "http://schemas.cisco.com/ast/soap"
CUCM_BUILD = "14.0.1.13900(155)"

# Application users (AXL) vs end users (UDS). Roles decide what each one may call.
APP_USERS = {"axladmin": ("C1sco12345", {"Standard AXL API Access"}),
             "reportuser": ("Report123", {"Standard CCM Read Only"})}        # no AXL role -> 403
END_USERS = {"jkam": {"password": "Us3rPass", "first": "Jun Hao", "last": "Kam", "dn": "2001",
                      "email": "jkam@lab.local", "pkid": "a3c1e2f0-1111-4c4c-9a9a-000000000001"},
             "wtan": {"password": "Us3rPass", "first": "Wendy", "last": "Tan", "dn": "2002",
                      "email": "wtan@lab.local", "pkid": "a3c1e2f0-2222-4c4c-9a9a-000000000002"}}

lines = {"2002": {"uuid": "{6F1C0A55-0000-4E3B-8C8D-000000002002}", "description": "Wendy Tan"}}
phones = {"SEP0CD0F894A1B2": {"uuid": "{B1F3E1A2-7C55-4A10-9C0D-0CD0F894A1B2}", "product": "Cisco 8845",
                              "class": "Phone", "protocol": "SIP", "devicePoolName": "Default",
                              "description": "Wendy Tan desk", "ownerUserName": "wtan", "line": "2002"}}
registered = {"SEP0CD0F894A1B2": "10.10.20.102"}          # live state, only RisPort70 sees this
associated = {"jkam": [], "wtan": ["SEP0CD0F894A1B2"]}


def local(tag):
    return tag.split("}", 1)[-1]


def child_text(elem, name, default=""):
    for c in elem.iter():
        if local(c.tag) == name and c.text:
            return c.text.strip()
    return default


def soap(body_xml):
    return (f'<?xml version="1.0" encoding="UTF-8"?><soapenv:Envelope xmlns:soapenv="{SOAP_ENV}">'
            f"<soapenv:Body>{body_xml}</soapenv:Body></soapenv:Envelope>")


def axl_ok(op, inner):
    return soap(f'<ns:{op}Response xmlns:ns="{AXL_NS}">{inner}</ns:{op}Response>')


def axl_fault(op, code, message):
    return soap(f"<soapenv:Fault><faultcode>soapenv:Server</faultcode><faultstring>{message}</faultstring>"
                f"<detail><axlError><axlcode>{code}</axlcode><axlmessage>{message}</axlmessage>"
                f"<request>{op}</request></axlError></detail></soapenv:Fault>")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def send(self, code, body="", ctype="text/xml;charset=UTF-8", headers=None):
        data = body.encode()
        self.send_response(code)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        if data:
            self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def basic_user(self):
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Basic "):
            return None, None
        user, _, pw = base64.b64decode(auth[6:]).decode().partition(":")
        return user, pw

    def uri(self, path):
        return f"https://{HOST}:{PORT}/cucm-uds{path}"

    # ------------------------------------------------------------------ routing
    def do_GET(self):
        url = urlparse(self.path)
        if url.path.startswith("/cucm-uds/"):
            return self.uds_get(url.path[len("/cucm-uds"):], parse_qs(url.query))
        if url.path == "/axl/":
            return self.send(405, "", headers={"Allow": "POST"})   # AXL is POST-only
        self.send(404)

    def do_POST(self):
        url = urlparse(self.path)
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if url.path == "/axl":                                     # trailing slash is required
            return self.send(404)
        if url.path == "/axl/":
            return self.axl(body)
        if url.path == "/realtimeservice2/services/RISService70":
            return self.risport(body)
        if url.path.startswith("/mock/boot/"):                     # NOT a CUCM API: simulates a phone powering on
            name = url.path.rsplit("/", 1)[-1]
            registered[name] = "10.10.20.101"
            return self.send(204)
        if url.path.startswith("/cucm-uds/"):
            return self.send(405, "", headers={"Allow": "GET"})    # directory/users are read-only in UDS
        self.send(404)

    # ------------------------------------------------------------------ AXL (SOAP)
    def axl(self, body):
        user, pw = self.basic_user()
        if user not in APP_USERS or APP_USERS[user][0] != pw:
            return self.send(401, "", headers={"WWW-Authenticate": 'Basic realm="Cisco AXL"'})
        if "Standard AXL API Access" not in APP_USERS[user][1]:
            return self.send(403, "<html><body>Forbidden: user lacks the AXL API role</body></html>", "text/html")
        try:
            root = ET.fromstring(body)
            req = next(c for c in root.iter() if local(c.tag) == "Body")[0]
        except Exception:
            return self.send(500, axl_fault("unknown", 5003, "Malformed SOAP request"))
        op = local(req.tag)
        action = self.headers.get("SOAPAction", "").strip('"')
        ns_version = req.tag[1:].split("}")[0].rsplit("/", 1)[-1]
        if action != f"CUCM:DB ver={ns_version} {op}":
            return self.send(500, axl_fault(op, 5003, f"SOAPAction '{action}' does not match request {op} ver={ns_version}"))
        handler = getattr(self, f"axl_{op}", None)
        if handler is None:
            return self.send(500, axl_fault(op, 5003, f"Operation {op} not supported by this mock"))
        code, xml = handler(req)
        self.send(code, xml)

    def axl_getCCMVersion(self, req):
        return 200, axl_ok("getCCMVersion", f"<return><componentVersion><version>{CUCM_BUILD}</version>"
                                            "</componentVersion></return>")

    def axl_addLine(self, req):
        pattern = child_text(req, "pattern")
        if pattern in lines:
            return 500, axl_fault("addLine", -239, "Could not insert new row - duplicate value in a UNIQUE INDEX column")
        lines[pattern] = {"uuid": "{" + str(uuid.uuid5(uuid.NAMESPACE_DNS, pattern)).upper() + "}", "description": child_text(req, "description")}
        return 200, axl_ok("addLine", f"<return>{lines[pattern]['uuid']}</return>")

    def axl_addPhone(self, req):
        name = child_text(req, "name")
        missing = [t for t in ("name", "product", "class", "protocol", "devicePoolName") if not child_text(req, t)]
        if missing:
            return 500, axl_fault("addPhone", 5003, f"Mandatory tag(s) missing: {', '.join(missing)}")
        if name in phones:
            return 500, axl_fault("addPhone", -239, "Could not insert new row - duplicate value in a UNIQUE INDEX column")
        phones[name] = {"uuid": "{" + str(uuid.uuid5(uuid.NAMESPACE_DNS, name)).upper() + "}", "product": child_text(req, "product"),
                        "class": child_text(req, "class"), "protocol": child_text(req, "protocol"),
                        "devicePoolName": child_text(req, "devicePoolName"),
                        "description": child_text(req, "description"),
                        "ownerUserName": child_text(req, "ownerUserName"), "line": child_text(req, "pattern")}
        return 200, axl_ok("addPhone", f"<return>{phones[name]['uuid']}</return>")

    def axl_updateUser(self, req):
        user = child_text(req, "userid")
        if user not in END_USERS:
            return 500, axl_fault("updateUser", 5007, f"Item not valid: The specified User {user} was not found")
        associated[user] = [c.text for c in req.iter() if local(c.tag) == "device"]
        return 200, axl_ok("updateUser", "<return>{" + END_USERS[user]["pkid"].upper() + "}</return>")

    def axl_getPhone(self, req):
        name = child_text(req, "name")
        p = phones.get(name)
        if p is None:
            return 500, axl_fault("getPhone", 5007, f"Item not valid: The specified {name} was not found")
        return 200, axl_ok("getPhone", (
            f'<return><phone uuid="{p["uuid"]}"><name>{name}</name><description>{p["description"]}</description>'
            f'<product>{p["product"]}</product><class>{p["class"]}</class><protocol>{p["protocol"]}</protocol>'
            f'<devicePoolName>{p["devicePoolName"]}</devicePoolName><ownerUserName>{p["ownerUserName"]}</ownerUserName>'
            f'<lines><line><index>1</index><dirn><pattern>{p["line"]}</pattern></dirn></line></lines>'
            "</phone></return>"))

    def axl_listPhone(self, req):
        like = child_text(req, "name", "%").replace("%", "")
        rows = "".join(f'<phone uuid="{p["uuid"]}"><name>{n}</name><description>{p["description"]}</description>'
                       f'<product>{p["product"]}</product></phone>'
                       for n, p in sorted(phones.items()) if n.startswith(like))
        return 200, axl_ok("listPhone", f"<return>{rows}</return>")

    def axl_executeSQLQuery(self, req):
        sql = child_text(req, "sql").lower()
        if not sql.startswith("select"):
            return 500, axl_fault("executeSQLQuery", -201, "A syntax error has occurred.")
        rows = "".join(f"<row><name>{n}</name><description>{p['description']}</description></row>"
                       for n, p in sorted(phones.items()))
        return 200, axl_ok("executeSQLQuery", f"<return>{rows}</return>")

    # ------------------------------------------------------------------ UDS (REST, XML only)
    def uds_get(self, path, query):
        if path == "/version":                                      # no auth needed
            return self.send(200, f'<versionInformation version="14.0.1" uri="{self.uri("/version")}">'
                                  "<version>14.0.1</version><capabilities>"
                                  "<usersResourceAuthEnabled>false</usersResourceAuthEnabled>"
                                  "</capabilities></versionInformation>", "application/xml")
        if path == "/servers":                                      # no auth needed
            return self.send(200, f'<servers version="14.0.1" uri="{self.uri("/servers")}">'
                                  "<server>cucm-pub.lab.local</server><server>cucm-sub1.lab.local</server></servers>",
                             "application/xml")
        if path == "/users":                                        # directory search
            last = query.get("last", [""])[0].lower()
            hits = [(u, d) for u, d in END_USERS.items() if d["last"].lower().startswith(last)]
            users = "".join(f'<user uri="{self.uri("/user/" + u)}"><id>{d["pkid"]}</id><userName>{u}</userName>'
                            f'<firstName>{d["first"]}</firstName><lastName>{d["last"]}</lastName>'
                            f'<phoneNumber>{d["dn"]}</phoneNumber><email>{d["email"]}</email></user>'
                            for u, d in hits)
            return self.send(200, f'<users version="14.0.1" uri="{self.uri("/users")}" start="0" '
                                  f'requestedCount="64" returnedCount="{len(hits)}" totalCount="{len(hits)}">'
                                  f"{users}</users>", "application/xml")
        if path.startswith("/user/"):                               # personal data: end-user Basic auth
            parts = path.split("/")                                 # ['', 'user', '{userId}', ...]
            owner = parts[2]
            user, pw = self.basic_user()
            if user not in END_USERS or END_USERS[user]["password"] != pw or user != owner:
                return self.send(401, "", headers={"WWW-Authenticate": 'Basic realm="Cisco UDS"'})
            if parts[3:] == ["devices"]:
                devs = ""
                for n in associated.get(owner, []):
                    p = phones[n]
                    pkid = p["uuid"].strip("{}").lower()
                    devs += (f'<device uri="{self.uri("/user/" + owner + "/device/" + pkid)}"><id>{pkid}</id>'
                             f'<name>{n}</name><description>{p["description"]}</description>'
                             f'<model>{p["product"]}</model><protocol>{p["protocol"]}</protocol></device>')
                return self.send(200, f'<devices version="14.0.1" uri="{self.uri("/user/" + owner + "/devices")}">'
                                      f"{devs}</devices>", "application/xml")
        self.send(404, "", "application/xml")

    # ------------------------------------------------------------------ RisPort70 (SOAP, live state)
    def risport(self, body):
        user, pw = self.basic_user()
        if user not in APP_USERS or APP_USERS[user][0] != pw:
            return self.send(401, "", headers={"WWW-Authenticate": 'Basic realm="Cisco RIS"'})
        root = ET.fromstring(body)
        item = child_text(root, "Item", "*").replace("*", "")
        found = [n for n in sorted(phones) if n.startswith(item) and n in registered]
        devs = "".join(f"<ns1:item><ns1:Name>{n}</ns1:Name><ns1:DirNumber>{phones[n]['line']}-Registered</ns1:DirNumber>"
                       f"<ns1:Status>Registered</ns1:Status><ns1:IPAddress><ns1:item><ns1:IP>{registered[n]}</ns1:IP>"
                       f"</ns1:item></ns1:IPAddress></ns1:item>" for n in found)
        self.send(200, soap(f'<ns1:selectCmDeviceResponse xmlns:ns1="{RIS_NS}"><ns1:selectCmDeviceReturn>'
                            f"<ns1:SelectCmDeviceResult><ns1:TotalDevicesFound>{len(found)}</ns1:TotalDevicesFound>"
                            f"<ns1:CmNodes><ns1:item><ns1:ReturnCode>Ok</ns1:ReturnCode><ns1:Name>cucm-sub1.lab.local</ns1:Name>"
                            f"<ns1:CmDevices>{devs}</ns1:CmDevices></ns1:item></ns1:CmNodes>"
                            "</ns1:SelectCmDeviceResult></ns1:selectCmDeviceReturn></ns1:selectCmDeviceResponse>"))


if __name__ == "__main__":
    cert, key = sys.argv[1], sys.argv[2]
    server = HTTPServer((HOST, PORT), Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(cert, key)
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    print(f"mock CUCM on https://{HOST}:{PORT}  (AXL /axl/, UDS /cucm-uds/, RisPort70)")
    server.serve_forever()
