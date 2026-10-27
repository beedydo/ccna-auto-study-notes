---
id: T50
title: "API cheat sheet: transport, style, auth, headers, operations"
owner: Bob
blueprint: "2.x, 3.1-3.6, 3.9, 4.9"
primary_domain: D3
cbt_coverage: "None"
status: drafted   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-31
cross_study: 2026-11-04
---

# T50 · API cheat sheet: transport, style, auth, headers, operations

> Owner: **Bob** · A one-page rearrangement of T12-T25, T37, T42 and T48. No new platform facts: every cell comes from the platform note named in its row.

![T50 at a glance: 24 platforms on the same six axes, plus four-spellings, ports, status codes and the clue-to-platform map](../assets/T50/00-overview.png)

*Read a row left to right: where it listens, what style, how you log in, which headers, which operations, what success looks like. Bands: blue = one device, green = controller, orange = cloud, purple = app server.*

## The six questions (ask them of every platform)

1. **Transport:** SSH `:830` (NETCONF), HTTPS `:443` (most), `:8443` (SD-WAN, CUCM), `:9060` (ISE ERS), gRPC `:9339` (gNMI). Single-URL APIs: `/ins`, `/nuova`, `/axl/`, `/putxml`.
2. **Style:** REST/JSON (most) · RESTCONF (YANG path, `application/yang-data+json`) · NETCONF (XML RPC) · SOAP (AXL) · XML over HTTP (UCSM, xAPI) · CLI-in-JSON (NX-API CLI) · gRPC (gNMI).
3. **Auth:** Basic every call · static key · login → token header · login → cookie · signed request · key in a parameter · SSH session. Detail: T48.02.
4. **Headers:** `Accept` (what I want back) / `Content-Type` (what I send) + the auth header, whose **name** names the platform (`X-auth-access-token` = FMC, `X-Auth-Token` = Catalyst Center, `X-XSRF-TOKEN` = SD-WAN, `APIC-cookie` = ACI).
5. **Operations:** HTTP verbs, NETCONF RPCs, UCSM `configResolve*`/`configConfMos`, AXL `add/get/list/update/remove`, xAPI `xCommand/xConfiguration/xStatus/xEvent`.
6. **Success:** `200` ≠ worked (SD-WAN, UCSM, ACI), `201`/`202` ≠ live (FMC deploy, Catalyst Center task), candidate `<ok/>` ≠ live (NETCONF `commit`).

## Exam traps

- **"Bearer" names no platform.** Meraki, Webex, FDM, CML, XDR and Secure Connect all use it; FMC and Catalyst Center do not.
- **830 / 443 / 22:** NETCONF is SSH 830, RESTCONF is HTTPS 443, 22 is plain SSH.
- **`PUT` replaces, `PATCH` merges.** A leaf left out of a RESTCONF `PUT` is deleted.
- **One URL, many operations:** NX-API CLI, UCSM, AXL, xAPI. The body says what to do.
- **`Accept` vs `Content-Type`.** ISE ERS without `Accept: application/json` answers in XML.
- **Analysers don't enforce:** XDR and Malware Analytics report; Secure Endpoint, ISE and FMC act.

## Sources

- The platform notes: T12, T15-T25, T37, T42, T48 (each row's second line names its note).

## To verify

- ⚠ NSO ports (RESTCONF `:8080`, NETCONF `:2022`) are doc-example / local-install defaults (T25).
- ⚠ ISE ERS `:9060` vs `:443` on ISE 3.1+ (T23). gNMI secure default `:9339` (T17).
- ⚠ Verb lists for FDM, CML, Secure Endpoint and XDR are the generic REST set, not checked per endpoint.
