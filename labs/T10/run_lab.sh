#!/usr/bin/env bash
# Start the T10 mock auth API, load the fake credentials, run a client, show the
# server access log lines that leaked a secret, then stop the API.
# Usage:  bash labs/T10/run_lab.sh                         (runs auth_tour.py)
#         bash labs/T10/run_lab.sh labs/T10/curl_drill.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CLIENT="${1:-$HERE/auth_tour.py}"
LOG="$(mktemp)"

python3 "$HERE/mock_auth_api.py" > "$LOG" 2>&1 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null; rm -f "$LOG"' EXIT

for _ in $(seq 1 40); do
  curl --silent --output /dev/null "http://127.0.0.1:8110/" && break
  sleep 0.25
done

set -a && source "$HERE/mock-creds.env" && set +a

case "$CLIENT" in
  *.py) python3 "$CLIENT" ;;
  *)    bash "$CLIENT" ;;
esac

echo
echo "== Server access log: lines that contain a secret =="
grep "api_key=" "$LOG" || echo "(none)"
