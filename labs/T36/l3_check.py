"""T36 reference program: a Layer 3 pre-change checker built on the ipaddress module.

1. Subnet facts for each interface (network, broadcast, mask, hosts, RFC 1918)
2. Gateway sanity check per host
3. Host forwarding decision: same subnet -> ARP for the target, else ARP for the gateway
4. Router: install the best route per prefix (lowest AD, then metric), then forward by longest prefix match
5. IPv6 awareness: compressed/exploded, /64, link-local

Run: python3 l3_check.py   (standard library only)
"""
import ipaddress as ip

RFC1918 = [ip.ip_network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")]

HOSTS = [  # hostname, interface address/prefix, default gateway
    ("pc1", "10.1.10.50/24", "10.1.10.1"),
    ("pc2", "10.1.10.60/24", "10.1.11.1"),        # gateway on another subnet
    ("pc3", "192.168.5.130/26", "192.168.5.191"),  # gateway = broadcast address of its own /26
    ("lnk", "10.0.0.1/30", "10.0.0.2"),
    ("p2p", "10.0.0.8/31", "10.0.0.9"),
    ("dmz", "172.32.1.1/16", "172.32.0.1"),        # 172.32 is NOT in 172.16/12
]

# Candidate routes offered to R1's RIB: (code, prefix, admin distance, metric, next hop)
CANDIDATES = [
    ("C", "10.1.10.0/24", 0, 0, "Gi0/1"),
    ("L", "10.1.10.1/32", 0, 0, "Gi0/1"),
    ("C", "10.1.20.0/24", 0, 0, "Gi0/2"),
    ("C", "203.0.113.0/30", 0, 0, "Gi0/0"),
    ("S", "10.20.0.0/16", 1, 0, "10.1.10.254"),
    ("S", "10.20.0.0/16", 250, 0, "10.1.10.253"),  # floating static (backup)
    ("O", "10.20.30.0/24", 110, 20, "10.1.20.2"),
    ("D", "10.20.30.0/24", 90, 3072, "10.1.20.3"),
    ("B", "172.16.0.0/12", 20, 0, "203.0.113.1"),
    ("S*", "0.0.0.0/0", 1, 0, "203.0.113.1"),
    ("O*E2", "0.0.0.0/0", 110, 1, "10.1.20.2"),
]


def subnet_facts(cidr):
    """Return a dict of facts for one interface address such as 10.1.10.50/24."""
    iface = ip.ip_interface(cidr)                  # host address + prefix (host bits allowed)
    net = iface.network                            # same as ip_network(cidr, strict=False)
    host_bits = 32 - net.prefixlen
    usable = list(net.hosts())                     # excludes network + broadcast (except /31, /32)
    return {
        "address": str(iface.ip),
        "network": str(net),
        "mask": str(net.netmask),
        "wildcard": str(net.hostmask),
        "broadcast": str(net.broadcast_address),
        "formula": 2 ** host_bits - 2,             # classic 2^h - 2
        "usable": len(usable),
        "range": f"{usable[0]} - {usable[-1]}",
        "rfc1918": any(iface.ip in block for block in RFC1918),
        "is_private": iface.ip.is_private,         # wider than RFC 1918 (loopback, link-local...)
    }


def check_gateway(cidr, gateway):
    """A gateway must sit inside the host's subnet and not be its network or broadcast address."""
    net = ip.ip_interface(cidr).network
    gw = ip.ip_address(gateway)
    if gw not in net:
        return f"FAIL {gw} is not in {net}"
    if net.prefixlen < 31 and gw in (net.network_address, net.broadcast_address):
        return f"FAIL {gw} is the network/broadcast address of {net}"
    return "ok"


def host_next_hop(cidr, gateway, destination):
    """The host's own decision: AND dst with MY mask. Same network -> ARP dst, else ARP gateway."""
    net = ip.ip_interface(cidr).network
    dst = ip.ip_address(destination)
    if dst in net:
        return f"same subnet {net} -> ARP for {dst}"
    return f"off-subnet -> ARP for gateway {gateway} (dst IP stays {dst})"


def build_rib(candidates):
    """Route installation: for each identical prefix keep the lowest AD, then the lowest metric."""
    rib = {}
    for code, prefix, ad, metric, nh in candidates:
        net = ip.ip_network(prefix)                # strict=True: host bits set -> ValueError
        best = rib.get(net)
        if best is None or (ad, metric) < (best[1], best[2]):
            rib[net] = (code, ad, metric, nh)
    return rib


def lookup(rib, destination):
    """Forwarding: among installed routes that contain dst, the longest prefix wins. AD is not used."""
    dst = ip.ip_address(destination)
    matches = [net for net in rib if dst in net]
    if not matches:
        return "no route -> drop (ICMP unreachable)"
    best = max(matches, key=lambda n: n.prefixlen)
    code, ad, metric, nh = rib[best]
    lengths = " ".join(f"/{n.prefixlen}" for n in sorted(matches, key=lambda n: n.prefixlen))
    return f"{best} via {nh} ({code})   matched {lengths}"


def ipv6_facts(cidr):
    iface = ip.ip_interface(cidr)
    return {
        "compressed": str(iface.ip),
        "exploded": iface.ip.exploded,
        "network": str(iface.network),
        "link_local": iface.ip.is_link_local,      # fe80::/10
        "/64 hosts": f"2^{128 - iface.network.prefixlen}",
    }


def main():
    print("== 1. Subnet facts ==")
    print(f"{'host':<5}{'network':<18}{'mask':<17}{'broadcast':<16}{'2^h-2':>6}{'hosts()':>8}  rfc1918 is_private")
    for name, cidr, _gw in HOSTS:
        f = subnet_facts(cidr)
        print(f"{name:<5}{f['network']:<18}{f['mask']:<17}{f['broadcast']:<16}"
              f"{f['formula']:>6}{f['usable']:>8}  {str(f['rfc1918']):<8}{f['is_private']}")
    f = subnet_facts("192.168.5.130/26")
    print(f"pc3 detail: wildcard {f['wildcard']}, usable {f['range']}")
    print("127.0.0.1 rfc1918?", any(ip.ip_address("127.0.0.1") in b for b in RFC1918),
          "| is_private?", ip.ip_address("127.0.0.1").is_private)

    print("\n== 2. Gateway check ==")
    for name, cidr, gw in HOSTS:
        print(f"{name:<5}{cidr:<18} gw {gw:<14} {check_gateway(cidr, gw)}")

    print("\n== 3. Host decision (pc1 10.1.10.50/24, gw 10.1.10.1) ==")
    for dst in ("10.1.10.77", "10.1.11.5", "10.20.30.40"):
        print(f"to {dst:<12} {host_next_hop('10.1.10.50/24', '10.1.10.1', dst)}")
    print("192.168.1.10/25 and 192.168.1.200 same subnet?",
          ip.ip_address("192.168.1.200") in ip.ip_interface("192.168.1.10/25").network)

    print("\n== 4. R1 routing table (best per prefix) ==")
    rib = build_rib(CANDIDATES)
    for net, (code, ad, metric, nh) in sorted(rib.items(), key=lambda r: (r[0].network_address, r[0].prefixlen)):
        print(f"{code:<5}{str(net):<16}[{ad}/{metric}] via {nh}")
    installed = {(net, route[3]) for net, route in rib.items()}
    for code, prefix, ad, metric, nh in CANDIDATES:
        if (ip.ip_network(prefix), nh) not in installed:
            print(f"  not installed: {code} {prefix} [{ad}/{metric}] via {nh} (higher AD/metric)")
    print("\n== 5. R1 forwarding (longest prefix match) ==")
    for dst in ("10.1.10.77", "10.20.30.40", "10.20.99.1", "172.20.1.1", "8.8.8.8"):
        print(f"{dst:<12}-> {lookup(rib, dst)}")

    print("\n== 6. Subnetting helpers ==")
    print("10.1.10.0/24 into /26:", [str(n) for n in ip.ip_network("10.1.10.0/24").subnets(new_prefix=26)])
    print("10.20.30.0/24 subnet_of 10.20.0.0/16?",
          ip.ip_network("10.20.30.0/24").subnet_of(ip.ip_network("10.20.0.0/16")))
    try:
        ip.ip_network("10.1.10.50/24")
    except ValueError as err:
        print("ip_network('10.1.10.50/24') ->", err)

    print("\n== 7. IPv6 ==")
    for cidr in ("2001:db8:acad:10::50/64", "fe80::1/64"):
        print(cidr, ipv6_facts(cidr))


if __name__ == "__main__":
    main()
