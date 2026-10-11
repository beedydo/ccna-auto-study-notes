"""T11 reference program: a requests client for the mock inventory API.

Same API as T07 (labs/T07/rest_walkthrough.py used urllib), now with `requests`:
log in, reuse a Session, page through devices, CRUD, retry on 429, handle every error.

Run everything:   bash labs/T11/run_lab.sh
Credentials are fake and read from env vars (defaults match the local mock).
"""
import json
import os
import time
import warnings
from urllib.parse import urljoin

import requests
import urllib3

BASE_URL = os.environ.get("API_BASE", "https://127.0.0.1:8111/api/v1")
USER = os.environ.get("API_USER", "admin")
PASSWORD = os.environ.get("API_PASS", "C1sco12345")
CA_CERT = os.environ.get("API_CA_CERT", True)   # path to the mock's self-signed cert (run_lab.sh sets it)


def show(resp):
    """One line per response: method, URL, status code, reason phrase."""
    print(f"  {resp.request.method:6} {resp.url} -> {resp.status_code} {resp.reason}")


def tls_demo():
    """T11.06: verify=True fails on a self-signed cert, verify=False warns, verify=<CA path> works."""
    url = f"{BASE_URL}/health"
    try:
        requests.get(url, timeout=5)                                   # verify=True is the default
    except requests.exceptions.SSLError as err:
        print("  verify=True (default) ->", type(err).__name__, "(self-signed cert)")
    with warnings.catch_warnings(record=True) as caught:               # capture the warning to print it
        warnings.simplefilter("always")
        resp = requests.get(url, verify=False, timeout=5)
    print("  verify=False          ->", resp.status_code, "+", caught[0].category.__name__)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # lab only: hide the warning
    with warnings.catch_warnings(record=True) as caught:               # no "always" filter this time
        requests.get(url, verify=False, timeout=5)
    print("  after disable_warnings ->", len(caught), "warnings")
    resp = requests.get(url, verify=CA_CERT, timeout=5)                # the right fix: trust the cert
    print("  verify=<CA cert path> ->", resp.status_code, "no warning")


def login():
    """T11.07 step 1: POST credentials with Basic auth, read the token from the JSON body."""
    resp = requests.post(f"{BASE_URL}/auth/token", auth=(USER, PASSWORD), verify=CA_CERT, timeout=5)
    show(resp)
    resp.raise_for_status()
    return resp.json()["Token"]


def get_all_devices(session, role=None):
    """T11.07 pagination: keep calling while the body has a "next" link."""
    devices, url = [], f"{BASE_URL}/devices"
    params = {"limit": 2, "role": role}            # a None value is left out of the query string
    while url:
        resp = session.get(url, params=params, timeout=5)
        show(resp)
        resp.raise_for_status()
        data = resp.json()
        devices.extend(data["response"])
        url = urljoin(BASE_URL, data["next"]) if data["next"] else None
        params = None                              # the next link already carries the query string
    return devices


def get_with_retry(session, url, max_tries=4):
    """T11.07 rate limit: on 429, sleep Retry-After seconds, then try again."""
    for attempt in range(1, max_tries + 1):
        resp = session.get(url, timeout=5)
        show(resp)
        if resp.status_code != 429:
            resp.raise_for_status()
            return resp
        wait = int(resp.headers.get("Retry-After", 1))
        print(f"         try {attempt} got 429: sleeping {wait}s (Retry-After), then retrying")
        time.sleep(wait)
    raise RuntimeError(f"still rate limited after {max_tries} tries")


def safe_get(session, url, timeout=5):
    """T11.05: catch the specific exceptions first and the base class last."""
    try:
        resp = session.get(url, timeout=timeout)
        resp.raise_for_status()                    # 4xx/5xx -> HTTPError
        return resp.json()
    except requests.exceptions.HTTPError as err:
        print(f"  HTTPError: {err}")
        print(f"    err.response.json() = {err.response.json()}")
    except requests.exceptions.Timeout as err:
        print(f"  Timeout ({type(err).__name__}): no reply within {timeout}s")
    except requests.exceptions.ConnectionError as err:
        print(f"  ConnectionError: nothing listening at {err.request.url}")
    except requests.exceptions.RequestException as err:  # base class of all of the above
        print(f"  RequestException ({type(err).__name__}): {err}")
    return None


def main():
    print("== 1. TLS: verify= ==")
    tls_demo()

    print("\n== 2. Log in, then reuse a Session ==")
    token = login()
    session = requests.Session()
    session.headers.update({"X-Auth-Token": token, "Accept": "application/json"})
    session.verify = CA_CERT                       # every session call checks the cert
    show(requests.get(f"{BASE_URL}/devices", verify=CA_CERT, timeout=5))     # no token -> 401
    show(session.get(f"{BASE_URL}/devices", timeout=5))                      # token from session -> 200
    ports = {session.get(f"{BASE_URL}/health", timeout=5).headers["X-Client-Port"] for _ in range(3)}
    print(f"  Session: 3 calls over {len(ports)} TCP connection(s)")
    ports = {requests.get(f"{BASE_URL}/health", verify=CA_CERT, timeout=5).headers["X-Client-Port"]
             for _ in range(3)}
    print(f"  requests.get: 3 calls over {len(ports)} TCP connection(s)")

    print("\n== 3. Read every page, inspect, extract ==")
    devices = get_all_devices(session)
    print(json.dumps(devices[:2], indent=2))       # look at the structure first
    for d in devices:                              # then pull out the fields you need
        print(f"  {d['hostname']:8} {d['mgmt_ip']:12} {d['role']}")

    print("\n== 4. Create, update, delete ==")
    new = {"hostname": "edge3", "mgmt_ip": "10.10.20.50", "role": "edge", "os": "iosxe"}
    show(session.post(f"{BASE_URL}/devices", data=new, timeout=5))          # dict as a form -> 415
    resp = session.post(f"{BASE_URL}/devices", json=new, timeout=5)          # json= -> 201
    show(resp)
    print(f"  status_code={resp.status_code!r} ok={resp.ok} Location={resp.headers['location']}")
    print(f"  text={resp.text!r}")
    print(f"  content={resp.content[:30]!r}...")
    print(f"  json()['id']={resp.json()['id']}")
    item = urljoin(BASE_URL, resp.headers["Location"])
    show(session.request("PATCH", item, json={"role": "core"}, timeout=5))  # generic form of .patch()
    show(session.put(item, json={**new, "role": "core", "mgmt_ip": "10.10.20.51"}, timeout=5))
    resp = session.delete(item, timeout=5)
    show(resp)
    try:
        resp.json()                                # 204 has an empty body
    except requests.exceptions.JSONDecodeError:
        print(f"  204 body={resp.text!r} -> .json() raises JSONDecodeError")

    print("\n== 5. Rate limit: retry on 429 ==")
    for _ in range(3):
        get_with_retry(session, f"{BASE_URL}/interfaces/stats")

    print("\n== 6. Errors ==")
    safe_get(session, f"{BASE_URL}/devices/99")                       # 404 -> HTTPError
    safe_get(session, f"{BASE_URL}/slow", timeout=1)                  # server takes 3 s -> Timeout
    safe_get(session, "https://127.0.0.1:8112/api/v1/health")         # nothing on 8112 -> ConnectionError
    safe_get(session, "127.0.0.1:8111/api/v1/health")                 # no scheme -> RequestException


if __name__ == "__main__":
    main()
