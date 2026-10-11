"""Lint stage: validate the network intent file before anything is built or deployed."""
import json
import sys

from netlib import Device

path = sys.argv[1]
with open(path) as fh:
    intent = json.load(fh)                        # bad JSON fails here (json.JSONDecodeError)

errors = []
ids = [v["id"] for v in intent["vlans"]]
for vlan in intent["vlans"]:
    if not Device.is_valid_vlan(vlan["id"]):      # reuse the app's own rule (1-4094)
        errors.append(f"VLAN {vlan['id']} out of range 1-4094")
    if not vlan.get("name"):
        errors.append(f"VLAN {vlan['id']} has no name")
if len(ids) != len(set(ids)):
    errors.append(f"duplicate VLAN IDs in {ids}")

for e in errors:
    print(f"  FAIL {path}: {e}")
if errors:
    sys.exit(1)                                   # non-zero exit = the CI job fails
print(f"  OK {path}: {len(ids)} VLANs valid for site {intent['site']}")
