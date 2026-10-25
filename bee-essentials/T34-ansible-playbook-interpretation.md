# T34 · Ansible playbook interpretation: essentials

> Blueprint 5.8: interpret what an Ansible playbook automates · Full note: [bee/T34-ansible-playbook-interpretation.md](../bee/T34-ansible-playbook-interpretation.md)

![T34 at a glance: inventory, play structure, modules, variables, control keywords, running and reading a playbook on one page](../assets/T34/00-overview.png)

*Rows follow the concept sections. Numbered examples are lines from the playbooks in `labs/T34/`. Red boxes are exam traps.*

## 🧭 The big idea

The exam shows you a playbook and asks **what it automates**. Answer four questions, in this order. **Analogy: a playbook is a delivery run sheet.**

| | Question | Where to look | Delivery run sheet analogy |
|---|---|---|---|
| 📋 | **Which devices?** | `hosts:` plus the inventory | `hosts:` is the list of addresses |
| 🚚 | **How does it connect?** | `ansible_connection` decides the protocol (SSH CLI, NETCONF, RESTCONF) | the connection is the vehicle: the SSH van (`network_cli`), the NETCONF van (`netconf`) or the HTTPS van (`httpapi`) |
| 📦 | **What does it read or change?** | the module name on each task tells you read or write | each task is one parcel, delivered to **every** address before the next parcel goes out |
| 🔢 | **In what order?** | plays top to bottom, each task on every host before the next, handlers at the end | a 📞 handler is the "phone the office" note at the end of the run: however many parcels asked for it, you phone **once**, and only if something was actually delivered |

> 💡 You know Ansible from Linux work. The new part is the **network angle**: a switch can't run Python, so network modules **run on the control node** and talk out to the device.

- 🎯 **What the exam asks:** read an exhibit and say which hosts, which protocol, what gets configured or read, and in what order; predict `ok` / `changed` / `skipping`; spot the read-only module dressed up as config. The blueprint verb is "interpret", so it's reading, not writing.

## 🟥 Must know

### 1. 📋 Inventory and variable files: which devices, with which values

> 💡 The **inventory** answers "which devices?". The lab's `inventory.yml`:

```yaml
all:
  children:
    ios_switches:              # group name: what a play's hosts: points at
      hosts:
        sw1:                   # inventory name = inventory_hostname
          ansible_host: 10.10.20.11   # the address actually used to connect
        sw2:
          ansible_host: 10.10.20.12
    nxos_switches:
      hosts:
        n9k1:
          ansible_host: 10.10.20.58
```

- INI form of the same group: `[ios_switches]`, then one host per line.

**Variable files are matched by file name**, with no include needed:

| File | Applies to |
|---|---|
| `group_vars/all.yml` | every host |
| `group_vars/ios_switches.yml` | every host in that group |
| `host_vars/sw2.yml` | only sw2 |

**The three connection variables an exhibit shows** (from `group_vars/ios_switches.yml`):

```yaml
ansible_network_os: cisco.ios.ios                  # WHICH platform: how to parse prompts and CLI
ansible_connection: ansible.netcommon.network_cli  # WHICH transport: SSH to the CLI
ansible_user: "{{ lookup('ansible.builtin.env', 'IOS_USER') }}"          # login from env vars,
ansible_password: "{{ lookup('ansible.builtin.env', 'IOS_PASSWORD') }}"  # never hard-coded
```

> 🎯 **Precedence: host beats group, specific groups beat `all`, `-e` beats everything.**

| ❌ Looks like a merge | ✅ Lists and dicts are replaced, not merged |
|---|---|
| `group_vars/all.yml` sets `vlans` to 10 and 20; `host_vars/sw2.yml` sets 10 and 99 | sw2 gets **10 and 99 only**; VLAN 20 is gone for sw2 |

- Why it matters: two hosts running the **same** playbook can get different config. The host vars drive the difference, not the playbook.

![Variable precedence: group_vars/all, then group_vars/<group>, then host_vars, then play vars, then register/set_fact, then -e extra vars which always win](../assets/T34/03-precedence.png)

*Left to right is lowest to highest precedence (a shortened view of the full list). `-e` extra vars always win.*

### 2. 🧱 Plays, tasks and indentation

| Term | Is |
|---|---|
| **Playbook** | a YAML list of **plays** |
| **Play** | `hosts:` mapped to a list of **tasks** |
| **Task** | **one** module call |

- 🔢 **To count plays**, count the top-level items that have `hosts:`.
- Play 1 of the lab's `site.yml`, annotated:

```yaml
- name: Baseline the IOS XE switches   # a PLAY (top-level item with hosts:)
  hosts: ios_switches                  # the inventory group: sw1 and sw2 (never n9k1)
  gather_facts: false                  # skip the generic setup module (not for switches)

  tasks:
    - name: Read the VLAN table        # a TASK
      cisco.ios.ios_command:           # the one MODULE key (FQCN: collection cisco.ios + module ios_command)
        commands:                      # module ARGUMENT: one level UNDER the module
          - show vlan brief
      register: vlan_out               # task KEYWORD: lines up WITH the module name
      tags: [vlans]
```

| Level | Keywords to recognise |
|---|---|
| Play | `hosts:` (a group, a host, `all` or a pattern like `ios_switches:!sw1`), `gather_facts:`, `vars:`, `connection:`, `tasks:`, `handlers:` |
| Task | `register`, `when`, `loop`, `notify`, `tags`, `delegate_to` |

**📐 Indentation is the structure:**

| ✅ Rule | ❌ Break it and you get |
|---|---|
| module arguments go one level **under** the module | an argument at the module's level → `conflicting action statements` (Ansible sees two "modules") |
| task keywords line up **with** the module name | a keyword dedented to the `- name` dash level → `YAML parsing failed` |

- 🏷️ **FQCN** (fully qualified collection name): `cisco.ios.ios_config` = collection `cisco.ios` + module `ios_config`. Exam items may show the short form `ios_config`; it's the same module.

![Anatomy: inventory groups feed plays via hosts:, each play holds tasks run top to bottom, and a notify points at a handler](../assets/T34/01-anatomy.png)

*The inventory group decides the devices, `hosts:` picks the group, tasks run in order, and the dotted `notify` fires only on `changed`.*

### 3. 🚚 Connection types: network modules run on the control node

| 🐧 Linux target | 🔀 Network device |
|---|---|
| Ansible copies the module over and runs it there | a switch doesn't run Python, so **network modules execute on the control node** and talk out over a connection plugin |

> 🚚 Vehicle analogy: the connection is the van. The parcel (module) never leaves the depot; the van carries the conversation.

- `ansible_connection` picks the van; `ansible_network_os` says which platform is on the other end. `network_cli` needs **both**.

| `ansible_connection` | Protocol / port | Pairs with |
|---|---|---|
| `network_cli` | the device CLI over SSH, port 22 | `ios_command`, `ios_config`, `ios_facts`, resource modules |
| `netconf` | XML over SSH, port **830** | `netconf_get`, `netconf_config` |
| `httpapi` | HTTP(S) API, port 443 | `restconf_get` / `restconf_config` (with network_os `ansible.netcommon.restconf`), NX-API |
| `local` | none: runs on the control node | `uri`, `template`, controller collections (Meraki, Catalyst Center) |

**Play vars beat group_vars.** Play 2 of `site.yml` reaches the **same switches** over RESTCONF instead of SSH:

```yaml
- name: Audit interfaces over RESTCONF
  hosts: ios_switches
  gather_facts: false
  vars:
    ansible_connection: ansible.netcommon.httpapi   # overrides network_cli from group_vars
    ansible_network_os: ansible.netcommon.restconf  # required by restconf_get
    ansible_httpapi_use_ssl: true
    ansible_httpapi_validate_certs: false
```

- ⚠️ `ansible_connection: local` for **network devices** is deprecated; it stays normal for `uri` calls and localhost plays.

![Connections: network_cli SSH 22, netconf SSH 830, httpapi HTTPS 443, local plus uri for any REST API; network modules execute on the control node](../assets/T34/02-connections.png)

*All network modules run on the control node and talk out over the connection. Only Linux targets get the module copied over and run there.*

### 4. 📦 Modules: read or write?

> 💡 The module name tells you whether the task reads or changes anything. That's half of any "what does this playbook do" question.

| Module | Read or write | Key args |
|---|---|---|
| `ios_command` | 👁️ **read**: sends exec (show) commands | `commands:` |
| `ios_config` | ✏️ **write** to running-config | `lines`, `parents`, `src`, `save_when` |
| `ios_facts` | 👁️ read; sets `ansible_net_version`, `ansible_net_model`… | `gather_subset` |
| `uri` | either, depending on `method` | `url`, `method`, `headers`, `body` |
| `restconf_get` / `restconf_config` | 👁️ read / ✏️ write | `path`, `content`, `method` |
| `netconf_get` / `netconf_config` | 👁️ read (`<get>`/`<get-config>`) / ✏️ write (`<edit-config>`) | `filter`; `target`, `content` |
| `template` | ✏️ writes a file from a Jinja2 `.j2` | `src`, `dest` |
| `debug` | prints only | `msg` or `var` |

**`ios_config` in detail:**

```yaml
    - name: Create VLANs that are missing
      cisco.ios.ios_config:
        parents: "vlan {{ item.id }}"   # the config-mode context to enter first
        lines:
          - "name {{ item.name }}"      # lines typed inside that context
```

- This is the same as typing `conf t`, `vlan 99`, `name LAB-TEST`.
- It compares with running-config and only sends missing lines, so a rerun is `ok`.
- 💾 **It doesn't save to startup-config by default.** `save_when` defaults to `never`; the other choices are `always`, `modified` and `changed`. The lab saves in a handler with `save_when: modified`.

**`uri` vs `restconf_get`** (both can GET RESTCONF):

| `uri` | `restconf_get` |
|---|---|
| generic: you build the full URL, auth and `Accept: application/yang-data+json` yourself | uses the `httpapi` connection |
| runs on the control node (`delegate_to: localhost`) | its `path` starts **after** `/restconf`: `/data/ietf-interfaces:interfaces` |

**`template` vs `ios_config src:`** (both render the same `.j2`):

| `template` | `ios_config src:` |
|---|---|
| writes a **file** | pushes the rendered lines to the **device** |

> 🔐 **Exam-sim gap (package modules, server side):**

| Module | For |
|---|---|
| `ansible.builtin.yum` / `dnf` | RPM hosts (RHEL, CentOS) |
| `apt` | Debian/Ubuntu |
| `package` | the OS-agnostic wrapper |

> 🎯 Cue: "module that installs packages" → **yum** (or apt, or package).

### 5. 🔁 register, when and loop: read state, then act on it

| Keyword | Does | Detail |
|---|---|---|
| **`register: vlan_out`** | saves the task's whole result dict for **this host** | for `ios_command`, `vlan_out.stdout` is a **list**, one string per command. So `vlan_out.stdout[0]` is the `show vlan brief` text. On a looped task, the registered variable holds `results`: a list with one entry per item. |
| **`loop:`** | runs the task once per list item, with the current one in `item` | `with_items:` is the older form and reads the same |
| **`when:`** | a **raw Jinja2 expression with no `{{ }}`**: `when: site_role == "lab"` | false → the task shows `skipping` for that host |

- **`when` + `loop` is checked per item**, so some items are skipped while others change in the same task.

> 🎯 **`register` + `when` is the exam's favourite pair:**

```yaml
    - name: Read the VLAN table
      cisco.ios.ios_command:
        commands:
          - show vlan brief
      register: vlan_out                          # save the show output for this host

    - name: Create VLANs that are missing
      cisco.ios.ios_config:
        parents: "vlan {{ item.id }}"
        lines:
          - "name {{ item.name }}"
      loop: "{{ vlans }}"                         # quoted: a value starting with {{ must be
      when: item.name not in vlan_out.stdout[0]   # bare expression, checked per VLAN
      notify: Save running config                 # queue the handler, only if this reports changed
```

- Read: "for each VLAN in this host's `vlans` list, create it only if its name isn't already in the `show vlan brief` text, and ask for a save if anything changed".

| ❌ `loop: {{ vlans }}` | ✅ `loop: "{{ vlans }}"` |
|---|---|
| YAML reads `{` as the start of a dict | **YAML quoting:** a value that **starts** with `{{` must be quoted |

### 6. 📞 Handlers: once, at the end, only on changed

> 💡 **`notify:`** queues a **handler** by its exact name, but only when the task reports **`changed`**.

> 📞 Analogy: the "phone the office" note. Ten parcels can ask for the call; you make it **once**, at the end of the run, and only if something was delivered.

| | Rule |
|---|---|
| ⏰ When | queued handlers run **after all tasks** in the section, not straight after the notifying task |
| 1️⃣ How often | **once**, however many tasks notified them, in the order listed under `handlers:` |
| ✅ All-`ok` rerun | queues nothing, so no handler runs |
| ❌ Later task **fails** on that host | its queued handlers don't run, unless you pass `--force-handlers` |
| 🔤 Name mismatch | a `notify` name that doesn't match a handler exactly (case matters) → "handler not found" error and the run fails |

```yaml
  handlers:
    - name: Save running config        # must match the notify: text exactly
      cisco.ios.ios_config:
        save_when: modified            # copy running to startup only if they differ
```

![Handler decision: ok/skipped never queue; failed stops the host; changed queues once and runs at the end in handlers order](../assets/T34/04-handler-flow.png)

*Only `changed` queues a handler, and it still waits until the end of the tasks section.*

![Animated: site.yml play 1 on sw2 task by task, the handler queue fills on the first change, stays one entry on the second notify, and runs once after the last task](../assets/T34/06-handler-queue.gif)

*The queue fills on the first change, stays at one entry on the second notify, and the handler runs once after the last task. Device output in the GIF is illustrative.*

### 7. ▶️ Running a playbook and reading the recap

> 💡 `ansible-playbook -i inventory.yml site.yml` runs it. `-i` can be dropped if `ansible.cfg` sets the inventory.

| Flag | Effect |
|---|---|
| `--check` | dry run: **connects**, reports what would change, changes nothing |
| `--diff` | show before and after |
| `--limit sw2` | narrow to hosts that match **both** `hosts:` and the limit (it can't add hosts) |
| `-v` … `-vvvv` | more detail (`-vvv` adds connection detail) |
| `--syntax-check` | parse only, **no connection** |
| `--list-tasks` / `--list-hosts` | what would run, and where |
| `-e key=value` | extra vars, highest precedence |

**Result states**, per task per host:

| | State | Means |
|---|---|---|
| 🟢 | **`ok`** | ran and **changed nothing** (or was a read/debug). Not "passed a test". |
| 🟡 | **`changed`** | made a change |
| 🔵 | **`skipping`** | `when` was false |
| 🔴 | **`failed`** / **`unreachable`** | error / couldn't connect; that host stops |

- 🔄 **Idempotent** = run it again and nothing changes: the second run shows `changed=0`. The lab's `build.yml` went `changed=2` → `changed=0`, and no `RUNNING HANDLER` line appeared on run 2.
- `command`, `shell` and `ios_command` aren't config at all; `command` reports `changed` every time.

![Result states: already matches → ok, made a change → changed, when false → skipping, error → failed, can't connect → unreachable; a changed task becomes ok on the second run](../assets/T34/05-run-states.png)

*The dotted line is idempotency: what was `changed` on run 1 is `ok` on run 2.*

### 8. 🔍 The four-pass read, and the project around it

**Read any exhibit in four passes:**

```
1. Devices  hosts: -> group -> which hosts (check --limit and when too)
2. How      ansible_connection / connection: (group_vars or play vars)
3. What     each module: read or write? what data (lines, src, content, path)?
4. Order    plays in file order; each task finishes on all hosts before the next;
            handlers at the end, once, only where something changed
```

**Applied to the lab's `site.yml`:**

1. 📋 Devices: both plays target `ios_switches` = sw1 and sw2. n9k1 is **never** touched.
2. 🚚 How: play 1 uses `network_cli` (from group_vars); play 2 uses `httpapi` + `restconf` (play vars override).
3. 📦 What: play 1 reads facts and `show vlan brief`, writes missing VLANs, pushes the baseline template, shuts unused ports on **lab switches only**, prints the version. Play 2 GETs the interfaces twice and prints names: **nothing is written in play 2**.
4. 🔢 Order: "Save running config" runs **once per host** at the end of play 1, only on hosts where a VLAN or template task changed.

- One-sentence answer: "Play 1 baselines VLANs, hostname and NTP on the IOS XE switches over SSH, shuts unused ports on lab switches only, and saves the config if anything changed. Play 2 reads the interface list from the same switches over RESTCONF."

> 🔐 **Exam-sim gap (project hygiene):** the first step when starting an Ansible project is to **create a dedicated project directory** holding `ansible.cfg`, the inventory, `group_vars/`, `host_vars/`, playbooks and `roles/`, all under Git.

## ⚠️ Exam traps

| ❌ Looks like… | ✅ Actually… |
|---|---|
| 📦 `ios_command` with `configure terminal` lines configures the device | **`ios_command` is read-only**, even with `configure terminal` lines in the question. Config goes through `ios_config` or a resource module. |
| 💾 `ios_config` saves the config | **`ios_config` doesn't save.** `save_when` defaults to `never`; startup-config only changes with `save_when: modified\|always\|changed`, often in a handler. |
| 📞 a handler runs right after the notifying task | **A handler runs once, at the end, only on `changed`**: not right after the notifying task, not on an all-`ok` rerun, not if the host later fails (without `--force-handlers`). |
| 🔁 `when: "{{ x }}"`; `stdout` is a string | **`when:` takes a bare expression**, never `{{ }}`. And `stdout` is a **list**: use `stdout[0]` for the first command's text. |
| 🚚 `ansible_network_os` = `ansible_connection` | **`ansible_network_os` ≠ `ansible_connection`.** network_os = which platform; connection = which transport. `network_cli` = SSH 22, `netconf` = SSH 830, `httpapi` = HTTPS. |
| ▶️ `--check` = `--syntax-check` | **`--check` ≠ `--syntax-check`.** Check mode contacts the devices and simulates; syntax-check only parses the file. |

<details><summary><b>🟨 Should know (second pass)</b></summary>

### 🔎 Facts, magic variables, Jinja2 timing

| Item | Detail |
|---|---|
| **Facts** | data discovered from the target. `gather_facts: true` runs the generic setup module, which isn't for switches. Network plays set it `false` and run an explicit `ios_facts` task. |
| **`ios_facts`** | sets `ansible_net_version`, `ansible_net_model`, `ansible_net_hostname`… Using `ansible_net_version` without an `ios_facts` task → undefined-variable error. |
| **Magic variables** | always there: `inventory_hostname` (sw2), `groups['ios_switches']` (`["sw1","sw2"]`), `hostvars['sw2']['site_role']` (`lab`) |
| **Jinja2 timing** | `{{ var }}` is filled in on the control node, for each host, just before the task runs. In a template, `hostname {{ device_hostname }}` became `hostname LAB-SW2` for sw2. |

### 🧱 Task helpers

| Item | Detail |
|---|---|
| **`tags:`** | label tasks so `--tags vlans` or `--skip-tags restconf` runs a subset. `--tags vlans` on `site.yml` lists only "Read the VLAN table" and "Create VLANs that are missing". |
| **Empty loops are fine** | `loop: "{{ unused_ports \| default([]) }}"` on sw1 (no such variable) is an empty loop, not an error |
| **`debug`** | prints `msg:` (a string or expression) or `var:` (a variable name, no `{{ }}`). It's always `ok`. |

### 📁 Roles and project files

- **Roles:** a standard folder layout (`tasks/`, `handlers/`, `templates/`, `defaults/`, `vars/`, `meta/`) that a play pulls in with `roles: [name]`.
  - `ansible-galaxy role init <name>` creates the skeleton.
  - Roles run **before** the play's `tasks:`.
  - `defaults/` has the lowest precedence (meant to be overridden); `vars/` is high.

| Collections (`cisco.ios`) | Roles |
|---|---|
| package modules: `ansible-galaxy collection install cisco.ios` | package **your** tasks |

- **`ansible.cfg`** sets defaults (inventory path, `host_key_checking`). Search order, first found wins: `$ANSIBLE_CONFIG` → `./ansible.cfg` → `~/.ansible.cfg` → `/etc/ansible/ansible.cfg`.

### 🚚 NETCONF play (`netconf.yml`)

- `ansible_connection: ansible.netcommon.netconf`, `ansible_port: 830`.

| 👁️ Read | ✏️ Write |
|---|---|
| `netconf_get` with `source: running` and a `filter` | `netconf_config` with `target: running` and `<config>` content (`<edit-config>`) |

</details>

> 📚 **Recognise only, details in the full note:** the full 22-level precedence list and `hash_behaviour=replace`, `listen:` and `meta: flush_handlers`, `rescued` / `ignored` states, `-vvvv` detail, `pre_tasks` → `roles` → `tasks` → `post_tasks` order, `ios_config` `backup` / `match` / `replace`, `stdout_lines`, `netconf_rpc`, world-writable `ansible.cfg` being ignored, `--ask-pass`.

## ✍️ Quick self-check
<details><summary>Q1. A task has <code>when: site_role == "lab"</code>. sw1 is prod, sw2 is lab. What does the run show for sw1?</summary><code>skipping</code>, because the condition is false for sw1.</details>
<details><summary>Q2. Two tasks both notify <code>Save running config</code> and both report <code>changed</code>. How often does the handler run, and when?</summary>Once, after all tasks in the section finish. Notifications are queued and deduplicated.</details>
<details><summary>Q3. Which connection settings does <code>restconf_get</code> need against IOS XE?</summary><code>ansible_connection: ansible.netcommon.httpapi</code> and <code>ansible_network_os: ansible.netcommon.restconf</code>.</details>
<details><summary>Q4. <code>group_vars/all.yml</code> sets VLANs 10 and 20; <code>host_vars/sw2.yml</code> sets 10 and 99. Which VLANs does sw2 get?</summary>10 and 99. host_vars win, and lists are replaced, not merged.</details>
<details><summary>Q5. Which keyword saves a task's output for a later <code>when:</code>?</summary><code>register</code>, at the same indentation as the module name.</details>
<details><summary>Q6. An <code>ios_config</code> task reports <code>changed</code> and has no <code>save_when</code>. Is startup-config updated?</summary>No. <code>save_when</code> defaults to <code>never</code>, so only running-config changed.</details>
<details><summary>Q7. Which module installs a package on a RHEL host?</summary><code>ansible.builtin.yum</code> (or <code>dnf</code>). <code>apt</code> is for Debian/Ubuntu; <code>package</code> is the OS-agnostic wrapper.</details>

## 🗣️ Say it out loud
- 📋🚚📦🔢 "Four passes: devices, connection, module, order."
- 📦 "Command reads, config writes, and config doesn't save unless `save_when` says so."
- 📞 "Handlers run once, at the end, only on changed."
- 🚚 "network_cli is SSH 22, netconf is SSH 830, httpapi is HTTPS, and network modules always run on the control node."
- 📋 "Host vars beat group vars, lists replace, and `-e` beats everything."
