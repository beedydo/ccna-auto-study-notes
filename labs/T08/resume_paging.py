"""T08 drill: resume a cursor-paged fetch after a crash, instead of starting again.

Start the mock API first:   python3 labs/T08/mock_api.py
Then:                       python3 labs/T08/resume_paging.py
Or both at once:            bash labs/T08/run_lab.sh labs/T08/resume_paging.py

Run 1 fetches 2 pages, then "crashes" (CRASH_AFTER_PAGES=2) with the bookmark saved.
Run 2 reads the bookmark and fetches only the pages it hadn't got yet.
"""
import json
import os
import pathlib
import tempfile

import requests

BASE_URL = os.environ.get("API_BASE", "http://127.0.0.1:8108/api/v1")
USER = os.environ.get("API_USER", "admin")
PASSWORD = os.environ.get("API_PASS", "C1sco12345")
TIMEOUT = (3.05, 5)
WORK = pathlib.Path(tempfile.gettempdir()) / "t08-resume"
BOOKMARK = WORK / "clients.cursor"      # the next URL to fetch
DATA = WORK / "clients.jsonl"           # one client per line, appended page by page


def session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/auth/token", auth=(USER, PASSWORD), timeout=TIMEOUT)
    r.raise_for_status()
    s.headers["Authorization"] = f"Bearer {r.json()['access_token']}"
    return s


def fetch_all(s, crash_after_pages=None):
    """Fetch every client page. Resumes from BOOKMARK if a previous run stopped early."""
    if BOOKMARK.exists():
        url = BOOKMARK.read_text()
        print(f"  resuming from bookmark: ...{url[url.index('/networks'):]}")
    else:
        url = f"{BASE_URL}/networks/N_100/clients?perPage=10"
        print("  no bookmark: starting from page 1")
    pages = 0
    while url:
        r = s.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        page = r.json()
        with DATA.open("a") as f:                         # 1. save this page's data first
            for client in page:
                f.write(json.dumps(client) + "\n")
        pages += 1
        print(f"  page {pages}: {page[0]['id']}..{page[-1]['id']} saved")
        url = r.links.get("next", {}).get("url")
        if url:
            BOOKMARK.write_text(url)                      # 2. then move the bookmark
        else:
            BOOKMARK.unlink(missing_ok=True)              # last page: nothing left to resume
        if crash_after_pages and pages == crash_after_pages and url:
            raise ConnectionError("simulated crash (network dropped)")


def main():
    WORK.mkdir(exist_ok=True)
    for p in (BOOKMARK, DATA):
        p.unlink(missing_ok=True)
    s = session()

    print("== Run 1 (crashes after 2 pages)")
    try:
        fetch_all(s, crash_after_pages=2)
    except ConnectionError as err:
        print(f"  !! {err}. Bookmark kept: {BOOKMARK.exists()}")

    print("\n== Run 2 (same script, started again)")
    fetch_all(s)

    ids = [json.loads(line)["id"] for line in DATA.read_text().splitlines()]
    print(f"\nSaved {len(ids)} clients ({ids[0]}..{ids[-1]}), duplicates: {len(ids) - len(set(ids))}, "
          f"bookmark left behind: {BOOKMARK.exists()}")


if __name__ == "__main__":
    main()
