---
id: T06
title: "Data formats + parsing"
owner: Beedy
blueprint: "1.1, 1.2"
primary_domain: D1
cbt_coverage: "Full"
status: drafted   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-06
teach_back: 2026-10-08
cross_study: 2026-10-21
---

# T06 · Data formats + parsing

> Owner: **Beedy** · Blueprint: **1.1, 1.2** · CBT coverage: **Full** · Learn by 2026-10-06 · Teach-back 2026-10-08

## TL;DR (teach-back card)

- **Formats:** XML uses tags, one root, attributes and namespaces, and is used by NETCONF/SOAP. JSON uses `{}` and `[]`, double quotes only, has no comments, and is used by REST/RESTCONF. YAML uses indentation (spaces only), supports `#` comments, and is used by Ansible/CI. YAML 1.2 is a superset of JSON.
- **Parse to Python:** `json.loads`/`json.load` (string/file) · `yaml.safe_load` (never plain `yaml.load` on untrusted input) · `xmltodict.parse` (attributes → `@`, text → `#text`) or `ET.fromstring` + `find`/`findall`. Types map object→dict, array→list, true→True, null→None.
- **Navigate:** a `{` level takes a key and a `[` level takes an index, e.g. `data["ietf-interfaces:interfaces"]["interface"][0]["name"]`. Use `.get(k, default)` to avoid `KeyError`.
- **Trap:** with xmltodict, a single element becomes a **dict** but repeated elements become a **list**. With ElementTree, `find("interface")` returns `None` when the XML has a namespace, so pass a namespaces map.

## Concepts

### T06.01 · XML

**Must cover:**

- [x] Optional declaration: <?xml version="1.0" encoding="UTF-8"?>
- [x] Exactly one root element wraps everything
- [x] Elements: <name>value</name>; tags are case-sensitive and must close
- [x] Attributes inside the start tag: <interface type="ethernet">
- [x] Empty element: <shutdown/>
- [x] Well-formed = properly nested, closed and quoted; special characters escaped (&lt; &amp;)

**Notes:**

- XML = tagged tree. Every value sits between a start tag and an end tag.

```xml
<?xml version="1.0" encoding="UTF-8"?>        <!-- declaration: optional, must be line 1 if present -->
<interfaces>                                   <!-- exactly ONE root element -->
  <interface type="ethernet">                  <!-- attribute: name="value" inside the start tag -->
    <name>GigabitEthernet1</name>              <!-- element: <tag>text</tag> -->
    <shutdown/>                                <!-- empty element (self-closing) -->
  </interface>
</interfaces>
```

- **Well-formed** rules (parser rejects otherwise):
  - One root; every tag closed (`</x>` or `<x/>`); properly nested (`<a><b></b></a>`, never `<a><b></a></b>`).
  - Tags **case-sensitive**: `<Name>…</name>` is an error.
  - Attribute values quoted (`"` or `'`).
  - Escape special chars in text: `&lt;` `<` · `&gt;` `>` · `&amp;` `&` · `&quot;` · `&apos;`. Raw `1 < 2` → `not well-formed (invalid token)`.
- Element vs attribute: both carry data. Attributes = metadata, can't nest, can't repeat. Elements can nest and repeat.
- Comments allowed: `<!-- ... -->`.

### T06.02 · XML

**Must cover:**

- [x] Namespace declared with xmlns="urn:..." or prefixed xmlns:if="..."
- [x] Avoids name clashes when combining models (e.g. ietf-interfaces vs Cisco native)
- [x] NETCONF payloads and replies always carry namespaces
- [x] XPath selects nodes: /interfaces/interface[name="Gi1"]/description

**Notes:**

- **Namespace** = URI that qualifies a tag name, so `<interface>` from two YANG models doesn't clash.
  - Default: `<interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">` → applies to this element and its children.
  - Prefixed: `xmlns:ianaift="urn:...:iana-if-type"` then `ianaift:ethernetCsmacd`.
  - The URI is just a unique ID; nothing is downloaded.
- Why it matters: one NETCONF payload can mix `ietf-interfaces` and Cisco `Cisco-IOS-XE-native` elements. Namespace tells the device which YANG model each belongs to (T14/T15).
- NETCONF always carries namespaces: `<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">` plus a model namespace in the filter/config.
- RESTCONF JSON equivalent = module prefix in the key: `"ietf-interfaces:interfaces"` (RFC 7951).
- **XPath** = path language to select XML nodes:
  - `/interfaces/interface[name="Gi1"]/description` → the description of interface Gi1.
  - `/` = from root · `//` = anywhere · `[...]` = predicate/filter · `@type` = attribute.
  - Used by NETCONF `<filter type="xpath" select="...">` and by ElementTree (limited subset).

### T06.03 · JSON

**Must cover:**

- [x] Object {"key": value} = unordered key/value pairs; array [1, 2, 3] = ordered list
- [x] Keys and strings must use double quotes
- [x] Value types: string, number, true/false, null, object, array
- [x] No comments, no trailing commas
- [x] Default format for REST APIs and RESTCONF (application/yang-data+json)

**Notes:**

- Home turf → syntax rules only:
  - Object `{"k": v}` = key/value pairs (spec: unordered; Python keeps insertion order). Array `[…]` = ordered.
  - Keys **must** be strings in **double quotes**. Single quotes → `Expecting property name enclosed in double quotes`.
  - Values: string, number, `true`/`false`, `null`, object, array. **Lowercase** literals: `True` → `Expecting value`.
  - **No comments. No trailing comma** (`{"a": 1,}` → `Illegal trailing comma`).
  - No dates/binary type: send as strings.
  - Duplicate keys: legal but undefined; Python keeps the **last**.
- Default for REST APIs. RESTCONF media type: `application/yang-data+json` (XML: `application/yang-data+xml`). Plain REST: `application/json`.

### T06.04 · YAML

**Must cover:**

- [x] Indentation with spaces defines structure (no tabs)
- [x] key: value pairs; list items start with "- "
- [x] --- starts a document; # starts a comment
- [x] Strings usually unquoted; multi-line with | (keep newlines) or > (fold)
- [x] JSON is valid YAML; used by Ansible, Docker Compose, pyATS testbeds, CI pipelines

**Notes:**

- Home turf (Ansible) → traps only:
  - Spaces only; **tab in indentation = error** (`while scanning for the next token`).
  - `key: value` needs the space after `:`. List item `- item`.
  - `---` = document start (multiple docs per file; `yaml.safe_load_all`). `...` = document end. `#` = comment.
  - `|` literal: keeps newlines → `"line1\nline2\n"`. `>` folded: newlines → spaces → `"line1 line2\n"`.
  - YAML 1.2 is a strict **superset of JSON** → `{"a": [1, 2]}` is valid YAML.
  - Ansible playbooks, Docker Compose, pyATS testbeds, GitHub Actions/GitLab CI, Kubernetes.
- **PyYAML implements YAML 1.1** (verified, 6.0.3): `yes`/`no`/`on`/`off` → bool, `010` → 8 (octal), `1.10` → `1.1`, `~` → None, `2026-10-08` → `date`. Quote it to keep a string (`'on'`).

### T06.05 · Comparison

**Must cover:**

- [x] XML: most verbose, attributes + namespaces, used by NETCONF and SOAP
- [x] JSON: compact, native to JavaScript/REST, no comments
- [x] YAML: most human-readable, supports comments, indentation-sensitive
- [x] All three can represent the same nested data

**Notes:**

| | XML | JSON | YAML |
|---|---|---|---|
| Structure via | Tags (open/close) | `{}` `[]` | Indentation |
| Verbosity | Highest | Medium | Lowest |
| Comments | `<!-- -->` | **None** | `#` |
| Attributes / namespaces | Yes / Yes | No / module prefix in key | No / No |
| Data types | Everything is text (schema adds types) | string, number, bool, null | JSON's + dates etc. |
| Whitespace significant | No | No | **Yes** |
| Typical use | NETCONF, SOAP (CUCM AXL), RESTCONF option | REST APIs, RESTCONF, webhooks | Ansible, Compose, CI, pyATS testbeds |
| Python parser | `xmltodict`, `xml.etree.ElementTree`, `minidom` | `json` (stdlib) | `yaml` (PyYAML, third-party) |

- All three can represent the same nested data (Examples shows one interface list in each).
- "Most human-readable / supports comments" → YAML. "Required by NETCONF" → XML. "Smallest, native to JavaScript" → JSON.

### T06.06 · Python mapping

**Must cover:**

- [x] JSON object → Python dict
- [x] JSON array → list
- [x] JSON string → str; number → int/float
- [x] true/false → True/False; null → None
- [x] Going back (dumps) reverses the mapping

**Notes:**

| JSON | Python (`loads`) | Back to JSON (`dumps`) |
|---|---|---|
| object `{}` | `dict` | object |
| array `[]` | `list` | array (**tuple** also → array) |
| string | `str` | string |
| number int / real | `int` / `float` | number |
| `true` / `false` | `True` / `False` | `true` / `false` |
| `null` | `None` | `null` |

- Round trip is not perfect: tuple → array → list; int dict keys `{1: "a"}` → `"1"` string keys.

### T06.07 · Python json

**Must cover:**

- [x] import json
- [x] json.loads(text) → Python object; json.dumps(obj) → JSON string
- [x] json.load(file_obj) and json.dump(obj, file_obj) work with files
- [x] json.dumps(obj, indent=2) pretty-prints; sort_keys=True sorts keys
- [x] response.json() in requests already does json.loads for you

**Notes:**

- `import json` (stdlib).
- **`s` = string:** `json.loads(text)` → object · `json.dumps(obj)` → str.
- **No `s` = file:** `json.load(f)` / `json.dump(obj, f)` with an open file object.
- `json.dumps(obj, indent=2, sort_keys=True)` → pretty, sorted.
- Bad input → `json.JSONDecodeError` (subclass of `ValueError`).
- `requests`: `response.json()` = `json.loads(response.text)`. Send with `requests.post(url, json=payload)` → serialises **and** sets `Content-Type: application/json`. `data=json.dumps(payload)` serialises but you set the header.

### T06.08 · Python YAML

**Must cover:**

- [x] import yaml (PyYAML package)
- [x] yaml.safe_load(text) → dict/list (safe: no arbitrary object creation)
- [x] yaml.load without a safe Loader can execute code: avoid with untrusted input
- [x] yaml.dump(obj) / yaml.safe_dump(obj) → YAML string

**Notes:**

- `pip install pyyaml` → `import yaml` (package name ≠ import name).
- `yaml.safe_load(text)` → dict/list. Only builds standard types.
- `yaml.load(text)` with no Loader → **`TypeError: load() missing 1 required positional argument: 'Loader'`** (PyYAML ≥ 6). `yaml.load(text, Loader=yaml.Loader)` / `UnsafeLoader` can construct arbitrary Python objects → code execution on untrusted input. `safe_load` rejects `!!python/object/apply:os.system` with `could not determine a constructor`.
- `yaml.safe_dump(obj)` / `yaml.dump(obj)` → YAML string. Add `sort_keys=False` to keep order (default sorts).
- Multiple documents: `yaml.safe_load_all(text)` → generator.

### T06.09 · Python XML

**Must cover:**

- [x] xmltodict.parse(xml_string) → nested dict (OrderedDict in older versions)
- [x] Attributes become keys prefixed with @ (e.g. ["@type"])
- [x] Element text with attributes is under "#text"
- [x] Repeated elements become a list
- [x] xmltodict.unparse(dict) → XML string

**Notes:**

- `pip install xmltodict` → `xmltodict.parse(xml_string)` → nested dict. Easiest way to treat XML like JSON.
  - Returns plain `dict` in current versions (1.0.4 verified); older versions returned `OrderedDict`. Access is identical.
- Mapping rules (verified output):
  - Element → key; text → **str** (`"true"`, `"1500"`: no type conversion).
  - Attribute → key with **`@`**: `vlan["@id"]` → `"10"`.
  - Namespace declaration → `@xmlns` key.
  - Element with attributes **and** text → text under **`#text`**: `type["#text"]`.
  - **Repeated** element → `list`; **single** element → `dict`. Code that loops over `["interface"]` breaks when only one interface comes back. Fix: `xmltodict.parse(x, force_list=("interface",))`.
- `xmltodict.unparse(d, pretty=True)` → XML string (dict must have exactly one root key).

### T06.10 · Python XML

**Must cover:**

- [x] import xml.etree.ElementTree as ET
- [x] root = ET.fromstring(text) or ET.parse(file).getroot()
- [x] root.find("tag") first match; root.findall("tag") all matches; iter() walks the tree
- [x] elem.tag, elem.text, elem.attrib (dict of attributes)
- [x] Namespaced tags look like {urn:...}name; pass a namespaces dict to find()
- [x] xml.dom.minidom: older DOM API; toprettyxml() for display

**Notes:**

- Stdlib, no install. `import xml.etree.ElementTree as ET`.
- Load: `root = ET.fromstring(text)` (string → root **Element**) · `root = ET.parse("file.xml").getroot()` (`parse` returns an **ElementTree**, so `.getroot()`).
- Search (direct children by default; path syntax is an XPath subset):
  - `root.find("tag")` → first match or **`None`**.
  - `root.findall("tag")` → list (possibly empty).
  - `root.iter("tag")` → every matching descendant at any depth.
  - `root.findtext("tag")` → text of first match.
- Element properties: `.tag` (name) · `.text` (str or None) · `.attrib` (dict) · `.get("id")` (one attribute).
- **Namespaces:** tag becomes `{urn:…}name`. `root.find("interface")` → **None** (verified). Use one of:
  - `ns = {"if": "urn:ietf:params:xml:ns:yang:ietf-interfaces"}` then `root.findall("if:interface", ns)`.
  - `root.findall("{urn:ietf:params:xml:ns:yang:ietf-interfaces}interface")`.
- `xml.dom.minidom` = older DOM API (`parseString`, `getElementsByTagName`, `.firstChild.nodeValue`). Mostly used for `minidom.parseString(x).toprettyxml()` to pretty-print NETCONF replies.

### T06.11 · Navigating data

**Must cover:**

- [x] Chain keys and indexes: data["response"][0]["hostname"]
- [x] Loop: for dev in data["devices"]: print(dev["name"])
- [x] dict.get("key", default) avoids KeyError
- [x] Check type() when unsure whether a level is a list or dict

**Notes:**

- Read path left to right; each `[]` goes one level deeper. `{` → use a key, `[` → use an index.
  - `data["ietf-interfaces:interfaces"]["interface"][0]["name"]` → `"GigabitEthernet1"`.
- Loop over the list level: `for intf in data["ietf-interfaces:interfaces"]["interface"]: print(intf["name"])`.
- `intf.get("speed", "unknown")` → default instead of `KeyError`.
- Unsure of a level → `type(x)` / `print(json.dumps(x, indent=2))`.
- Common errors: `KeyError` (wrong key, or missing module prefix) · `TypeError: list indices must be integers or slices, not str` (forgot `[0]`) · `IndexError` (empty list).

### T06.12 · Terms

**Must cover:**

- [x] Serialisation (encoding): Python object → text/bytes for storage or sending
- [x] Deserialisation (decoding/parsing): text → Python object
- [x] In APIs: you serialise the request body and deserialise the response body

**Notes:**

- **Serialise** (encode, marshal) = Python object → text/bytes: `json.dumps`, `yaml.safe_dump`, `xmltodict.unparse`.
- **Deserialise** (decode, parse, unmarshal) = text → Python object: `json.loads`, `yaml.safe_load`, `xmltodict.parse`, `ET.fromstring`.
- API call: serialise the request body → send → receive → deserialise the response body.

### T06.13 · Exam angle

**Must cover:**

- [x] Spot the invalid snippet (single quotes in JSON, tab in YAML, unclosed XML tag)
- [x] Pick the Python expression that extracts a given value from parsed data
- [x] Match a format to its typical use (NETCONF = XML, REST = JSON, Ansible = YAML)

**Notes:**

- **Spot the invalid:** JSON single quotes / trailing comma / comment / `True` · YAML tab or missing space after `:` · XML unclosed or mis-nested tag, two roots, unescaped `<`/`&`, case mismatch.
- **Pick the expression:** count `{`/`[` levels; add `[0]` wherever the level is a list.
- **Match format → use:** NETCONF = XML · REST/RESTCONF/webhooks = JSON · Ansible/Compose/CI = YAML · SOAP (CUCM AXL) = XML.
- **Match parser → format:** `json.loads` / `yaml.safe_load` / `xmltodict.parse` or `ET.fromstring`.

## Exam traps

- **JSON quotes:** `{'name': 'Gi1'}` is **invalid** JSON (it's a Python dict literal). JSON needs double quotes, lowercase `true`/`false`/`null`, no trailing comma and no comments.
- **`loads` vs `load`:** `s` = string. `json.load(f)` takes a file object; passing it a string → `AttributeError: 'str' object has no attribute 'read'`.
- **`yaml.load` vs `yaml.safe_load`:** pick `safe_load` for "securely parse YAML from an untrusted source". In PyYAML 6, `yaml.load(text)` with no Loader raises `TypeError`.
- **YAML tabs:** any tab in indentation is a parse error. `key:value` with no space isn't a mapping.
- **PyYAML booleans:** `enabled: yes` → `True`, `mode: on` → `True`, `code: 010` → `8`. Quote them to keep strings.
- **YAML `|` vs `>`:** `|` keeps newlines (literal), `>` folds them into spaces.
- **xmltodict text is always `str`:** `<enabled>true</enabled>` → `'true'`, not `True`.
- **xmltodict `@` / `#text`:** `<vlan id="10">USERS</vlan>` → `{"@id": "10", "#text": "USERS"}`.
- **xmltodict single vs repeated:** one `<interface>` → dict and two → list. Fix with `force_list`.
- **ElementTree namespaces:** `root.tag` = `{urn:...}interfaces`. `find("interface")` → `None`, so use a `{"if": "urn:..."}` map plus the `if:interface` path.
- **`find` vs `findall` vs `iter`:** first match or `None` / list of direct-path matches / all descendants.
- **`ET.parse` returns an ElementTree** (call `.getroot()`), while `ET.fromstring` returns an Element.
- **Format → protocol:** NETCONF = XML only. RESTCONF = XML **or** JSON (`application/yang-data+json` / `+xml`). Ansible = YAML.
- **XML well-formed:** one root, case-sensitive matching tags, quoted attributes, `&lt;`/`&amp;` escapes.

## Examples

### 1. Same data in all three formats, parsed four ways (lab T06.3)

Runs in the lab container, which already has `xmltodict` and `pyyaml`:

```bash
docker build --tag ccna-auto-lab:latest --file labs/Dockerfile labs/
docker run --rm --interactive --tty --volume "$(pwd)":/work ccna-auto-lab:latest python /work/labs/T06/parse_formats.py
```

Or locally: `python3 -m venv .venv && .venv/bin/pip install pyyaml xmltodict && .venv/bin/python parse_formats.py`.

`parse_formats.py`:

```python
"""T06 drill: same interface data in XML, JSON and YAML, parsed into Python."""
import json
import xml.etree.ElementTree as ET

import xmltodict
import yaml

XML_DATA = """<?xml version="1.0" encoding="UTF-8"?>
<interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
  <interface>
    <name>GigabitEthernet1</name>
    <description>Uplink to core</description>
    <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
    <enabled>true</enabled>
  </interface>
  <interface>
    <name>GigabitEthernet2</name>
    <description>Users</description>
    <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
    <enabled>false</enabled>
  </interface>
</interfaces>"""

JSON_DATA = """{
  "ietf-interfaces:interfaces": {
    "interface": [
      {"name": "GigabitEthernet1", "description": "Uplink to core", "enabled": true, "mtu": 1500},
      {"name": "GigabitEthernet2", "description": "Users", "enabled": false, "mtu": null}
    ]
  }
}"""

YAML_DATA = """---
# Same data, YAML
interfaces:
  - name: GigabitEthernet1
    description: Uplink to core
    enabled: true
    mtu: 1500
  - name: GigabitEthernet2
    description: Users
    enabled: false
    mtu: null
banner: |
  Authorised access only
  Disconnect now
"""

print("== JSON")
data = json.loads(JSON_DATA)
intfs = data["ietf-interfaces:interfaces"]["interface"]
print(type(data).__name__, type(intfs).__name__)
print(intfs[0]["name"], intfs[0]["enabled"], intfs[1]["mtu"])
print(intfs[1].get("speed", "unknown"))
print(json.dumps(intfs[1], indent=2, sort_keys=True))

print("== YAML")
ydata = yaml.safe_load(YAML_DATA)
print(ydata["interfaces"][1]["name"], ydata["interfaces"][1]["enabled"], ydata["interfaces"][1]["mtu"])
print(repr(ydata["banner"]))
print(yaml.safe_dump({"vlan": 10, "names": ["USERS", "VOICE"]}, sort_keys=False), end="")

print("== xmltodict")
xdata = xmltodict.parse(XML_DATA)
xi = xdata["interfaces"]["interface"]
print(type(xi).__name__, xi[0]["name"], repr(xi[0]["enabled"]))
print(xdata["interfaces"]["@xmlns"])
print(xi[0]["type"]["#text"], xi[0]["type"]["@xmlns:ianaift"])
one = xmltodict.parse("<vlans><vlan id='10'>USERS</vlan></vlans>")
print(type(one["vlans"]["vlan"]).__name__, one["vlans"]["vlan"]["@id"], one["vlans"]["vlan"]["#text"])
print(xmltodict.unparse({"vlan": {"@id": "20", "name": "VOICE"}}, pretty=True))

print("== ElementTree")
root = ET.fromstring(XML_DATA)
print(root.tag)
ns = {"if": "urn:ietf:params:xml:ns:yang:ietf-interfaces"}
print(root.find("interface"))
for intf in root.findall("if:interface", ns):
    print(intf.find("if:name", ns).text, intf.find("if:enabled", ns).text)
vlan = ET.fromstring("<vlan id='10'><name>USERS</name></vlan>")
print(vlan.tag, vlan.attrib, vlan.find("name").text)
```

Output (Python 3.14, PyYAML 6.0.3, xmltodict 1.0.4):

```
== JSON
dict list
GigabitEthernet1 True None
unknown
{
  "description": "Users",
  "enabled": false,
  "mtu": null,
  "name": "GigabitEthernet2"
}
== YAML
GigabitEthernet2 False None
'Authorised access only\nDisconnect now\n'
vlan: 10
names:
- USERS
- VOICE
== xmltodict
list GigabitEthernet1 'true'
urn:ietf:params:xml:ns:yang:ietf-interfaces
ianaift:ethernetCsmacd urn:ietf:params:xml:ns:yang:iana-if-type
dict 10 USERS
<?xml version="1.0" encoding="utf-8"?>
<vlan id="20">
	<name>VOICE</name>
</vlan>
== ElementTree
{urn:ietf:params:xml:ns:yang:ietf-interfaces}interfaces
None
GigabitEthernet1 true
GigabitEthernet2 false
vlan {'id': '10'} USERS
```

- Things to notice: JSON `true` → `True` but xmltodict `'true'` stays a string. Two `<interface>` → `list` but one `<vlan>` → `dict`. `find("interface")` → `None` without the namespace map.

### 2. Invalid-snippet drill (the error messages you'll see)

```bash
python3 - <<'EOF'
import json
import xml.etree.ElementTree as ET

for text in ["{'name': 'Gi1'}", '{"a": 1,}', '{"a": True}']:
    try:
        json.loads(text)
    except json.JSONDecodeError as err:
        print(repr(text), "->", err)

for text in ["<a><b></a>", "<a>1 < 2</a>"]:
    try:
        ET.fromstring(text)
    except ET.ParseError as err:
        print(repr(text), "->", err)
EOF
```

```
"{'name': 'Gi1'}" -> Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
'{"a": 1,}' -> Illegal trailing comma before end of object: line 1 column 8 (char 7)
'{"a": True}' -> Expecting value: line 1 column 7 (char 6)
'<a><b></a>' -> mismatched tag: line 1, column 8
'<a>1 < 2</a>' -> not well-formed (invalid token): line 1, column 6
```

### 3. Real RESTCONF reply in JSON and XML (DevNet Sandbox)

IOS XE always-on sandbox. Host and credentials change, so check developer.cisco.com/sandbox and put them in `labs/.env` (`IOSXE_HOST`, `IOSXE_USER`, `IOSXE_PASS`). ⚠ verify the sandbox host and port.

```bash
set -a && source labs/.env && set +a

curl --silent --insecure --user "$IOSXE_USER:$IOSXE_PASS" \
  --header "Accept: application/yang-data+json" \
  "https://$IOSXE_HOST/restconf/data/ietf-interfaces:interfaces"

curl --silent --insecure --user "$IOSXE_USER:$IOSXE_PASS" \
  --header "Accept: application/yang-data+xml" \
  "https://$IOSXE_HOST/restconf/data/ietf-interfaces:interfaces"
```

Parse the JSON reply in Python:

```python
import os

import requests

url = f"https://{os.environ['IOSXE_HOST']}/restconf/data/ietf-interfaces:interfaces"
response = requests.get(
    url,
    auth=(os.environ["IOSXE_USER"], os.environ["IOSXE_PASS"]),
    headers={"Accept": "application/yang-data+json"},
    verify=False,
    timeout=10,
)
response.raise_for_status()
for intf in response.json()["ietf-interfaces:interfaces"]["interface"]:
    print(intf["name"], intf.get("description", "-"), intf["enabled"])
```

## Practice questions

**Q1.** Which snippet is valid JSON?
A. `{'vlan': 10}`  B. `{"vlan": 10, "name": "USERS",}`  C. `{"vlan": 10, "active": true, "desc": null}`  D. `{"vlan": 10, # users}`

<details><summary>Answer</summary>

**C.** A uses single quotes, B has a trailing comma, and D has a comment. JSON uses lowercase `true` and `null`. (T06.03)
</details>

**Q2.** Which data format is most human-readable, supports comments, and uses indentation to define structure?
A. XML  B. JSON  C. YAML  D. CSV

<details><summary>Answer</summary>

**C.** YAML. XML has comments but uses tags. JSON has no comments. (T06.05)
</details>

**Q3.** Refer to the code:

```python
import json
text = '{"response": [{"hostname": "leaf1", "ip": "10.1.1.1"}, {"hostname": "leaf2", "ip": "10.1.1.2"}]}'
data = json.loads(text)
```

Which expression returns `"10.1.1.2"`?
A. `data["response"]["ip"][1]`  B. `data["response"][1]["ip"]`  C. `data[1]["response"]["ip"]`  D. `data.response[1].ip`

<details><summary>Answer</summary>

**B.** `response` is a list, so it needs an index before the key. D is attribute syntax, which doesn't work on a dict. (T06.11)
</details>

**Q4.** Complete the code to safely parse a YAML inventory file received from an untrusted user:

```python
import yaml
with open("inventory.yml") as f:
    inventory = yaml.________(f)
```

<details><summary>Answer</summary>

**`safe_load`.** It only builds standard types. Plain `load` with an unsafe Loader can construct arbitrary Python objects. (T06.08)
</details>

**Q5.** Refer to the code:

```python
import xmltodict
xml = '<vlan id="10"><name>USERS</name></vlan>'
d = xmltodict.parse(xml)
```

Which expression returns `"10"`?
A. `d["vlan"]["id"]`  B. `d["vlan"]["@id"]`  C. `d["vlan"]["#text"]`  D. `d["@vlan"]["id"]`

<details><summary>Answer</summary>

**B.** xmltodict prefixes attributes with `@`. `#text` holds element text only when the element also has attributes. (T06.09)
</details>

**Q6.** A script parses a NETCONF reply whose root is `<interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">`. `root.find("interface")` returns `None`, even though interfaces exist. Why?
A. `find` only returns attributes  B. ElementTree stores namespaced tags as `{urn:...}interface`, so the search needs a namespace map  C. NETCONF replies are JSON  D. `find` needs `getroot()` first

<details><summary>Answer</summary>

**B.** Use `root.find("if:interface", {"if": "urn:ietf:params:xml:ns:yang:ietf-interfaces"})`. (T06.10)
</details>

**Q7.** Match each JSON value to the Python type that `json.loads` produces: `{}` · `[]` · `true` · `null` · `"10"` · `10.5`

<details><summary>Answer</summary>

`{}` → `dict` · `[]` → `list` · `true` → `True` (`bool`) · `null` → `None` · `"10"` → `str` · `10.5` → `float`. (T06.06)
</details>

**Q8.** Which XML snippet is well-formed?
A. `<intf><name>Gi1</Name></intf>`  B. `<intf><name>Gi1</intf></name>`  C. `<intf name=Gi1/>`  D. `<intf><name>Gi1</name><shutdown/></intf>`

<details><summary>Answer</summary>

**D.** A has a case mismatch, B is mis-nested, and C has an unquoted attribute value. `<shutdown/>` is a valid empty element. (T06.01)
</details>

## Study aids

| Aid | Type | Title | Est. min | Resource |
|---|---|---|---|---|
| T06.1 | Video | XML syntax, elements/tags/attributes, DOM only | 13 | CBT: XML, JSON, and YAML Data Formats |
| T06.2 | Video | Parse Data Formats into Python Structures | 26 | CBT module |
| T06.3 | Lab | Parse RESTCONF XML with xmltodict + ElementTree | 25 | Docker lab |

- Skip / low priority: Long parsing walkthroughs

## Sources

- Python `json` module (conversion table, `load`/`loads`, `JSONDecodeError`): https://docs.python.org/3/library/json.html
- Python `xml.etree.ElementTree` (`fromstring`, `find`/`findall`/`iter`, namespaces): https://docs.python.org/3/library/xml.etree.elementtree.html
- Python `xml.dom.minidom`: https://docs.python.org/3/library/xml.dom.minidom.html
- RFC 8259, JSON: https://www.rfc-editor.org/rfc/rfc8259
- W3C XML 1.0 (well-formedness, predefined entities): https://www.w3.org/TR/xml/
- W3C Namespaces in XML: https://www.w3.org/TR/xml-names/
- YAML 1.2.2 spec (JSON superset, no tabs, `|` / `>`, `---`): https://yaml.org/spec/1.2.2/
- PyYAML documentation (`safe_load`, `load` Loader): https://pyyaml.org/wiki/PyYAMLDocumentation
- xmltodict (`@` attributes, `#text`, `force_list`, `unparse`): https://github.com/martinblech/xmltodict
- RFC 8040, RESTCONF media types `application/yang-data+json` / `+xml`: https://www.rfc-editor.org/rfc/rfc8040
- RFC 7951, JSON encoding of YANG data (`module:name` member names): https://www.rfc-editor.org/rfc/rfc7951
- Cisco 200-901 v1.1 exam topics (1.1, 1.2): https://learningcontent.cisco.com/documents/marketing/exam-topics/200-901-CCNAAUTO_v.1.1.pdf

## To verify

- ⚠ IOS XE RESTCONF sandbox host, port and credentials (Example 3) change, so check developer.cisco.com/sandbox. Example 3 wasn't run.
- ⚠ PyYAML follows YAML **1.1** for booleans and octals (`yes`/`on` → `True`, `010` → 8). This is verified on PyYAML 6.0.3. Other YAML 1.2 parsers (e.g. ruamel.yaml) behave differently.
- ⚠ The `xmltodict.parse` return type is plain `dict` in 1.0.x and was `OrderedDict` in older releases, so exam answers may still say OrderedDict.
- Examples 1 and 2 were run locally (Python 3.14, PyYAML 6.0.3, xmltodict 1.0.4), and the output shown is real.
- `labs/T06/parse_formats.py` is the Example 1 script, verified with the local venv. It hasn't been run in the Docker lab image yet, because the image isn't built.
