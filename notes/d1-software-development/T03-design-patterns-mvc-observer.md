---
id: T03
title: "Design patterns: MVC + Observer"
owner: Bob
blueprint: "1.6"
primary_domain: D1
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-05
teach_back: 2026-10-08
cross_study: 2026-10-21
---

# T03 · Design patterns: MVC + Observer

> Owner: **Bob** · Blueprint: **1.6** · CBT coverage: **Full** · Learn by 2026-10-05 · Teach-back 2026-10-08

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T03.01 · Design patterns

**Must cover:**

- [ ] Reusable, proven solution to a recurring software design problem (a template, not code)
- [ ] Gang of Four groups: creational, structural, behavioural

**Notes:**

<!-- TODO -->

### T03.02 · MVC

**Must cover:**

- [ ] Model: data and business logic (e.g. device inventory)
- [ ] View: presentation/UI shown to the user
- [ ] Controller: receives user input, updates the model, selects the view
- [ ] Flow: user → controller → model → view → user

**Notes:**

<!-- TODO -->

### T03.03 · MVC advantages

**Must cover:**

- [ ] Separation of concerns: change the UI without touching data logic
- [ ] Parallel development of UI and back end
- [ ] Several views over the same model (web page, API, report)
- [ ] Easier testing and code reuse

**Notes:**

<!-- TODO -->

### T03.04 · Observer

**Must cover:**

- [ ] Subject keeps a list of observers (subscribers)
- [ ] When the subject state changes, it notifies every registered observer automatically
- [ ] Observers can subscribe/unsubscribe at run time (publish-subscribe idea)

**Notes:**

<!-- TODO -->

### T03.05 · Observer advantages

**Must cover:**

- [ ] Loose coupling: subject does not need to know observer details
- [ ] One change broadcast to many listeners
- [ ] Examples: GUI event listeners, model notifying views in MVC, webhooks, streaming telemetry subscriptions

**Notes:**

<!-- TODO -->

### T03.06 · Singleton (awareness)

**Must cover:**

- [ ] Ensures only one instance of a class exists; NOT named in blueprint 1.6 (skip the CBT video)

**Notes:**

<!-- TODO -->

### T03.07 · Exam angle

**Must cover:**

- [ ] Match a description/diagram to MVC or Observer; state an advantage of each

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
| T03.1 | Video | Determine When to Use Design Patterns (skip Singleton) | 18 | CBT module |

- Skip / low priority: Singleton video

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
