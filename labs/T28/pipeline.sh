#!/usr/bin/env bash
# T28 local pipeline: the same stages as .gitlab-ci.yml, in order, stopping at the first failure.
# Usage: bash labs/T28/pipeline.sh                  # continuous DELIVERY: stops before prod
#        APPROVE_PROD=yes bash labs/T28/pipeline.sh # a human approved the prod gate
#        MODE=deployment bash labs/T28/pipeline.sh  # continuous DEPLOYMENT: no gate
set -euo pipefail                                  # any failing command ends the run (fail fast)

LAB="$(cd "$(dirname "$0")" && pwd)"
cd "$LAB"                                          # every path below is relative to labs/T28
OUT="${OUT:-${TMPDIR:-/tmp}/t28-pipeline}"         # runner workspace (never inside the repo)
MODE="${MODE:-delivery}"
INTENT="${INTENT:-intent/vlans.json}"              # the network source of truth
export PYTHONPATH="src" PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$OUT/pycache"  # keep the repo clean
rm -rf "$OUT" && mkdir -p "$OUT/dist"

stage() { echo; echo "=== stage $1: $2 ==="; }
trap 'echo; echo "PIPELINE FAILED in stage ${CURRENT:-?}: later stages did not run"' ERR

CURRENT=lint
stage 1 "lint / validate (source + network intent)"
python3 -m py_compile src/build_inventory.py src/netlib/*.py
echo "  OK syntax: build_inventory.py netlib/"
python3 ci/validate_intent.py "$INTENT"

CURRENT=test
stage 2 "unit test"
python3 -m unittest discover --start-directory tests 2>&1 | sed 's/^/  /'

CURRENT=build
stage 3 "build + package the artifact (once)"
python3 -m zipapp src --main "build_inventory:main" --output "$OUT/dist/netinv.pyz"
echo "  artifact: dist/netinv.pyz ($(wc -c < "$OUT/dist/netinv.pyz" | tr -d ' ') bytes, built once, reused below)"

CURRENT=deploy-dev
stage 4 "deploy dev (automatic)"
python3 ci/deploy.py --env dev --artifact "$OUT/dist/netinv.pyz" --out "$OUT"

CURRENT=deploy-staging
stage 5 "deploy staging (automatic)"
python3 ci/deploy.py --env staging --artifact "$OUT/dist/netinv.pyz" --out "$OUT"

CURRENT=deploy-prod
stage 6 "deploy prod"
if [[ "$MODE" == "deployment" || "${APPROVE_PROD:-no}" == "yes" ]]; then
  python3 ci/deploy.py --env prod --artifact "$OUT/dist/netinv.pyz" --out "$OUT"
  echo; echo "PIPELINE PASSED: released to prod (mode=$MODE)"
else
  echo "  WAITING: manual approval gate. Re-run with APPROVE_PROD=yes"
  echo; echo "PIPELINE PASSED up to the gate: artifact is releasable (mode=$MODE)"
fi
