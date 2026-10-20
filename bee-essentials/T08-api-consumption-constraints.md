# T08 · API consumption constraints: essentials

> Blueprint 2.3: constraints when consuming APIs (rate limits, pagination, payload size) · Full note: [bee/T08-api-consumption-constraints.md](../bee/T08-api-consumption-constraints.md) · Teach-back 2026-10-18

![T08 at a glance: every API consumption limit, its signal, the fix and the trap](../assets/T08/00-overview.png)

*Each row is one limit: read left to right from what the server sends, to what your code should do (blue), to the exam trap (red).*

## 🧭 The big idea

An API is a **shared service**, so the provider limits how each consumer uses it. This topic asks, for each limit: **what signal does the server send, and what should my script do about it?**

| | Question | Limit | Analogy: a busy library |
|---|---|---|---|
| 🚦 | **How fast** may I call? | rate limit | you may borrow only a few books **per visit** |
| 📄 | **How much** comes back at once? | pagination | a long catalogue is printed **one page at a time** |
| 📦 | **How big** may one request be? | payload size | the returns slot only takes **so many books at once** |
| ⏳ | **How long** will anyone wait? | timeouts and async jobs | |
| 🎫 | **How long** does my login last? | token expiry | your **library card expires** |

> 💡 **None of these mean your code is broken.** Each limit has a recognisable signal (a status code or a header), and a well-behaved script reacts to it.

- 🎯 **What the exam asks:** a scenario ("the script starts getting 429", "records are missing but there's no error", "bulk update returns 413") and "what's the cause / what should the script do?". CBT doesn't cover blueprint 2.3, so these questions come straight from this material.

## 🟥 Must know

### 1. 🚦 Rate limits: `429` means "slow down", not "you're wrong"

> 💡 **A rate limit** is the most requests the server accepts from **one caller** in **one time window**. **Going over the limit returns `429 Too Many Requests`.** It's a 4xx, but the request itself is **fine**. It was only sent **too soon**.

| | |
|---|---|
| 👤 The "caller" | whatever the server counts by: an API key, a token, a user, an org or an IP address |
| 🧪 Full note's mock API | **3 requests per 2 seconds per token** |
| 🧩 **Meraki** | enforces its limit per **organization**, about **10 requests per second** according to the Meraki SDK source ⚠ verify |
| ❓ Why | to protect the backend from bursts and share capacity fairly between customers |
| 🚧 Analogy | a turnstile that lets 3 people through every 2 seconds. Person 4 isn't banned; they just wait for the next gap |

- What it looks like on the wire (from the full note's lab run):

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 2                        ← wait 2 seconds, then send the SAME request again
X-RateLimit-Limit: 3                  ← quota per window
X-RateLimit-Remaining: 0              ← calls left in this window (0 = you're out)
X-RateLimit-Reset: 2                  ← seconds until the window resets

{"error": "rate limit: 3 requests per 2 s"}
```

| Header | Means | Notes |
|---|---|---|
| **`Retry-After`** | how long to wait, in **one of two forms**: a number of seconds (`Retry-After: 2`) or an HTTP date (`Retry-After: Fri, 31 Dec 1999 23:59:59 GMT`) | can also appear on `503` (maintenance) and on a temporary `413` |
| **`X-RateLimit-*`** | a common **convention, not a standard**, so names vary between APIs | `X-RateLimit-Remaining: 0` warns you **before** the 429 arrives. `X-RateLimit-Reset` is seconds in the mock; some APIs send a Unix time instead |

![Animated rate-limit window: quota drains, 429, sleep Retry-After, retry succeeds](../assets/T08/10-rate-limit-retry.gif)

*The quota counts down to zero, call 4 gets `429` with `Retry-After: 2`, the client waits, and the very same call then succeeds. A 429 is a pause, not lost data.*

### 2. 🔁 How a polite script retries, and how to make fewer calls

> 💡 **On `429`:** sleep for exactly the `Retry-After` value, then send the **same** request again. Don't change the URL, the body or the token.

- **No `Retry-After`? Use exponential backoff:** wait 1, 2, 4, 8 seconds, doubling each time, up to a **cap**.
  - Doubling gives a struggling server breathing room fast; the cap stops waits growing to minutes.
  - Real clients add random **jitter** so a thousand scripts don't all retry on the same second.
- 📞 **Analogy: a busy phone line.** You don't redial instantly a hundred times; you wait a bit longer after each busy tone.
- The retry logic from the full note's reference program, annotated:

```python
for attempt in range(MAX_RETRIES + 1):                     # cap the retries: never retry forever
    r = self.session.request(method, url, **kwargs)
    if r.status_code == 429:                               # rate limited: obey the server
        wait = int(r.headers.get("Retry-After", min(2 ** attempt, BACKOFF_CAP)))  # header if sent, else backoff
        time.sleep(wait)
        continue                                           # send the SAME request again
    if r.status_code in (502, 503, 504) and "Retry-After" not in r.headers:
        wait = min(2 ** attempt, BACKOFF_CAP)              # 1, 2, 4, 8, 8 ... (BACKOFF_CAP = 8)
        time.sleep(wait)
        continue
    return r                                               # any other code: hand it back, don't retry
```

- Lab run: `503` → sleep 1 s → `503` → sleep 2 s → `200`.
- `int(...)` here is fine for the mock, but **crashes on the HTTP-date form** of `Retry-After` (see Exam traps).

**Which codes to retry:**

| ✅ Retry | ❌ Don't retry |
|---|---|
| `429`, `502`, `503`, `504` ("come back later") | `400`, `401`, `403`, `404`, `413`. The request is wrong, so sending it again unchanged can't work. |
| | **One exception:** an **expired-token `401`**: get a new token first, then retry (section 6). |

- 🚫 **Never retry instantly:** each extra call extends the throttle.

**Libraries that do this for you:**

| Library | How |
|---|---|
| Meraki SDK | `wait_on_rate_limit=True` makes it sleep on 429, with `maximum_retries=5` (SDK 4.6.0 defaults ⚠ verify) |
| curl | `--retry 3` retries on 408, 429, 500, 502, 503 and 504 and obeys `Retry-After` |

![Retry decision: which codes to retry, how long to wait, which never to retry](../assets/T08/02-retry-decision.png)

*Blue codes are worth retrying (obey `Retry-After`, else back off); red codes mean fix the request instead.*

> 💡 **The best fix is to make fewer calls**, because a call you don't make can't be throttled.

| Technique | How it helps |
|---|---|
| 💾 **Cache** | keep results you already have; revalidate with `ETag` (Should know) |
| 🧺 **Batch** | one call carrying many items instead of many calls (Meraki "action batches" ⚠ verify limits) |
| 🪝 **Webhooks instead of polling** | the platform pushes a notification to you when something changes (T43) |
| 📄 **Bigger pages** | `perPage=1000` instead of 10 means fewer paging calls |
| 🐢 **Spread over time** | pace yourself below the limit (e.g. a short sleep between calls) instead of bursting |

### 3. 📄 Pagination: get the whole list, not just page one

> 💡 **Pagination** = the server returns a big collection in **pages**, one page per request, so no single response is huge. **Every page is a normal `200 OK`.** The status code never tells you there's more; you must check the **body** or the **headers**.

- 🔍 **Analogy: a search engine's results.** Page 1 shows 10 results and a "Next" link. If you only read page 1, you never see result 11, and nothing tells you anything went wrong.

**Three styles:**

| Style | Example request | "Is there more?" signal | Who builds the next request |
|---|---|---|---|
| 🔢 **Offset / limit** | `?offset=5&limit=5` = skip 5, take 5 | body says `"total": 12`; stop when `offset >= total` | you: `offset += limit` |
| 📖 **Page number** | `?page=2&per_page=4` | body says `"total_pages": 3`; stop when `page >= total_pages` | you: `page += 1` |
| 🔖 **Cursor / `Link` header (Meraki)** | `?perPage=10&startingAfter=c010` | the server hands you the **ready-made next URL** in a response header; stop when there's no `rel="next"` | the server |

- **Meraki's `Link` header**, from the full note's lab:

```http
HTTP/1.1 200 OK
Link: <…/networks/N_100/clients?perPage=10>; rel="first", <…/networks/N_100/clients?perPage=10&startingAfter=c010>; rel="next"
```

- `rel="next"` = the URL of the next page. `startingAfter=c010` is the **cursor**: "continue after client c010".
- Possible `rel` values include `first`, `prev`, `next` and `last`. The **last page has no `next`**.
- **Never build `startingAfter` yourself**; the server sets it and you just follow the URL.
- **The paging loop in Python** (`requests` parses the `Link` header into `r.links`):

```python
url = f"{BASE_URL}/networks/N_100/clients?perPage=10"
items = []
while url:                                         # stops when url becomes None
    r = api.call("GET", url)
    items += r.json()                              # collect this page
    url = r.links.get("next", {}).get("url")       # next page URL, or None on the last page
```

- Lab result: 3 pages, **25 clients**. `.get("next", {})` avoids a `KeyError` on the last page.

> 🎯 **Meraki SDK trap:** `total_pages` defaults to **1**, so you get **only the first page** unless you pass `total_pages="all"` (or `-1`).

![Three pagination styles side by side, each ending with its stop condition](../assets/T08/03-pagination-styles.png)

*Offset and page number read a count from the body; the cursor style reads the next URL from a header, which is the Meraki way.*

| ❌ The classic bug | ✅ The fix |
|---|---|
| The script does **one GET** and stops. The lab's `first_page_only()` reports **5 of 12** devices, with **no error and no exception**, just missing data. | Loop on the "more?" signal. |

> 🎯 Exam cue: "records missing, no error" → the answer is **pagination**.

![First-page-only bug vs the paging loop](../assets/T08/04-first-page-bug.png)

*Missing paging loop in red; the fix in green is to loop on the "more?" signal.*

### 4. 📦 Payload size: `413` means "too big", so split it

> 💡 Servers cap what **one request** may carry. **The fix is to split** into batches that fit under **both** caps.

| Cap | What it limits | Example | Signal |
|---|---|---|---|
| ⚖️ **Bytes** | the whole body | the mock caps it at 512 bytes | **`413`**. Old name "Payload Too Large", current name (RFC 9110) "Content Too Large". Same code. |
| 🔢 **Items** | entries per call | the mock allows at most 10 serials. Meraki's synchronous action batches allow at most **20 actions** ⚠ verify | often a plain **`400`** with the reason in the body. Read the error body. |

- 🏤 **Analogy: a post-office counter.** One parcel can't weigh more than the limit, and you can only hand over so many parcels in one go. Send several trips instead.
- From the lab, posting 40 serials:

```
POST /api/v1/devices/claim  {40 serials}  → 413 Content Too Large   {"error": "body is 533 bytes; limit is 512"}
POST /api/v1/devices/claim  {15 serials}  → 400 Bad Request         {"error": "15 serials; max 10 per request"}
4 × POST with 10 serials each             → 200 {'claimed': 10}  (×4)
```

- The split:

```python
def chunks(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]                    # slices of at most `size` items

for batch in chunks(serials, 10):                  # 40 serials → 4 calls of 10
    r = api.call("POST", "/devices/claim", json={"serials": batch})
```

- ⚠️ **Waiting doesn't help a `413`:** the body is still too big. Splitting raises the call count, so keep the rate limit in mind.

![Payload limits: 413 on bytes, 400 on item count, then chunks of 10 succeed](../assets/T08/05-payload-split.png)

*Both limits lead to the same fix (blue): split into batches that fit under both caps.*

### 5. ⏳ Timeouts and async jobs

> 💡 **The Python `requests` library has no default timeout.** Without one, a call can hang for minutes or more.

- ☎️ **Analogy: a phone call on hold.** Without a timeout you'd hold forever. With one, you hang up after 10 seconds and decide what to do.
- **Setting a timeout:**

```python
requests.get(url, timeout=10)          # 10 s for connecting AND 10 s for reading
requests.get(url, timeout=(3.05, 5))   # (connect, read): 3.05 s to connect, 5 s max gap between bytes
```

- The **read** timeout is the longest gap **between bytes**, not the total download time.

| | 🙋 Client timeout | 🚪 `504 Gateway Timeout` | 🎟️ Async job (`202`) |
|---|---|---|---|
| Who gives up | your client | a proxy, load balancer or gateway **in the middle** gave up waiting for the backend | nobody waits |
| What you get | **an exception**, `requests.exceptions.ConnectTimeout` or `requests.exceptions.ReadTimeout`. There's **no HTTP response and no status code at all** | a real HTTP response | **`202 Accepted`** at once, with a job URI in `Location`. You **poll** that URI until it says complete |
| Notes | curl's equivalents: `--connect-timeout` and `--max-time`; a timeout exits with code 28 | | for work longer than any sensible timeout (reports, firmware upgrades, backups) |

```
POST /api/v1/reports                → 202 Accepted, Location: /api/v1/jobs/1   ← queued, NOT done
GET  /api/v1/jobs/1                 → running
GET  /api/v1/jobs/1                 → running
GET  /api/v1/jobs/1                 → complete
```

- 🧩 Catalyst Center (DNA Center) does this for many write calls ⚠ verify the exact task endpoint (T09).

![Client timeout vs gateway timeout vs async job](../assets/T08/06-timeouts-async.png)

*A: the client gives up (exception, no code). B: the gateway gives up (`504`). C: nobody waits (`202`, then poll).*

### 6. 🎫 Expiring tokens: `401` in the middle of a run

> 💡 **Tokens expire on purpose**, so a leaked one stops working soon. The lifetime usually comes in the login response as `"expires_in": 300` (seconds).

- ⏲️ Lifetimes vary by platform, e.g. about **30 minutes** for Secure Firewall Management Center (FMC) and about **12 hours** for Webex personal tokens ⚠ verify both.
- 🪪 **Analogy: a day visitor badge.** It worked all morning; at 5 pm the door stops opening. Your identity didn't change; the badge ran out. Go back to reception for a new one.
- **The symptom:** a script that worked for its first calls suddenly gets **`401`** mid-run. A good server says why:

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer error="invalid_token", error_description="The access token expired"
```

**The fix:** get a new token and retry the failed call **once**.

| Case | Do |
|---|---|
| 🔄 **With a refresh token** (a longer-lived second credential) | POST it with `grant_type=refresh_token` to get a new access token without re-sending the password |
| 🔑 **Without one** (common on Cisco APIs) | simply log in again |
| 🛑 **Still `401` after one refresh** | stop. The credentials really are wrong |
| ⏰ Better still | refresh **before** expiry by tracking `expires_in` |
| ❌ `403` | **a new token never fixes `403`**: that's a role problem, not an expiry (T10) |

![Token expiry mid-script, refresh, retry once](../assets/T08/07-token-expiry.png)

*The token lives 1 s; 1.5 s later the call gets `401` with "The access token expired"; refresh → new token → the same call returns `200`.*

### 7. 🎯 Scenario → cause → fix (the exam's answer key)

| Scenario in the question | | Cause | Fix |
|---|---|---|---|
| Loop over 500 devices starts getting `429` | 🚦 | too many calls per window | honour `Retry-After`; back off; pace; cache/batch; webhooks instead of polling |
| Report shows 1000 clients, dashboard has 2400 | 📄 | only the first page read | loop on `Link rel="next"` / `total` / `total_pages`; Meraki SDK `total_pages="all"` |
| Script hangs forever on one call | ⏳ | no client timeout | `requests.get(url, timeout=(3.05, 10))` |
| `504` from the API | ⏳ | gateway timed out waiting for the backend | retry later with backoff; use the async (`202`) variant if there is one |
| Bulk update returns `413` | 📦 | body too large | split into smaller requests |
| Works for 30 min, then every call returns `401` | 🎫 | token expired | refresh or log in again, then retry once |

## ⚠️ Exam traps

| ❌ Looks like… | ✅ Actually… |
|---|---|
| 🚦 429 = fix the request | **429 ≠ fix the request.** The request is fine: don't change the URL, body or token. Wait `Retry-After` seconds and resend the **same** call. **429 vs 503:** 429 = **you** sent too many; 503 = the service is down for everyone. Both say "wait and retry". |
| 📄 "Records missing, no error" = permissions or a timeout | **Pagination.** Every page returns `200`. On Meraki the next page is in the **`Link` response header** (`rel="next"`), not the body. |
| 🚦 `Retry-After` is always seconds | **`Retry-After` can be a date.** `int(r.headers["Retry-After"])` crashes on the HTTP-date form. |
| ⏳ A client timeout returns `504` | **A client timeout is an exception, not a `504`.** `requests` never times out unless you pass `timeout=`; `504` comes from a gateway in the middle. |
| 🎫 `401` after many successful calls = wrong credentials | **Expired token.** Refresh once; if still 401, stop. A new token never fixes 403. |
| 🔁 Retry any 4xx | **Don't retry other 4xx** (`400`, `403`, `404`, `413`): unchanged, they can't succeed. Waiting doesn't shrink a 413 body. |

<details><summary><b>🟨 Should know (second pass)</b></summary>

### 📏 Page size

- The **API** sets a default and a maximum in its docs; **you** pick a size up to that maximum with `limit`, `per_page` or `perPage`.
  - The same 9 events come back as 3 pages at `per_page=4` and as 2 pages at `per_page=6`.
  - Asking for more than the maximum usually gives `400`, or the API quietly caps it ⚠ verify per API.

- ⚖️ Bigger pages = ✅ fewer calls against the rate limit, but ❌ each response is slower and heavier. Pick a size near the maximum unless responses time out.

### 🔢 Jumping to page n

Arithmetic on the page size, and only works if the list is always sorted the same way:

| Style | Rule / example |
|---|---|
| Offset / limit | page 3 at `limit=5` is `offset=10` |
| Page number | page *n* holds items `(n − 1) × per_page + 1` to `n × per_page`, so page 3 at `per_page=4` holds items 9 to 12. You can request it directly |

### 🔖 A cursor is a bookmark

- It marks the last item you saw, so the next request means "continue after this one".
- **Why cursors exist:** offsets and page numbers shift when items are added or deleted mid-fetch, so you skip or repeat items. A cursor is tied to a real item, so it doesn't shift.
- **Trade-off:** you can't jump to "page 7"; you can only follow `next` (sometimes `prev`, `first`, `last`).
- Some APIs use an opaque token such as `nextPageToken=eyJ...` instead. Same idea: pass it back unchanged.

| Style | Jump to a page? | Stable if data changes? |
|---|---|---|
| Offset / limit | ✅ yes | ❌ no |
| Page number | ✅ yes | ❌ no |
| Cursor / `Link` | ❌ no, next only | ✅ yes |

### 💥 Resuming a fetch that died halfway

The API won't do it for you, because REST is stateless. Your script decides.

| ❌ No saved bookmark | ✅ Saved bookmark after each page |
|---|---|
| it starts again at page 1 and fetches everything twice | it resumes from the first page it hadn't finished |

- **Order matters:** save the page's data first, then move the bookmark. A crash between the two means at worst re-fetching one page, so de-duplicate on the item's id.
- On `429` or a timeout, retry the **same** URL; only a successful page moves the bookmark.
- Cursors can **expire** ⚠ verify per API. If resuming gives `400` or `410`, start again from page 1.

![Resume a paged fetch from a saved bookmark](../assets/T08/11-resume-paging.png)

*For each page: save the data (1), then save the next URL as the bookmark (2); after a crash the restart begins at the first unsaved page.*

### 🏷️ Versions retire

- APIs are versioned in the URL (`/api/v1/...`, the common form the exam shows) or in a header such as `Accept: application/vnd.example.v2+json`.

| Lifecycle stage | What you see |
|---|---|
| 🟢 **active** | normal responses |
| 🟡 **deprecated** | still answers `200` but adds warning headers: `Deprecation` (when it was deprecated), `Sunset` (when it stops working) and `Link: <...>; rel="successor-version"` (the replacement) |
| 🔴 **removed** | after the sunset date, calls fail with `404` or `410 Gone`. A version that never existed also gives `404` |

- **Migrate the field names, not just the path.** In the lab, v0 called the field `name` and v1 calls it `hostname`, so a script that only changes the URL hits a `KeyError`.

![Version lifecycle: active, deprecated with warning headers, removed; migrate to v1](../assets/T08/08-version-lifecycle.png)

*The deprecated phase (yellow) still returns `200`, which is why scripts don't notice until removal (red).*

### 💾 Caching with ETags

Saves bandwidth and server work:

1. The server sends a version tag in the **`ETag`** header, e.g. `ETag: "Q2SW-0001-r1"`.
2. Next time, the client sends it back in **`If-None-Match`**: a **conditional GET**.
3. Unchanged → **`304 Not Modified`** with an **empty body**: reuse your copy. Changed → a normal `200` with a new body and a new tag.

- Whether a `304` counts against your rate limit depends on the API ⚠ verify per platform.
- `Cache-Control: max-age=60` is cheaper still: reuse the copy for 60 seconds without asking at all.

![ETag and If-None-Match: 304 if unchanged, 200 with new ETag if changed](../assets/T08/09-etag-cache.png)

*The tag goes out as `ETag` and comes back as `If-None-Match`. Only a conditional GET can produce `304`.*

</details>

> 📚 **Recognise only, details in the full note:** `414 URI Too Long` and `431 Request Header Fields Too Large`, weak ETags (`W/"…"`), the IETF `RateLimit` draft headers, Meraki SDK smart flow and `nginx_429_retry_wait_time`, per-endpoint `perPage` ranges, parsing the HTTP-date `Retry-After` form, `X-API-Version` headers.

## ✍️ Quick self-check
<details><summary>Q1. A loop over 400 devices starts getting <code>429</code> with <code>Retry-After: 1</code>. Best fix?</summary>Sleep for the <code>Retry-After</code> value, retry the same call, and pace the loop; the request itself is fine.</details>
<details><summary>Q2. Which <code>requests</code> expression gives the next Meraki page URL, or <code>None</code> on the last page?</summary><code>r.links.get("next", {}).get("url")</code>, because <code>requests</code> parses the <code>Link</code> header into <code>r.links</code>.</details>
<details><summary>Q3. A bulk call with 2000 serials returns <code>413</code>. What do you change?</summary>Split it into smaller requests; waiting doesn't shrink the body.</details>
<details><summary>Q4. A fetch crashes on page 23. What must the script have saved to resume there?</summary>The next-page URL (the cursor) after each successful page, because the API keeps no record of your progress.</details>
<details><summary>Q5. Which response says your cached copy is still current?</summary><code>304 Not Modified</code>, and only after you sent <code>If-None-Match</code> with the ETag.</details>
<details><summary>Q6. A script reports 5 of 12 devices. Every call returned <code>200</code>. Cause?</summary>It read only the first page. Loop on the "more?" signal (<code>total</code>, <code>total_pages</code> or <code>Link rel="next"</code>).</details>
<details><summary>Q7. <code>requests.get(url)</code> has hung for 10 minutes. What's missing, and what happens once it's added and hit?</summary><code>timeout=</code> (e.g. <code>timeout=(3.05, 10)</code>). Hitting it raises <code>requests.exceptions.ReadTimeout</code> (or <code>ConnectTimeout</code>): an exception, no status code.</details>

## 🗣️ Say it out loud
- 🚦 "429 means wait and resend the same thing, not fix the request."
- 📄 "Every page says 200, so follow the Link header until next disappears."
- 📦 "413 means split it; waiting won't shrink the box."
- ⏳ "Requests never times out unless I tell it to, and a timeout is an exception, not a 504."
- 🎫 "401 after it was working means the badge expired: refresh once, then stop."
