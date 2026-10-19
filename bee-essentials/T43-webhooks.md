# T43 · Webhooks: essentials

> Blueprint 2.2: webhook usage patterns · Full note: [bee/T43-webhooks.md](../bee/T43-webhooks.md) · Teach-back 2026-10-25

![T43 at a glance: register once, event happens, platform POSTs to you, verify and ack, follow-up GET](../assets/T43/00-overview.png)

*Read the top row left to right as the life of one event (the numbers give the order, and the "who" line shows who is client and who is server at each step). The bottom row covers the comparison with polling, testing, retries and exam scenarios. Red boxes are exam traps.*

## The big idea
- With a normal API, **your script asks** and the platform answers. With a **webhook**, you leave your address with the platform **once**, and the platform **calls you** when something happens. The topic answers three questions:
  - **How do I get told about events** without asking over and over? → register a webhook.
  - **What arrives, and what do I do with it?** → an HTTP POST with a JSON body; verify it, reply 200 fast, then fetch the details.
  - **What breaks it?** → an unreachable URL, slow or failing replies (retries, duplicates), forged requests.
- **Analogy: a doorbell.**
  - **Polling** is walking to the front door every minute to see if anyone is there. Most trips find nobody.
  - A **webhook** is a doorbell. You do nothing until it rings.
  - The platform "rings" by sending an **HTTP POST** with a JSON body to a URL you registered. That URL belongs to a small web server that **you** run.
- **What the exam asks:** recognise the webhook pattern in a scenario ("notify the application when…", "instead of repeatedly querying", "reduce API calls", "callback URL"), know the Webex registration fields, explain why the URL must be public, and explain why the app makes a follow-up GET. CBT has no video for blueprint 2.2, so this page and the full note are your only coverage.

## 🟥 Must know

### 1. What a webhook is, and why the roles flip
- A webhook is an **HTTP callback**: when an event happens, the service sends an **HTTP POST** to a URL you registered earlier.
  - Webex's definition: "an HTTP callback, or an HTTP POST, to a specified URL that notifies your app when a particular activity or 'event' has occurred."
- People call it a **"reverse API"** because the usual direction flips. Track who is client and who is server at each step:

| Step | Who is the HTTP client | Who is the HTTP server | How often |
|---|---|---|---|
| 1. **Register** (`POST /v1/webhooks`) | **your app** | the platform | once |
| 2. **Deliver** (`POST <targetUrl>`) | **the platform** | **your app** (listens on a port) | once per event |
| 3. **Follow-up GET** (`GET /v1/messages/{id}`) | **your app** | the platform | once per event, if you need details |

- **Analogy: leaving your phone number with a shop.** You call them once to say "ring me when my order arrives" (register). Then **they** call **you** (deliver). Then you call back to ask what exactly arrived (follow-up GET).
- **Event-driven:** no event means **no traffic at all**.
- **Near real time, not instant.** Real platforms add some delay (see Should know), so the exam wording is "near real time".

![Animated webhook flow: register, idle, event, platform POSTs to your targetUrl, you verify and reply 200, follow-up GET, act](../assets/T43/09-webhook-flow.gif)

*Seven steps: register, wait with zero requests, the event happens, the platform POSTs to you, you verify and reply 200, you GET the details, you act. Your app never asks; it only listens.*

### 2. Webhook vs polling: when each one is right
- **Polling** = your script asks "anything new?" on a timer.
  - In the full note's lab, **6 GETs in 6 seconds** found only **2 events**: 4 calls wasted.
  - **Every empty answer still counts against your rate limit.** Poll faster to cut the delay and you burn quota faster, until you get `429` (T08).
  - **Delay:** an event is only noticed at the next poll, so up to one full interval late.
  - **Upside:** it needs **outbound access only**, so it works from behind NAT or a locked-down network.
- **Webhook** = the platform pushes **one POST per event**, plus one follow-up GET if you need details. Nothing is wasted.
  - **Cost:** you must run a **reachable HTTPS listener**, and handle signatures, retries and duplicates.
- **Analogy:** polling is refreshing your parcel-tracking page every minute; a webhook is the courier texting you when it's delivered. The text only works if the courier has a number that reaches you.
- **The exam decision:**
  - "reduce API calls" / "react as it happens" → **webhook**.
  - "no inbound connections allowed to the app" → **polling** (a webhook is impossible without reachability).

![Choose: polling if the platform can't reach you; WebSocket for a continuous two-way stream; webhook for "tell me when X happens"](../assets/T43/08-choose.png)

*The exam decision path: "reduce API calls" or "react as it happens" points to a webhook; "no inbound connections allowed" points to polling; "two-way, continuous" points to WebSocket.*

- **Summary:**

| | Polling | Webhook |
|---|---|---|
| Who starts each exchange | your app, on a timer | the platform, once per event |
| Wasted calls | many (4 of 6 in the lab) | none |
| Latency | up to one interval | near real time |
| What your side needs | outbound access only | a public HTTPS endpoint |

### 3. The three components, and why the URL must be public
- **① Event source:** the platform where things happen and which sends the notifications. Webex (messages, rooms, memberships, meetings), Meraki (network alerts), Catalyst Center (DNA Center) (assurance and system events), GitHub/GitLab (push, merge request).
- **② Target URL:** the address the source will POST to. **You host it**, and it must be **reachable from the source**.
  - Webex: the URL "must be publicly reachable and Internet-accessible by Webex."
  - Meraki: the URL must be **HTTPS** on a **public** server with a **valid certificate** signed by a globally trusted CA. **Self-signed certificates are not supported.**
  - So `127.0.0.1`, `localhost`, a private IP such as `192.168.10.25`, or a host behind NAT **never receives anything** from a cloud platform.
  - Your firewall or NAT must allow **inbound HTTPS (443)** to the receiver.
- **③ Receiver app:** the code behind the URL. In order, it:
  1. reads the raw body,
  2. verifies the signature (section 6),
  3. checks the shape,
  4. drops duplicates,
  5. replies 2xx,
  6. hands the event to a background worker, which fetches details and acts.
- **Analogy: a letterbox.** The postman (event source) can only deliver to a letterbox on the street (public URL). A letterbox inside your locked flat (`127.0.0.1`, private IP) never gets post, however good it is.

![Components: event source, firewall/NAT allowing inbound 443, your public target URL, receiver and worker; the worker's follow-up GET goes back to the API](../assets/T43/10-components-arch.png)

*Blue arrows point from client to server. The delivery runs down (the platform is the client) and the follow-up GET runs back up (you are the client, using your own token). The firewall zone is the usual reason nothing arrives.*

### 4. Registering a webhook (Webex)
- Registration is an **ordinary authenticated API call** you make **once**, not once per event.
- **Analogy: filling in a "notify me" form.** Your name on it (`name`), where to reach you (`targetUrl`), what you care about (`resource`), which change (`event`), optionally only one shop (`filter`), and a password you'll both recognise (`secret`).
- The full request, annotated:

```bash
curl --silent --request POST "https://webexapis.com/v1/webhooks" \
  --header "Authorization: Bearer $WEBEX_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"name":"T43 lab","targetUrl":"https://YOUR-NGROK-URL/webhook","resource":"messages","event":"created","filter":"roomId='"$ROOM_ID"'","secret":"s3cr3t-T43-demo"}'
```

  - `Authorization: Bearer $WEBEX_TOKEN` = your token, needed to **create** the webhook.
  - `"name"` = a label for you. **Required.**
  - `"targetUrl"` = where the platform will POST. A **public `https://`** URL. **Required.**
  - `"resource"` = the **noun** being watched, **plural** like the API name: `messages`, `rooms`, `memberships`, `attachmentActions`, `meetings`. **Required.**
  - `"event"` = the **verb** that triggers it: `created`, `updated`, `deleted` (meetings also have `started` / `ended`). **Required.**
  - `"filter"` = optional; narrows the scope, usually a query parameter of `GET` on that resource (e.g. `roomId=…`); combine several with `&`.
  - `"secret"` = optional; a shared secret the platform uses to **sign every payload** (section 6).
- **The reply** is the webhook object with an `id` and `"status": "active"`. Keep the `id` to update or delete it.
- **The token needs read scope** on the resource, e.g. `spark:messages_read` for a `messages` webhook.
- **The lifecycle is ordinary REST CRUD** on the `webhooks` resource: list (`GET /v1/webhooks`), read (`GET /v1/webhooks/{id}`), update (`PUT /v1/webhooks/{id}`, e.g. a new `targetUrl` or `status: active`), `DELETE /v1/webhooks/{id}` → `204`.
- **Bad registrations fail like any API call:** a missing `targetUrl` → `400 {'message': 'missing required field(s): targetUrl'}` in the lab.

![Registration sequence: POST /v1/webhooks with the six fields, 200 with an id; a missing targetUrl gives 400; list; delete gives 204](../assets/T43/03-registration.png)

*Registration is ordinary REST CRUD on a `webhooks` resource. Only the deliveries are "reverse".*

### 5. The payload, and the follow-up GET
- **The POST body = an envelope + a `data` object.** What the lab's platform sends (same shape as Webex):

```
{"id": "wh-0001",                       ← the WEBHOOK's ID (not the message!)
 "name": "netops room commands",
 "resource": "messages", "event": "created",
 "filter": "roomId=room-netops",
 "actorId": "person-alice",             ← who caused the event
 "data": {"id": "msg-0001",             ← the RESOURCE's ID: the message
          "roomId": "room-netops",
          "personEmail": "alice@example.com",
          "created": "2026-10-10T13:06:36.000Z"}}
```

  - **No `text` field.** The Webex payload is **minimal on purpose**.
- **Why no message text:** room content is encrypted with keys only room members hold, and Webex didn't have your token when it sent the notification.
  - Side effect: anyone who forges or intercepts a notification only gets **IDs, not content**.
- **The follow-up GET:** to read the text, call the API with **your own** token:

```
GET https://webexapis.com/v1/messages/{data.id}       ← data.id, not the envelope id
Authorization: Bearer <your bot or user token>
```

  - Lab: `GET /v1/messages/msg-0001` → `text='show ip interface brief'` → the bot acts on the command.
  - **Bots only see messages in which they are mentioned**, so a bot's `messages` webhook only fires for those.
- **Analogy: a parcel-collection card.** The card through your door says "parcel #1234 is waiting" but not what's in it. You take the card (the ID) to the depot with your ID (your token) to collect the contents.
- **"IDs only" is common, not universal.** Meraki's alert body is self-contained (`alertType`, `alertData`, `networkId`, `occurredAt`…), so it usually needs no follow-up GET.

### 6. Security: proving the POST really came from the platform
- **The problem:** your target URL is public, so **anyone** can POST to it. Webex says IP allow-lists aren't practical, because it keeps adding infrastructure.
- **The fix: a shared secret plus an HMAC signature.**
  1. At registration you send a `secret`. After that only you and the platform know it; **it never travels with the events**.
  2. For each delivery, the platform computes an HMAC of the **raw body** with the secret and puts it in a header. Webex: **`X-Spark-Signature`** = an **HMAC-SHA1** hex digest of the unmodified raw body.
  3. Your receiver computes the same HMAC over the bytes it received and compares. **Match** = the sender had the secret (**origin**) and the body wasn't changed (**integrity**). **Mismatch** = reject with `401`.
- **Analogy: a wax seal.** Only the sender has the stamp (secret). An intact seal proves who sent the letter and that nobody opened and changed it. It doesn't hide the letter: anyone can still read it (that's what HTTPS is for).
- The receiver's check, from the full note's lab:

```python
raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))       # 1. the RAW bytes, before parsing
received = self.headers.get("X-Spark-Signature")                        #    header lookup is case-insensitive
expected = hmac.new(SECRET, raw, hashlib.sha1).hexdigest()              # 2. same algorithm: HMAC-SHA1
if not hmac.compare_digest(expected, received or ""):                   # 3. constant-time compare, never ==
    return self.reply(401, "bad signature")
event = json.loads(raw)                                                 # 4. only NOW parse the JSON
```

- **Rules the official guides spell out:**
  - Hash the **raw request bytes before parsing**. Parse and re-serialise the JSON and the spacing changes, so the HMAC no longer matches (lab: raw bytes → `True`, re-serialised → `False`).
  - Compare in **constant time** with `hmac.compare_digest`, never `==`.
  - Look the header up **case-insensitively**: it may arrive in lowercase over HTTP/2.
  - Use the **platform's algorithm**. SHA-256 over the same body gives a different digest.
- **Proof from the lab's curl drill:** a correctly signed body → `200`; the same body with **one byte changed** and the old signature → `401`.
- **HMAC is not encryption.** It proves origin and integrity but hides nothing. **HTTPS** hides the content.
- **After the signature passes:** still validate the shape (`400` if fields are missing), and treat any text you fetch as **untrusted user input** (never pass it to a shell or SQL).

![HMAC verification: platform and receiver both compute HMAC-SHA1 over the raw body with the shared secret; compare_digest equal means process, different means 401](../assets/T43/05-hmac-verify.png)

*The secret is shared once (at registration). Every delivery carries only the signature. Anything that changes the bytes (wrong secret, tampering, re-serialised JSON) fails the compare.*

### 7. Reply 200 fast, and survive retries
- **The sender holds the connection open until you answer**, so your reply means "**got it**", not "done it".
  - GitHub documents a hard limit of **10 seconds** and recommends a queue.
- **The pattern:** cheap checks → put the event on a queue → `return 200` → a background worker does the follow-up GET and the action.
- **Analogy: a restaurant till.** The cashier says "order received" and hands you a ticket straight away; the kitchen cooks afterwards. If the cashier made you wait while they cooked, the queue would give up and leave.
- **Retries create duplicates.** A non-2xx reply, or no reply within the timeout, counts as a **failure**, and the platform sends the **same event again**. Delivery is **"at least once"**, not "exactly once".
  - Lab: the receiver did 4 s of work before replying; the platform's timeout was 3 s, so it **retried**. Without a dedupe check, `ACTION: run 'show ip interface brief'` ran **twice** for **one** message: the "duplicate ticket" bug.
- **The fix: an idempotent receiver.** Remember which IDs you've already handled and skip them:

```python
with lock:
    duplicate = msg_id in seen          # seen = set of data.id values already accepted
    seen.add(msg_id)
if duplicate:
    return self.reply(200, "duplicate") # reply 200 to a duplicate, or the platform keeps retrying
jobs.put(event)                         # hand off to the background worker
return self.reply(200, "ok")            # ack fast
```

  - A real receiver stores handled IDs in a database or Redis, not in memory. GitHub gives each delivery a unique `X-GitHub-Delivery` ID for this.
  - Deduping on ID also defeats **replays**: a captured genuine request still has a valid signature (lab: replay → `duplicate -> HTTP 200`, no second action).
- **Failing receivers get disabled.** After enough failures in a row, the platform switches the webhook off (`status: inactive`), and it does **not** fix itself. Fix the receiver, then (Webex) `PUT` `status: active`.

![Payload then follow-up: POST with IDs only, receiver verifies and replies 200 immediately, queues, worker GETs the full message and acts](../assets/T43/04-payload-followup.png)

*Acknowledge first, work second. The 200 OK goes back before the follow-up GET even starts.*

![Retries and idempotency: 500 twice then 200; a slow reply times out so the same data.id is retried and the receiver dedupes it; receiver down leads to the webhook being disabled](../assets/T43/06-retries-idempotency.png)

*A: a crashed receiver gets retried with backoff. B: a slow receiver is treated as failed even though it was working, so the retry must be deduped. C: an unreachable receiver eventually gets the webhook disabled.*

### 8. Testing a receiver that lives on your laptop
- **The problem:** your receiver runs on a laptop behind NAT, so a cloud platform can't reach it (section 3).
- **ngrok** = a **tunnel**. The ngrok agent on your laptop opens an **outbound** connection to ngrok's edge and gets a **public HTTPS URL** that forwards to your local port:

```bash
ngrok http 8144      # public https URL → forwards to 127.0.0.1:8144; register <that URL>/webhook as targetUrl
```

  - Works through NAT because the tunnel is opened **outbound**.
  - The agent has a local inspection API at `http://localhost:4040/api/tunnels`.
  - The free URL may change each run, so update the webhook (`PUT /v1/webhooks/{id}`) or re-register ⚠ verify the current free-tier behaviour.
- **webhook.site / RequestBin** = a hosted URL that only **displays** each incoming request's headers and body. **No code needed.** Use it to see what a platform really sends. It runs **none** of your logic and makes no follow-up GET. Meraki's docs suggest webhook.site for testing.
- **Analogy:** ngrok is a mail-forwarding service to your real flat (your app runs). webhook.site is a glass letterbox: you can see the letter, but nobody opens or answers it.

![Testing: Webex POSTs to the ngrok edge, which forwards down the tunnel to the receiver; or to webhook.site just to inspect; a direct POST to 127.0.0.1 is unreachable](../assets/T43/11-testing-ngrok-arch.png)

*ngrok exposes your real app; webhook.site only shows the request. The red dashed line is why `127.0.0.1` as `targetUrl` receives nothing.*

## Exam traps
- **Roles flip.** During delivery the **platform is the HTTP client** and **your app is the server**. "Which side needs a listening port?" Yours. Registration (your `POST /v1/webhooks`, once, with a token) ≠ delivery (the platform's POST to `targetUrl`, once per event, signed).
- **`resource` is a plural noun (`messages`), `event` is a verb (`created`).** `"resource": "created"` is a classic distractor. Required: `name`, `targetUrl`, `resource`, `event`; optional: `filter`, `secret`.
- **"The bot gets the message ID but no text" is by design.** Do a follow-up `GET /v1/messages/{data.id}` with your own token. The envelope `id` is the **webhook** ID.
- **`X-Spark-Signature` = HMAC-SHA1 of the raw body** with the webhook secret. Not a token, not base64, not SHA-256. Verify before parsing, with `hmac.compare_digest`.
- **Any non-2xx or slow reply triggers retries**, which cause duplicate actions. Reply 200 fast, work in the background, dedupe on ID. Returning `500` doesn't make the platform stop.
- **A private or `localhost` `targetUrl` never gets deliveries.** Test with ngrok. And **polling is right when no inbound connection is allowed.**

<details><summary><b>🟨 Should know (second pass)</b></summary>

- **WebSocket (RFC 6455, awareness only):** one **long-lived, two-way connection** that the **client opens** (`ws://` / `wss://`, starting as an HTTP `Upgrade`). After that, either side can send at any time. Suits chat UIs and live dashboards. No public inbound URL needed, but the connection has to stay up.
  - **WebSocket ≠ webhook:** WebSocket = one persistent connection the client opens. Webhook = a separate HTTP POST per event that the server starts.

| | Polling | Webhook | WebSocket |
|---|---|---|---|
| Who starts each exchange | your app, on a timer | the platform, once per event | your app opens it once, then both sides send |
| Wasted calls | many | none | none (keep-alives only) |
| Latency | up to one interval | near real time | real time |
| What your side needs | outbound access only | a public HTTPS endpoint | outbound access, and keep the socket up |

- **How "near" is near real time:** Meraki says an alert is sent on average within 90 seconds of the event, and some take up to about 10 minutes ⚠ verify. Webex says some meeting-related data can lag the webhook (synced within 10 minutes for 99.5 % of cases).
- **Firehose webhooks:** `"event": "all"` for one resource, or `"resource": "all", "event": "all"` for all events on memberships, messages and rooms. Needs read scopes for each resource.
- **Token lifetime:** Webex says the token is only needed to **create** the webhook. As long as deliveries get a successful response, the webhook keeps running even after the token expires. Your follow-up GETs still need a valid token.
- **Auto-disable thresholds** (numbers change):
  - Webex: 100 delivery attempts within five minutes with no 2xx → disabled, **not** re-enabled automatically ⚠ verify the threshold.
  - Meraki: disabled after consistent failure for more than 100 attempts in 24 hours ⚠ verify.
- **Meraki's `sharedSecret` is weaker than an HMAC:** it travels **inside the JSON body** in plain text and you just compare it. That's a password check, not a signature, so it proves nothing about integrity. Meraki relies on HTTPS for confidentiality.
- **Newer Webex header:** `X-Webex-Signature` (HMAC-SHA256/SHA512) "for supported webhook types" ⚠ verify which types send it. For the exam, `X-Spark-Signature` = HMAC-SHA1 is the classic answer.
- **Other Cisco platforms, same idea:**
  - **Meraki:** add an "HTTP server" (`POST /networks/{networkId}/webhooks/httpServers` with `name`, `url`, optional `sharedSecret`), then pick it as an alert destination.
  - **Catalyst Center (DNA Center):** create a webhook destination (`/dna/intent/api/v1/event/webhook`), then an event subscription (`/dna/intent/api/v1/event/subscription/rest`) ⚠ verify these paths against your version.
- **Use cases** (all the same shape: something changes, the platform tells your code, your code acts):

| Use case | Event | What the receiver does |
|---|---|---|
| Webex bot (ChatOps) | `messages`/`created` | follow-up GET, parse the command, post a reply |
| Card button clicks | `attachmentActions`/`created` | GET the submitted inputs (⚠ verify path) |
| Meraki alerts | device down, settings changed | open a ticket or post to a Webex room |
| Catalyst Center events | e.g. device unreachable | open an incident, run remediation |
| CI/CD | GitHub/GitLab push or merge request | start a pipeline |
| Async job done | long task finished | fetch the result instead of polling a task ID |

</details>

> **Recognise only, details in the full note:** the full Webex envelope fields (`orgId`, `appId`, `ownedBy`, `createdBy`), whether Webex echoes `secret` back (⚠ verify), the `webexpythonsdk` `api.webhooks.create(...)` signature, Meraki `payloadTemplate`, ngrok's `localhost:4040` API detail, signing with `openssl dgst -sha1 -hmac`, `printf '%s'` vs `echo` when signing, the lab's retry schedule (teaching values only).

## Quick self-check
<details><summary>Q1. A script polls every 10 s and keeps getting 429. What is the better design?</summary>Register a webhook so the platform pushes events; it removes the wasted "anything new?" calls.</details>
<details><summary>Q2. Which four fields are required to create a Webex webhook?</summary><code>name</code>, <code>targetUrl</code>, <code>resource</code>, <code>event</code>. <code>filter</code> and <code>secret</code> are optional.</details>
<details><summary>Q3. A webhook points at <code>http://192.168.10.25:5000/events</code> and never receives anything. Why, and what is the test fix?</summary>A private IP cannot be reached by the cloud platform; use ngrok to get a public HTTPS URL for testing.</details>
<details><summary>Q4. One Meraki alert creates two tickets, and the receiver takes 15 s to reply. What two fixes?</summary>Reply 2xx immediately and do the work in a background worker, and skip alert IDs you have already processed. The slow reply caused a retry.</details>
<details><summary>Q5. Why must you verify the HMAC on the raw body and not on re-serialised JSON?</summary>Re-serialising changes the bytes (spacing), so the HMAC no longer matches even for a genuine request.</details>
<details><summary>Q6. A Webex bot's receiver gets <code>"data": {"id": "msg-0001", …}</code> but no message text. What does it do next?</summary><code>GET https://webexapis.com/v1/messages/msg-0001</code> with the bot's own token. The payload carries IDs only, by design.</details>
<details><summary>Q7. During a delivery, which side is the HTTP client and which is the server?</summary>The platform is the client (it sends the POST); your app is the server (it listens on a port and returns a status code).</details>

## Say it out loud
- "Polling is checking the door every minute; a webhook is a doorbell."
- "Register once as a client; receive every event as a server."
- "Webex sends IDs, not text, so I always do a follow-up GET with my own token."
- "Verify the HMAC on the raw bytes, say 200 fast, work later, and dedupe on the ID."
- "The target URL must be public HTTPS: ngrok to test, webhook.site to just look."
