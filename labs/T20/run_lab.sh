#!/usr/bin/env bash
# Start the mock Catalyst Center, wait until it answers, run a client against it, then stop it.
# Usage:  bash labs/T20/run_lab.sh                         (runs catc_inventory.py)
#         bash labs/T20/run_lab.sh labs/T20/sdk_inventory.py
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CLIENT="${1:-$HERE/catc_inventory.py}"

python3 "$HERE/mock_catc.py" > /dev/null 2>&1 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null' EXIT

for _ in $(seq 1 40); do
  curl --silent --output /dev/null "http://127.0.0.1:8443/dna/intent/api/v1/network-device" && break
  sleep 0.25
done

export DNAC_URL="http://127.0.0.1:8443" DNAC_USER="devnetuser" DNAC_PASS="Cisco123!"
case "$CLIENT" in
  *.py) python3 "$CLIENT" ;;
  *)    bash "$CLIENT" ;;
esac
