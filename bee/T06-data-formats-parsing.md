---
id: T06
title: "Data formats + parsing"
owner: Beedy
blueprint: "1.1, 1.2"
primary_domain: D1
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-06
teach_back: 2026-10-08
cross_study: 2026-10-21
---

# T06 · Data formats + parsing

> Owner: **Beedy** · Blueprint: **1.1, 1.2** · CBT coverage: **Full** · Learn by 2026-10-06 · Teach-back 2026-10-08

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T06.01 · XML

**Must cover:**

- [ ] Optional declaration: <?xml version="1.0" encoding="UTF-8"?>
- [ ] Exactly one root element wraps everything
- [ ] Elements: <name>value</name>; tags are case-sensitive and must close
- [ ] Attributes inside the start tag: <interface type="ethernet">
- [ ] Empty element: <shutdown/>
- [ ] Well-formed = properly nested, closed and quoted; special characters escaped (&lt; &amp;)

**Notes:**

<!-- TODO -->

### T06.02 · XML

**Must cover:**

- [ ] Namespace declared with xmlns="urn:..." or prefixed xmlns:if="..."
- [ ] Avoids name clashes when combining models (e.g. ietf-interfaces vs Cisco native)
- [ ] NETCONF payloads and replies always carry namespaces
- [ ] XPath selects nodes: /interfaces/interface[name="Gi1"]/description

**Notes:**

<!-- TODO -->

### T06.03 · JSON

**Must cover:**

- [ ] Object {"key": value} = unordered key/value pairs; array [1, 2, 3] = ordered list
- [ ] Keys and strings must use double quotes
- [ ] Value types: string, number, true/false, null, object, array
- [ ] No comments, no trailing commas
- [ ] Default format for REST APIs and RESTCONF (application/yang-data+json)

**Notes:**

<!-- TODO -->

### T06.04 · YAML

**Must cover:**

- [ ] Indentation with spaces defines structure (no tabs)
- [ ] key: value pairs; list items start with "- "
- [ ] --- starts a document; # starts a comment
- [ ] Strings usually unquoted; multi-line with | (keep newlines) or > (fold)
- [ ] JSON is valid YAML; used by Ansible, Docker Compose, pyATS testbeds, CI pipelines

**Notes:**

<!-- TODO -->

### T06.05 · Comparison

**Must cover:**

- [ ] XML: most verbose, attributes + namespaces, used by NETCONF and SOAP
- [ ] JSON: compact, native to JavaScript/REST, no comments
- [ ] YAML: most human-readable, supports comments, indentation-sensitive
- [ ] All three can represent the same nested data

**Notes:**

<!-- TODO -->

### T06.06 · Python mapping

**Must cover:**

- [ ] JSON object → Python dict
- [ ] JSON array → list
- [ ] JSON string → str; number → int/float
- [ ] true/false → True/False; null → None
- [ ] Going back (dumps) reverses the mapping

**Notes:**

<!-- TODO -->

### T06.07 · Python json

**Must cover:**

- [ ] import json
- [ ] json.loads(text) → Python object; json.dumps(obj) → JSON string
- [ ] json.load(file_obj) and json.dump(obj, file_obj) work with files
- [ ] json.dumps(obj, indent=2) pretty-prints; sort_keys=True sorts keys
- [ ] response.json() in requests already does json.loads for you

**Notes:**

<!-- TODO -->

### T06.08 · Python YAML

**Must cover:**

- [ ] import yaml (PyYAML package)
- [ ] yaml.safe_load(text) → dict/list (safe: no arbitrary object creation)
- [ ] yaml.load without a safe Loader can execute code: avoid with untrusted input
- [ ] yaml.dump(obj) / yaml.safe_dump(obj) → YAML string

**Notes:**

<!-- TODO -->

### T06.09 · Python XML

**Must cover:**

- [ ] xmltodict.parse(xml_string) → nested dict (OrderedDict in older versions)
- [ ] Attributes become keys prefixed with @ (e.g. ["@type"])
- [ ] Element text with attributes is under "#text"
- [ ] Repeated elements become a list
- [ ] xmltodict.unparse(dict) → XML string

**Notes:**

<!-- TODO -->

### T06.10 · Python XML

**Must cover:**

- [ ] import xml.etree.ElementTree as ET
- [ ] root = ET.fromstring(text) or ET.parse(file).getroot()
- [ ] root.find("tag") first match; root.findall("tag") all matches; iter() walks the tree
- [ ] elem.tag, elem.text, elem.attrib (dict of attributes)
- [ ] Namespaced tags look like {urn:...}name; pass a namespaces dict to find()
- [ ] xml.dom.minidom: older DOM API; toprettyxml() for display

**Notes:**

<!-- TODO -->

### T06.11 · Navigating data

**Must cover:**

- [ ] Chain keys and indexes: data["response"][0]["hostname"]
- [ ] Loop: for dev in data["devices"]: print(dev["name"])
- [ ] dict.get("key", default) avoids KeyError
- [ ] Check type() when unsure whether a level is a list or dict

**Notes:**

<!-- TODO -->

### T06.12 · Terms

**Must cover:**

- [ ] Serialisation (encoding): Python object → text/bytes for storage or sending
- [ ] Deserialisation (decoding/parsing): text → Python object
- [ ] In APIs: you serialise the request body and deserialise the response body

**Notes:**

<!-- TODO -->

### T06.13 · Exam angle

**Must cover:**

- [ ] Spot the invalid snippet (single quotes in JSON, tab in YAML, unclosed XML tag)
- [ ] Pick the Python expression that extracts a given value from parsed data
- [ ] Match a format to its typical use (NETCONF = XML, REST = JSON, Ansible = YAML)

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
| T06.1 | Video | XML syntax, elements/tags/attributes, DOM only | 13 | CBT: XML, JSON, and YAML Data Formats |
| T06.2 | Video | Parse Data Formats into Python Structures | 26 | CBT module |
| T06.3 | Lab | Parse RESTCONF XML with xmltodict + ElementTree | 25 | Docker lab |

- Skip / low priority: Long parsing walkthroughs

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
