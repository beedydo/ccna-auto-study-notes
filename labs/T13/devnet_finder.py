"""T13 lab: match a scenario to the right DevNet resource, and check the URLs are live.

    python3 labs/T13/devnet_finder.py "need a lab to test a RESTCONF call"
    python3 labs/T13/devnet_finder.py --drill     # run the built-in exam scenarios
    python3 labs/T13/devnet_finder.py --check     # HTTP status of every resource URL

Standard library only. --check needs internet; redirects are shown, not followed.
"""
import argparse
import sys
import urllib.error
import urllib.request

# One entry per DevNet resource: the verb to remember, where it lives, and the
# words that point to it in an exam scenario.
RESOURCES = [
    {"name": "DevNet Sandbox", "verb": "TRY",
     "url": "https://developer.cisco.com/site/sandbox/",
     "keywords": ["lab", "test", "try", "hardware", "environment", "reserve",
                  "always-on", "admin", "vpn", "no equipment"]},
    {"name": "Learning Labs", "verb": "LEARN",
     "url": "https://developer.cisco.com/learning/",
     "keywords": ["step by step", "step-by-step", "tutorial", "guided",
                  "track", "module", "new to", "beginner"]},
    {"name": "Code Exchange", "verb": "REUSE",
     "url": "https://developer.cisco.com/codeexchange/",
     "keywords": ["sample code", "existing script", "github", "repo",
                  "reuse", "example code", "share my code", "use case"]},
    {"name": "API documentation", "verb": "LOOK UP",
     "url": "https://developer.cisco.com/docs/",
     "keywords": ["endpoint", "schema", "reference", "openapi", "parameter",
                  "payload", "sdk docs", "exact url"]},
    {"name": "Community forums", "verb": "ASK",
     "url": "https://community.cisco.com/t5/for-developers/ct-p/4409j-developer-home",
     "keywords": ["peer", "community", "others", "forum", "discuss",
                  "sandbox is down"]},
    {"name": "Developer support case", "verb": "ESCALATE",
     "url": "https://developer.cisco.com/docs/devnet-support/support-faq/",
     "keywords": ["ticket", "case", "cisco engineer", "one-on-one",
                  "unresolved", "bug in the api"]},
]

DRILL = [
    "need a lab to test a RESTCONF call without buying hardware",
    "need full admin rights on a private ACI fabric for a day",
    "find an existing script on GitHub that pulls Meraki clients",
    "new to NETCONF and want a guided step by step tutorial",
    "look up the exact endpoint and request schema for Catalyst Center",
    "ask peers whether others see the same API quirk",
    "forum gave no answer, open a case with a Cisco engineer",
]


def match(scenario):
    """Return (resource, score) for the resource whose keywords appear most often."""
    text = scenario.lower()
    scored = [(sum(k in text for k in r["keywords"]), r) for r in RESOURCES]
    score, best = max(scored, key=lambda pair: pair[0])
    return (best, score) if score else (None, 0)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # surface the 301/302 instead of following it


def check(url, timeout=8):
    opener = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, headers={"User-Agent": "T13-lab"})
    try:
        with opener.open(req, timeout=timeout) as resp:
            return f"{resp.status}"
    except urllib.error.HTTPError as err:
        where = err.headers.get("Location")
        return f"{err.code} -> {where}" if where else f"{err.code}"
    except (urllib.error.URLError, TimeoutError) as err:
        return f"unreachable ({err})"


def main():
    parser = argparse.ArgumentParser(description="Scenario -> DevNet resource")
    parser.add_argument("scenario", nargs="?", help="scenario text to match")
    parser.add_argument("--drill", action="store_true", help="run built-in scenarios")
    parser.add_argument("--check", action="store_true", help="HTTP-check every URL")
    args = parser.parse_args()

    if args.check:
        for r in RESOURCES:
            print(f"{r['name']:<24} {check(r['url'])}")
        return 0

    scenarios = DRILL if args.drill else [args.scenario] if args.scenario else []
    if not scenarios:
        parser.print_help()
        return 1
    for s in scenarios:
        best, score = match(s)
        answer = f"{best['verb']:<8} -> {best['name']}" if best else "no match"
        print(f"{answer:<36} | {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
