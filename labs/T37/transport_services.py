"""T37 reference program: TCP vs UDP, exam ports, DNS records and NTP, with raw sockets.

Run:  python3 labs/T37/transport_services.py          (local mocks only)
      python3 labs/T37/transport_services.py --live   (also asks pool.ntp.org on UDP 123)

Python stdlib only. mock_services.py starts the local servers in threads.
"""
import socket
import struct
import sys
import time

import mock_services as mock

# name: (port, transport). The exam table for blueprint 6.7, plus the IP services in 6.6.
EXAM_PORTS = {
    "ftp-data": (20, "tcp"), "ftp": (21, "tcp"), "ssh": (22, "tcp"), "telnet": (23, "tcp"),
    "smtp": (25, "tcp"), "domain": (53, "udp+tcp"), "bootps": (67, "udp"), "bootpc": (68, "udp"),
    "tftp": (69, "udp"), "http": (80, "tcp"), "ntp": (123, "udp"), "snmp": (161, "udp"),
    "snmp-trap": (162, "udp"), "https": (443, "tcp"), "syslog": (514, "udp"), "netconf-ssh": (830, "tcp"),
}
RTYPE_NAMES = {mock.A: "A", mock.AAAA: "AAAA", mock.CNAME: "CNAME", mock.MX: "MX", mock.PTR: "PTR"}


def port_table():
    """Print the exam ports and what this OS's /etc/services says (getservbyname)."""
    print(f"{'service':<12}{'port':>5}  {'transport':<9} /etc/services")
    for name, (port, proto) in EXAM_PORTS.items():
        try:
            os_port = socket.getservbyname(name, proto.split("+")[0])
        except OSError:
            os_port = "-"                              # not listed on this OS
        print(f"{name:<12}{port:>5}  {proto:<9} {os_port}")


def tcp_demo():
    """TCP: connect() = 3-way handshake; a closed port answers with RST."""
    with socket.create_connection((mock.HOST, mock.TCP_ECHO), timeout=2) as s:   # SYN, SYN-ACK, ACK
        local, remote = s.getsockname(), s.getpeername()
        print(f"connected {local[0]}:{local[1]} -> {remote[0]}:{remote[1]} (ephemeral src port)")
        s.sendall(b"show version")                      # bytes are acked and delivered in order
        print("reply:", s.recv(1024).decode())
    try:
        socket.create_connection((mock.HOST, 5099), timeout=2)                  # nothing listens here
    except ConnectionRefusedError as err:
        print("closed port 5099:", type(err).__name__, "(peer sent TCP RST)")


def udp_demo():
    """UDP: no connection, no ack. sendto() succeeds even when nobody is listening."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(1)
    sent = s.sendto(b"<189>%SYS-5-CONFIG_I: Configured", (mock.HOST, mock.UDP_ECHO))
    data, addr = s.recvfrom(1024)
    print(f"sent {sent} bytes, reply from {addr[0]}:{addr[1]}: {data.decode()}")
    sent = s.sendto(b"lost?", (mock.HOST, 5099))       # closed port
    print(f"sent {sent} bytes to closed port 5099, sendto() raised nothing")
    try:
        s.recvfrom(1024)
    except socket.timeout:
        print("no reply after 1 s: UDP has no ack, so the app must time out and retry")
    s.close()


def dns_query(name, qtype):
    """Build a raw DNS query (RFC 1035), send it over UDP, return (rcode, answers)."""
    txid = 0x3737
    query = struct.pack("!HHHHHH", txid, 0x0100, 1, 0, 0, 0)    # RD=1, one question
    query += mock.encode_name(name) + struct.pack("!HH", qtype, 1)   # QTYPE, QCLASS=IN
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(2)
    s.sendto(query, (mock.HOST, mock.DNS_PORT))
    reply, _ = s.recvfrom(512)                          # classic UDP DNS limit: 512 bytes
    s.close()
    _, flags, _, ancount, _, _ = struct.unpack("!HHHHHH", reply[:12])
    _, offset = mock.decode_name(reply, 12)
    offset += 4                                         # skip QTYPE + QCLASS of the echoed question
    answers = []
    for _ in range(ancount):
        rname, offset = mock.decode_name(reply, offset)
        rtype, _, ttl, rdlen = struct.unpack("!HHIH", reply[offset:offset + 10])
        offset += 10
        raw = reply[offset:offset + rdlen]
        if rtype == mock.A:
            value = socket.inet_ntop(socket.AF_INET, raw)
        elif rtype == mock.AAAA:
            value = socket.inet_ntop(socket.AF_INET6, raw)
        elif rtype == mock.MX:
            value = f"{struct.unpack('!H', raw[:2])[0]} {mock.decode_name(reply, offset + 2)[0]}"
        else:
            value = mock.decode_name(reply, offset)[0]
        answers.append((rname, RTYPE_NAMES[rtype], ttl, value))
        offset += rdlen
    return flags & 0x000F, answers


def dns_demo():
    lookups = [("csr1.lab.example", mock.A), ("csr1.lab.example", mock.AAAA),
               ("www.lab.example", mock.A), ("lab.example", mock.MX),
               ("48.20.10.10.in-addr.arpa", mock.PTR), ("nope.lab.example", mock.A)]
    for name, qtype in lookups:
        rcode, answers = dns_query(name, qtype)
        print(f"? {name} {RTYPE_NAMES[qtype]}  rcode={rcode}{' NXDOMAIN' if rcode == 3 else ''}")
        for rname, rtype, ttl, value in answers:
            print(f"    {rname:<26} {ttl:<4} IN {rtype:<5} {value}")


def ntp_query(host, port):
    """SNTP client request: 48 bytes, first byte 0x1b = LI 0, version 3, mode 3 (client)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(3)
    s.sendto(b"\x1b" + 47 * b"\0", (host, port))
    data, addr = s.recvfrom(48)
    s.close()
    stratum = data[1]
    refid = socket.inet_ntoa(data[12:16]) if 2 <= stratum <= 15 else data[12:16].decode(errors="replace").strip("\0")
    secs = struct.unpack("!I", data[40:44])[0] - mock.NTP_EPOCH_OFFSET   # transmit timestamp, 1900 -> 1970
    print(f"{addr[0]}:{addr[1]} mode={data[0] & 7} stratum={stratum} refid={refid} "
          f"offset_vs_local={secs - int(time.time()):+d}s")


def main():
    mock.start_all()
    time.sleep(0.2)
    print("== 1. Exam ports ==")
    port_table()
    print("\n== 2. TCP: connection-oriented ==")
    tcp_demo()
    print("\n== 3. UDP: connectionless ==")
    udp_demo()
    print("\n== 4. DNS over UDP (mock on 5053) ==")
    dns_demo()
    print("\n== 5. NTP over UDP (mock on 5123) ==")
    ntp_query(mock.HOST, mock.NTP_PORT)
    if "--live" in sys.argv:
        try:
            ntp_query("pool.ntp.org", 123)
        except OSError as err:
            print("live NTP failed:", err)


if __name__ == "__main__":
    main()
