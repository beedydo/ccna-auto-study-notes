# T34 · Ansible playbook interpretation: essentials

> Blueprint 5.8 · Full note: [bee/T34-ansible-playbook-interpretation.md](../bee/T34-ansible-playbook-interpretation.md) · Teach-back 2026-11-01

## In one picture
![T34 at a glance: inventory, play structure, modules, variables, control keywords, running and reading a playbook on one page](../assets/T34/00-overview.png)
*Rows follow the concept sections; numbered examples are lines from the playbooks in `labs/T34/`, and red boxes are exam traps.*

## The big idea
- Blueprint 5.8 shows you a playbook and asks what it automates: which devices, how it connects, what it reads or changes, and in what order.
- You know Ansible well from Linux work. The new part is the **network angle**: network modules run on the control node, the connection type decides the protocol, and the module name tells you whether anything is written.
- An analogy: a playbook is a delivery run sheet. `hosts:` is the list of addresses, the connection is the vehicle (SSH van, NETCONF van, HTTPS van), and each task is one parcel, delivered to every address before the next parcel goes out.

## What you need to know

### 1. Inventory and variable files
- The **inventory** answers "which devices?". The lab's `inventory.yml` has two groups: `ios_switches` (sw1, sw2) and `nxos_switches` (n9k1). INI form is `[ios_switches]` followed by one host per line.
- `sw1` is the **inventory name** (`inventory_hostname`); `ansible_host: 10.10.20.11` is the address actually used to connect.
- Variable files are matched **by file name**, with no include needed: `group_vars/ios_switches.yml` applies to that group, `group_vars/all.yml` to every host, and `host_vars/sw2.yml` only to sw2.
- **Host beats group, and specific groups beat `all`.** Lists and dicts are **replaced, not merged**, so sw2's own `vlans` list (10, 99) completely replaces the `all` list (10, 20), and sw2 never gets VLAN 20.

| Variable | Lab value | Meaning |
|---|---|---|
| `ansible_network_os` | `cisco.ios.ios` | which platform (how to parse prompts and CLI) |
| `ansible_connection` | `ansible.netcommon.network_cli` | which transport |
| `ansible_user` / `ansible_password` | env lookups | login; never hard-coded (use `ansible-vault` or env vars) |

![Variable precedence: group_vars/all, then group_vars/<group>, then host_vars, then play vars, then register/set_fact, then -e extra vars which always win](../assets/T34/03-precedence.png)
*Left to right is lowest to highest precedence (a shortened view of the 22-level list); `-e` extra vars always win.*

### 2. Plays, tasks and connection types
- A **playbook** is a YAML list of **plays**. A play maps `hosts:` to a list of **tasks**. A task is **one module call**. To count plays, count the top-level items that have `hosts:`.

![Anatomy: inventory groups feed plays via hosts:, each play holds tasks run top to bottom, and a notify points at a handler](../assets/T34/01-anatomy.png)
*The inventory group decides the devices, `hosts:` picks the group, tasks run in order, and the dotted `notify` fires only on `changed`.*

- Play keywords to recognise: `hosts:` (a group, host, `all` or a pattern like `ios_switches:!sw1`), `gather_facts:`, `vars:`, `connection:`, `tasks:` and `handlers:`.
- **Play vars beat group_vars.** In the lab's `site.yml`, play 2 sets `ansible_connection: ansible.netcommon.httpapi` in `vars:`, so the same switches are reached over RESTCONF instead of SSH.
- **Connection types, explained gently.** Unlike Linux targets, a switch doesn't run Python modules. Instead, **network modules execute on the control node** and talk out to the device using one of these connection plugins:

| `ansible_connection` | Protocol / port | Pairs with |
|---|---|---|
| `network_cli` | the device CLI over SSH, port 22 | `ios_command`, `ios_config`, `ios_facts`, resource modules |
| `netconf` | XML over SSH, port **830** | `netconf_get`, `netconf_config` |
| `httpapi` | HTTP(S) API, port 443 | `restconf_get`/`restconf_config` (with network_os `ansible.netcommon.restconf`), NX-API |
| `local` | none: runs on the control node | `uri`, `template`, controller collections (Meraki, Catalyst Center) |

![Connections: network_cli SSH 22, netconf SSH 830, httpapi HTTPS 443, local plus uri for any REST API; network modules execute on the control node](../assets/T34/02-connections.png)
*All network modules run on the control node and talk out over the connection; only Linux targets get the module copied over and run there.*

- `ansible_connection: local` for **network** devices is deprecated; it stays normal for `uri` calls and localhost plays.
- A task is `name:` plus exactly **one** module key plus its arguments, plus optional keywords (`register`, `when`, `loop`, `notify`, `tags`, `delegate_to`).
- **Indentation is the structure.** Module arguments go one level **under** the module; task keywords line up **with** the module name.
- **FQCN** (fully qualified collection name): `cisco.ios.ios_config` is collection `cisco.ios` plus module `ios_config`. Exam items may show the short form; it is the same module.

### 3. Modules: read or write?
- The module name tells you whether the task reads or changes anything. That is half of any "what does this playbook do" question.

| Module | Read or write | Key args |
|---|---|---|
| `ios_command` | **read**: sends exec (show) commands | `commands:` |
| `ios_config` | **write** to running-config | `lines`, `parents`, `src`, `save_when` |
| `ios_facts` | read; sets `ansible_net_version`, `ansible_net_model`… | `gather_subset` |
| `uri` | either, depending on `method` | `url`, `method`, `headers`, `body` |
| `restconf_get` / `restconf_config` | read / write | `path`, `content`, `method` |
| `netconf_get` / `netconf_config` | read (`<get>`/`<get-config>`) / write (`<edit-config>`) | `filter`; `target`, `content` |
| `template` | writes a file from a Jinja2 `.j2` | `src`, `dest` |
| `debug` | prints only | `msg` or `var` |

- `ios_config` with `parents: "vlan 99"` and `lines: ["name LAB-TEST"]` is the same as typing `conf t`, `vlan 99`, `name LAB-TEST`. It compares with running-config and only sends missing lines, so a rerun is `ok`.
- **`ios_config` doesn't save to startup-config by default.** `save_when` defaults to `never`; the other choices are `always`, `modified` and `changed`.
- `uri` is generic, so you build the full URL, auth and `Accept: application/yang-data+json` yourself, and it runs on the control node (`delegate_to: localhost`). `restconf_get` uses the `httpapi` connection, and its `path` starts **after** `/restconf`.
- `template` writes a file; `ios_config src:` renders the same `.j2` and pushes the lines to the device.
- From the practice-exam review: the package-install modules are `ansible.builtin.yum` / `dnf` for RPM hosts, `apt` for Debian/Ubuntu, and `package` as the OS-agnostic wrapper. Exam cue: "module that installs packages" means **yum** (or apt, or package).

### 4. Variables, register and facts
- `{{ var }}` is Jinja2, filled in on the control node for each host just before the task runs.
- A value that **starts** with `{{` must be quoted (`loop: "{{ vlans }}"`), otherwise YAML reads `{` as the start of a dict.
- **`register: vlan_out`** saves the task's whole result dict for this host. For `ios_command`, `vlan_out.stdout` is a **list** with one string per command, so `vlan_out.stdout[0]` is the `show vlan brief` text.
- On a looped task, the registered variable holds `results`, a list with one entry per item.
- **Facts** are data discovered from the target. On a network play, `gather_facts: false` is usual, and an explicit `ios_facts` task sets the `ansible_net_*` variables. Using `ansible_net_version` without an `ios_facts` task gives an undefined-variable error.
- **Magic variables** are always there: `inventory_hostname`, `groups['ios_switches']` and `hostvars['sw2']['site_role']`.

### 5. Control: loop, when, notify, tags
- **`loop:`** runs the task once per list item, with the current one in `item`. `with_items:` is the older form and reads the same.
- **`when:`** is a **raw Jinja2 expression with no `{{ }}`**, for example `when: site_role == "lab"`. Combined with `loop`, it is checked **per item**, so some items can be skipped while others change.
- **`register` + `when`** is the exam's favourite pair: read state with a `*_command` task, then act only if the output does (or doesn't) contain something.
- **`notify:`** queues a **handler** by its exact name, but only when the task reports **`changed`**.

![Handler decision: ok/skipped never queue; failed stops the host; changed queues once and runs at the end in handlers order](../assets/T34/04-handler-flow.png)
*Only `changed` queues a handler, and it still waits until the end of the tasks section.*

- Queued handlers run **once**, **after all tasks** in the section, in the order listed under `handlers:`. Ten notifies still mean one run.
- No changes on a rerun means no handler. If a later task **fails** on that host, its queued handlers don't run, unless you pass `--force-handlers`.
- A notify name that doesn't match a handler exactly (the lab showed case matters) gives a "handler not found" error and the run fails.
- **`tags:`** label tasks so `--tags vlans` or `--skip-tags restconf` runs a subset.

### 6. Running a playbook and reading the recap
- `ansible-playbook -i inventory.yml site.yml` runs it; `-i` can be dropped if `ansible.cfg` sets the inventory.

| Flag | Effect |
|---|---|
| `--check` | dry run: connects, reports what would change, changes nothing |
| `--diff` | show before and after |
| `--limit sw2` | narrow to hosts that match **both** `hosts:` and the limit (it can't add hosts) |
| `-v` … `-vvvv` | more detail (`-vvv` adds connection detail) |
| `--syntax-check` | parse only, no connection |
| `--list-tasks` / `--list-hosts` | what would run, and where |
| `-e key=value` | extra vars, highest precedence |

![Result states: already matches → ok, made a change → changed, when false → skipping, error → failed, can't connect → unreachable; a changed task becomes ok on the second run](../assets/T34/05-run-states.png)
*The dotted line is idempotency: what was `changed` on run 1 is `ok` on run 2.*

- **`ok`** means "ran and changed nothing", not "passed a test". **`changed`** means a change was made. **`skipped`** means `when` was false. **`failed`** and **`unreachable`** stop that host.
- **Idempotent** means a second run shows `changed=0`. `command`, `shell` and `ios_command` aren't config at all; `command` reports `changed` every time.

### 7. Project structure and the four-pass read
- A **role** is a standard folder layout (`tasks/`, `handlers/`, `templates/`, `defaults/`, `vars/`, `meta/`) that a play pulls in by name; `ansible-galaxy role init <name>` creates it. Roles run before the play's `tasks:`. `defaults/` has the lowest precedence.
- **`ansible.cfg`** sets defaults. The search order, first found wins, is `$ANSIBLE_CONFIG`, then `./ansible.cfg`, then `~/.ansible.cfg`, then `/etc/ansible/ansible.cfg`.
- From the practice-exam review: the first step when starting an Ansible project is to **create a dedicated project directory** holding `ansible.cfg`, the inventory, vars, playbooks and roles, all under Git.
- **Read any exhibit in four passes:**

```
1. Devices  hosts: -> group -> which hosts (check --limit and when too)
2. How      ansible_connection / connection: (group_vars or play vars)
3. What     each module: read or write? what data (lines, src, content, path)?
4. Order    plays in file order; each task finishes on all hosts before the next;
            handlers at the end, once, only where something changed
```

- Applied to the lab's `site.yml`: both plays target sw1 and sw2 (n9k1 is never touched). Play 1 uses SSH CLI to baseline VLANs, hostname and NTP, shuts unused ports on lab switches only, and saves the config if anything changed. Play 2 only **reads** the interface list over RESTCONF.

## Exam traps (the ones that catch people)
- `ios_command` with `configure terminal` lines looks like it configures the switch, but it is read-only. Config goes through `ios_config` or a resource module.
- `ios_config` looks like it saves, but it only changes running-config, because `save_when` defaults to `never`.
- A handler looks like it runs straight after the notifying task, but it runs once at the end, and only if something reported `changed`.
- `when: "{{ x }}"` looks normal, but `when` takes a bare expression with no `{{ }}`.
- `vlan_out.stdout` looks like a string, but it is a list, so use `stdout[0]` for the first command's output.
- `ansible_network_os` looks like it sets the protocol, but it only sets the platform. `ansible_connection` sets the transport, and `network_cli` needs both.
- `--check` looks like `--syntax-check`, but check mode contacts the devices and simulates, while syntax-check only parses the file.
- A module argument at the same level as the module looks harmless, but it gives `conflicting action statements`; a keyword dedented to the `- name` level gives `YAML parsing failed`.

## Quick self-check
<details><summary>Q1. A task has `when: site_role == "lab"`. sw1 is prod, sw2 is lab. What does the run show for sw1?</summary>`skipping`, because the condition is false for sw1.</details>
<details><summary>Q2. Two tasks both notify `Save running config` and both report `changed`. How often does the handler run, and when?</summary>Once, after all tasks in the section finish. Notifications are queued and deduplicated.</details>
<details><summary>Q3. Which connection settings does `restconf_get` need against IOS XE?</summary>`ansible_connection: ansible.netcommon.httpapi` and `ansible_network_os: ansible.netcommon.restconf`.</details>
<details><summary>Q4. `group_vars/all.yml` sets VLANs 10 and 20; `host_vars/sw2.yml` sets 10 and 99. Which VLANs does sw2 get?</summary>10 and 99. host_vars win, and lists are replaced, not merged.</details>
<details><summary>Q5. Which keyword saves a task's output for a later `when:`?</summary>`register`, at the same indentation as the module name.</details>

## Cheat lines to say out loud
- "Four passes: devices, connection, module, order."
- "Command reads, config writes, and config doesn't save unless `save_when` says so."
- "Handlers run once, at the end, only on changed."
- "network_cli is SSH 22, netconf is SSH 830, httpapi is HTTPS, and network modules always run on the control node."
- "Host vars beat group vars, lists replace, and `-e` beats everything."
