"""T14 reference program: read YANG models the way the exam asks you to.

Run:  bash labs/T14/fetch_models.sh        (once: downloads IETF, Cisco native, OpenConfig models)
      python3 labs/T14/yang_explorer.py

Needs pyang (pip install pyang). It loads the .yang files with pyang's own parser, then:
  1. prints each module header (name, namespace, prefix, imports, revision)
  2. walks campus-vlans.yang and labels every node: kind, rw/ro, type, key, grouping, augment
  3. resolves typedefs down to their built-in type
  4. turns schema nodes into RESTCONF URLs (module:container/list=key/leaf)
  5. reads a RESTCONF JSON reply and maps every value back to its YANG node
  6. optional: GETs one of those URLs from a real device (set RESTCONF_HOST/USER/PASS)
"""
import base64
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from urllib.parse import quote

from pyang import context, repository

HERE = os.path.dirname(os.path.abspath(__file__))
SEARCH_PATH = os.pathsep.join(
    [HERE] + [os.path.join(HERE, "models", d) for d in ("ietf", "xe", "oc")])
DATA_NODES = ("container", "list", "leaf", "leaf-list")


def load(ctx, name):
    """Find a module on the search path and parse it (None if not downloaded)."""
    return ctx.search_module(None, name)


def show_header(module):
    """T14.03: the statements at the top of every module."""
    imports = [f"{i.arg} (prefix {i.search_one('prefix').arg})" for i in module.search("import")]
    revision = module.search_one("revision")
    org = module.search_one("organization")
    print(f"module {module.arg}")
    print(f"  namespace    {module.search_one('namespace').arg}")
    print(f"  prefix       {module.search_one('prefix').arg}")
    print(f"  import       {', '.join(imports) or '-'}")
    print(f"  organization {org.arg.splitlines()[0] if org else '-'}")
    print(f"  revision     {revision.arg if revision else '-'}")


def base_type(type_stmt):
    """T14.05: follow typedefs (vlan-id -> uint16) until a built-in type is reached."""
    chain = [type_stmt.arg]
    while getattr(type_stmt, "i_typedef", None) is not None:
        type_stmt = type_stmt.i_typedef.search_one("type")
        chain.append(type_stmt.arg)
    return " -> ".join(chain)


def describe(node):
    """T14.04-T14.06: what kind of node, config or state, its type and where it came from."""
    rw = "rw" if node.i_config else "ro"
    kind = node.keyword
    notes = []
    if kind == "list":
        notes.append("key=" + ",".join(k.arg for k in node.i_key))
    if kind in ("leaf", "leaf-list"):
        notes.append("type=" + base_type(node.search_one("type")))
    if getattr(node, "i_uses", None):
        notes.append("from grouping " + node.i_uses[0].arg)
    if node.parent.keyword != "module" and node.i_module.i_modulename != node.parent.i_module.i_modulename:
        notes.append("augmented in by " + node.i_module.i_modulename)
    for attr in ("default", "mandatory"):
        sub = node.search_one(attr)
        if sub is not None:
            notes.append(f"{attr}={sub.arg}")
    return rw, kind, "  ".join(notes)


def walk(node, depth=0, only_module=None):
    """Print every data node under `node`, indented like a tree (optionally only one module's nodes)."""
    for child in getattr(node, "i_children", []):        # leaves have no children
        if only_module and child.i_module.i_modulename != only_module:
            continue
        if child.keyword in ("choice", "case"):        # not data nodes: never appear in paths/payloads
            print(f"{'   ' * depth}({child.keyword} {child.arg})")
            walk(child, depth)
            continue
        if child.keyword not in DATA_NODES:
            continue
        rw, kind, notes = describe(child)
        label = f"{'   ' * depth}{child.arg}"
        print(f"{label:<28} {rw}  {kind:<10} {notes}")
        walk(child, depth + 1)


def find(module, names):
    """Return the schema node at names[...] below a module, stepping through choice/case."""
    node = module
    for name in names:
        candidates = list(node.i_children)
        while True:
            hit = [c for c in candidates if c.arg == name and c.keyword in DATA_NODES]
            if hit:
                node = hit[0]
                break
            nested = [g for c in candidates if c.keyword in ("choice", "case") for g in c.i_children]
            if not nested:
                raise KeyError(f"{name} not found under {node.arg}")
            candidates = nested
    return node


def restconf_path(leaf, keys):
    """T14.08: schema node + key values -> RESTCONF data resource path (RFC 8040 3.5.3)."""
    chain, node = [], leaf
    while node.keyword != "module":
        if node.keyword in DATA_NODES:
            chain.insert(0, node)
        node = node.parent
    parts, previous_module = [], None
    for node in chain:
        module = node.i_module.i_modulename
        name = node.arg if module == previous_module else f"{module}:{node.arg}"   # prefix on first node / module change
        if node.keyword == "list":
            name += "=" + ",".join(quote(str(k), safe="") for k in keys[node.arg])  # list=key, '/' -> %2F
        parts.append(name)
        previous_module = module
    return "/restconf/data/" + "/".join(parts)


def map_json(schema_parent, data, indent="  "):
    """T14.06/T14.09: walk a RESTCONF JSON reply and label each value with its YANG node."""
    for member, value in data.items():
        name = member.split(":")[-1]                     # "ietf-ip:ipv4" -> "ipv4" (RFC 7951 member name)
        node = find(schema_parent, [name])
        if node.keyword == "list":
            for entry in value:                          # JSON list instance = array of objects
                keys = ",".join(str(entry[k.arg]) for k in node.i_key)
                print(f"{indent}{member}  (list entry, key={keys})")
                map_json(node, entry, indent + "  ")
        elif node.keyword == "container":
            print(f"{indent}{member}  (container)")
            map_json(node, value, indent + "  ")
        else:
            rw = "rw" if node.i_config else "ro"
            label = f"{indent}{member}"
            print(f"{label:<32} {rw}  {json.dumps(value):<40} {base_type(node.search_one('type'))}")


def live_get(path):
    """Optional: GET the path from a real IOS XE device (DevNet sandbox creds in env vars)."""
    host, user, password = (os.environ.get(v) for v in ("RESTCONF_HOST", "RESTCONF_USER", "RESTCONF_PASS"))
    if not (host and user and password):
        print("  skipped: set RESTCONF_HOST, RESTCONF_USER, RESTCONF_PASS to try a real device")
        return
    request = urllib.request.Request(f"https://{host}{path}", headers={
        "Accept": "application/yang-data+json",
        "Authorization": "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()})
    try:
        with urllib.request.urlopen(request, context=ssl._create_unverified_context(), timeout=10) as resp:
            print(f"  {resp.status} {resp.reason}\n{resp.read().decode()[:600]}")
    except (urllib.error.URLError, OSError) as err:
        print(f"  failed: {err}")


def main():
    ctx = context.Context(repository.FileRepository(SEARCH_PATH, use_env=False))
    names = ["campus-vlans", "ietf-interfaces", "ietf-ip", "Cisco-IOS-XE-native", "openconfig-interfaces"]
    mods = {n: load(ctx, n) for n in names}
    if None in (mods["ietf-interfaces"], mods["ietf-ip"]):
        sys.exit("run labs/T14/fetch_models.sh first")
    ctx.validate()

    print("== 1. Module headers (T14.02, T14.03) ==")
    for name in ("campus-vlans", "ietf-interfaces", "Cisco-IOS-XE-native", "openconfig-interfaces"):
        if mods[name]:
            show_header(mods[name])

    print("\n== 2. Every node in campus-vlans (T14.04-T14.06) ==")
    print(f"{'node':<28} rw  {'kind':<10} notes")
    walk(mods["campus-vlans"])
    print("augment /if:interfaces/if:interface:")
    walk(find(mods["ietf-interfaces"], ["interfaces", "interface"]), 1, only_module="campus-vlans")
    print("\nietf-ip ipv4/address (augmented into ietf-interfaces):")
    walk(find(mods["ietf-interfaces"], ["interfaces", "interface", "ipv4", "address"]), 1)

    print("\n== 3. Typedefs resolved (T14.05) ==")
    for module, names_ in (("campus-vlans", ["vlans", "vlan", "id"]),
                           ("ietf-interfaces", ["interfaces", "interface", "higher-layer-if"]),
                           ("ietf-ip", ["interfaces", "interface", "ipv4", "address", "ip"])):
        root = mods["ietf-interfaces"] if module == "ietf-ip" else mods[module]
        leaf = find(root, names_)
        print(f"  {'/'.join(names_):<45} {base_type(leaf.search_one('type'))}")

    print("\n== 4. Schema node -> RESTCONF URL (T14.08) ==")
    gi1 = {"interface": ["GigabitEthernet1"]}
    targets = [
        (mods["ietf-interfaces"], ["interfaces", "interface", "description"], gi1),
        (mods["ietf-interfaces"], ["interfaces", "interface", "description"], {"interface": ["GigabitEthernet1/0/1"]}),
        (mods["ietf-interfaces"], ["interfaces", "interface", "ipv4", "address", "netmask"],
         {"interface": ["GigabitEthernet1"], "address": ["10.10.20.48"]}),
        (mods["ietf-interfaces"], ["interfaces", "interface", "access-vlan"], gi1),
        (mods["campus-vlans"], ["vlans", "vlan", "name"], {"vlan": [10]}),
    ]
    if mods["Cisco-IOS-XE-native"]:
        targets += [(mods["Cisco-IOS-XE-native"], ["native", "hostname"], {}),
                    (mods["Cisco-IOS-XE-native"], ["native", "interface", "GigabitEthernet", "description"],
                     {"GigabitEthernet": ["1"]})]
    if mods["openconfig-interfaces"]:
        targets.append((mods["openconfig-interfaces"], ["interfaces", "interface", "config", "description"], gi1))
    for root, names_, keys in targets:
        print("  " + restconf_path(find(root, names_), keys))

    print("\n== 5. RESTCONF JSON reply mapped to the model (T14.06, T14.09) ==")
    with open(os.path.join(HERE, "sample-data", "gi1-restconf.json")) as fh:
        reply = json.load(fh)
    map_json(find(mods["ietf-interfaces"], ["interfaces"]), reply)

    print("\n== 6. Same URL against a real device (optional) ==")
    live_get(restconf_path(find(mods["ietf-interfaces"], ["interfaces", "interface", "description"]), gi1))


if __name__ == "__main__":
    main()
