# T51 · Summary examples: REST request/response anatomy and parsing a dictionary: essentials

> Worked examples for blueprint 2.x (REST) and 1.x/5.x (reading Python) · Related: [T45](T45-reading-python-scripts-using-cisco-apis.md), [T50](T50-api-cheatsheet-transport-auth-operations.md)

## 🧭 The big idea
| Example | Shows | Exam cue |
|---|---|---|
| 1. REST request + response | the six parts of one HTTP exchange (raw) | "which part carries X?" |
| 2. Parsing a dictionary | `[]` vs `.get()`, dict holding a list of dicts, looping | "what does this script print?" |

## Example 1 · The six parts of a REST call
🟦 = what I send · 🟩 = what I get back · headers and body are split by one blank line.

```text
🟦 REQUEST (client → server)
  POST /api/v1/devices HTTP/1.1                     ◀── [1] request line
  Content-Type: application/json                    ◀── [2] request headers
  Accept: application/json                          ◀── [2]
  Authorization: Bearer abc123                      ◀── [2]
  Content-Length: 33                                ◀── [2]
                                                    ◀── (blank line: headers end, body starts)
  {"name": "sw1", "ip": "10.0.0.1"}                 ◀── [3] request body

🟩 RESPONSE (server → client)
  HTTP/1.1 201 Created                              ◀── [4] status line
  Content-Type: application/json                    ◀── [5] response headers
  Location: /api/v1/devices/42                      ◀── [5]
  Content-Length: 25                                ◀── [5]
                                                    ◀── (blank line: headers end, body starts)
  {"id": 42, "name": "sw1"}                         ◀── [6] response body
```

### 🚩 Exam traps
| Looks like | Actually |
|---|---|
| `Content-Type` and `Accept` are the same | `Content-Type` = format of **my body**; `Accept` = format I **want back** |
| `json=` and `data=` are the same | `json=` serialises the dict **and** sets `Content-Type: application/json`; `data=` does neither |
| `resp.json` | a method: needs `()` |
| `201` means done | `201` = created (check `Location`); `202` = accepted, not finished |
| Headers and body are one thing | headers = metadata (auth, format, length); body = the data |

## Example 2 · Python script parsing a dictionary
A typical API reply is a dict holding a list of dicts. Read it from the outside in.

```python
data = {
    "version": "1.0",
    "devices": [
        {"hostname": "sw1", "status": "up"},
        {"hostname": "sw2", "status": "down"},
    ],
}

print(data["version"])
for device in data["devices"]:
    print(device["hostname"], device["status"])
print(data["devices"][0].get("role", "n/a"))
```

Output:
```text
1.0
sw1 up
sw2 down
n/a
```

| Syntax | Meaning | Trap |
|---|---|---|
| `data["version"]` | value for a key | missing key → `KeyError` |
| `data["devices"]` | the list of dicts | a list, so loop it or index it |
| `for device in data["devices"]` | one dict per loop | looping a dict directly gives **keys** |
| `data["devices"][0]` | first item of the list | index starts at `0` |
| `.get("role", "n/a")` | value or default | missing key → default, **no** error |
