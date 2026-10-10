"""T38 reference program: read a topology the way the exam asks you to.

    python3 labs/T38/trace_path.py

It loads labs/T38/topology.json (campus + DMZ + branch), prints the
physical view (cables) and the logical view (subnets, VLANs, gateways),
then traces eight flows hop by hop and answers the three exam questions:
where is the gateway, which device filters, what path does traffic take.
Python stdlib only.
"""
import ipaddress
import json
import pathlib

TOPO = json.loads((pathlib.Path(__file__).parent / "topology.json").read_text())
DEV = TOPO["devices"]
L3_ROLES = ("router", "l3_switch", "firewall")
ROLE_LABEL = {"host": "host", "access_point": "AP", "wlc": "WLC", "switch": "L2 switch",
              "l3_switch": "L3 switch", "router": "router", "firewall": "firewall",
              "load_balancer": "load bal."}


def iface_list(name):
    """Every (interface, ip_interface) a device owns, hosts included."""
    d = DEV[name]
    if "interfaces" in d:
        return [(i, ipaddress.ip_interface(a)) for i, a in d["interfaces"].items()]
    if "ip" in d:
        return [("eth0", ipaddress.ip_interface(d["ip"]))]
    return []


def owner_of(ip):
    """Which device answers ARP for this IP (interface IP or LB VIP)."""
    ip = ipaddress.ip_address(ip)
    for name, d in DEV.items():
        if d.get("vip") and ipaddress.ip_address(d["vip"]) == ip:
            return name, "VIP"
        for iface, addr in iface_list(name):
            if addr.ip == ip:
                return name, iface
    return None, None


def connected_iface(name, ip):
    """The interface on `name` whose subnet contains `ip` (None if not connected)."""
    ip = ipaddress.ip_address(ip)
    for iface, addr in iface_list(name):
        if ip in addr.network:
            return iface, addr
    return None, None


def longest_match(name, dst):
    """Routing table lookup: most specific prefix wins."""
    dst = ipaddress.ip_address(dst)
    best = None
    for prefix, nh in DEV[name].get("routes", []):
        net = ipaddress.ip_network(prefix)
        if dst in net and (best is None or net.prefixlen > best[0].prefixlen):
            best = (net, nh)
    return best


def firewall_check(fw, in_zone, out_zone, dst, proto, port):
    """First matching rule wins; nothing matches = implicit deny."""
    for rule in DEV[fw]["policy"]:
        if (rule["from"], rule["to"]) != (in_zone, out_zone):
            continue
        if ipaddress.ip_address(dst) not in ipaddress.ip_network(rule["dst"]):
            continue
        if rule["proto"] not in ("any", proto) or rule["port"] not in ("any", port):
            continue
        return rule["action"].upper(), f"rule {rule['id']}"
    return "DENY", "implicit deny"


def pick_backend(lb):
    """Load balancer: first pool member that passes its health check."""
    for member in DEV[lb]["pool"]:
        if member["health"] == "up":
            return member
    return None


def print_physical():
    print("PHYSICAL view: who is cabled to whom (ports)")
    for a, a_port, b, b_port in TOPO["cables"]:
        print(f"  {a:>8} {a_port:<9} <-> {b:<8} {b_port}")


def print_logical():
    print("LOGICAL view: L3 segments, members and gateway")
    segments = {}
    for name in DEV:
        for iface, addr in iface_list(name):
            segments.setdefault(addr.network, []).append((name, iface, addr.ip))
    for net in sorted(segments, key=lambda n: (n.network_address, n.prefixlen)):
        members = segments[net]
        vlans = {DEV[m]["vlan"] for m, _, _ in members if "vlan" in DEV[m]}
        gws = [f"{m} {i}" for m, i, ip in members if DEV[m]["role"] in L3_ROLES]
        tag = f"VLAN {vlans.pop()}" if vlans else ("transit" if net.prefixlen == 30 else "LAN")
        names = ", ".join(m for m, _, _ in members)
        print(f"  {str(net):<16} {tag:<8} gw/L3: {', '.join(gws):<34} members: {names}")


def trace(src, dst_ip, proto, port, label):
    print(f"\n=== {label}: {src} -> {dst_ip} {proto}/{port} ===")
    hops, filters, step = [], [], 0

    def hop(dev, text):
        nonlocal step
        step += 1
        print(f"  {step:>2}. {dev:<8} {ROLE_LABEL[DEV[dev]['role']]:<10} {text}")
        hops.append(dev)

    def via_switch(target, why):
        sw = DEV[target].get("switch")
        if sw:
            hop(sw, f"switches the frame to {target} ({why}, no IP lookup)")

    s = DEV[src]
    src_if = ipaddress.ip_interface(s["ip"])
    gateway = None
    if ipaddress.ip_address(dst_ip) in src_if.network:
        hop(src, f"{dst_ip} is in my subnet {src_if.network}: ARP for it directly")
        sw = s.get("switch")
        hop(sw, f"forwards in VLAN {s.get('vlan')} by MAC table (no router involved)")
        current, _ = owner_of(dst_ip)
    else:
        gateway = s["gateway"]
        hop(src, f"{dst_ip} is off-subnet {src_if.network}: send to gateway {gateway}")
        current, in_iface = owner_of(gateway)
        if current is None:
            print(f"      {'':<8} {'':<10} ARP for {gateway} gets no reply: DROP (wrong default gateway)")
            return report(src, gateway, filters, hops, "DROPPED (bad gateway)")
        if s.get("switch"):
            hop(s["switch"], f"forwards in VLAN {s.get('vlan')} to the gateway's MAC (no IP lookup)")
        while True:
            d = DEV[current]
            if d["role"] == "load_balancer":
                break
            out_iface, _ = connected_iface(current, dst_ip)
            if out_iface:
                next_ip, why = dst_ip, f"{dst_ip} is directly connected on {out_iface}"
            else:
                match = longest_match(current, dst_ip)
                if not match:
                    hop(current, f"no route to {dst_ip}: DROP")
                    return report(src, gateway, filters, hops, "DROPPED (no route)")
                next_ip = match[1]
                out_iface, _ = connected_iface(current, next_ip)
                why = f"route {match[0]} via {next_ip} ({out_iface})"
            if d["role"] == "firewall":
                verdict, rule = firewall_check(current, in_iface, out_iface, dst_ip, proto, port)
                filters.append(current)
                state = "; return traffic allowed by the state table" if verdict == "PERMIT" else ""
                hop(current, f"{in_iface} -> {out_iface} {proto}/{port}: {verdict} ({rule}){state}")
                if verdict == "DENY":
                    return report(src, gateway, filters, hops, "BLOCKED")
                print(f"      {'':<8} {'':<10} then {why}")
            else:
                hop(current, why)
            nxt, nxt_iface = owner_of(next_ip)
            if next_ip == dst_ip or nxt_iface == "VIP":
                current = nxt
                break
            current, in_iface = nxt, nxt_iface

    if DEV[current]["role"] == "load_balancer":
        via_switch(current, "VIP lives on the LB")
        member = pick_backend(current)
        if member is None:
            hop(current, f"VIP {dst_ip}:{port}: no healthy pool member: DROP (client sees 503 / reset)")
            return report(src, gateway, filters, hops, "DROPPED (pool down)")
        down = [m["name"] for m in DEV[current]["pool"] if m["health"] != "up"]
        note = f" ({', '.join(down)} failed health check)" if down else ""
        hop(current, f"VIP {dst_ip}:{port} -> {member['name']} {member['ip']}{note}")
        current = member["name"]
        via_switch(current, "LB to real server")
    elif hops[-1] != DEV[current].get("switch"):
        via_switch(current, "last hop")
    hop(current, "delivered")
    return report(src, gateway, filters, hops, "DELIVERED")


def report(src, gateway, filters, hops, result):
    if gateway is None:
        gw = "none (same subnet)"
    else:
        gw = f"{gateway} ({' '.join(owner_of(gateway))})" if owner_of(gateway)[0] else f"{gateway} (nobody)"
    print(f"  -> gateway for {src}: {gw} | filtered by: {', '.join(filters) or 'nothing'}"
          f" | L3 hops: {sum(DEV[h]['role'] in L3_ROLES for h in hops)} | {result}")
    return result


if __name__ == "__main__":
    print(f"Topology: {TOPO['site']}\n")
    print_physical()
    print()
    print_logical()
    trace("pc1", "10.10.10.22", "tcp", 445, "A. same VLAN")
    trace("pc1", "10.10.20.30", "tcp", 9100, "B. inter-VLAN")
    trace("pc1", "172.16.50.10", "tcp", 443, "C. campus to DMZ web VIP")
    trace("ext1", "172.16.50.10", "tcp", 443, "D. internet to DMZ web VIP")
    trace("ext1", "172.16.50.11", "tcp", 22, "E. internet to a DMZ server directly")
    trace("web1", "10.10.10.21", "tcp", 445, "F. DMZ server to inside PC")
    trace("pc1", "10.20.10.50", "tcp", 22, "G. HQ to branch over the WAN")
    trace("ap1", "10.0.9.10", "udp", 5246, "H. AP joins its WLC (CAPWAP control)")
