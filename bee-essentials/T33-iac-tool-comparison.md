# T33 · IaC + tool comparison: essentials

> Blueprint 5.5, 5.6 · Full note: [bee/T33-iac-tool-comparison.md](../bee/T33-iac-tool-comparison.md) · Teach-back 2026-11-01

## In one picture
![T33 at a glance: IaC principles, declarative vs imperative, push vs pull, a six-tool matrix and scenario answers on one page](../assets/T33/00-overview.png)
*Rows are concept groups, the matrix compares six tools on the same criteria, blue cells are the exam's go-to answers and red boxes are traps.*

## The big idea
- **Infrastructure as Code (IaC)** means the infrastructure you want is written down in files, kept in Git, and applied by a tool, instead of being typed into a CLI by hand.
- An analogy: an IaC file is the architect's blueprint, and the tool is the builder who checks the building against it and fixes only what differs.
- You already live this with Ansible and Terraform. The exam's angle is classification: **declarative vs imperative**, **push vs pull**, **agentless vs agent-based**, and "which tool fits this scenario". The one new piece is Cisco **NSO**.

## What you need to know

### 1. Why IaC (5.5)
- The wanted state (VLANs, NTP, VMs, ACI tenants, firewall rules) lives in **machine-readable files** such as `*.tf`, playbooks or manifests, and only the tool changes the devices.
- **Version control** gives you **history** (who changed VLAN 20, and why), **review** (a pull request where people read the diff and the plan output before merge) and **rollback** (`git revert`, then re-apply).
- It is **repeatable and consistent**: the same files give the same result in every environment. Dev, test and prod differ only in variables, so there are no hand-made "snowflake" devices.
- It **enables CI/CD for infrastructure**: because a change is a commit, a pipeline can lint, run `terraform plan` or `ansible-playbook --check`, wait for approval, apply and test.
- Other wins the exam may name: speed, fewer human errors, documentation-as-code and disaster recovery (rebuild from the repo).

### 2. Declarative vs imperative
- **Declarative** means you describe the end state ("VLAN 10 named USERS exists") and the tool works out the steps. **Imperative** (also called **procedural**) means you write the steps in order ("create VLAN 10, then name it").

![Imperative steps vs declarative diff loop](../assets/T33/01-imperative-vs-declarative.png)
*Left: a fixed step list that ignores the current state, so a re-run breaks. Right: read the device, diff it against the desired state, and change only the difference.*

| | **Declarative** (WHAT) | **Imperative / procedural** (HOW) |
|---|---|---|
| You write | the end state | the steps |
| Tool's job | read actual, diff, work out the steps and order | run the steps as written |
| Re-run | does nothing if already correct | depends on the author; often errors or duplicates |
| Examples | Terraform (HCL), NSO (YANG service models), Puppet, Salt states, Kubernetes YAML | shell/Python scripts; Chef recipes run in order; Ansible tasks run top to bottom |

- In the lab, running the imperative step list a second time gave `ERROR 409 VLAN 10 already exists` and a duplicated NTP server, because the steps never check the current state.
- The **diff** is the heart of every declarative tool. Terraform calls it a **plan**, and NSO calls it a **dry-run**.
- In Terraform the order of blocks doesn't matter, because it builds a dependency graph. In an Ansible playbook, task order **does** matter.
- **Ansible is the grey area.** Its tasks run in order (procedural), but most of its modules are state-based and idempotent (`state: merged`). If you must pick "declarative" from a list, pick Terraform, Puppet or NSO. ⚠ verify the exact framing in the CBT/N2K questions.

### 3. Idempotency, drift, mutable vs immutable
- **Idempotency** means running the same thing again gives the same end state and changes nothing after the first time. In the lab, the second apply reported `0 changed, 2 ok`. Ansible shows it as `changed=0` in the recap.
- Idempotency is a property of **how the code is written**, not of the tool. Ansible's `command` and `shell` modules are not idempotent unless you add `creates:` or `changed_when:`.
- **Configuration drift** means the real config has moved away from the code, usually because someone made a manual change.

![Animated drift and idempotency loop](../assets/T33/07-drift-loop.gif)
*Plan (8 changes), apply, apply again (0 changed: idempotent), a manual CLI edit on sw2 (drift), plan detects it, apply fixes only sw2. A push tool doesn't watch devices; drift waits for the next run.*

- **Push tools catch drift only when you run them** (`terraform plan`, `ansible-playbook --check --diff`). Pull agents catch it on their next timed run and fix it themselves. NSO detects it with `check-sync` / `compare-config`.
- **Mutable** infrastructure is changed in place (patch the same box), so its drift risk grows over time. **Immutable** infrastructure is never edited: you build a new image or instance, swap it in, and destroy the old one.
- Network hardware is mutable by nature, since you can't throw away a core switch for each change. Immutable is the container and cloud golden-image pattern. "Pets vs cattle" is the same idea: pets are nursed back to health, cattle are replaced.

### 4. Push vs pull, agentless vs agent-based
- Push vs pull is about **who opens the connection**. Agentless vs agent-based is about **whether extra software lives on the managed node**.

![Push vs pull architecture: a control node connecting out to agentless devices, and agents on nodes calling a config server](../assets/T33/09-push-vs-pull-arch.png)
*Follow each line from its start to its arrow. Push: the control node connects out over SSH, NETCONF or HTTPS when you run it. Pull: an agent on each node calls the server on a schedule.*

| | **Push** | **Pull** |
|---|---|---|
| Who connects | controller to node | node's agent to server |
| When changes land | when you (or CI) run it | on the agent's next check-in (Puppet: every 30 min by default) |
| Drift fix | only on the next run | automatic on every agent run |
| Tools | Ansible, Terraform, NSO, Salt | Puppet, Chef (and `ansible-pull`) |

| | **Agentless** | **Agent-based** |
|---|---|---|
| On the node | nothing extra: SSH, NETCONF (830), RESTCONF/HTTPS, vendor APIs | a daemon installed and kept updated |
| Fits | network devices, appliances, cloud APIs | general-purpose servers you control |
| Tools | Ansible, Terraform, NSO (and `salt-ssh`) | Puppet, Chef, Salt (default) |

- The two axes usually line up, but not always. **Salt** is agent-based (minions) yet **push** (the master publishes over ZeroMQ on ports 4505/4506).
- Routers and switches generally can't run agents, so **network automation is agentless push**. ⚠ verify: older NX-OS releases had Puppet/Chef agent support, so don't say "never".

### 5. Ansible and Terraform: the one-line angle
- **Ansible** is agentless and push. Its **network modules run on the control node itself**, not on the device, and reach the device through a connection type: `network_cli` (SSH to the CLI), `netconf` (NETCONF over SSH on 830), `httpapi` (an HTTPS API such as NX-API), or `local` with a module that makes REST calls (Meraki, Catalyst Center, ACI, ISE).
- Ansible has **no state file**: every run reads the device and compares. That's why it can't "destroy what it created last time" the way Terraform can. The exam pairs it with "agentless" and "YAML". Its sweet spot is config management and orchestration across many devices.
- **Terraform** (HashiCorp) is declarative HCL. **Providers** are plugins that turn resources into API calls; Cisco ones include `CiscoDevNet/aci` and `CiscoDevNet/iosxe` (⚠ verify the other namespaces at registry.terraform.io). The iosxe provider talks NETCONF over SSH (830); from v1.0 it dropped RESTCONF.

![Terraform core workflow](../assets/T33/04-terraform-workflow.png)
*`init` downloads providers, `plan` refreshes and diffs (the preview), `apply` calls the APIs and writes the state, and `destroy` removes everything in the state.*

- The **state file** `terraform.tfstate` maps each resource block to a real object. Remove a block and the next plan says **destroy**. Keep it in a remote backend and never commit it, because it can hold secrets.
- `plan -detailed-exitcode` returns 0 for no changes and 2 for changes, which CI uses for drift checks.
- Terraform's sweet spot is **provisioning** (VMs, VPCs, ACI tenants, Meraki networks). The classic split is "Terraform builds the VM, Ansible configures what runs inside it".

### 6. Cisco NSO, explained gently
- **Cisco Network Services Orchestrator (NSO)** came from the Tail-f acquisition, so commands and files still say `ncs` and `tail-f`. Bob owns the deep dive in T25; this is the exam-level summary.
- Think of NSO as a translator and air-traffic controller in one. You describe a **service** once ("L3VPN for customer ACME"), and NSO works out the config for every router involved, whatever the vendor, and sends it all as one coordinated change.

![NSO architecture: northbound clients, NSO core with Service Manager, Device Manager and CDB, one NED per vendor, multivendor devices](../assets/T33/08-nso-architecture-arch.png)
*Read top to bottom: every northbound interface reaches the same core, the Service Manager maps a YANG service onto per-device config, and the Device Manager sends each diff through one NED per vendor as one atomic transaction.*

- **Model-driven:** services are defined by **YANG service models** that you write. The **Service Manager** handles services; the **Device Manager** handles device config. The mapping from service to device config is called **FASTMAP** (⚠ verify the name stays exam-relevant).
- **NEDs (Network Element Drivers)** are NSO's **southbound** drivers, one per vendor or device type. Each models the device in YANG, so NSO can speak CLI (Cisco, Juniper, Arista), NETCONF or an API. That is how it does **multivendor**.
- **CDB** (configuration database) holds the config of every device and service and is kept in sync with the network (`sync-from`, `sync-to`, `check-sync`).
- **Transactions:** a commit goes to all devices "in a distributed and atomic transaction", and either everything succeeds or the whole change is rolled back. `commit dry-run` previews the device changes first. **This is the key difference from Ansible, which has no cross-device rollback.**
- **Northbound APIs** (how people and systems talk *to* NSO): CLI, Web UI, NETCONF, RESTCONF and JSON-RPC. Exam wording "REST" maps to RESTCONF/JSON-RPC.

### 7. Puppet, Chef, Salt and picking the tool (5.6)

| | Puppet | Chef | Salt |
|---|---|---|---|
| Architecture | agent + primary server ("master" in old docs) | Chef Infra Client + Chef Infra Server, Workstation with `knife` | master + minions; `salt-ssh` agentless |
| Push/pull | **pull**: catalog over HTTPS **8140**, every **30 min** by default | **pull**: client periodically fetches cookbooks | **push** over ZeroMQ |
| Language | Puppet DSL **manifests** (`*.pp`), declarative | **Ruby** **recipes** in **cookbooks** | YAML state files (`*.sls`) |

- Chef's resources run in the order written (procedural flavour). ⚠ verify if a question calls Chef "declarative". Neither Puppet nor Chef is typical for network devices on this exam.

![Scenario to tool decision tree](../assets/T33/06-tool-decision.png)
*Ask the questions in this order: atomic multivendor services first (only NSO does it), agent/pull last.*

| Scenario cue | Answer |
|---|---|
| Multivendor service across routers; if one fails, all roll back | **NSO** |
| Service defined once as a YANG model, RESTCONF northbound for the OSS | **NSO** |
| Create ACI tenants or AWS VPCs, preview, track, tear down later; "state file", "plan", "provider", "HCL" | **Terraform** |
| Push config to 500 IOS XE switches over SSH, nothing may be installed; "playbook", "inventory", "YAML" | **Ansible** |
| Every Linux server checks in and self-corrects every 30 min; "manifest", "catalog" | **Puppet** |
| "Recipe", "cookbook", "Ruby" | **Chef** |
| Replace the server with a new one built from an image | **immutable** |

## Exam traps (the ones that catch people)
- Push vs pull looks like it's about which way config flows, but it's actually about **who starts the connection**. Config ends up on the node either way.
- Agentless looks like it always means push, but Salt is agent-based yet push, and `ansible-pull` makes Ansible pull.
- Ansible looks declarative because of `state: merged`, but its tasks run in order. If the exam wants "declarative", pick Terraform, Puppet or NSO.
- Idempotent looks like a synonym for declarative, but it isn't: a careful script can be idempotent, and Ansible `command`/`shell` tasks are not idempotent by default.
- Deleting the Terraform state file looks like a reset, but Terraform simply forgets the resources (they still exist) and will try to create duplicates. Deleting a resource **block** is what plans a destroy.
- `terraform plan` looks like it might change something, but it never does; `apply` does. `destroy` removes what is in state, not everything in the account.
- NEDs look like an API you call, but they are NSO's **southbound** drivers. Northbound is CLI, Web UI, NETCONF, RESTCONF and JSON-RPC.
- A push tool looks like it watches devices live, but drift only shows up on the next `plan` or `--check` run. Pull agents fix it on their next interval.

## Quick self-check
<details><summary>Q1. The same automation runs twice and the second run changes nothing. Which property is this?</summary>Idempotency: the end state is the same however many times it runs.</details>
<details><summary>Q2. L3VPN across IOS XR and Juniper PEs; any failure must roll back every router. Which tool?</summary>Cisco NSO: atomic multivendor transactions through NEDs, with rollback.</details>
<details><summary>Q3. Which two tools use an agent that pulls config on a timer?</summary>Puppet and Chef. Ansible, Terraform and NSO are agentless push.</details>
<details><summary>Q4. You delete a resource block from `main.tf` and run `terraform plan`. What does it show?</summary>A destroy for that resource, because the state file says Terraform manages it.</details>
<details><summary>Q5. New VMs are built from a fresh image for each release and old ones deleted. What is this called?</summary>Immutable infrastructure; instances are never edited, so they don't drift.</details>

## Cheat lines to say out loud
- "Declarative says what, imperative says how; Ansible is steps in order with idempotent modules."
- "Push means the controller dials out; pull means the agent dials in every 30 minutes."
- "Ansible is agentless YAML, Terraform has state and providers, NSO has YANG services, NEDs and atomic rollback."
- "Puppet writes manifests, Chef writes Ruby recipes, and both are agent pull."
- "Drift waits for the next run on a push tool."
