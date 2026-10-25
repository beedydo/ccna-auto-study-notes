"""T30 OWASP: the DEFENSIVE pattern for each attack, safe and runnable.

No attack lab: this shows WHY each fix works, with real output.
Run: python3 labs/T30/defences.py   (stdlib only)
"""
import hmac
import html
import secrets
import sqlite3


def sqli_demo():
    print("== 1. SQL injection: vulnerable vs parameterised ==")
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE users(name TEXT, role TEXT)")
    db.executemany("INSERT INTO users VALUES (?,?)", [("alice", "admin"), ("bob", "user")])
    evil = "' OR 1=1 --"

    q = f"SELECT * FROM users WHERE name = '{evil}'"   # VULNERABLE: string-built
    print("sent to DB:", q)
    print("vulnerable returns:", db.execute(q).fetchall())

    # SAFE: placeholder, value bound separately
    print("parameterised returns:",
          db.execute("SELECT * FROM users WHERE name = ?", (evil,)).fetchall())


def xss_demo():
    print("\n== 2. XSS: output encoding ==")
    comment = "<script>alert(document.cookie)</script>"
    print("stored/displayed as:", html.escape(comment))


def csrf_demo():
    print("\n== 3. CSRF: anti-CSRF token ==")
    issued = secrets.token_urlsafe(32)   # server issues per session, embeds in form

    def handle(submitted):
        if not hmac.compare_digest(submitted, issued):
            return "403 rejected"
        return "200 action performed"

    print("real user  :", handle(issued))
    print("attacker   :", handle(""))


if __name__ == "__main__":
    sqli_demo()
    xss_demo()
    csrf_demo()
