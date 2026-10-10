"""Mock Cisco Intersight REST API for the T24 lab.

Run:  python3 labs/T24/mock_intersight.py      -> http://127.0.0.1:18024/api/v1
Needs: cryptography (pip install cryptography; the lab container has it via ansible-core).

Response shapes follow developer.cisco.com/docs/intersight (OData query syntax, .List
envelopes with "ObjectType" + "Results"). Data and keys are fake.

What it imitates:
  - auth:      API key = keyId + private key. EVERY request carries
               Authorization: Signature keyId="...",algorithm="...",headers="(request-target) host date digest",signature="..."
               The mock looks up the PUBLIC key for keyId and verifies the signature.
               No / bad signature, wrong Digest or a Date more than 5 min off -> 401
  - resources: GET /api/v1/compute/PhysicalSummaries   (every server, any management mode)
               GET /api/v1/compute/Blades, /compute/RackUnits
               GET /api/v1/server/Profiles             (Intersight server profiles)
  - OData:     $select, $filter (Prop eq 'value' [and ...]), $top (default 100, max 1000),
               $skip, $orderby, $inlinecount=allpages -> "Count"
"""
import base64
import hashlib
import json
import os
import re
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa

HOST, PORT = "127.0.0.1", int(os.environ.get("MOCK_INTERSIGHT_PORT", "18024"))
KEY_ID = os.environ.get("MOCK_INTERSIGHT_KEY_ID", "5f7b3c9e7564612d33a1b2c3/5f7b3c9e7564612d33a1b2c4/6702a1b07564612d30c0ffee")
PUBLIC_KEY_FILE = os.environ.get("MOCK_INTERSIGHT_PUBKEY", "/tmp/t24-lab/PublicKey.pem")


def phys(moid, name, model, serial, mode, dn, power="on", cpus=2, mem=393216, fw="4.2(3d)", source="UCS-SG-DC1"):
    return {"ClassId": "compute.PhysicalSummary", "ObjectType": "compute.PhysicalSummary", "Moid": moid,
            "Name": name, "Model": model, "Serial": serial, "ManagementMode": mode, "Dn": dn,
            "OperPowerState": power, "NumCpus": cpus, "AvailableMemory": mem, "Firmware": fw,
            "SourceObjectType": "compute.Blade" if "blade" in dn else "compute.RackUnit",
            "RegisteredDevice": {"ClassId": "mo.MoRef", "ObjectType": "asset.DeviceRegistration",
                                 "Moid": "6702a0f07564612d30aa0001", "DeviceHostname": [source]}}


DATA = {
    "compute/PhysicalSummaries": [
        phys("6702a1c17564612d30b00001", "UCS-SG-DC1-1-1", "UCSB-B200-M5", "FLM2341001A", "UCSM", "sys/chassis-1/blade-1"),
        phys("6702a1c17564612d30b00002", "UCS-SG-DC1-1-2", "UCSB-B200-M5", "FLM2341001B", "UCSM", "sys/chassis-1/blade-2"),
        phys("6702a1c17564612d30b00003", "UCS-SG-DC1-1-3", "UCSB-B200-M6", "FLM2341001C", "UCSM", "sys/chassis-1/blade-3", power="off", mem=524288),
        phys("6702a1c17564612d30b00004", "UCS-TY-DC2-1-1", "UCSX-210C-M7", "FCH2701X01A", "Intersight", "/redfish/v1/Systems/FCH2701X01A", mem=1048576, fw="5.2(2.240053)", source="UCS-TY-DC2"),
        phys("6702a1c17564612d30b00005", "UCS-TY-DC2-1-2", "UCSX-210C-M7", "FCH2701X01B", "Intersight", "/redfish/v1/Systems/FCH2701X01B", power="off", mem=1048576, fw="5.2(2.240053)", source="UCS-TY-DC2"),
        phys("6702a1c17564612d30b00006", "NY-EDGE-C220", "UCSC-C220-M6S", "WZP2701001E", "IntersightStandalone", "sys/rack-unit-1", cpus=1, mem=131072, fw="4.3(2.230207)", source="NY-EDGE-C220"),
    ],
    "server/Profiles": [
        {"ClassId": "server.Profile", "ObjectType": "server.Profile", "Moid": "6702a2007564612d30c00001",
         "Name": "TY-ESX-01", "TargetPlatform": "FIAttached", "ConfigContext": {"ConfigState": "Associated"},
         "AssignedServer": {"ObjectType": "compute.Blade", "Moid": "6702a1c17564612d30b00004"}},
        {"ClassId": "server.Profile", "ObjectType": "server.Profile", "Moid": "6702a2007564612d30c00002",
         "Name": "TY-ESX-02", "TargetPlatform": "FIAttached", "ConfigContext": {"ConfigState": "Not-assigned"},
         "AssignedServer": None},
    ],
}
DATA["compute/Blades"] = [dict(s, ClassId="compute.Blade", ObjectType="compute.Blade")
                          for s in DATA["compute/PhysicalSummaries"] if s["SourceObjectType"] == "compute.Blade"]
DATA["compute/RackUnits"] = [dict(s, ClassId="compute.RackUnit", ObjectType="compute.RackUnit")
                             for s in DATA["compute/PhysicalSummaries"] if s["SourceObjectType"] == "compute.RackUnit"]


def load_public_key():
    with open(PUBLIC_KEY_FILE, "rb") as fh:
        return serialization.load_pem_public_key(fh.read())


def verify(handler, body):
    """Return None if the HTTP signature is valid, else an error message."""
    auth = handler.headers.get("Authorization", "")
    if not auth.startswith("Signature "):
        return "Authorization header must use the HTTP Signature scheme"
    params = dict(re.findall(r'(\w+)="([^"]*)"', auth))
    if params.get("keyId") != KEY_ID:
        return f"Unknown API key ID '{params.get('keyId')}'"
    try:
        sent = parsedate_to_datetime(handler.headers.get("Date", ""))
    except (TypeError, ValueError):
        return "Missing or invalid Date header"
    if abs((datetime.now(timezone.utc) - sent).total_seconds()) > 300:
        return "Date header is more than 5 minutes off"
    expected_digest = "SHA-256=" + base64.b64encode(hashlib.sha256(body).digest()).decode()
    if handler.headers.get("Digest") != expected_digest:
        return "Digest header does not match the request body"
    lines = []
    for name in params.get("headers", "").split():
        if name == "(request-target)":
            lines.append(f"(request-target): {handler.command.lower()} {handler.path}")
        else:
            lines.append(f"{name}: {handler.headers.get(name, '')}")
    to_sign = "\n".join(lines).encode()
    signature = base64.b64decode(params.get("signature", ""))
    key = load_public_key()
    try:
        if isinstance(key, ec.EllipticCurvePublicKey):
            key.verify(signature, to_sign, ec.ECDSA(hashes.SHA256()))
        elif isinstance(key, rsa.RSAPublicKey):
            key.verify(signature, to_sign, padding.PKCS1v15(), hashes.SHA256())
    except InvalidSignature:
        return "Signature verification failed"
    return None


def odata(items, query):
    """Apply the OData query options Intersight supports to a list of dicts."""
    q = {k: v[0] for k, v in parse_qs(query).items()}
    if "$filter" in q:
        for prop, val in re.findall(r"(\w+) eq '([^']*)'", q["$filter"]):
            items = [i for i in items if str(i.get(prop)) == val]
    count = len(items)
    if "$orderby" in q:
        items = sorted(items, key=lambda i: str(i.get(q["$orderby"].split()[0], "")))
    skip, top = int(q.get("$skip", 0)), min(int(q.get("$top", 100)), 1000)
    items = items[skip:skip + top]
    if "$select" in q:
        keep = ["ClassId", "Moid", "ObjectType"] + q["$select"].split(",")
        items = [{k: i[k] for k in keep if k in i} for i in items]
    return items, count, q.get("$inlinecount") == "allpages"


class Handler(BaseHTTPRequestHandler):
    server_version = "MockIntersight/1.0"

    def reply(self, code, payload):
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        problem = verify(self, b"")
        if problem:
            return self.reply(401, {"code": "AuthenticationFailure", "message": problem,
                                    "messageId": "iam_signature_invalid", "traceId": "mock-trace-0001"})
        url = urlparse(self.path)
        resource = url.path.removeprefix("/api/v1/")
        if resource not in DATA:
            return self.reply(404, {"code": "NotFound", "message": f"Unknown resource '{url.path}'"})
        items, count, inline = odata(DATA[resource], url.query)
        object_type = DATA[resource][0]["ObjectType"]
        body = {"ObjectType": f"{object_type}.List", "Results": items}
        if inline:
            body["Count"] = count
        self.reply(200, body)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    print(f"Mock Intersight API on http://{HOST}:{PORT}/api/v1 (public key {PUBLIC_KEY_FILE})")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
