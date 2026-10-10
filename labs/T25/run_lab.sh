#!/usr/bin/env bash
# Start the T25 mock (NSO RESTCONF + CML API on :8125), run a client, then stop the mock.
# Usage:  bash labs/T25/run_lab.sh                       (runs pipeline.py)
#         bash labs/T25/run_lab.sh labs/T25/curl_drill.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CLIENT="${1:-$HERE/pipeline.py}"
PY="${PYTHON:-python3}"

"$PY" "$HERE/mock_nso_cml.py" > /dev/null 2>&1 &
MOCK_PID=$!
trap 'kill $MOCK_PID 2>/dev/null' EXIT

for _ in $(seq 1 40); do
  curl --silent --output /dev/null "http://127.0.0.1:8125/health" && break
  sleep 0.25
done

case "$CLIENT" in
  *.py) "$PY" "$CLIENT" ;;
  *)    bash "$CLIENT" ;;
esac
