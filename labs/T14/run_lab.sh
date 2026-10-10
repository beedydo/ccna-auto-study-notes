#!/usr/bin/env bash
# T14 lab: download the models, print pyang trees, then run the reference program.
# Usage:  bash labs/T14/run_lab.sh          (needs python3 + pyang; the Docker lab image has both)
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
M="$HERE/models"
bash "$HERE/fetch_models.sh"

echo; echo "== pyang -f tree: teaching module =="
pyang -p "$M/ietf" -f tree "$HERE/campus-vlans.yang"

echo; echo "== pyang -f tree: IETF ietf-interfaces (RFC 8343), depth 3 =="
pyang -p "$M/ietf" -f tree --tree-depth 3 "$M/ietf/ietf-interfaces@2018-02-20.yang"

echo; echo "== pyang -f tree: ietf-ip augments ietf-interfaces (first 20 lines: ipv4) =="
pyang -p "$M/ietf" -f tree "$M/ietf/ietf-ip@2018-02-22.yang" | head -20

echo; echo "== pyang -f tree: Cisco native, one interface list, depth 4 =="
pyang -p "$M/ietf:$M/xe" -f tree --tree-path /native/interface/GigabitEthernet --tree-depth 4 \
  "$M/xe/Cisco-IOS-XE-native.yang" 2>/dev/null | head -11

echo; echo "== pyang -f tree: OpenConfig interfaces, depth 4 =="
pyang -p "$M/ietf:$M/oc" -f tree --tree-depth 4 "$M/oc/openconfig-interfaces.yang" | head -20

echo; echo "== yang_explorer.py =="
python3 "$HERE/yang_explorer.py"
