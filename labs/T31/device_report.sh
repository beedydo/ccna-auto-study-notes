#!/usr/bin/env bash
# device_report.sh: read device inventories, query each device's version API, write a report.
# Usage: ./device_report.sh INVENTORY.csv [MORE.csv ...]
# Env:   API_BASE (default http://127.0.0.1:8131), REPORT (default report.csv)

API_BASE="${API_BASE:-http://127.0.0.1:8131}"     # env var with a default
REPORT="${REPORT:-report.csv}"
WORKFILE="$(mktemp "${TMPDIR:-/tmp}/devices.XXXXXX")" || exit 3   # $(...) captures output
ok=0
failed=0

usage() {
    echo "Usage: $0 INVENTORY.csv [MORE.csv ...]" >&2   # $0 = how the script was called
    exit 2
}

log() {
    echo "[$(date -u +%H:%M:%S)] $*" >&2                # messages go to stderr, data to stdout/file
}

valid_ip() {
    [[ $1 =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]          # function's exit status = last command's
}

get_version() {
    local host="$1"                                    # local: not visible outside the function
    local json
    json=$(curl --silent --fail --max-time 3 "$API_BASE/$host.json") || return   # keeps curl's code
    echo "$json" | grep '"version"' | cut -d '"' -f 4  # pipe: stdout of one -> stdin of next
}

if [ $# -lt 1 ]; then                                  # $# = number of arguments
    usage
fi

echo "hostname,mgmt_ip,os,api,version,status" > "$REPORT"   # > creates/overwrites

for inventory in "$@"; do                              # "$@" = each argument, kept whole
    if [ ! -f "$inventory" ]; then
        log "skip: no such file '$inventory'"
        continue
    fi
    grep -v -e '^#' -e '^$' "$inventory" >> "$WORKFILE"     # drop comments and blank lines
done

log "loaded $(wc -l < "$WORKFILE" | tr -d ' ') devices from $# file(s)"

while IFS=, read -r host ip os; do                    # split each line on commas
    if ! valid_ip "$ip"; then
        log "$host: bad IP '$ip'"
        echo "$host,$ip,$os,-,-,BAD_IP" >> "$REPORT"
        failed=$((failed + 1))
        continue
    fi

    if [ "$os" == "nxos" ]; then
        api="NX-API"
    else
        api="RESTCONF"
    fi

    version=$(get_version "$host")
    rc=$?                                              # exit status of the line above
    if [ $rc -eq 0 ]; then
        echo "$host,$ip,$os,$api,$version,OK" >> "$REPORT"     # >> appends
        ok=$((ok + 1))
    else
        log "$host: API call failed (rc=$rc)"
        echo "$host,$ip,$os,$api,-,UNREACHABLE" >> "$REPORT"
        failed=$((failed + 1))
    fi
done < "$WORKFILE"                                     # < feeds the file to the loop's stdin

rm -f "$WORKFILE"

echo "--- $(basename "$REPORT") ---"
cat "$REPORT"
echo "--- OK devices per OS ---"
awk -F, 'NR > 1 && $6 == "OK" { n[$3]++ } END { for (o in n) print o, n[o] }' "$REPORT" | sort
echo "ok=$ok failed=$failed"

if [ "$failed" -gt 0 ]; then
    exit 1                                             # non-zero = something went wrong
fi
exit 0
