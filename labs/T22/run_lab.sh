#!/usr/bin/env bash
# Run a T22 client against the offline mock SD-WAN Manager (default) or the live DevNet sandbox.
# Usage:  bash labs/T22/run_lab.sh                          (mock + sdwan_inventory.py)
#         bash labs/T22/run_lab.sh labs/T22/curl_drill.sh   (mock + curl drill)
#         bash labs/T22/run_lab.sh --live [client]          (sandbox-sdwan-2.cisco.com, no mock)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
LIVE=0
if [ "${1:-}" = "--live" ]; then LIVE=1; shift; fi
CLIENT="${1:-$HERE/sdwan_inventory.py}"
PY="${PYTHON:-python3}"

if [ "$LIVE" -eq 0 ]; then
  "$PY" "$HERE/mock_sdwan.py" > /dev/null 2>&1 &
  API_PID=$!
  trap 'kill $API_PID 2>/dev/null' EXIT
  for _ in $(seq 1 40); do
    curl --silent --output /dev/null "http://127.0.0.1:18022/welcome.html" && break
    sleep 0.25
  done
  export SDWAN_SCHEME="http" SDWAN_HOST="127.0.0.1" SDWAN_PORT="18022"
fi

case "$CLIENT" in
  *.py) "$PY" "$CLIENT" ;;
  *)    bash "$CLIENT" ;;
esac
