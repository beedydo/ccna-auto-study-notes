#!/usr/bin/env bash
# Start the mock Meraki API, wait until it answers, run a client, then stop the mock.
# Usage:  bash labs/T18/run_lab.sh                         (runs meraki_requests.py)
#         bash labs/T18/run_lab.sh labs/T18/meraki_sdk.py
#         bash labs/T18/run_lab.sh labs/T18/curl_drill.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CLIENT="${1:-$HERE/meraki_requests.py}"
PY="${PYTHON:-python3}"

python3 "$HERE/mock_meraki.py" > /dev/null 2>&1 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null' EXIT

for _ in $(seq 1 40); do
  curl --silent --output /dev/null "http://127.0.0.1:8118/api/v1/organizations" && break
  sleep 0.25
done

case "$CLIENT" in
  *.py) "$PY" "$CLIENT" ;;
  *)    bash "$CLIENT" ;;
esac
