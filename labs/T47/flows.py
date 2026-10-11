"""T47 reference program: five API flows, each printed as a sequence-diagram trace.

Run:  python3 labs/T47/flows.py
It starts labs/T47/mock_api.py in a thread on http://127.0.0.1:8147, runs the flows, and exits
(the server stops with the process). Python stdlib only.

Every HTTP request prints one solid arrow (->>) and every response one dashed arrow (-->>),
numbered in time order, so the output can be laid next to the matching diagram in
assets/T47/ and compared line by line.
"""
import base64
import json
import threading
import time
import urllib.error
import urllib.request

import mock_api
import seqtrace

BASE = f"http://{mock_api.HOST}:{mock_api.PORT}"
BASIC = "Basic " + base64.b64encode(b"devnet:cisco123").decode()
WEBEX = {"Authorization": f"Bearer {mock_api.WEBEX_TOKEN}"}


def summary(body):
    """Shorten a JSON reply to the fields a diagram label would show."""
    if body is None:
        return ""
    inner = body.get("response", body) if isinstance(body, dict) else body
    if isinstance(inner, list) and inner and "commandResponses" in inner[0]:   # Command Runner file
        return "SUCCESS: " + ", ".join(inner[0]["commandResponses"]["SUCCESS"])
    if isinstance(inner, list):                                    # device list
        return "[" + ", ".join(d["hostname"] for d in inner) + "]"
    if "Token" in inner:
        return f'{{"Token": "{inner["Token"]}"}}'
    if "isError" in inner:                                         # task status
        done = f'endTime set, progress={inner["progress"]}' if "endTime" in inner else "no endTime yet"
        return f'isError={str(inner["isError"]).lower()}, {done}'
    keys = ("taskId", "error", "id", "status", "targetUrl", "text", "message")
    return json.dumps({k: inner[k] for k in keys if k in inner})


def call(src, dst, method, path, body=None, headers=None):
    """One request/response pair = one solid arrow down, one dashed arrow back."""
    headers = dict(headers or {})
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    auth = next((f" [{k}: {v}]" for k, v in headers.items()
                 if k in ("X-Auth-Token", "Authorization")), "")
    seqtrace.arrow(src, dst, f"{method} {path}{auth}")
    request = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        response = urllib.request.urlopen(request, timeout=5)
    except urllib.error.HTTPError as err:          # 4xx/5xx still carry a body
        response = err
    text = response.read().decode()
    body = json.loads(text) if text else None
    seqtrace.arrow(dst, src, f"{response.status} {response.reason} {summary(body)}", reply=True)
    return response.status, body


# ---------- Flow 1 (T47.03): authenticate, then call the API with the token ----------
def get_token():
    status, body = call("Client", "CatC", "POST", "/dna/system/api/v1/auth/token",
                        headers={"Authorization": BASIC})
    return body["Token"]


# ---------- Flow 2 (T47.02 alt): 200 → use data | 401 → get a new token, retry once ----------
def get_devices(session, path="/dna/intent/api/v1/network-device"):
    status, body = call("Client", "CatC", "GET", path, headers={"X-Auth-Token": session["token"]})
    if status == 401:                                              # alt [401 token expired]
        seqtrace.note("Client", "alt 401: token expired -> log in again, retry once")
        session["token"] = get_token()
        status, body = call("Client", "CatC", "GET", path, headers={"X-Auth-Token": session["token"]})
    return body["response"]


# ---------- Flow 3 (T47.04 loop): POST job → 202 + taskId → poll task → GET result ----------
def run_command(session, command):
    hdr = {"X-Auth-Token": session["token"]}
    status, body = call("Client", "CatC", "POST",
                        "/dna/intent/api/v1/network-device-poller/cli/read-request",
                        {"commands": [command], "deviceUuids": ["dev-1"]}, hdr)
    task_id = body["response"]["taskId"]                           # 202 = accepted, NOT done
    while True:                                                    # loop [until endTime is set]
        time.sleep(0.2)
        task = call("Client", "CatC", "GET", f"/dna/intent/api/v1/task/{task_id}", headers=hdr)[1]["response"]
        if task["isError"]:                                        # opt [isError true]
            raise RuntimeError(task.get("failureReason"))
        if "endTime" in task:
            break
    file_id = json.loads(task["progress"])["fileId"]
    return call("Client", "CatC", "GET", f"/dna/intent/api/v1/file/{file_id}", headers=hdr)[1]


# ---------- Flow 4 (T47.02 loop): paginate with offset/limit until a short page ----------
def all_devices(session, limit=2):
    devices, offset = [], 1                                        # Catalyst Center offset starts at 1
    while True:                                                    # loop [until page < limit]
        page = get_devices(session, f"/dna/intent/api/v1/network-device?offset={offset}&limit={limit}")
        devices += page
        if len(page) < limit:
            return devices
        offset += limit


# ---------- Flow 5 (T47.05): register webhook → event → service POSTs to us → we GET details ----------
received = threading.Event()


def webhook_listener(handler):
    """The app's targetUrl. Runs when Webex (the mock) POSTs a notification to us."""
    length = int(handler.headers.get("Content-Length", 0))
    note = json.loads(handler.rfile.read(length))
    seqtrace.arrow("Webex", "App", f"POST /webhook-listener {json.dumps(note['data'])}")
    handler.send(200)                                              # ack fast, then do the work
    seqtrace.arrow("App", "Webex", "200 OK", reply=True)
    message = call("App", "Webex", "GET", f"/v1/messages/{note['data']['id']}", headers=WEBEX)[1]
    seqtrace.note("App", f"full text = {message['text']!r}")
    received.set()


def webhook_flow():
    mock_api.extra_routes["/webhook-listener"] = webhook_listener
    call("App", "Webex", "POST", "/v1/webhooks",
         {"name": "new-msg", "targetUrl": f"{BASE}/webhook-listener",
          "resource": "messages", "event": "created"}, WEBEX)
    seqtrace.note("App", "nothing to do now: no polling, just wait")
    call("User", "Webex", "POST", "/v1/messages", {"roomId": "room-1", "text": "edge1 is down"}, WEBEX)
    received.wait(timeout=5)


def main():
    server = mock_api.serve_in_thread()
    try:
        seqtrace.start("Flow 1 · auth, then call")
        session = {"token": get_token()}
        get_devices(session, "/dna/intent/api/v1/network-device?offset=1&limit=2")

        seqtrace.start("Flow 2 · alt: 200 vs 401 -> re-auth")
        get_devices(session, "/dna/intent/api/v1/network-device?offset=1&limit=1")
        mock_api.expire_tokens()                                   # time passes; the token expires
        seqtrace.note("CatC", "time passes: tok-0001 expires")
        get_devices(session, "/dna/intent/api/v1/network-device?offset=1&limit=1")

        seqtrace.start("Flow 3 · async job: 202 + taskId, poll, fetch")
        result = run_command(session, "show version")
        print(f"   result: {result[0]['commandResponses']['SUCCESS']['show version']!r}")

        seqtrace.start("Flow 4 · pagination loop")
        names = [d["hostname"] for d in all_devices(session, limit=2)]
        print(f"   collected {len(names)} devices: {names}")

        seqtrace.start("Flow 5 · webhook")
        webhook_flow()
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
