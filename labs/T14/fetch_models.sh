#!/usr/bin/env bash
# Download the pinned YANG modules used by the T14 lab into labs/T14/models/.
#   models/ietf : IETF standard models (RFC 8343 ietf-interfaces, RFC 8344 ietf-ip, + types)
#   models/xe   : Cisco native model Cisco-IOS-XE-native for IOS XE 17.15.1, + the modules it needs
#   models/oc   : OpenConfig openconfig-interfaces, + the modules it needs
# Source repos: github.com/YangModels/yang and github.com/openconfig/public
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
IETF=https://raw.githubusercontent.com/YangModels/yang/main/standard/ietf/RFC
XE=https://raw.githubusercontent.com/YangModels/yang/main/vendor/cisco/xe/17151
OC=https://raw.githubusercontent.com/openconfig/public/v5.10.0/release/models

get() {  # get <dir> <url>: download once
  local dir="$HERE/models/$1" file="${2##*/}"
  mkdir -p "$dir"
  [ -s "$dir/$file" ] || curl --silent --show-error --fail --max-time 30 --output "$dir/$file" "$2"
}

for m in ietf-interfaces@2018-02-20 ietf-ip@2018-02-22 iana-if-type@2014-05-08 \
         ietf-inet-types@2013-07-15 ietf-yang-types@2013-07-15; do
  get ietf "$IETF/$m.yang"
done

for m in Cisco-IOS-XE-native Cisco-IOS-XE-features Cisco-IOS-XE-hsrp Cisco-IOS-XE-interface-common \
         Cisco-IOS-XE-interfaces Cisco-IOS-XE-ipv6 Cisco-IOS-XE-ip Cisco-IOS-XE-license Cisco-IOS-XE-line \
         Cisco-IOS-XE-location Cisco-IOS-XE-logging Cisco-IOS-XE-parser Cisco-IOS-XE-transceiver-monitor \
         Cisco-IOS-XE-types cisco-semver; do
  get xe "$XE/$m.yang"
done

get oc "$OC/interfaces/openconfig-interfaces.yang"
get oc "$OC/openconfig-extensions.yang"
get oc "$OC/types/openconfig-types.yang"
get oc "$OC/types/openconfig-yang-types.yang"
get oc "$OC/optical-transport/openconfig-transport-types.yang"

echo "models ready: $(find "$HERE/models" -name '*.yang' | wc -l) files in $HERE/models"
