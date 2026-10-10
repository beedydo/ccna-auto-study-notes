"""T15 raw NETCONF over SSH: what ncclient hides. Prints the bytes on the wire.

1. open SSH, request the "netconf" subsystem (same as: ssh -p 830 user@host -s netconf)
2. read the server <hello>, ended by ]]>]]>
3. send our <hello> with base:1.1, so both sides switch to chunked framing
4. send <get-config> as one chunk: \\n#<bytes>\\n<xml>\\n##\\n
5. send <close-session>
Uses paramiko only (installed with ncclient). Same env vars as netconf_walkthrough.py.
"""
import os
import re

import paramiko

HOST = os.environ.get("NETCONF_HOST", "127.0.0.1")
PORT = int(os.environ.get("NETCONF_PORT", "8830"))
USER = os.environ.get("NETCONF_USER", "admin")
PASSWORD = os.environ.get("NETCONF_PASS", "C1sco12345")

CLIENT_HELLO = """<?xml version="1.0" encoding="UTF-8"?>
<hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <capabilities>
    <capability>urn:ietf:params:netconf:base:1.0</capability>
    <capability>urn:ietf:params:netconf:base:1.1</capability>
  </capabilities>
</hello>]]>]]>"""

GET_CONFIG = """<rpc message-id="101" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <get-config>
    <source><running/></source>
    <filter type="subtree">
      <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
        <interface><name>Loopback0</name></interface>
      </interfaces>
    </filter>
  </get-config>
</rpc>"""

CLOSE = '<rpc message-id="102" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><close-session/></rpc>'


def chunk(xml):
    data = xml.encode()
    return b"\n#%d\n" % len(data) + data + b"\n##\n"


def read_until(chan, marker):
    buf = b""
    while marker.encode() not in buf:
        buf += chan.recv(65535)
    return buf.decode()


client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASSWORD, look_for_keys=False, allow_agent=False)
chan = client.get_transport().open_session()
chan.invoke_subsystem("netconf")

hello = read_until(chan, "]]>]]>")
print("<<< server hello (capabilities shortened):")
print(re.sub(r"(<capabilities>).*(</capabilities>)", r"\1...\2", hello))
print("    capabilities:", hello.count("<capability>"), "| base:1.1 offered:", "base:1.1" in hello)

chan.sendall(CLIENT_HELLO.encode())
print("\n>>> client hello sent (base:1.0 + base:1.1), so chunked framing from now on")

chan.sendall(chunk(GET_CONFIG))
print(f"\n>>> get-config sent as one chunk: #{len(GET_CONFIG.encode())}")
print("<<< raw reply bytes:")
print(repr(read_until(chan, "\n##\n")))

chan.sendall(chunk(CLOSE))
print("\n>>> close-session")
print("<<<", repr(read_until(chan, "\n##\n")))
client.close()
