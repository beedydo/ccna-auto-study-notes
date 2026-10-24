# T33 · IaC + tool comparison: essentials

> Blueprint 5.5: principles of infrastructure as code; 5.6: automation tool capabilities (Ansible, Terraform, NSO) · Full note: [bee/T33-iac-tool-comparison.md](../bee/T33-iac-tool-comparison.md) · Teach-back 2026-11-01

![T33 at a glance: IaC principles, declarative vs imperative, push vs pull, a six-tool matrix and scenario answers on one page](../assets/T33/00-overview.png)

*Rows are concept groups, the matrix compares six tools on the same criteria, blue cells are the exam's go-to answers and red boxes are traps.*

## 🧭 The big idea

This topic answers two questions:

| | Question | Answer | Analogy |
|---|---|---|---|
| 📐 | **Why write infrastructure as code?** | The infrastructure you want is written down in files, kept in Git, and applied by a tool, instead of being typed into a CLI by hand. | **An IaC file is the architect's blueprint, and the tool is the builder** who checks the building against it and fixes only what differs. |
| 🧰 | **Which tool fits which job?** | Classified on three axes: 🗺️ **declarative vs imperative**, 📡 **push vs pull**, 🔌 **agentless vs agent-based**, then matched to a scenario. | **Declarative is a sat-nav destination; imperative is a list of turns.** Give the destination and the sat-nav works out the route from wherever you are. A list of turns only works if you start from the same spot every time. |
| 🛫 | **What is NSO?** (the one new piece: you already live this with 🅰️ Ansible and 🏗️ Terraform) | Cisco **NSO** | **NSO is a translator and air-traffic controller in one.** You describe a service once; it translates it for every vendor's router and lands every change together, or none. |

- 🎯 **What the exam asks:** the IaC benefits, classify a tool on the axes, and pick the tool for a scenario: **multivendor atomic service → NSO**, **provisioning with state → Terraform**, **agentless config push → Ansible**.

## 🟥 Must know

### 1. 📐 Why IaC (5.5)

> 💡 **Machine-readable files:** the wanted state (VLANs, NTP, VMs, ACI tenants, firewall rules) lives in files such as `*.tf`, playbooks or manifests. Only the tool changes the devices.

| | Benefit | What it means |
|---|---|---|
| 📜 | **Version control: history** (Git) | who changed VLAN 20, when and why |
| 👀 | **Version control: review** | a pull request where people read the diff and the plan output before merge |
| ⏪ | **Version control: rollback** | `git revert` the commit, then re-apply; the tool converges the devices back |
| 🔁 | **Repeatable and consistent** | the same files give the same result in every environment. Dev, test and prod differ only in variables, so there are no hand-made "snowflake" devices. |
| 🚀 | **Enables CI/CD for infrastructure** | a change is a commit, so a pipeline can run on it: lint → `terraform plan` or `ansible-playbook --check` → approve → apply → test |
| ➕ | Other wins the exam may name | speed, fewer human errors, documentation-as-code, disaster recovery (rebuild from the repo) |

### 2. 🗺️ Declarative vs imperative

| | 🗺️ **Declarative** (WHAT) | 🪜 **Imperative / procedural** (HOW) |
|---|---|---|
| Analogy | the sat-nav destination | the list of turns |
| You write | the **end state** ("VLAN 10 named USERS exists") | the **steps** in order ("create VLAN 10, then name it") |
| Tool's job | read the device (actual), diff, work out the steps and order | run the steps as written |
| Re-run | does nothing if already correct | depends on the author; often errors or duplicates |
| Examples | Terraform (HCL), NSO (YANG service models), Puppet, Salt states, Kubernetes YAML | shell/Python scripts; Chef recipes run in order; Ansible tasks run top to bottom |

![Imperative steps vs declarative diff loop](../assets/T33/01-imperative-vs-declarative.png)

*Left: a fixed step list that ignores the current state, so a re-run breaks. Right: read the device, diff it against the desired state, and change only the difference.*

**🧪 In the lab:** the desired state is one JSON file (the "code" in Git):

```json
{
  "sw1": {"hostname": "branch1-sw1", "vlans": {"10": "USERS", "20": "VOICE"}, "ntp_servers": ["10.0.0.1"]},
  "sw2": {"hostname": "branch1-sw2", "vlans": {"10": "USERS", "20": "VOICE"}, "ntp_servers": ["10.0.0.1"]}
}
```

| ❌ 🪜 Imperative step list, run a second time | ✅ 🗺️ Declarative plan/apply path |
|---|---|
| gave `ERROR 409 VLAN 10 already exists` and a duplicated NTP server, because the steps never check the current state | compares this file with each device and changes only the difference |

> 💡 **The diff is the heart of every declarative tool.** Terraform calls it a **plan**; NSO calls it a **dry-run**.

| 🏗️ Terraform | 🅰️ Ansible playbook |
|---|---|
| builds a dependency graph, so block order doesn't matter | task order **does** matter |

> 🎯 **Ansible is the grey area.** Its tasks run in order (procedural), but most modules are state-based and idempotent (`state: merged`). If you must pick "declarative" from a list, pick **Terraform, Puppet or NSO**. ⚠ verify the exact framing in the CBT/N2K questions.

### 3. 🔄 Idempotency, drift, mutable vs immutable

> 💡 **Idempotency** = running the same thing again gives the same end state and changes nothing after the first time.

- Lab: the second apply reported `0 changed, 2 ok`. Ansible shows it as `changed=0` in the play recap.
- It is a property of **how the code is written**, not of the tool. Ansible's `command` and `shell` modules are not idempotent unless you add `creates:` or `changed_when:`.

**🌊 Configuration drift** = the real config has moved away from the code, usually through a manual change.

![Animated drift and idempotency loop](../assets/T33/07-drift-loop.gif)

*Plan (8 changes), apply, apply again (0 changed: idempotent), a manual CLI edit on sw2 (drift), plan detects it, apply fixes only sw2. A push tool doesn't watch devices; drift waits for the next run.*

| Tool kind | Catches drift |
|---|---|
| 📤 Push tools | **only when you run them** (`terraform plan`, `ansible-playbook --check --diff`) |
| 📥 Pull agents | catch and fix it on their next timed run |
| 🛫 NSO | detects it with `check-sync` / `compare-config` |

#### 🏠 Mutable vs 📦 immutable infrastructure

> 💡 **The question: when the config needs to change, do you edit the thing that's running, or throw it away and start a new one from the recipe?** Mutable = edit in place. Immutable = never edit; **replace**.

> 🏠 **Analogy:** mutable = **renovating your house** (edit what's there; over years every house ends up different). Immutable = **swapping a prefab cabin** (build a new one from the blueprint, move in, remove the old one).

**🔍 What each looks like in the lab** (`labs/T33/iac_demo.py`):

```bash
python3 iac_demo.py apply          # MUTABLE: edits the existing sw1-v1 in place (same instance, new config)
python3 iac_demo.py replace sw1    # IMMUTABLE: builds a fresh instance from the desired state, retires the old one
```

```
sw1: replaced sw1-v1 -> sw1-v2 (old instance destroyed, not patched)
```

- 🔢 The instance **ID changes** (`sw1-v1` → `sw1-v2`). That's the giveaway: immutable means a **new thing**, not a changed thing.
- ✅ A following `plan` prints `No changes. Devices match the desired state.`: the new instance is the desired state from birth, so there's nothing to fix.

**The immutable workflow, step by step:**

1. 📝 Change the **source** (the Dockerfile, the Packer template, the Terraform config), never the running server.
2. 🔨 **Build** a new image from it (container image, cloud "golden image" such as an AWS AMI).
3. 🧪 **Test** that image.
4. 🚀 **Start new instances** from it, move traffic to them.
5. 🗑️ **Destroy** the old instances.

- This is the same rule as T28's "**build once, promote the same artifact**": the image is the artifact, and nobody logs in to change it afterwards.

| | 🏠 **Mutable** | 📦 **Immutable** |
|---|---|---|
| How a change happens | edit, patch or upgrade the **existing** server or device in place | build a **new** image/instance, swap it in, destroy the old one |
| Instance identity | the same box for years | replaced on every change (`sw1-v1` → `sw1-v2`) |
| Drift risk | **grows** over time: every manual fix or failed half-change is a difference | **low**: instances are never edited, so they can't drift |
| Rollback | re-apply the old config (and hope it reverses cleanly) | redeploy the **previous image** |
| Typical tools | Ansible, Puppet, Chef (they connect and change what's there) | Docker / Kubernetes (T27), cloud VMs from golden images, Terraform `-replace` |
| Where you'll see it | **physical routers and switches**, long-lived VMs | containers, autoscaling cloud VMs |

> 🌐 **Network hardware is mutable by nature.** You can't throw away a core switch every time you add a VLAN, so network automation (Ansible, NSO, RESTCONF) **edits devices in place**, and that's exactly why drift detection matters so much for networks. Immutable is the cloud and container pattern.
>
> 🎯 **Exam cue:** "never modify a running server; replace it with a new one built from an image" → **immutable**. "Patch / upgrade the existing server in place" → **mutable**.

### 4. 📡 Push vs pull, 🔌 agentless vs agent-based

> 💡 **Push vs pull = who opens the connection.** 
>
> 🔌 **Agentless vs agent-based = whether extra software lives on the managed node.**

| 📤 **Push** | 📥 **Pull** |
|---|---|
| the controller connects out to the node when you (or CI) run it | an agent on each node calls a server on a schedule and fetches its config |

![Push vs pull architecture: a control node connecting out to agentless devices, and agents on nodes calling a config server](../assets/T33/09-push-vs-pull-arch.png)

*Follow each line from its start to its arrow. Push: the control node connects out over SSH, NETCONF or HTTPS when you run it. Pull: an agent on each node calls the server on a schedule.*

> 🎯 Routers and switches generally can't run agents, so **network automation is agentless push**. ⚠ verify: older NX-OS releases had Puppet/Chef agent support, so don't say "never".

| | 📤 **Push** | 📥 **Pull** |
|---|---|---|
| Who connects | controller to node | node's agent to server |
| When changes land | when you (or CI) run it | on the agent's next check-in (Puppet: every 30 min by default) |
| Drift fix | only on the next run | automatic on every agent run |
| Tools | Ansible, Terraform, NSO, Salt | Puppet, Chef (and `ansible-pull`) |

| | 🔌 **Agentless** | 🤖 **Agent-based** |
|---|---|---|
| On the node | nothing extra: SSH, NETCONF (830), RESTCONF/HTTPS, vendor APIs | a daemon installed and kept updated |
| Fits | network devices, appliances, cloud APIs | general-purpose servers you control |
| Tools | Ansible, Terraform, NSO (and `salt-ssh`) | Puppet, Chef, Salt (default) |

### 5. 🅰️ Ansible: agentless YAML push

> 💡 **Agentless + push:** the control node connects out with existing credentials. **Network modules run on the control node itself**, not on the device, and reach it through a connection type:

| Connection type | Reaches the device by |
|---|---|
| `network_cli` | SSH to the CLI |
| `netconf` | NETCONF over SSH, 830 |
| `httpapi` | an HTTPS API such as NX-API |
| `local` | with a module that makes REST calls (Meraki, Catalyst Center, ACI, ISE) |

**The lab playbook**, showing both halves of the grey area:

```yaml
- name: Branch switch baseline
  hosts: branch_switches           # targets from the inventory
  gather_facts: false
  tasks:                           # run top to bottom: procedural order
    - name: VLANs 10 and 20
      cisco.ios.ios_vlans:         # resource module
        config:
          - vlan_id: 10
            name: USERS
          - vlan_id: 20
            name: VOICE
        state: merged              # state-based: only changes what differs, so re-runs are idempotent
```

- ❌ **No state file:** every run reads the device and compares. That's why it can't "destroy what it created last time" the way Terraform can, and why it has **no cross-device rollback**.
- 🎯 Sweet spot: **configuration management and orchestration across many devices**. Exam cues: "playbook", "inventory", "YAML", "agentless".

### 6. 🏗️ Terraform: declarative HCL + providers + state

> 💡 **Terraform** (HashiCorp) = declarative **HCL** (`*.tf`). **Providers** are plugins that turn resources into API calls; Cisco ones include `CiscoDevNet/aci` and `CiscoDevNet/iosxe` (⚠ verify the other namespaces at registry.terraform.io). The iosxe provider talks NETCONF over SSH (830); from v1.0 it dropped RESTCONF.

```hcl
terraform {
  required_providers {
    iosxe = { source = "CiscoDevNet/iosxe" }   # which provider plugin to download on init
  }
}

provider "iosxe" {
  host     = "10.10.20.11"                     # NETCONF over SSH, port 830 by default
  username = "admin"
  password = var.iosxe_password                # from a variable, never hardcoded
}

resource "iosxe_vlan" "users" {                # one managed object: type "iosxe_vlan", name "users"
  vlan_id = 10
  name    = "USERS"                            # the end state, not a command
}
```

![Terraform core workflow](../assets/T33/04-terraform-workflow.png)

*`init` downloads providers, `plan` refreshes and diffs (the preview), `apply` calls the APIs and writes the state, and `destroy` removes everything in the state.*

```bash
terraform init        # download providers, set up the backend
terraform plan        # refresh, diff, preview: changes NOTHING
terraform apply       # execute the plan, write terraform.tfstate
terraform destroy     # delete everything in the state
```

- 🗃️ **State file** `terraform.tfstate` maps each resource block to a real object, so Terraform knows what *it* manages. Remove a block → the next plan says **destroy**. Keep it in a remote backend and never commit it, because it can hold secrets.
- 🎯 Sweet spot: **provisioning** (VMs, VPCs, ACI tenants, Meraki networks). The classic split: "Terraform builds the VM, Ansible configures what runs inside it".

### 7. 🛫 Cisco NSO: YANG services, NEDs, atomic transactions

> 💡 **Cisco Network Services Orchestrator (NSO)** came from the Tail-f acquisition, so commands and files still say `ncs` and `tail-f`. Bob owns the deep dive in T25; this is the exam-level summary.

- **The translator/air-traffic-controller idea:** you describe a **service** once ("L3VPN for customer ACME"), and NSO works out the config for every router involved, whatever the vendor, and sends it all as **one coordinated change**.

![NSO architecture: northbound clients, NSO core with Service Manager, Device Manager and CDB, one NED per vendor, multivendor devices](../assets/T33/08-nso-architecture-arch.png)

*Read top to bottom: every northbound interface reaches the same core, the Service Manager maps a YANG service onto per-device config, and the Device Manager sends each diff through one NED per vendor as one atomic transaction.*

| | Part | What it does |
|---|---|---|
| 📐 | **Model-driven** | services are defined by **YANG service models** that you write. The **Service Manager** handles services; the **Device Manager** handles device config. |
| 🔌 | **NEDs (Network Element Drivers)** | NSO's **southbound** drivers, one per vendor or device type. Each models the device in YANG, so NSO can speak CLI (Cisco, Juniper, Arista), NETCONF or an API. That is how it does **multivendor**. |
| 🗃️ | **CDB** (configuration database) | holds the config of every device and service, kept in sync with the network (`sync-from`, `sync-to`, `check-sync`) |
| ⚛️ | **Transactions** | a commit goes to all devices "in a distributed and atomic transaction". Either everything succeeds or the whole change is rolled back. `commit dry-run` previews the device changes first. **This is the key difference from Ansible**, which has no cross-device rollback. |
| ⬆️ | **Northbound APIs** (how people and systems talk *to* NSO) | CLI, Web UI, NETCONF, RESTCONF and JSON-RPC. Exam wording "REST" maps to RESTCONF/JSON-RPC. |

### 8. 🎯 Picking the tool (5.6)

![Scenario to tool decision tree](../assets/T33/06-tool-decision.png)

*Ask the questions in this order: atomic multivendor services first (only NSO does it), agent/pull last.*

| Scenario cue | | Answer |
|---|---|---|
| Multivendor service across routers; if one fails, all roll back | 🛫 | **NSO** |
| Service defined once as a YANG model, RESTCONF northbound for the OSS | 🛫 | **NSO** |
| Create ACI tenants or AWS VPCs, preview, track, tear down later; "state file", "plan", "provider", "HCL" | 🏗️ | **Terraform** |
| Push config to 500 IOS XE switches over SSH, nothing may be installed; "playbook", "inventory", "YAML" | 🅰️ | **Ansible** |
| Every Linux server checks in and self-corrects every 30 min; "manifest", "catalog" | 🧸 | **Puppet** |
| "Recipe", "cookbook", "Ruby" | 👨‍🍳 | **Chef** |
| Replace the server with a new one built from an image | 📦 | **immutable** |

## ⚠️ Exam traps

| ❌ Looks like… | ✅ Actually… |
|---|---|
| 📡 push vs pull = which way config flows; agentless = push | **Push vs pull is about who starts the connection**, not which way config flows. And agentless ≠ push by definition: Salt is agent-based yet push; `ansible-pull` makes Ansible pull. |
| 🗺️ Ansible is the "declarative" pick; idempotent = declarative | **Ansible isn't the "declarative" pick.** Its tasks run in order; pick Terraform, Puppet or NSO. And **idempotent ≠ declarative**: a careful script can be idempotent, and Ansible `command`/`shell` tasks aren't by default. |
| 🏗️ deleting the state file deletes the resources | **Terraform state:** deleting a resource **block** plans a destroy. Deleting the **state file** makes Terraform forget the resources (they still exist), so it tries to create duplicates. `plan` never changes anything; `destroy` removes what's in state, not everything in the account. |
| 🛫 Ansible does atomic multivendor rollback; NEDs are northbound | **NSO = atomic multivendor rollback**, not Ansible. **NEDs are southbound**; northbound is CLI, Web UI, NETCONF, RESTCONF, JSON-RPC. |
| 🌊 push tools watch for drift live | **Drift isn't watched live by push tools.** It shows up on the next `plan` or `--check` run; pull agents fix it on their next interval. |

<details><summary><b>🟨 Should know (second pass)</b></summary>

### 🧸👨‍🍳🧂 Puppet, Chef, Salt

| | 🧸 Puppet | 👨‍🍳 Chef | 🧂 Salt |
|---|---|---|---|
| Architecture | agent + primary server ("master" in old docs) | Chef Infra Client + Chef Infra Server, Workstation with `knife` | master + minions; `salt-ssh` agentless |
| Push/pull | 📥 **pull**: catalog over HTTPS **8140**, every **30 min** by default | 📥 **pull**: client periodically fetches cookbooks | 📤 **push** over ZeroMQ (ports 4505/4506) |
| Language | Puppet DSL **manifests** (`*.pp`), declarative | **Ruby** **recipes** in **cookbooks** | YAML state files (`*.sls`) |

- Chef's resources run in the order written (procedural flavour). ⚠ verify if a question calls Chef "declarative".
- Neither Puppet nor Chef is typical for network devices on this exam.

### ➕ More details

| | Point | Detail |
|---|---|---|
| 🏗️ | **Terraform in CI** | `terraform plan -detailed-exitcode` returns 0 for no changes and 2 for changes, which pipelines use for drift checks. `apply` asks for `yes` unless you pass `-auto-approve`. |
| 🛫 | **NSO FASTMAP** | the mapping from a service down to per-device config, which also handles service modify and delete (⚠ verify the name stays exam-relevant) |
| 🔌 | **The "why" behind agentless for networks** | devices already expose SSH, NETCONF and HTTPS APIs, so a controller can use what's there instead of installing and patching a daemon on every box |

</details>

> 📚 **Recognise only, details in the full note:** other Cisco Terraform provider namespaces (⚠ verify), `terraform fmt` / `validate`, remote backends (S3, HCP Terraform), NSO `ncs_cli` and `load merge`, NSO Python/Java bindings, `puppet agent -t`, `salt '*' state.apply`, tool vendor ownership (⚠ verify), the Terraform "No changes" message wording (⚠ verify).

## ✍️ Quick self-check
<details><summary>Q1. The same automation runs twice and the second run changes nothing. Which property is this?</summary>Idempotency: the end state is the same however many times it runs.</details>
<details><summary>Q2. L3VPN across IOS XR and Juniper PEs; any failure must roll back every router. Which tool?</summary>Cisco NSO: atomic multivendor transactions through NEDs, with rollback.</details>
<details><summary>Q3. Which two tools use an agent that pulls config on a timer?</summary>Puppet and Chef. Ansible, Terraform and NSO are agentless push.</details>
<details><summary>Q4. You delete a resource block from <code>main.tf</code> and run <code>terraform plan</code>. What does it show?</summary>A destroy for that resource, because the state file says Terraform manages it.</details>
<details><summary>Q5. New VMs are built from a fresh image for each release and old ones deleted. What is this called?</summary>Immutable infrastructure; instances are never edited, so they don't drift.</details>
<details><summary>Q6. Someone changes VLAN 20's name on a switch CLI. When does Ansible or Terraform notice?</summary>Only on the next run (<code>terraform plan</code> or <code>ansible-playbook --check --diff</code>). Push tools don't watch devices; that is configuration drift.</details>
<details><summary>Q7. Which are NSO's northbound interfaces, and what are NEDs?</summary>Northbound: CLI, Web UI, NETCONF, RESTCONF, JSON-RPC. NEDs are the southbound drivers, one per vendor or device type.</details>

## 🗣️ Say it out loud
- 🗺️🪜 "Declarative says what, imperative says how; Ansible is steps in order with idempotent modules."
- 📡 "Push means the controller dials out; pull means the agent dials in every 30 minutes."
- 🅰️🏗️🛫 "Ansible is agentless YAML, Terraform has state and providers, NSO has YANG services, NEDs and atomic rollback."
- 🧸👨‍🍳 "Puppet writes manifests, Chef writes Ruby recipes, and both are agent pull."
- 🌊 "Drift waits for the next run on a push tool."
