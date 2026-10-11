#!/usr/bin/env bash
# Start the T12 mock network, wait until it answers, run a client, then stop the mock.
# Usage:  bash labs/T12/run_lab.sh                         (runs automation_levels.py)
#         bash labs/T12/run_lab.sh labs/T12/curl_drill.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CLIENT="${1:-$HERE/automation_levels.py}"
PY="${PYTHON:-python3}"
PORT="${T12_PORT:-18012}"
export T12_BASE_URL="${T12_BASE_URL:-http://127.0.0.1:$PORT}"

T12_PORT="$PORT" python3 "$HERE/mock_network.py" > /dev/null 2>&1 &
MOCK_PID=$!
trap 'kill $MOCK_PID 2>/dev/null' EXIT

for _ in $(seq 1 40); do
  curl --silent --output /dev/null --request POST "$T12_BASE_URL/_mock/reset" && break
  sleep 0.25
done

case "$CLIENT" in
  *.py) "$PY" "$CLIENT" ;;
  *)    bash "$CLIENT" ;;
esac
