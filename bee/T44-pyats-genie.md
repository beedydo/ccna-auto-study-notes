---
id: T44
title: "pyATS + Genie"
owner: Beedy
blueprint: "5.3"
primary_domain: D5
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-18
teach_back: 2026-10-20
cross_study: 2026-10-23
---

# T44 · pyATS + Genie

> Owner: **Beedy** · Blueprint: **5.3** · CBT coverage: **Full** · Learn by 2026-10-18 · Teach-back 2026-10-20

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T44.01 · Components

**Must cover:**

- [ ] pyATS: Cisco Python test automation framework
- [ ] Genie: library of parsers (show output → structured dicts) and device feature models
- [ ] Unicon: connection library (SSH/Telnet/console, CLI handling)
- [ ] Free to use; works with physical, virtual or CML devices

**Notes:**

<!-- TODO -->

### T44.02 · Testbed

**Must cover:**

- [ ] YAML file describing devices to test
- [ ] Per device: os (iosxe, nxos), type, connections (protocol: ssh, ip, port)
- [ ] credentials (default username/password; can reference env vars)

**Notes:**

<!-- TODO -->

### T44.03 · Workflow

**Must cover:**

- [ ] from pyats.topology import loader / from genie.testbed import load
- [ ] tb = load("testbed.yaml"); dev = tb.devices["csr1"]
- [ ] dev.connect(); dev.parse("show version") → dict
- [ ] dev.execute("show run") → raw text; dev.configure("...") pushes config

**Notes:**

<!-- TODO -->

### T44.04 · Learn and diff

**Must cover:**

- [ ] dev.learn("ospf") builds a vendor-neutral model of a feature
- [ ] genie learn ospf --testbed-file tb.yaml --output before (CLI)
- [ ] genie diff before after shows what changed after a change window

**Notes:**

<!-- TODO -->

### T44.05 · AEtest

**Must cover:**

- [ ] AEtest = test harness: CommonSetup → Testcase(s) → CommonCleanup
- [ ] Sections decorated with @aetest.setup / @aetest.test / @aetest.cleanup
- [ ] pyats run job job.py runs tests and produces reports

**Notes:**

<!-- TODO -->

### T44.06 · CML link

**Must cover:**

- [ ] CML (Cisco Modeling Labs) provides virtual topologies to run pyATS tests against
- [ ] Blueprint 5.3 covers both; Bob covers CML in T25

**Notes:**

<!-- TODO -->

### T44.07 · Use cases

**Must cover:**

- [ ] Pre/post-change checks (snapshot → change → snapshot → diff)
- [ ] Automated network tests inside a CI/CD pipeline
- [ ] Compliance/state verification

**Notes:**

<!-- TODO -->

### T44.08 · Exam angle

**Must cover:**

- [ ] Pick pyATS/Genie for a test or validation scenario (vs CML for simulation)
- [ ] Read a short pyATS snippet and say what it does

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
| T44.1 | Video | Automate and Test Networks with pyATS | 50 | CBT module |

- Skip / low priority: Long demos

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
