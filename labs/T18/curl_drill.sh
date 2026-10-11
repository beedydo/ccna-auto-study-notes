#!/usr/bin/env bash
# T18 curl drill: the Meraki calls the exam shows, against the local mock.
# Real cloud:  export MERAKI_BASE_URL=https://api.meraki.com/api/v1 MERAKI_DASHBOARD_API_KEY=<key>
set -u
BASE="${MERAKI_BASE_URL:-http://127.0.0.1:8118/api/v1}"
KEY="${MERAKI_DASHBOARD_API_KEY:-0123456789abcdef0123456789abcdef01234567}"
NET="L_646829496481105433"

echo "== 1. Bearer header (v1 standard)"
curl --silent --show-error \
  --header "Authorization: Bearer $KEY" \
  "$BASE/organizations"

echo; echo; echo "== 2. Legacy header X-Cisco-Meraki-API-Key"
curl --silent --show-error \
  --header "X-Cisco-Meraki-API-Key: $KEY" \
  --write-out "\nHTTP %{http_code}\n" --output /dev/null \
  "$BASE/organizations"

echo; echo "== 3. No key -> 401"
curl --silent --show-error --include "$BASE/organizations" | tr -d '\r' | grep -E '^HTTP|^\{'

echo; echo "== 4. Page 1 of networks: read the Link header"
curl --silent --show-error --include \
  --header "Authorization: Bearer $KEY" \
  "$BASE/organizations/549236/networks?perPage=3" | tr -d '\r' | grep -E '^HTTP|^Link'

echo; echo "== 5. Page 2: copy startingAfter from rel=next"
curl --silent --show-error \
  --header "Authorization: Bearer $KEY" \
  "$BASE/organizations/549236/networks?perPage=3&startingAfter=L_646829496481105435" \
  | python3 -c "import json, sys; print([n['name'] for n in json.load(sys.stdin)])"

echo; echo "== 6. Which switch port is 10.10.10.21 on?"
curl --silent --show-error --get \
  --header "Authorization: Bearer $KEY" \
  --data "ip=10.10.10.21" \
  "$BASE/networks/$NET/clients" \
  | python3 -c "import json, sys; c = json.load(sys.stdin)[0]; print(c['recentDeviceName'], c['recentDeviceSerial'], 'port', c['switchport'])"

echo; echo "== 7. 15 calls in under a second -> some 429s"
sleep 1.1
for i in $(seq 1 15); do
  curl --silent --output /dev/null --write-out "%{http_code} " \
    --header "Authorization: Bearer $KEY" "$BASE/networks/$NET/devices"
done
echo
curl --silent --show-error --include \
  --header "Authorization: Bearer $KEY" "$BASE/networks/$NET/devices" | tr -d '\r' | grep -E '^HTTP|^Retry-After|^\{"errors'
