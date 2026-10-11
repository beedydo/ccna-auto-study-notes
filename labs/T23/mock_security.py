"""Mock Cisco security platform APIs for the T23 lab (Python stdlib only).

One process, one port per platform, so each "product" has its own base URL:

    FMC   http://127.0.0.1:9401   /api/fmc_platform/v1/auth/generatetoken, /api/fmc_config/v1/domain/...
    FDM   http://127.0.0.1:9402   /api/fdm/latest/fdm/token, /api/fdm/latest/object/networks
    ISE   http://127.0.0.1:9060   /ers/config/...            (9060 = the real ERS port)
    XDR   http://127.0.0.1:9404   /iroh/oauth2/token, /iroh/iroh-inspect/..., /iroh/iroh-enrich/..., /iroh/iroh-response/...
    SE    http://127.0.0.1:9405   /v1/computers, /v1/events, /v1/computers/{guid}/isolation
    SMA   http://127.0.0.1:9406   /api/v2/samples, /api/v2/samples/{id}/state, /api/v2/samples/{id}/threat
    UMB   http://127.0.0.1:9407   /auth/v2/token, /policies/v2/destinationlists/...   (Secure Connect / Umbrella)

Paths, headers and response shapes follow the public Cisco docs (see the T23 note's Sources).
All credentials are fake and only valid against this mock.

Run:  python3 labs/T23/mock_security.py
"""
import base64
import json
import re
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

HOST = "127.0.0.1"
PORTS = {"fmc": 9401, "fdm": 9402, "ise": 9060, "xdr": 9404, "se": 9405, "sma": 9406, "umb": 9407}

CREDS = {                                   # fake, mock-only
    "fmc": ("apiuser", "T23-fmc-pass"),
    "fdm": ("admin", "T23-fdm-pass"),
    "ise": ("ersadmin", "T23-ise-pass"),
    "xdr": ("client-t23-xdr", "T23-xdr-secret"),
    "se": ("t23-se-client-id", "T23-se-api-key"),
    "umb": ("t23-umbrella-key", "T23-umbrella-secret"),
}
SMA_API_KEY = "t23-sma-api-key"
DOMAIN_UUID = "e276abec-e0f2-11e3-8169-6d9ed49b625f"     # the Global domain UUID shown in Cisco's FMC docs
ACP_ID = "005056BB-0B24-0ed3-0000-268435460"
GUID = "6b8e0c2a-3f6d-4c8e-9a1b-23e1f0c0ffee"
MAC = "00:50:56:A1:23:23"
SHA256 = "a9f1b6e2c47d0d3e5b8c1f2a6e4d7b9c0e3f5a1b2c4d6e8f0a1b3c5d7e9f1a2b"
C2_IP, C2_DOMAIN = "203.0.113.66", "update-checker.example"

state = {
    "fmc_tokens": {},                       # access -> refresh count
    "fdm_tokens": set(), "xdr_tokens": set(), "umb_tokens": set(),
    "isolation": "not_isolated",
    "ise_anc": {},
    "samples": {},
    "fmc_objects": [
        {"id": "00505683-1A2B-0ed3-0000-000000000101", "name": "any-ipv4", "type": "Network"},
        {"id": "00505683-1A2B-0ed3-0000-000000000102", "name": "IPv4-Private-10.0.0.0-8", "type": "Network"},
        {"id": "00505683-1A2B-0ed3-0000-000000000103", "name": "IPv4-Private-172.16.0.0-12", "type": "Network"},
        {"id": "00505683-1A2B-0ed3-0000-000000000104", "name": "IPv4-Private-192.168.0.0-16", "type": "Network"},
    ],
    "fmc_rules": [],
    "umb_list": [],
}


def basic(headers):
    auth = headers.get("Authorization", "")
    if not auth.startswith("Basic "):
        return None
    user, _, pwd = base64.b64decode(auth[6:]).decode().partition(":")
    return user, pwd


def bearer(headers):
    auth = headers.get("Authorization", "")
    return auth[7:] if auth.lower().startswith("bearer ") else None


class Base(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    platform = ""

    def log_message(self, *args):
        pass

    def send(self, code, body=None, headers=None):
        data = b"" if body is None else json.dumps(body).encode()
        self.send_response(code)
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        if data:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        n = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(n) if n else b""

    def parts(self):
        url = urlsplit(self.path)
        return url.path, {k: v[-1] for k, v in parse_qs(url.query).items()}

    def do_GET(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")

    def do_PUT(self):
        self.route("PUT")

    def do_DELETE(self):
        self.route("DELETE")


class FMC(Base):
    def route(self, method):
        path, q = self.parts()
        if path == "/api/fmc_platform/v1/auth/generatetoken" and method == "POST":
            if basic(self.headers) != CREDS["fmc"]:
                return self.send(401, {"error": {"category": "FRAMEWORK", "messages": [
                    {"description": "Unauthorized: invalid username or password"}], "severity": "ERROR"}})
            return self.new_token()
        if path == "/api/fmc_platform/v1/auth/refreshtoken" and method == "POST":
            old = self.headers.get("X-auth-access-token")
            if old not in state["fmc_tokens"] or not self.headers.get("X-auth-refresh-token"):
                return self.send(401, None)
            count = state["fmc_tokens"].pop(old) + 1
            if count > 3:                                    # docs: refresh up to three times
                return self.send(401, {"error": {"messages": [{"description": "Refresh limit reached"}]}})
            return self.new_token(count)

        if self.headers.get("X-auth-access-token") not in state["fmc_tokens"]:
            return self.send(401, {"error": {"category": "FRAMEWORK", "messages": [
                {"description": "Access token invalid."}], "severity": "ERROR"}})
        m = re.fullmatch(r"/api/fmc_config/v1/domain/([^/]+)(/.*)", path)
        if not m:
            return self.send(404, {"error": {"messages": [{"description": "Not found"}]}})
        if m.group(1) != DOMAIN_UUID:
            return self.send(404, {"error": {"messages": [{"description": "Invalid domain UUID"}]}})
        sub = m.group(2)
        base = f"/api/fmc_config/v1/domain/{DOMAIN_UUID}"

        if sub == "/object/networks" and method == "GET":
            offset, limit = int(q.get("offset", 0)), int(q.get("limit", 25))
            items = state["fmc_objects"][offset:offset + limit]
            return self.send(200, {
                "links": {"self": f"{base}/object/networks?offset={offset}&limit={limit}"},
                "items": [dict(o, links={"self": f"{base}/object/networks/{o['id']}"}) for o in items],
                "paging": {"offset": offset, "limit": limit, "count": len(state["fmc_objects"]),
                           "pages": -(-len(state["fmc_objects"]) // limit)}})
        if sub == "/object/hosts" and method == "POST":
            obj = json.loads(self.body())
            obj.update(id=str(uuid.uuid4()).upper(), links={"self": f"{base}/object/hosts/<id>"})
            return self.send(201, obj)
        if sub == "/policy/accesspolicies" and method == "GET":
            return self.send(200, {"items": [{"type": "AccessPolicy", "name": "T23-Branch-ACP", "id": ACP_ID}],
                                   "paging": {"offset": 0, "limit": 25, "count": 1, "pages": 1}})
        if sub == f"/policy/accesspolicies/{ACP_ID}/accessrules" and method == "POST":
            rule = json.loads(self.body())
            rule.update(id=str(uuid.uuid4()).upper(), type="AccessRule")
            state["fmc_rules"].append(rule)
            return self.send(201, rule)
        if sub == "/deployment/deployabledevices" and method == "GET":
            return self.send(200, {"items": [{"type": "DeployableDevice", "name": "T23-BR1-FTD",
                                              "version": "1728553267000", "upToDate": False,
                                              "device": {"id": "a1b2c3d4-23c3-11ef-9f3b-005056a12399",
                                                         "type": "Device", "name": "T23-BR1-FTD"}}],
                                   "paging": {"offset": 0, "limit": 25, "count": 1, "pages": 1}})
        if sub == "/deployment/deploymentrequests" and method == "POST":
            return self.send(202, {"type": "DeploymentRequest", "version": json.loads(self.body())["version"],
                                   "metadata": {"task": {"id": "4294969699", "status": "Deploying"}}})
        return self.send(404, {"error": {"messages": [{"description": "Not found"}]}})

    def new_token(self, count=0):
        access, refresh = str(uuid.uuid4()), str(uuid.uuid4())
        state["fmc_tokens"][access] = count
        return self.send(204, None, {
            "X-auth-access-token": access, "X-auth-refresh-token": refresh,
            "DOMAIN_UUID": DOMAIN_UUID, "global": DOMAIN_UUID,
            "DOMAINS": json.dumps([{"name": "Global", "uuid": DOMAIN_UUID}])})


class FDM(Base):
    def route(self, method):
        path, _ = self.parts()
        if path == "/api/fdm/latest/fdm/token" and method == "POST":
            req = json.loads(self.body() or b"{}")
            if req.get("grant_type") != "password" or (req.get("username"), req.get("password")) != CREDS["fdm"]:
                return self.send(400, {"message": "Invalid credentials or grant_type"})
            token = "eyJhbGciOiJIUzI1NiJ9." + uuid.uuid4().hex
            state["fdm_tokens"].add(token)
            return self.send(200, {"access_token": token, "expires_in": 1800, "token_type": "Bearer",
                                   "refresh_token": "eyJhbGciOiJIUzI1NiJ9." + uuid.uuid4().hex,
                                   "refresh_expires_in": 2400})
        if bearer(self.headers) not in state["fdm_tokens"]:
            return self.send(401, {"message": "Authentication required"})
        if path == "/api/fdm/latest/object/networks" and method == "GET":
            return self.send(200, {"items": [
                {"name": "any-ipv4", "subType": "NETWORK", "value": "0.0.0.0/0", "type": "networkobject"},
                {"name": "OutsideIPv4Gateway", "subType": "HOST", "value": "198.51.100.1", "type": "networkobject"}],
                "paging": {"prev": [], "next": [], "limit": 10, "offset": 0, "count": 2}})
        return self.send(404, {"message": "Not found"})


class ISE(Base):
    def route(self, method):
        path, q = self.parts()
        if basic(self.headers) != CREDS["ise"]:
            return self.send(401, None, {"WWW-Authenticate": 'Basic realm="ERS"'})
        if "application/json" not in self.headers.get("Accept", ""):   # ERS answers XML unless asked for JSON
            xml = b'<?xml version="1.0" encoding="UTF-8"?><ns3:searchResult total="2" ' \
                  b'xmlns:ns3="v2.ers.ise.cisco.com"><ns3:resources>...</ns3:resources></ns3:searchResult>'
            self.send_response(200)
            self.send_header("Content-Type", "application/xml")
            self.send_header("Content-Length", str(len(xml)))
            self.end_headers()
            return self.wfile.write(xml)
        base = f"http://{HOST}:{PORTS['ise']}/ers/config"
        if path == "/ers/config/networkdevice" and method == "GET":
            devs = [("4a7e1c20-23c1-11ef-9f3b-005056a12301", "T23-BR1-C9300", "Branch 1 access switch"),
                    ("4a7e1c20-23c1-11ef-9f3b-005056a12302", "T23-BR1-WLC", "Branch 1 wireless controller")]
            return self.send(200, {"SearchResult": {"total": len(devs), "resources": [
                {"id": i, "name": n, "description": d,
                 "link": {"rel": "self", "href": f"{base}/networkdevice/{i}", "type": "application/json"}}
                for i, n, d in devs]}})
        if path == "/ers/config/endpoint" and method == "GET":
            found = q.get("filter", "").upper() == f"MAC.EQ.{MAC}"
            res = [{"id": "8d3b2a10-23c2-11ef-9f3b-005056a12323", "name": MAC,
                    "link": {"rel": "self", "href": f"{base}/endpoint/8d3b2a10-23c2-11ef-9f3b-005056a12323",
                             "type": "application/json"}}] if found else []
            return self.send(200, {"SearchResult": {"total": len(res), "resources": res}})
        if path == "/ers/config/ancendpoint/apply" and method == "PUT":
            data = {d["name"]: d["value"] for d in
                    json.loads(self.body())["OperationAdditionalData"]["additionalData"]}
            state["ise_anc"][data["macAddress"]] = data["policyName"]
            return self.send(204, None)
        if path == "/ers/config/ancendpoint" and method == "GET":
            res = [{"id": "c0a8" + str(i), "name": mac, "description": pol}
                   for i, (mac, pol) in enumerate(state["ise_anc"].items())]
            return self.send(200, {"SearchResult": {"total": len(res), "resources": res}})
        return self.send(404, {"ERSResponse": {"messages": [{"title": "Resource not found"}]}})


class XDR(Base):
    def route(self, method):
        path, _ = self.parts()
        if path == "/iroh/oauth2/token" and method == "POST":
            form = parse_qs(self.body().decode())
            if basic(self.headers) != CREDS["xdr"] or form.get("grant_type") != ["client_credentials"]:
                return self.send(400, {"error": "invalid_client"})
            token = "eyJhbGciOiJSUzI1NiJ9." + uuid.uuid4().hex
            state["xdr_tokens"].add(token)
            return self.send(200, {"access_token": token, "token_type": "bearer", "expires_in": 600,
                                   "scope": "enrich:read inspect:read response"})
        if bearer(self.headers) not in state["xdr_tokens"]:
            return self.send(401, {"error": "invalid_token"})
        if path == "/iroh/iroh-inspect/inspect" and method == "POST":
            text = json.loads(self.body())["content"]
            found = [{"type": "sha256", "value": v} for v in re.findall(r"\b[0-9a-f]{64}\b", text)]
            found += [{"type": "ip", "value": v} for v in re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)]
            found += [{"type": "domain", "value": v} for v in re.findall(r"\b[a-z0-9-]+\.example\b", text)]
            return self.send(200, found)
        if path == "/iroh/iroh-enrich/observe/observables" and method == "POST":
            obs = json.loads(self.body())
            docs = [{"observable": o, "disposition": 2, "disposition_name": "Malicious"} for o in obs]
            return self.send(200, {"data": [
                {"module": "Secure Malware Analytics", "module-type": "ThreatGridModule",
                 "data": {"verdicts": {"count": len(docs), "docs": docs}}},
                {"module": "Secure Endpoint", "module-type": "AMPModule",
                 "data": {"sightings": {"count": 1}}}]})
        if path == "/iroh/iroh-response/respond/observables" and method == "POST":
            return self.send(200, {"data": [
                {"module": "Secure Endpoint", "title": "Add SHA256 to File List", "id": "amp-add-sha256-scd"},
                {"module": "Secure Endpoint", "title": "Isolate Host", "id": "amp-isolate-host"},
                {"module": "Umbrella", "title": "Block this domain", "id": "umbrella-block-domain"}]})
        return self.send(404, {"error": "not found"})


class SE(Base):
    def route(self, method):
        path, q = self.parts()
        if basic(self.headers) != CREDS["se"]:
            return self.send(401, {"version": "v1.2.0", "data": {}, "errors": [
                {"error_code": 401, "description": "Unauthorized", "details": ["Unknown API key or Client ID"]}]})
        env = {"version": "v1.2.0", "metadata": {"links": {"self": f"http://{HOST}:{PORTS['se']}{self.path}"}}}
        if path == "/v1/computers" and method == "GET":
            data = [{"connector_guid": GUID, "hostname": q.get("hostname", "T23-LAPTOP-07"),
                     "operating_system": "Windows 11 Enterprise", "internal_ips": ["10.23.1.57"],
                     "network_addresses": [{"mac": MAC.lower(), "ip": "10.23.1.57"}],
                     "isolation": {"available": True, "status": state["isolation"]}}]
            env["metadata"]["results"] = {"total": 1, "current_item_count": 1, "index": 0, "items_per_page": 500}
            return self.send(200, dict(env, data=data))
        if path == "/v1/events" and method == "GET":
            data = [{"id": 6371299400000000001, "event_type": "Threat Detected", "connector_guid": GUID,
                     "date": "2026-10-10T09:41:07+00:00", "severity": "High",
                     "file": {"file_name": "invoice_2026.pdf.exe", "disposition": "Malicious",
                              "identity": {"sha256": SHA256}}}]
            env["metadata"]["results"] = {"total": 1, "current_item_count": 1, "index": 0, "items_per_page": 500}
            return self.send(200, dict(env, data=data))
        if path == f"/v1/computers/{GUID}/isolation" and method == "PUT":
            state["isolation"] = "pending_start"
            return self.send(200, dict(env, data={"available": True, "status": "pending_start",
                                                  "unlock_code": "7XK2Q9"}))
        return self.send(404, dict(env, errors=[{"error_code": 404, "description": "Not Found"}]))


class SMA(Base):
    def route(self, method):
        path, q = self.parts()
        body = self.body() if method == "POST" else b""
        key = q.get("api_key")
        if not key and body:                               # multipart form field api_key
            m = re.search(rb'name="api_key"\r\n\r\n([^\r]+)', body)
            key = m.group(1).decode() if m else None
        if key != SMA_API_KEY:
            return self.send(401, {"api_version": 2, "error": {"code": 401, "message": "Unauthorized"}})
        if path == "/api/v2/samples" and method == "POST":
            fname = re.search(rb'name="sample"; filename="([^"]+)"', body).group(1).decode()
            sid = uuid.uuid4().hex
            state["samples"][sid] = 0
            return self.send(200, {"api_version": 2, "id": 5512390, "data": {
                "id": sid, "filename": fname, "state": "wait", "status": "pending", "vm": "win10", "private": True}})
        m = re.fullmatch(r"/api/v2/samples/([0-9a-f]{32})/(state|threat)", path)
        if m and m.group(1) in state["samples"]:
            sid, what = m.groups()
            if what == "state":
                state["samples"][sid] += 1                 # finishes on the 2nd poll
                st = "succ" if state["samples"][sid] >= 2 else "run"
                return self.send(200, {"api_version": 2, "data": {"state": st}})
            return self.send(200, {"api_version": 2, "data": {
                "score": 95, "max-severity": 100, "max-confidence": 95, "count": 7,
                "bis": ["malware-known-trojan-av", "network-communications-http-get-url",
                        "registry-autorun-key-modified"]}})
        return self.send(404, {"api_version": 2, "error": {"code": 404, "message": "Not Found"}})


class UMB(Base):
    def route(self, method):
        path, _ = self.parts()
        if path == "/auth/v2/token" and method == "POST":
            form = parse_qs(self.body().decode())
            if basic(self.headers) != CREDS["umb"] or form.get("grant_type") != ["client_credentials"]:
                return self.send(401, {"error": "invalid_client"})
            token = "eyJhbGciOiJSUzI1NiJ9." + uuid.uuid4().hex
            state["umb_tokens"].add(token)
            return self.send(200, {"token_type": "bearer", "access_token": token, "expires_in": 3600})
        if bearer(self.headers) not in state["umb_tokens"]:
            return self.send(401, {"message": "Invalid or expired token"})
        if path == "/policies/v2/destinationlists" and method == "GET":
            return self.send(200, {"status": {"code": 200, "text": "OK"}, "meta": {"page": 1, "limit": 100, "total": 1},
                                   "data": [{"id": 15755711, "name": "T23 Block List", "access": "block",
                                             "meta": {"destinationCount": len(state["umb_list"])}}]})
        if path == "/policies/v2/destinationlists/15755711/destinations" and method == "POST":
            state["umb_list"] += json.loads(self.body())
            return self.send(200, {"status": {"code": 200, "text": "OK"}, "data": {
                "id": 15755711, "name": "T23 Block List", "access": "block",
                "meta": {"destinationCount": len(state["umb_list"])}}})
        return self.send(404, {"message": "Not found"})


HANDLERS = {"fmc": FMC, "fdm": FDM, "ise": ISE, "xdr": XDR, "se": SE, "sma": SMA, "umb": UMB}


def main():
    servers = [ThreadingHTTPServer((HOST, PORTS[name]), cls) for name, cls in HANDLERS.items()]
    for srv in servers[1:]:
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    print("mock security APIs on " + ", ".join(f"{n}:{p}" for n, p in PORTS.items()), flush=True)
    servers[0].serve_forever()


if __name__ == "__main__":
    main()
