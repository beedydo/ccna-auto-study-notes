"""T09 reference program: one device lookup in three API styles, then sync vs async.

Start the mock API first:   python3 labs/T09/mock_api.py
Then in another terminal:   python3 labs/T09/api_styles.py
Or both at once:            bash labs/T09/run_lab.sh

Python stdlib only (urllib), so every method, URL, header and body is visible.
"""
import asyncio
import json
import os
import socket
import time
import urllib.error
import urllib.request

BASE = os.environ.get("API_BASE", "http://127.0.0.1:8109")


def http(method, path, body=None, headers=None, timeout=10):
    """Send one request, print what went over the wire, return (status, body text)."""
    data = body.encode() if isinstance(body, str) else body
    request = urllib.request.Request(BASE + path, data=data, headers=headers or {}, method=method)
    print(f">>> {method} {path}")
    for name, value in (headers or {}).items():
        print(f"    {name}: {value}")
    if body:
        print("    " + body.strip().replace("\n", "\n    "))
    try:
        response = urllib.request.urlopen(request, timeout=timeout)
    except urllib.error.HTTPError as err:          # 4xx/5xx still carry a body
        response = err
    text = response.read().decode()
    print(f"<<< {response.status} {response.reason}")
    print("    " + text.strip().replace("\n", "\n    "))
    return response.status, text


# ---------- 1. REST: the resource is in the URI, the action is the HTTP method ----------
def rest_get_device(dev_id):
    return http("GET", f"/api/v1/devices/{dev_id}", headers={"Accept": "application/json"})


# ---------- 2. JSON-RPC: one endpoint, always POST, the action is "method" in the body ----------
def rpc_call(method, params, call_id):
    payload = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": call_id})
    status, text = http("POST", "/jsonrpc", payload, {"Content-Type": "application/json"})
    reply = json.loads(text)
    if "error" in reply:                           # errors arrive inside an HTTP 200
        print(f"    -> HTTP {status} but JSON-RPC error {reply['error']['code']}")
    return reply


# ---------- 3. SOAP: XML Envelope > Body, operation named by SOAPAction + body element ----------
SOAP_REQUEST = """<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Header/>
  <soapenv:Body>
    <GetDevice><id>{dev_id}</id></GetDevice>
  </soapenv:Body>
</soapenv:Envelope>
"""


def soap_get_device(dev_id):
    return http("POST", "/soap", SOAP_REQUEST.format(dev_id=dev_id),
                {"Content-Type": "text/xml; charset=utf-8", "SOAPAction": '"GetDevice"'})


# ---------- 4. Synchronous: the client blocks until the full answer arrives ----------
def sync_get_config(dev_id, timeout):
    start = time.monotonic()
    try:
        http("GET", f"/api/v1/devices/{dev_id}/config", timeout=timeout)
    except (TimeoutError, socket.timeout, urllib.error.URLError) as err:
        print(f"    !!! client gave up: {err}")
    print(f"    (blocked for {time.monotonic() - start:.1f} s)")


# ---------- 5. Asynchronous: 202 + taskId -> poll the task -> fetch the result ----------
def async_run_command():
    payload = json.dumps({"commands": ["show version"], "deviceUuids": ["csr1"]})
    status, text = http("POST", "/dna/intent/api/v1/network-device-poller/cli/read-request",
                        payload, {"Content-Type": "application/json"})
    task_id = json.loads(text)["response"]["taskId"]           # 202: accepted, NOT done
    print(f"    -> {status}: job queued, taskId {task_id[:8]}..., client is free")

    for attempt in range(1, 11):
        time.sleep(1)                                            # poll interval
        task = json.loads(http("GET", f"/dna/intent/api/v1/task/{task_id}")[1])["response"]
        if task.get("isError"):
            raise RuntimeError(task.get("failureReason", "task failed"))
        if "endTime" in task:                                    # endTime set = finished
            print(f"    -> finished after {attempt} poll(s)")
            break
    file_id = json.loads(task["progress"])["fileId"]             # result pointer lives in progress
    http("GET", f"/dna/intent/api/v1/file/{file_id}")


# ---------- 6. asyncio (awareness): wait on two slow calls at the same time ----------
def fetch_quietly(dev_id):
    with urllib.request.urlopen(f"{BASE}/api/v1/devices/{dev_id}/config", timeout=10) as r:
        return r.read().decode().strip()


async def fetch_both():
    return await asyncio.gather(asyncio.to_thread(fetch_quietly, 1),
                                asyncio.to_thread(fetch_quietly, 2))


def main():
    print("== 1. REST ==")
    rest_get_device(1)
    rest_get_device(99)

    print("\n== 2. JSON-RPC ==")
    rpc_call("getDevice", {"id": 1}, 1)
    rpc_call("deleteEverything", {}, 2)

    print("\n== 3. SOAP ==")
    soap_get_device(1)
    soap_get_device(99)

    print("\n== 4. Synchronous (server takes 1.5 s) ==")
    sync_get_config(1, timeout=0.5)
    sync_get_config(1, timeout=5)

    print("\n== 5. Asynchronous (Catalyst Center-style task API) ==")
    async_run_command()

    print("\n== 6. asyncio: two 1.5 s calls ==")
    start = time.monotonic()
    one_by_one = [fetch_quietly(1), fetch_quietly(2)]
    print(f"    sequential: {one_by_one} in {time.monotonic() - start:.1f} s")
    start = time.monotonic()
    together = asyncio.run(fetch_both())
    print(f"    asyncio.gather: {together} in {time.monotonic() - start:.1f} s")


if __name__ == "__main__":
    main()
