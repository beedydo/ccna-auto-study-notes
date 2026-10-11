#!/usr/bin/env bash
# Start the mock Catalyst Center, wait until it answers, run a client, then stop the mock.
# Usage:  bash labs/T45/run_lab.sh                         (runs device_audit.py)
#         bash labs/T45/run_lab.sh labs/T45/break_it.sh    (runs the bug drill)
# PYTHON=/path/to/python overrides the interpreter (needs the requests package).
# T45_TRACE=1 prints, at the end, every call the mock received, in order.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CLIENT="${1:-$HERE/device_audit.py}"
PY="${PYTHON:-python3}"
export T45_PORT="${T45_PORT:-18045}"
export DNAC_URL="${DNAC_URL:-http://127.0.0.1:$T45_PORT}"

CALL_LOG="$(mktemp)"
"$PY" "$HERE/mock_catalyst_center.py" >> "$CALL_LOG" 2>&1 &
MOCK_PID=$!
trap 'kill $MOCK_PID 2>/dev/null; rm -f "$CALL_LOG"' EXIT

for _ in $(seq 1 40); do
  curl --silent --output /dev/null "http://127.0.0.1:$T45_PORT/dna/intent/api/v1/network-device" && break
  sleep 0.25
done
: > "$CALL_LOG"                     # drop the readiness probe from the log

case "$CLIENT" in
  *.py) "$PY" "$CLIENT" ;;
  *)    PYTHON="$PY" bash "$CLIENT" ;;
esac

if [ "${T45_TRACE:-0}" = "1" ]; then
  echo; echo "== Calls the mock received, in order =="
  cat "$CALL_LOG"
fi
