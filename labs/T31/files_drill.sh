#!/usr/bin/env bash
# T31 navigation / files / env drill: run with  bash files_drill.sh
work="$(mktemp -d "${TMPDIR:-/tmp}/t31files.XXXXXX")" || exit 1
cd "$work" || exit 1
work="$(pwd)"                        # normalise (TMPDIR may end in /)

echo "1. navigation"
mkdir -p backups/2026/oct            # -p: create parents, no error if they exist
cd backups/2026/oct && pwd | sed "s|$work|\$work|"
cd ../..  && pwd | sed "s|$work|\$work|"
cd -      >/dev/null && pwd | sed "s|$work|\$work|"   # cd - = previous directory
cd ~ && [ "$PWD" == "$HOME" ] && echo "cd ~ -> \$HOME"
cd "$work" || exit 1

echo "2. files"
printf 'hostname csr1\nntp server 10.0.0.1\nlogging host 10.0.0.9\n' > csr1.cfg
touch .hidden
ls | tr '\n' ' '; echo
ls -a | tr '\n' ' '; echo
cp csr1.cfg backups/2026/oct/         # copy a file
cp -r backups backups-copy            # copy a directory needs -r
mv csr1.cfg csr1-running.cfg          # mv = rename here
rmdir backups-copy 2>&1 | sed "s|$work|\$work|"   # rmdir only removes EMPTY dirs
rm -r backups-copy && echo "rm -r removed backups-copy"
find . -name "*.cfg" | sort
grep -r -i "NTP" . | sort
grep -v ntp csr1-running.cfg
head -n 1 csr1-running.cfg; tail -n 1 csr1-running.cfg

echo "3. PATH"
mkdir bin; printf '#!/usr/bin/env bash\necho "hello from mytool"\n' > bin/mytool; chmod +x bin/mytool
mytool 2>/dev/null || echo "mytool: not found (rc=$?)"
PATH="$work/bin:$PATH"; mytool
command -v mytool | sed "s|$work|\$work|"

echo "4. source vs run"
echo 'SITE=lab' > vars.sh
bash vars.sh; echo "after bash vars.sh: SITE=[$SITE]"
source vars.sh; echo "after source vars.sh: SITE=[$SITE]"
unset SITE; echo "after unset: SITE=[$SITE]"
