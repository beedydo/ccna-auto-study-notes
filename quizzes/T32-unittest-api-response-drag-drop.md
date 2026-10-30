# T32 · Testing an API response with `unittest` (drag-and-drop walkthrough)

> Topic: [T32 TDD + Python unit tests](../bee/T32-tdd-python-unit-tests.md) · Blueprint 1.3 / 4.5 · Added by Bob
> Question type: fill the blanks in a `unittest.TestCase` that tests a Flask-style API (`app.test_client()`), with spare options that are not used.
> This file explains the pattern and the answers in my own words; it does not reproduce the question text.

## The pattern in one go
```python
import unittest
from apidogs import app


class TestsAPIDogs(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()                      # fake HTTP client, no real server

    def test_status(self):
        resp = self.app.get('/dogs/all')
        status_code = resp.status_code                    # blank 1 -> status_code
        self.assertEqual(status_code, 200)                # blank 2 -> 200

    def test_content_type(self):
        resp = self.app.get('/dogs/all')
        self.assertEqual(resp.content_type, 'application/json')   # blank 3 -> content_type

    def test_item_not_exist(self):
        resp = self.app.get('/dogs?id=none')              # blank 4 -> none
        self.assertEqual(resp.status_code, 404)


if __name__ == '__main__':
    unittest.main()
```

## Answers
| Blank | Where | Answer | Why |
|---|---|---|---|
| 1 | `status_code = resp.____` | `status_code` | the response object's attribute holding the HTTP code (an int) |
| 2 | `assertEqual(status_code, ____)` | `200` | a successful `GET` returns `200 OK` |
| 3 | `assertEqual(resp.____, 'application/json')` | `content_type` | the attribute holding the `Content-Type` header value |
| 4 | `get('/dogs?id=____')` | `none` | an id that does not exist, so the next assertion expects `404` |

Not used: `403`, `content`, `status`.

## Why each spare option is wrong
| Spare | Looks like | Actually |
|---|---|---|
| `403` | an error code, so fits the "not found" test | `403` = Forbidden (authenticated but not allowed). Not-found is `404`, and it belongs in the assertion, not the URL |
| `content` | sounds like "content type" | `resp.content` is not an attribute for the `Content-Type`; it is the body. The header is `content_type` |
| `status` | sounds like the status code | `resp.status` is the string `"200 OK"` in Flask/Werkzeug, so it would never equal the int `200` |

## Exam traps
- 🟥 `assertEqual(actual, expected)`: both orders pass, but the exam usually writes the value under test first.
- 🟥 `status_code` is an `int`: `200`, not `"200"`.
- 🟥 `setUp` runs before **every** test method, so each test gets a fresh `test_client()`.
- 🟥 Test methods must start with `test`, or `unittest` will not run them.
- 🟨 `unittest.main()` runs the tests when the file is executed directly (`python3 test_dogs.py`); `if __name__ == '__main__':` guards it.
- 🟨 `test_client()` calls the app in-process: no network, no port, no running server.
- The `__name__` / `__main__` and `test_client` underscores can be lost in rendering; the real names are `__name__ == '__main__'`, `test_client`, `status_code`.

## To verify
- ⚠ verify: attribute names (`status_code`, `content_type`, `status`) are the Flask/Werkzeug `Response` API; checked from memory, not run here (Flask is not installed in this environment).
