#!/usr/bin/env bash
# T17 curl drill: NX-API CLI, NX-API REST and IOS XE RESTCONF with plain curl.
# Run via:  bash labs/T17/run_lab.sh labs/T17/curl_drill.sh   (starts the mock devices first)
# Real switch: export NXOS_URL=https://<switch> NXOS_USER=... NXOS_PASS=...
set -u
NXOS="${NXOS_URL:-http://127.0.0.1:18443}"
IOSXE="${IOSXE_URL:-http://127.0.0.1:18444}"
NX_USER="${NXOS_USER:-admin}"; NX_PASS="${NXOS_PASS:-Admin_1234!}"
XE_USER="${IOSXE_USER:-admin}"; XE_PASS="${IOSXE_PASS:-Admin_1234!}"
JAR="$(mktemp)"; trap 'rm -f "$JAR"' EXIT

echo "== 1. NX-API CLI, ins_api JSON: POST /ins with Basic auth =="
curl --silent --insecure --user "$NX_USER:$NX_PASS" \
  --header "Content-Type: application/json" \
  --data '{"ins_api": {"version": "1.0", "type": "cli_show", "chunk": "0", "sid": "1", "input": "show switchname", "output_format": "json"}}' \
  "$NXOS/ins"
echo

echo "== 2. NX-API CLI, JSON-RPC: Content-Type application/json-rpc =="
curl --silent --insecure --user "$NX_USER:$NX_PASS" \
  --header "Content-Type: application/json-rpc" \
  --data '[{"jsonrpc": "2.0", "method": "cli_ascii", "params": {"cmd": "show switchname", "version": 1}, "id": 1}]' \
  "$NXOS/ins"
echo

echo "== 3. NX-API CLI with GET: wrong method =="
curl --silent --insecure --user "$NX_USER:$NX_PASS" --output /dev/null \
  --write-out "HTTP %{http_code}\n" "$NXOS/ins"

echo "== 4. NX-API REST: aaaLogin, cookie saved to a jar =="
curl --silent --insecure --cookie-jar "$JAR" \
  --header "Content-Type: application/json" \
  --data "{\"aaaUser\": {\"attributes\": {\"name\": \"$NX_USER\", \"pwd\": \"$NX_PASS\"}}}" \
  --output /dev/null --write-out "HTTP %{http_code}\n" \
  "$NXOS/api/aaaLogin.json"
grep --only-matching "APIC-cookie" "$JAR"

echo "== 5. NX-API REST: GET one MO by DN (cookie sent back) =="
curl --silent --insecure --globoff --cookie "$JAR" \
  "$NXOS/api/mo/sys/intf/phys-[eth1/1].json"
echo

echo "== 6. NX-API REST: GET without the cookie =="
curl --silent --insecure --globoff --write-out "\nHTTP %{http_code}\n" \
  "$NXOS/api/class/l1PhysIf.json"

echo "== 7. IOS XE RESTCONF: GET with Basic auth and the YANG media type =="
curl --silent --insecure --user "$XE_USER:$XE_PASS" \
  --header "Accept: application/yang-data+json" \
  "$IOSXE/restconf/data/ietf-interfaces:interfaces/interface=GigabitEthernet1"
echo
