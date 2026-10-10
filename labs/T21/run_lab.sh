#!/usr/bin/env bash
# Make a throwaway self-signed cert, start the mock CUCM on https://127.0.0.1:${CUCM_PORT:-8443},
# wait until it answers, run a client, then stop the mock.
# Usage:  bash labs/T21/run_lab.sh                      (runs cucm_lab.py)
#         bash labs/T21/run_lab.sh labs/T21/curl_drill.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CLIENT="${1:-$HERE/cucm_lab.py}"
PYTHON="${PYTHON:-python3}"
export CUCM_PORT="${CUCM_PORT:-8443}"
TMP="$(mktemp -d)"

openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj "/CN=cucm-pub.lab.local" \
  -keyout "$TMP/key.pem" -out "$TMP/cert.pem" > /dev/null 2>&1

"$PYTHON" "$HERE/mock_cucm.py" "$TMP/cert.pem" "$TMP/key.pem" > /dev/null 2>&1 &
MOCK_PID=$!
trap 'kill $MOCK_PID 2>/dev/null; rm -rf "$TMP"' EXIT

for _ in $(seq 1 40); do
  curl --silent --insecure --output /dev/null "https://127.0.0.1:$CUCM_PORT/cucm-uds/version" && break
  sleep 0.25
done
kill -0 $MOCK_PID 2>/dev/null || { echo "mock CUCM did not start (port $CUCM_PORT in use? try CUCM_PORT=28443)"; exit 1; }

case "$CLIENT" in
  *.py) "$PYTHON" "$CLIENT" ;;
  *)    bash "$CLIENT" ;;
esac
