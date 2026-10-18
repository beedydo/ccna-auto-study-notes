#!/usr/bin/env python3
"""T48.07: why cookie and token platforms need a requests.Session(), and Basic ones do not.

Builds requests offline (nothing is sent). A Session keeps the login cookie and adds it to
every later request; plain requests.Request(...) forgets it.

  python3 labs/T48/session_demo.py
"""
import requests

URL = "https://apic.example/api/class/fabricNode.json"

# Pretend the aaaLogin.json reply already set this cookie on the session.
s = requests.Session()
s.cookies.set("APIC-cookie", "<token>", domain="apic.example")

with_session = s.prepare_request(requests.Request("GET", URL))
plain = requests.Request("GET", URL).prepare()
basic = requests.Request("GET", "https://ise.example:9060/ers/config/networkdevice",
                         auth=("apiuser", "apipass")).prepare()

print("ACI, Session   :", with_session.headers.get("Cookie"))
print("ACI, plain     :", plain.headers.get("Cookie"))
print("ISE, plain     :", basic.headers.get("Authorization", "")[:12] + "...", "(no Session needed)")
