#!/usr/bin/env bash
# Make a throwaway self-signed cert, start the mock RESTCONF device on https://127.0.0.1:9443,
# run a client, then stop the mock.
# Usage:  bash labs/T16/run_lab.sh                         (runs restconf_client.py)
#         bash labs/T16/run_lab.sh labs/T16/curl_drill.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CLIENT="${1:-$HERE/restconf_client.py}"
TMP="$(mktemp -d)"

openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj "/CN=localhost" \
  -keyout "$TMP/key.pem" -out "$TMP/cert.pem" > /dev/null 2>&1

MOCK_CERT="$TMP/cert.pem" MOCK_KEY="$TMP/key.pem" python3 "$HERE/mock_restconf.py" > /dev/null 2>&1 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null; rm -rf "$TMP"' EXIT

for _ in $(seq 1 40); do
  curl --silent --insecure --output /dev/null "https://127.0.0.1:9443/.well-known/host-meta" && break
  sleep 0.25
done

case "$CLIENT" in
  *.py) python3 "$CLIENT" ;;
  *)    bash "$CLIENT" ;;
esac
