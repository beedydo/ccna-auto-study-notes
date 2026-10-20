# T32 · TDD + Python unit tests: essentials

> Blueprint 1.3: test-driven development concepts; 4.5: construct a Python unit test · Full note: [bee/T32-tdd-python-unit-tests.md](../bee/T32-tdd-python-unit-tests.md) · Teach-back 2026-11-01

![T32 at a glance: TDD cycle, test types, unittest anatomy, output codes, mocking, pytest](../assets/T32/00-overview.png)

*Read top to bottom: the red-green-refactor loop, the test-type pyramid, the anatomy of a `TestCase` (numbers show run order), the `.`/`F`/`E` output codes, then mocking and pytest.*

## 🧭 The big idea

This topic answers two questions:

| | Question | Answer | Analogy |
|---|---|---|---|
| 🔁 | **In what order do you write tests and code?** | Test first. That is **test-driven development (TDD)**: write the test, watch it fail, only then write code. The test is the requirement written as code. | **write the marking scheme before the answer.** You know exactly what "done" looks like, and you can re-mark the answer every time you edit it. |
| 🧬 | **How do you write and read a Python test?** | With the built-in `unittest` module: a class, methods named `test_*`, and `self.assert*` checks. | |
| 🎭 | **How do you test API code without the network?** (mocking, section 7) | swap the real call for a mock | **a stunt double.** The real actor (the network call) is swapped for a double who does exactly what the script says, so the scene (your parsing code) can be filmed safely and repeatedly. |

- 🎯 **What the exam asks:** the order of the TDD cycle and its benefits (1.3); the kinds of test (unit, integration, functional, regression); and how to complete or read a `unittest` test, including whether it **passes, fails or errors** (4.5).

## 🟥 Must know

### 1. 🔁 The TDD cycle: red, green, refactor

1. 🔴 **Red:** write a test for **one** new requirement and run it. It must actually **fail**, because the feature doesn't exist yet. (A test that passes before the code exists tests nothing.)
2. 🟢 **Green:** write the **minimum** code that makes the test pass, nothing more.
3. 🔵 **Refactor:** clean the code up while every test stays green. Refactoring changes the code, **never the behaviour and never the tests**.
4. Then the next requirement starts as a new failing test.

![TDD red-green-refactor cycle](../assets/T32/01-tdd-cycle.png)

*The loop never starts with code. Red must really fail before you write the fix.*

**🧪 The lab cycle**, one requirement: "`enabled` must be a Python `bool`, and I need a list of enabled interface names".

| Step | What changed in `iflib.py` | Result |
|---|---|---|
| 🔴 Red | nothing yet: `enabled` is the string `'true'`, no `enabled_names()` | `FAILED (failures=1, errors=1)` |
| 🟢 Green | add `== "true"` and a 2-line `enabled_names()`: the **minimum** | `OK` |
| 🔵 Refactor | pull repeated code into `_text()`, add docstrings | still `OK`, tests untouched |

- The red run had one **FAIL** (`AssertionError: 'true' is not True`) and one **ERROR** (`AttributeError: module 'iflib' has no attribute 'enabled_names'`). The other 6 old tests kept passing.

![Animated red-green-refactor cycle on iflib.py](../assets/T32/02-red-green.gif)

*One requirement through the loop: the red run shows `...FE...` and `FAILED (failures=1, errors=1)`, the fix turns it green (`OK`), and the refactor stays `OK` with the tests untouched.*

**🏆 Benefits (the words blueprint 1.3 wants):**

| | Benefit | Why |
|---|---|---|
| 📋 | **Clear requirements** | the test is an executable spec |
| 🛡️ | **Fewer regressions** | old requirements stay as tests and are re-run on every change |
| 🧹 | **Safer refactoring** | green tests prove nothing broke |
| 🧩 | **Better design** | testable code tends to be small functions with clear inputs and outputs |
| ➕ | Also | living documentation and fast feedback in CI |

| ⚠️ Cost | ❌ Distractors to reject |
|---|---|
| more code up front and slower first delivery | "TDD removes the need for integration tests" and "TDD guarantees bug-free code". Neither is true. |

### 2. 🧪 Kinds of test

| | Type | What it checks | Scenario cue |
|---|---|---|---|
| 🔬 | **Unit** | one function or class **in isolation**. Network, database and files are faked (mocked). Fast, so you have many. | "test the parser with a sample XML string, no device" |
| 🔗 | **Integration** | two or more components **working together** (your app + a real API), through the real interface between them | "check the script can log in to Catalyst Center and parse the real reply" |
| 🌐 | **Functional / system / end-to-end** | the **whole system** checked against the requirements | "check the new VLAN appears on the switch after the whole workflow" |
| 🔄 | **Regression** | **re-running** existing tests (any layer) after a change, to catch old bugs coming back. A habit, not a layer. | "a bug fixed last month came back" |

![Test types pyramid with examples from labs/T32](../assets/T32/03-test-types.png)

*Bottom = fast, many, isolated. Top = slow, few, real systems. Regression is a habit, not a layer.*

- TDD tests are unit tests. TDD doesn't replace the other layers.
- Some sources use "functional" for one feature and "system" or "end-to-end" for the whole stack; the exam treats them as one family. ⚠ verify the wording in the N2K practice questions.

### 3. 🧬 Anatomy of a unittest test

> 💡 **`unittest`** = Python's built-in test framework (no `pip install`), modelled on Java's JUnit. Every "complete the code" question is built from these lines:

```python
import os
import unittest                                        # 1. stdlib module

import iflib                                           #    the code under test

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "fixtures", "interfaces.xml")   # sample XML: the test never touches a device

class TestParseInterfaces(unittest.TestCase):          # 2. subclass TestCase (capital T, capital C)
    @classmethod
    def setUpClass(cls):                               #    runs ONCE for the class: read the sample XML
        with open(FIXTURE, encoding="utf-8") as f:
            cls.xml_text = f.read()

    def setUp(self):                                   #    runs before EVERY test: a fresh parsed list
        self.intfs = iflib.parse_interfaces(self.xml_text)

    def test_enabled_is_bool(self):                    # 3. a method, takes self, name starts with "test"
        self.assertIs(self.intfs[1]["enabled"], False) # 4. asserts are methods called on self

if __name__ == "__main__":                             # 5. run this file directly...
    unittest.main()                                    #    ...and unittest finds and runs the tests
```

**🏷️ Name rules:**

| Name | Collected? |
|---|---|
| method `test_x` / `testX` | ✅ both run: the runner collects every method whose name **starts with `test`** |
| method `check_names()` | ❌ **silently ignored**: no error, no warning, the count just drops. In the lab, renaming one test changed `Ran 8 tests` to `Ran 7 tests`, still `OK`. |
| file `test_iflib.py` | ✅ found: test files must match **`test*.py`** to be discovered |
| file `iflib_test.py` | ❌ not found |

> 💡 **Tests must be independent.** Each must pass alone and in any order. Inside a class, unittest runs methods in **alphabetical** order, not the order written. `setUp` gives each test fresh data so one test can't break another.

### 4. 🪝 Fixtures: setUp, tearDown and the class-level hooks

> 💡 **Fixtures** = the setup a test needs and the cleanup after it.

![Fixture run order for one TestCase class](../assets/T32/04-fixture-order.png)

*Class-level hooks run once; `setUp` and `tearDown` wrap every single test, and `tearDown` runs even when the test failed.*

| Hook | When it runs | Needs `@classmethod`? |
|---|---|---|
| `setUpClass(cls)` | **once**, before the first test in the class | ✅ yes |
| `setUp(self)` | before **every** test | ❌ no |
| `tearDown(self)` | after **every** test, pass or fail (if `setUp` succeeded) | ❌ no |
| `tearDownClass(cls)` | **once**, after the last test | ✅ yes |

- ⚠️ **Names are exact camelCase.** `def setup(self):` is just an ordinary method that never runs, so every test relying on its data errors with `AttributeError`.
- If `setUp()` raises, that test counts as an **error** and its body doesn't run.
- 🧹 Why `tearDown`: cleanup there runs even when the test fails, so leftover state (temp files, a counter) can't leak into the next test.

### 5. ✔️ Assert methods

> 💡 Each one is a `self.` method; it passes silently or raises `AssertionError` (→ **FAIL**).

| Method | Passes when |
|---|---|
| `assertEqual(a, b)` / `assertNotEqual` | `a == b` / `a != b` |
| `assertTrue(x)` / `assertFalse(x)` | `x` is truthy / falsy |
| `assertIs(a, b)` | same object (`a is b`) |
| `assertIn(a, b)` | `a in b` (the thing first, then where to look) |
| `assertIsNone(x)` / `assertIsNotNone` | `x is None` |
| `assertIsInstance(x, cls)` | `isinstance(x, cls)` |
| `assertRaises(Exc)` | the block raises `Exc` |

| ❌ `assertTrue(x)` | ✅ `assertIs(x, True)` |
|---|---|
| **checks truthiness, not `== True`.** `assertTrue("false")` passes, because any non-empty string is truthy. | use it when the type matters. That is exactly what caught the red-step bug (`'true'` string instead of `True`). |

**`assertRaises`, the context-manager form to learn:**

```python
with self.assertRaises(ValueError):   # passes only if the block raises ValueError
    make_device(self.row)
```

| Block raises… | Result |
|---|---|
| `ValueError` | ✅ pass |
| **nothing** | **FAIL** (`ValueError not raised`) |
| a **different** exception (e.g. `KeyError`) | it isn't caught, escapes the test → **ERROR** |

- Old call form: `self.assertRaises(ValueError, make_device, row)`: pass the function and its arguments **without calling it**.

### 6. ▶️ Running tests and reading the output

```bash
python3 test_iflib.py                                   # runs the file via unittest.main() under the __main__ guard
python3 -m unittest                                     # discovery: every test*.py under the current directory
python3 -m unittest -v test_iflib                       # verbose: one line per test (ok / FAIL / ERROR)
python3 -m unittest test_inventory.TestVlans.test_vlan_range   # one test, by dotted path
```

| Char | `-v` word | Meaning |
|---|---|---|
| `.` | `ok` | ✅ pass |
| `F` | `FAIL` | ❌ an `assert*` was false (`AssertionError`) |
| `E` | `ERROR` | 💥 **any other** exception: typo, `KeyError`, `AttributeError`, a crash in `setUp`, a failed import |
| `s` | `skipped` | ⏭️ `@unittest.skip` or `skipUnless` |

| Last line | Exit code |
|---|---|
| `OK` (maybe `OK (skipped=1)`) | 0 |
| `FAILED (failures=N, errors=M)` | 1, which is how CI turns the build red |

**🔍 Pass / fail / error decision** for any snippet:

1. Is the method collected? Not starting with `test` → **not run at all**.
2. Does `setUp` or the body raise something **other than** `AssertionError` first? → **ERROR**.
3. Does an `assert*` evaluate false, or `assertRaises` see no exception? → **FAIL**.
4. Otherwise → **pass**.

### 7. 🎭 Mocking: test API code without the network

| ❌ Problem | ✅ Fix |
|---|---|
| a unit test must not need a real device, credentials or a network | **a mock** (the stunt double) = a stand-in object that accepts any call, returns what you tell it, and **records how it was called**. `unittest.mock` is in the standard library. |

- The test below is a method of a `TestCase` class whose `setUpClass` loaded `self.xml_text` (full file in the full note):

```python
from unittest.mock import patch

URL = "https://10.10.20.48/restconf/data/ietf-interfaces:interfaces"   # the URL the code should build

@patch("netclient.requests.get")                       # swap the real requests.get for a fake during this test
def test_parses_reply(self, mock_get):                 # the fake arrives as an extra argument
    mock_get.return_value.status_code = 200            # the fake response's status
    mock_get.return_value.text = self.xml_text         # the fake response's body: real sample XML
    intfs = netclient.get_interfaces("10.10.20.48", "developer", "pw")   # real code, fake network
    self.assertEqual([i["name"] for i in intfs], ["GigabitEthernet1", "GigabitEthernet2"])
    mock_get.assert_called_once_with(                  # prove the code built the right request
        URL,
        auth=("developer", "pw"),
        headers={"Accept": "application/yang-data+xml"},
        timeout=10,
    )
```

![How patch replaces requests.get in test_parses_reply](../assets/T32/05-mock-patch.png)

*The real `requests.get` is never called. The parsing code is real and really tested; only the network edge is faked.*

- `side_effect = requests.HTTPError(...)` makes a call **raise** instead, which tests the 401 path without a device.

> 🎯 **Patch where the name is looked up**, not where it is defined.

| The code does… | Patch |
|---|---|
| `import requests` (as `netclient` does) | `"netclient.requests.get"` |
| `from requests import get` | `"netclient.get"` |

## ⚠️ Exam traps

| ❌ Looks like… | ✅ Actually… |
|---|---|
| ▶️ `F` and `E` mean the same | **`F` vs `E`:** `F` = an assertion was false. `E` = any other exception, before or instead of the assert. |
| 🏷️ `def check_vlan(self):` runs as a test | **No `test` prefix, no run.** `def check_vlan(self):` never runs and never reports. `def setup(self):` (lowercase) is never called either, so dependent tests error. |
| ✔️ wrong exception inside `assertRaises` = FAIL | **`assertRaises(ValueError)` around code that raises `KeyError` = ERROR**, not FAIL. And `self.assertRaises(ValueError, make_device(row))` calls the function first, so the exception escapes → ERROR. Pass it uncalled, or use `with`. |
| ✔️ `assertTrue("false")` fails | **`assertTrue("false")`, `assertTrue([0])`, `assertTrue(10, 20)` all pass.** The second argument of `assertTrue` is only the failure message. |
| 🧬 base class `unittest.TestSuite` or `unittest.Test` | **The base class is always `unittest.TestCase`**, not `unittest.TestSuite` or `unittest.Test`. |
| 🔁 code first, tests after = TDD | **Code first, tests after is not TDD.** The order is red, green, refactor; refactor never touches the tests. |

<details><summary><b>🟨 Should know (second pass)</b></summary>

### ▶️ Runner and errors

| Point | Detail |
|---|---|
| **More runner options** | `python3 -m unittest -k enabled` runs only tests whose name contains "enabled". Discovery only searches subfolders that are packages (have `__init__.py`). ⚠ verify: this behaviour changed in Python 3.11 and again in 3.14. |
| **A failed import is an error too** | run the suite without `requests` installed and `test_netclient` can't even be imported → `ModuleNotFoundError` shows as an **error** |
| **Shared state breaks independence** | in the lab, moving a shared dict into `setUpClass()` let two tests change it, and an unrelated test then errored. Fresh data per test (`setUp`) prevents that. |
| **Skipping an integration test** | `@unittest.skipUnless(os.environ.get("RESTCONF_HOST"), "...")` keeps one real-device test in the file that only runs when you point it at a sandbox |

### ✔️ Assert details

- **`cm.exception`:** `with self.assertRaises(ValueError) as cm:` keeps the caught exception, so you can then check its message with `self.assertIn("no hostname", str(cm.exception))`.

| `assertEqual(1, True)` | `assertIs(1, True)` |
|---|---|
| ✅ passes (`1 == True`) | ❌ fails |

### 🎭 Mock forms

| `@patch(...)` decorator | `with patch(...) as mock_get:` |
|---|---|
| passes the mock in as an argument | active only inside the block |

- Patching the wrong module (e.g. `"iflib.requests.get"` when `iflib` doesn't import `requests`) → `AttributeError` → test **error**.

### 🐍 pytest (awareness)

> 💡 A third-party runner (`pip install pytest`).

| | 🐍 pytest | 🧬 unittest |
|---|---|---|
| Tests are | plain functions named `test_*` | `class ...(unittest.TestCase)` methods |
| Checks | bare `assert` | `self.assert...` |
| Setup | `@pytest.fixture` | `setUp` / `setUpClass` |
| Exceptions | `with pytest.raises(E):` | `with self.assertRaises(E):` |
| Runs the other style? | ✅ **pytest runs unittest tests too** | ❌ **unittest does not run pytest-style functions** |

- Recognition rule: bare `assert` in plain functions = pytest; `class ...(unittest.TestCase)` with `self.assert...` = unittest.

</details>

> 📚 **Recognise only, details in the full note:** `assertGreater`, `assertIsNot` / `assertNotIn`, `side_effect` as a list, `MagicMock`, `-p no:cacheprovider`, pytest also discovering `*_test.py`, the DevNet sandbox integration test (⚠ verify host and credentials).

## ✍️ Quick self-check
<details><summary>Q1. Put in order: refactor; watch the test fail; write a test; write the minimum code.</summary>Write a test, watch it fail, write the minimum code, refactor. That is red, green, refactor.</details>
<details><summary>Q2. A class has 4 tests, <code>setUp</code>, <code>tearDown</code> and <code>setUpClass</code>. One test fails. How often does each hook run?</summary><code>setUp</code> 4, <code>tearDown</code> 4, <code>setUpClass</code> 1. <code>tearDown</code> still runs after a failed test.</details>
<details><summary>Q3. Output <code>..F.E.</code>: what happened to tests 3 and 5?</summary>Test 3 had a false assertion (failure); test 5 raised some other exception (error).</details>
<details><summary>Q4. You need a CI test of code that calls the Meraki API, with no network. What do you use?</summary>A unit test that patches <code>requests.get</code> with <code>unittest.mock.patch</code> and sets its <code>return_value</code> to a sample reply.</details>
<details><summary>Q5. A bug fixed two months ago reappears after a refactor. Which testing should have caught it?</summary>Regression testing: keep a test for every fixed bug and re-run all tests after each change.</details>
<details><summary>Q6. <code>with self.assertRaises(ValueError):</code> wraps a call that raises nothing. Pass, fail or error?</summary>FAIL: <code>ValueError not raised</code>. (If it raised a <code>KeyError</code> instead, that would be an ERROR.)</details>
<details><summary>Q7. Which two benefits of TDD are the answer to "why write the test first"?</summary>Any of: clear requirements (the test is the spec), fewer regressions, safer refactoring, better design. Not "bug-free code" and not "no integration tests needed".</details>

## 🗣️ Say it out loud
- 🔁 "Red, green, refactor: test first, minimum code, then tidy with the tests untouched."
- ▶️ "F is a false assert; E is any other exception."
- 🏷️ "No `test` prefix, no run, and no warning either."
- 🪝 "setUp and tearDown wrap every test; setUpClass runs once and needs `@classmethod`."
- 🎭 "Patch where it's looked up, not where it's defined."
