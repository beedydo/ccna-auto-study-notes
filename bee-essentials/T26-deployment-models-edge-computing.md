# T26 · Deployment models + edge computing: essentials

> Blueprint 4.1-4.3: benefits of edge computing; deployment models (private, public, hybrid, edge); deployment types (VMs, bare metal, containers) · Full note: [bee/T26-deployment-models-edge-computing.md](../bee/T26-deployment-models-edge-computing.md) · Teach-back 2026-10-25

![T26 at a glance: cloud models, service models, edge, deployment types and scenario answers](../assets/T26/00-overview.png)

*Each row is one concept group; blue cells mark the winner on that criterion, and the red boxes are the exam traps.*

## The big idea
- This topic asks **separate questions** about any workload. Each has its own answer; keep them apart.
  - **Who is the infrastructure for?** That's the deployment model: private, public, community, hybrid (and multi-cloud).
  - **Where does the processing happen?** In a far-away cloud region, or at the **edge**, next to the data.
  - **What wraps the app?** That's the deployment type: bare metal, VM, container (or a function).
  - A fourth, secondary question, **how much does the provider run for you** (IaaS, PaaS, SaaS), is in Should know.
- **Analogy for deployment models: places to live.**
  - **Private** = a house used only by your family. You can own it or rent the whole house from a landlord; it's private either way, because nobody else lives there.
  - **Public** = a hotel. Anyone can book a room, the hotel runs the building, and you pay per night.
  - **Community** = a shared staff housing block for several agencies that follow the same rules.
  - **Hybrid** = your house plus hotel rooms you book on busy weekends, with a car that links them. No link, no hybrid.
- **Analogy for edge: a factory foreman.** The foreman makes the stop-the-line call on the floor instead of phoning head office for every decision. Head office still gets the daily report.
- **Analogy for deployment types: housing again.**
  - **Bare metal** = a detached house: one family, nothing shared.
  - **VM** = flats in one building: each flat has its own front door, kitchen and plumbing (its own kernel), on a shared plot (the hypervisor).
  - **Container** = rooms in one shared flat: everyone shares the same kitchen and plumbing (the host kernel). Quick to move into, many fit, but less privacy.
- **What the exam asks:** short scenarios. Spot the **one constraint** (latency, data location, isolation, start-up speed, different OS) and map it to the answer. Name the edge benefits, tell hybrid from multi-cloud, edge from fog, VM from container, and know that IOx is Cisco's edge answer.

## 🟥 Must know

### 1. Deployment models: who the infrastructure is for
- A deployment model answers **"who is the infrastructure provisioned for?"**, not "where is the rack?". The definitions follow **NIST SP 800-145**, which is the vocabulary the exam wording matches.
- **Private:** used **exclusively by one organisation** (it can have many business units).
  - It can sit **on premises**, or be **hosted off premises by a third party**. Both are private, because the test is exclusive use.
  - Exam cues: "regulated data", "full control", "own hardware". Most control, highest cost.
- **Public:** open to the **general public**, on the **provider's premises** (AWS, Azure, GCP).
  - Exam cues: "no capex", "pay-as-you-go", "global", "elastic".
- **Community:** shared by **several organisations with the same concerns** (mission, security, policy, compliance).
  - Exam cues: "several government agencies", "same compliance regime". It isn't "public cloud for a community".
- **Hybrid:** **two or more distinct clouds** (private, community or public) that stay separate but are **bound together** by technology that lets data and apps move between them.
  - The binding is something like a site-to-site VPN, Direct Connect / ExpressRoute, or a common management layer. Two unconnected clouds are not hybrid.
  - NIST's classic hybrid example is **cloud bursting**: run on private capacity, overflow to public cloud at peak.
  - Exam cues: "burst to cloud at peak", "DB on-prem by regulation, front end in AWS".
- **Multi-cloud:** **not a NIST model**. Workloads spread across **two or more public** providers.
  - Exam cues: "avoid vendor lock-in", "best service from each provider".
  - Hybrid and multi-cloud can overlap: on-prem plus AWS plus Azure is both.
- **Cisco context:** the Meraki dashboard is SaaS in the public cloud; Catalyst Center (DNA Center) is an appliance you run on-prem.

![Cloud deployment models](../assets/T26/01-cloud-models.png)

*The three base models on top define who uses the infrastructure; hybrid binds distinct clouds together, and multi-cloud is several public providers.*

| Model | Who uses it | Where | Exam cue |
|---|---|---|---|
| **Private** | one organisation only | on **or** off premises | regulated data, full control |
| **Public** | the general public | provider's premises | no capex, pay-as-you-go |
| **Community** | several orgs with shared concerns | on or off premises | several agencies, one compliance regime |
| **Hybrid** | 2+ distinct clouds **bound together** | mix | burst to cloud, DB on-prem + web in cloud |
| **Multi-cloud** (not NIST) | 2+ **public** providers | several providers | avoid lock-in |

### 2. Edge computing: process the data where it is produced
- **The problem, from first principles:**
  - A cloud region is far away. Every request pays a **WAN round trip**: light in fibre covers roughly **200 km per ms** each way, plus queuing and processing.
  - Every byte sent uses **WAN bandwidth**, which costs money and may be thin at a factory, ship or store.
- **Edge computing** moves the processing to where the data is produced: **on the device itself, or on a box next to it** (router, switch, gateway, local server). Only results, summaries or alerts go up to the cloud.
- **Tie to the foreman analogy:** the sensor reading goes to the foreman (the edge box), who decides "stop the motor" in milliseconds. Head office (the cloud) gets the summary.
- **Example: the edge drill in the full note** (200 sensors, 10 readings/s, 64-byte readings, one 512-byte summary per sensor per minute):

```
Cloud-only WAN upload:  11.06 GB/day     ← every raw reading crosses the WAN
Edge (summaries only):   0.15 GB/day     ← only per-minute summaries cross it
WAN traffic saved:      98.67 %
edge app on the factory router     min RTT   0.001 ms (propagation only)
regional cloud region              min RTT   8.000 ms (propagation only)   ← 800 km away
cloud region on another continent  min RTT 100.000 ms (propagation only)   ← 10,000 km away
```

  - These RTTs are **lower bounds**: real WAN round trips add queuing, routing and TLS handshakes.
  - So a "stop within 10 ms" deadline can't be met reliably from a distant region, and no amount of cloud auto scaling fixes distance.
- **The four benefits (blueprint 4.1)**, each with why it happens:
  - **Lower latency:** the decision is made locally in milliseconds, with no WAN round trip. Cue: "robot arm must stop within 10 ms", "real-time video analytics".
  - **Less WAN bandwidth:** filter and aggregate locally, send summaries (about 99% less in the drill). Cue: "thousands of sensors", "HD cameras at every branch".
  - **Resilience:** keeps working when the WAN link fails and queues results until it returns. Cue: "remote oil rig", "ship", "intermittent satellite link".
  - **Data locality:** raw data never leaves the site (privacy, sovereignty, compliance). Cue: "patient video must not leave the hospital".
- **Edge complements the cloud, it doesn't replace it.** Fleet-wide analytics, long-term storage and ML training stay central; the cloud pushes models and app updates back down.
- **The cost:** many distributed boxes to patch and secure, each with limited CPU and RAM, and physically exposed.

![Edge, fog and cloud layers](../assets/T26/03-edge-fog-cloud-arch.png)

*Read it bottom to top: raw data stops at the edge, filtered results reach the fog nodes, and only summaries cross the WAN, while the cloud pushes models and updates back down.*

![Cloud-only vs edge decision path](../assets/T26/04-cloud-vs-edge-path.png)

*Same sensor, two designs. Cloud-only pays a WAN round trip for every decision; edge decides locally and keeps working through a WAN outage.*

| Benefit | Why | Scenario cue |
|---|---|---|
| **Lower latency** | decided locally, no WAN round trip | "stop within 10 ms" |
| **Less WAN bandwidth** | send summaries, not raw data | "thousands of sensors" |
| **Resilience** | keeps working through a WAN outage | "intermittent satellite link" |
| **Data locality** | raw data stays on site | "must not leave the hospital" |

### 3. Fog computing and Cisco IOx
- **Fog computing** = a layer of **fog nodes** in the network **between** the end devices and the cloud. Cisco coined the term; **NIST SP 500-325** defines it.
  - Fog nodes are physical (**gateways, switches, routers**, servers) or virtual (VMs, virtual switches).
  - **Edge vs fog** if the options split them: **edge** = at or on the device producing the data (sensor, meter). **Fog** = the network layer above it (routers, switches, gateways) that also does storage and control.
  - Foreman analogy: edge is the worker's own judgement at the machine; fog is the floor supervisor's office between the floor and head office.
- **Cisco IOx** = Cisco's **application-hosting framework**: it lets you run **your own apps on Cisco routers and switches** (industrial routers such as the IR1101, Catalyst switches, IOS XE routers). It is the textbook "Cisco edge computing" answer. ⚠ verify the supported-platform list and app types.
  - Why it matters: the router at the branch already sits next to the sensors, so it becomes the edge/fog compute box. No extra server on site.
  - On IOS XE the app lifecycle is **install → activate → start**; removal is **stop → deactivate → uninstall**. ⚠ verify the CLI syntax.

```
configure terminal
 iox                                              ! enable the app-hosting framework
 end
app-hosting install appid sensorapp package flash:sensorapp.tar   ! 1. install the package from flash
app-hosting activate appid sensorapp              ! 2. activate it
app-hosting start appid sensorapp                 ! 3. run it
show app-hosting list                             ! check the app's state
```

  - Reference only: syntax from the full note, not run on a device. ⚠ verify.
- **Exam-sim gap: IOx only runs trusted apps.** IOx supports **application signing**: the app package is signed and the device verifies the signature before running it, so only approved code executes on a router or switch. ⚠ verify the exact signing workflow.
  - Cue: "Cisco framework that hosts only signed, verified apps on network devices" → **IOx**, not Intersight, not the Meraki dashboard, not IOS XE itself.

### 4. Deployment types: bare metal, VM, container
- Deployment type = **what sits between your app and the hardware**. The question to ask: **how many kernels are there, and who shares them?**
- **Bare metal:** one OS directly on the physical server.
  - Nothing separates apps on it, so either one app hogs the box or you buy a server per app.
  - Pick it for: **maximum performance**, GPUs or low-latency hardware access, software licensed per physical CPU, or as the host for a hypervisor.
  - Slow to provision: hours to days (rack, cable, install the OS).
- **Virtual machine (VM):** a **hypervisor** carves one server into many VMs.
  - Each VM has virtual hardware and a **complete guest OS with its own kernel**. That is why **Windows and Linux VMs can share one host**.
  - Start-up takes minutes, because each VM boots a full OS.
- **Hypervisor types:**
  - **Type 1 (bare-metal / native):** runs **directly on the hardware**. VMware ESXi, KVM, Microsoft Hyper-V, Xen. Used in data centres and cloud (EC2 runs on a Type 1 hypervisor). Less overhead, no host OS to attack.
  - **Type 2 (hosted):** runs **on top of a host OS** (Windows, macOS, Linux). Oracle VirtualBox, VMware Workstation / Fusion. Used on laptops and in labs. "Hosted" = Type 2.
  - KVM is a Linux kernel module that turns Linux itself into a hypervisor, and it is usually classed as Type 1. ⚠ verify if exam options treat it differently.
- **Container:** an isolated process (isolated by the host kernel's namespaces and cgroups), packaged with its libraries in an **image**. All containers on a host **share the host kernel**.
  - Starts in **seconds or less**: it starts a process, it doesn't boot an OS.
  - Containers are **OS-family specific** (NIST SP 800-190): a Linux host only runs Linux containers. Docker Desktop on a Mac quietly runs a Linux VM to host them.
  - The image brings userland (libraries, shell), **not a kernel**. Proof, on a Linux host:

```bash
uname -r                                   # host kernel version
docker run --rm alpine:3.20 uname -r       # Alpine container: same kernel version as the host
docker run --rm ubuntu:24.04 uname -r      # Ubuntu container: same again, a different distro but no kernel of its own
```

  - All three print the same kernel version. A VM would print its own guest kernel. (Not run in the full note: expected result from documented behaviour.)

![Bare metal vs VM vs container stacks](../assets/T26/05-stacks.png)

*Count the yellow kernels: one per server on bare metal, one per guest on VMs, and one shared by all containers.*

![Type 1 vs Type 2 hypervisors](../assets/T26/06-hypervisor-types.png)

*Type 2 has an extra host-OS layer under the hypervisor. That's why it suits laptops, not data centres.*

| | **Type 1** (bare-metal / native) | **Type 2** (hosted) |
|---|---|---|
| Runs on | the hardware directly | top of a host OS |
| Examples | ESXi, KVM, Hyper-V, Xen | VirtualBox, VMware Workstation / Fusion |
| Used for | data centres, cloud | laptops, labs |

### 5. How the deployment types compare
- **Memory hook: isolation goes down as density goes up.** Each step shares more of the stack: VMs share the hardware; containers share the hardware **and the kernel**.
- A shared kernel means a larger attack surface than a hypervisor (NIST SP 800-190), so containers are the least isolated.
- **The types stack, they don't exclude each other:** containers often run inside VMs in the cloud (EC2 plus ECS/EKS).
- **"Runs the same anywhere" has limits:** an `amd64` image won't run natively on `arm64`, and a Linux image won't run on a Windows kernel.

| Criterion | Bare metal | VM | Container |
|---|---|---|---|
| **Isolation** | **highest** | high (separate kernels) | lowest (shared kernel) |
| **Start-up** | hours to days | minutes (boots a full OS) | **seconds or less** |
| **Overhead** | none | a guest OS per VM | tiny |
| **Density per host** | one OS per box | tens | **hundreds** |
| **Portability** | tied to that hardware | tied to a hypervisor image format | same image on any host with a runtime (same OS family and CPU arch) |
| **Different OS per workload** | no | **yes** | no |

### 6. Reading the scenario
- Find the **one constraint** in the question, then walk the tree. Latency and IoT override everything; data location comes next; then the workload wrapper.

![Scenario decision tree](../assets/T26/08-scenario-decision.png)

*Latency and IoT are checked first because they override everything; data location comes next, then the workload wrapper.*

| Scenario cue | Answer |
|---|---|
| IoT sensors, ms latency, unreliable WAN | **Edge** (fog if "in the network between") |
| Docker app on a Cisco router at the branch | **Edge via IOx** |
| All data must stay on-prem, full control of hardware | **Private** |
| DB on-prem by regulation, web tier bursts to AWS | **Hybrid** |
| AWS and Azure to avoid lock-in | **Multi-cloud** |
| Several agencies share infrastructure under one compliance regime | **Community** |
| No upfront cost, scale globally, pay as you go | **Public** |
| Fast start-up, many identical instances, same image dev → prod | **Containers** |
| Windows and Linux on one host, strongest isolation short of hardware | **VMs** |
| Max performance, GPU, licence per physical socket | **Bare metal** |

## Exam traps
- **Private ≠ on-prem.** Private = exclusive use by one organisation, so a dedicated cloud hosted by a third party is still private.
- **AWS plus Azure with nothing private is multi-cloud, not hybrid.** Hybrid needs two distinct cloud types **bound together** (VPN, Direct Connect).
- **Edge vs fog:** edge is at or on the device; fog is the network layer (routers, switches, gateways) **between** devices and the cloud. Edge doesn't remove the cloud.
- **Containers can't run a different OS family from the host.** "Different OS" or "strongest isolation" → **VM**. "Hosted hypervisor" → **Type 2** (VirtualBox).
- **Cisco on-box app hosting = IOx**, including signed, verified apps. Not IOS XE itself, not Intersight, not the Meraki dashboard.

<details><summary><b>🟨 Should know (second pass)</b></summary>

- **Service models: how much of the stack the provider runs.** This is independent of the deployment model: you can run private IaaS (OpenStack in your own DC) or consume public SaaS.
  - **IaaS:** the provider runs the hardware and virtualisation; **you** control the OS, storage, your apps, maybe host firewalls. EC2, Azure VMs, DevNet Sandbox VMs.
  - **PaaS:** the provider also runs the **OS** and runtime; you control only your deployed app and some hosting config. Elastic Beanstalk, Google App Engine, Heroku.
  - **SaaS:** the provider runs everything including the app; you control at most a few user settings. Webex, Microsoft 365, Meraki dashboard.
  - One-question test: **"who patches the OS?"** You → IaaS. The provider, and you still write code → PaaS. You only log in → SaaS.
  - Analogy: IaaS = renting an empty flat (you furnish and fix it); PaaS = a serviced flat (you bring your clothes); SaaS = a hotel room (you just sleep there).

![Who manages each layer](../assets/T26/02-service-models.png)

*Yellow is what you manage and blue is what the provider manages; each step right hands one more layer to the provider.*

- **NIST's five essential characteristics.** If any one is missing, it is hosting or virtualisation, not cloud.
  - **On-demand self-service:** you provision without talking to a human at the provider. "Raise a ticket and wait three days for a VM" fails this, so a ticket-driven VMware farm is not a private cloud.
  - **Broad network access:** reachable over standard network mechanisms from any client (API and web console from anywhere).
  - **Resource pooling:** the provider's resources serve many tenants (**multi-tenant**), assigned dynamically. You choose a region, not a rack. A private cloud still pools, but only across one org's business units.
  - **Rapid elasticity:** capacity grows **and shrinks** quickly, ideally automatically. Elasticity ≠ scalability: scalability only means it can grow.
  - **Measured service:** usage is metered and reported, usually pay per use.
- **Serverless / FaaS (Function as a Service):** you upload a **function**; the provider runs it only when an event fires (HTTP request, file upload, queue message, schedule), then tears it down.
  - The provider handles servers, OS, runtime and scaling, including **scale to zero**. You pay **per invocation and duration**, not for idle time. AWS Lambda, Azure Functions, Google Cloud Functions.
  - Wrong answer for long-running jobs (Lambda's max run time is 15 min ⚠ verify), anything sensitive to **cold-start** delay, or stateful work. It still runs on servers; you just don't manage them.
  - Network example: a Meraki or Webex webhook hits an API gateway, and a Lambda opens a ticket. Nothing runs between events.
- **Monolith vs microservices** (app shape, not deployment type):
  - **Monolith:** one codebase, one deployable unit. To scale one busy part you copy the **whole** app, and one bug can take everything down. Simple to build at first.
  - **Microservices:** many small services talking over APIs (REST, message queues). Each deploys and scales independently, and a failure can be contained to one service. The price: network latency between services, distributed tracing, versioned APIs, more ops work. They pair naturally with containers (one service per image).
  - Cue: "scale one component independently / teams deploy separately" → microservices. "Small team, simple app" → a monolith is fine.

![Monolith vs microservices](../assets/T26/07-monolith-vs-microservices.png)

*To add capacity for one busy part, the monolith copies the whole app, while microservices scale only the busy service.*

</details>

> **Recognise only, details in the full note:** NIST SP numbers (800-145, 500-325, 800-190), `ioxclient` and IOx Local Manager, the `app-vnic` sub-mode, VM image formats (VMDK, QCOW2), `systemd-detect-virt` output, CaaS/NaaS labels, Lambda's 15-min limit (⚠ verify).

## Quick self-check
<details><summary>Q1. A motor must stop within 10 ms of a bad sensor reading over a thin WAN. Which model?</summary>Edge computing, because a cloud round trip can't meet the deadline. Auto scaling fixes capacity, not distance.</details>
<details><summary>Q2. Customer DB on-prem for regulation, web front end in AWS, linked by a site-to-site VPN: which model?</summary>Hybrid. Two distinct cloud types (private + public) bound together. Multi-cloud would mean 2+ public providers.</details>
<details><summary>Q3. Is VirtualBox a Type 1 or Type 2 hypervisor?</summary>Type 2, because it runs on top of a host OS.</details>
<details><summary>Q4. Order bare metal, VM and container from strongest isolation to highest density.</summary>Bare metal → VM → container, because more of the stack is shared at each step.</details>
<details><summary>Q5. Which Cisco capability runs a containerised data-collection app directly on a branch industrial router?</summary>Cisco IOx, the application-hosting framework on routers and switches. Not Intersight or Catalyst Center.</details>
<details><summary>Q6. Can a Linux host run a Windows container natively? Why?</summary>No. Containers share the host kernel, so the OS family must match. Use a VM for a different OS.</details>
<details><summary>Q7. Who patches the OS in PaaS?</summary>The provider. You only push code; if you patch the OS, it's IaaS.</details>

## Say it out loud
- "Who's it for, where does it run, and what wraps it."
- "Two public clouds is multi-cloud; private bound to public is hybrid."
- "Edge decides on the floor; only summaries cross the WAN; IOx is Cisco's edge."
- "Isolation down, density up: bare metal, VM, container."
- "Who patches the OS? Me = IaaS, them plus my code = PaaS, I just log in = SaaS."
