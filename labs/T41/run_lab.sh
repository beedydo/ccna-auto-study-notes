#!/usr/bin/env bash
# Run the T41 reference program (it starts the whole stack in-process), or the dig/curl drill.
# Usage:  bash labs/T41/run_lab.sh                  (walkthrough.py)
#         bash labs/T41/run_lab.sh drill            (dig_curl_drill.sh)
# Port:   T41_PORT (default 18041). Needs Linux loopback (127.0.41.x / 127.0.42.x); the lab container is fine.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-python3}"
case "${1:-walkthrough}" in
  drill) bash "$HERE/dig_curl_drill.sh" ;;
  *)     "$PY" -B "$HERE/walkthrough.py" ;;
esac
