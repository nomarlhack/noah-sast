#!/bin/bash
# grep_index.py 래퍼. exit code + JSON 카운트 + 예상 카운트를 stdout으로 출력.
# Bash tool 최종 exit는 항상 0 (UI의 "Exit code N" 경고 방지). 실제 결과는 stdout 파싱.
#
# Usage:
#   grep_index.sh <NOAH_SAST_DIR> <PROJECT_ROOT> <PATTERN_INDEX_DIR>
#
# Output:
#   run_grep_index_exit=<0|1|2>
#   json_count=<int>
#   expected=<int>

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <NOAH_SAST_DIR> <PROJECT_ROOT> <PATTERN_INDEX_DIR>" >&2
    exit 0
fi

NOAH_SAST_DIR="$1"
PROJECT_ROOT="$2"
OUT_DIR="$3"

python3 "$NOAH_SAST_DIR/tools/grep_index.py" \
    --scanners-dir "$NOAH_SAST_DIR/scanners" \
    --project-root "$PROJECT_ROOT" \
    --out-dir "$OUT_DIR"
RC=$?
JSON_COUNT=$(ls -1 "$OUT_DIR"/*-scanner.json 2>/dev/null | wc -l | tr -d ' ')
EXPECTED=$(ls -1d "$NOAH_SAST_DIR"/scanners/*-scanner 2>/dev/null | wc -l | tr -d ' ')
echo "run_grep_index_exit=$RC"
echo "json_count=$JSON_COUNT"
echo "expected=$EXPECTED"
exit 0
