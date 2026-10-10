#!/usr/bin/env bash
# T21 curl drill: raw AXL (SOAP) vs raw UDS (REST) against the mock CUCM.
# Run:  bash labs/T21/run_lab.sh labs/T21/curl_drill.sh
# Real CUCM: export CUCM_HOST, AXL_USER, AXL_PASS, UDS_USER, UDS_PASS first.
set -u
BASE="https://${CUCM_HOST:-127.0.0.1}:${CUCM_PORT:-8443}"
AXL_USER="${AXL_USER:-axladmin}"; AXL_PASS="${AXL_PASS:-C1sco12345}"
UDS_USER="${UDS_USER:-jkam}";     UDS_PASS="${UDS_PASS:-Us3rPass}"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT

cat > "$WORK/request.xml" <<'XML'
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns="http://www.cisco.com/AXL/API/14.0">
  <soapenv:Header/>
  <soapenv:Body>
    <ns:executeSQLQuery>
      <sql>select name, description from device where tkclass = 1</sql>
    </ns:executeSQLQuery>
  </soapenv:Body>
</soapenv:Envelope>
XML

echo "== 1. AXL: POST a SOAP envelope to /axl/ (SOAPAction names version + operation)"
curl --silent --insecure --user "$AXL_USER:$AXL_PASS" \
  --header 'Content-Type: text/xml' \
  --header 'SOAPAction: "CUCM:DB ver=14.0 executeSQLQuery"' \
  --data @"$WORK/request.xml" \
  "$BASE/axl/"
echo

echo; echo "== 2. AXL: SOAPAction version does not match the namespace -> SOAP fault, HTTP 500"
curl --silent --insecure --user "$AXL_USER:$AXL_PASS" --write-out '\nHTTP %{http_code}\n' \
  --header 'Content-Type: text/xml' \
  --header 'SOAPAction: "CUCM:DB ver=12.5 executeSQLQuery"' \
  --data @"$WORK/request.xml" \
  "$BASE/axl/"

echo; echo "== 3. AXL: GET instead of POST -> 405"
curl --silent --insecure --user "$AXL_USER:$AXL_PASS" --output /dev/null --write-out 'HTTP %{http_code}\n' \
  "$BASE/axl/"

echo; echo "== 4. UDS: plain GET, no envelope, no SOAPAction; XML back"
curl --silent --insecure --header 'Accept: application/xml' \
  "$BASE/cucm-uds/users?last=Kam"
echo

echo; echo "== 5. UDS: personal resource needs the END USER's own credentials"
curl --silent --insecure --output /dev/null --write-out 'no auth   -> HTTP %{http_code}\n' \
  --header 'Accept: application/xml' "$BASE/cucm-uds/user/$UDS_USER/devices"
curl --silent --insecure --output /dev/null --write-out 'AXL admin -> HTTP %{http_code}\n' \
  --user "$AXL_USER:$AXL_PASS" --header 'Accept: application/xml' "$BASE/cucm-uds/user/$UDS_USER/devices"
curl --silent --insecure --output /dev/null --write-out 'end user  -> HTTP %{http_code}\n' \
  --user "$UDS_USER:$UDS_PASS" --header 'Accept: application/xml' "$BASE/cucm-uds/user/$UDS_USER/devices"
