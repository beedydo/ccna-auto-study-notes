# T06 · Data formats + parsing: essentials

> Blueprint 1.1, 1.2 · Full note: [bee/T06-data-formats-parsing.md](../bee/T06-data-formats-parsing.md) · Teach-back 2026-10-11

## In one picture
There is no image for T06 yet, so here is the same interface written three ways, and where each one ends up in Python:

```
XML (NETCONF, SOAP)                 JSON (REST, RESTCONF)              YAML (Ansible, CI)
-------------------                 ---------------------              ------------------
<interfaces xmlns="urn:...">        {"ietf-interfaces:interfaces": {   interfaces:
  <interface>                         "interface": [                     - name: Gi1
    <name>Gi1</name>                    {"name": "Gi1",                    enabled: true
    <enabled>true</enabled>              "enabled": true}
  </interface>                        ]
</interfaces>                       }}
        |                                    |                                 |
xmltodict.parse  or  ET.fromstring      json.loads                      yaml.safe_load
        |                                    |                                 |
        +------------------> Python dict / list you navigate <-----------------+
```
*Read across: the data is identical, only the wrapping changes; read down: each format has its own parser, and they all end in Python dicts and lists (ElementTree gives you Element objects instead).*

## The big idea
XML, JSON and YAML are three ways to write the same nested data, like the same shopping list written as a formal form (XML), a compact note (JSON) or an indented bullet list (YAML). Network APIs send you one of these, and your script turns it into Python dicts and lists so it can pull values out. On the exam you will be asked to spot an invalid snippet, match a format to its protocol, pick the right parser, and write the expression that extracts a value. JSON and YAML are home turf, so those sections are traps only; XML gets a gentler walk-through because NETCONF depends on it.

## What you need to know

### 1. XML basics: tags, one root, and "well-formed"
- XML is a **tree of tags**. Every value sits between a start tag and an end tag, like `<name>GigabitEthernet1</name>`. Each tagged item is called an **element**.

```xml
<?xml version="1.0" encoding="UTF-8"?>        <!-- declaration: optional, must be line 1 if present -->
<interfaces>                                   <!-- exactly ONE root element wraps everything -->
  <interface type="ethernet">                  <!-- attribute: name="value" inside the start tag -->
    <name>GigabitEthernet1</name>              <!-- element: <tag>text</tag> -->
    <shutdown/>                                <!-- empty element, closes itself -->
  </interface>
</interfaces>
```

- The first line, `<?xml version="1.0" encoding="UTF-8"?>`, is the **declaration**. It is optional, but if present it must be the first line.
- An **attribute** is a small `name="value"` label inside the start tag. Think of attributes as metadata: they can't nest and can't repeat. Elements can nest and repeat.
- `<shutdown/>` is an **empty (self-closing) element**: a tag with no content.
- Comments look like `<!-- ... -->`.
- A parser only accepts XML that is **well-formed**, which means all of these hold:
  - There is exactly one root element.
  - Every tag is closed, either with `</x>` or as `<x/>`.
  - Tags are properly nested: `<a><b></b></a>` is fine, `<a><b></a></b>` is not.
  - Tags are **case-sensitive**: `<Name>…</name>` is an error.
  - Attribute values are in quotes, single or double.
  - Special characters in text are escaped: `&lt;` for `<`, `&gt;` for `>`, `&amp;` for `&`, plus `&quot;` and `&apos;`. A raw `1 < 2` gives `not well-formed (invalid token)`.

### 2. XML namespaces and XPath (why NETCONF looks so busy)
- A **namespace** is a unique ID (a URI) attached to tag names, so that an `<interface>` from one data model doesn't clash with an `<interface>` from another. It works like a surname: two people called "interface" are told apart by their family.
- A **default namespace** applies to an element and all its children: `<interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">`.
- A **prefixed namespace** gives the URI a short nickname: `xmlns:ianaift="urn:...:iana-if-type"`, then you write `ianaift:ethernetCsmacd`.
- The URI is just a unique label; nothing is downloaded from it.
- One NETCONF payload can mix the standard `ietf-interfaces` model with Cisco's `Cisco-IOS-XE-native` model, and the namespace tells the device which YANG model each part belongs to (T14/T15).
- NETCONF messages **always** carry namespaces, for example `<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">` plus a model namespace in the filter or config.
- In RESTCONF JSON, the namespace becomes a **module prefix in the key** instead: `"ietf-interfaces:interfaces"` (RFC 7951).
- **XPath** is a path language for picking parts of an XML tree, much like a file path:
  - `/interfaces/interface[name="Gi1"]/description` selects the description of interface Gi1.
  - `/` starts from the root, `//` means "anywhere below", `[...]` is a filter (a **predicate**), and `@type` selects an attribute.
  - NETCONF uses it in `<filter type="xpath" select="...">`, and ElementTree supports a limited subset.

### 3. JSON and YAML rules (home turf, traps only)
- **JSON:** an **object** `{"k": v}` holds key/value pairs and an **array** `[...]` is an ordered list.
  - Keys and strings must use **double quotes**. Single quotes give `Expecting property name enclosed in double quotes`.
  - Literals are **lowercase**: `true`, `false`, `null`. Writing `True` gives `Expecting value`.
  - **No comments and no trailing comma.** `{"a": 1,}` gives `Illegal trailing comma`.
  - There is no date or binary type, so those are sent as strings. Duplicate keys are legal but undefined, and Python keeps the **last** one.
  - Media types: plain REST uses `application/json`; RESTCONF uses `application/yang-data+json` or `application/yang-data+xml`.
- **YAML:**
  - Indentation must be **spaces**; a tab in indentation is a parse error. `key: value` needs the space after the colon, and list items start with `- `.
  - `---` starts a document (a file can hold several), `...` ends one, and `#` starts a comment.
  - `|` (**literal**) keeps newlines, giving `"line1\nline2\n"`. `>` (**folded**) turns newlines into spaces, giving `"line1 line2\n"`.
  - YAML 1.2 is a **superset of JSON**, so any valid JSON is valid YAML.
  - Used by Ansible playbooks, Docker Compose, pyATS testbeds, GitHub Actions and GitLab CI, and Kubernetes.
  - **PyYAML follows YAML 1.1** (verified on 6.0.3): `yes`, `no`, `on`, `off` become booleans, `010` becomes 8 (octal), `1.10` becomes `1.1`, `~` becomes None, and `2026-10-08` becomes a date. Quote the value (`'on'`) to keep it a string. ⚠ verify: other YAML 1.2 parsers such as ruamel.yaml behave differently.

### 4. Comparing the three formats
| | XML | JSON | YAML |
|---|---|---|---|
| Structure shown by | opening and closing tags | `{}` and `[]` | indentation |
| Verbosity | highest | medium | lowest |
| Comments | `<!-- -->` | **none** | `#` |
| Attributes / namespaces | yes / yes | no / module prefix in key | no / no |
| Data types | everything is text (a schema adds types) | string, number, bool, null | JSON's types plus dates and more |
| Whitespace matters | no | no | **yes** |
| Typical use | NETCONF, SOAP (CUCM AXL), RESTCONF option | REST APIs, RESTCONF, webhooks | Ansible, Compose, CI, pyATS testbeds |
| Python parser | `xmltodict`, `xml.etree.ElementTree`, `minidom` | `json` (standard library) | `yaml` (PyYAML, third-party) |

- Quick matches: "most human-readable and supports comments" is YAML; "required by NETCONF" is XML; "smallest and native to JavaScript" is JSON.
- NETCONF is XML only, while RESTCONF can use XML **or** JSON.

### 5. Parsing into Python: JSON and YAML
- Turning text into Python objects is **deserialising** (also decoding or parsing). Turning Python objects into text is **serialising** (encoding). In an API call you serialise the request body and deserialise the response body.

| JSON | Python after `loads` | Back to JSON with `dumps` |
|---|---|---|
| object `{}` | `dict` | object |
| array `[]` | `list` | array (a tuple also becomes an array) |
| string | `str` | string |
| number | `int` or `float` | number |
| `true` / `false` | `True` / `False` | `true` / `false` |
| `null` | `None` | `null` |

- The round trip is not perfect: a tuple comes back as a list, and integer dict keys like `{1: "a"}` come back as the string `"1"`.
- **The `s` means string:** `json.loads(text)` and `json.dumps(obj)` work with strings; `json.load(f)` and `json.dump(obj, f)` work with an open file object.
- `json.dumps(obj, indent=2, sort_keys=True)` pretty-prints with sorted keys. Bad input raises `json.JSONDecodeError`, a subclass of `ValueError`.
- With `requests`, `response.json()` is the same as `json.loads(response.text)`. `requests.post(url, json=payload)` serialises **and** sets `Content-Type: application/json`; `data=json.dumps(payload)` serialises but leaves the header to you.
- **YAML:** `pip install pyyaml`, then `import yaml` (the install name differs from the import name).
  - `yaml.safe_load(text)` builds only standard types (dict, list, str and so on), so it is the safe choice.
  - In PyYAML 6 and later, `yaml.load(text)` with no Loader raises `TypeError: load() missing 1 required positional argument: 'Loader'`. With `Loader=yaml.Loader` or `UnsafeLoader` it can build arbitrary Python objects, which means **code execution** on untrusted input. `safe_load` rejects `!!python/object/apply:os.system`.
  - `yaml.safe_dump(obj)` writes YAML and sorts keys by default; add `sort_keys=False` to keep order. `yaml.safe_load_all(text)` reads several documents.

### 6. Parsing XML in Python: xmltodict and ElementTree
- **xmltodict** (`pip install xmltodict`) turns XML into a nested dict, so you can treat it like JSON. It returns a plain `dict` in current versions; older versions returned `OrderedDict`, and access works the same. ⚠ verify: exam answers may still say OrderedDict.
  - Each element becomes a key, and its text is always a **string**: `<enabled>true</enabled>` gives `'true'`, not `True`.
  - An attribute becomes a key starting with **`@`**: `vlan["@id"]` gives `"10"`. A namespace declaration becomes an `@xmlns` key.
  - If an element has attributes **and** text, the text goes under **`#text`**: `<vlan id="10">USERS</vlan>` gives `{"@id": "10", "#text": "USERS"}`.
  - A **repeated** element becomes a **list**, but a **single** element becomes a **dict**. A loop over `["interface"]` breaks when the device returns just one interface. The fix is `xmltodict.parse(x, force_list=("interface",))`.
  - `xmltodict.unparse(d, pretty=True)` goes back to XML; the dict must have exactly one root key.
- **ElementTree** is in the standard library: `import xml.etree.ElementTree as ET`.
  - `ET.fromstring(text)` returns the root **Element**. `ET.parse("file.xml")` returns an **ElementTree**, so you add `.getroot()`.
  - `root.find("tag")` returns the first match or **`None`**; `root.findall("tag")` returns a list (possibly empty); `root.iter("tag")` walks every matching descendant at any depth; `root.findtext("tag")` returns the text of the first match.
  - Each element has `.tag` (its name), `.text` (string or None), `.attrib` (a dict of attributes) and `.get("id")` for one attribute.
  - **Namespaces trap:** with a namespace, the tag is stored as `{urn:…}name`, so `root.find("interface")` returns **None** even though interfaces exist. Pass a map instead:

```python
ns = {"if": "urn:ietf:params:xml:ns:yang:ietf-interfaces"}
root.findall("if:interface", ns)
```

- `xml.dom.minidom` is an older DOM API, mostly used as `minidom.parseString(x).toprettyxml()` to pretty-print NETCONF replies.
- **Exam-sim gap (from practice test review):** untrusted XML is risky to parse.
  - XML allows **external entities** (XXE), where the file asks the parser to read something like `/etc/passwd` or a URL, and **entity expansion bombs** ("billion laughs"), where a tiny file expands to gigabytes.
  - Python's answer is **`defusedxml`**, a drop-in replacement that refuses those features: `from defusedxml.ElementTree import fromstring`. Recent Python docs say modern Expat blocks some of these, but `defusedxml` is still the exam answer. ⚠ verify
  - Exam cue: "safely parse XML from an untrusted source" means **defusedxml**, just as untrusted YAML means `yaml.safe_load`.

### 7. Navigating parsed data
- Read a path left to right, one level per bracket. If the level is a `{`, use a **key**; if it is a `[`, use an **index**.

```python
data["ietf-interfaces:interfaces"]["interface"][0]["name"]    # -> "GigabitEthernet1"
```

- Loop over the list level: `for intf in data["ietf-interfaces:interfaces"]["interface"]: print(intf["name"])`.
- `intf.get("speed", "unknown")` returns a default instead of raising `KeyError`.
- If you are unsure what a level is, check `type(x)` or print it with `json.dumps(x, indent=2)`.
- Common errors: `KeyError` means a wrong key or a missing module prefix; `TypeError: list indices must be integers or slices, not str` means you forgot the `[0]`; `IndexError` means the list was empty.

## Exam traps (the ones that catch people)
- Looks like `{'name': 'Gi1'}` is JSON, but it is a Python dict literal; JSON needs double quotes.
- Looks like `json.load(text)` should parse a string, but without the `s` it expects a file and fails with `'str' object has no attribute 'read'`.
- Looks like `yaml.load` is the normal call, but for untrusted input the answer is `yaml.safe_load`, and in PyYAML 6 plain `load` without a Loader raises `TypeError`.
- Looks like `enabled: yes` stays a string, but PyYAML turns it into `True` (and `010` into 8); quote it to keep it as text.
- Looks like xmltodict gives you booleans and numbers, but every value is a **string**, such as `'true'`.
- Looks like xmltodict always returns a list of interfaces, but one interface comes back as a **dict**; use `force_list`.
- Looks like `root.find("interface")` should work on a NETCONF reply, but namespaced tags need a namespace map, or you get `None`.
- Looks like `ET.parse` returns the root, but it returns an ElementTree; call `.getroot()`, whereas `ET.fromstring` already returns an Element.

## Quick self-check
<details><summary>Q1. Is `{"vlan": 10, "active": true, "desc": null}` valid JSON?</summary>Yes; double quotes, lowercase literals, no trailing comma and no comments.</details>
<details><summary>Q2. Which expression returns the second device's IP from `{"response": [{...}, {"hostname": "leaf2", "ip": "10.1.1.2"}]}`?</summary>`data["response"][1]["ip"]`; `response` is a list, so it needs an index before the key.</details>
<details><summary>Q3. After `xmltodict.parse('<vlan id="10"><name>USERS</name></vlan>')`, how do you get "10"?</summary>`d["vlan"]["@id"]`; xmltodict prefixes attributes with `@`.</details>
<details><summary>Q4. Which data format does NETCONF require?</summary>XML only; RESTCONF can use XML or JSON.</details>
<details><summary>Q5. Which XML snippet is well-formed: `<intf><name>Gi1</Name></intf>` or `<intf><name>Gi1</name><shutdown/></intf>`?</summary>The second; the first has a case mismatch between `<name>` and `</Name>`.</details>

## Cheat lines to say out loud
- "NETCONF speaks XML, REST speaks JSON, Ansible speaks YAML."
- "The s in loads means string; no s means file."
- "Safe load for YAML, defusedxml for XML: never trust strangers' data."
- "xmltodict: at-sign for attributes, hash-text for text, one item is a dict, many is a list."
- "Curly brace means key, square bracket means index."
