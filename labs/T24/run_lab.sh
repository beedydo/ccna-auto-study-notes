#!/usr/bin/env bash
# Make a throwaway API key, start both mocks, run a client, then stop the mocks.
# Usage:  bash labs/T24/run_lab.sh                          (runs compute_inventory.py)
#         bash labs/T24/run_lab.sh labs/T24/curl_drill.sh
#         T24_KEY_TYPE=rsa bash labs/T24/run_lab.sh         (v2-style RSA key instead of EC)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CLIENT="${1:-$HERE/compute_inventory.py}"
PY="${PYTHON:-python3}"
export INTERSIGHT_KEY_ID="5f7b3c9e7564612d33a1b2c3/5f7b3c9e7564612d33a1b2c4/6702a1b07564612d30c0ffee"
export INTERSIGHT_KEY_FILE="/tmp/t24-lab/SecretKey.txt"

"$PY" "$HERE/make_mock_key.py" ${T24_KEY_TYPE:-} > /dev/null
"$PY" "$HERE/mock_ucsm.py" > /dev/null 2>&1 &
UCSM_PID=$!
"$PY" "$HERE/mock_intersight.py" > /dev/null 2>&1 &
IS_PID=$!
trap 'kill $UCSM_PID $IS_PID 2>/dev/null' EXIT

for _ in $(seq 1 40); do
  curl --silent --output /dev/null --data '<aaaLogout inCookie=""/>' "http://127.0.0.1:8124/nuova" \
    && curl --silent --output /dev/null "http://127.0.0.1:18024/api/v1/compute/Blades" && break
  sleep 0.25
done

case "$CLIENT" in
  *.py) "$PY" "$CLIENT" ;;
  *)    bash "$CLIENT" ;;
esac
