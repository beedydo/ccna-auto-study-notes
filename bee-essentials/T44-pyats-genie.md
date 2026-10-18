# T44 · pyATS + Genie: essentials

> Blueprint 5.3 · Full note: [bee/T44-pyats-genie.md](../bee/T44-pyats-genie.md) · Teach-back 2026-11-01

## In one picture
![T44 at a glance: pyATS/Genie/Unicon stack, testbed YAML, parse vs execute, learn + diff change window, AEtest structure, use cases and tool choice](../assets/T44/00-overview.png)
*Read top to bottom: the system map (your code, then pyATS + Genie, then Unicon, then the devices), the testbed and device calls, the before/after diff, the AEtest structure and result words, and finally the use cases and "which tool" table. Red boxes are exam traps.*

## The big idea
- Router CLI output is text written for humans. To test a network in code, you need four things: a list of devices and how to reach them, a way to log in and run commands, a way to turn text into data, and a test harness that reports pass or fail.
- **pyATS**, **Genie** and **Unicon** are Cisco's free, packaged answer to all four. Think of it as `pytest` plus an Ansible inventory plus a CLI-to-JSON converter, built for network devices.
- The headline use: take a snapshot of the network before a change, make the change, take another snapshot, and let the tool show exactly what changed.
- On the exam, expect "which component does X", reading a short snippet, the `parse` vs `execute` difference, the AEtest structure, and "pyATS or CML?" questions.

## What you need to know

### 1. The three layers and their jobs
- There are three pieces, and each has one job. Only Unicon ever touches a device.

| Piece | Plain job | What it actually provides |
|---|---|---|
| **pyATS** (the core) | the **test framework** | the testbed loader, the **AEtest** test harness, the **Easypy** job runner (logs, archive), result objects |
| **Genie** (now called the **pyATS Library**) | the **network smarts** | thousands of **parsers** (show text into a dict), **Ops** feature models (`learn`), **Diff**, and the `genie` command-line tool |
| **Unicon** | the **connection** | SSH, Telnet or console login; enable prompts; `config term`; turning off paging (`term length 0`); one plugin per OS |

![pyATS stack architecture: your code → pyATS framework + Genie library → Unicon → physical, CML or mock csr1 devices](../assets/T44/08-stack-arch.png)
*Blue arrows are Python calls and grey dashed lines are CLI sessions. Because only Unicon touches a device, swapping a real router for a CML node or a mock changes only the testbed file.*

- It is **free** and on public PyPI. `pip install pyats` gives the core only; `pip install "pyats[library]"` adds Genie and is Cisco's recommended option; `pip install "pyats[full]"` adds every extra.
- It runs on Linux and macOS. There is no native Windows support, so use WSL or a container (⚠ verify).
- It works with any device you can reach over CLI: physical, virtual (C8000v, NX-OSv, IOS XRv) or a **CML** topology.

### 2. The testbed file: your device inventory
- A **testbed** is a YAML file listing the **devices under test**: what they are, how to reach them, and which credentials to use. It is the pyATS equivalent of an Ansible inventory.

```yaml
testbed:
  credentials:
    default:
      username: "%ENV{PYATS_USERNAME}"
      password: "%ENV{PYATS_PASSWORD}"
devices:
  csr1:
    os: iosxe
    type: router
    connections:
      cli:
        protocol: ssh
        ip: "%ENV{IOSXE_HOST}"
        port: 22
```

- The device name (`csr1`) is the **key you look up** in code. It should match the device's prompt hostname, or you connect with `learn_hostname=True`. The lookup is case-sensitive.
- **`os:`** (`iosxe`, `nxos`, `iosxr`, `ios`, `asa`…) is mandatory in practice. It picks both the **Unicon plugin** and the **Genie parsers**. Without it you get an `OS is unknown` warning and the wrong parser, or none.
- `type:` is a free-text role such as `router` or `switch`. `platform:` (for example `cat8k`) is an optional finer model.
- `connections:` says how to reach the device: `protocol`, `ip` and `port`. You can define several (for example `cli`, `vty`, `console`) and pick one with `connect(via="vty")`.
- Testbed-level `credentials: default:` apply to every device, and device-level credentials override them.
- **Keep secrets out of git** with pyATS YAML markup:
  - `%ENV{VAR}` is replaced by an environment variable when the file loads.
  - `%ASK{}` prompts you at load time.
  - `%ENC{}` holds an encoded password (made with `pyats secret encode`).
  - `%INCLUDE{file}` pulls in another YAML file.
- You can check a testbed without connecting: `pyats validate testbed testbed.yaml`.

### 3. The basic workflow: load, connect, parse, execute, configure
- There are two loaders for the same file. `from pyats.topology import loader` then `loader.load(...)` gives plain pyATS devices. `from genie.testbed import load` then `load(...)` gives **Genie** devices, which add `parse()` and `learn()`.

```python
from genie.testbed import load
testbed = load("testbed.yaml")
dev = testbed.devices["csr1"]
dev.connect()
```
*Read the YAML, pick a device by its key, and let Unicon open the CLI session.*

| Call | What happens | What you get back |
|---|---|---|
| `dev.connect()` | Unicon logs in and sets up the terminal | nothing; the session lives on `dev` |
| `dev.execute("show ip interface brief")` | runs the command and captures the text | a **string** |
| `dev.parse("show ip interface brief")` | runs the command, then the Genie parser for that OS and command | a **dict** |
| `dev.configure([...])` | enters `config term`, sends each line, then `end` | the config-mode output as a string |

![parse vs execute: same command, two return types; parse can also take saved text](../assets/T44/02-parse-vs-execute.png)
*`execute()` stops at a string. `parse()` goes one step further to a dict. The green path shows you can also hand `parse()` saved text with `output=`, with no device at all.*

- Why parse? With a string you would write a regex. With a dict you index a stable key such as `brief["interface"]["GigabitEthernet3"]["status"]`. Each parser has a fixed **schema**, so the same code works on every IOS XE box.
- `parse()` needs either a live connection or `output=` with saved text. Otherwise it raises `TypeError: device is not connected, output must be provided.`
- Short command forms work only if they are unambiguous. `sh ip int br` was rejected as ambiguous in the lab.
- The **`genie` CLI** does the same without Python: `genie parse "show ip interface brief" --testbed-file testbed.yaml --devices csr1 --output parsed_before`.

### 4. Learn and diff: before-and-after snapshots
- **`parse`** works on **one** command. **`learn`** works on a whole **feature** and runs several commands for you.

| | `parse("show ip route")` | `learn("routing")` |
|---|---|---|
| Input | one show command | a feature name: `interface`, `routing`, `ospf`, `bgp`, `vlan`… |
| Runs | that one command | several commands (for `routing` on IOS XE: `show vrf detail`, `show ip route`, `show ipv6 route`) |
| Output | a dict with OS-specific keys | an **Ops object**; `.info` holds a dict with the **same structure on every OS** (the "vendor-neutral model") |
| Good for | one fact | whole-feature snapshots to compare |

- The blueprint's example is `dev.learn("ospf")`. The exact list of feature names depends on your release (⚠ verify).
- The **change window** from the command line:

```bash
genie learn ospf --testbed-file tb.yaml --output before
# ... make the change ...
genie learn ospf --testbed-file tb.yaml --output after
genie diff before after
```
*Snapshot, change, snapshot, compare. `genie diff` only compares two folders already on disk; it never connects to a device.*

![Animated change window: learn before, configure, learn after, diff, identical](../assets/T44/07-change-window.gif)
*Learn before, configure, learn after, diff. The last frame shows `genie diff before before` giving `Identical`, which is the "nothing changed" answer.*

- In the diff, a line starting with `-` is the old value and `+` is the new value, just like a unified diff.
- In Python, the same thing is `Diff(before, after)`, then `.findDiff()`, then `print(diff)`.
- **Default exclusions**: `genie diff` ignores keys that change all the time, such as counters, timers and uptime, plus each parser's own exclude list (for `show ip interface brief`, `method` is excluded). Use `--no-default-exclusion` to see everything, or `--exclude "age" "uptime"` to add your own.

### 5. AEtest: the test harness
- **AEtest** is pyATS's test harness, the network counterpart of Python's `unittest`. A test script has three containers, always run in this order:

| Container | Contains | When it runs |
|---|---|---|
| **CommonSetup** | `@aetest.subsection` methods | first, once (connect, check prerequisites) |
| **Testcase** (one class per check) | optional `@aetest.setup`, one or more `@aetest.test`, optional `@aetest.cleanup` | in file order |
| **CommonCleanup** | `@aetest.subsection` methods | last, once (disconnect, undo config) |

![AEtest structure of interface_check.py](../assets/T44/04-aetest.png)
*Inside a Testcase the order is setup, then each test, then cleanup. The red note is the BLOCKED rule.*

- **Decorators mark the sections, not method names.** A method without `@aetest.test` is just a helper and **never runs**. In the lab, removing that decorator from the failing check made the whole job report PASSED, even though the interface was still shut.
- Results you need to know:

| Result | Meaning |
|---|---|
| `PASSED` | it ran and nothing failed (also the default if it does nothing) |
| `FAILED` | an assertion was false, or `self.failed()` was called |
| `ERRORED` | an unexpected exception (typo, `KeyError`, lost connection) |
| `BLOCKED` | it never ran, because something it depends on (CommonSetup) did not pass |
| `SKIPPED` / `ABORTED` / `PASSX` | `self.skipped()` / the run was aborted / an expected failure |

- If CommonSetup fails or errors, the testcases are **BLOCKED** (not failed), and **CommonCleanup still runs**.
- A Testcase rolls up to the worst result of its sections. The summary counts testcases, not individual test methods.
- **Running it**: a **job file** has a `main(runtime)` function that calls `run(testscript=...)`. You run it with `pyats run job job.py --testbed-file testbed.yaml`. Easypy prints a report and writes a `.zip` **archive** of logs and results.
- You can also run a script directly with `python interface_check.py` through its `__main__` block, but then you get no archive.

### 6. CML, CI/CD and other use cases
- **CML** (Cisco Modeling Labs) is a **network simulator**: it runs virtual IOS XE, NX-OS and IOS XR nodes. Bob covers it in T25.
- **CML gives you the devices; pyATS gives you the tests.** Point the testbed at the CML nodes and the same test script runs unchanged. Blueprint 5.3 names CML and pyATS together as "simulation and testing tools".
- The three main use cases:
  1. **Pre/post change checks**: snapshot, change, snapshot, diff. Any line you did not intend, such as a lost route, means roll back.
  2. **Network tests inside a CI/CD pipeline**: a stage runs `pyats run job ...`. pyATS exits non-zero when a testcase fails, so the pipeline stops, and the archive is your evidence.
  3. **Compliance or state checks**: parse, then assert on keys ("every addressed interface is up", "a default route exists", "IOS XE version is 17.9"). You can run these on a schedule, not only around changes.

![Network CI/CD with pyATS: lint/unit → pyATS pre-checks on CML → deploy → pyATS post-checks + diff → production or stop](../assets/T44/05-cicd.png)
*Unit tests check your Python; the blue pyATS stages check the network. CML or staging takes the change before production does.*

- **Which tool?** "Test", "validate", "verify state", "before and after", "parse show output" point to **pyATS/Genie**. "Simulate", "virtual topology", "lab" point to **CML**.

## Exam traps (the ones that catch people)
- All three names sound like "the pyATS thing", but **pyATS is the test framework, Genie is the library (parse, learn, diff), and Unicon is the connection**. "Which component turns show output into a dictionary?" is **Genie**.
- pyATS and CML both sound like lab tools, but **pyATS tests and validates, while CML simulates**. pyATS runs *against* CML devices.
- `execute()` and `parse()` look the same, but **`execute()` returns a string and `parse()` returns a dict**. `dev.execute("show version")["version"]` fails with a `TypeError`.
- `parse` and `learn` look similar, but **`parse` handles one command with OS-shaped keys, while `learn` builds a whole feature from several commands with an OS-independent structure**.
- `genie diff` looks like it checks the device, but it **only compares two saved folders**. `Identical` means no change.
- A missing method looks like a failure, but **a method without `@aetest.test` silently never runs**, so a failing check can turn into a PASSED report.
- A broken CommonSetup looks like it should fail the tests, but the testcases are **BLOCKED**, and **CommonCleanup still runs**.
- `${VAR}` and `{{ VAR }}` look like valid variables, but pyATS only understands **`%ENV{VAR}`**. The others are treated as literal strings.

## Quick self-check
<details><summary>Q1. Which component handles the SSH login and the enable prompt?</summary>Unicon. It is the connection library; Genie only parses, and pyATS is the framework.</details>
<details><summary>Q2. What type does `dev.parse("show version")` return, and what does `dev.execute("show version")` return?</summary>`parse` returns a dict (a Genie `QDict`); `execute` returns a plain string.</details>
<details><summary>Q3. Put in order: `genie diff before after`, apply the change, learn `--output after`, learn `--output before`.</summary>Learn before, apply the change, learn after, then diff. Snapshot, change, snapshot, compare.</details>
<details><summary>Q4. CommonSetup raises `ConnectionError`. What happens to the testcases and to CommonCleanup?</summary>The testcases are BLOCKED, and CommonCleanup still runs.</details>
<details><summary>Q5. A team wants a virtual topology plus automatic health checks on every merge request. Which two tools?</summary>CML for the virtual topology and pyATS/Genie for the checks.</details>

## Cheat lines to say out loud
- "pyATS tests, Genie understands, Unicon connects."
- "Execute gives me text; parse gives me a dict; learn gives me a whole feature."
- "Learn before, change, learn after, diff: and diff never touches the router."
- "CommonSetup, Testcases, CommonCleanup; no decorator, no test."
- "CML simulates the network, pyATS proves it works."
