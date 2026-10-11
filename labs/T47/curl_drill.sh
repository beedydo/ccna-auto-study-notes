#!/usr/bin/env bash
# T47 curl drill: the auth flow + async flow, one curl per solid arrow.
# Starts labs/T47/mock_api.py on 127.0.0.1:8147, runs the calls, then stops the API.
#   bash labs/T47/curl_drill.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
BASE="http://127.0.0.1:8147"

python3 "$HERE/mock_api.py" > /dev/null 2>&1 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null' EXIT
for _ in $(seq 1 40); do
  curl --silent --output /dev/null "$BASE/health" && break
  sleep 0.25
done

echo "== arrow 1: no token yet (the out-of-order bug)"
curl --silent --write-out " [HTTP %{http_code}]\n" "$BASE/dna/intent/api/v1/network-device"

echo "== arrows 1-2: POST credentials -> 200 + token"
TOKEN=$(curl --silent --request POST --user "devnet:cisco123" "$BASE/dna/system/api/v1/auth/token" \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['Token'])")
echo "Token=$TOKEN"

echo "== arrows 3-4: GET with X-Auth-Token -> 200 + data"
curl --silent --write-out " [HTTP %{http_code}]\n" --header "X-Auth-Token: $TOKEN" \
  "$BASE/dna/intent/api/v1/network-device?offset=1&limit=2"

echo "== async arrows 1-2: POST job -> 202 + taskId"
TASK_ID=$(curl --silent --request POST --header "X-Auth-Token: $TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"commands": ["show version"], "deviceUuids": ["dev-1"]}' \
  "$BASE/dna/intent/api/v1/network-device-poller/cli/read-request" \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['response']['taskId'])")
echo "taskId=$TASK_ID"

echo "== async loop: GET the task until endTime appears"
for poll in 1 2 3; do
  curl --silent --write-out " [HTTP %{http_code}] poll $poll\n" --header "X-Auth-Token: $TOKEN" \
    "$BASE/dna/intent/api/v1/task/$TASK_ID"
done

echo "== async last arrow: GET the result"
curl --silent --write-out " [HTTP %{http_code}]\n" --header "X-Auth-Token: $TOKEN" \
  "$BASE/dna/intent/api/v1/file/file-001"
