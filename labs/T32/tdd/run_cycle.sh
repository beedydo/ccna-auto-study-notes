#!/usr/bin/env bash
# Run the SAME test file (../test_iflib.py) against each TDD snapshot of iflib.py.
# Usage (from the repo root): bash labs/T32/tdd/run_cycle.sh
cd "$(dirname "$0")" || exit 1
export PYTHONDONTWRITEBYTECODE=1
for step in 1-red 2-green; do
  echo "===== $step ====="
  PYTHONPATH="$step:.." python3 -m unittest -v test_iflib
done
echo "===== 3-refactor (labs/T32/iflib.py) ====="
PYTHONPATH=".." python3 -m unittest -v test_iflib
