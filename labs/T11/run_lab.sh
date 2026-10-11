#!/usr/bin/env bash
# Make a throwaway self-signed cert, start the HTTPS mock API on :8111, run a client, then stop the API.
# Usage:  bash labs/T11/run_lab.sh                         (runs inventory_client.py)
#         bash labs/T11/run_lab.sh labs/T11/some_other.py
# Needs: python3 with requests installed, and openssl.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CLIENT="${1:-$HERE/inventory_client.py}"
PYTHON="${PYTHON:-python3}"

CERT_DIR="$(mktemp -d)"
openssl req -x509 -newkey rsa:2048 -nodes -days 1 \
  -keyout "$CERT_DIR/key.pem" -out "$CERT_DIR/cert.pem" \
  -subj "/CN=127.0.0.1" -addext "subjectAltName=IP:127.0.0.1" > /dev/null 2>&1

"$PYTHON" "$HERE/mock_api.py" "$CERT_DIR/cert.pem" "$CERT_DIR/key.pem" > /dev/null 2>&1 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null; rm -rf "$CERT_DIR"' EXIT

for _ in $(seq 1 40); do
  curl --silent --insecure --output /dev/null "https://127.0.0.1:8111/api/v1/health" && break
  sleep 0.25
done

# REQUESTS_CA_BUNDLE / CURL_CA_BUNDLE (set by some corporate proxies) would override session.verify
unset REQUESTS_CA_BUNDLE CURL_CA_BUNDLE
API_CA_CERT="$CERT_DIR/cert.pem" "$PYTHON" "$CLIENT"
