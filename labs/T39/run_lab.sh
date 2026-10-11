#!/usr/bin/env bash
# Start the mock RESTCONF device, wait until it answers, run the probe, then stop the mock.
# Usage:  bash labs/T39/run_lab.sh
# Port:   T39_PORT (default 18039). Point at a real device instead: export RESTCONF_BASE=... and run planes_probe.py directly.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
PORT="${T39_PORT:-18039}"
export RESTCONF_BASE="${RESTCONF_BASE:-http://127.0.0.1:$PORT/restconf/data}"
PY="${PYTHON:-python3}"

T39_PORT="$PORT" "$PY" "$HERE/mock_device.py" > /dev/null 2>&1 &
MOCK_PID=$!
trap 'kill $MOCK_PID 2>/dev/null' EXIT

for _ in $(seq 1 40); do
  curl --silent --output /dev/null "http://127.0.0.1:$PORT/health" && break
  sleep 0.25
done

"$PY" "$HERE/planes_probe.py"
