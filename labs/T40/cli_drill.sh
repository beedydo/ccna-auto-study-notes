#!/usr/bin/env bash
# T40 CLI drill: the exam's diagnostic tools against the fake network from lab_env.py.
# Run with the lab up:  bash labs/T40/run_lab.sh labs/T40/cli_drill.sh
set -u
H=127.0.0.1
P="${T40_BASE_PORT:-18040}"
CA="${T40_CA:-/tmp/t40-certs/corp-ca.pem}"
export no_proxy='' NO_PROXY=''             # use only the proxies we name on the command line
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy

step() { printf '\n$ %s\n' "$*"; "$@" 2>&1; }

echo "== 0. Name and path: dig / nslookup / ping with DF bit =="
step dig +short localhost
step nslookup api.corp.invalid
step ping -c 2 -M do -s 1472 $H

echo; echo "== 1. Is the port open? (nc = TCP handshake only) =="
step nc -zv -w 2 $H $P
step nc -zv -w 2 $H $((P + 1))
step nc -zv -w 2 $H $((P + 2))

echo; echo "== 2. curl -v: where does it stop? =="
step curl -sSv --max-time 3 http://$H:$((P + 1))/health
step curl -sSv --connect-timeout 2 http://$H:$((P + 2))/health

echo; echo "== 3. Proxy: 407 then --proxy-user =="
step curl --silent --include --proxy http://$H:$((P + 3)) http://$H:$P/whoami
step curl --silent --proxy http://$H:$((P + 3)) --proxy-user labuser:labpass http://$H:$P/whoami

echo; echo "== 4. HTTPS via proxy: TLS inspection CA =="
step curl --silent --show-error --proxy http://labuser:labpass@$H:$((P + 3)) https://$H:$((P + 4))/health
step curl --silent --show-error --proxy http://labuser:labpass@$H:$((P + 3)) --cacert "$CA" https://$H:$((P + 4))/health

echo; echo "== 5. Who is listening locally? =="
printf '\n$ ss -ltn | grep 1804\n'
if command -v ss > /dev/null; then ss -ltn | grep 1804; else echo "ss not installed (Docker lab: apt-get install iproute2)"; fi
