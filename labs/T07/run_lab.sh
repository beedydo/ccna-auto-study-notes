#!/usr/bin/env bash
# Start the mock API, wait until it answers, run a client script, then stop the API.
# Usage:  bash labs/T07/run_lab.sh                      (runs rest_walkthrough.py)
#         bash labs/T07/run_lab.sh labs/T07/curl_drill.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CLIENT="${1:-$HERE/rest_walkthrough.py}"

python3 "$HERE/mock_api.py" > /dev/null 2>&1 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null' EXIT

for _ in $(seq 1 40); do
  curl --silent --output /dev/null "http://127.0.0.1:8080/api/v1/health" && break
  sleep 0.25
done

case "$CLIENT" in
  *.py) python3 "$CLIENT" ;;
  *)    bash "$CLIENT" ;;
esac
