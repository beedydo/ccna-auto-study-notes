#!/usr/bin/env bash
# T41 drill: the same journey with dig and curl against labs/T41/stack.py.
# Usage:  bash labs/T41/dig_curl_drill.sh      (needs dig + curl; both are in the lab image)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
PORT="${T41_PORT:-18041}"
T41_PORT="$PORT" "${PYTHON:-python3}" -B "$HERE/stack.py" > /dev/null 2>&1 &
STACK_PID=$!
trap 'kill $STACK_PID 2>/dev/null' EXIT
for _ in $(seq 1 40); do
  curl --silent --output /dev/null "http://127.0.41.1:$PORT/ready" && break   # any reply (404) = up
  sleep 0.25
done

DIG="dig @127.0.0.1 -p $PORT +norecurse +noall +answer +comments"
echo "== 1. DNS: two A records, order rotates on each query (round robin)"
$DIG app.t41.lab A | grep -E "status|IN"
$DIG app.t41.lab A | grep -E "IN"
echo "== 2. DNS: unknown name"
$DIG nope.t41.lab A | grep -E "status"

URL="http://app.t41.lab:$PORT"
RESOLVE="--resolve app.t41.lab:$PORT:127.0.41.1"    # pin the name to site A's VIP (skip /etc/hosts)
echo "== 3. Firewall: blocklisted source 127.0.0.66 is dropped (no reply -> timeout)"
curl --silent --show-error --max-time 1 $RESOLVE --interface 127.0.0.66 "$URL/api/hello"
echo " (curl exit code $?)"
echo "== 4. WAF: SQL injection in the query string -> 403"
curl --silent --get $RESOLVE --data-urlencode "q=' OR 1=1--" --write-out " HTTP %{http_code}\n" "$URL/api/search"
echo "== 5. LB + reverse proxy: hidden Server header, Via, X-Forwarded-For, sticky cookie"
curl --silent --include $RESOLVE --interface 127.0.0.10 "$URL/api/hello" | grep -vE "^(Date|Content-Length|Content-Type)"
echo
echo "== 6. Sticky: keep the cookie in a jar and send it back -> same server every time"
JAR="$(mktemp)"
for _ in 1 2 3; do
  curl --silent $RESOLVE --cookie-jar "$JAR" --cookie "$JAR" "$URL/api/hello"; echo
done
rm -f "$JAR"
echo "== 7. Cache + compression on /static/*"
curl --silent --output /dev/null --dump-header - $RESOLVE "$URL/static/app.css" | grep -E "X-Cache"
curl --silent --output /dev/null --dump-header - $RESOLVE "$URL/static/app.css" | grep -E "X-Cache"
curl --silent --output /dev/null $RESOLVE --write-out "plain: %{size_download} bytes\n" "$URL/static/app.css"
curl --silent --output /dev/null $RESOLVE --header "Accept-Encoding: gzip" --write-out "gzip:  %{size_download} bytes\n" "$URL/static/app.css"
