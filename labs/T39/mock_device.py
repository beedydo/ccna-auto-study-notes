"""Mock IOS XE RESTCONF device for the T39 lab (Python stdlib only).

Run:  python3 labs/T39/mock_device.py      -> http://127.0.0.1:18039/restconf/data
It answers four RESTCONF paths, one or more per plane, with doc-shaped JSON:
  management plane config : Cisco-IOS-XE-native:native/logging, .../ip/ssh
  control plane results   : ietf-routing:routing-state (RIB), Cisco-IOS-XE-arp-oper:arp-data
  data plane counters     : ietf-interfaces:interfaces-state/interface=GigabitEthernet2/statistics
The interface counters grow on every read, as if traffic were being forwarded.
Credentials come from env vars; the fallbacks are fake, for this local mock only.
"""
import base64
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = "127.0.0.1"
PORT = int(os.environ.get("T39_PORT", "18039"))
USER = os.environ.get("RESTCONF_USER", "admin")
PASSWORD = os.environ.get("RESTCONF_PASS", "C1sco12345")
MEDIA = "application/yang-data+json"

reads = {"count": 0}

MGMT_LOGGING = {"Cisco-IOS-XE-native:logging": {
    "host": {"ipv4-host-list": [{"ipv4-host": "10.10.20.100"}]}}}
MGMT_SSH = {"Cisco-IOS-XE-native:ssh": {"version": 2}}

RIB = {"ietf-routing:routing-state": {"routing-instance": [{
    "name": "default",
    "ribs": {"rib": [{
        "name": "ipv4-default",
        "address-family": "ietf-routing:ipv4",
        "routes": {"route": [
            {"destination-prefix": "0.0.0.0/0", "source-protocol": "ietf-routing:static",
             "next-hop": {"next-hop-address": "10.10.20.254"}},
            {"destination-prefix": "10.10.20.0/24", "source-protocol": "ietf-routing:direct",
             "next-hop": {"outgoing-interface": "GigabitEthernet1"}},
            {"destination-prefix": "172.16.10.0/24", "source-protocol": "ietf-ospf:ospfv2",
             "next-hop": {"next-hop-address": "192.168.1.2"}},
            {"destination-prefix": "203.0.113.0/24", "source-protocol": "ietf-routing:bgp",
             "next-hop": {"next-hop-address": "192.168.1.6"}},
        ]},
    }]},
}]}}

ARP = {"Cisco-IOS-XE-arp-oper:arp-data": {"arp-vrf": [{
    "vrf": "",
    "arp-oper": [
        {"address": "10.10.20.254", "hardware": "00:50:56:bf:49:0f", "interface": "GigabitEthernet1"},
        {"address": "192.168.1.2", "hardware": "52:54:00:1a:2b:3c", "interface": "GigabitEthernet2"},
    ],
}]}}


def interface_stats():
    """Counters that grow on every read: the ASIC kept forwarding in between."""
    reads["count"] += 1
    n = reads["count"]
    return {"ietf-interfaces:statistics": {
        "in-octets": 918273645 + n * 1_250_000,
        "in-unicast-pkts": 1402115 + n * 1_000,
        "out-octets": 734120988 + n * 1_100_000,
        "out-unicast-pkts": 1188730 + n * 900,
        "in-discards": 0,
        "in-errors": 0,
    }}


ROUTES = {
    "/restconf/data/Cisco-IOS-XE-native:native/logging": lambda: MGMT_LOGGING,
    "/restconf/data/Cisco-IOS-XE-native:native/ip/ssh": lambda: MGMT_SSH,
    "/restconf/data/ietf-routing:routing-state": lambda: RIB,
    "/restconf/data/Cisco-IOS-XE-arp-oper:arp-data": lambda: ARP,
    "/restconf/data/ietf-interfaces:interfaces-state/interface=GigabitEthernet2/statistics": interface_stats,
}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def send(self, code, body=None):
        data = json.dumps(body).encode() if body is not None else b""
        self.send_response(code)
        if data:
            self.send_header("Content-Type", MEDIA)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            return self.send(200, {"status": "up"})
        expected = "Basic " + base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()
        if self.headers.get("Authorization") != expected:
            return self.send(401, {"errors": {"error": [{"error-tag": "access-denied"}]}})
        handler = ROUTES.get(self.path)
        if handler is None:
            return self.send(404, {"errors": {"error": [{"error-tag": "invalid-value"}]}})
        return self.send(200, handler())


if __name__ == "__main__":
    HTTPServer((HOST, PORT), Handler).serve_forever()
