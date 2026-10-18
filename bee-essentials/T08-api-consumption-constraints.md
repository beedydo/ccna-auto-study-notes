# T08 · API consumption constraints: essentials

> Blueprint 2.3 · Full note: [bee/T08-api-consumption-constraints.md](../bee/T08-api-consumption-constraints.md) · Teach-back 2026-10-18

## In one picture

![T08 at a glance: every API consumption limit, its signal, the fix and the trap](../assets/T08/00-overview.png)

*Each row is one limit: read left to right from what the server sends, to what your code should do (blue), to the exam trap (red).*

## The big idea

- An API is a shared service, so the provider puts limits on how each consumer uses it: how fast you may call, how much comes back at once, how big a request may be, how long a token lasts and how long an old version keeps working. Think of a busy library: you may borrow only a few books per visit, a long list is printed one page at a time, and your library card eventually expires.
- None of these limits mean your code is broken. Each one sends a recognisable signal (a status code or a header), and a well-behaved script reacts to it. CBT doesn't cover blueprint 2.3, so the exam's "what should the script do?" questions come straight from this material.

## What you need to know

### 1. Rate limits: "slow down", not "you're wrong"

- A **rate limit** is the most requests the server accepts from one caller in one **time window**. The "caller" is whatever the server counts by: an API key, a token, a user, an org or an IP address.
  - The note's mock API allows 3 requests per 2 seconds per token. Meraki enforces its limit per **organization**, about 10 requests per second according to the Meraki SDK source ⚠ verify.
  - Servers do this to protect the backend from bursts and to share capacity fairly.
- Going over the limit returns **`429 Too Many Requests`**. It is a 4xx, but the request itself is fine; it was only sent **too soon**.
- The **`Retry-After`** header says how long to wait, in one of two forms: a number of seconds (`Retry-After: 2`) or an HTTP date (`Retry-After: Fri, 31 Dec 1999 23:59:59 GMT`). It can also appear on `503` and on a temporary `413`.
- Many APIs also send **`X-RateLimit-*`** headers. These are a common **convention, not a standard**, so names vary.

| Header | Meaning |
|---|---|
| `X-RateLimit-Limit: 3` | the quota per window |
| `X-RateLimit-Remaining: 0` | calls left in this window; 0 means the next call gets `429` |
| `X-RateLimit-Reset: 2` | seconds until the window resets (some APIs send a Unix time instead) |

![Animated rate-limit window: quota drains, 429, sleep Retry-After, retry succeeds](../assets/T08/10-rate-limit-retry.gif)

*The quota counts down to zero, call 4 gets `429` with `Retry-After: 2`, the client waits, and the very same call then succeeds. A 429 is a pause, not lost data.*

### 2. How a polite script retries, and how to make fewer calls

- On `429`, sleep for exactly the `Retry-After` value, then send the **same** request again. Don't change the URL, the body or the token.
- If there is no `Retry-After` header, use **exponential backoff**: wait 1, 2, 4, 8 seconds, doubling each time up to a **cap**. Real clients also add random **jitter** so a thousand scripts don't all retry at the same second.
- Only retry "come back later" codes: `429`, `502`, `503` and `504`. Other 4xx codes (`400`, `401`, `403`, `404`, `413`) mean the request is wrong, so sending it again unchanged can't work. The one exception is an expired-token `401`: get a new token first, then retry.
- Cap the number of retries too. Never retry forever, and never retry instantly, because each extra call extends the throttle.

![Retry decision: which codes to retry, how long to wait, which never to retry](../assets/T08/02-retry-decision.png)

*Blue codes are worth retrying (obey `Retry-After`, else back off); red codes mean fix the request instead.*

- The Meraki SDK behaves this way out of the box: `wait_on_rate_limit=True` makes it sleep on 429, with `maximum_retries=5` (SDK 4.6.0 defaults ⚠ verify). curl's `--retry 3` also retries on 408, 429, 500, 502, 503 and 504 and obeys `Retry-After`.
- The best fix is to make fewer calls, since a call you don't make can't be throttled:

| Technique | How it helps |
|---|---|
| **Cache** | Keep results you already have and revalidate them with `ETag` (section 6). |
| **Batch** | One call carrying many items instead of many calls (Meraki "action batches" ⚠ verify limits). |
| **Webhooks instead of polling** | The platform pushes a notification to you when something changes (T43). |
| **Bigger pages** | `perPage=1000` instead of 10 means fewer paging calls. |
| **Spread over time** | Pace yourself below the limit (for example a short sleep between calls) instead of bursting. |

### 3. Pagination: getting the whole list, not just page one

- **Pagination** means the server returns a big collection in **pages**, one page per request. Every page is a normal `200 OK`, so the status code never tells you there is more. You must check the body or the headers.
- There are three styles:

| Style | Example request | "Is there more?" signal | Who builds the next request | Jump to a page? | Stable if data changes? |
|---|---|---|---|---|---|
| **Offset / limit** | `?offset=5&limit=5` (skip 5, take 5) | body `total`; stop when `offset >= total` | you: `offset += limit` | yes | no |
| **Page number** | `?page=2&per_page=4` | body `total_pages`; stop when `page >= total_pages` | you: `page += 1` | yes | no |
| **Cursor / `Link` header** | `?perPage=10&startingAfter=c010` | `Link` header has `rel="next"`; stop when it is gone | the server | no, next only | yes |

![Three pagination styles side by side, each ending with its stop condition](../assets/T08/03-pagination-styles.png)

*Offset and page number read a count from the body; the cursor style reads the next URL from a header, which is the Meraki way.*

- **Meraki uses cursors.** The next-page URL arrives ready-made in the **`Link` response header**, for example `Link: <https://...?perPage=10&startingAfter=c010>; rel="next"`. Possible `rel` values include `first`, `prev`, `next` and `last`, and the last page has no `next`.
  - Never build `startingAfter` yourself; the server sets it and you just follow the URL.
  - In Python, `requests` parses the header for you: `r.links.get("next", {}).get("url")` returns the next URL, or `None` on the last page, which ends a `while url:` loop.
- **Meraki SDK trap:** `total_pages` defaults to 1, so you get only the first page unless you pass `total_pages="all"` (or `-1`).
- **The classic bug:** the script does one GET and stops. It reports 5 of 12 devices, with no error and no exception, just missing data. If a question says "records missing, no error", the answer is pagination.

![First-page-only bug vs the paging loop](../assets/T08/04-first-page-bug.png)

*Missing paging loop in red; the fix in green is to loop on the "more?" signal.*

### 4. Page size, jumping to a page, cursors and resuming a failed fetch

- **Page size:** the **API** sets a default and a maximum in its docs, and **you** pick a size up to that maximum with `limit`, `per_page` or `perPage`.
  - The same 9 events come back as 3 pages at `per_page=4` and as 2 pages at `per_page=6`.
  - Asking for more than the maximum usually gives `400`, or the API quietly caps it ⚠ verify per API.
  - Bigger pages mean fewer calls against your rate limit, but each response is slower and heavier. Pick a size near the maximum unless responses time out.
- **Jumping to page n** is plain arithmetic on the page size, and works only if the list is always sorted the same way.
  - Offset / limit: page 3 at `limit=5` is `offset=10`.
  - Page number: page *n* holds items `(n − 1) × per_page + 1` to `n × per_page`, so page 3 at `per_page=4` holds items 9 to 12. You can request it directly without fetching earlier pages.
- **A cursor is a bookmark.** It marks the last item you saw, so the next request means "continue after this one".
  - Cursors exist because offsets and page numbers shift when items are added or deleted mid-fetch, so you skip or repeat items. A cursor is tied to a real item, so it doesn't shift.
  - The trade-off is that you can't jump to "page 7"; you can only follow `next` (sometimes `prev`, `first`, `last`).
  - Some APIs use an opaque token such as `nextPageToken=eyJ...` instead. It works the same way: pass it back unchanged.
- **If the fetch dies halfway, the API won't resume for you**, because REST is stateless. Your script decides.
  - With no saved bookmark, it starts again at page 1 and fetches everything twice.
  - If it saved a bookmark after each page, it resumes from the first page it hadn't finished.
  - Order matters: **save the page's data first, then move the bookmark.** A crash between the two means at worst re-fetching one page, so make saving an item twice harmless by de-duplicating on its id.
  - On `429` or a timeout, retry the **same** URL; only a successful page moves the bookmark.
  - Cursors can **expire** ⚠ verify per API. If resuming gives `400` or `410`, start again from page 1.

![Resume a paged fetch from a saved bookmark](../assets/T08/11-resume-paging.png)

*For each page: save the data (1), then save the next URL as the bookmark (2); after a crash the restart begins at the first unsaved page.*

### 5. Payload size and timeouts

- Servers cap what one request may carry, in **bytes** (the whole body) and in **items** (entries per call). Meraki's synchronous action batches allow at most 20 actions ⚠ verify.
- A body that is too big gets **`413`**. Its old name is "Payload Too Large" and its current name (RFC 9110) is "Content Too Large"; both mean the same code.
- An items limit often comes back as a plain **`400`** with the reason in the body, such as `"15 serials; max 10 per request"`. Read the error body.
- The fix is to **split** the work into batches that fit under both caps. Splitting raises the call count, so keep the rate limit in mind.
- Rarely tested relatives: `414 URI Too Long` and `431 Request Header Fields Too Large`.
- **Client timeouts:** the Python `requests` library has **no default timeout**, so without one a call can hang for minutes or more.
  - `timeout=10` applies 10 seconds to both connecting and reading. `timeout=(3.05, 5)` sets connect and read separately. The read timeout is the longest gap between bytes, not the total download time.
  - Hitting it raises an **exception** (`requests.exceptions.ConnectTimeout` or `ReadTimeout`). There is no HTTP response and no status code at all. curl's equivalent is `--connect-timeout` and `--max-time`, which exit with code 28.
- **`504 Gateway Timeout`** is different: a proxy, load balancer or gateway **in the middle** gave up waiting for the backend, and it sends you a real HTTP response.
- **Async jobs:** for work longer than any sensible timeout (reports, firmware upgrades, backups) the API answers **`202 Accepted`** at once, with a job URI in `Location`. You **poll** that URI until it says complete. Catalyst Center (DNA Center) does this for many write calls ⚠ verify the exact task endpoint.

![Client timeout vs gateway timeout vs async job](../assets/T08/06-timeouts-async.png)

*A: the client gives up (exception, no code). B: the gateway gives up (`504`). C: nobody waits (`202`, then poll).*

### 6. Expiring tokens, retiring versions and caching

- **Tokens expire on purpose**, so a leaked one stops working soon. The lifetime usually comes in the login response as `"expires_in": 300` (seconds). Lifetimes vary by platform, for example about 30 minutes for Secure Firewall Management Center (FMC) and about 12 hours for Webex personal tokens ⚠ verify both.
  - The symptom is a script that worked for its first calls and then gets **`401`** mid-run. A good server says why: `WWW-Authenticate: Bearer error="invalid_token", error_description="The access token expired"`.
  - The fix is to get a new token and retry the failed call **once**. With a **refresh token** (a longer-lived second credential), you POST it with `grant_type=refresh_token` and skip re-sending the password. Without one, which is common on Cisco APIs, simply log in again.
  - If it is still `401` after one refresh, stop: the credentials really are wrong. Better still, refresh before expiry by tracking `expires_in`. A new token never fixes `403`.
- **Versions retire.** APIs are versioned in the URL (`/api/v1/...`, the common form the exam shows) or in a header such as `Accept: application/vnd.example.v2+json`.
  - The lifecycle is **active, then deprecated, then removed**. A **deprecated** version still answers `200` but adds warning headers: `Deprecation` (when it was deprecated), `Sunset` (when it stops working) and `Link: <...>; rel="successor-version"` (the replacement).
  - After the sunset date, calls fail with `404` or `410 Gone`. A version that never existed also gives `404`.
  - Migrate the **field names**, not just the path. In the lab, v0 called the field `name` and v1 calls it `hostname`, so a script that only changes the URL hits a `KeyError`.

![Version lifecycle: active, deprecated with warning headers, removed; migrate to v1](../assets/T08/08-version-lifecycle.png)

*The deprecated phase (yellow) still returns `200`, which is why scripts don't notice until removal (red).*

- **Caching with ETags** saves bandwidth and server work. The server sends a version tag in the **`ETag`** header. Next time, the client sends it back in **`If-None-Match`**, which makes a **conditional GET**.
  - Unchanged gives **`304 Not Modified`** with an **empty body**, so reuse your copy. Changed gives a normal `200` with a new body and a new tag.
  - Whether a `304` counts against your rate limit depends on the API ⚠ verify per platform.
  - `Cache-Control: max-age=60` is cheaper still: you may reuse the copy for 60 seconds without asking at all.

## Exam traps (the ones that catch people)

- `429` and `503` both look like "server trouble", but `429` means **you** sent too many and `503` means the service is down for everyone. Both say "wait and retry", and both can carry `Retry-After`.
- A `429` looks like a broken request, but it is actually fine; don't change the URL or re-authenticate, just wait and send the same call again.
- "Records missing, no error" looks like a permissions or timeout problem, but it is actually a missing paging loop, because every page returns `200`.
- On Meraki the next page looks like it should be in the body, but it is actually in the `Link` **response header** as `rel="next"`.
- `int(r.headers["Retry-After"])` looks safe, but it crashes when the server uses the HTTP-date form.
- A client timeout looks like it should return `504`, but it actually raises an exception with no response at all; `504` comes from a gateway in the middle.
- A `401` after many successful calls looks like wrong credentials, but it is actually an expired token. Refresh once; if it is still 401, stop.
- A deprecated API looks fine because it returns `200`, but it is actually on its way out, so watch the `Deprecation` and `Sunset` headers.

## Quick self-check

<details><summary>Q1. A loop over 400 devices starts getting <code>429</code> with <code>Retry-After: 1</code>. Best fix?</summary>Sleep for the <code>Retry-After</code> value, retry the same call, and pace the loop; the request itself is fine.</details>

<details><summary>Q2. Which <code>requests</code> expression gives the next Meraki page URL, or <code>None</code> on the last page?</summary><code>r.links.get("next", {}).get("url")</code>, because <code>requests</code> parses the <code>Link</code> header into <code>r.links</code>.</details>

<details><summary>Q3. A bulk call with 2000 serials returns <code>413</code>. What do you change?</summary>Split it into smaller requests; waiting doesn't shrink the body.</details>

<details><summary>Q4. A fetch crashes on page 23. What must the script have saved to resume there?</summary>The next-page URL (the cursor) after each successful page, because the API keeps no record of your progress.</details>

<details><summary>Q5. Which response says your cached copy is still current?</summary><code>304 Not Modified</code>, and only after you sent <code>If-None-Match</code> with the ETag.</details>

## Cheat lines to say out loud

- "429 means wait and resend the same thing, not fix the request."
- "Every page says 200, so follow the Link header until next disappears."
- "A cursor is a bookmark the server hands me; my script, not the API, remembers where I stopped."
- "Requests never times out unless I tell it to, and a timeout is an exception, not a 504."
- "ETag goes out, If-None-Match comes back, 304 means reuse what I have."
