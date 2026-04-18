#!/usr/bin/env bash
# validate-report-precommit.sh — scan-report 보고서 커밋 전 검증 훅 (선택 설치)
#
# 요구 사항:
#   - python3 (3.8+)
#   - bash 4+ (또는 /usr/bin/env bash)
#   - jq (선택, 경고 파싱에 사용)
#
# 설치 방법:
#   cd <프로젝트 루트>
#   ln -sf "$PWD/<경로>/noah-8719/skills/sast/hooks/validate-report-precommit.sh" \
#          .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit
#
# 동작:
#   - 스테이징된 noah-sast-report.md 또는 그 .html이 있으면
#     validate_report.py를 `--json-output`으로 실행하여 경고를 파싱
#   - 경고 존재 시 stderr에 출력. 경고는 exit 0(통과)로 처리하여 커밋을 막지 않음.
#     커밋 차단을 원하면 아래 SOFT_MODE를 0으로 변경.

set -euo pipefail

SOFT_MODE="${SOFT_MODE:-1}"  # 1: 경고만, 0: 경고도 차단

# 스테이징된 보고서 파일 탐색 (보고서명 커스텀 가능)
REPORT_NAME="${REPORT_NAME:-noah-sast-report}"
MD="${REPORT_NAME}.md"
HTML="${REPORT_NAME}.html"

STAGED=$(git diff --cached --name-only 2>/dev/null || true)
if ! echo "$STAGED" | grep -qE "(^|/)${REPORT_NAME}\.(md|html)$"; then
  exit 0
fi

# master-list.json 탐색 (환경변수 또는 /tmp/phase1_results_* 최신)
MASTER_LIST="${MASTER_LIST:-}"
if [ -z "$MASTER_LIST" ]; then
  MASTER_LIST=$(ls -t /tmp/phase1_results_*/master-list.json 2>/dev/null | head -1 || true)
fi

if [ -z "$MASTER_LIST" ] || [ ! -f "$MASTER_LIST" ]; then
  echo "⚠  validate-report-precommit: master-list.json 없음, 검증 스킵" >&2
  exit 0
fi

# 기대 건수: MD 파일의 "재현 방법 및 POC" 카운트를 그대로 사용
if [ ! -f "$MD" ]; then
  echo "⚠  validate-report-precommit: $MD 없음" >&2
  exit 0
fi
EXPECTED=$(grep -c "재현 방법 및 POC" "$MD")

JSON_OUT=$(mktemp -t validate-report.XXXXXX.json)
trap 'rm -f "$JSON_OUT"' EXIT

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATE="$SCRIPT_DIR/../sub-skills/scan-report/validate_report.py"

set +e
python3 "$VALIDATE" "$EXPECTED" "$REPORT_NAME" \
  --master-list "$MASTER_LIST" \
  --json-output "$JSON_OUT"
RET=$?
set -e

case $RET in
  0)
    exit 0
    ;;
  6)
    # 경고 수준
    WARN_COUNT=$(python3 -c "
import json, sys
try:
    with open('$JSON_OUT') as f:
        d = json.load(f)
    print(len(d.get('warnings', [])))
except Exception:
    print(0)
")
    echo "⚠  validate-report-precommit: ${WARN_COUNT} warnings (exit 6)" >&2
    echo "   상세: $JSON_OUT" >&2
    if [ "$SOFT_MODE" = "0" ]; then
      echo "   SOFT_MODE=0 설정됨 → 커밋 차단" >&2
      cat "$JSON_OUT" >&2
      exit 1
    fi
    exit 0
    ;;
  *)
    # fail (exit 1) — 차단
    echo "✗  validate-report-precommit: validate_report FAIL (exit $RET)" >&2
    exit 1
    ;;
esac
