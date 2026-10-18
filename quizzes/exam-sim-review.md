# Exam simulation review (100 questions)

Answer key from Kaplan; explanations are my own wording. Question text is paraphrased, not copied.

## Software Development and Design

**Q23 (1.1) NETCONF message element (XML)**

- Key: B, <rpc>
- Why: Every NETCONF operation is wrapped in `<rpc>`. The answer comes back in `<rpc-reply>`.

**Q99 (1.1) Hierarchical data format for parent-child**

- Key: D, XML
- Why: XML nests elements as a tree, which suits parent-child relationships. JSON also nests.

**Q16 (1.2) Python type of a JSON array after json.loads**

- Key: D, List
- Why: In Python a JSON array becomes a list and a JSON object becomes a dict.

**Q49 (1.2) Safe XML parsing library**

- Key: A, defusedxml
- Why: defusedxml disables dangerous XML features such as external entities.
- Notes gap: G01

**Q62 (1.2) Parse nested YAML config in Python**

- Key: A, Direct key indexing
- Why: PyYAML turns nested YAML into nested dicts, so `data["database"]["credentials"]` reaches the value.

**Q83 (1.3) Cisco framework for network test automation (TDD)**

- Key: C, pyATS
- Why: Cisco's open-source automation test framework, with TDD alongside.

**Q29 (1.4) Model for MVPs and early feedback**

- Key: A, Lean
- Why: Lean aims at waste removal, MVPs and rapid feedback.

**Q30 (1.5) Reason for private methods**

- Key: B, Stop outside code changing internal state
- Why: Private members are only reachable inside the class, which is encapsulation.

**Q91 (1.7) Version control advantage for troubleshooting**

- Key: D, History and rollback
- Why: Version history lets you find which change broke something and revert to a good state.

**Q26 (1.8) What git add does**

- Key: B, Stages changes for the next commit
- Why: `git add` moves changes to the staging area. `git commit` records them.

**Q55 (1.8) Command that records a snapshot**

- Key: D, git commit
- Why: `git commit` records the staged snapshot.

**Q73 (1.8) Compare changes**

- Key: C, git diff
- Why: `git diff` shows changes between commits, branches, files or working tree.

**Q75 (1.8) Obtain a local copy of a remote repo**

- Key: C, git clone
- Why: Copies a remote repository, with history, to your machine.

## Understanding and Using APIs

**Q5 (2.1) Tool to construct an API request**

- Key: B, Postman
- Why: Postman builds and sends API requests. Traceroute shows a network path, Ansible automates configuration, Skype is chat.
- Notes gap: G20

**Q25 (2.1) Tool to call APIC REST APIs**

- Key: C, Postman
- Why: A GUI client for REST. APIC also has its own API Inspector in the GUI.

**Q72 (2.1) Where to specify action in request**

- Key: C, Endpoint URL
- Why: The endpoint URL is where you specify the target resource of the request.

**Q11 (2.2) Role of webhooks in integration**

- Key: B, Connecting diverse applications
- Why: Webhooks push an HTTP callback when an event happens, which is how apps get wired together. They are not an encryption feature.

**Q36 (2.2) Steps to implement incoming webhooks**

- Key: A, Expose an API endpoint on your server
- Why: The provider POSTs to a URL you control, so you build the endpoint and register it.

**Q87 (2.2) Webhooks and authentication**

- Key: C, Secure tokens in webhook payloads
- Why: Webhooks are not an auth mechanism. Include a secret token or signature so the receiver can verify the sender.

**Q1 (2.3) API keys: required handling**

- Key: D, Send API keys over HTTPS
- Why: TLS stops anyone on the path reading the key. Never share one key across apps, never publish it, and rotate on a schedule rather than per request.

**Q79 (2.4) Error while processing a request**

- Key: C, 500
- Why: A generic server-side failure is 500. Other 5xx codes are more specific.

**Q97 (2.4) Server-side error indicator**

- Key: A, 500
- Why: Server-side errors are 5xx.

**Q3 (2.5) 401 on a POST: likely cause**

- Key: D, Invalid API key in the header
- Why: 401 means missing or bad credentials. A wrong method gives 405, a missing device 404, a downed server 5xx.

**Q24 (2.5) GET to /products: response interpretation**

- Key: A, Body is a JSON object describing the resource
- Why: Read the status line first, then headers such as Content-Type, then the body. A JSON body is the resource representation.

**Q89 (2.5) DELETE a device endpoint: response**

- Key: B, DELETE not allowed at that endpoint (405)
- Why: 405 Method Not Allowed: the resource exists but does not accept DELETE.

**Q93 (2.5) Malformed JSON body on POST**

- Key: A, 400
- Why: 400 Bad Request: malformed syntax such as invalid JSON.

**Q51 (2.6) Response data format**

- Key: A, JSON
- Why: Cisco REST APIs return JSON by default. XML is sometimes available, for example UCS Manager.

**Q90 (2.6) Three main parts of an HTTP response**

- Key: A, Status line, headers, body
- Why: The three parts of an HTTP response.

**Q14 (2.7) Credentials as base64 in Authorization header**

- Key: A, Basic authentication
- Why: Basic = base64(user:password) in the Authorization header. Bearer carries a token, OAuth issues tokens, Digest sends a hash.

**Q50 (2.7) Use of bearer tokens**

- Key: C, Unique token in the header
- Why: A bearer token goes in `Authorization: Bearer <token>`.

**Q77 (2.7) Where API key is usually sent**

- Key: A, In the request header
- Why: API keys usually go in a header such as `X-API-Key`, sometimes in the query string.

**Q43 (2.8) API style for lightweight, scalable service**

- Key: D, REST
- Why: REST is stateless, lightweight and scales easily, which is why it is the default for web services.

**Q60 (2.9) Not a method of requests**

- Key: A, fetch()
- Why: `fetch()` is JavaScript. `requests` has get, post, put, patch, delete, head and options.

**Q70 (2.9) Correct requests script**

- Key: A, import requests; requests.get(url)
- Why: Needs `import requests` and a call such as `requests.get()`. Anything else is not the library's API.

## Cisco Platforms and Development

**Q18 (3.1) Connect to a Cisco device with IP, user, password**

- Key: D, ncclient connect call
- Why: Kaplan's key shows `ncclient.connect(host=..., username=..., password=...)`. In real code it is `from ncclient import manager` then `manager.connect(host=..., port=830, username=..., password=..., hostkey_verify=False)`. Learn the real one.

**Q85 (3.1) Create a build environment before using an SDK**

- Key: D, Create an RPM build directory structure
- Why: Trivia: rpmbuild expects BUILD, RPMS, SOURCES, SPECS and SRPMS directories. Low priority.
- Notes gap: G19

**Q28 (3.2) SDN platform for provisioning**

- Key: B, ACI
- Why: ACI is Cisco's data-centre SDN fabric with policy-driven automation through APIC.

**Q61 (3.2) App to monitor network health**

- Key: D, gRPC
- Why: gRPC runs over HTTP/2 and supports streaming, so the server can push device status in real time.

**Q69 (3.2) Primary function of NSO northbound API**

- Key: C, Integrate with external tools and platforms
- Why: NSO's northbound interfaces (REST, NETCONF, CLI, JSON-RPC) expose it to orchestrators and other software.

**Q82 (3.2) SD-WAN path selection feature**

- Key: A, Path selection from real-time conditions
- Why: SD-WAN picks the best path by measured loss, latency and jitter against policy (SLA).

**Q20 (3.4) RESTful CUCM API for user resources**

- Key: C, User Data Services (UDS)
- Why: UDS is the RESTful user-data API in CUCM. AXL is the SOAP/XML admin API. XAPI is for Webex devices, and Spark/Teams are old Webex names.

**Q31 (3.4) CUCM API for access permissions**

- Key: B, AXL
- Why: AXL is the SOAP admin API for users, roles and permissions in CUCM.
- Notes gap: G21

**Q6 (3.5) Firepower key capabilities**

- Key: D, Deep packet inspection, intrusion prevention, threat intelligence
- Why: Firepower (Secure Firewall) is the NGFW/IPS. DNS filtering is Umbrella, antivirus/EDR is Secure Endpoint, identity and MFA is ISE.

**Q10 (3.6) Real-time performance telemetry in IOS XE**

- Key: D, Model-Driven Telemetry
- Why: MDT streams operational data from the device (push, near real time) instead of polling like SNMP. NETCONF and RESTCONF are request/response.

**Q34 (3.6) Primary API to configure IOS XE**

- Key: A, RESTCONF
- Why: RESTCONF is the HTTP-based, YANG-modelled API for configuring IOS XE.

**Q33 (3.7) Guided exercises integrating Cisco APIs with AWS/Azure**

- Key: A, Learning Labs
- Why: Guided hands-on exercises. Sandbox gives environments and Code Exchange gives code.

**Q46 (3.7) Test a new API outside production**

- Key: B, Sandbox
- Why: DevNet Sandbox gives non-production environments to try an API safely.

**Q94 (3.7) Find verified code blocks, peer expertise**

- Key: A, Cisco Code Exchange
- Why: Code Exchange is the community repository of code.

**Q41 (3.8) Library for YANG, NETCONF, RESTCONF**

- Key: D, ncclient
- Why: ncclient is the Python NETCONF client. RESTCONF is just HTTP, so use requests.

**Q63 (3.8) System to streamline NETCONF/RESTCONF usage**

- Key: D, Cisco ConfD
- Why: ConfD is Cisco's device management agent. From YANG models it provides NETCONF, RESTCONF and CLI.

**Q95 (3.8) Update router config from a web portal**

- Key: D, Separation of concerns, easier maintenance
- Why: MVC splits model, view and controller so each can change independently.

**Q100 (3.8) Data format used by NETCONF**

- Key: D, XML
- Why: NETCONF messages are XML. RESTCONF can use XML or JSON.

## Application Deployment and Security

**Q2 (4.2) Deployment model combining private and public**

- Key: A, Hybrid cloud
- Why: Hybrid joins a private cloud with a public one. Multi-cloud = several public providers, community = shared by one group, edge = processing near the source.

**Q15 (4.3) Best fit for bare metal**

- Key: B, Large, high-performance, customised enterprise app
- Why: Bare metal has no hypervisor overhead and gives full hardware control. Elastic traffic fits cloud VMs, microservices fit containers.

**Q35 (4.3) Framework allowing only signed, verified apps**

- Key: B, Cisco IOx
- Why: IOx is Cisco's application-hosting framework for edge devices and runs signed, verified applications.
- Notes gap: G18

**Q78 (4.3) One host, many OSes**

- Key: A, Virtual machines
- Why: VMs run several guest operating systems on one host through a hypervisor.

**Q19 (4.4) CI/CD best practice in NSO deployments**

- Key: B, Pipeline is the only route to production
- Why: A single, automated path gives consistency, auditability and repeatability. Manual side doors defeat the purpose.
- Notes gap: G23

**Q76 (4.4) CI/CD for an NSO deployment: needed action**

- Key: A, Tracking system (Jira)
- Why: Kaplan's key: a tracking system for features. Pipeline stages are what matter. Jira = issue tracking.
- Notes gap: G23

**Q8 (4.5) Method to clean up after a test**

- Key: A, tearDown()
- Why: tearDown() runs after each test method, setUp() before it. setUpClass/tearDownClass run once per class.

**Q32 (4.6) Purpose of EXPOSE 80**

- Key: B, Documents the port the app listens on
- Why: EXPOSE is metadata. You still publish the port with `docker run --publish`.

**Q65 (4.6) FROM ubuntu:latest**

- Key: D, Sets the base image
- Why: `FROM` picks the image your build starts from.

**Q47 (4.7) Share a local Docker image**

- Key: A, Push to a registry
- Why: Pushing publishes the image so others can `docker pull` it by name.

**Q7 (4.8) Least secure protocol for data in transit**

- Key: C, RC4 stream cipher
- Why: RC4 is broken and deprecated. HTTP Basic is an authentication scheme (weak without TLS) rather than a cipher. TLS with strong ciphers and SSH keys are fine.
- Notes gap: G22

**Q17 (4.9) Tool to orchestrate several load balancers**

- Key: D, Cisco ACI
- Why: ACI (APIC) centrally orchestrates the fabric, including layer 4-7 services such as load balancers.

**Q22 (4.9) True statement about reverse proxies**

- Key: A, Intermediary between clients and app servers
- Why: A reverse proxy sits in front of the servers and can terminate TLS, cache, filter and hide the origin.

**Q39 (4.10) Data read from DB via client-tier queries**

- Key: C, SQL injection
- Why: Untrusted input reaches a database query. Fix with parameterised queries and input validation.

**Q57 (4.11) Go to home directory**

- Key: B, cd ~
- Why: Kaplan wrote `cd~`; the working command is `cd ~` (or plain `cd`).

**Q67 (4.11) Create an empty file**

- Key: C, touch {filename}
- Why: `touch` creates an empty file or updates its timestamp.

**Q45 (4.12) Why a learning culture matters in DevOps**

- Key: B, Continuous improvement
- Why: A learning culture lets the team adapt and improve its process after each failure.
- Notes gap: G07

## Infrastructure and Automation

**Q88 (5.1) YANG model for individual device config**

- Key: A, Device data model
- Why: Device data models describe one element's configuration. Service models span devices.
- Notes gap: G06

**Q56 (5.3) CML with pyATS: what to use**

- Key: B, Testbed file
- Why: pyATS describes devices, connections and credentials in a YAML testbed, including simulated CML devices.

**Q53 (5.5) Open-source IaC tool for infrastructure**

- Key: D, Terraform
- Why: Open-source declarative IaC from HashiCorp.

**Q84 (5.5) File type holding infrastructure config**

- Key: B, .tf
- Why: Terraform configuration files use the .tf extension (HCL).

**Q9 (5.6) How Ansible bridges network and app teams**

- Key: D, Automates tasks that used to be siloed per team
- Why: One automation language and playbooks serve both network and application teams, so the handover gap shrinks.

**Q86 (5.8) Best practice to start an Ansible project**

- Key: D, Create a new directory for the project
- Why: Keep each Ansible project in its own directory with inventory, playbooks and roles.
- Notes gap: G12

**Q96 (5.8) Ansible module for packages**

- Key: A, yum
- Why: Ansible's yum module manages packages on RPM-based hosts. apt is the Debian equivalent.
- Notes gap: G12

**Q58 (5.9) Temporarily change directory across scripts**

- Key: C, pushd
- Why: `pushd` saves the current directory on a stack and changes directory. `popd` returns.
- Notes gap: G09

**Q40 (5.10) RESTCONF method to modify resources**

- Key: C, PATCH
- Why: PATCH changes part of a resource, PUT replaces it and POST creates one.

**Q71 (5.11) Purpose of native operational YANG models**

- Key: A, Real-time device feature data
- Why: Operational YANG models expose runtime state such as counters and interface status. Configuration models hold desired settings.
- Notes gap: G06

**Q21 (5.12) Meaning of ! in diff -c output**

- Key: A, A changed line
- Why: In context-format diff (-c), `!` marks a changed line. `+` is added and `-` is removed.

**Q27 (5.12) Spot a large block of deleted lines in default diff output**

- Key: A, Consecutive lines starting with -
- Why: In unified output removed lines start with `-` and added with `+`, so a deleted block is a run of `-` lines.
- Notes gap: G24

**Q13 (5.13) Code review best practice**

- Key: D, Set review goals and collect metrics
- Why: Track inspection rate and defect rate, keep reviews under roughly 500 LOC an hour, annotate before the review, assign by expertise rather than seniority.
- Notes gap: G13

**Q44 (5.13) Benefit of collaborative code review**

- Key: A, Supportive environment for learning
- Why: Collaborative review shares knowledge and builds team standards besides catching defects.
- Notes gap: G13

**Q52 (5.14) Sequence diagram: completion and error events**

- Key: C, TCHECK control function
- Why: This is a telecom-style time-sequence diagram, off the exam's API theme. In API diagrams a response arrow shows success or error.
- Notes gap: G14

**Q81 (5.14) Vertical lines delimiting the transport interface**

- Key: B, The user and provider endpoints
- Why: Another telecom-style diagram question: the vertical lines show the two endpoints talking. Off the exam's API theme.
- Notes gap: G14

## Network Fundamentals

**Q12 (6.1) Valid MAC address**

- Key: A, 00-11-22-33-AA-BB
- Why: A MAC is six hex byte pairs separated by - or :. AH is not hex, 192.168.1.1 is IPv4, and Cisco dotted format is three groups of four hex digits.

**Q54 (6.1) LAN vs VLAN**

- Key: A, VLAN isolates broadcasts within a LAN
- Why: A VLAN splits one physical LAN into separate logical broadcast domains.

**Q98 (6.2) Primary use of IP addresses**

- Key: B, Route packets between networks
- Why: IP addresses are logical, hierarchical addresses used for routing between networks.

**Q4 (6.3) Main function of a router**

- Key: C, Forwards packets between networks by destination IP
- Why: A is a firewall, B a load balancer, D a switch.

**Q66 (6.3) Spread traffic across servers**

- Key: A, Load balancer
- Why: Spreads requests across servers for scale and availability.

**Q42 (6.4) Device icon: square with four connection points**

- Key: D, Router
- Why: Kaplan's key is router. Decide by function: a router joins separate networks and needs at least two interfaces.

**Q59 (6.4) Star topology: central component**

- Key: D, Switch
- Why: A star topology has one central switch (or hub) with every device connected to it.
- Notes gap: G16

**Q68 (6.5) Plane making routing decisions**

- Key: C, Control plane
- Why: The control plane builds routing decisions. The data plane forwards, the management plane configures.

**Q92 (6.5) Management plane functions (choose two)**

- Key: B + E, Monitoring/configuring devices; firmware updates
- Why: The management plane is how you manage the device: monitor, configure, access and upgrade it.

**Q37 (6.6) How DNS works**

- Key: D, Translates domain names into IP addresses
- Why: DNS maps names to addresses through a hierarchy of servers, usually over UDP 53.

**Q80 (6.7) Port for unencrypted web**

- Key: C, 80
- Why: HTTP is TCP 80. HTTPS is 443.

**Q38 (6.8) Home web access problem (scenario)**

- Key: A, Transport port blocked
- Why: The key picks a blocked port. When some traffic works and a specific service fails, suspect a port filter, not DNS or routing.

**Q64 (6.8) Cannot reach game server over a UDP port**

- Key: C, NAT problem
- Why: The key points to NAT: a UDP game port needs a mapping or port-forward, and UDP is harder for NAT than TCP.

**Q74 (6.8) Websites OK at home, not over company VPN**

- Key: D, VPN interference
- Why: Sites work from home but not over the company VPN, so the VPN path is the culprit rather than DNS or the sites.

**Q48 (6.9) Multi-player game disconnects**

- Key: B, Packet loss
- Why: Frequent disconnects point to dropped packets. Latency and jitter cause lag rather than drops.
