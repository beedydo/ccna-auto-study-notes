#!/usr/bin/env bash
# Start the T43 platform (8143) and receiver (8144), run a driver, print the servers' shared log, stop both.
# Usage:  bash labs/T43/run_lab.sh                         (demo.py, then poll_client.py)
#         bash labs/T43/run_lab.sh labs/T43/curl_drill.sh
# Break-it knobs (env vars): NO_RECEIVER=1, WEBHOOK_SECRET=..., FAIL_FIRST=N, INLINE_WORK_SECONDS=N,
#                            SETTLE_SECONDS=N (how long demo.py waits for deliveries)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
LOGS="$(mktemp -d "${TMPDIR:-/tmp}/t43-logs.XXXXXX")"

python3 -u "$HERE/platform.py" >> "$LOGS/servers.log" 2>&1 &
PIDS="$!"
if [ "${NO_RECEIVER:-0}" != "1" ]; then
  python3 -u "$HERE/receiver.py" >> "$LOGS/servers.log" 2>&1 &
  PIDS="$PIDS $!"
else
  echo "[receiver] NOT STARTED (NO_RECEIVER=1)" >> "$LOGS/servers.log"
fi
trap 'kill $PIDS 2>/dev/null; rm -rf "$LOGS"' EXIT

for _ in $(seq 1 40); do
  curl --silent --output /dev/null "http://127.0.0.1:8143/v1/webhooks" && break
  sleep 0.25
done

if [ $# -gt 0 ]; then
  case "$1" in *.py) python3 "$1" ;; *) bash "$1" ;; esac
else
  python3 "$HERE/demo.py"
  echo; echo "== 4. Contrast: polling for the same kind of event =="
  python3 "$HERE/poll_client.py"
fi
sleep 0.5
echo; echo "---------- server log (platform + receiver, in time order) ----------"
cat "$LOGS/servers.log"
