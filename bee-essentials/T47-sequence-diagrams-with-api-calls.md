# T47 · Sequence diagrams with API calls: essentials

> Blueprint 5.14 · Full note: [bee/T47-sequence-diagrams-with-api-calls.md](../bee/T47-sequence-diagrams-with-api-calls.md) · Teach-back 2026-10-25

## In one picture
![T47 at a glance: notation, frames, auth, async, webhook and reading flows](../assets/T47/00-overview.png)
*Six panels, one per concept group. Read each mini diagram top to bottom: the black numbers are the order of the arrows, solid lines are requests, dashed lines are responses, and yellow boxes are frames. Red boxes are exam traps.*

## The big idea
- A **sequence diagram** shows **who talks to whom, and in what order**. For APIs, it shows which system calls which endpoint and what comes back.
- Analogy: it is like a comic strip of a phone conversation, read from top to bottom. Each person has a column, and each speech bubble is an arrow from one column to another.
- Every HTTP call you write with `requests` becomes two arrows: the request going out and the response coming back. If you can read a diagram as code, you can answer the exam questions.
- Blueprint 5.14 says "Interpret a sequence diagram that includes API calls". Expect "what is arrow N?", "put these calls in order", and "spot the missing step". Your CBT course has no 5.14 video, so this page and the full note are your coverage.

## What you need to know

### 1. The basic notation: boxes, lifelines, arrows
- **Participants** are the boxes along the top, one per system: your script, an auth server, a controller (Catalyst Center (DNA Center), SD-WAN Manager, the Meraki cloud), a device, or a webhook receiver. A stick figure (`actor`) is a human, and means the same thing.
- The **left-to-right order of the boxes means nothing**. The author just chose it.
- Each box has a **lifeline**: the vertical, often dashed, line underneath it. It represents that participant existing over time.
- **Time runs from top to bottom.** An arrow lower on the page happens later.

| Looks like | Meaning | In an API diagram | Mermaid syntax |
|---|---|---|---|
| solid line, **filled** arrowhead | synchronous call | a request: method + URL | `A->>B: label` |
| **dashed** line | reply message | a response: status code + data | `B-->>A: label` |
| solid line, **open** arrowhead | asynchronous message (the sender does not wait) | fire-and-forget event, push, webhook | `A-)B: label` |
| arrow from a box back to itself | self-call | local processing, such as parsing JSON | `A->>A: label` |

- Requests are labelled with **method + URL** (sometimes a header or body). Responses are labelled with **status code + data**.
- Arrows may be numbered (`autonumber` in Mermaid) so a question can say "at arrow 5". Whether the exam numbers them is ⚠ verify.

![Notation: participants, lifelines, solid vs dashed vs open arrows, activation](../assets/T47/01-notation.png)
*Four participants with time running down. Solid is a request and dashed is a response; the open arrowhead to the switch is async. The grey bars are activation.*

- **Exam-sim gap:** practice tests may show **telecom-style time-sequence diagrams** (OSI/ITU service primitives), not just API calls.
  - The vertical lines are the **endpoints**: the service user and the service provider on each side of an interface.
  - Messages between them are labelled with primitives such as **request, indication, response and confirm**.
  - Timers and checks (for example a timer-check function) mark completion or error events.
  - These are less likely on the real exam than API diagrams (⚠ verify). The reading rule is the same: lifelines are participants, time runs down, and an arrow is a message.

### 2. Activation bars and frames
- An **activation bar** is a thin rectangle on a lifeline. It starts when a request arrives and ends when the response leaves, and it means **this participant is busy working right now**. (The lifeline means "exists"; the bar means "busy".)
- A long bar on the client during a synchronous call means the client is blocked waiting.
- A **frame** is a box drawn around some arrows, with an operator tag in the top-left corner and a **guard** condition in `[brackets]`. Frames are just code structures:

| Frame | Rule | Code equivalent |
|---|---|---|
| `alt [g1] / [else]` | at most one branch runs | `if … elif … else` |
| `opt [g]` | the block either happens or nothing happens | `if` with no `else` |
| `loop [g]` | the block repeats | `while` / `for` (polling, paging) |
| `par` | the branches run in parallel | threads / `asyncio.gather()` |
| `break [g]` | this runs instead of the rest | an early `return` or `raise` |
| `critical` | an atomic region that cannot be interleaved | a lock (awareness only) |

- **Notes** (`Note over A,B: …`) are yellow comment boxes. They are not messages.

![All four exam frames in one diagram](../assets/T47/02-frames.png)
*alt: exactly one of [200] or [401] happens. loop: the GET and its 200 repeat. opt: the logs call happens only if isError. par: both POSTs go out together, and the two 202s can return in either order.*

### 3. The auth flow: token first, then data
- This is the most common diagram. Four arrows:
  1. Client to auth endpoint: `POST /dna/system/api/v1/auth/token` with Basic credentials.
  2. Auth endpoint to client: `200 OK {"Token": "..."}`.
  3. Client to API: `GET /dna/intent/api/v1/network-device` with the header `X-Auth-Token: <token>`.
  4. API to client: `200 OK` plus the device list (or `401` if the token is missing or expired).
- The password is sent once, in arrow 1. After that, the token travels in a header instead.

![alt frame: 200 uses the data, 401 re-authenticates and retries](../assets/T47/04-alt-401.png)
*The same GET is sent, and its answer decides the branch. [200] ends the flow; [401] adds a new token request and a retry. Only one branch runs.*

- The `alt` version shows an expired token: the GET returns `401`, so the client logs in again and retries once. In code, the frame is literally an `if status == 401:` block.

![Animated: alt frame, one arrow = one line of code](../assets/T47/10-alt-reauth.gif)
*GET with the old token, `401`, the alt picks the [401] branch, POST for a new token, the new token returns, retry GET, `200`. It shows that both branches do not run, and that a `401` does not end the flow.*

- **`401` vs `403`**: `401` means there is no valid token, so the fix is to authenticate. `403` means the token is fine but the user lacks the role, so re-authenticating will not help.

### 4. The async flow: submit, poll, fetch
- For long jobs, the server accepts the request and works in the background:
  1. Client: `POST …/network-device-poller/cli/read-request` (submit the job).
  2. Server: **`202 Accepted`** plus a `taskId`. This means "accepted", **not** "done".
  3. A `loop [until endTime is set]` around: client `GET /dna/intent/api/v1/task/{taskId}`, server `200` with the task status.
  4. When the task finishes, it gives a `fileId`, and the client makes one more GET: `GET /dna/intent/api/v1/file/{fileId}` for the actual output.

![Async: POST job, 202 + taskId, loop polling the task, then GET the result](../assets/T47/05-async-poll.png)
*The 202 arrow is short and fast because the job runs in the background. Every poll gets a 200, but only the [finished] branch carries endTime and the fileId. Then one more GET fetches the output.*

- **The diagram draws the loop body once and never tells you how many times it ran.** In the lab it ran three times. A diagram only gives you the condition.
- An `opt [isError]` inside the loop means "if the task failed, stop with an error".
- **Pagination is the same shape**: a `loop` around one GET with `offset` and `limit`, stopping when a page comes back shorter than the limit. Catalyst Center's `offset` starts at 1 (⚠ verify).

### 5. The webhook flow: the arrows change direction
- Here the **service calls the app**:
  1. App to service: `POST /v1/webhooks` with `name`, `targetUrl`, `resource: "messages"`, `event: "created"`.
  2. Service to app: `200 OK`, webhook registered. Then the app sits idle, with no polling.
  3. and 4. Someone else causes the event (a user posts a message) and gets their own `200`.
  5. **Service to app**: `POST <targetUrl>` with a small payload of IDs. The service is now the client.
  6. App to service: a quick `200 OK` acknowledgement.
  7. and 8. App to service: `GET /v1/messages/{id}` with its Bearer token, and the full message comes back.

![Webhook: register, event, service POSTs to targetUrl, app ACKs and GETs details](../assets/T47/07-webhook.png)
*The app registers once and then waits. Arrow 5 starts at Webex and points at the app. The app replies 200 quickly, then GETs the full message by ID.*

- Arrow 7 exists because, for sensitive resources, Webex sends only metadata in the notification. The app must make an authenticated GET to `/messages/{id}`.
- Arrow 6 matters because Webex disables a webhook that keeps failing to get a 2xx (100 failed attempts within five minutes, ⚠ verify). So the listener replies **before** doing slow work.
- **Webhook vs polling at a glance**: the async diagram has a `loop` on the client; the webhook diagram has **no loop**, and one arrow runs from the **service to the app**.

### 6. Reading routine and spotting bugs
- Use this **five-step routine** on every exam diagram:
  1. **Participants**: name each box. Which one holds the data?
  2. **Solid arrows**: write the method and URL for each. Is the verb right? (create = `POST`, read = `GET`, replace = `PUT`, partial update = `PATCH`.)
  3. **Dashed arrows**: what status and data would you expect? `200` OK, `201` created, `202` accepted (async), `204` no content, or `401` / `403` / `404` / `429`.
  4. **Frames**: what repeats (`loop`), what branches (`alt`), what may be skipped (`opt`)?
  5. **Order**: auth before data, submit before poll, poll before result, register before event.

![Drill: what is wrong with this order?](../assets/T47/08-drill-spot-bug.png)
*A script against Secure Firewall Management Center (FMC). Arrow 1 calls the data API before any token exists, so arrow 2 is a 401. Then the script authenticates and repeats the call.*

- In that drill, arrows 1 and 2 are wasted because the call came **before auth**. A second clue: FMC returns the token and `DOMAIN_UUID` in **response headers**, so the `{domainUUID}` in arrow 1's URL could not be known yet (⚠ verify the `204` status on `generatetoken`).
- Other missing-step or wrong-order patterns:
  - A GET for the result straight after `202`, with no polling: the result is not ready yet.
  - A repeated job `POST` inside the loop instead of `GET /task/{taskId}`: this creates duplicate jobs.
  - A response with no request above it.
  - A webhook arrow drawn from the app to the service at event time: that is polling, not a webhook.
  - A retry after `429` with no wait: it should honour `Retry-After`.
- **"Order the calls" questions**: find the anchors first (auth is always first, the result GET is always last), then fill the middle by data dependency. You cannot call `/task/{taskId}` until a response gave you `taskId`.
- **"What is arrow N?" questions**: if it is solid, the answer is a method and URL; if dashed, a status and data. Check which frame and guard it sits under.
- **Diagram to code**: one solid plus dashed pair is one `requests.get()` or `post()` call. `alt [200] / [401]` is `if r.status_code == 401: … else: …`. `loop [until endTime]` is a `while` loop with a sleep. An arrow from the service to the app is an HTTP route handler that receives a POST.

## Exam traps (the ones that catch people)
- A dashed arrow looks like it could be any message, but **dashed is always a response** (status + data). A dashed arrow never carries a `GET`.
- The leftmost box looks like it goes first, but **box order means nothing; the highest arrow happens first**.
- `202 Accepted` looks like the end of the flow, but it is the **middle**. The next arrow is `GET /task/{taskId}`, not "read the result" and not "POST again".
- An `alt` frame looks like both branches run, but **exactly one branch runs**. `opt` is the one that may not run at all, and `loop` never tells you the number of passes.
- A data call at the top looks like a normal start, but **a data call before the token arrow is the classic bug**: expect a `401`.
- `401` and `403` both look like "re-login", but **only `401` is fixed by re-authenticating**; `403` is a role or scope problem.
- An open arrowhead looks like a typo, but **open means async** (the sender does not wait); filled means a sync call. A `202` response is still drawn dashed.
- Ten arrows look like ten calls, but **one HTTP call is two arrows**. Count only the solid arrows.

## Quick self-check
<details><summary>Q1. A dashed arrow from the controller to the script says `200 OK`. What is it?</summary>The response to an earlier request from the script; dashed means reply.</details>
<details><summary>Q2. Order: GET task, POST auth/token, GET file, 202 + taskId, POST job, 200 + Token.</summary>POST auth/token, 200 + Token, POST job, 202 + taskId, GET task (in a loop), GET file. Each call needs a value from the response before it.</details>
<details><summary>Q3. An `alt [200] / [401]` frame, and the token is valid. How many branches run?</summary>Only the [200] branch; alt is if/else.</details>
<details><summary>Q4. In a webhook diagram, what comes right after "a user posts a message"?</summary>The service POSTs a JSON notification to the app's `targetUrl`.</details>
<details><summary>Q5. A diagram has 5 solid and 5 dashed arrows. How many HTTP requests?</summary>Five; each solid arrow is a request and each dashed arrow is its response.</details>

## Cheat lines to say out loud
- "Boxes across, time down; solid asks, dashed answers."
- "alt is if/else, opt is if, loop is while, par is at the same time."
- "Token first, then data; a data call before the token is a 401."
- "202 means poll the task, not read the result."
- "In a webhook, the service draws the arrow to me, I say 200, then I GET the details."
