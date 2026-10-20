# T09 · API styles: REST vs RPC, sync vs async: essentials

> Blueprint 2.8: compare API styles (REST, RPC, sync, async) · Full note: [bee/T09-api-styles-rest-vs-rpc-sync-vs-async.md](../bee/T09-api-styles-rest-vs-rpc-sync-vs-async.md) · Teach-back 2026-10-18

![T09 at a glance: REST vs RPC vs SOAP, sync vs async](../assets/T09/00-overview.png)

*Top table: the three API styles and how to spot each one on the wire. Bottom: sync vs async, with the Catalyst Center taskId steps numbered in order. Red boxes are exam traps.*

## 🧭 The big idea

This topic asks **two separate questions** about any API. Keep them apart: an API has one answer to each.

| | Question | Answer options | Analogy |
|---|---|---|---|
| 🔎 | **Where does the "verb" (the action) live?** | 🗄️ **REST** · 📞 **RPC** · 📋 **SOAP** | 🗄️ **REST is a filing cabinet.** Every drawer has a label (the URI, e.g. `/devices/1`). There are only a few standard things you can do to any drawer: look inside (GET), add (POST), replace (PUT), edit (PATCH), throw away (DELETE). The *drawer* changes; the *actions* are always the same five. 📞 **RPC is phoning a help desk.** You ask for a named service: "please run `getDevice` for device 1". Every request goes to the same phone number (one endpoint); only the service name changes. 📋 **SOAP is the same help-desk call, but on a strict official form.** Every request is the same XML envelope with fixed sections, checked against a rule book (the WSDL). |
| ⏳ | **Does the server make you wait for the answer?** | ☕ **synchronous** · 📟 **asynchronous** | ☕ **Synchronous is a coffee counter.** You order and stand there until the coffee is handed to you. 📟 **Asynchronous is a restaurant buzzer.** You order, you're handed a buzzer straight away (`202 Accepted` + a task ID), you go sit down, and you collect the food when it's ready (you poll, or it buzzes you). |

- 🧩 Example: Catalyst Center (DNA Center) is **REST** and, for long jobs, **asynchronous**. Both labels apply at once.
- 🎯 **What the exam asks:** recognise the style from a snippet, explain what a `202` means and what to do next, and match Cisco APIs to their style. The blueprint verb is "compare", so it's recognition, not building.

## 🟥 Must know

### 1. 🗄️ REST: the URL is a thing, the HTTP method is the action

> 💡 **REST** (Representational State Transfer) is **resource-centric**. The URL names a *thing* (a noun); the HTTP method says *what to do* to it.

```
GET    /api/v1/devices/1     → read device 1
PUT    /api/v1/devices/1     → replace device 1
DELETE /api/v1/devices/1     → delete device 1   (same URL, different method)
```

| Property | What it means |
|---|---|
| 🔢 URLs and verbs | many URLs (one per resource), but only **five verbs**: GET, POST, PUT, PATCH, DELETE |
| 🚦 **The result is in the HTTP status code** | ask for device 99 that doesn't exist → `404 Not Found` in the status line. You can tell success or failure without reading the body. |
| 🧠 **Stateless** | the server keeps no memory between calls, so you send your token on **every** request |
| 📄 Format | usually JSON, but REST doesn't require any format |
| 🧩 **Cisco REST APIs** | Meraki Dashboard · Catalyst Center (DNA Center) Intent API · Webex · ACI (APIC) · SD-WAN Manager (vManage) · Secure Firewall Management Center (FMC) · **RESTCONF** (REST access to YANG data on a device) |

### 2. 📞 RPC: you call a named function on the server

> 💡 **RPC** (Remote Procedure Call) is **action-centric**. The idea: calling a function on another machine should feel like calling a local function, `getDevice(id=1)`.

- The function name travels **in the body** (or sometimes **in the URL**). Requests usually go to **one endpoint**, nearly always with **POST**.

```http
POST /jsonrpc
Content-Type: application/json

{"jsonrpc": "2.0", "method": "getDevice", "params": {"id": 1}, "id": 7}
```

| Part | Meaning |
|---|---|
| `"method": "getDevice"` | the action: the verb lives here, not in the HTTP method |
| `"params"` | holds the function's arguments |
| `"id": 7` | lets the client match the reply to this request |

**🚰 HTTP is just a pipe.** Even when the call fails, the server usually replies `200 OK` and puts the error **in the body**:

```json
{"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": 7}
```

> 🎯 So with RPC you check the body for `"error"`, not the status code.

**📡 NETCONF is RPC.** Every NETCONF operation is an `<rpc>` element, and the operation name is the child element:

```xml
<rpc message-id="101" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <get-config>                    <!-- the action: a named operation -->
    <source><running/></source>
  </get-config>
</rpc>
```

- Sent over **SSH port 830**. The reply is `<rpc-reply message-id="101">` with the same ID.

**The classic exam pair:** NETCONF and RESTCONF both work on the same YANG data.

| 📞 NETCONF | 🗄️ RESTCONF |
|---|---|
| **RPC** (named `<rpc>` operations) | **REST** (URLs + HTTP methods) |

Other RPC styles you may see:

| RPC style | What it is |
|---|---|
| **JSON-RPC** | above |
| **NX-API** on Nexus switches | `"method": "cli"` with a `show` command |
| **gRPC** | Google's binary RPC, used for streaming telemetry |

### 3. 📋 SOAP: RPC on a strict XML form

> 💡 **SOAP** (Simple Object Access Protocol) is a W3C **protocol**: it has a fixed specification. REST, by contrast, is a **style** (a set of guidelines). SOAP messages are **always XML**.

- Like RPC, the action is a named operation. Unlike plain RPC, every message is wrapped in the same envelope:

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">   <!-- mandatory root -->
  <soapenv:Header/>                                                             <!-- optional -->
  <soapenv:Body>                                                                <!-- mandatory -->
    <ns:getPhone>                                                               <!-- the operation (the verb) -->
      <name>SEP001122334455</name>                                              <!-- its argument -->
    </ns:getPhone>
  </soapenv:Body>
</soapenv:Envelope>
```

| | |
|---|---|
| 📮 Transport | sent by **HTTP POST**, usually to one URL |
| 💥 Errors | **errors come back as HTTP `500`** with a `<Fault>` element inside the Body |
| 🧩 **Cisco example** | CUCM **AXL** (provisioning phones and users) is SOAP. CUCM's UDS is the REST one. |

![Same lookup in three styles](../assets/T09/01-same-call-three-styles.png)

*The same "get device 1" question in REST, JSON-RPC and SOAP. Only REST puts the verb in the HTTP method and uses status codes for the outcome.*

### 4. 🔎 How to tell them apart from a snippet

| | 🗄️ REST | 📞 RPC | 📋 SOAP |
|---|---|---|---|
| The verb (action) is… | the **HTTP method** | a **function name** in the body or URL | an **operation element** inside the XML Body |
| Example | `DELETE /api/v1/devices/1` | `"method": "getDevice"` · `POST /api/runCommand` | `<soapenv:Body><getPhone>` |
| Endpoints | **many** URLs (one per resource) | usually **one** | usually **one** |
| Errors are in… | the **status code** (`404`) | the **body** (often under `200 OK`) | a `<Fault>` (HTTP `500`) |
| Format | any (mostly JSON) | JSON / XML / binary | **XML only** |
| Cisco | Meraki · Catalyst Center · Webex · ACI · FMC · RESTCONF | NETCONF · NX-API | CUCM AXL |

**Three-step check:**

1. **Look at the body first.** `<soapenv:Envelope>` → SOAP. `<rpc>` → NETCONF (RPC). `"jsonrpc"` or `"method"` → RPC.
2. **Then look at the URL.** A verb in the path (`/runCommand`, `/getDevice`) → RPC-style.
3. **A noun in the URL plus a meaningful HTTP method** (`DELETE /devices/1`) → REST.

> 🎯 **JSON doesn't make it REST.** `POST /api/v1/runCommand` with `{"cmd": "show ip int brief"}` is JSON over HTTPS, but the verb is in the URL, so it's **RPC-style**.

![Identify the API style](../assets/T09/06-identify-style.png)

*The decision flow: body first, then the URL and method.*

### 5. ☕ Synchronous: you wait on the line

> 💡 **Synchronous** = you send a request, then **wait** until the full answer comes back on the same call. Every ordinary `requests.get()` is synchronous.

| ✅ Good | ❌ Bad for long jobs |
|---|---|
| simple to code. The result is just the return value; the next line of your script can use it straight away. No IDs, no polling. | 🐢 if the work takes 90 seconds, your script is stuck for 90 seconds doing nothing. |
| | ⏱️ if the work takes longer than the **timeout** (yours, `requests.get(..., timeout=30)`, or a proxy's), the client gives up and gets **nothing back**, even though the server carries on and finishes the job. A proxy in the middle reports this as `504 Gateway Timeout`. |
| | ➕ it adds up: 500 devices × 1.5 s each = 12.5 minutes of waiting. |

### 6. 📟 Asynchronous: take a ticket, check back later

> 💡 **Asynchronous** = the server **accepts** the job and replies **at once**, before the work is done. The typical reply is:

```http
HTTP/1.1 202 Accepted
Content-Type: application/json

{"response": {"taskId": "4a1d7c2e-…", "url": "/api/v1/task/4a1d7c2e-…"}, "version": "1.0"}
```

| Part | Meaning |
|---|---|
| **`202 Accepted`** | means "I've queued your job". It does **not** mean the job is done or succeeded. |
| **task ID** (or status URL) | your buzzer: you use it to ask "is it ready yet?" |

**Two ways to get the result:**

| | 🔁 Polling | 🪝 Webhook (callback) |
|---|---|---|
| How | your script sends `GET` to the status URL every few seconds until it says "done" | you give the server a URL beforehand; it sends a `POST` to that URL when the job finishes |
| ✅ Pro | simple, works through firewalls | no wasted calls |
| ❌ Con | uses up calls (watch rate limits) | you need a listener the server can reach (see T43) |

- 🚀 **Why bother:** while the job runs, your script is free. It can start jobs on 200 other switches instead of waiting on one.

| ☕ Use **synchronous** when… | 📟 Use **asynchronous** when… |
|---|---|
| reading one device, listing VLANs, getting a token | provisioning a site, pushing a template to 200 switches |
| making a small config change on one device | upgrading images (SWIM), running device discovery |
| you need the answer before the next line runs | the job may take longer than any timeout |

### 7. 🎫 Catalyst Center (DNA Center) taskId flow

> 💡 Catalyst Center's long-running Intent API calls (`POST`/`PUT`/`DELETE`) are asynchronous. Example: run `show version` on a device with Command Runner.

| Step | Call | What you read in the reply |
|---|---|---|
| 1 | `POST /dna/intent/api/v1/network-device-poller/cli/read-request` | `202` + `response.taskId` |
| 2 | `GET /dna/intent/api/v1/task/{taskId}` | **no `endTime` field** = still running → wait and repeat |
| 3 | same `GET`, until `endTime` appears | `isError: false` = ✅ success · `isError: true` = ❌ failed, read `failureReason` |
| 4 | `GET /dna/intent/api/v1/file/{fileId}` | the actual command output |

> 🪤 The task lookup in step 2 returns **`200 OK` the whole time**. That `200` means "I found your task", not "your job finished". Only `endTime` tells you it's done.
>
> 🎯 **Sequence-diagram questions** (T47) draw exactly this flow: authenticate → POST → 202 → poll task → GET result. "What's the next call after the 202?" → GET the task URL.

![Animated async taskId flow](../assets/T09/07-async-task.gif)

*Step by step: POST, 202 + taskId, poll with no endTime, poll with endTime set, then GET the file.*

## ⚠️ Exam traps

| ❌ Looks like… | ✅ Actually… |
|---|---|
| `202` means the job is done | **`202` is a ticket, not a result.** It means accepted and queued. Your next step is to poll the task. Resending the POST queues a **second** copy of the job. |
| `200` on the task URL means the job finished | **The task URL says `200` while the job is still running.** Done = `endTime` is present; then check `isError`. |
| `200 OK` from an RPC call means success | **RPC hides errors inside `200 OK`.** Check the body for `"error"`, not the status code. |
| JSON over HTTP is REST | **JSON over HTTP isn't automatically REST.** A verb in the URL or a `"method"` field = RPC-style. |
| NETCONF and RESTCONF are the same style | **NETCONF = RPC (SSH 830), RESTCONF = REST, CUCM AXL = SOAP.** The names look alike; the styles don't. |

<details><summary><b>🟨 Should know (second pass)</b></summary>

### 📋 SOAP parts

| Element | Required? | Role |
|---|---|---|
| `<Envelope>` | ✅ mandatory root | its namespace shows the SOAP version |
| `<Header>` | ❌ **optional** | carries metadata such as security credentials |
| `<Body>` | ✅ **mandatory** | holds the operation and its arguments |
| `<Fault>` | only on errors | appears **inside the Body** |

- 📖 **WSDL** (Web Services Description Language) = a separate XML file listing every operation and its input/output types. It's the SOAP "rule book": tools generate client code from it, and requests that don't match it are rejected. It is **not** sent with each message.
- 📨 **SOAP headers on the wire:** `Content-Type: text/xml` (SOAP 1.1) plus a `SOAPAction` header naming the operation.

### 📟 Async API ≠ async code

| Async *API* | Async *code* (Python's `asyncio`) |
|---|---|
| about how the server replies (202 + task) | about your script not blocking while it waits |

- You can poll an async API from ordinary synchronous code.

### 📞 More RPC flavours

| | What it is |
|---|---|
| **gRPC** | Google's RPC framework: binary **Protocol Buffers** over **HTTP/2**, with the functions defined in a `.proto` file. Used for model-driven telemetry. |
| **NX-API** (Nexus) | sends CLI commands over HTTPS. One of its message formats is JSON-RPC: `{"jsonrpc": "2.0", "method": "cli", "params": {"cmd": "show version", "version": 1}, "id": 1}` |

### ⚖️ Polling vs webhook trade-off

| 🔁 Polling | 🪝 Webhook |
|---|---|
| simple and works through NAT but costs calls | instant but needs a reachable HTTPS listener |

</details>

> 📚 **Recognise only, details in the full note:** JSON-RPC error codes (`-32601` etc.) and "notifications", SOAP 1.1 vs 1.2 fault fields, `.proto` syntax, `asyncio` keywords, decoding Catalyst Center's `progress` field.

## ✍️ Quick self-check
<details><summary>Q1. <code>{"jsonrpc": "2.0", "method": "interfaces.list", "id": 12}</code> POSTed to <code>/api</code>: which style?</summary>RPC (JSON-RPC). The action is a named function in the body, sent to one endpoint.</details>
<details><summary>Q2. You get <code>202 Accepted</code> with a taskId. What next?</summary>GET <code>/dna/intent/api/v1/task/{taskId}</code> until <code>endTime</code> is set, check <code>isError</code>, then fetch the result. Don't resend the POST.</details>
<details><summary>Q3. CUCM AXL, NETCONF, Meraki, RESTCONF: which style is each?</summary>SOAP, RPC, REST, REST.</details>
<details><summary>Q4. <code>POST /api/v1/runCommand</code> with a JSON body: REST?</summary>No, RPC-style. The verb (<code>runCommand</code>) is in the URL, not the HTTP method.</details>
<details><summary>Q5. A JSON-RPC call returns <code>200 OK</code>. Did it succeed?</summary>Not necessarily. RPC puts errors in the body, so check for an <code>"error"</code> member.</details>
<details><summary>Q6. Which two parts must every SOAP message have?</summary>Envelope and Body. The Header is optional; the Fault appears only on errors.</details>
<details><summary>Q7. A firmware upgrade on 200 switches: sync or async, and why?</summary>Async. The job takes far longer than any HTTP timeout, and the script should be free to track all 200 in parallel.</details>

## 🗣️ Say it out loud
- 🗄️📞📋 "Find the verb. In the HTTP method: REST. In the body: RPC. Wrapped in an Envelope: SOAP."
- 📟 "202 is a buzzer, not your food."
- 🎫 "The task says 200 the whole time. Wait for endTime, then check isError."
- 📡 "NETCONF is RPC on SSH 830; RESTCONF is REST; AXL is SOAP."
- 📞 "RPC hides its errors inside a 200."
