"""T39 reference program: one RESTCONF session that reads all three planes.

Start the mock first:  python3 labs/T39/mock_device.py
Then:                  python3 labs/T39/planes_probe.py
Real device:           export RESTCONF_BASE=https://<host>/restconf/data (plus RESTCONF_USER / RESTCONF_PASS)

Every call below travels over the MANAGEMENT plane (RESTCONF over HTTP/S).
What it reads back is management config, CONTROL-plane results or DATA-plane counters.
"""
import os
import time

import requests

BASE = os.environ.get("RESTCONF_BASE", "http://127.0.0.1:18039/restconf/data")
AUTH = (os.environ.get("RESTCONF_USER", "admin"), os.environ.get("RESTCONF_PASS", "C1sco12345"))
HEADERS = {"Accept": "application/yang-data+json"}

# Which plane does each protocol or function belong to? (T39.05)
PLANES = {
    "management": ["SSH", "Telnet", "SNMP", "NETCONF", "RESTCONF", "gNMI", "syslog",
                   "NTP", "TACACS+", "RADIUS", "NetFlow export", "HTTPS GUI"],
    "control": ["OSPF", "EIGRP", "BGP", "IS-IS", "STP", "ARP", "LACP", "CDP", "LLDP",
                "HSRP", "BFD", "PIM", "OpenFlow (controller -> switch)"],
    "data": ["forward frame by MAC table", "forward packet by FIB (CEF)", "ACL permit/deny",
             "NAT translation", "QoS marking/queuing", "VXLAN/GRE encapsulation", "TTL decrement"],
}


def which_plane(item):
    """Return the plane name for a protocol or function, or 'unknown'."""
    for plane, items in PLANES.items():
        if item in items:
            return plane
    return "unknown"


def get(path):
    """One RESTCONF GET over the management plane; returns the decoded JSON body."""
    response = requests.get(f"{BASE}/{path}", auth=AUTH, headers=HEADERS, verify=False, timeout=10)
    response.raise_for_status()
    return response.json()


def management_plane():
    print("== MANAGEMENT plane: how we reach and watch the box ==")
    ssh = get("Cisco-IOS-XE-native:native/ip/ssh")["Cisco-IOS-XE-native:ssh"]
    log = get("Cisco-IOS-XE-native:native/logging")["Cisco-IOS-XE-native:logging"]
    print(f"  ip ssh version {ssh['version']}")
    for host in log["host"]["ipv4-host-list"]:
        print(f"  logging host {host['ipv4-host']}")


def control_plane():
    print("\n== CONTROL plane: what the protocols decided (RIB + ARP) ==")
    state = get("ietf-routing:routing-state")["ietf-routing:routing-state"]
    rib = state["routing-instance"][0]["ribs"]["rib"][0]
    for route in rib["routes"]["route"]:
        proto = route["source-protocol"].split(":")[1]
        hop = route["next-hop"].get("next-hop-address") or route["next-hop"].get("outgoing-interface")
        print(f"  {route['destination-prefix']:<16} via {hop:<16} learned by {proto}")
    arp = get("Cisco-IOS-XE-arp-oper:arp-data")["Cisco-IOS-XE-arp-oper:arp-data"]
    for entry in arp["arp-vrf"][0]["arp-oper"]:
        print(f"  ARP {entry['address']:<14} -> {entry['hardware']} on {entry['interface']}")


def data_plane(interval=1.0):
    print("\n== DATA plane: what the hardware forwarded (counters) ==")
    path = "ietf-interfaces:interfaces-state/interface=GigabitEthernet2/statistics"
    first = get(path)["ietf-interfaces:statistics"]
    time.sleep(interval)
    second = get(path)["ietf-interfaces:statistics"]
    for key in ("in-unicast-pkts", "out-unicast-pkts", "in-discards"):
        delta = int(second[key]) - int(first[key])
        print(f"  {key:<17} {int(second[key]):>9}  (+{delta} in {interval:.0f}s)")


def classify_drill():
    print("\n== Exam drill: place each item in its plane ==")
    for item in ["BGP", "SNMP", "ARP", "ACL permit/deny", "NETCONF", "STP", "NAT translation", "syslog"]:
        print(f"  {item:<16} -> {which_plane(item)}")


def main():
    requests.packages.urllib3.disable_warnings()      # lab devices use self-signed certs
    management_plane()
    control_plane()
    data_plane()
    classify_drill()


if __name__ == "__main__":
    main()
