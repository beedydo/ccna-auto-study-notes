#!/usr/bin/env bash
# T24 curl drill: the raw UCS Manager XML API, no SDK. Every call is a POST of XML to /nuova.
# Start the mock first (python3 labs/T24/mock_ucsm.py) or: bash labs/T24/run_lab.sh labs/T24/curl_drill.sh
# Real UCSM: UCSM=https://<ucsm-vip>/nuova and add --insecure for a self-signed cert.
set -u
UCSM="${UCSM:-http://127.0.0.1:8124/nuova}"
USER="${UCSM_USER:-ucspe}"
PASS="${UCSM_PASS:-ucspe}"
pretty() {   # indent the one-line XML reply so the tree is readable
  python3 -c "import sys, xml.dom.minidom as m; print(m.parseString(sys.stdin.read()).toprettyxml(indent='  ').split(chr(10), 1)[1].strip())"
}

echo "== 1. aaaLogin: credentials as XML attributes -> outCookie"
LOGIN=$(curl --silent --request POST --header "Content-Type: application/xml" \
  --data "<aaaLogin inName=\"$USER\" inPassword=\"$PASS\" />" "$UCSM")
echo "$LOGIN" | pretty
COOKIE=$(echo "$LOGIN" | sed -E 's/.*outCookie="([^"]+)".*/\1/')

echo; echo "== 2. wrong password: still HTTP 200, the error is INSIDE the XML"
curl --silent --output /dev/null --write-out "HTTP status %{http_code}\n" --request POST \
  --data '<aaaLogin inName="ucspe" inPassword="wrong" />' "$UCSM"
curl --silent --request POST --data '<aaaLogin inName="ucspe" inPassword="wrong" />' "$UCSM" | pretty

echo; echo "== 3. configResolveClass: every computeBlade (cookie goes in the XML, not a header)"
curl --silent --request POST \
  --data "<configResolveClass cookie=\"$COOKIE\" classId=\"computeBlade\" inHierarchical=\"false\" />" "$UCSM" | pretty

echo; echo "== 4. configResolveDn: one object by its DN"
curl --silent --request POST \
  --data "<configResolveDn cookie=\"$COOKIE\" dn=\"sys/chassis-1/blade-3\" inHierarchical=\"false\" />" "$UCSM" | pretty

echo; echo "== 5. configResolveDn on a DN that does not exist: success, empty outConfig"
curl --silent --request POST \
  --data "<configResolveDn cookie=\"$COOKIE\" dn=\"sys/chassis-1/blade-8\" inHierarchical=\"false\" />" "$UCSM" | pretty

echo; echo "== 6. no cookie -> errorCode 552"
curl --silent --request POST --data '<configResolveClass classId="computeBlade" />' "$UCSM" | pretty

echo; echo "== 7. aaaLogout"
curl --silent --request POST --data "<aaaLogout inCookie=\"$COOKIE\" />" "$UCSM" | pretty
