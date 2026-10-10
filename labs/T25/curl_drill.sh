#!/usr/bin/env bash
# T25 curl drill: NSO RESTCONF actions and dry-run by hand. Start the mock first:
#   python3 labs/T25/mock_nso_cml.py      (or: bash labs/T25/run_lab.sh labs/T25/curl_drill.sh)
set -u
NSO="${NSO_URL:-http://127.0.0.1:18025}"
AUTH="${NSO_USER:-admin}:${NSO_PASS:-admin}"
JSON="application/yang-data+json"

echo "== 1. Wrong password -> 401 (NSO RESTCONF uses HTTP Basic)"
curl --silent --write-out "HTTP %{http_code}\n" --output /dev/null \
  --user "admin:wrong" --header "Accept: $JSON" \
  "$NSO/restconf/data/tailf-ncs:devices/device"

echo; echo "== 2. check-sync one device (an action = POST, no body)"
curl --silent --request POST --user "$AUTH" --header "Accept: $JSON" \
  "$NSO/restconf/data/tailf-ncs:devices/device=ios0/check-sync"

echo; echo; echo "== 3. sync-to: push NSO's copy (CDB) down to the box, overwriting the CLI change"
curl --silent --request POST --user "$AUTH" --header "Accept: $JSON" \
  "$NSO/restconf/data/tailf-ncs:devices/device=ios0/sync-to"
echo
curl --silent --request POST --user "$AUTH" --header "Accept: $JSON" \
  "$NSO/restconf/data/tailf-ncs:devices/check-sync"

echo; echo; echo "== 4. Service create with ?dry-run=native: preview only, nothing committed"
curl --silent --request POST --user "$AUTH" \
  --header "Content-Type: $JSON" --header "Accept: $JSON" \
  --data '{"loopback:loopback": [{"name": "T25-LO200", "device": ["xr0"], "id": 200, "ipv4": "10.200.0.1"}]}' \
  "$NSO/restconf/data?dry-run=native"
echo
curl --silent --write-out "after dry-run, GET the service: HTTP %{http_code}\n" --output /dev/null \
  --user "$AUTH" --header "Accept: $JSON" \
  "$NSO/restconf/data/loopback:loopback=T25-LO200"
