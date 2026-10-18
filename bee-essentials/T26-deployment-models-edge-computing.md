# T26 · Deployment models + edge computing: essentials

> Blueprint 4.1-4.3 · Full note: [bee/T26-deployment-models-edge-computing.md](../bee/T26-deployment-models-edge-computing.md) · Teach-back 2026-10-25

## In one picture
![T26 at a glance: cloud models, service models, edge, deployment types and scenario answers](../assets/T26/00-overview.png)
*Each row is one concept group; blue cells mark the winner on that criterion, and the red boxes are the exam traps.*

## The big idea
- This topic asks three separate questions about any workload: **who** the infrastructure is for (private, public, hybrid and so on), **how much** the provider runs for you (IaaS, PaaS, SaaS), and **what wraps** the app (bare metal, VM, container, function).
- Edge computing adds a fourth question: **where** the processing happens. Think of it like a factory foreman who makes the stop-the-line call on the floor instead of phoning head office for every decision.
- Almost every exam question here is a short scenario. Your job is to spot the one constraint in it (latency, data location, isolation, start-up speed) and map it to the answer.

## What you need to know

### 1. Who the cloud is for (cloud deployment models)
- A deployment model answers "who is the infrastructure provisioned for?", not "where is the rack?". The definitions follow **NIST SP 800-145**, which is the vocabulary the exam wording matches.

![Cloud deployment models](../assets/T26/01-cloud-models.png)
*The three base models on top define who uses the infrastructure; hybrid binds distinct clouds together, and multi-cloud is several public providers.*

| Model | Plain meaning | Exam cue |
|---|---|---|
| **Private** | Used exclusively by one organisation. It can be on premises or hosted off premises by a third party. | "regulated data", "full control", "own hardware", highest cost |
| **Public** | Open to the general public, on the provider's premises. | "no capex", "pay-as-you-go", "global", "elastic" |
| **Community** | Shared by several organisations with the same concerns (mission, security, compliance). | "several agencies", "same compliance regime" |
| **Hybrid** | Two or more distinct clouds that stay separate but are **bound together** so data and apps can move. | "burst to cloud at peak", "DB on-prem, front end in cloud" |
| **Multi-cloud** | Not a NIST model. Workloads spread across two or more **public** providers. | "avoid vendor lock-in", "best service from each provider" |

- Private does not mean on-prem. A dedicated environment hosted by a third party is still private, because the test is exclusive use by one organisation.
- Hybrid needs something that ties the clouds together, such as a VPN, Direct Connect / ExpressRoute, or a common management layer. Two unconnected clouds are not hybrid.
- NIST's classic hybrid example is **cloud bursting**: run on private capacity and overflow to public cloud at peak.
- Hybrid and multi-cloud can overlap. On-prem plus AWS plus Azure is both.
- Cisco context: the Meraki dashboard is SaaS in the public cloud, while Catalyst Center (DNA Center) is an appliance you run on-prem.

### 2. How much the provider runs (service models) and what makes it "cloud"
- The service model is independent of the deployment model. You can run private IaaS (OpenStack in your own DC) or consume public SaaS.

![Who manages each layer](../assets/T26/02-service-models.png)
*Yellow is what you manage and blue is what the provider manages; each step right hands one more layer to the provider.*

| Model | You control | Example |
|---|---|---|
| **IaaS** | The OS, storage, your apps, maybe host firewalls | EC2, Azure VMs, DevNet Sandbox VMs |
| **PaaS** | Only your deployed app and some hosting config; the provider runs the OS | Elastic Beanstalk, Google App Engine, Heroku |
| **SaaS** | At most a few user-specific settings | Webex, Microsoft 365, Meraki dashboard |

- The one-question test is **"who patches the OS?"** If you do, it's IaaS. If the provider does and you still write code, it's PaaS. If you only log in, it's SaaS.
- NIST lists **five essential characteristics**. If any one is missing, it is hosting or virtualisation, not cloud:
  - **On-demand self-service**: you provision without talking to a human at the provider. "Raise a ticket and wait three days" fails this.
  - **Broad network access**: reachable over standard network mechanisms from any client.
  - **Resource pooling**: the provider's resources serve many tenants (**multi-tenant**). You choose a region, not a rack.
  - **Rapid elasticity**: capacity grows **and shrinks** quickly, ideally automatically.
  - **Measured service**: usage is metered and reported, usually pay per use.
- Elasticity is not the same as scalability. Scalability only means it can grow; elasticity means it grows and shrinks with demand.

### 3. Processing near the data (edge and fog computing)
- A cloud region is far away. Every request pays a WAN round trip (light in fibre covers roughly 200 km per ms each way), and every byte sent costs WAN bandwidth, which may be thin at a factory, ship or store.
- **Edge computing** moves the processing to where the data is produced: on the device itself or on a box next to it. Only results, summaries or alerts go up to the cloud.

![Edge, fog and cloud layers](../assets/T26/03-edge-fog-cloud-arch.png)
*Read it bottom to top: raw data stops at the edge, filtered results reach the fog nodes, and only summaries cross the WAN, while the cloud pushes models and updates back down.*

| Benefit (blueprint 4.1) | Why it happens | Scenario cue |
|---|---|---|
| **Lower latency** | The decision is made locally in milliseconds. | "robot arm must stop within 10 ms" |
| **Less WAN bandwidth** | Filter locally and send summaries (the note's drill shows about 99% less traffic). | "thousands of sensors", "HD cameras at every branch" |
| **Resilience** | Keeps working when the WAN drops and queues results until it returns. | "remote oil rig", "intermittent satellite link" |
| **Data locality** | Raw data never leaves the site (privacy, sovereignty). | "patient video must not leave the hospital" |

- **Fog computing** is a layer of **fog nodes** between the end devices and the cloud. Fog nodes are things like gateways, switches, routers and servers (physical or virtual). Cisco coined the term and **NIST SP 500-325** defines it.
- If the exam options split edge and fog: edge is at or on the device producing the data, and fog is **in the network between** the devices and the cloud.
- **Cisco IOx** is Cisco's application-hosting framework for running your own apps on Cisco routers and switches (industrial routers such as the IR1101, Catalyst switches, IOS XE routers). It is the textbook "Cisco edge computing" answer. ⚠ verify the supported-platform list and app types.
- On IOS XE, the app lifecycle runs **install → activate → start**, and removal runs stop → deactivate → uninstall. ⚠ verify the CLI syntax.
- **Exam-sim gap:** IOx only runs trusted apps. It supports **application signing**, so the device verifies a signed package before running it ⚠ verify the exact signing workflow. Cue: "Cisco framework that hosts only signed, verified apps on network devices" → **IOx**, not Intersight or the Meraki dashboard.
- Edge complements the cloud rather than replacing it. Fleet-wide analytics, long-term storage and ML training stay central. The cost is many distributed boxes to patch and secure, each with limited CPU and RAM.

### 4. What wraps the app (bare metal, VM, container)

![Bare metal vs VM vs container stacks](../assets/T26/05-stacks.png)
*Count the yellow kernels: one per server on bare metal, one per guest on VMs, and one shared by all containers.*

- **Bare metal** means one OS directly on the physical server. Choose it for maximum performance, GPU or low-latency hardware access, per-CPU licensing, or as the host for a hypervisor.
- A **virtual machine** runs on a **hypervisor**, and each VM has a complete guest OS with **its own kernel**. That is why Windows and Linux VMs can share one host.
- A **container** is an isolated process that **shares the host kernel**, packaged with its libraries in an image. Containers are **OS-family specific** (NIST SP 800-190): a Linux host only runs Linux containers. Docker Desktop on a Mac quietly runs a Linux VM to host them.

| | **Type 1 hypervisor** (bare-metal / native) | **Type 2 hypervisor** (hosted) |
|---|---|---|
| Runs on | The hardware directly | Top of a host OS |
| Examples | VMware ESXi, KVM, Hyper-V, Xen | VirtualBox, VMware Workstation / Fusion |
| Used for | Data centres and cloud (EC2 runs on Type 1) | Laptops and labs |

- KVM is a Linux kernel module that turns Linux into a hypervisor, and it is usually classed as Type 1. ⚠ verify if exam options treat it differently.

### 5. How the wrappers compare

| Criterion | Bare metal | VM | Container |
|---|---|---|---|
| **Isolation** | Highest | High | Lowest (shared kernel) |
| **Start-up** | Hours to days | Minutes (boots a full OS) | Seconds or less |
| **Density per host** | One OS per box | Tens | Hundreds |
| **Portability** | Tied to that hardware | Tied to a hypervisor image format | Same image on any host with a runtime (same OS family and CPU arch) |
| **Different OS per workload** | No | **Yes** | No |

- The memory hook is that isolation goes down as density goes up.
- The types stack rather than exclude each other: containers often run inside VMs in the cloud (EC2 plus ECS/EKS).
- "Runs the same anywhere" has limits. An `amd64` image won't run natively on `arm64`, and a Linux image won't run on a Windows kernel.

### 6. Functions and app shapes (serverless, monolith vs microservices)
- **Serverless / FaaS** (Function as a Service) means you upload a function and the provider runs it only when an event fires (HTTP request, file upload, queue message, schedule). The provider handles servers, OS, runtime and scaling, including scale to zero, and you pay **per invocation and duration**.
- Serverless is the wrong answer for long-running jobs (Lambda's max run time is 15 min ⚠ verify), anything sensitive to **cold-start** delay, or stateful work. It still runs on servers; you just don't manage them.
- Network example: a Meraki or Webex webhook hits an API gateway, and a Lambda opens a ticket. Nothing runs between events.

![Monolith vs microservices](../assets/T26/07-monolith-vs-microservices.png)
*To add capacity for one busy part, the monolith copies the whole app, while microservices scale only the busy service.*

| | **Monolith** | **Microservices** |
|---|---|---|
| Shape | One codebase and one deployable unit | Many small services talking over APIs |
| Deploy and scale | The whole app every time | Each service independently |
| Failure | One bug can take everything down | Can be contained to one service |
| Cost | Simple at first | Network latency, tracing, versioned APIs, more ops |

### 7. Reading the scenario (exam angle)

![Scenario decision tree](../assets/T26/08-scenario-decision.png)
*Latency and IoT are checked first because they override everything; data location comes next, then the workload wrapper.*

| Scenario cue | Answer |
|---|---|
| IoT sensors, ms latency, unreliable WAN | **Edge** (fog if "in the network between") |
| Docker app on a Cisco router at the branch | **Edge via IOx** |
| DB on-prem by regulation, web tier bursts to AWS | **Hybrid** |
| AWS and Azure to avoid lock-in | **Multi-cloud** |
| Fast start-up, many identical instances | **Containers** |
| Windows and Linux on one host, strongest isolation short of hardware | **VMs** |
| Code runs only on events, pay per execution | **Serverless** |
| Scale one part of the app independently | **Microservices** |

## Exam traps (the ones that catch people)
- Looks like "private = on-prem", but it's actually about exclusive use by one organisation, so a third-party hosted dedicated cloud is still private.
- Looks like hybrid, but AWS plus Azure with nothing private is actually **multi-cloud**, because hybrid needs two distinct cloud types bound together.
- Looks like a private cloud, but a ticket-driven VMware farm is actually just virtualisation, because it fails on-demand self-service.
- Looks like edge and fog are the same, but fog is actually the network layer (routers, switches, gateways) **between** devices and the cloud.
- Looks like containers can run anything, but they actually can't run a different OS family from the host, so "different OS" points to a **VM**.
- Looks like "hosted hypervisor" sounds enterprise-grade, but "hosted" actually means **Type 2** (VirtualBox), running on a host OS.
- Looks like any Cisco tool could host edge apps, but the on-box app-hosting answer is actually **IOx**, not IOS XE itself or Intersight.
- Looks like serverless means no servers, but it actually still runs on servers and is a poor fit for long-running or stateful jobs.

## Quick self-check
<details><summary>Q1. Who patches the OS in PaaS?</summary>The provider. You only push code; if you patch the OS, it's IaaS.</details>
<details><summary>Q2. A motor must stop within 10 ms of a bad sensor reading over a thin WAN. Which model?</summary>Edge computing, because a cloud round trip can't meet the deadline.</details>
<details><summary>Q3. Is VirtualBox a Type 1 or Type 2 hypervisor?</summary>Type 2, because it runs on top of a host OS.</details>
<details><summary>Q4. Order bare metal, VM and container from strongest isolation to highest density.</summary>Bare metal → VM → container, because more of the stack is shared at each step.</details>
<details><summary>Q5. Which NIST trait distinguishes elasticity from simple scalability?</summary>Rapid elasticity means scaling out and back in with demand, not just growing.</details>

## Cheat lines to say out loud
- "Who's it for, how much do they run, what wraps it, and where does it run."
- "Who patches the OS? Me = IaaS, them plus my code = PaaS, I just log in = SaaS."
- "Edge decides on the floor; only summaries cross the WAN; IOx is Cisco's edge."
- "Isolation down, density up: bare metal, VM, container."
- "Two public clouds is multi-cloud; private bound to public is hybrid."
