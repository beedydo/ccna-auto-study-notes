# T06 · Syntax cheat sheet: XML, JSON, YAML and the Python that reads them

> Companion to [T06 essentials](T06-data-formats-parsing.md) and the [full note](../bee/T06-data-formats-parsing.md). Every example below was run (Python 3.14, PyYAML 6.0.3, xmltodict 1.0.4); the output shown under each one is real.

**How to use:** cover the `→` output with your hand and predict it. If you can predict every line, you can answer the syntax questions.

- [1. One device, three formats](#1-one-device-three-formats)
- [2. JSON syntax](#2-json-syntax)
- [3. YAML syntax](#3-yaml-syntax)
- [4. XML syntax](#4-xml-syntax)
- [5. Python: json module](#5-python-json-module)
- [6. Python: yaml module](#6-python-yaml-module)
- [7. Python: xmltodict](#7-python-xmltodict)
- [8. Python: ElementTree](#8-python-elementtree)
- [9. Navigating parsed data](#9-navigating-parsed-data)
- [10. Question type → answer](#10-question-type--answer)
- [11. 60-second self-test](#11-60-second-self-test)

---

## 1. One device, three formats

- Same data each time: a switch with a hostname, two VLANs, a boolean and a null.
- Learn this table first. Every rule below is a detail of one of these columns.

<table>
<tr><th>JSON</th><th>YAML</th><th>XML</th></tr>
<tr><td>

```json
{
  "hostname": "sw1",
  "vlans": [10, 20],
  "up": true,
  "mgmt": null
}
```

</td><td>

```yaml
---
hostname: sw1
vlans:
  - 10
  - 20
up: true
mgmt: null
```

</td><td>

```xml
<device>
  <hostname>sw1</hostname>
  <vlan>10</vlan>
  <vlan>20</vlan>
  <up>true</up>
  <mgmt/>
</device>
```

</td></tr>
</table>

| | JSON | YAML | XML |
|---|---|---|---|
| Key / value | `"hostname": "sw1"` | `hostname: sw1` | `<hostname>sw1</hostname>` |
| List | `[10, 20]` | `- 10` on each line, or `[10, 20]` | repeat the tag |
| Nesting | `{ }` inside `{ }` | 2 more **spaces** | tag inside tag |
| Boolean | `true` / `false` | `true` / `false` (also `yes`, `on`…) | text `true` (no real type) |
| Null | `null` | `null`, `~` or empty | empty element `<mgmt/>` |
| Comment | ✗ none | `# …` | `<!-- … -->` |
| Wrapper | outer `{ }` or `[ ]` | none (optional `---`) | exactly **one root** element |

---

## 2. JSON syntax

**Rule in one line:** double quotes, lowercase literals, commas *between* items only, no comments.

### Valid building blocks

```json
{
  "string":  "Gi1/0/1",
  "integer": 1500,
  "float":   1.5,
  "exp":     1e3,
  "negative": -5,
  "bool":    true,
  "nothing": null,
  "list":    [10, "mixed", false, null],
  "object":  {"nested": {"deeper": 1}},
  "empty":   {"list": [], "object": {}},
  "escapes": "say \"hi\"\nnew line, C:\\path"
}
```

- Top level may be **any** value: `[1, 2]`, `"text"` and `null` are all valid JSON documents.
- Escapes inside strings: `\"` quote · `\\` backslash · `\n` newline · `\t` tab · `\u00e9` unicode.

### Invalid: the exam's favourite distractors

| Snippet | Why it's wrong | Python error |
|---|---|---|
| `{'name': 'Gi1'}` | single quotes (this is a Python dict) | `Expecting property name enclosed in double quotes` |
| `{name: "Gi1"}` | key not quoted | `Expecting property name enclosed in double quotes` |
| `{"a": 1,}` | trailing comma | `Illegal trailing comma before end of object` |
| `[1, 2,]` | trailing comma in array | `Illegal trailing comma before end of array` |
| `{"up": True}` | Python literal; JSON is `true` | `Expecting value` |
| `{"mtu": None}` | Python literal; JSON is `null` | `Expecting value` |
| `{"a": 1} // note` | no comments in JSON | `Extra data` |
| `{"port": 08}` | no leading zeros | `Expecting ',' delimiter` |
| `{"a": 1 "b": 2}` | missing comma | `Expecting ',' delimiter` |

- **Spot it fast:** look for `'` · `True`/`False`/`None` · a comma before `}` or `]` · `//` or `#`.

### RESTCONF JSON (Bob's T16): module prefix on the top key

```json
{
  "ietf-interfaces:interfaces": {
    "interface": [
      {"name": "GigabitEthernet1", "enabled": true}
    ]
  }
}
```

- Prefix `module:` appears on the **top** key, and again only where the YANG model changes (RFC 7951).
- Media type: `application/yang-data+json`. Plain REST: `application/json`.

---

## 3. YAML syntax

**Rule in one line:** indentation with spaces is the structure; `key: value` needs the space; `- ` starts a list item.

### Mappings, lists and nesting

```yaml
---                          # optional document start
hostname: sw1                # key: value   (space after the colon)
vlans:                       # key whose value is a list
  - 10                       # "- " starts each list item
  - 20
interfaces:                  # list of mappings (the RESTCONF/Ansible shape)
  - name: Gi1                # first key of the item sits on the dash line
    enabled: true            # following keys line up under "name"
  - name: Gi2
    enabled: false
inline_list: [10, 20]        # flow style = JSON-like, also valid
inline_map: {name: sw1, port: 22}
```

→ `yaml.safe_load` gives:

```python
{'hostname': 'sw1', 'vlans': [10, 20],
 'interfaces': [{'name': 'Gi1', 'enabled': True}, {'name': 'Gi2', 'enabled': False}],
 'inline_list': [10, 20], 'inline_map': {'name': 'sw1', 'port': 22}}
```

- Each `- ` at the same indent = one more list item. Keys under it at the **same** column = same dict.
- A top-level list is just dashes: `- a` / `- b` → `['a', 'b']`.
- An empty file or a comment-only file → `None`.

### Strings and quoting

```yaml
plain:   value # comment          # -> 'value'   (comment stripped)
hash:    '#not comment'           # -> '#not comment'
colon:   "url: http://x"          # -> 'url: http://x'   (quote anything with ": ")
single:  'it''s'                  # -> "it's"    (double the ' to escape it)
double:  "tab\tend"               # -> 'tab\tend' with a real tab (escapes work in "…")
nolit:   'no \t escape'           # -> 'no \\t escape' (no escapes in '…')
empty:   ''                       # -> ''
```

### Multi-line strings

```yaml
literal: |        # keeps newlines         -> 'line1\nline2\n'
  line1
  line2
folded: >         # newlines become spaces -> 'line1 line2\n'
  line1
  line2
strip: |-         # literal, no final \n    -> 'line1\nline2'
  line1
  line2
```

- Memory hook: `|` is a **pipe**, it keeps the lines standing up. `>` **folds** them over into one line.

### Type surprises (PyYAML follows YAML 1.1)

| You write | You get | Fix |
|---|---|---|
| `enabled: yes` · `mode: on` | `True` | `'yes'` |
| `country: NO` | `False` | `'NO'` |
| `perm: 010` | `8` (octal) | `'010'` |
| `ver: 3.10` | `3.1` (float) | `"3.10"` |
| `time: 22:30` | `1350` (base 60) | `"22:30"` |
| `hex: 0x1F` | `31` | `"0x1F"` |
| `date: 2026-10-08` | `datetime.date(2026, 10, 8)` | `'2026-10-08'` |
| `n: 1e3` | `'1e3'` (string! 1.1 needs `1.0e3`) | `1000` |
| `x: ~` or `x:` | `None` | |

### Anchors and merge keys (show up in CI/Compose files)

```yaml
base: &creds {user: admin, port: 22}   # & defines an anchor
sw1:
  <<: *creds                           # * reuses it; << merges keys in
  port: 830                            # local key overrides
```

→ `{'base': {'user': 'admin', 'port': 22}, 'sw1': {'user': 'admin', 'port': 830}}`

### Invalid YAML

| Snippet | Problem | Error |
|---|---|---|
| `vlans:` then a **tab** before `- 10` | tabs never allowed for indent | `ScannerError: while scanning for the next token` |
| `a:` / `␣␣b: 1` / `␣c: 2` | siblings not aligned | `ParserError: while parsing a block mapping` |
| `desc: uplink: core` | second `: ` unquoted | `ScannerError: mapping values are not allowed here` |
| `a:` / `␣␣- 1` / `␣␣b: 2` | list item and key at the same level | `ParserError: while parsing a block collection` |
| `hostname:R1` | **no error**, but it's the string `'hostname:R1'`, not a mapping | |

- **JSON is valid YAML:** `yaml.safe_load('{"a": [1, 2]}')` → `{'a': [1, 2]}`.

---

## 4. XML syntax

**Rule in one line:** one root, every tag closed in reverse order, case-sensitive, quoted attributes, escape `&` and `<`.

### Every piece in one document

```xml
<?xml version="1.0" encoding="UTF-8"?>          <!-- declaration: optional, line 1 only -->
<!-- a comment -->
<interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">  <!-- root + default namespace -->
  <interface>                                   <!-- child element -->
    <name>GigabitEthernet1</name>               <!-- element with text -->
    <description>AT&amp;T &lt;uplink&gt;</description>   <!-- escaped & < > -->
    <mtu unit="bytes">1500</mtu>                <!-- attribute in the start tag -->
    <shutdown/>                                 <!-- empty element, self-closing -->
    <note><![CDATA[1 < 2 & 3]]></note>          <!-- CDATA: raw text, no escaping -->
  </interface>
</interfaces>
```

### The 5 escapes

| Write | Means |
|---|---|
| `&lt;` | `<` |
| `&gt;` | `>` |
| `&amp;` | `&` |
| `&quot;` | `"` |
| `&apos;` | `'` |

### Well-formed rules with the error you get

| Broken | Rule | `ET.fromstring` error |
|---|---|---|
| `<a/><b/>` | one root only | `junk after document element` |
| `<a><b></a></b>` | close in reverse order | `mismatched tag` |
| `<Name>x</name>` | case-sensitive | `mismatched tag` |
| `<vlan id=10/>` | quote attribute values | `not well-formed (invalid token)` |
| `<d>AT&T</d>` | escape `&` | `not well-formed (invalid token)` |
| `<a>1 < 2</a>` | escape `<` | `not well-formed (invalid token)` |
| `<a><b></a>` | close every tag | `mismatched tag` |

### Namespaces (Bob's T15 NETCONF)

```xml
<config>
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">      <!-- default ns -->
    <interface>
      <name>Loopback100</name>
      <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:softwareLoopback</type>
    </interface>                                                         <!-- prefixed ns -->
  </interfaces>
</config>
```

- `xmlns="…"` = default namespace for this element and its children.
- `xmlns:ianaift="…"` declares a prefix; `ianaift:softwareLoopback` uses it.
- The URI is an ID only; nothing is downloaded.

### XPath in 5 lines

| XPath | Selects |
|---|---|
| `/interfaces/interface` | every `interface` directly under the root |
| `/interfaces/interface[name="Gi1"]/description` | Gi1's description (`[…]` = filter) |
| `//name` | every `name` anywhere |
| `//mtu/@unit` | the `unit` attribute |
| `/interfaces/interface[1]` | the **first** one (XPath counts from **1**) |

---

## 5. Python: json module

**The `s` means string.** `loads`/`dumps` work on strings; `load`/`dump` work on open files.

```python
import json

text = '{"hostname": "sw1", "vlans": [10, 20], "up": true, "mgmt": null}'
data = json.loads(text)
print(data)
# {'hostname': 'sw1', 'vlans': [10, 20], 'up': True, 'mgmt': None}

print(json.dumps(data))
# {"hostname": "sw1", "vlans": [10, 20], "up": true, "mgmt": null}

print(json.dumps(data, indent=2, sort_keys=True))
# {
#   "hostname": "sw1",
#   "mgmt": null,
#   "up": true,
#   "vlans": [
#     10,
#     20
#   ]
# }

with open("device.json") as f:          # file object in
    data = json.load(f)
with open("out.json", "w") as f:        # file object out
    json.dump(data, f, indent=2)
```

| Call | Takes | Returns |
|---|---|---|
| `json.loads(s)` | str (or bytes) | Python object |
| `json.load(f)` | open file | Python object |
| `json.dumps(obj)` | Python object | str |
| `json.dump(obj, f)` | Python object + open file | `None` (writes the file) |
| `resp.json()` | (requests response) | same as `json.loads(resp.text)` |

### Gotchas, with real output

```python
json.dumps({"name": "Gi1", "up": True, "mtu": None})   # '{"name": "Gi1", "up": true, "mtu": null}'
json.dumps({"vlans": (10, 20), 1: "a"})                # '{"vlans": [10, 20], "1": "a"}'   tuple→list, int key→str
json.dumps({"desc": "café"})                           # '{"desc": "caf\\u00e9"}'
json.dumps({"desc": "café"}, ensure_ascii=False)       # '{"desc": "café"}'
json.loads('[1, "two", 3.0, false]')                   # [1, 'two', 3.0, False]

json.load('{"a": 1}')      # AttributeError: 'str' object has no attribute 'read'
json.loads({"a": 1})       # TypeError: the JSON object must be str, bytes or bytearray, not dict
json.dumps({"v": {10, 20}})  # TypeError: Object of type set is not JSON serializable
```

### Sending JSON with requests (link to T11)

```python
requests.post(url, json=payload)                         # serialises + sets Content-Type: application/json
requests.post(url, data=json.dumps(payload),
              headers={"Content-Type": "application/json"})   # same result, done by hand
requests.post(url, data=payload)                         # form-encoded! Content-Type: application/x-www-form-urlencoded
```

---

## 6. Python: yaml module

```python
import yaml                 # pip install pyyaml  (install name ≠ import name)

text = """
hostname: sw1
vlans: [10, 20]
up: true
"""
cfg = yaml.safe_load(text)
print(cfg)                  # {'hostname': 'sw1', 'vlans': [10, 20], 'up': True}

with open("testbed.yaml") as f:
    cfg = yaml.safe_load(f)                   # accepts a file object too

docs = list(yaml.safe_load_all("---\na: 1\n---\na: 2\n"))
print(docs)                                   # [{'a': 1}, {'a': 2}]
```

### Writing YAML

```python
d = {"hostname": "sw1", "vlans": [10, 20], "up": True, "mgmt": None}

print(yaml.safe_dump(d))                       # keys SORTED by default
# hostname: sw1
# mgmt: null
# up: true
# vlans:
# - 10
# - 20

print(yaml.safe_dump(d, sort_keys=False))      # keeps your order
# hostname: sw1
# vlans:
# - 10
# - 20
# up: true
# mgmt: null

print(yaml.safe_dump({"vlans": [10, 20]}, default_flow_style=True))
# {vlans: [10, 20]}
```

### Safe vs unsafe

```python
yaml.load("a: 1")
# TypeError: load() missing 1 required positional argument: 'Loader'   (PyYAML 6+)

yaml.safe_load("!!python/object/apply:os.system ['id']")
# ConstructorError: could not determine a constructor for the tag
#   'tag:yaml.org,2002:python/object/apply:os.system'
```

- `yaml.load(text, Loader=yaml.Loader)` / `UnsafeLoader` **would** build that object, which means running `os.system`. Exam answer for untrusted input: **`yaml.safe_load`**.

---

## 7. Python: xmltodict

**XML → nested dict, so you can use `["key"]` like JSON.** Four mapping rules: `@` attributes · `#text` text · repeated tag → list · everything is a string.

```python
import xmltodict            # pip install xmltodict

x = """<device type="switch">
  <hostname>sw1</hostname>
  <vlan id="10">USERS</vlan>
  <vlan id="20">VOICE</vlan>
  <up>true</up>
  <mgmt/>
</device>"""

d = xmltodict.parse(x)
```

→ `d` is:

```python
{'device': {
    '@type': 'switch',                              # attribute  -> '@' + name
    'hostname': 'sw1',                              # element    -> key
    'vlan': [                                       # repeated   -> list
        {'@id': '10', '#text': 'USERS'},            # attr + text -> text under '#text'
        {'@id': '20', '#text': 'VOICE'}],
    'up': 'true',                                   # always a STRING, not True
    'mgmt': None}}                                  # empty element -> None
```

```python
d["device"]["@type"]               # 'switch'
d["device"]["hostname"]            # 'sw1'
d["device"]["vlan"][1]["#text"]    # 'VOICE'
d["device"]["vlan"][0]["@id"]      # '10'   (a string)
d["device"]["up"] == "true"        # True   (compare to the string)
```

### The one-vs-many trap

```python
xmltodict.parse('<device><vlan id="10">USERS</vlan></device>')
# {'device': {'vlan': {'@id': '10', '#text': 'USERS'}}}        <- ONE vlan = dict, not list

xmltodict.parse('<device><vlan id="10">USERS</vlan></device>', force_list=("vlan",))
# {'device': {'vlan': [{'@id': '10', '#text': 'USERS'}]}}      <- always a list
```

### Namespaces with xmltodict

```python
xmltodict.parse('<interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">'
                '<interface><name>Gi1</name></interface></interfaces>')
# {'interfaces': {'@xmlns': 'urn:ietf:params:xml:ns:yang:ietf-interfaces',
#                 'interface': {'name': 'Gi1'}}}
```

- Namespace becomes an `@xmlns` key; the tag names stay plain. So the key is `'interfaces'`, **not** `'ietf-interfaces:interfaces'` (that's RESTCONF JSON).

### dict → XML

```python
print(xmltodict.unparse({"vlan": {"@id": "30", "name": "CAMERAS"}}, pretty=True))
# <?xml version="1.0" encoding="utf-8"?>
# <vlan id="30">
# 	<name>CAMERAS</name>
# </vlan>

xmltodict.unparse({"vlan": {"@id": "30", "#text": "CAMERAS"}})
# '<?xml version="1.0" encoding="utf-8"?>\n<vlan id="30">CAMERAS</vlan>'

xmltodict.unparse({"a": 1, "b": 2})
# ValueError: Document must have exactly one root.
```

---

## 8. Python: ElementTree

**Stdlib. XML → tree of Element objects.** Each Element has `.tag`, `.text`, `.attrib`, `.get()`, and children.

```python
import xml.etree.ElementTree as ET

root = ET.fromstring(x)                # x = the <device> XML from section 7
# or from a file:  root = ET.parse("device.xml").getroot()

root.tag                    # 'device'
root.attrib                 # {'type': 'switch'}
root.get("type")            # 'switch'
len(root)                   # 5   (direct children)
[e.tag for e in root]       # ['hostname', 'vlan', 'vlan', 'up', 'mgmt']
```

### find / findall / findtext / iter

```python
root.find("hostname").text                       # 'sw1'        first match, or None
root.findtext("hostname")                        # 'sw1'        text of first match
[v.get("id") for v in root.findall("vlan")]      # ['10', '20'] all matches (a list)
[v.text for v in root.findall("vlan")]           # ['USERS', 'VOICE']
root.find("vlan[@id='20']").text                 # 'VOICE'      filter on attribute
root.find("up").text                             # 'true'       string again
repr(root.find("mgmt").text)                     # 'None'       empty element

root.find("missing")                             # None
root.findall("missing")                          # []
root.findtext("missing", default="n/a")          # 'n/a'
root.find("missing").text                        # AttributeError: 'NoneType' object has no attribute 'text'
```

| Method | Searches | Returns when nothing found |
|---|---|---|
| `find("x")` | direct children (or the path you give) | `None` |
| `findall("x")` | direct children (or path) | `[]` |
| `findtext("x")` | same as `find` | `None` (or `default=`) |
| `findall(".//x")` | **any depth** | `[]` |
| `iter("x")` | **any depth**, includes root | empty iterator |

```python
n = ET.fromstring("<a><b><name>x</name></b><name>y</name></a>")
[e.text for e in n.findall("name")]       # ['y']        direct children only
[e.text for e in n.findall(".//name")]    # ['x', 'y']   any depth
[e.text for e in n.iter("name")]          # ['x', 'y']   any depth

i = ET.fromstring("<ifs><if><name>Gi1</name><d>up</d></if><if><name>Gi2</name><d>down</d></if></ifs>")
i.find("if[name='Gi2']/d").text           # 'down'   filter on a child's text
i.find("if[2]/name").text                 # 'Gi2'    position counts from 1
```

### Namespaces (the NETCONF trap)

```python
nx = ET.fromstring('<interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">'
                   '<interface><name>Gi1</name><enabled>true</enabled></interface></interfaces>')

nx.tag                       # '{urn:ietf:params:xml:ns:yang:ietf-interfaces}interfaces'
nx.find("interface")         # None   <- the trap: no error, just None

NS = {"if": "urn:ietf:params:xml:ns:yang:ietf-interfaces"}
nx.find("if:interface/if:name", NS).text                  # 'Gi1'   prefix map
nx.findtext("if:interface/if:enabled", namespaces=NS)     # 'true'
nx.find("{urn:ietf:params:xml:ns:yang:ietf-interfaces}interface")[0].text   # 'Gi1'   full {uri}tag
[e.text for e in nx.iter("{urn:ietf:params:xml:ns:yang:ietf-interfaces}name")]  # ['Gi1']
```

- The prefix in your map (`"if"`) is **your** choice; only the URI has to match.
- `iter()` does not take a namespace map, so use the full `{uri}tag` form.

### Building XML (e.g. a NETCONF payload)

```python
cfg = ET.Element("interfaces", xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces")
intf = ET.SubElement(cfg, "interface")
ET.SubElement(intf, "name").text = "Loopback100"
ET.SubElement(intf, "description").text = "built by ET"
ET.indent(cfg)
print(ET.tostring(cfg, encoding="unicode"))
# <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
#   <interface>
#     <name>Loopback100</name>
#     <description>built by ET</description>
#   </interface>
# </interfaces>
```

- `ET.tostring(root)` without `encoding="unicode"` returns **bytes**.
- Pretty-print someone else's XML: `minidom.parseString(xml_text).toprettyxml(indent="  ")` (`from xml.dom import minidom`).

### Untrusted XML

```python
from defusedxml.ElementTree import fromstring     # pip install defusedxml
root = fromstring(untrusted_text)                  # raises EntitiesForbidden on XXE / entity bombs
```

---

## 9. Navigating parsed data

**Rule:** read the path left to right. At a `{` use a **key**. At a `[` use an **index** (from 0) or loop.

```python
r = {"response": [
        {"hostname": "sw1", "ip": "10.0.0.1", "tags": ["core", "lab"]},
        {"hostname": "sw2", "ip": "10.0.0.2", "tags": []}]}
```

| Expression | Result |
|---|---|
| `r["response"][1]["ip"]` | `'10.0.0.2'` |
| `r["response"][0]["tags"][-1]` | `'lab'` (`-1` = last) |
| `len(r["response"])` | `2` |
| `[d["hostname"] for d in r["response"]]` | `['sw1', 'sw2']` |
| `[d["ip"] for d in r["response"] if "core" in d["tags"]]` | `['10.0.0.1']` |
| `{d["hostname"]: d["ip"] for d in r["response"]}` | `{'sw1': '10.0.0.1', 'sw2': '10.0.0.2'}` |
| `r["response"][0].get("serial", "n/a")` | `'n/a'` |
| `r["response"][0].get("serial")` | `None` |
| `"ip" in r["response"][0]` | `True` |
| `list(r["response"][0].keys())` | `['hostname', 'ip', 'tags']` |

### The four errors and what they mean

| Expression | Error | Meaning |
|---|---|---|
| `r["response"]["hostname"]` | `TypeError: list indices must be integers or slices, not str` | forgot the `[0]` |
| `r["Response"]` | `KeyError: 'Response'` | wrong key (case, or missing `module:` prefix) |
| `r["response"][2]` | `IndexError: list index out of range` | only 2 items: indexes 0 and 1 |
| `r["response"][1]["tags"][0]` | `IndexError: list index out of range` | that list is empty |

### Worked example: a real-shaped RESTCONF reply

```python
data = {"ietf-interfaces:interfaces": {"interface": [
          {"name": "GigabitEthernet1", "enabled": True},
          {"name": "GigabitEthernet2", "enabled": False}]}}

#  {  → key       [  → index      {  → key
data["ietf-interfaces:interfaces"]["interface"][1]["name"]     # 'GigabitEthernet2'

for intf in data["ietf-interfaces:interfaces"]["interface"]:
    if not intf["enabled"]:
        print(intf["name"])                                    # GigabitEthernet2
```

---

## 10. Question type → answer

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

---

## 11. 60-second self-test

Predict, then open.

<details><summary>1. <code>json.loads('{"a": [1, 2], "b": null}')["b"]</code></summary>

`None`
</details>

<details><summary>2. <code>yaml.safe_load("x: 010\ny: '010'")</code></summary>

`{'x': 8, 'y': '010'}`: unquoted `010` is octal in YAML 1.1.
</details>

<details><summary>3. <code>xmltodict.parse('&lt;a id="5"&gt;hi&lt;/a&gt;')</code></summary>

`{'a': {'@id': '5', '#text': 'hi'}}`
</details>

<details><summary>4. <code>ET.fromstring('&lt;a&gt;&lt;b&gt;1&lt;/b&gt;&lt;b&gt;2&lt;/b&gt;&lt;/a&gt;').find("b").text</code></summary>

`'1'`: `find` returns the **first** match, and the text is a string.
</details>

<details><summary>5. Valid JSON? <code>{"vlan": 10, "name": "USERS",}</code></summary>

No: trailing comma → `Illegal trailing comma before end of object`.
</details>

<details><summary>6. <code>json.dumps({"up": True, "ids": (1, 2)})</code></summary>

`'{"up": true, "ids": [1, 2]}'`
</details>

<details><summary>7. What does this YAML give? <code>msg: |</code> then <code>  a</code> / <code>  b</code></summary>

`{'msg': 'a\nb\n'}`: `|` keeps the newlines.
</details>

<details><summary>8. <code>data = {"items": [{"id": 7}]}</code>: what does <code>data["items"]["id"]</code> raise?</summary>

`TypeError: list indices must be integers or slices, not str`. You need `data["items"][0]["id"]`.
</details>

<details><summary>9. Well-formed? <code>&lt;intf&gt;&lt;name&gt;Gi1&lt;/Name&gt;&lt;/intf&gt;</code></summary>

No: `<name>` vs `</Name>` is a case mismatch → `mismatched tag`.
</details>

<details><summary>10. NETCONF reply has <code>xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces"</code>. Why does <code>root.find("interface")</code> return None, and what's the fix?</summary>

The real tag is `{urn:…ietf-interfaces}interface`. Fix: `root.find("if:interface", {"if": "urn:ietf:params:xml:ns:yang:ietf-interfaces"})`.
</details>
