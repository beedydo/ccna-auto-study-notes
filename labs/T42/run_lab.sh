#!/usr/bin/env bash
# Start the mock Webex API + device, wait until it answers, run a client, then stop the mock.
# Usage:  bash labs/T42/run_lab.sh                          (runs webex_bot.py)
#         bash labs/T42/run_lab.sh labs/T42/xapi_device.py
#         bash labs/T42/run_lab.sh labs/T42/webex_sdk.py
#         bash labs/T42/run_lab.sh labs/T42/curl_drill.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CLIENT="${1:-$HERE/webex_bot.py}"
PY="${PYTHON:-python3}"
PORT="${MOCK_PORT:-18042}"
export WEBEX_BASE="${WEBEX_BASE:-http://127.0.0.1:$PORT/v1}"
export DEVICE_URL="${DEVICE_URL:-http://127.0.0.1:$PORT}"

MOCK_PORT="$PORT" python3 "$HERE/mock_webex.py" > /dev/null 2>&1 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null' EXIT

for _ in $(seq 1 40); do
  curl --silent --output /dev/null "http://127.0.0.1:$PORT/v1/people/me" && break
  sleep 0.25
done

case "$CLIENT" in
  *.py) "$PY" "$CLIENT" ;;
  *)    bash "$CLIENT" ;;
esac
