#!/usr/bin/env bash
# T33 walkthrough: imperative vs declarative, idempotency, drift, push vs pull, mutable vs immutable.
# Usage: bash labs/T33/run_demo.sh
set -u
cd "$(dirname "$0")"
export T33_STATE_DIR="${T33_STATE_DIR:-${TMPDIR:-/tmp}/t33-state}"
run() { echo; echo "\$ python3 iac_demo.py $*"; python3 iac_demo.py "$@"; }

echo "=== 1. Imperative: the same steps, run twice ==="
run reset
run imperative
run imperative

echo; echo "=== 2. Declarative: plan, apply, apply again ==="
run reset
run plan
run apply
run apply

echo; echo "=== 3. Drift: a manual change on sw2 ==="
run drift sw2
run plan
run apply

echo; echo "=== 4. Pull: the agent on sw2 fixes its own drift ==="
run drift sw2
run agent sw2
run agent sw2

echo; echo "=== 5. Immutable: replace sw1 instead of patching it ==="
run replace sw1
run plan
