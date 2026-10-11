#!/usr/bin/env bash
# T46 lab: play the CI half of a code review on "PR #42".
# 1. Builds a throwaway repo with labs/T46/base/ on main.
# 2. Creates the PR branch and applies pr-42.diff (the change under review).
# 3. Runs the automated checks a CI job would run, then the program itself.
# Usage:  bash labs/T46/review_pr.sh            # review PR #42 as submitted
#         FIX=yes bash labs/T46/review_pr.sh    # also apply pr-42-fix.diff (the author's fix-up commit)
# Linters are optional: put ruff/flake8/pylint/bandit on PATH (e.g. activate a venv) to see their output.
set -u
LAB="$(cd "$(dirname "$0")" && pwd)"
WORK="${TMPDIR:-/tmp}/t46-review"
PY="${PYTHON:-python3}"
export PYLINTHOME="$WORK/.pylint" RUFF_CACHE_DIR="$WORK/.ruff"

rm -rf "$WORK" && mkdir -p "$WORK" && cd "$WORK" || exit 1
git init --quiet --initial-branch=main
git config user.name "Beedy"
git config user.email "beedy@example.com"
git config commit.gpgsign false
cp -R "$LAB/base/." .
git add . && git commit --quiet --message "link_report: list down interfaces"

git switch --quiet --create feature/live-errors
git apply "$LAB/pr-42.diff" && git commit --quiet --all --message "link_report: live mode + error check"
if [ "${FIX:-no}" = "yes" ]; then
  git apply "$LAB/pr-42-fix.diff" && git commit --quiet --all --message "Address review: env creds, TLS, timeout, fix loop, tests"
fi

echo "== git log --oneline main..HEAD"; git log --oneline main..HEAD | sed 's/^[0-9a-f]* //'
echo "== git diff --stat main...HEAD"; git diff --stat main...HEAD

run() {                                   # run one check; never stop the script, report the exit code
  local name="$1"; shift
  echo "== $name"
  "$@"; echo "-- exit $?"
}
run "py_compile (syntax only)" "$PY" -m py_compile link_report.py test_link_report.py
run "unittest" "$PY" -m unittest 2>&1
for tool in ruff flake8 pylint bandit; do
  if ! command -v "$tool" >/dev/null 2>&1; then echo "== $tool: not installed, skipped"; continue; fi
  case "$tool" in
    ruff)   run "ruff check (E,F,B,S rules)" ruff check --no-cache --select E,F,B,S --output-format concise link_report.py ;;
    flake8) run "flake8" flake8 --max-line-length 100 link_report.py ;;
    pylint) run "pylint" pylint --score=n --disable=C0114,C0116,C0301 link_report.py ;;
    bandit) run "bandit (security)" bandit --quiet --format custom --msg-template "{line}: {test_id} [{severity}] {msg}" link_report.py ;;
  esac
done
run "program on the saved reply" "$PY" link_report.py fixtures/interfaces.json
