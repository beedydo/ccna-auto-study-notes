#!/usr/bin/env bash
# T20 curl drill: token -> X-Auth-Token -> async task, against DNAC_URL (mock or live sandbox).
# Mock:  bash labs/T20/run_lab.sh labs/T20/curl_drill.sh
# Live:  DNAC_URL=https://sandboxdnac2.cisco.com bash labs/T20/curl_drill.sh
set -u
BASE="${DNAC_URL:-https://sandboxdnac2.cisco.com}"
USER_PASS="${DNAC_USER:-devnetuser}:${DNAC_PASS:-Cisco123!}"
json() { python3 -c "import json, sys; d = json.load(sys.stdin); print($1)"; }

echo "== 1. POST auth/token with Basic auth -> {\"Token\": ...}"
TOKEN=$(curl --silent --insecure --request POST --user "$USER_PASS" \
  "$BASE/dna/system/api/v1/auth/token" | json 'd["Token"]')
echo "Token: ${TOKEN:0:20}..."

echo; echo "== 2. No X-Auth-Token header -> 401"
curl --silent --insecure --output /dev/null --write-out "HTTP %{http_code}\n" \
  "$BASE/dna/intent/api/v1/network-device"

echo; echo "== 3. With X-Auth-Token + query filter"
curl --silent --insecure --header "X-Auth-Token: $TOKEN" \
  "$BASE/dna/intent/api/v1/network-device?hostname=sw1" \
  | json '[(x["hostname"], x["managementIpAddress"], x["id"]) for x in d["response"]]'

echo; echo "== 4. Command runner POST -> 202 + taskId"
TASK=$(curl --silent --insecure --request POST \
  --header "X-Auth-Token: $TOKEN" --header "Content-Type: application/json" \
  --data '{"commands": ["show version | include uptime"], "deviceUuids": ["6b3dc2dd-a26f-4807-97eb-9d316b22fa83"]}' \
  --write-out '\n%{http_code}' \
  "$BASE/dna/intent/api/v1/network-device-poller/cli/read-request")
echo "HTTP $(echo "$TASK" | tail -1)  $(echo "$TASK" | head -1)"
TASK_ID=$(echo "$TASK" | head -1 | json 'd["response"]["taskId"]')

echo; echo "== 5. Poll GET task/{taskId} (twice)"
for _ in 1 2; do
  curl --silent --insecure --header "X-Auth-Token: $TOKEN" \
    "$BASE/dna/intent/api/v1/task/$TASK_ID" \
    | json '{k: d["response"].get(k) for k in ("isError", "progress", "endTime")}'
  sleep 1
done
