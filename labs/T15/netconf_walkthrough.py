"""T15 reference program: one NETCONF session that uses every operation on the exam.

Start the mock device first:  python3 labs/T15/mock_netconf.py
Then in another terminal:     python3 labs/T15/netconf_walkthrough.py
Or both at once:              bash labs/T15/run_lab.sh

Point it at a real IOS XE router with NETCONF_HOST / NETCONF_PORT / NETCONF_USER / NETCONF_PASS.
"""
import os

from lxml import etree
from ncclient import manager
from ncclient.operations import RPCError

HOST = os.environ.get("NETCONF_HOST", "127.0.0.1")
PORT = int(os.environ.get("NETCONF_PORT", "8830"))        # real devices: 830
USER = os.environ.get("NETCONF_USER", "admin")
PASSWORD = os.environ.get("NETCONF_PASS", "C1sco12345")

IF_NS = "urn:ietf:params:xml:ns:yang:ietf-interfaces"

# Subtree filters: an XML template of what to return
GI2_CONFIG = f"""
<interfaces xmlns="{IF_NS}">
  <interface>
    <name>GigabitEthernet2</name>
  </interface>
</interfaces>"""

GI2_STATE = f"""
<interfaces-state xmlns="{IF_NS}">
  <interface>
    <name>GigabitEthernet2</name>
    <oper-status/>
    <statistics><in-octets/></statistics>
  </interface>
</interfaces-state>"""

DESCRIPTIONS = f"""
<interfaces xmlns="{IF_NS}">
  <interface><name/><description/></interface>
</interfaces>"""


def intf_config(name, operation=None, **leaves):
    """Build an <edit-config> <config> payload for one ietf-interfaces entry."""
    op = f' xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="{operation}"' if operation else ""
    body = "".join(f"<{k}>{v}</{k}>" for k, v in leaves.items())
    if "type" in leaves:
        body = body.replace("<type>", '<type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">')
    return (f'<config><interfaces xmlns="{IF_NS}"><interface{op}>'
            f"<name>{name}</name>{body}</interface></interfaces></config>")


def pretty(xml):
    return etree.tostring(etree.fromstring(xml.encode()), pretty_print=True).decode().rstrip()


def rpc(label, call, *args, **kwargs):
    """Run one ncclient call; print <ok/>, the <data>, or the <rpc-error> fields."""
    print(f"\n>>> {label}")
    try:
        reply = call(*args, **kwargs)
    except RPCError as err:                       # ncclient raises on <rpc-error> by default
        print(f"<<< rpc-error  type={err.type}  tag={err.tag}  severity={err.severity}")
        print(f"    message: {err.message}")
        if err.path:
            print(f"    path:    {err.path}")
        if err.info:                              # <error-info> children, e.g. session-id of the lock owner
            info = etree.fromstring(err.info.encode())
            print("    info:   ", " ".join(f"{etree.QName(c).localname}={c.text}" for c in info))
        return err
    if hasattr(reply, "data_xml"):                # get / get-config -> GetReply
        print(pretty(reply.data_xml))
    else:
        print("<<< ok" if reply.ok else f"<<< {reply.xml}")
    return reply


def descriptions(m, source):
    reply = m.get_config(source=source, filter=("subtree", DESCRIPTIONS))
    rows = reply.data.findall(f".//{{{IF_NS}}}interface")
    return {r.findtext(f"{{{IF_NS}}}name"): r.findtext(f"{{{IF_NS}}}description") for r in rows}


def main():
    print("== 1. Connect: SSH, subsystem netconf, <hello> ==")
    m = manager.connect(host=HOST, port=PORT, username=USER, password=PASSWORD,
                        hostkey_verify=False, look_for_keys=False, allow_agent=False)
    caps = m.server_capabilities
    print(f"session-id {m.session_id}; server sent {len(list(caps))} capabilities")
    for short in (":base:1.0", ":base:1.1", ":candidate", ":writable-running", ":startup",
                  ":validate", ":xpath"):
        print(f"  {short:<18} {short in caps}")
    print("  model:", next(c for c in caps if "ietf-interfaces" in c))
    target = "candidate" if ":candidate" in caps else "running"
    print(f"edits will target: {target}")

    print("\n== 2. Read: get-config (config only) vs get (config + state) ==")
    rpc("get-config source=running, filter Gi2", m.get_config, source="running",
        filter=("subtree", GI2_CONFIG))
    rpc("get-config source=running, filter interfaces-state", m.get_config, source="running",
        filter=("subtree", GI2_STATE))
    rpc("get, filter interfaces-state Gi2", m.get, filter=("subtree", GI2_STATE))

    print("\n== 3. Lock the target so nobody else edits it ==")
    rpc(f"lock {target}", m.lock, target=target)
    other = manager.connect(host=HOST, port=PORT, username=USER, password=PASSWORD,
                            hostkey_verify=False, look_for_keys=False, allow_agent=False)
    rpc(f"(session {other.session_id}) lock {target}", other.lock, target=target)
    other.close_session()

    if target == "candidate":
        print("\n== 4. discard-changes: throw away candidate edits ==")
        rpc("edit-config candidate: Gi3 description", m.edit_config, target="candidate",
            config=intf_config("GigabitEthernet3", description="temp test"))
        print("candidate Gi3:", descriptions(m, "candidate")["GigabitEthernet3"])
        rpc("discard-changes", m.discard_changes)
        print("candidate Gi3:", descriptions(m, "candidate")["GigabitEthernet3"])

    print(f"\n== 5. edit-config on {target}: operations merge / create / delete / remove ==")
    rpc("merge Gi2 description (default operation)", m.edit_config, target=target,
        config=intf_config("GigabitEthernet2", description="uplink to core"))
    print("running   Gi2:", descriptions(m, "running")["GigabitEthernet2"])
    print(f"{target:<9} Gi2:", descriptions(m, target)["GigabitEthernet2"])
    rpc("create Loopback100", m.edit_config, target=target,
        config=intf_config("Loopback100", "create", description="mgmt loopback",
                           type="ianaift:softwareLoopback", enabled="true"))
    rpc("create Loopback100 again", m.edit_config, target=target,
        config=intf_config("Loopback100", "create", description="mgmt loopback",
                           type="ianaift:softwareLoopback", enabled="true"))
    rpc("delete Loopback99 (does not exist)", m.edit_config, target=target,
        config=intf_config("Loopback99", "delete"))
    rpc("remove Loopback99 (does not exist)", m.edit_config, target=target,
        config=intf_config("Loopback99", "remove"))
    rpc("merge Gi3 enabled=yes (bad value)", m.edit_config, target=target,
        config=intf_config("GigabitEthernet3", enabled="yes"))
    if ":writable-running" not in caps:
        rpc("edit-config target=running", m.edit_config, target="running",
            config=intf_config("GigabitEthernet2", description="direct"))

    if target == "candidate":
        print("\n== 6. validate, commit, then unlock ==")
        rpc("validate candidate", m.validate, source="candidate")
        rpc("commit", m.commit)
    rpc(f"unlock {target}", m.unlock, target=target)
    print("running:", descriptions(m, "running"))
    rpc("get, filter Loopback100 state", m.get, filter=("subtree", GI2_STATE.replace(
        "GigabitEthernet2", "Loopback100")))

    print("\n== 7. Save and close ==")
    if ":startup" in caps:
        rpc("copy-config running -> startup", m.copy_config, source="running", target="startup")
    rpc("close-session", m.close_session)


if __name__ == "__main__":
    main()
