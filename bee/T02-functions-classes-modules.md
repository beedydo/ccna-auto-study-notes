---
id: T02
title: "Functions, classes, modules"
owner: Beedy
blueprint: "1.5"
primary_domain: D1
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-05
teach_back: 2026-10-08
cross_study: 2026-10-21
---

# T02 · Functions, classes, modules

> Owner: **Beedy** · Blueprint: **1.5** · CBT coverage: **Full** · Learn by 2026-10-05 · Teach-back 2026-10-08

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T02.01 · Why organise code

**Must cover:**

- [ ] Reuse (DRY): write logic once, call it many times
- [ ] Readability: small named units describe intent
- [ ] Maintainability: fix a bug in one place
- [ ] Testability: functions/classes can be unit-tested in isolation
- [ ] Separation of concerns: each unit does one job; teams can work on separate modules

**Notes:**

<!-- TODO -->

### T02.02 · Functions

**Must cover:**

- [ ] Define with def name(params): and call with name(args)
- [ ] Parameters = names in the definition; arguments = values passed in
- [ ] Positional vs keyword args (f(1, b=2)); default values (def f(a, b=10))
- [ ] *args collects extra positional args as a tuple; **kwargs collects extra keyword args as a dict
- [ ] return sends a value back; no return statement means the function returns None

**Notes:**

<!-- TODO -->

### T02.03 · Functions

**Must cover:**

- [ ] Local variables exist only inside the function; global variables live at module level
- [ ] LEGB lookup order: Local, Enclosing, Global, Built-in
- [ ] global keyword needed to reassign a global inside a function
- [ ] Docstring = first string inside a function/class; read by help()

**Notes:**

<!-- TODO -->

### T02.04 · Methods

**Must cover:**

- [ ] A method is a function defined inside a class and called on an object (obj.method())
- [ ] self = reference to the instance, passed automatically as the first argument
- [ ] Instance method uses self; @classmethod gets cls; @staticmethod gets neither
- [ ] Example: router.get_interfaces() vs a plain get_interfaces(router)

**Notes:**

<!-- TODO -->

### T02.05 · Classes

**Must cover:**

- [ ] class Device: defines a blueprint; d = Device(...) creates an instance (object)
- [ ] __init__(self, ...) is the constructor that sets initial attributes
- [ ] Instance attributes (self.hostname) are per object; class attributes are shared by all instances
- [ ] Objects bundle data (attributes) and behaviour (methods)

**Notes:**

<!-- TODO -->

### T02.06 · OOP principles

**Must cover:**

- [ ] Encapsulation: hide internal state behind methods (convention: _private attributes)
- [ ] Inheritance: class Switch(Device) reuses parent code; super().__init__() calls the parent constructor
- [ ] Polymorphism: different classes expose the same method name (e.g. connect()) with different behaviour
- [ ] Abstraction: expose a simple interface, hide implementation detail

**Notes:**

<!-- TODO -->

### T02.07 · Modules

**Must cover:**

- [ ] A module is any .py file; its functions/classes/variables live in its own namespace
- [ ] import math then math.sqrt(); from math import sqrt then sqrt()
- [ ] import pandas as pd creates an alias
- [ ] Avoid from x import * (pollutes the namespace, hides where names come from)

**Notes:**

<!-- TODO -->

### T02.08 · Modules

**Must cover:**

- [ ] __name__ is "__main__" when the file is run directly, and the module name when imported
- [ ] if __name__ == "__main__": main() lets a file act as both a script and an importable module
- [ ] Code outside this guard runs on import, which is usually unwanted

**Notes:**

<!-- TODO -->

### T02.09 · Packages

**Must cover:**

- [ ] A package is a directory of modules, traditionally with __init__.py
- [ ] Import from packages with dotted paths: from mypkg.utils import parse
- [ ] Standard library ships with Python (json, os, sys, unittest, xml)
- [ ] Third-party packages come from PyPI (requests, ncclient, xmltodict, pyyaml)

**Notes:**

<!-- TODO -->

### T02.10 · Dependencies

**Must cover:**

- [ ] pip install requests installs from PyPI; pip freeze > requirements.txt records versions
- [ ] pip install -r requirements.txt recreates the set on another machine
- [ ] python3 -m venv venv then source venv/bin/activate isolates project dependencies
- [ ] Why: avoid version clashes between projects and keep the system Python clean

**Notes:**

<!-- TODO -->

### T02.11 · Python basics

**Must cover:**

- [ ] Types: str, int, float, bool, None; list (ordered, mutable), tuple (ordered, immutable), dict (key/value), set (unique, unordered)
- [ ] Mutable vs immutable: lists/dicts change in place; strings/tuples do not
- [ ] Comprehensions: [x*2 for x in nums if x > 0]; {k: v for k, v in pairs}
- [ ] f-strings: f"{host} is {status}"

**Notes:**

<!-- TODO -->

### T02.12 · Python basics

**Must cover:**

- [ ] if / elif / else; comparison and logical operators (and, or, not, in)
- [ ] for item in iterable; for i, x in enumerate(list); for k, v in dict.items()
- [ ] while loops; break exits the loop, continue skips to the next iteration
- [ ] try / except SomeError / else / finally; raise to throw an exception

**Notes:**

<!-- TODO -->

### T02.13 · Exam angle

**Must cover:**

- [ ] Expect "what is the benefit of organising code into functions/classes/modules?" style questions
- [ ] Expect short Python snippets where you predict the output or spot the error
- [ ] Know vocabulary: method vs function, class vs instance, module vs package

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
| T02.1 | Video | Code structures, functions/methods, OOP videos (1.5x) | 21 | CBT: Basic Programming Control Flow |

- Skip / low priority: Syntax basics (you know them)

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
