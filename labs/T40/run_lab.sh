#!/usr/bin/env bash
# Start the T40 fake network, wait until it answers, run a client, then stop it.
# Usage:  bash labs/T40/run_lab.sh                      (runs conn_doctor.py)
#         bash labs/T40/run_lab.sh labs/T40/cli_drill.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CLIENT="${1:-$HERE/conn_doctor.py}"
PORT="${T40_BASE_PORT:-18040}"
PY="${PYTHON:-python3}"
export T40_CERT_DIR="${T40_CERT_DIR:-/tmp/t40-certs}"
export T40_CA="$T40_CERT_DIR/corp-ca.pem"

"$PY" "$HERE/lab_env.py" > /dev/null 2>&1 &
ENV_PID=$!
trap 'kill $ENV_PID 2>/dev/null' EXIT

for _ in $(seq 1 40); do
  # TLS-APP starts last (after cert generation), so wait for it
  curl --silent --insecure --noproxy '*' --output /dev/null "https://127.0.0.1:$((PORT + 4))/health" && break
  sleep 0.25
done

case "$CLIENT" in
  *.py) "$PY" "$CLIENT" ;;
  *)    bash "$CLIENT" ;;
esac
