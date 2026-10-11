"""Mock API for T09: the same device data in three API styles, plus sync vs async jobs.

Run:  python3 labs/T09/mock_api.py          -> http://127.0.0.1:8109
Python stdlib only. Threaded, so slow requests don't block other clients.

Endpoints
  REST      GET  /api/v1/devices/{id}                  -> 200 JSON | 404
  JSON-RPC  POST /jsonrpc                              -> always HTTP 200; result or error object
  SOAP 1.1  POST /soap   (SOAPAction: "GetDevice")     -> 200 Envelope | 500 Envelope with Fault
  Sync      GET  /api/v1/devices/{id}/config           -> waits 1.5 s, then 200 text/plain
  Async     POST /dna/intent/api/v1/network-device-poller/cli/read-request -> 202 + taskId
            GET  /dna/intent/api/v1/task/{taskId}      -> 200; endTime appears when done
            GET  /dna/intent/api/v1/file/{fileId}      -> 200 command output
The async paths copy the shape of the Catalyst Center (DNA Center) Command Runner + Task API.
"""
import json
import re
import threading
import time
import uuid
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST, PORT = "127.0.0.1", 8109
SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"   # SOAP 1.1 envelope namespace
SLOW_CONFIG_SECONDS = 1.5
JOB_SECONDS = 2.0

devices = {
    1: {"id": 1, "hostname": "csr1", "mgmt_ip": "10.10.20.48", "role": "edge", "os": "iosxe"},
    2: {"id": 2, "hostname": "n9k1", "mgmt_ip": "10.10.20.58", "role": "core", "os": "nxos"},
}
tasks = {}            # taskId -> {"start": epoch ms, "fileId": str, "commands": [...]}
files = {}            # fileId -> command output
lock = threading.Lock()


def now_ms():
    return int(time.time() * 1000)


def soap_envelope(inner):
    return (f'<?xml version="1.0" encoding="utf-8"?>\n'
            f'<soapenv:Envelope xmlns:soapenv="{SOAP_NS}">\n'
            f"  <soapenv:Body>\n    {inner}\n  </soapenv:Body>\n"
            f"</soapenv:Envelope>\n")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def version_string(self):
        return "MockAPI-T09/1.0"

    def log_message(self, *args):
        pass

    def send(self, code, body=None, content_type="application/json"):
        data = b""
        if body is not None:
            data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
        self.send_response(code)
        if data:
            self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length else b""

    # ---------- REST + sync ----------
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/health":
            return self.send(200, {"status": "ok"})

        match = re.fullmatch(r"/api/v1/devices/(\d+)(/config)?", path)
        if match:
            dev = devices.get(int(match.group(1)))
            if dev is None:
                return self.send(404, {"error": f"device {match.group(1)} not found"})
            if match.group(2):                                   # slow synchronous call
                time.sleep(SLOW_CONFIG_SECONDS)
                return self.send(200, f"hostname {dev['hostname']}\n", "text/plain")
            return self.send(200, dev)

        match = re.fullmatch(r"/dna/intent/api/v1/task/([0-9a-f-]+)", path)
        if match:
            return self.get_task(match.group(1))
        match = re.fullmatch(r"/dna/intent/api/v1/file/([0-9a-f-]+)", path)
        if match:
            if match.group(1) not in files:
                return self.send(404, {"error": "file not found"})
            return self.send(200, files[match.group(1)])
        return self.send(404, {"error": "unknown path"})

    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/jsonrpc":
            return self.json_rpc()
        if path == "/soap":
            return self.soap()
        if path == "/dna/intent/api/v1/network-device-poller/cli/read-request":
            return self.start_job()
        return self.send(404, {"error": "unknown path"})

    # ---------- JSON-RPC 2.0 ----------
    def json_rpc(self):
        try:
            req = json.loads(self.read_body())
        except json.JSONDecodeError:
            return self.send(200, {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None})
        rid = req.get("id")
        method, params = req.get("method"), req.get("params", {})
        if method == "getDevice":
            dev = devices.get(params.get("id"))
            if dev is None:
                reply = {"jsonrpc": "2.0", "error": {"code": -32602, "message": "Invalid params: no such device"}, "id": rid}
            else:
                reply = {"jsonrpc": "2.0", "result": dev, "id": rid}
        else:
            reply = {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": rid}
        return self.send(200, reply)          # JSON-RPC errors travel inside an HTTP 200

    # ---------- SOAP 1.1 ----------
    def soap(self):
        action = self.headers.get("SOAPAction", "").strip('"')
        try:
            body = ET.fromstring(self.read_body()).find(f"{{{SOAP_NS}}}Body")
            dev_id = int(body.find("GetDevice/id").text)
        except (ET.ParseError, AttributeError, ValueError):
            dev_id = None
        dev = devices.get(dev_id)
        reason = (f"Unknown SOAPAction '{action}'" if action != "GetDevice"
                  else f"No device with id {dev_id}" if dev is None else None)
        if reason:
            fault = ("<soapenv:Fault>\n      <faultcode>soapenv:Client</faultcode>\n"
                     f"      <faultstring>{reason}</faultstring>\n    </soapenv:Fault>")
            return self.send(500, soap_envelope(fault), "text/xml; charset=utf-8")
        fields = "".join(f"<{k}>{v}</{k}>" for k, v in dev.items())
        return self.send(200, soap_envelope(f"<GetDeviceResponse><device>{fields}</device></GetDeviceResponse>"),
                         "text/xml; charset=utf-8")

    # ---------- async job + task API ----------
    def start_job(self):
        body = json.loads(self.read_body() or b"{}")
        task_id, file_id = str(uuid.uuid4()), str(uuid.uuid4())
        with lock:
            tasks[task_id] = {"start": now_ms(), "fileId": file_id, "commands": body.get("commands", [])}
        return self.send(202, {"response": {"taskId": task_id, "url": f"/api/v1/task/{task_id}"}, "version": "1.0"})

    def get_task(self, task_id):
        with lock:
            task = tasks.get(task_id)
        if task is None:
            return self.send(404, {"error": "task not found"})
        info = {"taskId": task_id, "startTime": task["start"], "isError": False}
        if now_ms() - task["start"] < JOB_SECONDS * 1000:
            info["progress"] = "CLI Runner request creation"           # still running: no endTime yet
        else:
            info["progress"] = json.dumps({"fileId": task["fileId"]})   # done: progress holds the fileId
            info["endTime"] = task["start"] + int(JOB_SECONDS * 1000)
            with lock:
                files.setdefault(task["fileId"], [{"deviceUuid": "csr1",
                                                   "commandResponses": {"SUCCESS": {
                                                       c: f"{c}\ncsr1 uptime is 4 weeks" for c in task["commands"]}}}])
        return self.send(200, {"response": info, "version": "1.0"})


if __name__ == "__main__":
    print(f"Mock API on http://{HOST}:{PORT}  (Ctrl+C to stop)")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
