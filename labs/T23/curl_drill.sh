#!/usr/bin/env bash
# T23 curl drill: the three auth styles side by side (FMC header token, ISE ERS Basic, XDR OAuth).
# Defaults hit the local mock:  bash labs/T23/run_lab.sh labs/T23/curl_drill.sh
# Real boxes: export FMC_URL=https://<fmc> FMC_USER=... FMC_PASS=... (and the ISE_/XDR_ vars)
set -u
FMC="${FMC_URL:-http://127.0.0.1:9401}"
ISE="${ISE_URL:-http://127.0.0.1:9060}"
XDR="${XDR_URL:-http://127.0.0.1:9404}"

echo "== 1. FMC: generatetoken = Basic auth in, tokens OUT in the response headers (204, no body)"
HDRS="$(curl --silent --insecure --request POST --user "${FMC_USER:-apiuser}:${FMC_PASS:-T23-fmc-pass}" \
  --dump-header - --output /dev/null "$FMC/api/fmc_platform/v1/auth/generatetoken")"
echo "$HDRS" | grep -iE '^(HTTP|X-auth-access-token|DOMAIN_UUID)' | sed 's/\r$//'
TOKEN="$(echo "$HDRS" | awk -F': ' 'tolower($1)=="x-auth-access-token" {print $2}' | tr -d '\r')"
DOMAIN="$(echo "$HDRS" | awk -F': ' '$1=="DOMAIN_UUID" {print $2}' | tr -d '\r')"

echo; echo "== 2. FMC: config call = token in the X-auth-access-token header, domain UUID in the path"
curl --silent --insecure --header "X-auth-access-token: $TOKEN" \
  "$FMC/api/fmc_config/v1/domain/$DOMAIN/object/networks?offset=0&limit=2" \
  | python3 -c "import json, sys; d = json.load(sys.stdin); print([o['name'] for o in d['items']], d['paging'])"

echo; echo "== 3. ISE ERS: Basic auth on EVERY call + Accept: application/json"
curl --silent --insecure --user "${ISE_USER:-ersadmin}:${ISE_PASS:-T23-ise-pass}" \
  --header "Accept: application/json" "$ISE/ers/config/networkdevice" \
  | python3 -c "import json, sys; r = json.load(sys.stdin)['SearchResult']; print('total', r['total'], [x['name'] for x in r['resources']])"

echo; echo "== 4. XDR: OAuth client credentials (form body), then Bearer"
XTOKEN="$(curl --silent --request POST --user "${XDR_CLIENT_ID:-client-t23-xdr}:${XDR_CLIENT_SECRET:-T23-xdr-secret}" \
  --header "Accept: application/json" --header "Content-Type: application/x-www-form-urlencoded" \
  --data "grant_type=client_credentials" "$XDR/iroh/oauth2/token" \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['access_token'])")"
curl --silent --request POST --header "Authorization: Bearer $XTOKEN" \
  --header "Content-Type: application/json" --header "Accept: application/json" \
  --data '{"content": "beacon to 203.0.113.66 and update-checker.example"}' \
  "$XDR/iroh/iroh-inspect/inspect"; echo

echo; echo "== 5. Same FMC call with no token -> 401"
curl --silent --insecure --output /dev/null --write-out "HTTP %{http_code}\n" \
  "$FMC/api/fmc_config/v1/domain/$DOMAIN/object/networks"
