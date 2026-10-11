#!/usr/bin/env bash
# T10 curl drill: the same auth methods as auth_tour.py, with curl.
# Run via:  bash labs/T10/run_lab.sh labs/T10/curl_drill.sh   (starts the API, loads mock-creds.env)
set -u
BASE="http://127.0.0.1:8110"

echo "== 1. --user builds the Basic header for you (see it with --verbose)"
curl --silent --verbose --output /dev/null --user "$LAB_USER:$LAB_PASS" "$BASE/basic/devices" 2>&1 \
  | grep -E "^> (GET|Authorization)|^< HTTP"

echo; echo "== 2. Same header by hand: base64 of user:pass"
B64=$(printf '%s' "$LAB_USER:$LAB_PASS" | base64)
echo "Authorization: Basic $B64"
printf '%s' "$B64" | base64 --decode; echo "   <- anyone can decode it"

echo; echo "== 3. Custom token: POST with Basic, then X-Auth-Token"
TOKEN=$(curl --silent --request POST --user "$LAB_USER:$LAB_PASS" "$BASE/catc/auth/token" \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['Token'])")
echo "TOKEN=$TOKEN"
curl --silent --header "X-Auth-Token: $TOKEN" "$BASE/catc/devices"; echo

echo; echo "== 4. API key in a header"
curl --silent --header "X-API-Key: $LAB_API_KEY" "$BASE/key/devices"; echo

echo; echo "== 5. Cookie jar: --cookie-jar saves Set-Cookie, --cookie sends it back"
JAR="$(mktemp)"
curl --silent --output /dev/null --cookie-jar "$JAR" --request POST \
  --data-urlencode "j_username=$LAB_USER" --data-urlencode "j_password=$LAB_PASS" \
  "$BASE/sdwan/j_security_check"
curl --silent --cookie "$JAR" "$BASE/sdwan/dataservice/device"; echo
rm -f "$JAR"

echo; echo "== 6. Wrong scheme word: Bearer where the API wants Basic -> 401"
curl --silent --include --header "Authorization: Bearer $B64" "$BASE/basic/devices" | head -1
