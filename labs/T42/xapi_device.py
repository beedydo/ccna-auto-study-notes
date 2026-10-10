"""T42 xAPI program: control a RoomOS device two ways (cloud xAPI and on-device HTTP xAPI).

Start the mock first:   python3 labs/T42/mock_webex.py
Then:                   python3 labs/T42/xapi_device.py
Or:                     bash labs/T42/run_lab.sh labs/T42/xapi_device.py

Real targets: WEBEX_BASE=https://webexapis.com/v1 with a token that has the
spark:xapi_statuses + spark:xapi_commands scopes, and DEVICE_URL=https://<device-ip>
with a local device user (Basic auth, self-signed cert -> verify=False).
"""
import os
import re
from urllib.parse import unquote

import requests

BASE = os.environ.get("WEBEX_BASE", "http://127.0.0.1:18042/v1")
BOT_TOKEN = os.environ.get("WEBEX_TOKEN", "T42-mock-bot-token")
XAPI_TOKEN = os.environ.get("WEBEX_XAPI_TOKEN", "T42-mock-integration-token")   # integration / admin token
DEVICE_URL = os.environ.get("DEVICE_URL", "http://127.0.0.1:18042")              # real: https://<device-ip>
DEVICE_AUTH = (os.environ.get("DEVICE_USER", "integrator"), os.environ.get("DEVICE_PASS", "integrator"))


def short_ids(text):
    """Shorten long Webex IDs (base64 of ciscospark://us/DEVICE/<uuid>) for printing."""
    return re.sub(r"Y2lzY29zcGFyazovL[\w-]+", lambda m: m.group()[:16] + "...", text)


def show(resp):
    path = unquote(resp.url.replace(BASE, "").replace(DEVICE_URL, ""))
    print(short_ids(f"<<< {resp.status_code} {resp.request.method} {path}"))
    if resp.content:
        print("    " + short_ids(resp.text.strip()).replace("\n", "\n    "))
    return resp


def cloud():
    print("== A. Cloud xAPI: webexapis.com/v1/xapi/... (JSON, Bearer token) ==")
    bearer = {"Authorization": f"Bearer {XAPI_TOKEN}"}
    device = requests.get(f"{BASE}/devices", headers=bearer, timeout=10).json()["items"][0]
    print(f"    device: {device['displayName']} ({device['product']}, {device['software']})")
    dev_id = device["id"]

    # xStatus Audio Volume  ->  GET /xapi/status?deviceId=...&name=Audio.Volume
    show(requests.get(f"{BASE}/xapi/status", params={"deviceId": dev_id, "name": "Audio.Volume"},
                      headers={"Authorization": f"Bearer {BOT_TOKEN}"}, timeout=10))    # 403: no xapi scope
    show(requests.get(f"{BASE}/xapi/status", params={"deviceId": dev_id, "name": "Audio.Volume"},
                      headers=bearer, timeout=10))

    # xCommand Audio Volume Set Level: 30  ->  POST /xapi/command/Audio.Volume.Set
    show(requests.post(f"{BASE}/xapi/command/Audio.Volume.Set",
                       json={"deviceId": dev_id, "arguments": {"Level": 30}}, headers=bearer, timeout=10))
    show(requests.get(f"{BASE}/xapi/status", params={"deviceId": dev_id, "name": "Audio.Volume"},
                      headers=bearer, timeout=10))


def on_device():
    print("\n== B. On-device xAPI over HTTP: /getxml and /putxml (XML, Basic auth) ==")
    # xStatus Audio Volume  ->  GET /getxml?location=/Status/Audio/Volume
    show(requests.get(f"{DEVICE_URL}/getxml", params={"location": "/Status/Audio/Volume"}, timeout=10))  # 401
    show(requests.get(f"{DEVICE_URL}/getxml", params={"location": "/Status/Audio/Volume"},
                      auth=DEVICE_AUTH, timeout=10))

    xml = {"Content-Type": "text/xml"}
    # xCommand Audio Volume Set Level: 70  ->  POST /putxml <Command>...</Command>
    show(requests.post(f"{DEVICE_URL}/putxml", auth=DEVICE_AUTH, headers=xml, timeout=10,
                       data="<Command><Audio><Volume><Set><Level>70</Level></Set></Volume></Audio></Command>"))
    # xConfiguration Audio DefaultVolume: 40  ->  POST /putxml <Configuration>...</Configuration>
    show(requests.post(f"{DEVICE_URL}/putxml", auth=DEVICE_AUTH, headers=xml, timeout=10,
                       data="<Configuration><Audio><DefaultVolume>40</DefaultVolume></Audio></Configuration>"))
    show(requests.get(f"{DEVICE_URL}/getxml", params={"location": "/Configuration/Audio/DefaultVolume"},
                      auth=DEVICE_AUTH, timeout=10))


if __name__ == "__main__":
    cloud()
    on_device()
