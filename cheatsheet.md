# Exam-eve cheat sheet (200-901 v1.1)

> Rebuilt by `/cheatsheet` from the "Exam traps" sections. Each person edits only their own sections. Read it on Sat 31 Oct.

## HTTP status codes
## REST methods, safe vs idempotent
## Auth per platform (header + login endpoint)
## Ports
## NETCONF operations and datastores
## RESTCONF URL, headers, codes
## YANG node types
## Git command pairs
## Dockerfile instructions
## OWASP threats and fixes
## IaC tool differentiators (Ansible / Terraform / NSO)
## Management / control / data planes
## Platform renames (old → new)
## Async task and webhook flows

## Beedy · question wording → answer

### T05 Unified diffs

| The question says… | Answer |
|---|---|
| "Which side is the original file?" | `---` / `a/` / lines starting with `-` |
| "What does `@@ -22,6 +22,9 @@` mean?" | 6-line region from old line 22 → 9-line region from new line 22, **net +3** |
| "How many lines were added?" | count the `+` lines (not the newCount) |
| "`--- /dev/null`" | file **created** |
| "`+++ /dev/null`" | file **deleted** |
| "What changed?" with a `-`/`+` pair | "X changed from A to B" |
| "Text after the second `@@`" | enclosing section/function label, not a change |
| "Default number of context lines" | **3** |
| "Show staged changes" | `git diff --staged` |
| "Show what a commit changed" | `git show <sha>` |
| "Unified diff outside Git" | `diff -u old new` |
| "Output with `<` and `>`" | normal `diff` format, not unified |
| "Recognise a large deleted block" | many consecutive lines starting with `-` |
| "Why does hunk 2 start at a different new line?" | earlier hunks added/removed lines |
| "`@@@`" | combined diff of a merge commit |
| "`switch.cfg \| 6 ++++--`" | 4 insertions, 2 deletions |

### T06 Data formats + parsing

| The question says… | Answer |
|---|---|
| "Which is valid JSON?" | the one with only `"`, lowercase `true`/`false`/`null`, no trailing comma, no comment |
| "Which is valid YAML?" | spaces aligned, `key: value` with the space, no tabs, `- ` for list items |
| "Which XML is well-formed?" | one root, tags closed in reverse order, same case, quoted attributes, `&amp;`/`&lt;` |
| "Most human-readable / supports comments" | YAML |
| "Required by NETCONF" | XML |
| "Native to JavaScript / most REST APIs" | JSON |
| "Parse a JSON string" | `json.loads(text)` |
| "Parse JSON from a file" | `json.load(f)` |
| "Convert a dict to a JSON string" | `json.dumps(obj)` (`indent=2` to pretty-print) |
| "Securely load YAML" | `yaml.safe_load(text)` |
| "Convert XML into a Python dict" | `xmltodict.parse(text)` |
| "Get an attribute after xmltodict" | `d["tag"]["@attr"]` |
| "Get text of an element that has attributes (xmltodict)" | `d["tag"]["#text"]` |
| "ElementTree: first match / all matches / any depth" | `find` / `findall` / `iter` or `.//` |
| "ElementTree: get an attribute" | `elem.get("id")` or `elem.attrib["id"]` |
| "`find()` returns None on a NETCONF reply" | missing namespace map |
| "Safely parse untrusted XML" | `defusedxml` |
| "Value printed is `'true'` not `True`" | it came from XML (xmltodict / ElementTree) |
| "Code works with 2 interfaces, breaks with 1" | xmltodict single item → dict; use `force_list` |
| "Extract the 2nd device's IP" | `data["response"][1]["ip"]` (count from 0) |
