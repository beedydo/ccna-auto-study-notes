---
id: T44
title: "pyATS + Genie"
owner: Beedy
blueprint: "5.3"
primary_domain: D5
cbt_coverage: "Full"
status: drafted   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-18
teach_back: 2026-10-20
cross_study: 2026-10-23
---

# T44 · pyATS + Genie

> Owner: **Beedy** · Blueprint: **5.3** · CBT coverage: **Full** · Learn by 2026-10-18 · Teach-back 2026-10-20

![T44 at a glance: pyATS/Genie/Unicon stack, testbed YAML, parse vs execute, learn + diff change window, AEtest structure, use cases and tool choice](../assets/T44/00-overview.png)

*Read top to bottom: panel 1 is the system map (your code → pyATS + Genie → Unicon → devices), panel 2 the testbed and the three device calls, panel 3 the before/after diff, panel 4 the AEtest structure and result words, panel 5 the use cases and "which tool" table. Numbers are order or index, red boxes are exam traps, and every code chip comes from `labs/T44/`.*

## TL;DR (teach-back card)

- **Three layers, three jobs.** **pyATS** is Cisco's free Python **test framework** (testbed loader, AEtest harness, `pyats run job` runner). **Genie** (the pyATS Library) **parses** show output into dicts, **learns** whole features (`dev.learn("routing")`) and **diffs** snapshots. **Unicon** **connects** over SSH, Telnet or console and handles prompts.
- **Workflow:** testbed YAML (`os:`, `type:`, `connections:`, credentials as `%ENV{...}`) → `load("testbed.yaml")` → `dev = testbed.devices["csr1"]` → `dev.connect()` → `dev.parse(cmd)` returns a **dict**, `dev.execute(cmd)` returns a **string**, `dev.configure(lines)` pushes config. For change windows: `genie learn routing --output before` → change → `--output after` → `genie diff before after`.
- **AEtest = CommonSetup → Testcase(s) → CommonCleanup.** Sections are marked by **decorators** (`@aetest.subsection`, `@aetest.setup`, `@aetest.test`, `@aetest.cleanup`). Run with `pyats run job job.py --testbed-file testbed.yaml`. Results are PASSED / FAILED / ERRORED / BLOCKED. Use it in CI (T28) against CML labs.
- **Trap:** pyATS **tests** and **validates**; CML **simulates** the network. If CommonSetup breaks, the testcases are **BLOCKED** (not failed) and cleanup still runs. A method without `@aetest.test` **never runs**, so a failing check silently becomes a PASSED report.

## Concepts

The whole note is built around one change window on one IOS XE router, `csr1`. Gi3 is shut. The change gives it an IP, does `no shutdown` and adds a static route. pyATS proves what changed and tests that the result is healthy. **No real router is used.** The device is Unicon's built-in **mock device** (`mock_device_cli`), a local process that replays real-format `show` output saved in `labs/T44/outputs/`. Everything below was run on **Python 3.13.12 with `pyats[full]` 26.9** (pyATS, Genie, Unicon all 26.9), and the output shown is real.

```
labs/T44/
├── outputs/show_version.txt            saved IOS XE 17.9 `show version` (C8000V)
├── outputs/before/*.txt                show ip interface brief + show ip route, before the change
├── outputs/after/*.txt                 the same two commands, after the change
├── make_mock.py                        builds mock/csr1.yaml (fake CLI) from outputs/
├── mock/csr1.yaml                      generated: states csr1_exec (before) → csr1_exec_after
├── testbed.yaml                        offline testbed: csr1 = the mock device
├── testbed-sandbox.yaml                same device on the DevNet Always-On sandbox (not run)
├── offline_parse.py                    Genie parser with NO device: parse(cmd, output=text)
├── change_window.py                    reference program: connect → parse/execute → configure → diff
├── interface_check.py                  AEtest script: CommonSetup → 2 Testcases → CommonCleanup
├── job.py                              Easypy job file for `pyats run job`
├── aetest_blocked_demo.py              CommonSetup error → testcase BLOCKED
├── break_it.py                         5 classic mistakes and the exception each raises
└── run_lab.sh                          runs all of the above end to end
```

**The reference program: `change_window.py`**

```python
"""Pre/post change check with pyATS + Genie: snapshot -> change -> snapshot -> diff.

Runs against the offline testbed (Unicon mock device), so no router is needed:
    CSR1_STATE=csr1_exec python change_window.py
"""
import json

from genie.testbed import load
from genie.utils.diff import Diff

CHANGE = [
    "interface GigabitEthernet3",
    "ip address 10.30.0.1 255.255.255.252",
    "no shutdown",
    "exit",
    "ip route 198.51.100.0 255.255.255.0 10.30.0.2",
]


def snapshot(dev):
    """Structured state: one parser + one learned feature."""
    brief = dev.parse("show ip interface brief")        # dict, from one show command
    routing = dev.learn("routing")                      # Ops object, from several commands
    return brief, routing.info


def down_interfaces(brief):
    return [name for name, intf in brief["interface"].items()
            if intf["status"] != "up"]


def main():
    testbed = load("testbed.yaml")                      # YAML -> Testbed object
    dev = testbed.devices["csr1"]                       # key = device name in YAML
    dev.connect(log_stdout=False, learn_hostname=True)  # Unicon opens the CLI session

    version = dev.parse("show version")
    print("OS version :", version["version"]["version"])
    raw = dev.execute("show ip interface brief")        # plain string, no parsing
    print("execute()  :", type(raw).__name__, f"({len(raw.splitlines())} lines)")

    before_brief, before_routes = snapshot(dev)
    print("down before:", down_interfaces(before_brief))

    dev.configure(CHANGE)                               # config term ... end

    after_brief, after_routes = snapshot(dev)
    print("down after :", down_interfaces(after_brief))

    for label, pre, post in [("show ip interface brief", before_brief, after_brief),
                             ("learn('routing')", before_routes, after_routes)]:
        diff = Diff(pre, post)
        diff.findDiff()
        print(f"\n--- diff: {label} ---\n{diff}")

    with open("snapshot_after.json", "w", encoding="utf-8") as f:
        json.dump(after_brief, f, indent=2)
    dev.disconnect()


if __name__ == "__main__":
    main()
```

**Output** (`cd labs/T44 && CSR1_STATE=csr1_exec python change_window.py`):

```
OS version : 17.9.4a
execute()  : str (5 lines)
down before: ['GigabitEthernet3']
down after : []

--- diff: show ip interface brief ---
 interface:
  GigabitEthernet3:
-  ip_address: unassigned
+  ip_address: 10.30.0.1
-  method: NVRAM
+  method: manual
-  protocol: down
+  protocol: up
-  status: administratively down
+  status: up

--- diff: learn('routing') ---
 vrf:
  default:
   address_family:
    ipv4:
     routes:
+     10.30.0.0/30:
+      active: True
+      next_hop:
+       outgoing_interface:
+        GigabitEthernet3:
+         outgoing_interface: GigabitEthernet3
+      route: 10.30.0.0/30
+      source_protocol: connected
+      source_protocol_codes: C
+     10.30.0.1/32:
+      active: True
+      next_hop:
+       outgoing_interface:
+        GigabitEthernet3:
+         outgoing_interface: GigabitEthernet3
+      route: 10.30.0.1/32
+      source_protocol: local
+      source_protocol_codes: L
+     198.51.100.0/24:
+      active: True
+      metric: 0
+      next_hop:
+       next_hop_list:
+        1:
+         index: 1
+         next_hop: 10.30.0.2
+      route: 198.51.100.0/24
+      route_preference: 1
+      source_protocol: static
+      source_protocol_codes: S
```

- Read the output like a change report:
  - `down before: ['GigabitEthernet3']` → `down after : []`: the check passed.
  - The first diff comes from **one parser**. The second comes from **`learn("routing")`**, which built the routing table model from several commands. It shows exactly the three new routes: the connected /30, the local /32 and the static route.
  - A diff line starting with `-` is the old value and `+` is the new one, the same as a unified diff ([T05](T05-unified-diffs.md)).

### T44.01 · Components

**Must cover:**

- [x] pyATS: Cisco Python test automation framework
- [x] Genie: library of parsers (show output → structured dicts) and device feature models
- [x] Unicon: connection library (SSH/Telnet/console, CLI handling)
- [x] Free to use; works with physical, virtual or CML devices

**Notes:**

- **The problem it solves.** CLI output is text made for humans. To test a network in code you need: a list of devices and how to reach them, a way to log in and run commands, a way to turn text into data, and a test harness that reports pass or fail. pyATS + Genie + Unicon is Cisco's packaged answer to all four.

![pyATS stack architecture: your code (job file, change_window.py, genie CLI) → pyATS framework + Genie library → Unicon → physical, CML or mock csr1 devices](../assets/T44/08-stack-arch.png)

*Read top to bottom. Blue arrows are Python calls (job → Easypy → AEtest, `load("testbed.yaml")`, `parse` / `learn` / `Diff`); grey dashed lines are CLI sessions. Only Unicon touches a device, so swapping a real router for CML or the mock `csr1` changes only `testbed.yaml`.*

| Piece | What it is | In this lab |
|---|---|---|
| **pyATS** (core) | Cisco's Python **test automation framework**: testbed/topology loader, **AEtest** (test harness), **Easypy** (job runner, logs, archive), result objects | `load("testbed.yaml")`, `interface_check.py`, `pyats run job` |
| **Genie** (now called the **pyATS Library**) | Network library on top: thousands of **parsers** (show text → dict), **Ops** feature models (`learn`), **Conf** objects, **Diff**, the `genie` CLI | `dev.parse(...)`, `dev.learn("routing")`, `Diff(...)`, `genie diff` |
| **Unicon** | **Connection** library: SSH / Telnet / console, login and enable prompts, `config term`, pagination (`term length 0`), one plugin per OS | `dev.connect()`, `dev.configure(...)`, `mock_device_cli` |

- **Install:** `pip install pyats` gives the core only. `pip install "pyats[library]"` adds Genie and is Cisco's recommended option. `pip install "pyats[full]"` adds every extra. All three are on public PyPI and **free**.
- **Platform:** Linux and macOS; there is no native Windows support, so use WSL or a container ⚠ verify. The PyPI 26.9 metadata lists Python 3.9 to 3.13. Python 3.14 isn't listed, which is why this lab used Homebrew `python3.13`.
- **Devices:** any device you can reach over CLI: physical, virtual (C8000v, NX-OSv, IOS XRv) or a **CML** topology. There are Unicon plugins and Genie parsers per OS (`iosxe`, `nxos`, `iosxr`, `ios`, `asa`, `junos`, `linux`…). The `os:` key in the testbed picks both.
- **Mock device** (lab trick, not exam content): `mock_device_cli --os iosxe --mock_data_dir mock --state csr1_exec` is a fake CLI from the Unicon package. It answers only the commands listed in `mock/csr1.yaml`, so you can practise the full workflow with no router.

### T44.02 · Testbed

**Must cover:**

- [x] YAML file describing devices to test
- [x] Per device: os (iosxe, nxos), type, connections (protocol: ssh, ip, port)
- [x] credentials (default username/password; can reference env vars)

**Notes:**

- **Testbed file** = a YAML inventory of the **devices under test**: what they are, how to reach them, which credentials to use, and optionally the links between them (`topology:`). It's the pyATS equivalent of an Ansible inventory (T34).
- **The real-device version** (`testbed-sandbox.yaml`, for the DevNet Always-On IOS XE sandbox, **not run** here ⚠ verify host and port):

```yaml
# DevNet Always-On IOS XE sandbox (Catalyst 8000v). NOT run from this repo.
# Host, port and credentials change: check developer.cisco.com/sandbox first.
testbed:
  name: devnet-always-on
  credentials:
    default:
      username: "%ENV{PYATS_USERNAME}"
      password: "%ENV{PYATS_PASSWORD}"

devices:
  csr1:                       # must match the device hostname (or set learn_hostname)
    os: iosxe
    type: router
    platform: cat8k
    connections:
      cli:
        protocol: ssh
        ip: "%ENV{IOSXE_HOST}"
        port: 22
```

| Key | Meaning | Exam note |
|---|---|---|
| `testbed: name:` | label for the testbed | optional |
| `testbed: credentials: default:` | `username` / `password` used by **every** device unless the device overrides them | device-level `credentials:` wins over testbed-level |
| `devices: <name>:` | the device's name = the **key you look up** (`testbed.devices["csr1"]`) | should match the **prompt hostname**, or connect with `learn_hostname=True` |
| `os:` | `iosxe`, `nxos`, `iosxr`, `ios`, `asa`… | **mandatory in practice**: picks the Unicon plugin **and** the Genie parsers |
| `type:` | free-text role: `router`, `switch` | descriptive |
| `platform:` | finer model (`cat8k`, `n9k`) | optional, helps pick platform-specific parsers |
| `connections: <alias>: protocol / ip / port` | how to reach it: `ssh` + IP + `22`, `telnet` + console server + port, or `command:` to spawn a local process (the mock) | several aliases allowed (`cli`, `vty`, `console`); pick with `connect(via="vty")` |

- **Secrets stay out of git.** The pyATS YAML markup `%ENV{VAR}` is replaced with the environment variable at load time. Other forms: `%ASK{}` prompts on load, `%ENC{}` holds an encoded password (`pyats secret encode`), `%INCLUDE{file}` pulls in another YAML. Same idea as [T29](T29-secrets-encryption-data-handling.md): never commit plaintext passwords.
- **The offline testbed used by every run below** (`testbed.yaml`):

```yaml
# Offline testbed: "csr1" is Unicon's mock device (a local process, not a router).
# CSR1_STATE picks which saved output it serves: csr1_exec (before) or csr1_exec_after.
testbed:
  name: t44-offline
  credentials:
    default:
      username: "%ENV{PYATS_USERNAME}"
      password: "%ENV{PYATS_PASSWORD}"

devices:
  csr1:
    os: iosxe
    type: router
    connections:
      defaults:
        class: unicon.Unicon
      cli:
        command: mock_device_cli --os iosxe --mock_data_dir mock --state %ENV{CSR1_STATE} --hostname csr1
```

- `command:` instead of `protocol/ip/port` tells Unicon to **spawn a local process** and talk to its terminal. `%ENV{CSR1_STATE}` chooses which saved output the mock serves: `csr1_exec` (before) or `csr1_exec_after`.
- **Check a testbed without connecting:** `pyats validate testbed testbed.yaml`. Real output (YAML lint warnings trimmed):

```
Testbed Name:
    t44-offline

Testbed Devices:
.
`-- csr1 [iosxe/router]
```

### T44.03 · Workflow

**Must cover:**

- [x] from pyats.topology import loader / from genie.testbed import load
- [x] tb = load("testbed.yaml"); dev = tb.devices["csr1"]
- [x] dev.connect(); dev.parse("show version") → dict
- [x] dev.execute("show run") → raw text; dev.configure("...") pushes config

**Notes:**

- **Two loaders, same file.** `from pyats.topology import loader` then `loader.load("testbed.yaml")` gives plain pyATS device objects. `from genie.testbed import load` then `load("testbed.yaml")` gives **Genie** devices, which add `parse()` and `learn()`. `change_window.py` uses the Genie one. Either returns a `Testbed` object; `testbed.devices` is a dict keyed by device name.
- **Four calls do almost everything** (all in `main()` of `change_window.py`):

| Call | What happens | Returns |
|---|---|---|
| `dev.connect(log_stdout=False, learn_hostname=True)` | Unicon opens the session, logs in, sends `term length 0`, `term width 0`, `no logging console`… | `None` (the session lives on `dev`) |
| `dev.execute("show ip interface brief")` | runs the command, captures the text | **`str`** (here `execute()  : str (5 lines)`) |
| `dev.parse("show ip interface brief")` | runs the command, then the Genie parser for `os: iosxe` + that command | **`dict`** (a Genie `QDict`, a dict subclass) |
| `dev.configure(CHANGE)` | `config term`, sends each line, `end` | the config-mode output as `str` |

![parse vs execute: same command, two return types; parse can also take saved text](../assets/T44/02-parse-vs-execute.png)

*`execute()` stops at the yellow string. `parse()` goes one step further, to the blue dict. The green path is the offline trick: hand `parse()` saved text with `output=` and no device is needed.*

- **Why parse:** with `execute()` you'd regex `GigabitEthernet3\s+(\S+)`. With `parse()` you index a stable key, `brief["interface"]["GigabitEthernet3"]["status"]`, so `down_interfaces()` is one list comprehension. Dict navigation is the same skill as [T06.11](T06-data-formats-parsing.md#t0611--navigating-data).
- **Offline parsing: `offline_parse.py`** (no testbed, no connection):

```python
"""Genie parsers with NO device: feed saved show output to dev.parse(output=...).

    python offline_parse.py outputs/show_version.txt "show version"
"""
import json
import sys

from genie.conf.base import Device

path, command = sys.argv[1], sys.argv[2]
dev = Device("csr1", os="iosxe")                       # os picks the parser family
dev.custom.setdefault("abstraction", {})["order"] = ["os"]

with open(path, encoding="utf-8") as f:
    parsed = dev.parse(command, output=f.read())       # output= skips the CLI call

print(json.dumps(parsed, indent=2))
```

```
$ python offline_parse.py outputs/before/show_ip_interface_brief.txt "show ip interface brief"
{
  "interface": {
    "GigabitEthernet1": {
      "ip_address": "10.10.20.48",
      "interface_is_ok": "YES",
      "method": "NVRAM",
      "status": "up",
      "protocol": "up"
    },
    "GigabitEthernet2": {
      "ip_address": "172.16.12.1",
      "interface_is_ok": "YES",
      "method": "NVRAM",
      "status": "up",
      "protocol": "up"
    },
    "GigabitEthernet3": {
      "ip_address": "unassigned",
      "interface_is_ok": "YES",
      "method": "NVRAM",
      "status": "administratively down",
      "protocol": "down"
    },
  ...
```

```
$ python offline_parse.py outputs/show_version.txt "show version"
{
  "version": {
    "xe_version": "17.09.04a",
    "version_short": "17.9",
    "platform": "Virtual XE",
    "version": "17.9.4a",
    "image_id": "X86_64_LINUX_IOSD-UNIVERSALK9-M",
    "label": "RELEASE SOFTWARE (fc3)",
  ...
```

- The `show version` dict has about 30 keys (`hostname`, `uptime`, `chassis`, `curr_config_register`…). The parser's **schema** fixes the key names, so the same code works on every IOS XE box.
- `dev.custom...["order"] = ["os"]` tells Genie to pick parsers by OS only. That's needed for a bare `Device()` object; a testbed-loaded device sets it up for you.
- **The `genie` CLI does the same without Python:** `genie parse "show ip interface brief" --testbed-file testbed.yaml --devices csr1 --output parsed_before`. Real output:

```
+==============================================================================+
| Genie Parse Summary for csr1                                                 |
+==============================================================================+
|  Connected to csr1                                                           |
|  -  Log: parsed_before/connection_csr1.txt                                   |
|------------------------------------------------------------------------------|
|  Parsed command 'show ip interface brief'                                    |
|  -  Parsed structure: parsed_before/csr1_show-ip-interface-brief_parsed.txt  |
|  -  Device Console:   parsed_before/csr1_show-ip-interface-brief_console.txt |
|------------------------------------------------------------------------------|
```

- Each command gives a `_parsed.txt` (the dict as JSON) and a `_console.txt` (the raw text). Leave out `--output` and the JSON is printed to the screen.

### T44.04 · Learn and diff

**Must cover:**

- [x] dev.learn("ospf") builds a vendor-neutral model of a feature
- [x] genie learn ospf --testbed-file tb.yaml --output before (CLI)
- [x] genie diff before after shows what changed after a change window

**Notes:**

- **parse vs learn:**

| | `parse("show ip route")` | `learn("routing")` |
|---|---|---|
| Input | **one** show command | a **feature** name: `interface`, `routing`, `ospf`, `bgp`, `vlan`, `arp`, `platform`… |
| Runs | that command | **several** commands (for `routing` on IOS XE: `show vrf detail`, `show ip route`, `show ipv6 route`) |
| Output | `dict` shaped like that command, **OS-specific** keys | an **Ops object**; `.info` holds the dict, with the **same structure on every OS** (the "vendor-neutral model") |
| Good for | one fact | whole-feature snapshots to compare |

- **`dev.learn("ospf")`** is the blueprint's example. This lab learns `routing` because the mock has no OSPF; the mechanism is identical. On real devices, feature names come from the Genie models list (⚠ verify the exact list for your release).
- In the program: `snapshot()` returns `dev.learn("routing").info`, and `Diff(pre, post).findDiff()` then `print(diff)` shows only what changed.
- **CLI version of the change window:**

![Change window: learn before → change → learn after → diff → close or roll back](../assets/T44/03-change-window.png)

*Green = snapshots (read-only), yellow = the change, blue = the diff and the happy path, red = roll back when the diff shows something you didn't intend.*

![Animated change window: learn before, configure, learn after, diff, identical](../assets/T44/07-change-window.gif)

*Six frames: state before → `genie learn ... --output before` writes files → `dev.configure(CHANGE)` changes only the router → `--output after` → `genie diff before after` → `genie diff before before` gives `Identical`. It fixes the belief that `genie diff` queries the device: it only compares two folders already on disk.*

```bash
cd labs/T44
export PYATS_USERNAME=lab PYATS_PASSWORD=lab
CSR1_STATE=csr1_exec       genie learn routing --testbed-file testbed.yaml --devices csr1 --output before
CSR1_STATE=csr1_exec_after genie learn routing --testbed-file testbed.yaml --devices csr1 --output after
genie diff before after --output diff
```

```
Learning '['routing']' on devices '['csr1']'

+==============================================================================+
| Genie Learn Summary for device csr1                                          |
+==============================================================================+
|  Connected to csr1                                                           |
|  -   Log: before/connection_csr1.txt                                         |
|------------------------------------------------------------------------------|
|  Learnt feature 'routing'                                                    |
|  -  Ops structure:  before/routing_iosxe_csr1_ops.txt                        |
|  -  Device Console: before/routing_iosxe_csr1_console.txt                    |
|==============================================================================|
```

```
+==============================================================================+
| Genie Diff Summary between directories before/ and after/                    |
+==============================================================================+
|  File: routing_iosxe_csr1_ops.txt                                            |
|   - Diff can be found at diff/diff_routing_iosxe_csr1_ops.txt                |
|------------------------------------------------------------------------------|
```

`diff/diff_routing_iosxe_csr1_ops.txt`:

```
--- before/routing_iosxe_csr1_ops.txt
+++ after/routing_iosxe_csr1_ops.txt
 info:
  vrf:
   default:
    address_family:
     ipv4:
      routes:
+      10.30.0.0/30:
+       active: True
+       next_hop:
+        outgoing_interface:
+         GigabitEthernet3:
+          outgoing_interface: GigabitEthernet3
+       route: 10.30.0.0/30
+       source_protocol: connected
+       source_protocol_codes: C
+      10.30.0.1/32:
+       active: True
+       next_hop:
+        outgoing_interface:
+         GigabitEthernet3:
+          outgoing_interface: GigabitEthernet3
+       route: 10.30.0.1/32
+       source_protocol: local
+       source_protocol_codes: L
+      198.51.100.0/24:
+       active: True
+       metric: 0
+       next_hop:
+        next_hop_list:
+         1:
+          index: 1
+          next_hop: 10.30.0.2
+       route: 198.51.100.0/24
+       route_preference: 1
+       source_protocol: static
+       source_protocol_codes: S
```

- `genie diff before before` → `- Identical`. That's the "nothing changed" answer.
- **Default exclusions.** `genie diff` ignores keys that change all the time: counters, timers, uptime, plus each parser's own `_exclude` list. For `show ip interface brief`, `method` is excluded. Real run, diffing two `genie parse` folders:

| `genie diff parsed_before parsed_after` | `... --no-default-exclusion` |
|---|---|
| `ip_address`, `protocol`, `status` changed | the same **plus** `- method: NVRAM` / `+ method: manual` |

- Add your own exclusions with `--exclude "age" "uptime"`.

### T44.05 · AEtest

**Must cover:**

- [x] AEtest = test harness: CommonSetup → Testcase(s) → CommonCleanup
- [x] Sections decorated with @aetest.setup / @aetest.test / @aetest.cleanup
- [x] pyats run job job.py runs tests and produces reports

**Notes:**

- **AEtest** ("Automation Easy Testing", per the AEtest intro page) is pyATS's test harness, the pyATS counterpart of `unittest` ([T32.03](T32-tdd-python-unit-tests.md#t3203--unittest)). A **testscript** has three container sections, always run in this order:

| Container | Class | Contains | Runs |
|---|---|---|---|
| **CommonSetup** | `class X(aetest.CommonSetup)` | `@aetest.subsection` methods | **first**, once (connect, check prerequisites) |
| **Testcase** | `class X(aetest.Testcase)` (one per check) | optional `@aetest.setup`, one or more `@aetest.test`, optional `@aetest.cleanup` | in **file order** |
| **CommonCleanup** | `class X(aetest.CommonCleanup)` | `@aetest.subsection` methods | **last**, once (disconnect, undo config) |

![AEtest structure of interface_check.py](../assets/T44/04-aetest.png)

*Inside a Testcase: setup → each test → cleanup. The red note is the BLOCKED rule.*

- **The testscript: `interface_check.py`**

```python
"""AEtest script: every interface with an IP address must be up/up.

Run it through the job file:  pyats run job job.py --testbed-file testbed.yaml
"""
import logging

from pyats import aetest

log = logging.getLogger(__name__)


class CommonSetup(aetest.CommonSetup):

    @aetest.subsection
    def connect(self, testbed):
        dev = testbed.devices["csr1"]
        dev.connect(log_stdout=False, learn_hostname=True)
        self.parent.parameters["dev"] = dev          # share with the testcases


class InterfacesUp(aetest.Testcase):

    @aetest.setup
    def collect(self, dev):
        self.brief = dev.parse("show ip interface brief")["interface"]

    @aetest.test
    def addressed_interfaces_up(self):
        bad = [name for name, i in self.brief.items()
               if i["ip_address"] != "unassigned" and i["protocol"] != "up"]
        if bad:
            self.failed(f"down with an IP: {bad}")
        self.passed("every addressed interface is up")

    @aetest.test
    def no_admin_down(self):
        shut = [n for n, i in self.brief.items() if i["status"] == "administratively down"]
        if shut:
            self.failed(f"shutdown: {shut}")

    @aetest.cleanup
    def done(self):
        log.info("checked %d interfaces", len(self.brief))


class DefaultRoute(aetest.Testcase):

    @aetest.test
    def has_default(self, dev):
        routes = dev.learn("routing").info["vrf"]["default"]["address_family"]["ipv4"]["routes"]
        assert "0.0.0.0/0" in routes, "no default route"


class CommonCleanup(aetest.CommonCleanup):

    @aetest.subsection
    def disconnect(self, dev):
        dev.disconnect()


if __name__ == "__main__":                             # standalone: python interface_check.py
    from genie.testbed import load
    aetest.main(testbed=load("testbed.yaml"))
```

- How it hangs together:
  - `testbed` is a **script parameter**. AEtest passes it to any section that has a `testbed` argument.
  - `self.parent.parameters["dev"] = dev` shares the connected device, so later sections just ask for a `dev` argument.
  - `self.failed("reason")` / `self.passed("reason")` set the result explicitly. A bare `assert` that fails also gives **FAILED**; any other exception gives **ERRORED**.
- **Result words** (from the pyATS results docs):

| Result | Means |
|---|---|
| `PASSED` | section ran and nothing failed (also the default if it does nothing) |
| `FAILED` | an assertion was false or `self.failed()` was called |
| `ERRORED` | an unexpected exception (typo, `KeyError`, lost connection) |
| `BLOCKED` | never ran, because something it depends on (CommonSetup) didn't pass |
| `SKIPPED` / `ABORTED` / `PASSX` | `self.skipped()` / run aborted / expected failure |

- **Job file + runner.** A **job** wraps one or more testscripts as **tasks**, with a standard runtime (Easypy): logs, a results summary and a `.zip` **archive**. `job.py`:

```python
"""pyATS job file: `pyats run job job.py --testbed-file testbed.yaml`."""
import os

from pyats.easypy import run

HERE = os.path.dirname(os.path.abspath(__file__))


def main(runtime):
    # runtime.testbed is the --testbed-file, already loaded
    run(testscript=os.path.join(HERE, "interface_check.py"),
        runtime=runtime, taskid="interface_check", testbed=runtime.testbed)
```

- Run it: `pyats run job job.py --testbed-file testbed.yaml --no-mail --archive-dir archive`. `--testbed-file` loads the YAML and hands it to the job as `runtime.testbed`.
- **Before the change** (`CSR1_STATE=csr1_exec`), real output. Exit code 1; reason logged: `Failed reason: shutdown: ['GigabitEthernet3']`:

```
interface_check: interface_check                                          FAILED
|-- common_setup                                                          PASSED
|   `-- connect                                                           PASSED
|-- InterfacesUp                                                          FAILED
|   |-- collect                                                           PASSED
|   |-- addressed_interfaces_up                                           PASSED
|   |-- no_admin_down                                                     FAILED
|   `-- done                                                              PASSED
|-- DefaultRoute                                                          PASSED
|   `-- has_default                                                       PASSED
`-- common_cleanup                                                        PASSED
    `-- disconnect                                                        PASSED
```

```
Overall Stats
    Passed     : 3
    Failed     : 1
    TOTAL      : 4
Success Rate   : 75.00 %
    Archive      : archive/26-10/job_2026Oct10_21_26_49_857503.zip
```

- **After the change** (`CSR1_STATE=csr1_exec_after`): exit code 0:

```
interface_check: interface_check                                          PASSED
|-- common_setup                                                          PASSED
|   `-- connect                                                           PASSED
|-- InterfacesUp                                                          PASSED
|   |-- collect                                                           PASSED
|   |-- addressed_interfaces_up                                           PASSED
|   |-- no_admin_down                                                     PASSED
|   `-- done                                                              PASSED
|-- DefaultRoute                                                          PASSED
|   `-- has_default                                                       PASSED
`-- common_cleanup                                                        PASSED
    `-- disconnect                                                        PASSED
```

- The counts are per **testcase** (common_setup, InterfacesUp, DefaultRoute, common_cleanup = 4), not per `@aetest.test` method. A testcase **rolls up** to the worst result of its sections.
- The archive `.zip` holds `results.json`, `ResultsSummary.xml`, `job.report`, `TaskLog.interface_check` and the device log. The run itself suggests `pyats logs view` to browse it (a log viewer; not run here, ⚠ verify).
- **Standalone run** (no Easypy, no archive): `CSR1_STATE=csr1_exec python interface_check.py`. That uses the `aetest.main(...)` block under the `__main__` guard. Inside a job, the `__main__` block is ignored.
- **BLOCKED demo** (`aetest_blocked_demo.py`: CommonSetup raises `ConnectionError`):

```python
from pyats import aetest


class CommonSetup(aetest.CommonSetup):
    @aetest.subsection
    def connect(self):
        raise ConnectionError("csr1 unreachable")     # not an assert -> ERRORED


class InterfacesUp(aetest.Testcase):
    @aetest.test
    def check(self):
        assert True


class CommonCleanup(aetest.CommonCleanup):
    @aetest.subsection
    def disconnect(self):
        pass


if __name__ == "__main__":
    aetest.main()
```

```
$ python aetest_blocked_demo.py
ConnectionError: csr1 unreachable
...
|-- common_setup                                                         ERRORED
|   `-- connect                                                          ERRORED
|-- InterfacesUp                                                         BLOCKED
`-- common_cleanup                                                        PASSED
    `-- disconnect                                                        PASSED
```

### T44.06 · CML link

**Must cover:**

- [x] CML (Cisco Modeling Labs) provides virtual topologies to run pyATS tests against
- [x] Blueprint 5.3 covers both; Bob covers CML in T25

**Notes:**

- **CML** (Cisco Modeling Labs) = a **network simulator**: you draw a topology of virtual IOS XE / NX-OS / IOS XR nodes and it runs them. Bob's [T25.05](../bob/T25-nso-cisco-modeling-labs.md#t2505--cml) covers it.
- **How they fit:** CML gives you the **devices**; pyATS gives you the **tests**. Point the testbed's `connections:` at the CML node's console or management IP, and the same `interface_check.py` runs unchanged. Only the testbed YAML differs, just as swapping the mock for the sandbox changes only `testbed.yaml`.
- Testbed from CML: the CML side can export a pyATS testbed for a lab ⚠ verify (CML feature, not checked). `pyats create testbed` in 26.9 has no CML source; its creators are `file`, `interactive`, `netbox`, `ansible`, `template` and `topology`.
- **Blueprint 5.3** wording: "simulation and testing tools" names **CML and pyATS** together (paraphrased; check the PDF). Expect "which tool" questions that pair them.

### T44.07 · Use cases

**Must cover:**

- [x] Pre/post-change checks (snapshot → change → snapshot → diff)
- [x] Automated network tests inside a CI/CD pipeline
- [x] Compliance/state verification

**Notes:**

- **1. Pre/post change checks.** This is `change_window.py` and the `genie learn` / `genie diff` run in T44.04. Snapshot the feature, change, snapshot again, diff. Any line you didn't intend (a lost route, a BGP neighbor no longer `Established`) means roll back.
- **2. Network tests inside CI/CD** ([T28.06](T28-ci-cd-devops-principles.md#t2806--infra-cicd)). A pipeline stage runs `pyats run job job.py --testbed-file testbed.yaml`. pyATS exits non-zero when a testcase fails (exit code 1 before the change, 0 after, as above), so the CI tool **stops the pipeline**, and the archive `.zip` is the evidence.

![Network CI/CD with pyATS: lint/unit → pyATS pre-checks on CML → deploy → pyATS post-checks + diff → production or stop](../assets/T44/05-cicd.png)

*Unit tests ([T32](T32-tdd-python-unit-tests.md)) test your Python; the blue pyATS stages test the network. CML or staging takes the change before production does.*

- **3. Compliance / state verification.** Parse → assert on keys. Examples: "every interface with an IP is up/up" (`addressed_interfaces_up`), "a default route exists" (`has_default`), "IOS XE version is 17.9" (`version["version"]["version"]`). You can run it on a schedule, not just around changes.
- **Others you'll see named:** health checks after a reload or upgrade, golden-config checks, traffic tests, and parsing output for documentation or inventory (T06).

### T44.08 · Exam angle

**Must cover:**

- [x] Pick pyATS/Genie for a test or validation scenario (vs CML for simulation)
- [x] Read a short pyATS snippet and say what it does

**Notes:**

![Tool choice: verify/test/diff → pyATS + Genie; virtual lab → CML; transactional multi-vendor config → NSO/Ansible; controller REST → requests/SDK](../assets/T44/06-tool-choice.png)

*Keyword match: "test", "validate", "verify state", "before and after", "parse show output" → pyATS/Genie (blue). "Simulate", "virtual topology", "lab" → CML.*

- **Snippet-reading checklist** (each line of `change_window.py` maps to one of these):

| You see | It does |
|---|---|
| `load("testbed.yaml")` / `loader.load(...)` | reads the testbed YAML into a Testbed object |
| `testbed.devices["csr1"]` | picks one device by its YAML key |
| `dev.connect()` | Unicon opens the CLI session |
| `dev.execute("show ...")` | runs it, returns **raw text** |
| `dev.parse("show ...")` | runs it, returns a **dict** |
| `dev.learn("ospf")` | builds the feature model (Ops object, `.info` = dict) |
| `dev.configure([...])` | enters config mode, sends the lines, exits |
| `Diff(a, b)` then `.findDiff()` | computes the changed keys between two snapshots |
| `class ...(aetest.Testcase)` + `@aetest.test` | one test check inside the AEtest harness |
| `pyats run job job.py --testbed-file tb.yaml` | runs the job, prints the report, writes the archive |

## Exam traps

- **pyATS vs Genie vs Unicon:** pyATS = the **test framework** (testbed, AEtest, Easypy). Genie = the **library** (parse, learn, diff, models). Unicon = the **connection** (SSH/Telnet/console). "Which component turns `show` output into a dictionary?" → **Genie**.
- **pyATS vs CML:** pyATS **tests and validates**; CML **simulates** (virtual devices). pyATS runs *against* CML devices. "Verify that OSPF neighbors are still up after a change" → pyATS. "Build a virtual lab to try the change" → CML.
- **`execute()` returns a string, `parse()` returns a dict.** `dev.execute("show version")["version"]` → `TypeError: string indices must be integers`.
- **`parse` vs `learn`:** `parse` = **one** command, OS-shaped keys. `learn` = a **feature** from several commands, OS-independent structure, an Ops object (`.info`).
- **`genie diff` order and source:** `genie diff before after` compares **two saved folders/files**. It doesn't connect to the device. Output `Identical` = no change. `-` is the old value, `+` the new.
- **Default exclusions hide volatile keys** (counters, uptime, and `method` for `show ip interface brief`). Use `--no-default-exclusion` to see everything.
- **`os:` is what picks the parser.** No `os:` in the testbed → a warning (`OS is unknown`) and the wrong or no Genie parser: in this lab, `parse("show version")` came back as a 4-key dict without the `version` wrapper, and the script crashed with a `TypeError`.
- **Device lookup is by the YAML key, and it's case-sensitive:** `testbed.devices["CSR1"]` → `KeyError: 'CSR1'`.
- **Credentials:** `%ENV{NAME}` reads an environment variable at load time; `%ASK{}` prompts. Plaintext passwords in a committed testbed is the wrong answer.
- **AEtest order is CommonSetup → Testcases (file order) → CommonCleanup.** Inside a Testcase: `@aetest.setup` → each `@aetest.test` → `@aetest.cleanup`. CommonSetup uses `@aetest.subsection`, not `@aetest.setup`.
- **Decorators mark the sections, not names.** Delete `@aetest.test` above `no_admin_down` and that check silently never runs: the before-change job goes from FAILED to **all PASSED** (run in the break-it table).
- **FAILED vs ERRORED vs BLOCKED:** false assert or `self.failed()` → FAILED. Any other exception → ERRORED. CommonSetup didn't pass → testcases **BLOCKED**, and CommonCleanup **still runs**.
- **`pyats run job` needs a job file with `main()`** that calls `run(testscript=...)`. `--testbed-file` (`-t`) is passed to the job. Running `python interface_check.py` directly works only through the `__main__` block, with no archive.

## Examples

**Install** (throwaway venv; pyATS 26.9 supports Python 3.9–3.13 per PyPI, so use 3.13 if your default `python3` is 3.14):

```bash
python3.13 -m venv /tmp/t44-venv
/tmp/t44-venv/bin/pip install --upgrade pip
/tmp/t44-venv/bin/pip install "pyats[full]"
/tmp/t44-venv/bin/pyats version check
```

**Run the whole lab** (from the repo root). Generated files (snapshots, logs, archives) go to `$TMPDIR/t44-run`, not into the repo. Unicon needs a pseudo-terminal even for the mock, so run it from a normal terminal:

```bash
PATH=/tmp/t44-venv/bin:$PATH bash labs/T44/run_lab.sh
```

`run_lab.sh`:

```bash
#!/usr/bin/env bash
# Run the whole T44 lab offline (no router): parse, change window, learn/diff, AEtest job.
# Usage: bash labs/T44/run_lab.sh    (needs pyats[full] on PATH; see README.md)
set -euo pipefail
cd "$(dirname "$0")"

export PYATS_USERNAME="${PYATS_USERNAME:-lab}"     # the mock ignores them; the testbed needs them set
export PYATS_PASSWORD="${PYATS_PASSWORD:-lab}"
WORK="${TMPDIR:-/tmp}/t44-run"                      # all generated files go here, not into the repo
rm -rf "$WORK" && mkdir -p "$WORK"

echo "== 1. build the mock device from outputs/"
python make_mock.py

echo "== 2. offline parse (no device)"
python offline_parse.py outputs/show_version.txt "show version" | head -8

echo "== 3. change window: snapshot -> configure -> snapshot -> Diff"
CSR1_STATE=csr1_exec python change_window.py
mv snapshot_after.json "$WORK/"

echo "== 4. genie CLI: learn before/after, then diff the two folders"
CSR1_STATE=csr1_exec       genie learn routing --testbed-file testbed.yaml --devices csr1 --output "$WORK/before" > /dev/null
CSR1_STATE=csr1_exec_after genie learn routing --testbed-file testbed.yaml --devices csr1 --output "$WORK/after"  > /dev/null
genie diff "$WORK/before" "$WORK/after" --output "$WORK/diff"
cat "$WORK"/diff/diff_routing_iosxe_csr1_ops.txt; echo

echo "== 5. AEtest job, before (expect FAILED) and after (expect PASSED)"
for state in csr1_exec csr1_exec_after; do
  CSR1_STATE="$state" pyats run job job.py --testbed-file testbed.yaml \
    --no-mail --archive-dir "$WORK/archive" > "$WORK/job_$state.log" 2>&1 || true
  echo "-- $state"
  sed -n '/Task Result Details/,/Done!/p' "$WORK/job_$state.log" | sed 's/^.*EASYPY-INFO: //' | sed -n '3,15p'
done
rm -rf __pycache__
echo "== outputs in $WORK"
```

**One piece at a time:**

```bash
cd labs/T44
export PATH=/tmp/t44-venv/bin:$PATH PYATS_USERNAME=lab PYATS_PASSWORD=lab
python make_mock.py                                                  # rebuild mock/csr1.yaml after editing outputs/
python offline_parse.py outputs/show_version.txt "show version"       # parser only, no device
CSR1_STATE=csr1_exec python change_window.py                          # the reference program
CSR1_STATE=csr1_exec python interface_check.py                        # AEtest standalone
CSR1_STATE=csr1_exec pyats run job job.py --testbed-file testbed.yaml --no-mail --archive-dir /tmp/t44-archive
pyats validate testbed testbed.yaml                                   # schema check, no connect
genie parse "show ip interface brief" --testbed-file testbed.yaml --devices csr1 --output /tmp/t44-parsed
```

**In the lab container.** `pyats[full]` is commented out in `labs/requirements.txt`, so install it at run time. Docker wasn't running here, so this is ⚠ not run:

```bash
docker build --tag ccna-auto-lab:latest --file labs/Dockerfile labs/
docker run --rm --interactive --tty --volume "$(pwd)":/work --workdir /work/labs/T44 ccna-auto-lab:latest \
  bash -c 'pip install "pyats[full]" && bash run_lab.sh'
```

**Against a real router** (DevNet Always-On IOS XE sandbox; ⚠ verify host, port and credentials at developer.cisco.com/sandbox first; **not run**). `change_window.py` would push config to a shared sandbox, so run the read-only commands:

```bash
cd labs/T44
export IOSXE_HOST="<sandbox host>" PYATS_USERNAME="<sandbox user>" PYATS_PASSWORD="<sandbox password>"
genie parse "show version" "show ip interface brief" --testbed-file testbed-sandbox.yaml --devices csr1 --output /tmp/t44-sandbox
genie learn interface --testbed-file testbed-sandbox.yaml --devices csr1 --output /tmp/t44-sandbox-learn
```

- The sandbox's real hostname may not be `csr1`. Rename the device key to match the prompt, or add `learn_hostname=True` (as `change_window.py` does).

**Break it on purpose: exceptions.** `break_it.py` runs five classic mistakes, with no device:

```python
"""Break it on purpose: one classic pyATS/Genie mistake per case.

    python break_it.py            # runs every case, prints the exception it raises
No device needed (case 5 loads the testbed but never connects).
"""
import warnings

from genie.conf.base import Device
from genie.testbed import load

warnings.filterwarnings("ignore")


def iosxe():
    dev = Device("csr1", os="iosxe")
    dev.custom.setdefault("abstraction", {})["order"] = ["os"]
    return dev


BRIEF = open("outputs/before/show_ip_interface_brief.txt", encoding="utf-8").read()

CASES = {
    "1 wrong device key": lambda: load("testbed.yaml").devices["CSR1"],
    "2 typo in command": lambda: iosxe().parse("show ip interfaces brief", output=BRIEF),
    "3 empty output": lambda: iosxe().parse("show ip interface brief", output=""),
    "4 ambiguous short form": lambda: iosxe().parse("sh ip int br", output=BRIEF),
    "5 parse before connect": lambda: load("testbed.yaml").devices["csr1"].parse("show version"),
}

for name, case in CASES.items():
    try:
        case()
        print(f"{name}: no error")
    except Exception as e:                     # show the type + first line of the message
        msg = str(e).strip().splitlines()[0]
        print(f"{name}: {type(e).__name__}: {msg}")
```

```
$ CSR1_STATE=csr1_exec python break_it.py
1 wrong device key: KeyError: 'CSR1'
2 typo in command: ParserNotFound: Could not find parser for 'show ip interfaces brief' under {'os': ['iosxe'], 'revision': ['2', '1']}
3 empty output: SchemaEmptyParserError: Parser Output is empty
4 ambiguous short form: Exception: Search for 'sh ip int br' is ambiguous. Please be more specific in your keywords.
5 parse before connect: TypeError: device is not connected, output must be provided.
```

- Case 4: Genie accepts short forms only when they're unambiguous. Here `sh ip int br` matched both `show ip interface brief` and `show ip interface {interface}`.
- Case 5: `parse()` needs a connection **or** `output=`.

**Break it on purpose: edits.** Work on a throwaway copy:

```bash
rm -rf /tmp/t44-break && cp -R labs/T44 /tmp/t44-break && cd /tmp/t44-break
export PATH=/tmp/t44-venv/bin:$PATH PYATS_USERNAME=lab PYATS_PASSWORD=lab CSR1_STATE=csr1_exec PYTHONDONTWRITEBYTECODE=1
```

| Edit (BSD/macOS `sed`; on Linux drop the `''`) | Run | Real result |
|---|---|---|
| `python3 -c 'p="interface_check.py"; s=open(p).read(); open(p,"w").write(s.replace("    @aetest.test\n    def no_admin_down","    def no_admin_down",1))'` | `python interface_check.py` | `no_admin_down` disappears from the report; `InterfacesUp PASSED`, every section PASSED, although Gi3 is still shut |
| `sed -i '' 's/^    os: iosxe$/    # os: iosxe/' testbed.yaml` | `python change_window.py` | `UnsupportedDeviceOsWarning: Device csr1 OS is unknown` → `TypeError: string indices must be integers, not 'str'` at `version["version"]["version"]` |
| `sed -i '' 's/raise ConnectionError("csr1 unreachable")     # not an assert -> ERRORED/assert False, "csr1 unreachable"/' aetest_blocked_demo.py` | `python aetest_blocked_demo.py` | `common_setup FAILED`, `InterfacesUp BLOCKED`, `common_cleanup PASSED`: FAILED or ERRORED, the testcases are blocked either way |

Reset with the `rm -rf ... cp -R ...` line before each row.

**Drill: what does this print?** (answer below; all keys are from the real parser output above)

```python
brief = dev.parse("show ip interface brief")
print([n for n, i in brief["interface"].items() if i["ip_address"] == "unassigned"])
print(type(dev.execute("show ip interface brief")).__name__)
```

<details><summary>Answer</summary>

`['GigabitEthernet3']` (before the change), then `str`.
</details>

## Practice questions

**Q1.** A network engineer needs a script that logs in to 40 IOS XE routers, runs `show ip interface brief`, and gets the result as a Python dictionary without writing any regular expressions. Which tool provides the parsing?

A. Unicon  B. Genie  C. Cisco Modeling Labs  D. AEtest

<details><summary>Answer</summary>

**B.** Genie's parsers turn show output into structured dicts. Unicon only handles the connection, AEtest is the test harness, and CML simulates devices. (T44.01)
</details>

**Q2.** Complete the snippet so it prints the status of GigabitEthernet3 as a string such as `administratively down`:

```python
from genie.testbed import ____(1)____
testbed = load("testbed.yaml")
dev = testbed.____(2)____["csr1"]
dev.connect()
out = dev.____(3)____("show ip interface brief")
print(out["interface"]["GigabitEthernet3"]["status"])
```

A. (1) `loader` (2) `hosts` (3) `execute`
B. (1) `load` (2) `devices` (3) `parse`
C. (1) `load` (2) `devices` (3) `execute`
D. (1) `Testbed` (2) `routers` (3) `learn`

<details><summary>Answer</summary>

**B.** `load` from `genie.testbed`, `testbed.devices[...]`, and `parse()` to get a dict. With `execute()` the indexing fails, because the result is a string. (T44.03)
</details>

**Q3.** Put the steps of a pre/post change validation in order:
1. `genie diff before after`
2. Apply the configuration change
3. `genie learn bgp --testbed-file tb.yaml --output after`
4. `genie learn bgp --testbed-file tb.yaml --output before`

<details><summary>Answer</summary>

**4 → 2 → 3 → 1.** Snapshot, change, snapshot, then compare the two saved folders. (T44.04, T44.07)
</details>

**Q4.** Which statement about `dev.learn("ospf")` is true?

A. It runs exactly one show command and returns raw text
B. It pushes an OSPF configuration to the device
C. It runs several commands and builds a feature model whose structure is the same across supported OSes
D. It compares two OSPF snapshots

<details><summary>Answer</summary>

**C.** `learn` builds an Ops object from multiple parsers. `.info` is a vendor-neutral structure. A is `execute`, B is `configure`, D is `diff`. (T44.04)
</details>

**Q5.** In this AEtest script, `connect()` raises `ConnectionError`. What is the result of `InterfacesUp`, and does `disconnect()` run?

```python
class CommonSetup(aetest.CommonSetup):
    @aetest.subsection
    def connect(self, testbed): ...

class InterfacesUp(aetest.Testcase):
    @aetest.test
    def check(self): ...

class CommonCleanup(aetest.CommonCleanup):
    @aetest.subsection
    def disconnect(self): ...
```

A. FAILED; no  B. ERRORED; no  C. BLOCKED; yes  D. SKIPPED; yes

<details><summary>Answer</summary>

**C.** The setup subsection is ERRORED, so testcases that depend on it are BLOCKED, and CommonCleanup still runs. This is the exact run of `aetest_blocked_demo.py`. (T44.05)
</details>

**Q6.** A team wants each merge request that changes router configs to deploy the change to a virtual topology and then automatically check that every interface and routing adjacency is still healthy before production. Which pair of tools fits? (Choose two.)

A. CML to provide the virtual topology
B. pyATS/Genie to run the checks
C. Webex Bot to push the config
D. Postman to simulate the routers

<details><summary>Answer</summary>

**A, B.** CML simulates the network and pyATS tests it. The pipeline stage would be `pyats run job ...`, and a FAILED result stops the merge. (T44.06, T44.07, T44.08)
</details>

**Q7.** Which testbed snippet keeps the password out of the file and still lets pyATS log in?

A. `password: "${PYATS_PASSWORD}"`
B. `password: "%ENV{PYATS_PASSWORD}"`
C. `password: env(PYATS_PASSWORD)`
D. `password: "{{ PYATS_PASSWORD }}"`

<details><summary>Answer</summary>

**B.** pyATS YAML markup `%ENV{...}` is replaced with the environment variable at load time. A is shell syntax and D is Jinja/Ansible syntax; pyATS treats both as a literal string. (T44.02)
</details>

**Q8.** An engineer removes the `@aetest.test` decorator from one method of a Testcase that was failing, then reruns `pyats run job job.py --testbed-file testbed.yaml`. What happens?

A. The job fails with a syntax error
B. That method still runs, as a normal test
C. That method no longer runs, and the Testcase can now report PASSED
D. The method runs as the Testcase cleanup

<details><summary>Answer</summary>

**C.** AEtest only runs decorated methods. A plain method is just a helper, so the failing check silently disappears from the report (run in the break-it table). (T44.05)
</details>

## Study aids

| Aid | Type | Title | Est. min | Resource |
|---|---|---|---|---|
| T44.1 | Video | Automate and Test Networks with pyATS | 50 | CBT module |

- Skip / low priority: Long demos
- Lab: `labs/T44/` (`bash labs/T44/run_lab.sh`). It covers every concept offline, on a mock router.

## Sources

- Overview image: HTML source `assets/T44/00-overview.html`, rendered to PNG (see `assets/README.md`).
- Animation: `assets/T44/07-change-window-anim.html` → `07-change-window.gif`. Frame values come from the real `genie learn` / `genie diff` runs above.
- Diagrams: `assets/T44/01-stack.mmd`, `02-parse-vs-execute.mmd`, `03-change-window.mmd`, `04-aetest.mmd`, `05-cicd.mmd`, `06-tool-choice.mmd` → `.png`.
- Architecture diagram: HTML source `assets/T44/08-stack-arch.html` (shared kit `assets/_arch/`)
- pyATS Getting Started (install extras, testbed example, loader, connect/execute/configure, AEtest example, job file, `pyats run job --testbed-file`): https://pubhub.devnetcloud.com/media/pyats/docs/getting_started/index.html
- pyATS topology schema (testbed keys, credentials, `%ASK`, `%ENC`): https://pubhub.devnetcloud.com/media/pyats/docs/topology/schema.html
- pyATS YAML markup (`%ENV{}`, `%CALLABLE{}`, `%INCLUDE{}`): https://pubhub.devnetcloud.com/media/pyats/docs/utilities/yaml_markup.html
- AEtest structure (CommonSetup / Testcase / CommonCleanup, subsections, setup/test/cleanup): https://pubhub.devnetcloud.com/media/pyats/docs/aetest/structure.html
- AEtest results (Passed, Failed, Errored, Blocked, Skipped, Aborted, Passx; roll-up): https://pubhub.devnetcloud.com/media/pyats/docs/aetest/results.html
- Easypy job file: https://pubhub.devnetcloud.com/media/pyats/docs/easypy/jobfile.html
- Genie CLI: `genie learn`, `genie diff` (default exclusions, `--no-default-exclusion`), `genie parse`: https://pubhub.devnetcloud.com/media/genie-docs/docs/cli/genie_learn.html , https://pubhub.devnetcloud.com/media/genie-docs/docs/cli/genie_diff.html , https://pubhub.devnetcloud.com/media/genie-docs/docs/cli/genie_parse.html
- pyATS on PyPI (version 26.9, Python classifiers 3.9–3.13): https://pypi.org/project/pyats/
- Cisco 200-901 v1.1 exam topics (5.3): https://learningcontent.cisco.com/documents/marketing/exam-topics/200-901-CCNAAUTO_v.1.1.pdf
- Everything else (return types, `learn("routing")` commands, exclusions, error messages, result trees) comes from running pyATS 26.9 locally, and the output is pasted as-is.

## To verify

- ⚠ verify: Windows support. The Getting Started page lists Linux and macOS only (and an old Python range, 3.7–3.10). PyPI 26.9 classifiers say 3.9–3.13. Python 3.14 wasn't tried; the lab used Homebrew `python3.13`.
- ⚠ verify: the DevNet Always-On IOS XE sandbox host, SSH port, hostname and credentials for `testbed-sandbox.yaml` (they change). Not run against any real device.
- ⚠ verify: the list of `genie learn` feature names for your release (Genie models browser). This lab learned `routing` and `interface` only; `ospf`/`bgp` weren't run (the mock has no OSPF/BGP output).
- ⚠ verify: exporting a pyATS testbed from a CML lab (CML-side feature; not checked).
- ⚠ verify: blueprint 5.3 exact wording (paraphrased in `data/blueprint-map.csv`).
- Not run: the Docker container command (Docker daemon not running), and the sandbox commands (no device by design).
- Lab note: Unicon needs a pseudo-terminal even for the local mock device. Inside the Claude Code Bash sandbox, connections failed with `out of pty devices`, so those runs were done with the sandbox disabled (local process only, no network). A normal terminal is fine.
- The mock device (`mock_device_cli`) is a Unicon test utility, not documented exam content. Its YAML format was taken from the files shipped in `unicon/plugins/tests/mock_data/`.
