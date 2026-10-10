#!/usr/bin/env bash
# T12 curl drill: device-level vs controller-level calls, raw HTTP, against the local mock.
set -u
BASE="${T12_BASE_URL:-http://127.0.0.1:18012}"
CRED="${T12_USER:-admin}:${T12_PASS:-C1sco12345}"
OC="openconfig-interfaces:interfaces"

echo "== 1. Device-level, CLI text (IOS XE)"
curl --silent --show-error --user "$CRED" --get --data-urlencode "cmd=show ip interface brief" "$BASE/sw1/cli"

echo; echo "== 2. Device-level, same ports as YANG-modelled JSON (first interface only)"
curl --silent --show-error --user "$CRED" --header "Accept: application/yang-data+json" \
  "$BASE/sw1/restconf/data/$OC" \
  | python3 -c "import json, sys; print(json.dumps(json.load(sys.stdin)['$OC']['interface'][0], indent=2))"

echo; echo "== 3. Slash in the key not encoded -> 404"
curl --silent --show-error --user "$CRED" --request PATCH \
  --header "Content-Type: application/yang-data+json" \
  --data '{"openconfig-interfaces:config": {"description": "UNUSED"}}' \
  --write-out "\nHTTP %{http_code}\n" \
  "$BASE/sw1/restconf/data/$OC/interface=GigabitEthernet1/0/3/config"

echo; echo "== 4. Slash encoded as %2F -> 204"
curl --silent --show-error --user "$CRED" --request PATCH \
  --header "Content-Type: application/yang-data+json" \
  --data '{"openconfig-interfaces:config": {"description": "UNUSED"}}' \
  --write-out "HTTP %{http_code}\n" \
  "$BASE/sw1/restconf/data/$OC/interface=GigabitEthernet1%2F0%2F3/config"

echo; echo "== 5. Controller-level: one intent for the whole site"
curl --silent --show-error --user "$CRED" --request POST \
  --header "Content-Type: application/json" \
  --data '{"intent": "disable-unused-ports", "site": "SG-HQ"}' \
  --write-out "\nHTTP %{http_code}\n" \
  "$BASE/ctrl/api/v1/intents"

echo; echo "== 6. Controller-level: unknown site -> rejected before any device is touched"
curl --silent --show-error --user "$CRED" --request POST \
  --header "Content-Type: application/json" \
  --data '{"intent": "disable-unused-ports", "site": "TY-LAB"}' \
  --write-out "\nHTTP %{http_code}\n" \
  "$BASE/ctrl/api/v1/intents"
