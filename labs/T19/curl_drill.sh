#!/usr/bin/env bash
# T19 curl drill: APIC aaaLogin + class query (fabricNode) + DN query, against the DevNet always-on APIC.
#   export APIC_HOST=sandboxapicdc.cisco.com APIC_USER=admin APIC_PASS='...'
#   bash labs/T19/curl_drill.sh
set -u
APIC="${APIC_HOST:-sandboxapicdc.cisco.com}"
USER="${APIC_USER:-admin}"
PASS="${APIC_PASS:-!v3G@!4@Y}"            # public DevNet sandbox default
JAR="$(mktemp)"                           # curl cookie jar: holds APIC-cookie after login
trap 'rm -f "$JAR"' EXIT

echo "== 1. aaaLogin: POST JSON body, save the Set-Cookie into the jar"
curl --silent --insecure --request POST \
  --cookie-jar "$JAR" \
  --header "Content-Type: application/json" \
  --data "{\"aaaUser\": {\"attributes\": {\"name\": \"$USER\", \"pwd\": \"$PASS\"}}}" \
  "https://$APIC/api/aaaLogin.json" \
  | python3 -c "import json, sys; a = json.load(sys.stdin)['imdata'][0]['aaaLogin']['attributes']; print('token', a['token'][:20] + '...', 'refresh', a['refreshTimeoutSeconds'])"
grep -o 'APIC-cookie' "$JAR"

echo; echo "== 2. Class query: all fabricNode objects (send the cookie back with --cookie)"
curl --silent --insecure --cookie "$JAR" \
  "https://$APIC/api/class/fabricNode.json" \
  | python3 -c "import json, sys; d = json.load(sys.stdin); print('totalCount', d['totalCount']); [print(' ', n['fabricNode']['attributes']['dn'], n['fabricNode']['attributes']['role']) for n in d['imdata']]"

echo; echo "== 3. Class query + filter (--get --data-urlencode builds the ?query string)"
curl --silent --insecure --cookie "$JAR" --get \
  --data-urlencode 'query-target-filter=eq(fabricNode.role,"leaf")' \
  "https://$APIC/api/class/fabricNode.json" \
  | python3 -c "import json, sys; d = json.load(sys.stdin); print('totalCount', d['totalCount'])"

echo; echo "== 4. DN query: one object by its distinguished name"
curl --silent --insecure --cookie "$JAR" \
  "https://$APIC/api/mo/uni/tn-common.json" \
  | python3 -c "import json, sys; d = json.load(sys.stdin); print(d['imdata'][0]['fvTenant']['attributes']['dn'])"

echo; echo "== 5. Same query with no cookie -> 403"
curl --silent --insecure --output /dev/null --write-out "HTTP %{http_code}\n" \
  "https://$APIC/api/class/fabricNode.json"
