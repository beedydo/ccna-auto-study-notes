#!/usr/bin/env bash
# Start the T23 mock security APIs, wait until they answer, run a client, then stop the mock.
# Usage:  bash labs/T23/run_lab.sh                         (runs incident_response.py)
#         bash labs/T23/run_lab.sh labs/T23/curl_drill.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CLIENT="${1:-$HERE/incident_response.py}"

python3 "$HERE/mock_security.py" > /dev/null 2>&1 &
MOCK_PID=$!
trap 'kill $MOCK_PID 2>/dev/null' EXIT

for _ in $(seq 1 40); do
  curl --silent --output /dev/null "http://127.0.0.1:9407/" && break
  sleep 0.25
done

case "$CLIENT" in
  *.py) python3 "$CLIENT" ;;
  *)    bash "$CLIENT" ;;
esac
