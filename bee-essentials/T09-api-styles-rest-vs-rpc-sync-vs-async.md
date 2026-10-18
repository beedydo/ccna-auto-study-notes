# T09 · API styles: REST vs RPC, sync vs async: essentials

> Blueprint 2.8 · Full note: [bee/T09-api-styles-rest-vs-rpc-sync-vs-async.md](../bee/T09-api-styles-rest-vs-rpc-sync-vs-async.md) · Teach-back 2026-10-18

## In one picture
![T09 at a glance: REST vs RPC vs SOAP, sync vs async](../assets/T09/00-overview.png)
*The top table compares the three API styles and shows how to spot each one on the wire. The bottom half shows sync vs async, with the Catalyst Center taskId steps numbered in order. Red boxes are exam traps.*

## The big idea
- This topic asks two separate questions about any API.
  - **Where does the "verb" (the action) live?** That tells you if it is REST, RPC or SOAP.
  - **Does the server make you wait for the answer?** That tells you if it is synchronous or asynchronous.
- Analogy for the styles:
  - **REST** is like a filing cabinet. Every drawer has a name (the URI). You only use a few standard actions on any drawer: open, add, replace, remove (the HTTP methods).
  - **RPC** is like phoning a help desk and asking for a named service: "please run getDevice for me".
  - **SOAP** is the same phone call, but every request goes on a strict official form.
- Analogy for async: a restaurant buzzer. You order, you get a buzzer at once (`202` + task ID), and you collect the food when it is ready.
- On the exam you mostly need to recognise a style from a snippet, explain a `202`, and match Cisco APIs to their style.

## What you need to know

### 1. REST: the URI is a thing, the HTTP method is the action
- In REST, the URI names a resource, which is a noun. The HTTP method is the action you take on it (**resource-centric**).
  - `GET /api/v1/devices/1` reads device 1.
  - To delete the same device, keep the same URI and change the method to `DELETE`.
- REST APIs have many URIs but only a few verbs: GET, POST, PUT, PATCH and DELETE.
- The outcome comes back in the **HTTP status code**. For example, a missing device returns `404 Not Found` in the status line, not hidden in the body.
- REST is **stateless**, which means you send the token on every call. It is also **cacheable**: GET responses can be cached using `ETag` and `304`.
- REST usually uses JSON, but it does not require any particular format.
- Cisco REST APIs include:
  - Meraki Dashboard
  - Catalyst Center (DNA Center) Intent API
  - Webex
  - ACI/APIC
  - SD-WAN Manager (vManage)
  - Secure Firewall Management Center (FMC)
  - RESTCONF, which gives REST-like access to YANG data

### 2. RPC: you call a named function on the server
- **RPC** stands for **Remote Procedure Call**. The idea is that calling a function on another machine should feel like calling a local one, for example `getDevice(id=1)`.
- RPC is **action-centric**.
  - The function name travels in the body (`"method": "getDevice"`), or sometimes in the URL (`POST /api/getDevice`).
  - Calls usually go to **one endpoint** and nearly always use **POST**.
- With RPC, HTTP is just a pipe. An unknown method still comes back as `200 OK`, and the error sits in the body: `"error": {"code": -32601, "message": "Method not found"}`.
- **JSON-RPC 2.0** rules to know:
  - `jsonrpc` must be `"2.0"`. `method` is the function name, and `params` is optional.
  - `id` links each reply to its request. A request with **no `id` is a notification**, and the server must not reply to it.
  - A reply contains **exactly one** of `result` or `error`, never both.
  - Error codes: `-32700` parse error, `-32600` invalid request, `-32601` method not found, `-32602` invalid params, `-32603` internal error.
- RPC family members to recognise:

| Name | How it travels | How to spot it |
|---|---|---|
| JSON-RPC | JSON, usually over HTTP POST | `"jsonrpc": "2.0"`, `"method"` |
| XML-RPC | XML over HTTP POST | `<methodCall><methodName>` |
| gRPC | **Protocol Buffers** (binary) over **HTTP/2**, defined in a `.proto` file | `rpc SayHello (HelloRequest) returns (HelloReply)`; used for model-driven telemetry ⚠ verify |
| NX-API CLI (Nexus) | CLI commands over HTTP(S); JSON-RPC is one format option | `"method": "cli"`, `"params": {"cmd": "show version", "version": 1}` ⚠ verify |
| NETCONF | XML over **SSH port 830** | `<rpc message-id="101">` … `<rpc-reply>` |

- **NETCONF is RPC.** Every operation is an `<rpc>` element with a required `message-id`, and the reply `<rpc-reply>` echoes the same ID. The operation is the child element, such as `<get-config>`, `<edit-config>`, `<lock>` or `<commit>`.
- **RESTCONF vs NETCONF** is the classic REST vs RPC pair on the exam. Both work on the same YANG data. RESTCONF uses URIs and HTTP methods; NETCONF uses named `<rpc>` operations.

![Same lookup in three styles](../assets/T09/01-same-call-three-styles.png)
*The same question in three wire formats. Only REST puts the verb in the HTTP method and uses status codes for the outcome.*

### 3. SOAP: RPC on a strict XML form
- **SOAP** stands for **Simple Object Access Protocol**. It is a W3C **protocol**, whereas REST is only a **style**. SOAP messages are **always XML**.
- Every message has the same structure:
  - `<Envelope>` is the mandatory root element. Its namespace shows the SOAP version.
  - `<Header>` is **optional** and holds metadata, such as WS-Security credentials.
  - `<Body>` is **mandatory** and holds the operation, for example `<GetDevice>`, plus its arguments.
  - `<Fault>` appears **inside the Body**, and only when there is an error.
    - SOAP 1.1 uses the children `faultcode` and `faultstring`.
    - SOAP 1.2 uses `Code`, `Reason` and `Detail`.
- The **WSDL** (Web Services Description Language) is a separate XML file. It lists every operation, its types and the endpoint. It works as a strict contract: tools generate client code from it, and requests that don't match it are rejected.
- SOAP is usually sent by **HTTP POST** with `Content-Type: text/xml` (1.1) or `application/soap+xml` (1.2). SOAP 1.1 also sends a `SOAPAction` header that names the operation.
- Errors come back as **HTTP 500 + Fault**. SOAP 1.2 maps a sender fault to `400`.
- **Cisco example:** CUCM **AXL** is SOAP and is used to provision phones and users. CUCM UDS is the REST one. The AXL endpoint is `https://<cucm>:8443/axl/` ⚠ verify.

![SOAP envelope structure](../assets/T09/02-soap-envelope.png)
*Envelope is the root, Header is optional, and Body is mandatory. The Body holds either the operation or a Fault.*

### 4. Spotting the style from a snippet

| | REST | RPC | SOAP |
|---|---|---|---|
| What it is | an architectural style | a style / family of protocols | a W3C protocol |
| Centred on | resources (nouns) | actions (function names) | actions (operations in the WSDL) |
| Where the verb lives | HTTP method | body `method`, URL, or `<rpc>` child | Body element + `SOAPAction` |
| Endpoints | many URIs | usually one | usually one |
| Format | any (mostly JSON) | JSON / XML / protobuf | XML only |
| Errors | HTTP status code | in the body (often HTTP 200) | Fault (HTTP 500) |
| Caching | yes (GET) | no | no |
| Cisco examples | Meraki, Catalyst Center, Webex, RESTCONF, FMC | NETCONF, NX-API JSON-RPC, gRPC telemetry | CUCM AXL |

- Look at the **body first**:
  - `<soapenv:Envelope>` means SOAP.
  - `<rpc>` means NETCONF.
  - `"jsonrpc"` means JSON-RPC.
- Then look at the **URL**. A verb in the path means RPC over HTTP. A noun plus an HTTP method means REST.
- JSON does not make an API REST. `POST /api/v1/runCommand` with `{"cmd": "show ip int brief"}` is **RPC-style**, even though it is JSON over HTTPS.

![Identify the API style](../assets/T09/06-identify-style.png)
*The decision flow: check the body, then the URL and method.*

### 5. Synchronous: you wait on the line
- In a **synchronous** call you send a request and then wait until the full answer comes back on the same connection.
- It is simple to code because the result is just the return value of the call. There are no IDs and no polling.
- It becomes a problem for long jobs.
  - In the lab, the server needs 1.5 s. With `timeout=5` the call works, but the client sits idle for 1.5 s.
  - With `timeout=0.5` the client gives up and gets **nothing**, even though the server goes on and finishes the work.
  - The real-world versions of this are a proxy or load balancer timeout (`504 Gateway Timeout`) or the `requests` `timeout=` setting.
  - It adds up at scale: 500 devices × 1.5 s is 12.5 minutes of waiting.

### 6. Asynchronous: take a ticket, check back later
- In an **asynchronous API**, the server accepts the job and answers **straight away**, before the work is done. The typical reply is **`202 Accepted`** plus a **task ID** or **status URL**, in the body or in a `Location` header.
- RFC 9110 defines 202 as "accepted for processing, but the processing has not been completed".
- The client can learn the result in one of two ways:
  - **Polling:** the client repeatedly sends `GET` to the status URL until it says the job is done.
  - **Callback / webhook:** the client registers a URL, and the server `POST`s to it when the job is finished (see T43).
- While it waits, the client is free to do other work, for example start jobs on other devices.
- An **async API** and **async code** are different things.
  - Async API describes how the server replies.
  - Async code (Python **`asyncio`**, awareness only) is about the client not blocking while it waits.
  - In the lab, two 1.5 s calls take 3.0 s one after the other, but only 1.5 s with `asyncio.gather()`, because the waits overlap.
  - Key words: `async def` defines a coroutine, `await` pauses it, `asyncio.run()` starts the event loop, and `asyncio.gather()` runs several coroutines at once.

### 7. The Catalyst Center taskId pattern, and when to pick which
- Long-running Catalyst Center Intent API calls (POST/PUT/DELETE) are asynchronous. The lab copies the Command Runner flow:

| Step | Call | What to read |
|---|---|---|
| 1 | `POST /dna/intent/api/v1/network-device-poller/cli/read-request` | `202` and `response.taskId` |
| 2 | `GET /dna/intent/api/v1/task/{taskId}` (repeat) | `endTime` missing = still running; `isError: true` = failed (`failureReason`) |
| 3 | the same call, until `endTime` appears | `isError: false` = success; `progress` holds `{"fileId": "…"}` |
| 4 | `GET /dna/intent/api/v1/file/{fileId}` | the command output |

- `progress` is a **string that contains JSON**, so you have to decode it a second time with `json.loads(task["progress"])["fileId"]`. The exact reply shape is ⚠ verify.
- Sequence-diagram questions (T47) draw exactly this flow: auth → POST → 202 → poll task → GET result.

![Animated async taskId flow](../assets/T09/07-async-task.gif)
*Step by step: POST, 202 + taskId, poll with no endTime, poll with endTime set, then GET the file.*

- How to choose between sync and async:

| Use synchronous | Use asynchronous |
|---|---|
| reading one device, listing VLANs, getting a token | provisioning a site, pushing a template to 200 switches |
| a small config change on one device | an image upgrade (SWIM) or device discovery |
| when you need the answer before the next line runs | when the job takes longer than the client or proxy timeout |

- Polling vs webhook:
  - Polling is simple and works through firewalls and NAT, but it wastes calls and can hit rate limits.
  - A webhook gives instant notice, but it needs a reachable HTTPS listener.

## Exam traps (the ones that catch people)
- `202` looks like success, but it only means **accepted and queued**. The next step is to poll the task URL. If you resend the POST, you queue a duplicate job.
- The task URL answers `200` while the job is still running. That `200` means "lookup OK", not "job done". The job is finished only when `endTime` is present, and then you check `isError`.
- A JSON-RPC reply of `200 OK` can still be a failure. Check whether the body has an `error` member.
- JSON over HTTP is not automatically REST. `POST /api/runCommand` or `"method": "getDevice"` is RPC style.
- In SOAP, the Header is optional, while the Envelope and Body are mandatory. The Fault sits **inside** the Body. The WSDL is a separate contract file and is not part of each message.
- NETCONF and RESTCONF both start with "NET/REST" and use YANG, but **NETCONF is RPC** (SSH 830, `message-id`) and **RESTCONF is REST**.
- gRPC uses **HTTP/2 + Protocol Buffers**, not HTTP/1.1 with JSON.
- `asyncio` is not an API style. You can poll an async API from ordinary synchronous code.

## Quick self-check
<details><summary>Q1. `{"jsonrpc": "2.0", "method": "interfaces.list", "id": 12}` POSTed to `/api`: which style?</summary>RPC (JSON-RPC). The action is a named function in the body, sent to one endpoint.</details>
<details><summary>Q2. You get `202 Accepted` with a taskId. What next?</summary>GET `/dna/intent/api/v1/task/{taskId}` until `endTime` is set, check `isError`, then fetch the result. Don't resend the POST.</details>
<details><summary>Q3. Which two parts must every SOAP message have?</summary>Envelope and Body. The Header is optional and the Fault appears only on errors.</details>
<details><summary>Q4. CUCM AXL, NETCONF, Meraki, RESTCONF: which style is each?</summary>SOAP, RPC, REST, REST.</details>
<details><summary>Q5. A JSON-RPC request has no `id`. What does the server send back?</summary>Nothing. A request without an `id` is a notification, and the server must not reply.</details>

## Cheat lines to say out loud
- "Find the verb. If it's in the HTTP method, it's REST. If it's in the body, it's RPC. If it's wrapped in an Envelope, it's SOAP."
- "202 is a ticket number, not your order."
- "The task returns 200 the whole time. Wait for endTime, then check isError."
- "NETCONF is RPC on SSH 830; RESTCONF is REST; AXL is SOAP."
- "JSON-RPC hides its errors inside a 200."
