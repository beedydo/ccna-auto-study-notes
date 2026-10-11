# Teach-back 1 · 2026-10-11

30 min together: Beedy teaches 12 min, Bob teaches 12 min, 6 min swapping one question per topic.

## Beedy teaches

_~3 min per topic. Say the 3 points, show the trap, then ask the question at the end._

### T02 · Functions, classes, modules

- Key point 1: **Why organise code** (blueprint 1.5): reuse, readability, maintainability, testability. Never "it runs faster".
- Key point 2: **function** = logic · **class** = data + behaviour (`__init__` sets attributes, methods take `self`) · **module** = a `.py` file, **package** = a folder of modules.
- Key point 3: `if __name__ == "__main__":` runs only when the file is executed, not when imported, so one file is both script and library.
- Exam trap: a child class with its own `__init__` must call `super().__init__()`, or the parent's attributes never get set (`AttributeError` later). Show the `super()` GIF.
- Question for partner: A function has no `return` line. What does `x = f()` give? → **`None`**.

### T04 · Git + version control

- Key point 1: **Four areas:** working dir → `add` → staging → `commit` → local repo → `push` → remote. Git is distributed: every clone has full history.
- Key point 2: **`fetch` vs `pull`:** fetch only updates `origin/main` (your files don't change). `pull` = fetch + merge. Play the workflow GIF.
- Key point 3: **Conflict markers:** `<<<<<<< HEAD` = your branch, `>>>>>>> feature` = incoming. Edit, `git add`, `git commit`.
- Exam trap: undo a commit **already pushed** → `git revert` (new undo commit), not `reset` (rewrites history). And `git rm --cached` keeps the file on disk.
- Question for partner: You ran `git add app.py`. Which command shows what the next commit will contain? → **`git diff --staged`** (plain `git diff` is now empty).

### T05 · Unified diffs

- Key point 1: `--- a/file` = **old**, `+++ b/file` = **new**. `/dev/null` on the `---` side = file created; on the `+++` side = deleted.
- Key point 2: Hunk `@@ -4,15 +4,17 @@`: old has 15 lines from line 4, new has 17 from line 4 → **net +2**. A missing count means 1.
- Key point 3: Prefix is the first character only: space = context, `-` = removed, `+` = added. A changed line is a `-` then a `+`.
- Exam trap: the counts **include context lines**, so `-6,2 +6,4` is +2 lines, not 4 added.
- Question for partner: `@@ -5,7 +5,6 @@` with 5 context lines. How many `-` and `+` lines? → **2 removed, 1 added** (7 = 5 + 2, 6 = 5 + 1).

### T06 · Data formats + parsing

- Key point 1: **XML** = tags, one root, namespaces (NETCONF/SOAP) · **JSON** = `{}` `[]`, double quotes, no comments (REST) · **YAML** = indentation, spaces only, `#` comments (Ansible). YAML 1.2 ⊃ JSON.
- Key point 2: **Parse:** `json.loads(text)` / `json.load(file)` · `yaml.safe_load` · `xmltodict.parse` (attributes → `@`, text → `#text`) or `ET.fromstring`.
- Key point 3: **Navigate:** `{` = use a key, `[` = use an index: `data["ietf-interfaces:interfaces"]["interface"][0]["name"]`.
- Exam trap: xmltodict gives a **dict for one element but a list for two**, and ElementTree's `find("interface")` returns `None` when the XML has a namespace.
- Question for partner: Is `{'vlan': 10}` valid JSON? → **No**: JSON needs double quotes. Also invalid: trailing commas, comments, `True`.

## Bob teaches

### T01 · Software dev methods: agile, lean, waterfall

- Key point 1:
- Key point 2:
- Key point 3:
- Exam trap:
- Question for partner:

### T03 · Design patterns: MVC + Observer

- Key point 1:
- Key point 2:
- Key point 3:
- Exam trap:
- Question for partner:

### T12 · Automation foundations: controller vs device

- Key point 1:
- Key point 2:
- Key point 3:
- Exam trap:
- Question for partner:

### T13 · DevNet resources

- Key point 1:
- Key point 2:
- Key point 3:
- Exam trap:
- Question for partner:

### T35 · Layer 2: MAC, VLANs

- Key point 1:
- Key point 2:
- Key point 3:
- Exam trap:
- Question for partner:

### T36 · Layer 3: IP, masks, routes, gateways

- Key point 1:
- Key point 2:
- Key point 3:
- Exam trap:
- Question for partner:

### T39 · Management, control, data planes

- Key point 1:
- Key point 2:
- Key point 3:
- Exam trap:
- Question for partner:

## Weak IDs logged

- 
