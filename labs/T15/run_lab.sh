#!/usr/bin/env bash
# Start the mock NETCONF device, wait until port 8830 answers, run a client, then stop the device.
# Usage:  bash labs/T15/run_lab.sh                          (runs netconf_walkthrough.py)
#         bash labs/T15/run_lab.sh labs/T15/raw_framing.py
# Needs ncclient (pip install ncclient); set PYTHON=/path/to/venv/bin/python to pick an interpreter.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CLIENT="${1:-$HERE/netconf_walkthrough.py}"
PY="${PYTHON:-python3}"

"$PY" "$HERE/mock_netconf.py" 2> /dev/null &
DEVICE_PID=$!
trap 'kill $DEVICE_PID 2>/dev/null' EXIT

for _ in $(seq 1 40); do
  "$PY" -c "import socket; socket.create_connection(('127.0.0.1', 8830), 1)" 2> /dev/null && break
  sleep 0.25
done

case "$CLIENT" in
  *.py) "$PY" "$CLIENT" ;;
  *)    bash "$CLIENT" ;;
esac
