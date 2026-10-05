---
id: T32
title: "TDD + Python unit tests"
owner: Beedy
blueprint: "1.3, 4.5"
primary_domain: D1
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-17
teach_back: 2026-10-20
cross_study: 2026-10-23
---

# T32 · TDD + Python unit tests

> Owner: **Beedy** · Blueprint: **1.3, 4.5** · CBT coverage: **Full** · Learn by 2026-10-17 · Teach-back 2026-10-20

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T32.01 · TDD

**Must cover:**

- [ ] Test-driven development: write a failing test before the code
- [ ] Red (test fails) → Green (minimum code to pass) → Refactor (clean up, tests still pass)
- [ ] Benefits: clear requirements, fewer regressions, safer refactoring, better design

**Notes:**

<!-- TODO -->

### T32.02 · Test types

**Must cover:**

- [ ] Unit: one function/class in isolation (fast, many)
- [ ] Integration: components working together (e.g. app + API)
- [ ] Functional/system/end-to-end: whole system against requirements
- [ ] Regression: re-run tests to catch previously fixed bugs returning

**Notes:**

<!-- TODO -->

### T32.03 · unittest

**Must cover:**

- [ ] import unittest
- [ ] class TestParser(unittest.TestCase):
- [ ] Each test is a method whose name starts with test_
- [ ] Tests should be independent of each other

**Notes:**

<!-- TODO -->

### T32.04 · unittest

**Must cover:**

- [ ] setUp() runs before every test; tearDown() after (setUpClass/tearDownClass once per class)
- [ ] assertEqual(a, b), assertNotEqual, assertTrue(x), assertFalse(x)
- [ ] assertIn(a, b), assertIsNone(x), assertIsInstance(x, cls)
- [ ] with self.assertRaises(ValueError): … checks an exception is raised

**Notes:**

<!-- TODO -->

### T32.05 · Running

**Must cover:**

- [ ] if __name__ == "__main__": unittest.main()
- [ ] python -m unittest (discovers test_*.py files) ; python -m unittest -v
- [ ] Output: "." pass, "F" failure (assertion false), "E" error (exception in test); final OK or FAILED

**Notes:**

<!-- TODO -->

### T32.06 · Mocking (awareness)

**Must cover:**

- [ ] unittest.mock.patch replaces a real call (e.g. requests.get) with a fake
- [ ] Lets you test API-calling code without the network

**Notes:**

<!-- TODO -->

### T32.07 · pytest (awareness)

**Must cover:**

- [ ] pytest: plain functions named test_* using bare assert statements
- [ ] Runs unittest tests too

**Notes:**

<!-- TODO -->

### T32.08 · Exam angle

**Must cover:**

- [ ] Complete a TestCase (class base, method name, assert)
- [ ] Say why a given test passes, fails or errors

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
| T32.1 | Video | Unit Tests and TDD (skip Postman testing) | 21 | CBT module |
| T32.2 | Lab | unittest TestCase for your XML parser | 40 | Docker lab |

- Skip / low priority: Postman testing

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
