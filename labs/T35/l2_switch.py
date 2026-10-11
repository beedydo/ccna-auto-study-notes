"""T35 reference program: a VLAN-aware Layer 2 switch, in about 150 lines.

Run:  python3 labs/T35/l2_switch.py
Python stdlib only. Every exam question "what does the switch do with this frame?"
is one call to Switch.receive() below.
"""
import re

OUI_DB = {"00000C": "Cisco Systems"}            # tiny stand-in for the IEEE OUI registry
BROADCAST = "ffff.ffff.ffff"


def normalise(mac):
    """Any of aa:bb:cc:dd:ee:ff, AA-BB-CC-DD-EE-FF, aabb.ccdd.eeff -> Cisco dotted form."""
    digits = re.sub(r"[^0-9a-fA-F]", "", mac).lower()
    if len(digits) != 12:                        # 12 hex digits x 4 bits = 48 bits
        raise ValueError(f"not a 48-bit MAC: {mac}")
    return f"{digits[0:4]}.{digits[4:8]}.{digits[8:12]}"


def classify_mac(mac):
    """Split a MAC into OUI + NIC part and read the two special bits of the first octet."""
    mac = normalise(mac)
    digits = mac.replace(".", "")
    first_octet = int(digits[0:2], 16)
    if mac == BROADCAST:
        cast = "broadcast"
    elif first_octet & 0b01:                     # I/G bit (LSB of octet 1): 1 = group
        cast = "multicast"
    else:
        cast = "unicast"
    admin = "local" if first_octet & 0b10 else "universal"   # U/L bit (2nd LSB)
    oui = digits[0:6].upper()
    return {"mac": mac, "oui": oui, "nic": digits[6:].upper(), "cast": cast,
            "admin": admin, "vendor": OUI_DB.get(oui, "-")}


def dot1q_tag(vlan, pcp=0, dei=0):
    """The 4-byte 802.1Q tag inserted after the source MAC: TPID 0x8100 + PCP(3) DEI(1) VID(12)."""
    if not 1 <= vlan <= 4094:                    # 0 and 4095 are reserved
        raise ValueError(f"VLAN {vlan} outside 1-4094")
    tci = (pcp << 13) | (dei << 12) | vlan
    return (0x8100).to_bytes(2, "big") + tci.to_bytes(2, "big")


class Switch:
    def __init__(self, name, ports, aging_time=300):
        self.name = name
        self.ports = ports                       # {port: {"mode": "access"|"trunk", ...}}
        self.aging_time = aging_time             # Cisco default: 300 seconds
        self.table = {}                          # {(vlan, mac): (port, last_seen)}

    def ingress_vlan(self, port, tag):
        """Which VLAN does an arriving frame belong to? None = drop."""
        cfg = self.ports[port]
        if cfg["mode"] == "access":
            return cfg["vlan"] if tag is None else None      # access ports expect untagged
        vlan = cfg["native"] if tag is None else tag         # trunk: untagged = native VLAN
        return vlan if vlan in cfg["allowed"] else None

    def egress(self, port, vlan):
        """How does the frame leave this port? Tagged on a trunk unless it is the native VLAN."""
        cfg = self.ports[port]
        if cfg["mode"] == "access":
            return f"{port} (untagged)" if cfg["vlan"] == vlan else None
        if vlan not in cfg["allowed"]:
            return None
        return f"{port} (untagged, native)" if vlan == cfg["native"] else f"{port} (tag {vlan})"

    def receive(self, port, src, dst, now, tag=None):
        """Learn, then forward / flood / filter. Returns (action, list of egress ports)."""
        src, dst = normalise(src), normalise(dst)
        vlan = self.ingress_vlan(port, tag)
        if vlan is None:
            return "DROP (VLAN not allowed on port)", []
        self.table[(vlan, src)] = (port, now)    # 1. LEARN the SOURCE MAC -> ingress port
        self.age(now)

        if classify_mac(dst)["cast"] != "unicast":
            action = f"FLOOD ({classify_mac(dst)['cast']})"   # 2. broadcast / multicast
            out_ports = [p for p in self.ports if p != port]
        elif (vlan, dst) not in self.table:
            action = "FLOOD (unknown unicast)"                # 3. destination not learned yet
            out_ports = [p for p in self.ports if p != port]
        else:
            known_port = self.table[(vlan, dst)][0]
            if known_port == port:
                return f"FILTER (dst is on {port}, same port)", []   # 4. never send back
            action = "FORWARD (known unicast)"                # 5. one port only
            out_ports = [known_port]
        egress = [e for e in (self.egress(p, vlan) for p in out_ports) if e]
        return f"vlan {vlan}: {action}", egress

    def age(self, now):
        """Remove dynamic entries not refreshed within aging_time seconds."""
        for key, (_, last_seen) in list(self.table.items()):
            if now - last_seen > self.aging_time:
                del self.table[key]

    def show_mac_address_table(self):
        lines = ["          Mac Address Table", "-------------------------------------------",
                 "Vlan    Mac Address       Type        Ports", "----    -----------       --------    -----"]
        for (vlan, mac), (port, _) in sorted(self.table.items()):
            lines.append(f"{vlan:>4}    {mac}    DYNAMIC     {port}")
        lines.append(f"Total Mac Addresses for this criterion: {len(self.table)}")
        return "\n".join(lines)


def parse_mac_table(text):
    """Turn 'show mac address-table' text (real IOS XE output) into dicts: the automation angle."""
    row = re.compile(r"^\s*(\d+)\s+([0-9a-f]{4}\.[0-9a-f]{4}\.[0-9a-f]{4})\s+(\S+)\s+(\S+)", re.M)
    return [{"vlan": int(v), "mac": m, "type": t, "port": p} for v, m, t, p in row.findall(text)]


PC_A, PC_D = "00:00:0C:AA:00:0A", "00-00-0C-DD-00-0D"   # both behind Gi1/0/1 (via a hub)
PC_B, PC_C = "0000.0cbb.000b", "02:42:ac:11:00:02"      # PC_C: Docker-style local MAC
ROUTER = "0000.0c99.0001"                                # router-on-a-stick on the trunk


def main():
    print("== 1. MAC address anatomy ==")
    for mac in (PC_A, PC_C, "01:00:5e:00:00:fb", "33:33:00:00:00:01", "FF:FF:FF:FF:FF:FF"):
        c = classify_mac(mac)
        print(f"{mac:<18} -> {c['mac']}  OUI {c['oui']} ({c['vendor']})  "
              f"NIC {c['nic']}  {c['cast']:<9} {c['admin']}")

    sw = Switch("SW1", {
        "Gi1/0/1":  {"mode": "access", "vlan": 10},     # PC-A and PC-D (hub)
        "Gi1/0/2":  {"mode": "access", "vlan": 10},     # PC-B
        "Gi1/0/3":  {"mode": "access", "vlan": 20},     # PC-C
        "Gi1/0/24": {"mode": "trunk", "allowed": {10, 20, 99}, "native": 99},  # to router
    })

    print("\n== 2. What the switch does with each frame ==")
    frames = [
        ("A -> B, table empty",          "Gi1/0/1",  PC_A, PC_B, 0, None),
        ("B -> A, reply",                "Gi1/0/2",  PC_B, PC_A, 1, None),
        ("A -> B again",                 "Gi1/0/1",  PC_A, PC_B, 2, None),
        ("A -> broadcast (ARP request)", "Gi1/0/1",  PC_A, BROADCAST, 3, None),
        ("D -> A, same hub port",        "Gi1/0/1",  PC_D, PC_A, 4, None),
        ("C (VLAN 20) -> A's MAC",       "Gi1/0/3",  PC_C, PC_A, 5, None),
        ("router -> C, tagged 20",       "Gi1/0/24", ROUTER, PC_C, 6, 20),
        ("untagged frame on trunk",      "Gi1/0/24", ROUTER, BROADCAST, 7, None),
        ("tag 30 on trunk",              "Gi1/0/24", ROUTER, PC_A, 8, 30),
        ("A -> mDNS multicast",          "Gi1/0/1",  PC_A, "01:00:5e:00:00:fb", 9, None),
    ]
    for label, port, src, dst, t, tag in frames:
        action, out = sw.receive(port, src, dst, now=t, tag=tag)
        print(f"t={t:<3} {label:<29} in {port:<8} -> {action}")
        for e in out:
            print(f"{'':39}out {e}")
        if action.startswith("vlan") and not out:
            print(f"{'':39}out (none: no other port in that VLAN)")

    print(f"\n== 3. {sw.name}# show mac address-table (t=9) ==")
    print(sw.show_mac_address_table())

    sw.age(now=306)                               # entries last seen at t<=5 are now > 300 s old
    print("\n== 4. After aging (t=306, aging-time 300) ==")
    print(sw.show_mac_address_table())

    print("\n== 5. 802.1Q tag on the wire ==")
    for vlan, pcp in ((10, 0), (20, 5), (4094, 0)):
        tag = dot1q_tag(vlan, pcp)
        tci = int.from_bytes(tag[2:], "big")
        print(f"VLAN {vlan:<4} PCP {pcp}: {tag.hex(' ')}  -> TPID 0x{tag[:2].hex()} "
              f"PCP {tci >> 13} DEI {(tci >> 12) & 1} VID {tci & 0xFFF}")
    try:
        dot1q_tag(4095)
    except ValueError as err:
        print(f"VLAN 4095: ValueError: {err}")

    print("\n== 6. Parse real 'show mac address-table' text ==")
    with open(__file__.replace("l2_switch.py", "show_mac_address_table.txt")) as f:
        for entry in parse_mac_table(f.read()):
            print(entry)


if __name__ == "__main__":
    main()
