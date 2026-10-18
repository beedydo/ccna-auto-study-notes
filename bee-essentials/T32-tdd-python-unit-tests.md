# T32 · TDD + Python unit tests: essentials

> Blueprint 1.3, 4.5 · Full note: [bee/T32-tdd-python-unit-tests.md](../bee/T32-tdd-python-unit-tests.md) · Teach-back 2026-11-01

## In one picture
![T32 at a glance: TDD cycle, test types, unittest anatomy, output codes, mocking, pytest](../assets/T32/00-overview.png)
*Read top to bottom: the red-green-refactor loop, the test-type pyramid, the anatomy of a `TestCase` (numbers show run order), the `.`/`F`/`E` output codes, then mocking and pytest.*

## The big idea
- **Test-driven development (TDD)** means you write the test first, watch it fail, and only then write code. The test is the requirement written as code.
- An analogy: it is like writing the exam marking scheme before writing the answer. You know exactly what "done" looks like, and you can re-mark the answer every time you edit it.
- The exam asks three things: the order of the TDD cycle (blueprint 1.3), the kinds of test (unit, integration, functional, regression), and how to complete or read a Python `unittest` test, including whether it passes, fails or errors (blueprint 4.5).

## What you need to know

### 1. The TDD cycle: red, green, refactor
- **Red:** write a test for one new requirement and run it. It must actually fail, because the feature doesn't exist yet.
- **Green:** write the **minimum** code that makes the test pass, nothing more.
- **Refactor:** clean the code up while every test stays green. Refactoring changes the code, never the behaviour, and never the tests.
- Then the next requirement starts as a new failing test.

![TDD red-green-refactor cycle](../assets/T32/01-tdd-cycle.png)
*The loop never starts with code. Red must really fail before you write the fix.*

![Animated red-green-refactor cycle on iflib.py](../assets/T32/02-red-green.gif)
*One requirement through the loop: the red run shows `...FE...` and `FAILED (failures=1, errors=1)`, the fix turns it green (`OK`), and the refactor stays `OK` with the tests untouched.*

- In the lab, the red run had one **FAIL** (the code returned the string `'true'` instead of the bool `True`) and one **ERROR** (`enabled_names()` didn't exist yet, so Python raised `AttributeError`). The other 6 old tests kept passing.
- **Benefits** (the words blueprint 1.3 wants): **clear requirements** (the test is an executable spec), **fewer regressions** (old requirements stay as tests), **safer refactoring** (green tests prove nothing broke), and **better design** (testable code tends to be small functions with clear inputs and outputs). Also living documentation and fast feedback in CI.
- **Cost:** more code up front and slower first delivery.
- Distractors to reject: "TDD removes the need for integration tests" and "TDD guarantees bug-free code". Neither is true.

### 2. Kinds of test

![Test types pyramid with examples from labs/T32](../assets/T32/03-test-types.png)
*Bottom = fast, many, isolated. Top = slow, few, real systems. Regression is a habit, not a layer.*

| Type | What it checks | Real dependencies? |
|---|---|---|
| **Unit** | one function or class **in isolation** | no: network, database and files are faked |
| **Integration** | two or more components **working together** (app + API) | yes, the real interface between them |
| **Functional / system / end-to-end** | the **whole system** against the requirements | yes, everything |
| **Regression** | any of the above, **re-run** after a change | same as the original tests |

- Scenario cues: "test the parser with a sample XML string, no device" is **unit**. "Check the script can log in to Catalyst Center and parse the real reply" is **integration**. "Check the new VLAN appears on the switch after the whole workflow" is **functional/end-to-end**. "A bug fixed last month came back" is **regression**.
- TDD tests are unit tests. TDD doesn't replace the other layers.
- Some sources use "functional" for one feature and "system" or "end-to-end" for the whole stack; the exam treats them as one family. ⚠ verify the wording in the N2K practice questions.

### 3. Writing a unittest test
- **`unittest`** is Python's built-in test framework (no `pip install`), modelled on Java's JUnit.
- Every "complete the code" question is built from these four lines:

```python
import unittest
class TestParseInterfaces(unittest.TestCase):      # subclass TestCase (capital T, capital C)
    def test_enabled_is_bool(self):                # a method, name starts with "test"
        self.assertIs(self.intfs[1]["enabled"], False)   # asserts are called on self
```

- The runner collects every method whose name **starts with `test`**. `test_x` and `testX` both run.
- A method called `check_names()` is **silently ignored**: no error, no warning, the test count just drops. In the lab, renaming one test changed `Ran 8 tests` to `Ran 7 tests`, still `OK`.
- Test files must match **`test*.py`** to be discovered. `test_iflib.py` is found; `iflib_test.py` is not.
- **Tests must be independent.** Each must pass alone and in any order. Inside a class, unittest runs methods in **alphabetical** order, not the order written.
- In the lab, moving a shared dict into `setUpClass()` let two tests change it, and an unrelated test then errored. Fresh data per test (`setUp`) prevents that.

### 4. Setup, cleanup and assert methods
- **Fixtures** are the setup a test needs and the cleanup after it.

![Fixture run order for one TestCase class](../assets/T32/04-fixture-order.png)
*Class-level hooks run once; `setUp` and `tearDown` wrap every single test, and `tearDown` runs even when the test failed.*

| Hook | When it runs | Needs `@classmethod`? |
|---|---|---|
| `setUpClass(cls)` | **once**, before the first test in the class | yes |
| `setUp(self)` | before **every** test | no |
| `tearDown(self)` | after **every** test, pass or fail (if `setUp` succeeded) | no |
| `tearDownClass(cls)` | **once**, after the last test | yes |

- Names are exact camelCase. A typo like `def setup(self):` is just an ordinary method that never runs, so every test that relies on it errors with `AttributeError`.
- If `setUp()` raises, that test counts as an **error** and its body doesn't run.

| Method | Passes when |
|---|---|
| `assertEqual(a, b)` / `assertNotEqual` | `a == b` / `a != b` |
| `assertTrue(x)` / `assertFalse(x)` | `x` is truthy / falsy |
| `assertIs(a, b)` | same object (`a is b`) |
| `assertIn(a, b)` | `a in b` (the thing first, then where to look) |
| `assertIsNone(x)` / `assertIsNotNone` | `x is None` |
| `assertIsInstance(x, cls)` | `isinstance(x, cls)` |
| `assertRaises(Exc)` | the block raises `Exc` |

- `assertTrue` checks **truthiness**, not `== True`. `assertTrue("false")` passes, because any non-empty string is truthy. Use `assertIs(x, True)` when the type matters.
- The `assertRaises` form to learn is the context manager:

```python
with self.assertRaises(ValueError):
    make_device(self.row)
```

- If the block raises nothing, the result is a **FAIL** (`ValueError not raised`). If it raises a **different** exception such as `KeyError`, that escapes and the result is an **ERROR**.
- The old call form passes the function and its arguments without calling it: `self.assertRaises(ValueError, make_device, row)`.

### 5. Running tests and reading the output
- `python3 test_iflib.py` runs the file through `unittest.main()`, which sits under `if __name__ == "__main__":`.
- `python3 -m unittest` uses **discovery**: it runs every `test*.py` under the current directory. Add `-v` for one line per test.
- `python3 -m unittest test_inventory.TestVlans.test_vlan_range` runs one test, and `-k enabled` runs only tests whose name contains "enabled".
- Discovery only searches subfolders that are packages (have `__init__.py`). ⚠ verify: this behaviour changed in Python 3.11 and again in 3.14.

| Char | `-v` word | Meaning |
|---|---|---|
| `.` | `ok` | pass |
| `F` | `FAIL` | an `assert*` was false (`AssertionError`) |
| `E` | `ERROR` | **any other** exception: typo, `KeyError`, `AttributeError`, a crash in `setUp`, a failed import |
| `s` | `skipped` | `@unittest.skip` or `skipUnless` |

- The last line is `OK` (maybe `OK (skipped=1)`) or `FAILED (failures=N, errors=M)`. The process exits 0 for OK and 1 for FAILED, which is how CI turns the build red.

### 6. Mocking and pytest (awareness)
- A unit test must not need a real device, credentials or a network. A **mock** is a stand-in object that accepts any call, returns what you tell it, and records how it was called. `unittest.mock` is in the standard library.
- `@patch("netclient.requests.get")` swaps the real `requests.get` for a fake while the test runs, then puts the original back.

![How patch replaces requests.get in test_parses_reply](../assets/T32/05-mock-patch.png)
*The real `requests.get` is never called. The parsing code is real and really tested; only the network edge is faked.*

- `mock_get.return_value` is the fake response; setting `.text` gives the parser real XML to work on. `side_effect = requests.HTTPError(...)` makes a call raise, which tests the 401 path. `assert_called_once_with(...)` proves the code built the right request.
- **Patch where the name is looked up**, not where it is defined. `netclient` does `import requests`, so you patch `"netclient.requests.get"`. If the code did `from requests import get`, you would patch `"netclient.get"`.
- **pytest** is a third-party runner (`pip install pytest`). Tests are plain functions named `test_*` using bare `assert`, setup comes from `@pytest.fixture`, and exceptions use `with pytest.raises(E):`.
- **pytest runs unittest tests too, but unittest does not run pytest-style functions.** Recognition rule: bare `assert` in plain functions means pytest; `class ...(unittest.TestCase)` with `self.assert...` means unittest.

## Exam traps (the ones that catch people)
- An `F` and an `E` look alike, but `F` means an assertion was false, while `E` means any other exception happened before or instead of the assert.
- A test method named `check_vlan` looks like a test, but it never runs and never reports, because the name doesn't start with `test`.
- `setup` looks like `setUp`, but the lowercase version is never called, so every test that needs its data errors.
- `with self.assertRaises(ValueError):` around code that raises `KeyError` looks like a failure, but it is an **error**, because the `KeyError` isn't caught.
- `self.assertRaises(ValueError, make_device(row))` looks fine, but it calls the function first, so the exception escapes and the test errors. Pass the function uncalled, or use `with`.
- `assertTrue("false")`, `assertTrue([0])` and `assertTrue(10, 20)` all look like they should fail, but they pass. The second argument of `assertTrue` is only the failure message.
- The base class looks like it could be `unittest.TestSuite` or `unittest.Test`, but it is always `unittest.TestCase`.
- Writing code first and tests after looks like TDD, but it isn't. The order is red, green, refactor.

## Quick self-check
<details><summary>Q1. Put in order: refactor; watch the test fail; write a test; write the minimum code.</summary>Write a test, watch it fail, write the minimum code, refactor. That is red, green, refactor.</details>
<details><summary>Q2. A class has 4 tests, `setUp`, `tearDown` and `setUpClass`. One test fails. How often does each hook run?</summary>`setUp` 4, `tearDown` 4, `setUpClass` 1. `tearDown` still runs after a failed test.</details>
<details><summary>Q3. Output `..F.E.`: what happened to tests 3 and 5?</summary>Test 3 had a false assertion (failure); test 5 raised some other exception (error).</details>
<details><summary>Q4. You need a CI test of code that calls the Meraki API, with no network. What do you use?</summary>A unit test that patches `requests.get` with `unittest.mock.patch` and sets its `return_value` to a sample reply.</details>
<details><summary>Q5. A bug fixed two months ago reappears after a refactor. Which testing should have caught it?</summary>Regression testing: keep a test for every fixed bug and re-run all tests after each change.</details>

## Cheat lines to say out loud
- "Red, green, refactor: test first, minimum code, then tidy with the tests untouched."
- "F is a false assert; E is any other exception."
- "No `test` prefix, no run, and no warning either."
- "setUp and tearDown wrap every test; setUpClass runs once and needs `@classmethod`."
- "Patch where it's looked up, not where it's defined."
