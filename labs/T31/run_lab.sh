#!/usr/bin/env bash
# Start a mock "device API" on 127.0.0.1:8131 (serves mock/*.json), run device_report.sh, stop the API.
# Usage:  bash labs/T31/run_lab.sh                 (uses labs/T31/devices.csv)
#         bash labs/T31/run_lab.sh my.csv other.csv
#         SCRIPT=/path/to/edited_copy.sh bash labs/T31/run_lab.sh   (run a "break it" copy)
# Needs: bash, python3 (only for the mock server), curl, awk.
HERE="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="${SCRIPT:-$HERE/device_report.sh}"
[ $# -eq 0 ] && set -- "$HERE/devices.csv"

python3 -m http.server 8131 --bind 127.0.0.1 --directory "$HERE/mock" > /dev/null 2>&1 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null' EXIT

for _ in $(seq 1 40); do
    curl --silent --output /dev/null "http://127.0.0.1:8131/csr1.json" && break
    sleep 0.25
done

# No cd here: relative inventory paths stay valid. The report goes to a temp dir instead.
REPORT="${REPORT:-$(mktemp -d "${TMPDIR:-/tmp}/t31lab.XXXXXX")/report.csv}" "$SCRIPT" "$@"
rc=$?
echo "$(basename "$SCRIPT") exit status: $rc"
exit "$rc"
