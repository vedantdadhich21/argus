#!/usr/bin/env bash
# scripts/smoke.sh — End-to-end integration smoke test for APK Sentinel
# Tests all core API endpoints, pipeline execution, and error handling.

set -e

BASE_URL="${1:-http://localhost:8000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Choose APK sample for testing
if [ -f "$REPO_ROOT/server/samples/fake_banker.apk" ]; then
    SAMPLE_APK="$REPO_ROOT/server/samples/fake_banker.apk"
elif [ -f "$REPO_ROOT/android/app/build/intermediates/apk/debug/app-debug.apk" ]; then
    SAMPLE_APK="$REPO_ROOT/android/app/build/intermediates/apk/debug/app-debug.apk"
else
    echo "❌ No sample APK found to test with."
    exit 1
fi

echo "========================================================"
echo "🛡️  Argus — E2E Smoke Test"
echo "Target Base URL: $BASE_URL"
echo "Test Sample APK: $SAMPLE_APK"
echo "========================================================"
echo ""

# 1. Health check
echo -n "[1/9] Testing GET /health ... "
HEALTH_RESP=$(curl -s -f "$BASE_URL/health" || echo "FAILED")
if [[ "$HEALTH_RESP" == *"\"status\":\"ok\""* ]] || [[ "$HEALTH_RESP" == *"\"status\": \"ok\""* ]]; then
    echo "✅ PASS"
else
    echo "❌ FAIL ($HEALTH_RESP)"
    exit 1
fi

# 2. Stats
echo -n "[2/9] Testing GET /api/stats ... "
STATS_RESP=$(curl -s -f "$BASE_URL/api/stats" || echo "FAILED")
if [[ "$STATS_RESP" == *"total_scans"* ]]; then
    echo "✅ PASS"
else
    echo "❌ FAIL ($STATS_RESP)"
    exit 1
fi

# 3. Upload APK
echo -n "[3/9] Testing POST /api/scan (upload) ... "
UPLOAD_RESP=$(curl -s -f -X POST "$BASE_URL/api/scan" -F "file=@$SAMPLE_APK" || echo "FAILED")
SCAN_ID=$(echo "$UPLOAD_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('scan_id', ''))" 2>/dev/null || echo "")

if [ -n "$SCAN_ID" ] && [ "$SCAN_ID" != "None" ]; then
    echo "✅ PASS (scan_id=$SCAN_ID)"
else
    echo "❌ FAIL ($UPLOAD_RESP)"
    exit 1
fi

# 4. Poll scan status until completion
echo -n "[4/9] Polling GET /api/scan/$SCAN_ID until completion ... "
MAX_ATTEMPTS=35
STATUS="unknown"

for i in $(seq 1 $MAX_ATTEMPTS); do
    SCAN_DATA=$(curl -s "$BASE_URL/api/scan/$SCAN_ID")
    STATUS=$(echo "$SCAN_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "error")
    
    if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
        break
    fi
    sleep 3
done

if [ "$STATUS" = "completed" ]; then
    SCORE=$(echo "$SCAN_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin).get('final_score', 'N/A'))" 2>/dev/null || echo "N/A")
    SEVERITY=$(echo "$SCAN_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin).get('severity', 'N/A'))" 2>/dev/null || echo "N/A")
    echo "✅ PASS (status=completed, score=$SCORE, severity=$SEVERITY)"
else
    echo "❌ FAIL (ended with status=$STATUS)"
    exit 1
fi

# 5. Hash lookup fast-path
echo -n "[5/9] Testing POST /api/lookup/hash ... "
SHA256=$(shasum -a 256 "$SAMPLE_APK" | awk '{print $1}')
LOOKUP_RESP=$(curl -s -f -X POST "$BASE_URL/api/lookup/hash" \
    -H "Content-Type: application/json" \
    -d "{\"sha256\": \"$SHA256\"}" || echo "FAILED")

KNOWN=$(echo "$LOOKUP_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('known', False))" 2>/dev/null || echo "False")

if [ "$KNOWN" = "True" ]; then
    echo "✅ PASS (known=True)"
else
    echo "❌ FAIL ($LOOKUP_RESP)"
    exit 1
fi

# 6. Scans history
echo -n "[6/9] Testing GET /api/scans ... "
SCANS_RESP=$(curl -s -f "$BASE_URL/api/scans?limit=5" || echo "FAILED")
TOTAL=$(echo "$SCANS_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total', 0))" 2>/dev/null || echo "0")

if [ "$TOTAL" -gt 0 ]; then
    echo "✅ PASS (total=$TOTAL)"
else
    echo "❌ FAIL ($SCANS_RESP)"
    exit 1
fi

# 7. Download report (Markdown and PDF)
echo -n "[7/9] Testing GET /api/scan/$SCAN_ID/report?format=md ... "
REPORT_RESP=$(curl -s -f "$BASE_URL/api/scan/$SCAN_ID/report?format=md" || echo "FAILED")

if [[ "$REPORT_RESP" == *"# Threat Investigation Report"* ]]; then
    echo "✅ PASS (report length=${#REPORT_RESP} bytes)"
else
    echo "❌ FAIL (report content invalid or empty)"
    exit 1
fi

echo -n "[8/9] Testing GET /api/scan/$SCAN_ID/report?format=pdf ... "
PDF_RESP=$(curl -s -f "$BASE_URL/api/scan/$SCAN_ID/report?format=pdf" || echo "FAILED")
if [[ "$PDF_RESP" == "%PDF"* ]]; then
    echo "✅ PASS (valid PDF header, size=${#PDF_RESP} bytes)"
else
    echo "❌ FAIL (invalid PDF content)"
    exit 1
fi

# 9. Error handling checks
echo -n "[9/9] Testing 415 rejection for non-APK upload ... "
TMP_FILE=$(mktemp /tmp/test_invalid.txt)
echo "not an apk" > "$TMP_FILE"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/scan" -F "file=@$TMP_FILE" || echo "000")
rm -f "$TMP_FILE"

if [ "$HTTP_CODE" = "415" ]; then
    echo "✅ PASS (received HTTP 415)"
else
    echo "❌ FAIL (expected HTTP 415, got $HTTP_CODE)"
    exit 1
fi

echo ""
echo "========================================================"
echo "🎉 ALL 9 SMOKE TESTS PASSED END-TO-END!"
echo "========================================================"
