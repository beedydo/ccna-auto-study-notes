#!/usr/bin/env bash
# Start the T08 mock API, wait until it answers, run a client, then stop the API.
# Usage:  bash labs/T08/run_lab.sh                      (runs consume_api.py)
#         bash labs/T08/run_lab.sh labs/T08/curl_drill.sh
#         bash labs/T08/run_lab.sh labs/T08/resume_paging.py
#         PYTHON=/path/to/venv/bin/python bash labs/T08/run_lab.sh   (if requests lives in a venv)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CLIENT="${1:-$HERE/consume_api.py}"

python3 "$HERE/mock_api.py" > /dev/null 2>&1 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null' EXIT

for _ in $(seq 1 40); do
  curl --silent --output /dev/null "http://127.0.0.1:8108/api/v1/auth/token" && break
  sleep 0.25
done

case "$CLIENT" in
  *.py) "${PYTHON:-python3}" "$CLIENT" ;;
  *)    bash "$CLIENT" ;;
esac
