#!/bin/bash
# Step 4 후처리 2~6단계: validate → lint → html → links → open.
# 조건부 단계인 report-review(1단계)는 메인 에이전트가 별도 수행 후 이 스크립트 호출.
#
# Usage:
#   finalize_report.sh <NOAH_SAST_DIR> <PHASE1_RESULTS_DIR> <confirmed_candidate_count>
#
# Exit code:
#   0: 모든 단계 통과
#   비0: 해당 단계 실패 (stdout에 단계명 + 에러 메시지 표시)

set -e

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <NOAH_SAST_DIR> <PHASE1_RESULTS_DIR> <confirmed_candidate_count>" >&2
    exit 1
fi

NOAH_SAST_DIR="$1"
PHASE1_RESULTS_DIR="$2"
COUNT="$3"

REPORT_MD="noah-sast-report.md"
REPORT_HTML="noah-sast-report.html"

echo "[1/5] validate_report.py"
python3 "$NOAH_SAST_DIR/sub-skills/scan-report/validate_report.py" "$COUNT" \
    --master-list "$PHASE1_RESULTS_DIR/master-list.json"

echo "[2/5] lint_reader_layer.py"
python3 "$NOAH_SAST_DIR/tools/lint_reader_layer.py" "$REPORT_MD"

echo "[3/5] md_to_html.py"
python3 "$NOAH_SAST_DIR/sub-skills/scan-report/md_to_html.py"

echo "[4/5] validate_links.py"
python3 "$NOAH_SAST_DIR/sub-skills/scan-report/validate_links.py" "$REPORT_HTML"

echo "[5/5] open"
open "$REPORT_HTML"

echo "DONE"
