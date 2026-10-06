---
id: T07
title: "REST fundamentals, HTTP codes"
owner: Beedy
blueprint: "2.1, 2.4-2.6"
primary_domain: D2
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-09
teach_back: 2026-10-12
cross_study: 2026-10-21
---

# T07 · REST fundamentals, HTTP codes

> Owner: **Beedy** · Blueprint: **2.1, 2.4-2.6** · CBT coverage: **Full** · Learn by 2026-10-09 · Teach-back 2026-10-12

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T07.01 · REST basics

**Must cover:**

- [ ] REST = Representational State Transfer: an architectural style, not a protocol
- [ ] Everything is a resource identified by a URI (e.g. /api/v1/devices/123)
- [ ] URI parts: scheme://host:port/path?query#fragment
- [ ] Base URL + endpoint path = full request URL

**Notes:**

<!-- TODO -->

### T07.02 · REST constraints

**Must cover:**

- [ ] Client-server: UI and data storage separated
- [ ] Stateless: each request carries everything needed (e.g. auth token); server keeps no session
- [ ] Cacheable: responses say whether they can be cached
- [ ] Uniform interface: standard methods, resource URIs, self-descriptive messages
- [ ] Layered system: proxies/load balancers can sit in between
- [ ] Code on demand (optional): server may send executable code

**Notes:**

<!-- TODO -->

### T07.03 · HTTP methods

**Must cover:**

- [ ] GET = read (no body)
- [ ] POST = create (server assigns the ID)
- [ ] PUT = create or fully replace a resource at a known URI
- [ ] PATCH = partial update (only the fields sent)
- [ ] DELETE = remove
- [ ] CRUD: Create=POST, Read=GET, Update=PUT/PATCH, Delete=DELETE

**Notes:**

<!-- TODO -->

### T07.04 · HTTP methods

**Must cover:**

- [ ] Safe = does not change state: GET, HEAD, OPTIONS
- [ ] Idempotent = repeating gives the same result: GET, PUT, DELETE (and HEAD, OPTIONS)
- [ ] POST is neither safe nor idempotent (repeat = duplicate objects)
- [ ] PATCH is not guaranteed idempotent

**Notes:**

<!-- TODO -->

### T07.05 · Request parts

**Must cover:**

- [ ] Request = method + URI + headers + optional body
- [ ] Path parameter: part of the path (/devices/{id})
- [ ] Query parameter: after ? as key=value pairs joined by & (filtering, paging)
- [ ] Body/payload: JSON or XML data for POST/PUT/PATCH

**Notes:**

<!-- TODO -->

### T07.06 · Headers

**Must cover:**

- [ ] Content-Type: format of the body being sent
- [ ] Accept: format the client wants back
- [ ] Authorization: credentials/token
- [ ] User-Agent, Cache-Control
- [ ] Response headers: Location (URI of created resource), Retry-After, Set-Cookie, ETag, Content-Length

**Notes:**

<!-- TODO -->

### T07.07 · Response parts

**Must cover:**

- [ ] Status line: HTTP version, code, reason phrase (HTTP/1.1 201 Created)
- [ ] Headers: metadata about the response
- [ ] Body: the data (often JSON), may be empty (204)
- [ ] Exam asks you to point to which part holds a given piece of information

**Notes:**

<!-- TODO -->

### T07.08 · Status classes

**Must cover:**

- [ ] 1xx informational
- [ ] 2xx success
- [ ] 3xx redirection (resource moved, use cache)
- [ ] 4xx client error (fix your request)
- [ ] 5xx server error (problem on the server side)

**Notes:**

<!-- TODO -->

### T07.09 · Key codes

**Must cover:**

- [ ] 200 OK; 201 Created; 202 Accepted (async); 204 No Content
- [ ] 301 Moved Permanently; 302 Found; 304 Not Modified
- [ ] 400 Bad Request; 401 Unauthorized; 403 Forbidden; 404 Not Found; 405 Method Not Allowed; 409 Conflict; 415 Unsupported Media Type; 429 Too Many Requests
- [ ] 500 Internal Server Error; 501 Not Implemented; 502 Bad Gateway; 503 Service Unavailable; 504 Gateway Timeout

**Notes:**

<!-- TODO -->

### T07.10 · Troubleshooting

**Must cover:**

- [ ] 401: missing, wrong or expired credentials → re-authenticate
- [ ] 403: authenticated but not allowed → check role/permissions
- [ ] 404: wrong URI/ID; 405: wrong method for that endpoint
- [ ] 415: wrong Content-Type header; 400: malformed or invalid body
- [ ] 429: rate limited → wait (Retry-After); 5xx: server-side, retry later or check the server

**Notes:**

<!-- TODO -->

### T07.11 · Using API docs

**Must cover:**

- [ ] Find base URL, endpoint path and method in the docs
- [ ] Add required headers: Content-Type, Accept, Authorization / API key
- [ ] Build the body from the documented schema (required vs optional fields)
- [ ] Add path/query parameters
- [ ] Compare the response to the documented codes and schema

**Notes:**

<!-- TODO -->

### T07.12 · curl

**Must cover:**

- [ ] curl -X POST https://host/api -H "Content-Type: application/json" -d '{"name":"x"}'
- [ ] -u user:pass basic auth; -k skip TLS verification
- [ ] -i show response headers; -v verbose (full request and response)
- [ ] Default method is GET (POST when -d is used)

**Notes:**

<!-- TODO -->

### T07.13 · Media types

**Must cover:**

- [ ] application/json: standard REST payloads
- [ ] application/xml: XML payloads
- [ ] application/yang-data+json / +xml: RESTCONF
- [ ] Must match the Content-Type and Accept headers

**Notes:**

<!-- TODO -->

### T07.14 · Exam angle

**Must cover:**

- [ ] Fill the missing method, URL part or header from an API doc snippet
- [ ] Diagnose a failed call from the code plus its response code
- [ ] Identify which part of the response holds a value (header vs body)

**Notes:**

<!-- TODO -->

## Exam traps

<!-- Easily confused pairs, exact syntax, scenario → answer mappings. -->

## Examples

<!-- Full, runnable commands/code. No partial commands. -->

## Practice questions

<!-- 5-8 exam-style Qs. Answers in <details>. -->

## Study aids

| Aid | Type | Title | Est. min | Resource |
|---|---|---|---|---|
| T07.1 | Video | REST API Fundamentals | 22 | CBT module |
| T07.2 | Video | REST API Requests and Responses | 22 | CBT module |
| T07.3 | Video | Parameters and Payloads for REST APIs | 18 | CBT module |

- Skip / low priority: Tool demos (Postman)

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
