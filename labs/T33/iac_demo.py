"""T33 reference program: imperative steps vs declarative desired state.

Two fake switches (sw1, sw2) are JSON files in a state folder. The same goal
(hostname, VLAN 10/20, one NTP server) is reached two ways:

  imperative   run a fixed list of steps in order (like a shell script)
  plan/apply   compare desired state with the real device, change only the delta
               (like Terraform, NSO, Puppet, or Ansible's state-based modules)

Other commands show drift, push vs pull, and mutable vs immutable changes.
Standard library only. Usage: python3 iac_demo.py <command> [device]
"""
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DESIRED_FILE = HERE / "desired_state.json"            # the "code": lives in Git
STATE_DIR = Path(os.environ.get("T33_STATE_DIR", Path(tempfile.gettempdir()) / "t33-state"))
DEVICES_DIR = STATE_DIR / "devices"                    # the "real" devices
STATE_FILE = STATE_DIR / "iac.tfstate.json"            # what the tool last applied
FACTORY = {"hostname": "Switch", "vlans": {"1": "default"}, "ntp_servers": []}


# ---------- device "API" (stand-in for SSH / NETCONF / RESTCONF) ----------
def read_device(name):
    return json.loads((DEVICES_DIR / f"{name}.json").read_text())


def write_device(name, config):
    (DEVICES_DIR / f"{name}.json").write_text(json.dumps(config, indent=2, sort_keys=True))


def load_desired():
    return json.loads(DESIRED_FILE.read_text())


def load_state():
    return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {"serial": 0, "devices": {}}


# ---------- setup ----------
def reset():
    """Factory-reset both switches and forget the state file."""
    DEVICES_DIR.mkdir(parents=True, exist_ok=True)
    for name in load_desired():
        write_device(name, {"instance_id": f"{name}-v1", **FACTORY})
    STATE_FILE.unlink(missing_ok=True)
    print(f"reset: {', '.join(load_desired())} at factory defaults, state file removed")


# ---------- 1. imperative / procedural ----------
STEPS = [                                              # HOW, in order; no idea of "already done"
    ("set_hostname", None),
    ("create_vlan", "10"),
    ("create_vlan", "20"),
    ("add_ntp_server", "10.0.0.1"),
]


def imperative():
    """Run the step list against every device. Run it twice to see it break."""
    desired = load_desired()
    for name, want in desired.items():
        dev, errors = read_device(name), 0
        for step, arg in STEPS:
            if step == "set_hostname":
                dev["hostname"] = want["hostname"]
            elif step == "create_vlan":
                if arg in dev["vlans"]:                # a real API would answer 409 Conflict
                    print(f"  {name}: create_vlan {arg} -> ERROR 409 VLAN {arg} already exists")
                    errors += 1
                    continue
                dev["vlans"][arg] = want["vlans"][arg]
            elif step == "add_ntp_server":
                dev["ntp_servers"].append(arg)         # appends blindly: duplicates on re-run
        write_device(name, dev)
        print(f"{name}: ran {len(STEPS)} steps, {errors} errors, ntp_servers={dev['ntp_servers']}")


# ---------- 2. declarative: diff desired vs actual ----------
def diff(want, have):
    """Return the list of changes needed to turn `have` into `want`."""
    changes = []
    if have["hostname"] != want["hostname"]:
        changes.append(f'~ hostname "{have["hostname"]}" -> "{want["hostname"]}"')
    for vid, vname in want["vlans"].items():
        if vid not in have["vlans"]:
            changes.append(f"+ vlan {vid} name {vname}")
        elif have["vlans"][vid] != vname:
            changes.append(f'~ vlan {vid} name "{have["vlans"][vid]}" -> "{vname}"')
    for vid in have["vlans"]:
        if vid not in want["vlans"] and vid != "1":    # VLAN 1 can't be deleted
            changes.append(f"- vlan {vid}")
    if have["ntp_servers"] != want["ntp_servers"]:
        changes.append(f"~ ntp_servers {have['ntp_servers']} -> {want['ntp_servers']}")
    return changes


def plan(quiet=False):
    """Refresh each device, compare with the desired state, print the delta."""
    desired, state = load_desired(), load_state()
    total = {}
    for name, want in desired.items():
        have = read_device(name)
        last = state["devices"].get(name)
        if last and {k: have[k] for k in last} != last:
            print(f"{name}: DRIFT detected: device no longer matches last apply (serial {state['serial']})")
        changes = diff(want, have)
        total[name] = changes
        if not quiet:
            for line in changes:
                print(f"  {name}: {line}")
    adds = sum(len(c) for c in total.values())
    print(f"Plan: {adds} change(s)." if adds else "No changes. Devices match the desired state.")
    return total


def converge(name, want):
    """Set the device to exactly the desired values (only called when a diff exists)."""
    dev = read_device(name)
    dev.update(hostname=want["hostname"], vlans={"1": "default", **want["vlans"]},
               ntp_servers=list(want["ntp_servers"]))
    write_device(name, dev)


def apply():
    """PUSH: the controller connects out to every device and fixes only what differs."""
    desired, state = load_desired(), load_state()
    changed = 0
    for name, changes in plan(quiet=True).items():
        if changes:
            converge(name, desired[name])
            changed += 1
        dev = read_device(name)
        state["devices"][name] = {k: dev[k] for k in ("hostname", "vlans", "ntp_servers")}
        print(f"push -> {name}: {'changed' if changes else 'ok'} ({len(changes)} change(s))")
    state["serial"] += 1 if changed else 0             # nothing changed -> same serial
    STATE_FILE.write_text(json.dumps(state, indent=2))
    print(f"Apply complete: {changed} changed, {len(desired) - changed} ok. State serial {state['serial']}.")


# ---------- 3. drift, pull agent, immutable replace ----------
def drift(name="sw2"):
    """Someone logs in and changes the device by hand (outside the IaC tool)."""
    dev = read_device(name)
    dev["vlans"]["20"] = "TEMP-FIX"
    dev["ntp_servers"] = ["192.0.2.99"]
    write_device(name, dev)
    print(f"{name}: manual CLI change: vlan 20 renamed TEMP-FIX, ntp server 192.0.2.99")


def agent(name="sw2"):
    """PULL: the agent on the device fetches its own catalog and converges itself."""
    want = load_desired()[name]
    changes = diff(want, read_device(name))
    print(f"{name} agent: fetched catalog from server, {len(changes)} change(s) needed")
    if changes:
        converge(name, want)
        print(f"{name} agent: converged; next check in 30 min")


def replace(name="sw1"):
    """IMMUTABLE: build a brand-new instance from the desired state, then retire the old one."""
    old = read_device(name)
    version = int(old["instance_id"].rsplit("-v", 1)[1]) + 1
    new = {"instance_id": f"{name}-v{version}", **FACTORY}
    new.update(hostname=load_desired()[name]["hostname"],
               vlans={"1": "default", **load_desired()[name]["vlans"]},
               ntp_servers=list(load_desired()[name]["ntp_servers"]))
    write_device(name, new)
    print(f"{name}: replaced {old['instance_id']} -> {new['instance_id']} (old instance destroyed, not patched)")


def show(name="sw1"):
    print(json.dumps(read_device(name), indent=2, sort_keys=True))


COMMANDS = {"reset": reset, "imperative": imperative, "plan": plan, "apply": apply,
            "drift": drift, "agent": agent, "replace": replace, "show": show}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        sys.exit(f"usage: python3 iac_demo.py {{{'|'.join(COMMANDS)}}} [device]")
    COMMANDS[sys.argv[1]](*sys.argv[2:])
