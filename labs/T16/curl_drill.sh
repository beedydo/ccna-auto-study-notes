#!/usr/bin/env bash
# T16 curl drill. Mock: bash labs/T16/run_lab.sh labs/T16/curl_drill.sh
# Real device: RESTCONF_HOST=... RESTCONF_USER=... RESTCONF_PASS=... bash labs/T16/curl_drill.sh
set -u
HOST="${RESTCONF_HOST:-127.0.0.1:9443}"
CREDS="${RESTCONF_USER:-admin}:${RESTCONF_PASS:-C1sco12345}"
URL="https://$HOST/restconf/data/ietf-interfaces:interfaces"

echo "== 1. GET one leaf, JSON, show status line + headers"
curl --silent --insecure --include --user "$CREDS" \
  --header "Accept: application/yang-data+json" \
  "$URL/interface=GigabitEthernet1/description"

echo; echo "== 2. Same GET with no Accept header: which encoding comes back?"
curl --silent --insecure --user "$CREDS" \
  "$URL/interface=GigabitEthernet1/description"

echo; echo "== 3. PATCH (merge) a description: 204, no body"
curl --silent --insecure --include --request PATCH --user "$CREDS" \
  --header "Content-Type: application/yang-data+json" \
  --header "Accept: application/yang-data+json" \
  --data '{"ietf-interfaces:interface": {"name": "GigabitEthernet3", "description": "LAN users - floor 2"}}' \
  "$URL/interface=GigabitEthernet3"

echo; echo "== 4. --data with curl's default Content-Type: 415"
curl --silent --insecure --include --request PATCH --user "$CREDS" \
  --header "Accept: application/yang-data+json" \
  --data '{"ietf-interfaces:interface": {"name": "GigabitEthernet3", "enabled": false}}' \
  "$URL/interface=GigabitEthernet3"

echo; echo "== 5. Wrong password: 401"
curl --silent --insecure --output /dev/null --write-out "HTTP %{http_code}\n" \
  --user "admin:wrong" --header "Accept: application/yang-data+json" "$URL"
