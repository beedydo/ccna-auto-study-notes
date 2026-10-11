"""T15 mock NETCONF server: a teaching stand-in for an IOS XE router in candidate mode.

Run:  python3 labs/T15/mock_netconf.py          (listens on 127.0.0.1:8830)
Then: python3 labs/T15/netconf_walkthrough.py   (or: bash labs/T15/run_lab.sh)

What it implements (RFC 6241 + RFC 6242), enough for the exam:
- SSH subsystem "netconf", <hello> capability exchange, ]]>]]> framing (base:1.0)
  and chunked framing (base:1.1) when both peers advertise base:1.1
- Datastores: running, candidate, startup (no :writable-running, like IOS XE with
  `netconf-yang feature candidate-datastore`)
- Operations: get, get-config, edit-config (merge/replace/create/delete/remove,
  default-operation), copy-config, delete-config, lock, unlock, commit,
  discard-changes, validate, close-session, kill-session
- Subtree filters; <ok/>, <data> and <rpc-error> replies
- Data model: ietf-interfaces (config: interfaces, state: interfaces-state)

Needs paramiko (installed with ncclient). Credentials: NETCONF_USER / NETCONF_PASS,
default admin / C1sco12345. Not a real device: real IOS XE replies differ in detail.
"""
import copy
import os
import socket
import sys
import threading
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

import paramiko

HOST, PORT = "127.0.0.1", int(os.environ.get("NETCONF_PORT", "8830"))
USER = os.environ.get("NETCONF_USER", "admin")
PASSWORD = os.environ.get("NETCONF_PASS", "C1sco12345")
VERBOSE = "-v" in sys.argv

BASE = "urn:ietf:params:xml:ns:netconf:base:1.0"
IF = "urn:ietf:params:xml:ns:yang:ietf-interfaces"
IANAIFT = "urn:ietf:params:xml:ns:yang:iana-if-type"
EOM = b"]]>]]>"

CAPABILITIES = [
    "urn:ietf:params:netconf:base:1.0",
    "urn:ietf:params:netconf:base:1.1",
    "urn:ietf:params:netconf:capability:candidate:1.0",
    "urn:ietf:params:netconf:capability:startup:1.0",
    "urn:ietf:params:netconf:capability:validate:1.1",
    "urn:ietf:params:netconf:capability:rollback-on-error:1.0",
    f"{IF}?module=ietf-interfaces&revision=2014-05-08",
    f"{IANAIFT}?module=iana-if-type&revision=2014-05-08",
]


def q(ns, tag):
    return f"{{{ns}}}{tag}"


def intf(name, desc, iftype, enabled):
    el = ET.Element(q(IF, "interface"))
    for tag, text in (("name", name), ("description", desc), ("type", iftype), ("enabled", enabled)):
        ET.SubElement(el, q(IF, tag)).text = text
    return el


def initial_config():
    root = ET.Element("data")
    ifs = ET.SubElement(root, q(IF, "interfaces"))
    ifs.append(intf("GigabitEthernet1", "MANAGEMENT INTERFACE - DON'T TOUCH ME", "ianaift:ethernetCsmacd", "true"))
    ifs.append(intf("GigabitEthernet2", "Network Interface", "ianaift:ethernetCsmacd", "true"))
    ifs.append(intf("GigabitEthernet3", "Network Interface", "ianaift:ethernetCsmacd", "false"))
    ifs.append(intf("Loopback0", "router-id", "ianaift:softwareLoopback", "true"))
    return root


class RpcError(Exception):
    def __init__(self, etype, tag, message, path=None, info=None):
        super().__init__(message)
        self.etype, self.tag, self.message, self.path, self.info = etype, tag, message, path, info

    def xml(self):
        out = f"<rpc-error><error-type>{self.etype}</error-type><error-tag>{self.tag}</error-tag>"
        out += "<error-severity>error</error-severity>"
        if self.path:
            out += f'<error-path xmlns:if="{IF}">{escape(self.path)}</error-path>'
        out += f'<error-message xml:lang="en">{escape(self.message)}</error-message>'
        if self.info:
            out += f"<error-info>{self.info}</error-info>"
        return out + "</rpc-error>"


class Device:
    """Shared state for all sessions: three datastores, locks and session table."""

    def __init__(self):
        self.mutex = threading.RLock()
        self.store = {"running": initial_config()}
        self.store["candidate"] = copy.deepcopy(self.store["running"])
        self.store["startup"] = copy.deepcopy(self.store["running"])
        self.locks = {"running": None, "candidate": None, "startup": None}   # datastore -> session-id
        self.candidate_dirty = False
        self.sessions = {}            # session-id -> Session
        self.next_id = 21

    def state_tree(self):
        """Operational state, derived from RUNNING (never from candidate)."""
        root = ET.Element("data")
        st = ET.SubElement(root, q(IF, "interfaces-state"))
        for i, cfg in enumerate(self.store["running"].find(q(IF, "interfaces"))):
            name = cfg.findtext(q(IF, "name"))
            enabled = cfg.findtext(q(IF, "enabled"), "true") == "true"
            el = ET.SubElement(st, q(IF, "interface"))
            ET.SubElement(el, q(IF, "name")).text = name
            ET.SubElement(el, q(IF, "type")).text = cfg.findtext(q(IF, "type"))
            ET.SubElement(el, q(IF, "admin-status")).text = "up" if enabled else "down"
            ET.SubElement(el, q(IF, "oper-status")).text = "up" if enabled else "down"
            ET.SubElement(el, q(IF, "phys-address")).text = f"00:50:56:bf:{i:02x}:{0x3a + i:02x}"
            stats = ET.SubElement(el, q(IF, "statistics"))
            ET.SubElement(stats, q(IF, "in-octets")).text = str((i + 1) * 1834211 if enabled else 0)
        return root


DEVICE = Device()


# ---------- XML helpers ----------

def serialise(el, parent_ns=None):
    """ElementTree element -> XML string with plain xmlns= declarations (no ns0: prefixes)."""
    ns, _, tag = el.tag[1:].partition("}") if el.tag.startswith("{") else (None, "", el.tag)
    attrs = f' xmlns="{ns}"' if ns and ns != parent_ns else ""
    if tag == "type" and ns == IF:
        attrs += f' xmlns:ianaift="{IANAIFT}"'
    inner = escape(el.text or "") + "".join(serialise(c, ns) for c in el)
    return f"<{tag}{attrs}>{inner}</{tag}>"


def is_leaf(el):
    return len(el) == 0


def subtree(data, flt):
    """RFC 6241 section 6 subtree filtering for one data node `data` matched by filter node `flt`."""
    if len(flt) == 0 and not (flt.text or "").strip():
        return copy.deepcopy(data)                                    # selection node: whole subtree
    matches = [f for f in flt if is_leaf(f) and (f.text or "").strip()]
    others = [f for f in flt if f not in matches]
    for m in matches:                                                 # content match nodes: AND
        if (data.findtext(m.tag) or "").strip() != m.text.strip():
            return None
    out = ET.Element(data.tag)
    if not others:                                                    # only content matches: return all siblings
        for child in data:
            out.append(copy.deepcopy(child))
        return out
    for m in matches:
        out.append(copy.deepcopy(data.find(m.tag)))
    for f in others:                                                  # selection + containment nodes
        for child in data.findall(f.tag):
            got = subtree(child, f)
            if got is not None:
                out.append(got)
    return out if len(out) else None


def apply_filter(root, flt):
    if flt is None:
        return root
    if flt.get("type", "subtree") != "subtree":
        raise RpcError("protocol", "operation-not-supported", "only subtree filters are supported (no :xpath)")
    out = ET.Element("data")
    for f in flt:
        for child in root.findall(f.tag):
            got = subtree(child, f)
            if got is not None:
                out.append(got)
    return out


def datastore_name(parent, what):
    if parent is None or len(parent) == 0:
        raise RpcError("protocol", "missing-element", f"<{what}> is missing a datastore")
    name = parent[0].tag.replace(q(BASE, ""), "")
    if name not in DEVICE.store:
        raise RpcError("protocol", "invalid-value", f"unknown datastore {name}")
    return name


# ---------- edit-config ----------

def find_intf(ifs, name):
    for el in ifs:
        if el.findtext(q(IF, "name")) == name:
            return el
    return None


def check_leaf(name, leaf):
    tag = leaf.tag.replace(q(IF, ""), "")
    if tag == "enabled" and (leaf.text or "").strip() not in ("true", "false"):
        raise RpcError("application", "invalid-value",
                       f'"{(leaf.text or "").strip()}" is not a valid value.',
                       path=f"/if:interfaces/if:interface[if:name='{name}']/if:enabled")
    if tag not in ("name", "description", "type", "enabled"):
        raise RpcError("application", "unknown-element", f"unknown element {tag}",
                       path=f"/if:interfaces/if:interface[if:name='{name}']")


def edit(target_root, config, default_op):
    for top in config:
        if top.tag != q(IF, "interfaces"):
            raise RpcError("application", "unknown-namespace", f"model not supported by this mock: {top.tag}")
        ifs = target_root.find(q(IF, "interfaces"))
        for new in top:
            op = new.get(q(BASE, "operation"), default_op)
            name = (new.findtext(q(IF, "name")) or "").strip()
            path = f"/if:interfaces/if:interface[if:name='{name}']"
            old = find_intf(ifs, name)
            for leaf in new:
                check_leaf(name, leaf)
            if op == "create" and old is not None:
                raise RpcError("application", "data-exists", "object already exists", path=path)
            if op in ("delete", "none") and old is None:
                raise RpcError("application", "data-missing", "object does not exist", path=path)
            if op in ("delete", "remove"):
                if old is not None:
                    ifs.remove(old)
                continue
            clean = copy.deepcopy(new)
            clean.attrib.pop(q(BASE, "operation"), None)
            if op in ("replace", "create") or old is None:
                if old is not None:
                    ifs.remove(old)
                ifs.append(clean)
                continue
            for leaf in clean:                                        # merge: leaf by leaf
                leaf_op = leaf.attrib.pop(q(BASE, "operation"), "merge")
                current = old.find(leaf.tag)
                if leaf_op in ("delete", "remove"):
                    if current is None and leaf_op == "delete":
                        raise RpcError("application", "data-missing", "leaf does not exist", path=path)
                    if current is not None:
                        old.remove(current)
                elif current is None:
                    old.append(leaf)
                else:
                    current.text = leaf.text


# ---------- RPC dispatch ----------

class Session:
    def __init__(self, chan):
        with DEVICE.mutex:
            self.id = DEVICE.next_id
            DEVICE.next_id += 1
            DEVICE.sessions[self.id] = self
        self.chan, self.chunked, self.buf, self.closed = chan, False, b"", False

    # framing
    def send(self, text):
        data = text.encode()
        if self.chunked:
            self.chan.sendall(b"\n#%d\n" % len(data) + data + b"\n##\n")
        else:
            self.chan.sendall(data + EOM)

    def _fill(self):
        more = self.chan.recv(65535)
        if not more:
            raise EOFError
        self.buf += more

    def recv(self):
        if not self.chunked:
            while EOM not in self.buf:
                self._fill()
            msg, _, self.buf = self.buf.partition(EOM)
            return msg.decode()
        msg = b""                                                     # chunked: \n#<size>\n<data> ... \n##\n
        while True:
            while not (self.buf.startswith(b"\n#") and self.buf.find(b"\n", 2) != -1):
                self._fill()
            nl = self.buf.find(b"\n", 2)
            header = self.buf[2:nl]
            if header == b"#":
                self.buf = self.buf[nl + 1:]
                return msg.decode()
            start, size = nl + 1, int(header)
            while len(self.buf) < start + size:
                self._fill()
            msg, self.buf = msg + self.buf[start:start + size], self.buf[start + size:]

    def release(self):
        with DEVICE.mutex:
            for ds, owner in DEVICE.locks.items():
                if owner == self.id:
                    DEVICE.locks[ds] = None
                    if ds == "candidate":                             # RFC 6241 8.3.5.2
                        discard()
            DEVICE.sessions.pop(self.id, None)

    def run(self):
        caps = "".join(f"<capability>{escape(c)}</capability>" for c in CAPABILITIES)
        self.send(f'<?xml version="1.0" encoding="UTF-8"?><hello xmlns="{BASE}"><capabilities>{caps}'
                  f"</capabilities><session-id>{self.id}</session-id></hello>")
        try:
            hello = ET.fromstring(self.recv().strip())
            client_caps = [c.text for c in hello.iter(q(BASE, "capability"))]
            self.chunked = "urn:ietf:params:netconf:base:1.1" in client_caps
            while not self.closed:
                self.handle(self.recv())
        except (EOFError, OSError):
            pass
        finally:
            self.release()
            self.chan.close()

    def handle(self, text):
        rpc = ET.fromstring(text.strip())
        attrs = "".join(f' {k}="{escape(v)}"' for k, v in rpc.attrib.items())
        op = rpc[0]
        name = op.tag.replace(q(BASE, ""), "")
        if VERBOSE:
            print(f"session {self.id}: {name}", file=sys.stderr)
        try:
            with DEVICE.mutex:
                body = getattr(self, "op_" + name.replace("-", "_"), self.op_unknown)(op)
        except RpcError as err:
            body = err.xml()
        except Exception as exc:                                      # mock bug -> still answer
            body = RpcError("application", "operation-failed", f"mock error: {exc!r}").xml()
        self.send(f'<rpc-reply xmlns="{BASE}"{attrs}>{body}</rpc-reply>')

    def locked_by_other(self, ds):
        owner = DEVICE.locks[ds]
        return owner is not None and owner != self.id

    # operations
    def op_unknown(self, op):
        raise RpcError("protocol", "operation-not-supported", f"{op.tag} is not supported")

    def op_get(self, op):
        root = DEVICE.store["running"]
        both = ET.Element("data")
        for part in (root, DEVICE.state_tree()):
            for child in part:
                both.append(copy.deepcopy(child))
        data = apply_filter(both, op.find(q(BASE, "filter")))
        return serialise(data).replace("<data>", f'<data xmlns="{BASE}">', 1)

    def op_get_config(self, op):
        ds = datastore_name(op.find(q(BASE, "source")), "source")
        data = apply_filter(DEVICE.store[ds], op.find(q(BASE, "filter")))
        return serialise(data).replace("<data>", f'<data xmlns="{BASE}">', 1)

    def op_edit_config(self, op):
        ds = datastore_name(op.find(q(BASE, "target")), "target")
        if ds == "running":
            raise RpcError("protocol", "operation-not-supported",
                           "running is not writable (:writable-running not advertised); edit the candidate")
        if self.locked_by_other(ds):
            raise RpcError("protocol", "in-use", f"{ds} is locked by session {DEVICE.locks[ds]}")
        default_op = op.findtext(q(BASE, "default-operation"), "merge")
        work = copy.deepcopy(DEVICE.store[ds])                        # all-or-nothing edit
        config = op.find(q(BASE, "config"))
        edit(work, config if config is not None else op.find("config"), default_op)
        DEVICE.store[ds] = work
        if ds == "candidate":
            DEVICE.candidate_dirty = True
        return "<ok/>"

    def op_copy_config(self, op):
        src = datastore_name(op.find(q(BASE, "source")), "source")
        dst = datastore_name(op.find(q(BASE, "target")), "target")
        if src == dst:
            raise RpcError("protocol", "invalid-value", "source and target are the same datastore")
        if dst == "running":
            raise RpcError("protocol", "operation-not-supported", "running is not writable; use <commit>")
        if self.locked_by_other(dst):
            raise RpcError("protocol", "in-use", f"{dst} is locked by session {DEVICE.locks[dst]}")
        DEVICE.store[dst] = copy.deepcopy(DEVICE.store[src])
        return "<ok/>"

    def op_delete_config(self, op):
        ds = datastore_name(op.find(q(BASE, "target")), "target")
        if ds == "running":
            raise RpcError("protocol", "invalid-value", "the running datastore cannot be deleted")
        DEVICE.store[ds] = ET.Element("data")
        ET.SubElement(DEVICE.store[ds], q(IF, "interfaces"))
        return "<ok/>"

    def op_lock(self, op):
        ds = datastore_name(op.find(q(BASE, "target")), "target")
        owner = DEVICE.locks[ds]
        if owner is not None or (ds == "candidate" and DEVICE.candidate_dirty):
            raise RpcError("protocol", "lock-denied", "Lock failed, lock is already held",
                           info=f"<session-id>{owner or 0}</session-id>")
        DEVICE.locks[ds] = self.id
        return "<ok/>"

    def op_unlock(self, op):
        ds = datastore_name(op.find(q(BASE, "target")), "target")
        if DEVICE.locks[ds] != self.id:
            raise RpcError("protocol", "operation-failed", f"{ds} is not locked by this session")
        DEVICE.locks[ds] = None
        if ds == "candidate":
            discard()                                                 # uncommitted changes are lost
        return "<ok/>"

    def op_validate(self, op):
        datastore_name(op.find(q(BASE, "source")), "source")          # values are checked at edit time
        return "<ok/>"

    def op_commit(self, op):
        for ds in ("running", "candidate"):
            if self.locked_by_other(ds):
                raise RpcError("protocol", "in-use", f"{ds} is locked by session {DEVICE.locks[ds]}",
                               info=f"<session-id>{DEVICE.locks[ds]}</session-id>")
        DEVICE.store["running"] = copy.deepcopy(DEVICE.store["candidate"])
        DEVICE.candidate_dirty = False
        return "<ok/>"

    def op_discard_changes(self, op):
        discard()
        return "<ok/>"

    def op_close_session(self, op):
        self.closed = True
        return "<ok/>"

    def op_kill_session(self, op):
        sid = int(op.findtext(q(BASE, "session-id"), "0"))
        if sid == self.id or sid not in DEVICE.sessions:
            raise RpcError("protocol", "invalid-value", f"cannot kill session {sid}")
        victim = DEVICE.sessions[sid]
        victim.closed = True
        victim.release()
        victim.chan.close()
        return "<ok/>"


def discard():
    DEVICE.store["candidate"] = copy.deepcopy(DEVICE.store["running"])
    DEVICE.candidate_dirty = False


# ---------- SSH layer ----------

class SshServer(paramiko.ServerInterface):
    def __init__(self):
        self.netconf = threading.Event()

    def check_channel_request(self, kind, chanid):
        return paramiko.OPEN_SUCCEEDED if kind == "session" else paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def get_allowed_auths(self, username):
        return "password"

    def check_auth_password(self, username, password):
        ok = username == USER and password == PASSWORD
        return paramiko.AUTH_SUCCESSFUL if ok else paramiko.AUTH_FAILED

    def check_channel_subsystem_request(self, channel, name):
        if name == "netconf":                                         # ssh ... -s netconf
            self.netconf.set()
            return True
        return False


HOST_KEY = paramiko.RSAKey.generate(2048)


def serve_client(sock):
    transport = paramiko.Transport(sock)
    transport.add_server_key(HOST_KEY)
    server = SshServer()
    try:
        transport.start_server(server=server)
        chan = transport.accept(20)
        if chan is None or not server.netconf.wait(10):
            return
        Session(chan).run()
    except (paramiko.SSHException, EOFError, OSError):
        pass
    finally:
        transport.close()


def main():
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind((HOST, PORT))
    listener.listen(10)
    print(f"mock NETCONF server on {HOST}:{PORT} (user {USER})", file=sys.stderr)
    while True:
        sock, _ = listener.accept()
        threading.Thread(target=serve_client, args=(sock,), daemon=True).start()


if __name__ == "__main__":
    main()
