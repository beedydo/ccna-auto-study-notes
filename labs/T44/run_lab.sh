#!/usr/bin/env bash
# Run the whole T44 lab offline (no router): parse, change window, learn/diff, AEtest job.
# Usage: bash labs/T44/run_lab.sh    (needs pyats[full] on PATH; see README.md)
set -euo pipefail
cd "$(dirname "$0")"

export PYATS_USERNAME="${PYATS_USERNAME:-lab}"     # the mock ignores them; the testbed needs them set
export PYATS_PASSWORD="${PYATS_PASSWORD:-lab}"
WORK="${TMPDIR:-/tmp}/t44-run"                      # all generated files go here, not into the repo
rm -rf "$WORK" && mkdir -p "$WORK"

echo "== 1. build the mock device from outputs/"
python make_mock.py

echo "== 2. offline parse (no device)"
python offline_parse.py outputs/show_version.txt "show version" | head -8

echo "== 3. change window: snapshot -> configure -> snapshot -> Diff"
CSR1_STATE=csr1_exec python change_window.py
mv snapshot_after.json "$WORK/"

echo "== 4. genie CLI: learn before/after, then diff the two folders"
CSR1_STATE=csr1_exec       genie learn routing --testbed-file testbed.yaml --devices csr1 --output "$WORK/before" > /dev/null
CSR1_STATE=csr1_exec_after genie learn routing --testbed-file testbed.yaml --devices csr1 --output "$WORK/after"  > /dev/null
genie diff "$WORK/before" "$WORK/after" --output "$WORK/diff"
cat "$WORK"/diff/diff_routing_iosxe_csr1_ops.txt; echo

echo "== 5. AEtest job, before (expect FAILED) and after (expect PASSED)"
for state in csr1_exec csr1_exec_after; do
  CSR1_STATE="$state" pyats run job job.py --testbed-file testbed.yaml \
    --no-mail --archive-dir "$WORK/archive" > "$WORK/job_$state.log" 2>&1 || true
  echo "-- $state"
  sed -n '/Task Result Details/,/Done!/p' "$WORK/job_$state.log" | sed 's/^.*EASYPY-INFO: //' | sed -n '3,15p'
done
rm -rf __pycache__
echo "== outputs in $WORK"
