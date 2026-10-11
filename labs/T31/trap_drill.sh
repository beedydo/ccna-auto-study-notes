#!/usr/bin/env bash
# T31 trap drill: run with  bash trap_drill.sh  (works in a throwaway temp dir)
cd "$(mktemp -d "${TMPDIR:-/tmp}/t31drill.XXXXXX")" || exit 1

echo "1. quotes"
host=csr1
echo "double: $host"
echo 'single: $host'

echo "2. \$@ vs \$*"
show() { printf '[%s] ' "$@"; echo; }
args() { show "$@"; show "$*"; show $@; }
args "site a" b

echo "3. > vs >>"
echo one > f.txt; echo two > f.txt; cat f.txt
echo one > g.txt; echo two >> g.txt; cat g.txt

echo "4. 2>&1 order"
ls /nope > out1.txt 2>&1; echo "out1 lines: $(wc -l < out1.txt | tr -d ' ')"
ls /nope 2>&1 > out2.txt; echo "out2 lines: $(wc -l < out2.txt | tr -d ' ')"

echo "5. \$? is overwritten"
grep -q zzz f.txt; echo "grep rc=$?"; echo "now rc=$?"

echo "6. [ ] vs [[ ]]"
name="core sw"
[ $name == "core sw" ] 2>/dev/null || echo "[ ] unquoted: error (rc=$?)"
[ "$name" == "core sw" ] && echo '[ "$name" == "core sw" ] true'
[[ $name == core* ]] && echo '[[ $name == core* ]] true (glob)'
[ 10 -gt 9 ] && echo '[ 10 -gt 9 ] true (numeric)'
[[ 10 > 9 ]] || echo '[[ 10 > 9 ]] false (string compare)'

echo "7. shell var vs export"
LOCALVAR=a; export EXPVAR=b
bash -c 'echo "child: LOCALVAR=[$LOCALVAR] EXPVAR=[$EXPVAR]"'
ONEOFF=c bash -c 'echo "child: ONEOFF=[$ONEOFF]"'; echo "parent: ONEOFF=[$ONEOFF]"

echo "8. chmod"
touch s.sh; chmod 755 s.sh; ls -l s.sh | cut -c1-10
chmod u=rw,go=r s.sh; ls -l s.sh | cut -c1-10
chmod +x s.sh; ls -l s.sh | cut -c1-10

echo "9. \$(...) and arithmetic"
count=$(printf 'a\nb\nc\n' | wc -l | tr -d ' '); echo "count=$count next=$((count + 1))"
x=5+1; echo "x=5+1 -> $x"
