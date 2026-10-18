#!/usr/bin/env bash
# Print every platform's first request side by side, then check the requests against the platform notes.
# No mock server and no network: requests are built, never sent.
# Usage:  bash labs/T48/run_lab.sh
#         bash labs/T48/run_lab.sh --only fmc,aci
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
export PYTHONWARNINGS=ignore PYTHONDONTWRITEBYTECODE=1

python3 "$HERE/auth_side_by_side.py" "$@"
echo
echo "== Drift check against bob/T12-T25 and T42"
python3 "$HERE/check_drift.py"
