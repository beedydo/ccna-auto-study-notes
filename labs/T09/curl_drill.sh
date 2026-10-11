#!/usr/bin/env bash
# T09 curl drill: spot the API style from the request alone. Start the API first:
#   python3 labs/T09/mock_api.py      (or: bash labs/T09/run_lab.sh labs/T09/curl_drill.sh)
set -u
BASE="http://127.0.0.1:8109"

echo "== 1. REST: noun in the URI, verb is the HTTP method"
curl --silent --show-error --write-out "\n[HTTP %{http_code}]\n" \
  --header "Accept: application/json" \
  "$BASE/api/v1/devices/2"

echo; echo "== 2. JSON-RPC: one URL, POST, the verb is \"method\" in the body"
curl --silent --show-error --write-out "\n[HTTP %{http_code}]\n" --request POST \
  --header "Content-Type: application/json" \
  --data '{"jsonrpc": "2.0", "method": "getDevice", "params": {"id": 2}, "id": 7}' \
  "$BASE/jsonrpc"

echo; echo "== 3. SOAP: XML Envelope, operation in SOAPAction + the Body element"
curl --silent --show-error --write-out "\n[HTTP %{http_code}]\n" --request POST \
  --header "Content-Type: text/xml; charset=utf-8" \
  --header 'SOAPAction: "GetDevice"' \
  --data '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><soapenv:Body><GetDevice><id>2</id></GetDevice></soapenv:Body></soapenv:Envelope>' \
  "$BASE/soap"

echo; echo "== 4. Sync call with a 0.5 s client timeout (server needs 1.5 s)"
curl --silent --show-error --max-time 0.5 "$BASE/api/v1/devices/2/config"
echo "[curl exit code $?]"

echo; echo "== 5. Async: 202 + taskId, then poll the task"
TASK_ID=$(curl --silent --request POST \
  --header "Content-Type: application/json" \
  --data '{"commands": ["show version"], "deviceUuids": ["csr1"]}' \
  "$BASE/dna/intent/api/v1/network-device-poller/cli/read-request" \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['response']['taskId'])")
echo "taskId=$TASK_ID"
curl --silent --show-error --write-out "\n[HTTP %{http_code}] (right away: no endTime)\n" \
  "$BASE/dna/intent/api/v1/task/$TASK_ID"
sleep 2.5
curl --silent --show-error --write-out "\n[HTTP %{http_code}] (after 2.5 s: endTime set)\n" \
  "$BASE/dna/intent/api/v1/task/$TASK_ID"
