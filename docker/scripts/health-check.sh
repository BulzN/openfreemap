#!/bin/bash
set -euo pipefail

HOST="${1:-http://localhost:8080}"
EXIT_CODE=0

echo "OpenFreeMap Health Check: $HOST"
echo

check_endpoint() {
    local url="$1"
    local expected="$2"
    local name="$3"
    
    status=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
    
    if [ "$status" = "$expected" ]; then
        echo "YES, IT WORKS - $name"
    else
        echo "NO, IT DOES NOT WORK - $name (got $status, expected $expected)"
        EXIT_CODE=1
    fi
}

check_endpoint "$HOST/health" "200" "Health endpoint"
check_endpoint "$HOST/monaco" "200" "TileJSON"
check_endpoint "$HOST/monaco/13/4264/2987.pbf" "200" "Sample tile"

exit $EXIT_CODE
