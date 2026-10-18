# T43 · Webhooks: essentials

> Blueprint 2.2 · Full note: [bee/T43-webhooks.md](../bee/T43-webhooks.md) · Teach-back 2026-10-25

## In one picture
![T43 at a glance: register once, event happens, platform POSTs to you, verify and ack, follow-up GET](../assets/T43/00-overview.png)
*Read the top row left to right as the life of one event (the numbers give the order, and the "who" line shows who is client and who is server at each step). The bottom row covers the comparison with polling, testing, retries and exam scenarios. Red boxes are exam traps.*

## The big idea
- With a normal API, your script asks and the platform answers. With a **webhook**, you leave your address with the platform once, and the platform calls *you* when something happens.
- Analogy: polling is walking to the front door every minute to see if anyone is there. A webhook is a doorbell. You do nothing until it rings.
- The platform "rings" by sending an **HTTP POST** with a JSON body to a URL you registered. That URL belongs to a small web server that you run.
- On the exam, you need to recognise the webhook pattern in a scenario, know the Webex registration fields, explain why the URL must be public, and explain why the app makes a follow-up GET. Your CBT course has no video for blueprint 2.2, so this page and the full note are your only coverage.

## What you need to know

### 1. What a webhook is, and why the roles flip
- A webhook is an **HTTP callback**. When an event happens, the service sends an HTTP POST to a URL you registered earlier. Webex defines it as "an HTTP callback, or an HTTP POST, to a specified URL that notifies your app when a particular activity or 'event' has occurred."
- People call it a **"reverse API"** because the usual direction flips:
  - When you **register** the webhook, you are the HTTP client, as normal.
  - When an event is **delivered**, the **platform is the HTTP client** and **your app is the HTTP server**. Your app listens on a port, receives a request, and returns a status code.
  - When you make the **follow-up GET**, you are the client again.
- It is **event-driven**: no event means no traffic at all.
- It is **near real time**, not instant. Meraki says an alert is sent on average within 90 seconds of the event, and some take up to about 10 minutes. Webex says some meeting-related data can lag the webhook (synced within 10 minutes for 99.5 % of cases).

![Animated webhook flow: register, idle, event, platform POSTs to your targetUrl, you verify and reply 200, follow-up GET, act](../assets/T43/09-webhook-flow.gif)
*Seven steps: register, wait with zero requests, the event happens, the platform POSTs to you, you verify and reply 200, you GET the details, you act. Your app never asks; it only listens.*

### 2. Webhook vs polling vs WebSocket
- **Polling** means your script asks "anything new?" on a timer. In the lab, 6 GETs in 6 seconds found only 2 events, so 4 calls were wasted.
  - Every empty answer still counts against your **rate limit**. If you poll faster to cut the delay, you burn your quota faster and eventually get `429`.
  - The delay can be up to one full polling interval.
  - Its upside: it only needs **outbound** access, so it works from behind NAT or a locked-down network.
- **Webhook** means the platform pushes one POST per event, plus one follow-up GET if you need details. Nothing is wasted. The cost is that you must run a reachable HTTPS listener and handle signatures, retries and duplicates.
- **WebSocket** (RFC 6455, awareness only) is one long-lived, two-way connection that the client opens. After that, either side can send at any time. It suits chat UIs and live dashboards.

| | Polling | Webhook | WebSocket |
|---|---|---|---|
| Who starts each exchange | your app, on a timer | the platform, once per event | your app opens it once, then both sides send |
| Wasted calls | many | none | none (keep-alives only) |
| Latency | up to one interval | near real time | real time |
| What your side needs | outbound access only | a public HTTPS endpoint | outbound access, and keep the socket up |

![Choose: polling if the platform can't reach you; WebSocket for a continuous two-way stream; webhook for "tell me when X happens"](../assets/T43/08-choose.png)
*The exam decision path: "reduce API calls" or "react as it happens" points to a webhook; "no inbound connections allowed" points to polling; "two-way, continuous" points to WebSocket.*

### 3. The three components
- **Event source**: the platform where things happen and which sends the notifications. Examples are Webex (messages, rooms, memberships, meetings), Meraki (network alerts), Catalyst Center (DNA Center) (assurance and system events) and GitHub/GitLab (push, merge request).
- **Target URL**: the address the source will POST to. You host it, and it must be reachable **from the source**.
  - Webex: the URL "must be publicly reachable and Internet-accessible by Webex."
  - Meraki: the URL must be **HTTPS** on a **public** server with a **valid certificate** signed by a globally trusted CA. Self-signed certificates are not supported.
  - So `127.0.0.1`, `localhost`, a private IP such as `192.168.x.x`, or a host behind NAT never receives anything from a cloud platform.
  - Your firewall or NAT must allow **inbound** HTTPS (443) to the receiver.
- **Receiver app**: the code behind the URL. It reads the body, verifies the signature, checks the shape, removes duplicates, replies 2xx, and then a background worker fetches details and acts.

![Components: event source, firewall/NAT allowing inbound 443, your public target URL, receiver and worker; the worker's follow-up GET goes back to the API](../assets/T43/10-components-arch.png)
*Blue arrows point from client to server. The delivery runs down (the platform is the client) and the follow-up GET runs back up (you are the client, using your own token). The firewall zone is the usual reason nothing arrives.*

### 4. Registering a webhook (Webex)
- Registration is an ordinary authenticated API call that you make **once**, not once per event: `POST https://webexapis.com/v1/webhooks` with `Authorization: Bearer <token>`.

| Field | Required? | Meaning | Example |
|---|---|---|---|
| `name` | yes | a label for you | `"netops room commands"` |
| `targetUrl` | yes | where the platform will POST | a public `https://` URL |
| `resource` | yes | the **noun** being watched, plural like the API name | `messages`, `rooms`, `memberships`, `attachmentActions`, `meetings` |
| `event` | yes | the **verb** that triggers it | `created`, `updated`, `deleted` (meetings also have `started`/`ended`) |
| `filter` | no | narrows the scope, usually a query parameter of `GET` on that resource; combine with `&` | `"roomId=..."` |
| `secret` | no | a shared secret the platform uses to sign every payload | `"s3cr3t-T43-demo"` |

- A **firehose** webhook uses `"event": "all"` for one resource, or `"resource": "all", "event": "all"` for all events on memberships, messages and rooms.
- The token needs **read scope** on the resource, for example `spark:messages_read` for a `messages` webhook.
- Webex says the token is only needed to **create** the webhook. As long as deliveries get a successful response, the webhook keeps running even after the token expires. Your follow-up GETs still need a valid token.
- The response is the webhook object with an `id` and `status: active`. Keep the ID so you can update or delete it. (The lab mock never echoes the `secret` back; whether real Webex does is ⚠ verify.)
- The lifecycle is ordinary REST CRUD: list (`GET /v1/webhooks`), read, update (`PUT /v1/webhooks/{id}`, for example a new `targetUrl` or `status: active`) and `DELETE`.
- Other Cisco platforms use the same idea with different names:
  - **Meraki**: add an "HTTP server" (`POST /networks/{networkId}/webhooks/httpServers` with `name`, `url`, optional `sharedSecret`), then pick it as an alert destination.
  - **Catalyst Center**: create a webhook destination (`/dna/intent/api/v1/event/webhook`), then an event subscription (`/dna/intent/api/v1/event/subscription/rest`). ⚠ verify these paths against your version.

### 5. The payload, the follow-up GET, and replying fast
- The POST body is an **envelope** plus a **`data`** object. The envelope `id` is the **webhook's** ID. `actorId` is who caused the event. `data.id` is the ID of the **resource** (for example the message).
- The Webex payload is **minimal on purpose**: it does not contain the message text. Room content is encrypted with keys only room members hold, and Webex did not have your token when it sent the notification.
  - To read the text, make a **follow-up GET** with your own token: `GET https://webexapis.com/v1/messages/{data.id}`.
  - A useful side effect: anyone who forges or intercepts a notification only gets IDs, not content.
  - Bots only see messages in which they are mentioned, so a bot's `messages` webhook only fires for those.
  - Meraki is the opposite. Its alert body is self-contained (`alertType`, `alertData`, `networkId`, `occurredAt` and so on), so you usually need no follow-up GET. "IDs only" is common, not universal.
- **Reply 2xx fast, then do the work in the background.** The sender holds the connection open until you answer, so your reply means "got it", not "done it". GitHub documents a hard limit of 10 seconds and recommends a queue.

![Payload then follow-up: POST with IDs only, receiver verifies and replies 200 immediately, queues, worker GETs the full message and acts](../assets/T43/04-payload-followup.png)
*Acknowledge first, work second. The 200 OK goes back before the follow-up GET even starts.*

- **Retries create duplicates, so make the receiver idempotent.** If you time out or return 5xx, the platform sends the **same event again**. Delivery is "at least once", not "exactly once".
  - The fix is to remember which IDs you have already handled and skip them.
  - Reply **200** to a duplicate, otherwise the platform keeps retrying it.
  - GitHub gives each delivery a unique `X-GitHub-Delivery` ID for this purpose. A real receiver stores handled IDs in a database or Redis.
- **Failing receivers get disabled.** Any non-2xx reply, or no reply within the timeout, counts as a failure. After enough failures, the webhook is switched off.
  - Webex: if it attempts 100 deliveries within five minutes and none get a 2xx, the webhook is disabled and **not** re-enabled automatically. You fix the receiver, then `PUT` `status: active`. ⚠ verify the threshold.
  - Meraki: disabled after consistent failure for more than 100 attempts in 24 hours. ⚠ verify.

### 6. Security: proving the POST really came from the platform
- Your target URL is public, so **anyone** can POST to it. Webex says IP allow-lists are not practical because it keeps adding infrastructure.
- The fix is a **shared secret plus an HMAC signature**:
  1. At registration, you send a `secret`. After that only you and the platform know it; it never travels with the events.
  2. For each delivery, the platform computes an HMAC of the raw body with the secret and puts it in a header. For Webex this is **`X-Spark-Signature`**, an **HMAC-SHA1** hex digest of the unmodified raw body.
  3. Your receiver computes the same HMAC over the bytes it received and compares the two. A match proves the sender had the secret (**origin**) and the body was not changed (**integrity**). A mismatch means reject with `401`.
- Newer Webex guides also list `X-Webex-Signature` (HMAC-SHA256/SHA512) "for supported webhook types". ⚠ verify which types send it. For the exam, `X-Spark-Signature` = HMAC-SHA1 is the classic answer.
- Rules the official guides spell out:
  - Hash the **raw request bytes before parsing**. If you parse and re-serialise the JSON, the spacing changes and the HMAC no longer matches.
  - Compare in **constant time** with `hmac.compare_digest`, never with `==`.
  - Look the header up case-insensitively, because it may arrive in lowercase over HTTP/2.
  - Use the platform's algorithm. SHA-256 over the same body gives a different digest.

```python
expected = hmac.new(SECRET, raw_body, hashlib.sha1).hexdigest()
ok = hmac.compare_digest(expected, received_signature)
```
*This is the whole check: HMAC-SHA1 of the raw bytes, then a constant-time compare.*

- **Meraki is weaker**: its `sharedSecret` travels **inside the JSON body** in plain text and you just compare it. That is a password check, not a signature, so it proves nothing about integrity. Meraki relies on HTTPS for confidentiality.
- **HMAC is not encryption.** It proves origin and integrity but hides nothing. HTTPS is what hides the content.
- After the signature passes, still **validate the shape** (return `400` if fields are missing) and treat any text you fetch as **untrusted user input**: never pass it to a shell or SQL.
- A captured genuine request still has a valid signature, so **dedupe on an ID** to defeat replays, and check timestamps where the platform signs one.

### 7. Testing tools and use cases
- The testing problem: your receiver runs on a laptop behind NAT, so a cloud platform cannot reach it.
- **ngrok** is a tunnel. The ngrok agent on your laptop opens an **outbound** connection to ngrok's edge and gets a **public HTTPS URL** that forwards to your local port. Command: `ngrok http 8144`. Register that public URL plus `/webhook` as your `targetUrl`.
  - The agent also has a local inspection API at `http://localhost:4040/api/tunnels`.
  - The free URL may change each run, so you update the webhook or re-register. ⚠ verify the current free-tier behaviour.
- **webhook.site / RequestBin** give you a hosted URL that only **displays** each incoming request's headers and body. No code is needed. Use it to see what a platform really sends. It runs none of your logic. Meraki's docs suggest webhook.site for testing.

![Testing: Webex POSTs to the ngrok edge, which forwards down the tunnel to the receiver; or to webhook.site just to inspect; a direct POST to 127.0.0.1 is unreachable](../assets/T43/11-testing-ngrok-arch.png)
*ngrok exposes your real app; webhook.site only shows the request. The red dashed line is why `127.0.0.1` as `targetUrl` receives nothing.*

- Typical use cases all follow the same shape: something changes on a platform, it tells your code, and your code acts.

| Use case | Event | What the receiver does |
|---|---|---|
| Webex bot (ChatOps) | `messages`/`created` | follow-up GET, parse the command, post a reply |
| Card button clicks | `attachmentActions`/`created` | GET the submitted inputs (⚠ verify path) |
| Meraki alerts | device down, settings changed | open a ticket or post to a Webex room |
| Catalyst Center events | e.g. device unreachable | open an incident, run remediation |
| CI/CD | GitHub/GitLab push or merge request | start a pipeline |
| Async job done | long task finished | fetch the result instead of polling a task ID |

## Exam traps (the ones that catch people)
- It looks like your app is the client, but **during delivery the platform is the HTTP client and your app is the server**. "Which side needs a listening port?" Yours.
- It looks like registration and delivery are the same POST, but **registration is your `POST /v1/webhooks`, done once with a token**, while delivery is **the platform's POST to your `targetUrl`, once per event, signed with the secret**.
- `resource` and `event` look interchangeable, but **`resource` is a plural noun (`messages`) and `event` is a verb (`created`)**. `"resource": "created"` is a classic distractor.
- "The bot gets the message ID but no text" looks like a bug, but it is **by design**: do a follow-up `GET /v1/messages/{data.id}`. The envelope `id` is the webhook ID, not the message ID.
- `X-Spark-Signature` looks like a token, but it is an **HMAC-SHA1 of the raw body** using the webhook secret. It is not base64 and not SHA-256.
- Returning `500` looks like a way to make the platform stop, but **any non-2xx or slow reply triggers retries**, which cause duplicate actions. Reply 200 fast, work in the background, and dedupe on ID.
- A webhook looks always better than polling, but **polling is the right answer when no inbound connection is allowed**, because a webhook needs a reachable URL.
- WebSocket sounds like webhook, but a **WebSocket is one persistent two-way connection the client opens**, while a webhook is a **separate HTTP POST per event that the server starts**.

## Quick self-check
<details><summary>Q1. A script polls every 10 s and keeps getting 429. What is the better design?</summary>Register a webhook so the platform pushes events; it removes the wasted "anything new?" calls.</details>
<details><summary>Q2. Which four fields are required to create a Webex webhook?</summary>`name`, `targetUrl`, `resource`, `event`. `filter` and `secret` are optional.</details>
<details><summary>Q3. A webhook points at `http://192.168.10.25:5000/events` and never receives anything. Why, and what is the test fix?</summary>A private IP cannot be reached by the cloud platform; use ngrok to get a public HTTPS URL for testing.</details>
<details><summary>Q4. One Meraki alert creates two tickets, and the receiver takes 15 s to reply. What two fixes?</summary>Reply 2xx immediately and do the work in a background worker, and skip alert IDs you have already processed. The slow reply caused a retry.</details>
<details><summary>Q5. Why must you verify the HMAC on the raw body and not on re-serialised JSON?</summary>Re-serialising changes the bytes (spacing), so the HMAC no longer matches even for a genuine request.</details>

## Cheat lines to say out loud
- "Polling is checking the door every minute; a webhook is a doorbell."
- "Register once as a client; receive every event as a server."
- "Webex sends IDs, not text, so I always do a follow-up GET with my own token."
- "Verify the HMAC on the raw bytes, say 200 fast, work later, and dedupe on the ID."
- "The target URL must be public HTTPS: ngrok to test, webhook.site to just look."
