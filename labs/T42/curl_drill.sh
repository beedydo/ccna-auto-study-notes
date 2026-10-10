#!/usr/bin/env bash
# T42 curl drill: post a Webex message and query a device, with curl only.
# Run:  bash labs/T42/run_lab.sh labs/T42/curl_drill.sh
# Real Webex: export WEBEX_BASE=https://webexapis.com/v1 WEBEX_TOKEN=<token>
set -u
BASE="${WEBEX_BASE:-http://127.0.0.1:18042/v1}"
TOKEN="${WEBEX_TOKEN:-T42-mock-bot-token}"
DEVICE="${DEVICE_URL:-http://127.0.0.1:18042}"

echo "== 1. Create a space"
ROOM_ID=$(curl --silent --request POST "$BASE/rooms" \
  --header "Authorization: Bearer $TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"title": "T42-curl-drill"}' \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['id'])")
echo "ROOM_ID=${ROOM_ID:0:24}..."

echo; echo "== 2. Post a markdown message"
curl --silent --request POST "$BASE/messages" \
  --header "Authorization: Bearer $TOKEN" \
  --header "Content-Type: application/json" \
  --data "{\"roomId\": \"$ROOM_ID\", \"markdown\": \"**curl** works\"}" \
  | python3 -c "import json, sys; m = json.load(sys.stdin); print(m['roomType'], repr(m['text']), m['markdown'])"

echo; echo "== 3. Forget 'Bearer ' -> 401"
curl --silent --include "$BASE/people/me" --header "Authorization: $TOKEN" | head -n 1

echo; echo "== 4. Device xAPI over HTTP (Basic auth, XML)"
curl --silent --user integrator:integrator "$DEVICE/getxml?location=/Status/Audio/Volume"
echo
curl --silent --user integrator:integrator --request POST "$DEVICE/putxml" \
  --header "Content-Type: text/xml" \
  --data '<Command><Audio><Volume><Set><Level>20</Level></Set></Volume></Audio></Command>'
echo

echo; echo "== 5. Clean up"
curl --silent --output /dev/null --write-out "DELETE room -> %{http_code}\n" --request DELETE \
  --header "Authorization: Bearer $TOKEN" "$BASE/rooms/$ROOM_ID"
