"""Offline mock of the SD-WAN Manager (vManage) REST API for T22 (Python stdlib only).

Run:  python3 labs/T22/mock_sdwan.py        -> http://127.0.0.1:18022
Shapes copy real responses from the DevNet always-on sandbox (20.18), trimmed to the fields
the T22 program reads. Behaviour copied from the real thing:
  - failed login        -> HTTP 200 with a JSON error body (success = 200 + EMPTY body + cookie)
  - no/expired session  -> HTTP 200 with an HTML login page (not 401!)
  - POST without token  -> HTTP 403 "SessionTokenFilter: ..."
Credentials are the public sandbox defaults, for this local mock only.
"""
import json
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

HOST, PORT = "127.0.0.1", 18022
USER, PASSWORD = "devnetuser", "RG!_Yw919_83"
SESSIONS = {}                                    # JSESSIONID -> XSRF token
LOGIN_PAGE = "<html><head><title>Cisco Catalyst SD-WAN</title></head><body>login</body></html>"


def dev(name, dtype, ip, site, model, version):
    return {"deviceId": ip, "host-name": name, "device-type": dtype, "personality": dtype,
            "system-ip": ip, "site-id": site, "reachability": "reachable", "status": "normal",
            "device-model": model, "version": version}


DEVICES = [dev("Manager01", "vmanage", "100.0.0.1", "100", "vmanage", "20.18.2.1"),
           dev("Controller01", "vsmart", "100.0.0.101", "100", "vsmart", "20.18.2.1"),
           dev("Validator01", "vbond", "100.0.0.201", "100", "vedge-cloud", "20.18.2.1")] + [
           dev(f"Edge{i}", "vedge", f"10.0.0.{i}", str(i), "vedge-C8000V", "17.18.01a.0.182")
           for i in range(1, 5)]
COUNTERS = [{"system-ip": "100.0.0.1", "number-vsmart-control-connections": 1, "expectedControlConnections": 1},
            {"system-ip": "100.0.0.201", "number-vsmart-control-connections": 1, "expectedControlConnections": 1},
            {"system-ip": "100.0.0.101", "number-vsmart-control-connections": 0, "expectedControlConnections": 0,
             "ompPeersUp": 4, "ompPeersDown": 0}] + [
            {"system-ip": f"10.0.0.{i}", "number-vsmart-control-connections": 2, "expectedControlConnections": 2,
             "ompPeersUp": 1, "ompPeersDown": 0, "bfdSessionsUp": 6, "bfdSessionsDown": 0} for i in (3, 4, 1, 2)]
CONTROL = [{"local-color": "biz-internet", "peer-type": "vsmart", "peer-host-name": "Controller01",
            "system-ip": "100.0.0.101", "protocol": "dtls", "state": "up"},
           {"local-color": "mpls", "peer-type": "vsmart", "peer-host-name": "Controller01",
            "system-ip": "100.0.0.101", "protocol": "dtls", "state": "up"},
           {"local-color": "biz-internet", "peer-type": "vmanage", "peer-host-name": "Manager01",
            "system-ip": "100.0.0.1", "protocol": "dtls", "state": "up"}]
IF_STATS = [{"host_name": "Edge4", "interface": f"GigabitEthernet{n}", "oper_status": "Up",
             "tx_octets": 3370, "rx_errors": 0} for n in (5, 8, 6)]
DEVICE_TEMPLATES = [{"templateName": f"Factory_Default_{n}", "deviceType": "vedge-" + n,
                     "configType": "template", "factoryDefault": True, "devicesAttached": 0}
                    for n in ("ISR_4331_V01", "C8000V_V01")] * 8 + [
                    {"templateName": "Factory_Default_vSmart", "deviceType": "vsmart", "configType": "template",
                     "factoryDefault": True, "devicesAttached": 0},
                    {"templateName": "edge_basic", "deviceType": "vedge-C8000V", "configType": "template",
                     "factoryDefault": False, "devicesAttached": 0},
                    {"templateName": "controller_basic", "deviceType": "vsmart", "configType": "template",
                     "factoryDefault": False, "devicesAttached": 1}]
FEATURE_TEMPLATES = ([{"templateType": "cisco_vpn_interface"}] * 47 + [{"templateType": "cisco_vpn"}] * 31
                     + [{"templateType": "cisco_omp"}] * 8 + [{"templateType": "vpn-vsmart"}] * 4
                     + [{"templateType": "cisco_banner"}] * 3
                     + [{"templateType": t} for t in ("cisco_system", "cisco_logging", "cisco_bfd", "cisco_ntp",
                                                      "cisco_aaa", "cisco_security", "cisco_snmp")] * 7)

GETS = {"/dataservice/device": DEVICES,
        "/dataservice/device/monitor": [{k: d[k] for k in ("host-name", "system-ip", "device-type", "status")}
                                        for d in DEVICES],
        "/dataservice/device/counters": COUNTERS,
        "/dataservice/device/control/connections": CONTROL,
        "/dataservice/alarms/count": [{"count": 304, "cleared_count": 408}],
        "/dataservice/template/device": DEVICE_TEMPLATES,
        "/dataservice/template/feature": FEATURE_TEMPLATES}
POSTS = {"/dataservice/statistics/interface": IF_STATS, "/dataservice/alarms": []}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def send(self, code, body="", ctype="application/json", headers=None):
        data = (body if isinstance(body, str) else json.dumps(body)).encode()
        self.send_response(code)
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        if data:
            self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def session_id(self):
        for part in self.headers.get("Cookie", "").split(";"):
            name, _, value = part.strip().partition("=")
            if name == "JSESSIONID" and value in SESSIONS:
                return value
        return None

    def wrap(self, rows):
        return {"header": {"generatedOn": 0, "columns": []}, "data": rows}

    def do_GET(self):
        path = urlparse(self.path).path
        sid = self.session_id()
        if path == "/welcome.html" or sid is None:
            return self.send(200, LOGIN_PAGE, "text/html;charset=UTF-8")      # not 401: a login page
        if path == "/dataservice/client/token":
            return self.send(200, SESSIONS[sid], "text/plain")
        if path in GETS:
            return self.send(200, self.wrap(GETS[path]), "application/json; charset=UTF-8")
        return self.send(404, {"error": {"message": f"{path} not found"}})

    def do_POST(self):
        url = urlparse(self.path)
        body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
        if url.path == "/j_security_check":
            form = parse_qs(body)
            if form.get("j_username") == [USER] and form.get("j_password") == [PASSWORD]:
                sid = secrets.token_hex(16)
                SESSIONS[sid] = secrets.token_hex(50)                          # 100-char XSRF token
                return self.send(200, "", headers={"Set-Cookie": f"JSESSIONID={sid}; path=/; HttpOnly"})
            return self.send(200, {"error": {"message": "Login Error", "code": "Failed to login user ",
                                             "details": f" {form.get('j_username', [''])[0]}"}})
        sid = self.session_id()
        if sid is None:
            return self.send(200, LOGIN_PAGE, "text/html;charset=UTF-8")
        if self.headers.get("X-XSRF-TOKEN") != SESSIONS[sid]:
            return self.send(403, "<html><head><title>Error</title></head><body>SessionTokenFilter: Token "
                                  "provided via HTTP Header does not match the token generated by the server."
                                  "</body></html>", "text/html")
        if url.path == "/logout":
            del SESSIONS[sid]
            return self.send(302, headers={"Location": f"http://{HOST}:{PORT}/welcome.html?nocache=1"})
        if url.path in POSTS:
            return self.send(200, self.wrap(POSTS[url.path]), "application/json; charset=UTF-8")
        return self.send(404, {"error": {"message": f"{url.path} not found"}})


if __name__ == "__main__":
    print(f"mock SD-WAN Manager on http://{HOST}:{PORT}")
    HTTPServer((HOST, PORT), Handler).serve_forever()
