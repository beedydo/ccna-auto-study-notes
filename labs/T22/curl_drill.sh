#!/usr/bin/env bash
# T22 curl drill: the official 3-step session login with a cookie jar, then GET, POST and logout.
# Live sandbox by default; bash labs/T22/run_lab.sh labs/T22/curl_drill.sh runs it on the mock.
set -u
BASE="${SDWAN_SCHEME:-https}://${SDWAN_HOST:-sandbox-sdwan-2.cisco.com}:${SDWAN_PORT:-443}"
JAR="$(mktemp)"
trap 'rm -f "$JAR"' EXIT

echo "== 1. Log in: form POST, cookie saved to the jar (-c)"
curl --silent --insecure --include --cookie-jar "$JAR" --request POST \
  --header "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "j_username=${SDWAN_USER:-devnetuser}" \
  --data-urlencode "j_password=${SDWAN_PASS:-RG!_Yw919_83}" \
  "$BASE/j_security_check" | grep -iE '^(HTTP|content-length|set-cookie)' | sed -E 's/JSESSIONID=[^;]+/JSESSIONID=<session-hash>/'

echo; echo "== 2. Get the XSRF token: cookie sent from the jar (-b), body = token"
TOKEN=$(curl --silent --insecure --cookie "$JAR" "$BASE/dataservice/client/token")
echo "TOKEN is ${#TOKEN} chars"

echo; echo "== 3. GET inventory with cookie + token"
curl --silent --insecure --cookie "$JAR" \
  --header "X-XSRF-TOKEN: $TOKEN" \
  "$BASE/dataservice/device" \
  | python3 -c "import json, sys; [print(d['host-name'], d['device-type'], d['system-ip']) for d in json.load(sys.stdin)['data']]"

echo; echo "== 4. POST without the token -> 403 SessionTokenFilter"
curl --silent --insecure --cookie "$JAR" --request POST \
  --header "Content-Type: application/json" --data '{"size": 1}' \
  --write-out "\nHTTP %{http_code}\n" "$BASE/dataservice/alarms"

echo; echo "== 5. Log out (POST /logout with the token)"
curl --silent --insecure --cookie "$JAR" --request POST \
  --header "X-XSRF-TOKEN: $TOKEN" --output /dev/null \
  --write-out "HTTP %{http_code} -> %{redirect_url}\n" "$BASE/logout?nocache=1"

echo; echo "== 6. Wrong password: still HTTP 200, but the body is an error"
curl --silent --insecure --request POST \
  --data "j_username=devnetuser&j_password=wrong" \
  --write-out "\nHTTP %{http_code}\n" "$BASE/j_security_check"
