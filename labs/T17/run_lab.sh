#!/usr/bin/env bash
# Start the mock NX-OS + IOS XE devices, wait until they answer, run a client, then stop them.
# Usage:  bash labs/T17/run_lab.sh                       (runs device_apis.py)
#         bash labs/T17/run_lab.sh labs/T17/curl_drill.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CLIENT="${1:-$HERE/device_apis.py}"
PY="${PYTHON:-python3}"

"$PY" "$HERE/mock_devices.py" > /dev/null 2>&1 &
MOCK_PID=$!
trap 'kill $MOCK_PID 2>/dev/null' EXIT

for _ in $(seq 1 40); do
  curl --silent --output /dev/null "http://127.0.0.1:18444/" && break
  sleep 0.25
done

case "$CLIENT" in
  *.py) "$PY" "$CLIENT" ;;
  *)    bash "$CLIENT" ;;
esac
