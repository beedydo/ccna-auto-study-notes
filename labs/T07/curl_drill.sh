#!/usr/bin/env bash
# T07 curl drill against the local mock API. Start it first:  python3 labs/T07/mock_api.py
set -u
BASE="http://127.0.0.1:8080/api/v1"

# Wait up to 10 s for the mock API to answer
for _ in $(seq 1 20); do
  curl --silent --output /dev/null "$BASE/health" && break
  sleep 0.5
done

TOKEN=$(curl --silent --request POST --user admin:C1sco12345 "$BASE/auth/token" \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['token'])")
echo "TOKEN=$TOKEN"

echo; echo "== 1. --include: status line + headers + body"
curl --silent --show-error --include \
  --header "Authorization: Bearer $TOKEN" \
  "$BASE/devices/1"

echo; echo; echo "== 2. --data alone: curl switches to POST and sends a FORM content type -> 415"
curl --silent --show-error --include \
  --header "Authorization: Bearer $TOKEN" \
  --data '{"hostname":"edge9"}' \
  "$BASE/devices"

echo; echo; echo "== 3. --request POST + Content-Type + --data: correct create -> 201"
curl --silent --show-error --include --request POST \
  --header "Authorization: Bearer $TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"hostname":"edge9","mgmt_ip":"10.10.20.59","role":"edge","os":"iosxe"}' \
  "$BASE/devices"

echo; echo; echo "== 4. --get + --data: data becomes a query string"
curl --silent --show-error --get \
  --header "Authorization: Bearer $TOKEN" \
  --data "role=core" \
  "$BASE/devices"

echo; echo; echo "== 5. 301 without and with --location"
curl --silent --show-error --include \
  --header "Authorization: Bearer $TOKEN" \
  "$BASE/old/devices"
curl --silent --show-error --location --output /dev/null \
  --write-out "after --location: %{http_code} %{url_effective}\n" \
  --header "Authorization: Bearer $TOKEN" \
  "$BASE/old/devices"

echo; echo "== 6. --verbose: '>' = request we sent, '<' = response we got"
curl --silent --verbose --output /dev/null --request DELETE \
  --header "Authorization: Bearer $TOKEN" \
  "$BASE/devices/4" 2>&1 | grep -E '^[<>] ' | tr -d '\r'
