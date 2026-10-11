"""T08 reference program: a polite API consumer that survives every consumer-side limit.

Start the mock API first:   python3 labs/T08/mock_api.py
Then in another terminal:   python3 labs/T08/consume_api.py
Needs the `requests` library (in the lab container, or: python3 -m pip install requests).
"""
import os
import time
from urllib.parse import urlsplit

import requests

BASE_URL = os.environ.get("API_BASE", "http://127.0.0.1:8108/api/v1")
USER = os.environ.get("API_USER", "admin")
PASSWORD = os.environ.get("API_PASS", "C1sco12345")
TIMEOUT = (3.05, 5)            # (connect, read) seconds: never wait forever
MAX_RETRIES = 4
BACKOFF_CAP = 8                # seconds: exponential backoff never waits longer than this
SHOW = ("Retry-After", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset",
        "Location", "Link", "ETag", "Deprecation", "Sunset")


class Client:
    def __init__(self, ttl=300):
        self.session = requests.Session()
        self.login(ttl)

    # ---------- auth limits ----------
    def login(self, ttl):
        r = self.session.post(f"{BASE_URL}/auth/token", params={"ttl": ttl},
                              auth=(USER, PASSWORD), timeout=TIMEOUT)
        r.raise_for_status()
        self.save_tokens(r.json())

    def save_tokens(self, data):
        self.session.headers["Authorization"] = f"Bearer {data['access_token']}"
        self.refresh_token = data["refresh_token"]
        print(f"    token {data['access_token']} (expires_in={data['expires_in']}s)")

    def refresh(self):
        r = self.session.post(f"{BASE_URL}/auth/token", timeout=TIMEOUT,
                              data={"grant_type": "refresh_token", "refresh_token": self.refresh_token})
        r.raise_for_status()
        self.save_tokens(r.json())

    # ---------- one call, with every retry rule ----------
    def call(self, method, path, quiet=False, **kwargs):
        url = path if path.startswith("http") else BASE_URL + path
        kwargs.setdefault("timeout", TIMEOUT)
        refreshed = False
        for attempt in range(MAX_RETRIES + 1):
            r = self.session.request(method, url, **kwargs)
            if not quiet or r.status_code >= 400:
                show(method, url, r)
            if r.status_code == 401 and "expired" in r.headers.get("WWW-Authenticate", "") and not refreshed:
                print("    ~ token expired: refresh it, then retry once")
                self.refresh()
                refreshed = True
                continue
            if r.status_code == 429:                                 # rate limited: obey the server
                wait = int(r.headers.get("Retry-After", min(2 ** attempt, BACKOFF_CAP)))
                print(f"    ~ 429: sleeping Retry-After={wait}s (attempt {attempt + 1})")
                time.sleep(wait)
                continue
            if r.status_code in (502, 503, 504) and "Retry-After" not in r.headers:
                wait = min(2 ** attempt, BACKOFF_CAP)                # 1, 2, 4, 8, 8 ...
                print(f"    ~ {r.status_code}: exponential backoff, sleeping {wait}s (attempt {attempt + 1})")
                time.sleep(wait)
                continue
            return r
        return r


def show(method, url, r):
    sent = urlsplit(r.url)                                           # the URL actually sent, with ?params
    print(f">>> {method} {sent.path}{'?' + sent.query if sent.query else ''}")
    print(f"<<< {r.status_code} {r.reason}")
    for name in SHOW:
        if name in r.headers:
            print(f"    {name}: {r.headers[name]}")
    if r.status_code >= 400 and r.content:
        print(f"    body: {r.text}")


# ---------- pagination ----------
def first_page_only(api):
    """The classic bug: one GET, no paging loop."""
    return api.call("GET", "/devices").json()["response"]


def all_by_offset(api, limit=5):
    items, offset = [], 0
    while True:
        body = api.call("GET", "/devices", params={"offset": offset, "limit": limit}).json()
        items += body["response"]
        offset += limit
        if offset >= body["total"]:
            return items


def all_by_page_number(api, per_page=4):
    items, page = [], 1
    while True:
        body = api.call("GET", "/events", params={"page": page, "per_page": per_page}).json()
        items += body["items"]
        if page >= body["total_pages"]:
            return items
        page += 1


def all_by_link_header(api, per_page=10):
    items, url = [], f"{BASE_URL}/networks/N_100/clients?perPage={per_page}"
    while url:
        r = api.call("GET", url)
        items += r.json()
        url = r.links.get("next", {}).get("url")                     # None on the last page
    return items


# ---------- payload limits ----------
def chunks(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def main():
    print("== 1. Log in (token has a lifetime) ==")
    api = Client()

    print("\n== 2. Rate limit: 6 status calls against a 3-per-2s limit ==")
    for n in range(1, 7):
        api.call("GET", f"/devices/Q2SW-{n:04d}/status")

    print("\n== 3. 503 with no Retry-After: exponential backoff ==")
    print("    final:", api.call("GET", "/reports/flaky").json())

    print("\n== 4. Pagination ==")
    print(f"    BUG first page only: {len(first_page_only(api))} devices")
    print(f"    offset/limit:        {len(all_by_offset(api))} devices")
    print(f"    page/per_page:       {len(all_by_page_number(api))} events")
    print(f"    Link rel=next:       {len(all_by_link_header(api))} clients")

    print("\n== 5. Payload limits ==")
    serials = [f"Q2XX-{n:04d}" for n in range(1, 41)]
    api.call("POST", "/devices/claim", json={"serials": serials})               # 413: body too big
    api.call("POST", "/devices/claim", json={"serials": serials[:15]})          # 400: too many items
    for batch in chunks(serials, 10):                                           # fix: split
        r = api.call("POST", "/devices/claim", json={"serials": batch}, quiet=True)
        print(f"    batch of {len(batch)} -> {r.status_code} {r.json()}")

    print("\n== 6. Timeouts and async jobs ==")
    try:
        api.call("GET", "/reports/slow", timeout=(3.05, 1))
    except requests.exceptions.ReadTimeout:
        print("    requests.exceptions.ReadTimeout: no reply within the 1 s read timeout")
    print("    with read timeout 5s:", api.call("GET", "/reports/slow", quiet=True).json())
    r = api.session.get(f"{BASE_URL}/reports/gateway", timeout=TIMEOUT)        # one raw call, no retry loop
    show("GET", r.url, r)
    r = api.call("POST", "/reports")                                            # 202 + Location
    job_url = r.headers["Location"].replace("/api/v1", "")
    while True:
        poll = api.call("GET", job_url, quiet=True)
        print(f"    poll {job_url} -> {poll.json()['status']}")
        if poll.json()["status"] == "complete":
            break
        time.sleep(int(poll.headers.get("Retry-After", 1)))

    print("\n== 7. Token expiry mid-script ==")
    short = Client(ttl=1)
    time.sleep(1.5)
    print("    final:", short.call("GET", "/devices", params={"limit": 1}).status_code)

    print("\n== 8. Versioning ==")
    old = api.call("GET", BASE_URL.replace("/v1", "/v0") + "/devices").json()["response"]
    print(f"    v0 fields: {sorted(old[0])}  (v1 renamed name -> hostname)")
    api.call("GET", BASE_URL.replace("/v1", "/v2") + "/devices")

    print("\n== 9. Caching with ETag ==")
    r = api.call("GET", "/devices/Q2SW-0001")
    cached, etag = r.json(), r.headers["ETag"]
    r = api.call("GET", "/devices/Q2SW-0001", headers={"If-None-Match": etag})
    if r.status_code == 304:
        print(f"    304: no body ({len(r.content)} bytes), reuse cached {cached['hostname']}")


if __name__ == "__main__":
    main()
