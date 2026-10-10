"""Local stand-ins for the T37 services (Python stdlib only).

Run alone:  python3 labs/T37/mock_services.py      (Ctrl-C to stop)
Or import:  start_all() starts every server in a background thread.

Real services use privileged ports (22, 53, 123, 514). These mocks use
unprivileged ports so no root is needed:

  TCP 5022  echo server       (stand-in for SSH 22)
  UDP 5514  echo server       (stand-in for syslog 514)
  UDP 5053  DNS, zone lab.example (stand-in for DNS 53)
  UDP 5123  NTP, stratum 2    (stand-in for NTP 123)
"""
import socket
import socketserver
import struct
import threading
import time

HOST = "127.0.0.1"
TCP_ECHO, UDP_ECHO, DNS_PORT, NTP_PORT = 5022, 5514, 5053, 5123

# DNS record types (RFC 1035 3.2.2, RFC 3596 for AAAA)
A, CNAME, PTR, MX, AAAA = 1, 5, 12, 15, 28
ZONE = {
    ("csr1.lab.example", A): "10.10.20.48",
    ("csr1.lab.example", AAAA): "2001:db8:10::48",
    ("www.lab.example", CNAME): "csr1.lab.example",
    ("lab.example", MX): (10, "mail.lab.example"),
    ("48.20.10.10.in-addr.arpa", PTR): "csr1.lab.example",
}
NTP_EPOCH_OFFSET = 2208988800          # seconds from 1900-01-01 (NTP) to 1970-01-01 (Unix)


def encode_name(name):
    """'csr1.lab.example' -> b'\\x04csr1\\x03lab\\x07example\\x00' (DNS label format)."""
    out = b""
    for label in name.rstrip(".").split("."):
        out += bytes([len(label)]) + label.encode()
    return out + b"\x00"


def decode_name(data, offset):
    """Read a DNS name at offset (follows compression pointers). Returns (name, next_offset)."""
    labels, jumped, end = [], False, offset
    while True:
        length = data[offset]
        if length & 0xC0 == 0xC0:                      # pointer: 2 bytes, top bits 11
            if not jumped:
                end = offset + 2
            offset, jumped = struct.unpack("!H", data[offset:offset + 2])[0] & 0x3FFF, True
            continue
        if length == 0:
            return ".".join(labels), (end if jumped else offset + 1)
        labels.append(data[offset + 1:offset + 1 + length].decode())
        offset += 1 + length


def rdata(rtype, value):
    if rtype == A:
        return socket.inet_pton(socket.AF_INET, value)
    if rtype == AAAA:
        return socket.inet_pton(socket.AF_INET6, value)
    if rtype == MX:
        return struct.pack("!H", value[0]) + encode_name(value[1])
    return encode_name(value)                          # CNAME, PTR: a domain name


class DNSHandler(socketserver.BaseRequestHandler):
    def handle(self):
        query, sock = self.request
        txid, flags = struct.unpack("!HH", query[:4])
        qname, offset = decode_name(query, 12)
        qtype, _qclass = struct.unpack("!HH", query[offset:offset + 4])
        question = query[12:offset + 4]
        answers = []
        if (qname, qtype) in ZONE:
            answers.append((qname, qtype, ZONE[(qname, qtype)]))
        elif qtype in (A, AAAA) and (qname, CNAME) in ZONE:   # alias: return CNAME + target's record
            target = ZONE[(qname, CNAME)]
            answers.append((qname, CNAME, target))
            if (target, qtype) in ZONE:
                answers.append((target, qtype, ZONE[(target, qtype)]))
        known = any(name == qname for name, _ in ZONE)
        rcode = 0 if answers or known else 3               # 3 = NXDOMAIN (name does not exist)
        rd = flags & 0x0100                                # echo the Recursion Desired bit
        header = struct.pack("!HHHHHH", txid, 0x8400 | rd | rcode, 1, len(answers), 0, 0)  # QR=1, AA=1
        body = b""
        for name, rtype, value in answers:
            data = rdata(rtype, value)
            body += encode_name(name) + struct.pack("!HHIH", rtype, 1, 300, len(data)) + data  # class IN, TTL 300
        sock.sendto(header + question + body, self.client_address)


class NTPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        request, sock = self.request
        if len(request) < 48:
            return
        now = time.time() + NTP_EPOCH_OFFSET
        secs, frac = int(now), int((now % 1) * 2**32)
        reply = struct.pack(
            "!BBbb II 4s QQQQ",
            0x24,                                      # LI=0, VN=4, Mode=4 (server)
            2,                                         # stratum 2 = synced to a stratum-1 server
            6, -20,                                    # poll 2^6 s, precision ~1 us
            0, 0,                                      # root delay, root dispersion
            socket.inet_aton("10.10.20.1"),            # refid = IPv4 of our upstream (stratum >= 2)
            (secs << 32) | frac,                       # reference timestamp
            struct.unpack("!Q", request[40:48])[0],    # origin = client's transmit timestamp
            (secs << 32) | frac,                       # receive timestamp
            (secs << 32) | frac,                       # transmit timestamp
        )
        sock.sendto(reply, self.client_address)


class UDPEcho(socketserver.BaseRequestHandler):
    def handle(self):
        data, sock = self.request
        sock.sendto(b"ack:" + data, self.client_address)


class TCPEcho(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request.recv(1024)
        self.request.sendall(b"echo:" + data)


class ReuseUDP(socketserver.ThreadingUDPServer):
    allow_reuse_address = True


class ReuseTCP(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_all():
    servers = [ReuseTCP((HOST, TCP_ECHO), TCPEcho), ReuseUDP((HOST, UDP_ECHO), UDPEcho),
               ReuseUDP((HOST, DNS_PORT), DNSHandler), ReuseUDP((HOST, NTP_PORT), NTPHandler)]
    for srv in servers:
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    return servers


if __name__ == "__main__":
    start_all()
    print(f"mock services on {HOST}: TCP {TCP_ECHO}, UDP {UDP_ECHO}, DNS {DNS_PORT}, NTP {NTP_PORT}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
