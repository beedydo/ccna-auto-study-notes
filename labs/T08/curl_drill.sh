#!/usr/bin/env bash
# T08 curl drill against the local mock API. Start it first:  python3 labs/T08/mock_api.py
set -u
BASE="http://127.0.0.1:8108/api/v1"

TOKEN=$(curl --silent --request POST --user admin:C1sco12345 "$BASE/auth/token" \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['access_token'])")
echo "TOKEN=$TOKEN"

echo; echo "== 1. Burst 4 calls: the 4th gets 429 + Retry-After + X-RateLimit-*"
for n in 1 2 3 4; do
  curl --silent --output /dev/null --dump-header - \
    --header "Authorization: Bearer $TOKEN" \
    "$BASE/devices/Q2SW-000$n/status" | grep -E '^(HTTP|Retry-After|X-RateLimit)' | tr -d '\r'
done

echo; echo "== 2. curl --retry obeys Retry-After on 429 (needs curl >= 7.66)"
for n in 1 2 3; do                     # use up this window's quota first
  curl --silent --output /dev/null --header "Authorization: Bearer $TOKEN" "$BASE/devices/Q2SW-0005/status"
done
curl --no-progress-meter --retry 3 --output /dev/null \
  --write-out "final %{http_code}\n" \
  --header "Authorization: Bearer $TOKEN" \
  "$BASE/devices/Q2SW-0005/status" 2>&1

echo; echo "== 3. Link header: the next page URL is in a header, not the body"
curl --silent --output /dev/null --dump-header - \
  --header "Authorization: Bearer $TOKEN" \
  "$BASE/networks/N_100/clients?perPage=10" | grep -i '^Link' | tr -d '\r'

echo; echo "== 4. Client-side timeout: --max-time 1 on a 2 s endpoint (exit code 28)"
curl --silent --show-error --max-time 1 \
  --header "Authorization: Bearer $TOKEN" \
  "$BASE/reports/slow"
echo "curl exit code: $?"

echo; echo "== 5. ETag then If-None-Match -> 304, empty body"
ETAG=$(curl --silent --output /dev/null --dump-header - \
  --header "Authorization: Bearer $TOKEN" \
  "$BASE/devices/Q2SW-0001" | grep -i '^ETag' | cut -d' ' -f2 | tr -d '\r')
echo "ETag=$ETAG"
curl --silent --include \
  --header "Authorization: Bearer $TOKEN" \
  --header "If-None-Match: $ETAG" \
  "$BASE/devices/Q2SW-0001" | tr -d '\r'
