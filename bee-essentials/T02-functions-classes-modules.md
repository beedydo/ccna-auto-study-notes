# T02 · Functions, classes, modules: essentials

> Blueprint 1.5 · Full note: [bee/T02-functions-classes-modules.md](../bee/T02-functions-classes-modules.md) · Teach-back 2026-10-11

## In one picture
![T02 at a glance: every concept on one page](../assets/T02/00-overview.png)
*Read it top to bottom: each row is one concept area, the numbered examples come from the reference program in `labs/T02/`, and the red boxes are exam traps.*

## The big idea
Organising code is like organising a toolbox: a function is one tool, a class is a kit that keeps related tools and their parts together, and a module or package is the drawer the kit lives in. Blueprint 1.5 mostly asks **why** you organise code this way (reuse, readability, maintainability, testability), not the syntax itself. The rest of the exam questions are short Python snippets where you predict the output or spot the error, so the traps below matter more than the basics you already know.

## What you need to know

### 1. Why organise code at all (the 1.5 answer)
- Write the logic once and call it many times. This is **reuse**, often called **DRY** ("Don't Repeat Yourself").
- Small, well-named units make the code read like a list of steps. This is **readability**.
- When the logic lives in one place, you fix a bug in one place. This is **maintainability**.
- A function that takes plain inputs and returns a value can be tested on its own without a real device. This is **testability** (unit testing, T32).
- Each unit does one job, so two people can own one file each. This is **separation of concerns** (modularity).
- Functions organise logic, classes organise data and logic together, and modules and packages organise files.
- Wrong answers on the exam claim "faster execution" or "less memory". Organising code does not make it faster.

### 2. Functions: parameters, arguments and return
- A **parameter** is the name in the `def` line; an **argument** is the value you pass in the call.
- Positional arguments match by order and must come first; keyword arguments match by name. `f(site="x", rows)` is a `SyntaxError`.
- One signature from the note shows every kind:

```python
def build_inventory(rows, *extra_rows, site="lab", **tags):
```

| Parameter | Kind | What it receives |
|---|---|---|
| `rows` | positional | the first argument |
| `*extra_rows` | extra positional arguments, collected as a **tuple** | `({"hostname": "box1", ...},)` |
| `site="lab"` | keyword with a **default value** | `"sandbox"` if passed, otherwise `"lab"` |
| `**tags` | extra keyword arguments, collected as a **dict** | `{"owner": "beedy", "env": "dev"}` |

- Any parameter written after `*extra_rows` can only be passed by keyword.
- Default values are worked out **once**, when `def` runs, not on every call. That is why `def f(x=[])` shares one list across all calls.
- `return a, b` sends back a **tuple**, which you can unpack with `a, b = f()`.
- A function with no `return` statement returns **`None`**.

### 3. Scope: where Python looks for a name
- A variable created inside a function is **local** and disappears when the function ends. A variable at the top of the file is **global** (module level).
- Python searches for a name in the **LEGB** order: **L**ocal, then **E**nclosing (an outer function), then **G**lobal (the module), then **B**uilt-in (like `len`).
- Reading a global inside a function needs nothing special.
- Assigning to a global inside a function needs the `global` keyword. Without it, the assignment makes the name local for the whole function, so `count += 1` fails with `UnboundLocalError`.
- `nonlocal` is the same idea for a variable in an enclosing function.
- A **docstring** is the first string inside a function, class or module. `help(f)` or `f.__doc__` reads it.

### 4. Classes, objects and the three method kinds
- A **class** is a blueprint (`class Device:`). An **instance** (object) is one thing built from it.
- `__init__(self, ...)` runs automatically when an object is created and sets its starting attributes. Strictly it is the initialiser, but the exam calls it the **constructor**.
- **Instance attributes** (`self.hostname`) belong to one object. **Class attributes** (written in the class body, like `vendor = "Cisco"`) are shared by every instance.
- Update a shared counter through the class: `Device.connections += 1`. Writing `self.connections += 1` creates a new attribute on that one object, which hides the class value, so the shared count stays at 0.
- A **method** is a function defined inside a class and called on an object: `router.get_interfaces()` rather than `get_interfaces(router)`.
- `self` is the object the method was called on. Python passes it automatically, and it must be the first parameter. It is a naming convention, not a keyword.

| Kind | First parameter | Called as | Used for |
|---|---|---|---|
| Instance method | `self` (the object) | `d.connect()` | read or change one object |
| `@classmethod` | `cls` (the class) | `IOSXE.from_dict(row)` | alternative constructor |
| `@staticmethod` | none | `Device.is_valid_vlan(4095)` | helper that needs no object or class |

- A classmethod uses `cls(...)` rather than a hard-coded class name, so calling it on a child class builds the child class.

### 5. The four OOP principles
| Principle | Plain meaning | Example in the note |
|---|---|---|
| **Encapsulation** | Keep internal state inside the object and expose it through methods | `_token` is internal; callers use `is_connected()` |
| **Inheritance** | A child class reuses and extends a parent | `class IOSXE(Device)` |
| **Polymorphism** | Same method name, different behaviour per class | `d.connect()` gives RESTCONF, NX-API or SSH |
| **Abstraction** | Simple interface, details hidden | `main()` calls `connect()` without knowing ports or URLs |

- Python has no `private` keyword. A leading `_name` means "internal" by convention, and `__name` triggers **name mangling** to `_Device__name`.
- If a child class defines its own `__init__`, the parent's `__init__` does **not** run unless the child calls `super().__init__(...)`. Forget it and the parent's attributes are never set, giving an `AttributeError` later.
- If the child defines no `__init__`, it inherits the parent's automatically.
- **Overriding** means the child defines a method with the same name; it can still call `super().connect()` to reuse the parent's logic.

![Animated super().__init__ call chain](../assets/T02/01-super-init.gif)
*Watch the order: the child's `__init__` runs first, `super()` jumps to the parent to set the shared attributes, then control returns to the child; the last frame shows what breaks when the `super()` line is deleted.*

### 6. Modules, packages and the `__name__` guard
- A **module** is any `.py` file, and each module has its own namespace, so names in different files don't clash.
- A **package** is a folder of modules, traditionally with an `__init__.py`. A **dotted path** maps to folders: `netlib.devices` is `netlib/devices.py`.
- `__init__.py` runs when the package is first imported, and it can re-export names so callers write `from netlib import IOSXE`.

| Statement | Names it creates | How you use it |
|---|---|---|
| `import json` | `json` | `json.loads(...)` |
| `from collections import Counter` | `Counter` only | `Counter(...)`; the name `collections` does not exist |
| `import netlib.devices as dev` | the alias `dev` | `dev.MAX_VLAN` |
| `from x import *` | every public name | avoid it: it pollutes the namespace and hides where names came from |

- A module's top-level code runs **once**, on the first import; later imports reuse the cached copy.
- `__name__` is `"__main__"` when you run the file directly, and the module's own name when it is imported.
- `if __name__ == "__main__": main()` lets one file act as both a script and an importable library. Code outside that guard runs on every import.
- The **standard library** ships with Python (`json`, `os`, `sys`, `re`, `unittest`, `xml.etree.ElementTree`, `csv`, `logging`). **Third-party** packages come from PyPI via `pip` (`requests`, `ncclient`, `xmltodict`, `pyyaml`, `netmiko`, `pyats`).
- The install name can differ from the import name: `pip install pyyaml`, then `import yaml`.

### 7. Dependencies and Python basics that show up in snippets
- `python3 -m venv venv` creates an isolated environment, `source venv/bin/activate` uses it, and `deactivate` leaves it.
- `pip freeze > requirements.txt` pins exact versions, and `pip install -r requirements.txt` rebuilds the same set on another machine, in CI or in a Docker image.
- Separate venvs stop project A's library version clashing with project B's, and keep the system Python clean.
- `list` is ordered and mutable; `tuple` is ordered and **immutable**; `dict` is key/value; `set` holds unique items with no order. Strings are immutable too.
- `{}` is an empty **dict**; an empty set is `set()`. `(5)` is just an int; `(5,)` is a one-item tuple.
- `b = a` copies the reference, not the data, so changing a shared dict changes it everywhere. `dict(tags)` makes a real copy.
- `try / except / else / finally`: `except` runs only on that error, `else` runs only when there was **no** error, and `finally` **always** runs, even after `continue`.
- `enumerate()` counts from 0; `for k, v in d.items()` gives key/value pairs; `break` leaves a loop and `continue` skips to the next pass.
- Use `is` only for `None` checks; `==` compares values.

## Exam traps (the ones that catch people)
- Looks like the function gives back its result, but with no `return` it actually returns **`None`**, so `x = print("hi")` leaves `x` as `None`.
- Looks like `def add(v, l=[])` gets a fresh list each call, but the default is created once and **shared**. Fix it with `l=None`, then `if l is None: l = []`.
- Looks like `from math import sqrt` gives you `math` too, but it binds only `sqrt`, so `math.pi` raises `NameError`.
- Looks like a method without `self` is fine, but `obj.show()` passes the object anyway, giving `TypeError: ... takes 0 positional arguments but 1 was given`.
- Looks like the parent's `__init__` runs by itself, but a child with its own `__init__` must call `super().__init__()`, or you get `AttributeError` later.
- Looks like `*args` and `**kwargs` are lists, but they are a **tuple** and a **dict**.
- Looks like importing a file runs its `main()`, but under the `__main__` guard it does **not** run on import.
- Looks like "faster code" is a benefit of functions and modules, but the right answers are reuse, readability, maintainability and testability.

## Quick self-check
<details><summary>Q1. What does a function with no return statement give back?</summary>`None`, because Python adds an implicit return of None.</details>
<details><summary>Q2. In `def f(*args, **kwargs)`, what types are args and kwargs?</summary>A tuple and a dict; extra positionals go in the tuple, extra keywords in the dict.</details>
<details><summary>Q3. Which method kind receives the class as `cls` and is often an alternative constructor?</summary>`@classmethod`; a staticmethod receives nothing automatically.</details>
<details><summary>Q4. A file ends with `if __name__ == "__main__": run_all()`. Does `run_all()` run when another script imports it?</summary>No; on import `__name__` is the module name, so the guarded block is skipped.</details>
<details><summary>Q5. What is the correct order to copy a dependency set to a new machine?</summary>`pip freeze > requirements.txt` on the old machine, then `python3 -m venv venv`, `source venv/bin/activate`, `pip install -r requirements.txt` on the new one.</details>

## Cheat lines to say out loud
- "Function organises logic, class organises data plus logic, module organises files, package is a folder of modules."
- "No return means None, and a mutable default is shared forever."
- "Child has its own init? Then call super, or the parent never runs."
- "Self is the object, cls is the class, static gets nothing."
- "The main guard makes one file both a script and a library."
