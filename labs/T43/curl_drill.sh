#!/usr/bin/env bash
# T43 curl drill. Needs platform.py (8143) and receiver.py (8144): bash labs/T43/run_lab.sh labs/T43/curl_drill.sh
set -u
API="http://127.0.0.1:8143/v1"
SECRET="s3cr3t-T43-demo"

echo "== 1. Register a webhook with curl (same body shape as Webex POST /v1/webhooks)"
curl --silent --request POST "$API/webhooks" \
  --header "Authorization: Bearer bot-token-T43" \
  --header "Content-Type: application/json" \
  --data '{"name":"curl hook","targetUrl":"http://127.0.0.1:8144/webhook","resource":"messages","event":"created","filter":"roomId=room-curl","secret":"'"$SECRET"'"}'
echo

echo; echo "== 2. Be the platform: sign a body with openssl and POST it to the receiver"
BODY='{"id":"wh-test","resource":"messages","event":"created","data":{"id":"msg-9999","roomId":"room-curl","personEmail":"alice@example.com"}}'
SIG=$(printf '%s' "$BODY" | openssl dgst -sha1 -hmac "$SECRET" | awk '{print $NF}')
echo "X-Spark-Signature: $SIG"
curl --silent --write-out " -> HTTP %{http_code}\n" --request POST "http://127.0.0.1:8144/webhook" \
  --header "Content-Type: application/json" --header "X-Spark-Signature: $SIG" --data "$BODY"

echo; echo "== 3. Same body, one byte changed (msg-9999 -> msg-9998), old signature"
TAMPERED=${BODY/msg-9999/msg-9998}
curl --silent --write-out " -> HTTP %{http_code}\n" --request POST "http://127.0.0.1:8144/webhook" \
  --header "Content-Type: application/json" --header "X-Spark-Signature: $SIG" --data "$TAMPERED"

echo; echo "== 4. Replay the genuine delivery from step 2 (a retry or a replay attack)"
curl --silent --write-out " -> HTTP %{http_code}\n" --request POST "http://127.0.0.1:8144/webhook" \
  --header "Content-Type: application/json" --header "X-Spark-Signature: $SIG" --data "$BODY"

echo; echo "== 5. List webhooks: the secret is never returned"
curl --silent "$API/webhooks" --header "Authorization: Bearer bot-token-T43"
echo
