"""Mock IOS XE RESTCONF server for the T16 lab (Python stdlib only).

Behaves like the RFC 8040 RESTCONF interface of a Catalyst 8000V for the
ietf-interfaces model, over HTTPS with a self-signed certificate.

Run:  bash labs/T16/run_lab.sh            (makes a cert, starts this, runs the client)
By hand:
  openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj "/CN=localhost" \
      -keyout /tmp/t16-key.pem -out /tmp/t16-cert.pem
  MOCK_CERT=/tmp/t16-cert.pem MOCK_KEY=/tmp/t16-key.pem python3 labs/T16/mock_restconf.py

Fake credentials for this local mock only (override with MOCK_USER / MOCK_PASS).
"""
import base64
import copy
import json
import os
import ssl
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote

HOST, PORT = "127.0.0.1", int(os.environ.get("MOCK_PORT", "9443"))
USER = os.environ.get("MOCK_USER", "admin")
PASSWORD = os.environ.get("MOCK_PASS", "C1sco12345")
JSON_T, XML_T = "application/yang-data+json", "application/yang-data+xml"
NS = {"ietf-interfaces": "urn:ietf:params:xml:ns:yang:ietf-interfaces",
      "ietf-ip": "urn:ietf:params:xml:ns:yang:ietf-ip",
      "ietf-restconf": "urn:ietf:params:xml:ns:yang:ietf-restconf"}
STATE = ("oper-status", "phys-address", "statistics")      # config false nodes (RFC 8343)
IFACES = "/restconf/data/ietf-interfaces:interfaces"


def phy(n, desc, ip, mac, octets):
    return {"name": f"GigabitEthernet{n}", "description": desc, "type": "iana-if-type:ethernetCsmacd",
            "enabled": True, "ietf-ip:ipv4": {"address": [{"ip": ip, "netmask": "255.255.255.0"}]},
            "oper-status": "up", "phys-address": mac,
            "statistics": {"in-octets": octets, "out-octets": octets // 2}}


running = {i["name"]: i for i in (
    phy(1, "MANAGEMENT - DO NOT TOUCH", "10.10.20.48", "00:50:56:bf:49:a1", 918273),
    phy(2, "WAN to ISP-A", "172.16.1.1", "00:50:56:bf:49:a2", 55120),
    phy(3, "LAN users", "192.168.10.1", "00:50:56:bf:49:a3", 4410))}
startup = copy.deepcopy(running)


def errors(tag, message=None, path=None, etype="application"):
    err = {"error-type": etype, "error-tag": tag}
    if path:
        err["error-path"] = path
    if message:
        err["error-message"] = message
    return {"ietf-restconf:errors": {"error": [err]}}


def to_xml(name, value, parent_mod=None, indent="  ", level=0):
    """Tiny RFC 7950-style XML encoder for the JSON trees used here."""
    pad = indent * level
    mod, _, local = name.rpartition(":")
    xmlns = f' xmlns="{NS[mod]}"' if mod and mod != parent_mod else ""
    mod = mod or parent_mod
    if isinstance(value, list):
        return "".join(to_xml(name, v, parent_mod, indent, level) for v in value)
    if isinstance(value, dict):
        inner = "".join(to_xml(k, v, mod, indent, level + 1) for k, v in value.items())
        return f"{pad}<{local}{xmlns}>\n{inner}{pad}</{local}>\n"
    if isinstance(value, bool):
        value = str(value).lower()
    if isinstance(value, str) and value.startswith("iana-if-type:"):
        return (f'{pad}<{local}{xmlns} xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">'
                f'ianaift:{value.split(":", 1)[1]}</{local}>\n')
    return f"{pad}<{local}{xmlns}>{value}</{local}>\n"


def prune(node, content, fields):
    node = copy.deepcopy(node)
    if content == "config":
        for k in STATE:
            node.pop(k, None)
    elif content == "nonconfig":
        node = {k: v for k, v in node.items() if k in STATE or k == "name"}   # keys always kept
    if fields:
        node = {k: v for k, v in node.items() if k in fields or k == "name"}
    return node


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def version_string(self):
        return "openresty"

    def log_message(self, *args):
        pass

    # ---------- helpers ----------
    def out_type(self):
        accept = self.headers.get("Accept", "*/*")
        if JSON_T in accept:
            return JSON_T
        if XML_T in accept or "*/*" in accept:
            return XML_T                                  # IOS XE answers XML when you don't ask
        return None

    def send(self, code, body=None, headers=None, ctype=None):
        data = b""
        if body is not None:
            ctype = ctype or self.out_type() or JSON_T
            if isinstance(body, str):
                data = body.encode()
            elif ctype == XML_T:
                (top, value), = body.items()
                data = to_xml(top, value).encode()
            else:
                data = (json.dumps(body, indent=2) + "\n").encode()
        self.send_response(code)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        if data:
            self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def authorised(self):
        want = "Basic " + base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()
        if self.headers.get("Authorization") == want:
            return True
        self.send(401, errors("access-denied", etype="protocol"),
                  {"WWW-Authenticate": 'Basic realm="restconf"'})
        return False

    def body(self):
        """Return the parsed JSON body, or None after sending 415/400."""
        ctype = self.headers.get("Content-Type", "")
        if not ctype.startswith(JSON_T):
            self.send(415, errors("invalid-value", f"unsupported Content-Type '{ctype}'", etype="protocol"))
            return None
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            self.send(400, errors("malformed-message", "invalid JSON", etype="rpc"))
            return None

    def entry(self, doc, name):
        """Validate {"ietf-interfaces:interface": {...}} (object or 1-item list)."""
        item = doc.get("ietf-interfaces:interface")
        if isinstance(item, list) and len(item) == 1:
            item = item[0]
        path = "/ietf-interfaces:interfaces/interface"
        if not isinstance(item, dict):
            self.send(400, errors("malformed-message", "expected one ietf-interfaces:interface", path))
            return None
        if name and item.get("name", name) != name:
            self.send(400, errors("invalid-value", "key leaf in body does not match the URI", path + "/name"))
            return None
        if "enabled" in item and not isinstance(item["enabled"], bool):
            self.send(400, errors("invalid-value", f"invalid value \"{item['enabled']}\" for boolean leaf",
                                  f"{path}[name='{item.get('name', name)}']/enabled"))
            return None
        return item

    # ---------- routing ----------
    def handle_any(self, method):
        raw_path, _, query = self.path.partition("?")
        params = {k: v[0] for k, v in parse_qs(query).items()}

        if raw_path == "/.well-known/host-meta" and method == "GET":
            return self.send(200, "<XRD xmlns='http://docs.oasis-open.org/ns/xri/xrd-1.0'>\n"
                                  "  <Link rel='restconf' href='/restconf'/>\n</XRD>\n",
                             ctype="application/xrd+xml")
        if not self.authorised():
            return None
        if self.out_type() is None:
            return self.send(406, errors("invalid-value", "Accept must be a yang-data media type",
                                         etype="protocol"), ctype=JSON_T)
        bad = set(params) - {"content", "depth", "fields", "with-defaults"}
        if bad or params.get("content", "all") not in ("config", "nonconfig", "all"):
            return self.send(400, errors("invalid-value", f"invalid query parameter {sorted(bad) or params}",
                                         etype="protocol"))

        if raw_path == "/restconf" and method == "GET":
            return self.send(200, {"ietf-restconf:restconf": {
                "data": {}, "operations": {}, "yang-library-version": "2016-06-21"}})
        if raw_path == "/restconf/operations/cisco-ia:save-config" and method == "POST":
            startup.clear()
            startup.update(copy.deepcopy(running))
            return self.send(200, {"cisco-ia:output": {"result": "Save running config is successful"}})

        if raw_path == IFACES:
            return self.collection(method, params)
        if raw_path.startswith(IFACES + "/interface="):
            rest = raw_path[len(IFACES + "/interface="):]
            key, _, leaf = rest.partition("/")          # an unencoded "/" in the key splits here
            return self.item(method, unquote(key), leaf, params)
        return self.send(404, errors("invalid-value", "uri keypath not found", etype="application"))

    def collection(self, method, params):
        if method == "GET":
            fields = None
            if "fields" in params:                       # fields=interface(name;enabled)
                fields = params["fields"].removeprefix("interface(").rstrip(")").split(";")
            items = [prune(i, params.get("content", "all"), fields) for i in running.values()]
            return self.send(200, {"ietf-interfaces:interfaces": {"interface": items}})
        if method == "POST":
            doc = self.body()
            item = doc is not None and self.entry(doc, None)
            if not item:
                return None
            if item["name"] in running:
                return self.send(409, errors("data-exists", "object already exists: "
                                             f"/ietf-interfaces:interfaces/interface[name='{item['name']}']",
                                             etype="application"))
            if "type" not in item:
                return self.send(400, errors("invalid-value", "missing mandatory leaf 'type'"))
            running[item["name"]] = item
            loc = f"https://{HOST}:{PORT}{IFACES}/interface={item['name']}"
            return self.send(201, headers={"Location": loc})
        return self.send(405, errors("operation-not-supported", etype="protocol"),
                         {"Allow": "GET, HEAD, POST, PUT, PATCH, OPTIONS"})

    def item(self, method, name, leaf, params):
        exists = name in running
        path = f"/ietf-interfaces:interfaces/interface[name='{name}']"
        if leaf and leaf.split("/")[0] not in ("description", "enabled", "type", "name"):
            return self.send(400, errors("invalid-value", f"unknown node '{leaf}' (unencoded '/' in a key?)"))
        if method == "GET":
            if not exists or (leaf and leaf not in running[name]):
                return self.send(404, errors("invalid-value", "uri keypath not found"))
            if leaf:
                return self.send(200, {f"ietf-interfaces:{leaf}": running[name][leaf]})
            fields = params["fields"].split(";") if "fields" in params else None
            return self.send(200, {"ietf-interfaces:interface":
                                   prune(running[name], params.get("content", "all"), fields)})
        if method in ("PUT", "PATCH"):
            doc = self.body()
            item = doc is not None and self.entry(doc, name)
            if not item:
                return None
            item["name"] = name
            if method == "PATCH":
                if not exists:
                    return self.send(404, errors("invalid-value", "uri keypath not found", path))
                running[name].update(item)              # merge: only the leaves sent change
                return self.send(204)
            if "type" not in item:
                return self.send(400, errors("invalid-value", "missing mandatory leaf 'type'", path))
            running[name] = item                         # replace: leaves not sent are removed
            return self.send(204 if exists else 201)
        if method == "DELETE":
            if not exists:
                return self.send(404, errors("invalid-value", "uri keypath not found", path))
            del running[name]
            return self.send(204)
        return self.send(405, errors("operation-not-supported", etype="protocol"))

    def do_GET(self): self.handle_any("GET")
    def do_POST(self): self.handle_any("POST")
    def do_PUT(self): self.handle_any("PUT")
    def do_PATCH(self): self.handle_any("PATCH")
    def do_DELETE(self): self.handle_any("DELETE")


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(os.environ["MOCK_CERT"], os.environ["MOCK_KEY"])
    server.socket = ctx.wrap_socket(server.socket, server_side=True, do_handshake_on_connect=False)
    print(f"mock RESTCONF on https://{HOST}:{PORT}/restconf  (user {USER})")
    server.serve_forever()
