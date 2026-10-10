#!/usr/bin/env bash
# T45 spot-the-bug drill: plant one classic bug at a time in a COPY of device_audit.py,
# run it against the mock, and show the symptom. The original file is never changed.
# Run via the lab wrapper (it starts the mock):  bash labs/T45/run_lab.sh labs/T45/break_it.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-python3}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# plant <n> <title> <old text> <new text> [extra env]
plant() {
  local n="$1" title="$2" old="$3" new="$4" extra="${5:-}"
  "$PY" - "$HERE/device_audit.py" "$WORK/bug$n.py" "$old" "$new" <<'EOF'
import sys
src, dst, old, new = sys.argv[1:5]
text = open(src).read()
assert old in text, f"pattern not found: {old!r}"
open(dst, "w").write(text.replace(old, new, 1))
EOF
  echo "== Bug $n: $title"
  env $extra "$PY" "$WORK/bug$n.py" 2>&1 \
    | grep -E '^(Found|Resyncing|All devices|Resync finished|[A-Za-z.]*Error)' \
    | sed 's/^/   /'
  echo
}

plant 1 "wrong HTTP method (POST instead of PUT on /sync)" \
  'resp = requests.put(url' 'resp = requests.post(url'

plant 2 "missing auth header (X-Auth-Token line deleted)" \
  '"X-Auth-Token": token,' ''

plant 3 "missing content header (Content-Type line deleted)" \
  '"Content-Type": "application/json",' ''

plant 4 "wrong JSON key path (token instead of Token)" \
  'resp.json()["Token"]' 'resp.json()["token"]'

echo "== Bug 5a: wrong password WITH raise_for_status (the correct script)"
DNAC_PASS=wrong "$PY" "$HERE/device_audit.py" 2>&1 | grep -E '^requests\.exceptions' | sed 's/^/   /'
echo
plant 5b "wrong password, raise_for_status() deleted from get_token()" \
  'resp.raise_for_status()                       # 401 stops here, with a clear error' \
  '# raise_for_status() deleted' DNAC_PASS=wrong

plant 6 "no pagination (loop returns after the first page)" \
  'if len(page) < PAGE_SIZE:' 'if True:'
