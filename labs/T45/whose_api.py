"""T45 drill: name the Cisco platform a script talks to, from the URL/library fingerprints.

Usage:  python3 labs/T45/whose_api.py labs/T45/snippets/*.py labs/T45/device_audit.py
Reads each file as text (nothing is executed) and prints the first fingerprint it finds.
Order matters: the more specific markers are checked first.
"""
import sys

FINGERPRINTS = [
    # (marker in the script text, platform, what the marker is)
    ("ncclient", "NETCONF (ncclient, SSH port 830)", "library"),
    ("/restconf/", "RESTCONF on IOS XE / NX-OS", "URL path"),
    ("api.meraki.com", "Meraki Dashboard API", "cloud host"),
    ("webexapis.com", "Webex API", "cloud host"),
    ("/dataservice", "Catalyst SD-WAN Manager (vManage)", "URL path"),
    ("j_security_check", "Catalyst SD-WAN Manager (vManage)", "login path"),
    ("/dna/", "Catalyst Center (DNA Center)", "URL path"),
    ("/api/aaaLogin", None, "login path"),          # ACI or NX-API REST: decide below
    ('"ins_api"', "NX-API CLI on Nexus (POST /ins)", "JSON body"),
]


def identify(text):
    for marker, platform, kind in FINGERPRINTS:
        if marker in text:
            if platform is None:                      # same login, different object tree
                platform = ("ACI (APIC)" if "uni/" in text or "fvTenant" in text
                            else "NX-API REST on Nexus (DN starts sys/)")
            return platform, f"{kind} {marker}"
    return "unknown", "no fingerprint"


def main():
    for path in sys.argv[1:]:
        with open(path) as handle:
            platform, evidence = identify(handle.read())
        print(f"{path.rsplit('/', 1)[-1]:<16} {platform:<38} <- {evidence}")


if __name__ == "__main__":
    main()
