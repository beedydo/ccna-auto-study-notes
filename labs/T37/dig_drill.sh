#!/usr/bin/env bash
# T37 dig drill: query the mock DNS server (UDP 5053) for each record type, then a real resolver.
# Usage:  bash labs/T37/dig_drill.sh        (needs dig: apt-get install dnsutils; already in the lab image)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/mock_services.py" > /dev/null 2>&1 &
MOCK_PID=$!
trap 'kill $MOCK_PID 2>/dev/null' EXIT
sleep 0.5

DIG="dig @127.0.0.1 -p 5053 +norecurse +noall +answer +comments"
echo "== 1. A (name -> IPv4)";        $DIG csr1.lab.example A    | grep -E "status|IN"
echo "== 2. AAAA (name -> IPv6)";     $DIG csr1.lab.example AAAA | grep -E "status|IN"
echo "== 3. CNAME (alias -> name)";   $DIG www.lab.example A     | grep -E "status|IN"
echo "== 4. MX (domain -> mail server, lowest preference wins)"; $DIG lab.example MX | grep -E "status|IN"
echo "== 5. PTR (IP -> name): dig -x builds 48.20.10.10.in-addr.arpa"; $DIG -x 10.10.20.48 | grep -E "status|IN"
echo "== 6. Missing name";            $DIG nope.lab.example A    | grep -E "status"
echo "== 7. Real resolver (needs internet): +short prints only the answer"
dig +short +time=2 +tries=1 developer.cisco.com A || echo "no internet DNS from here"
