#!/usr/bin/env python3
"""validate_report.py — 보고서 정량 검증. FAIL 시 보고서 파일을 삭제한다.

Usage:
    python3 validate_report.py [확인됨+후보 건수] [보고서명(선택)] [--chain-analysis] [--master-list <path>]
    예: python3 validate_report.py 15
    예: python3 validate_report.py 15 xss-scan-report
    예: python3 validate_report.py 8 --chain-analysis
    예: python3 validate_report.py 15 --master-list /tmp/phase1_results_foo/master-list.json
"""
import sys, os

# --master-list <path> 추출 (값은 다음 인자)
master_list_arg = None
raw = list(sys.argv[1:])
cleaned = []
i = 0
while i < len(raw):
    if raw[i] == '--master-list' and i + 1 < len(raw):
        master_list_arg = raw[i + 1]
        i += 2
        continue
    cleaned.append(raw[i])
    i += 1

args = [a for a in cleaned if not a.startswith('--')]
flags = [a for a in cleaned if a.startswith('--')]

if len(args) < 1:
    print("Usage: python3 validate_report.py [확인됨+후보 건수] [보고서명] [--chain-analysis] [--master-list <path>]")
    sys.exit(1)

try:
    expected = int(args[0])
except ValueError:
    print(f"ERROR: 첫 번째 인자는 정수여야 합니다 (입력: {args[0]!r})", file=sys.stderr)
    sys.exit(1)
report_name = args[1] if len(args) > 1 else "noah-sast-report"
check_chain = '--chain-analysis' in flags

md_path = f"{report_name}.md"
html_path = f"{report_name}.html"

errors = []

# 1. MD POC 건수 검증
if os.path.exists(md_path):
    with open(md_path, encoding="utf-8") as f:
        md_content = f.read()
    md_poc = md_content.count("재현 방법 및 POC")
    if md_poc != expected:
        errors.append(f"MD POC {md_poc}건 != 기대 {expected}건 (누락 {expected - md_poc}건)")
else:
    errors.append(f"{md_path} 파일 없음")
    md_content = ""

# 2. HTML POC 건수 검증
if os.path.exists(html_path):
    with open(html_path, encoding="utf-8") as f:
        html_content = f.read()
    html_poc = html_content.count("재현 방법 및 POC")
    if html_poc != expected:
        errors.append(f"HTML POC {html_poc}건 != 기대 {expected}건 (누락 {expected - html_poc}건)")
else:
    errors.append(f"{html_path} 파일 없음")
    html_content = ""

# 3. 심각도 표시 금지 검증
if md_content:
    for keyword in ["HIGH", "MEDIUM", "LOW", "CRITICAL"]:
        lines = md_content.split("\n")
        for i, line in enumerate(lines):
            if keyword in line and not line.strip().startswith(("```", "`", "#", "|")):
                if f"**{keyword}**" in line or f": {keyword}" in line:
                    errors.append(f"심각도 표시 발견: 라인 {i+1}: {line.strip()[:80]}")

# 4. 연계 분석 섹션 검증 (--chain-analysis 플래그 시)
if check_chain:
    if md_content and "## 공격 시나리오" not in md_content:
        errors.append("연계 분석 수행됨(--chain-analysis)이나 '## 공격 시나리오' 섹션이 MD에 없음")
    if html_content and "공격 시나리오" not in html_content:
        errors.append("연계 분석 수행됨(--chain-analysis)이나 '공격 시나리오' 섹션이 HTML에 없음")

# 5. 안전 판정 항목 섹션 검증 (#25 — safe_category 4분류 자동 생성 여부)
# master-list.json에 safe 후보가 있으면 보고서에 "## 안전 판정 항목" 섹션이 존재해야 한다.
# 플레이스홀더 부재·skeleton 미동기화로 조용히 누락되는 경우를 잡는다.
master_list_path = None
if master_list_arg:
    if os.path.isfile(master_list_arg):
        master_list_path = master_list_arg
    else:
        print(f"ERROR: --master-list {master_list_arg} 파일 없음", file=sys.stderr)
        sys.exit(1)
else:
    # fallback: /tmp/phase1_results_*/master-list.json 중 mtime 최신
    import glob
    candidates = glob.glob('/tmp/phase1_results_*/master-list.json')
    if candidates:
        master_list_path = max(candidates, key=os.path.getmtime)
if master_list_path and os.path.exists(master_list_path):
    try:
        import json as _json
        with open(master_list_path, encoding='utf-8') as f:
            _ml = _json.load(f)
        _safe_count = sum(1 for c in _ml.get('candidates', []) if c.get('status') == 'safe')
        # safe 후보 0건이면 '## 안전 판정 항목' 섹션 부재 허용
        # (build_safe_section이 빈 문자열 반환하여 플레이스홀더가 빈 값으로 치환된 정상 동작)
        if _safe_count > 0:
            if md_content and "## 안전 판정 항목" not in md_content:
                errors.append(
                    f"master-list.json에 safe 후보 {_safe_count}건 있으나 '## 안전 판정 항목' 섹션이 MD에 없음 "
                    f"(skeleton에 `<!-- SAFE_SECTION_HERE -->` 플레이스홀더 누락 가능성)"
                )
            if html_content and "안전 판정 항목" not in html_content:
                errors.append(
                    f"master-list.json에 safe 후보 {_safe_count}건 있으나 '안전 판정 항목' 섹션이 HTML에 없음"
                )
    except (OSError, ValueError):
        pass  # master-list.json 읽기 실패는 무시 (레거시 스캔 호환)

# 결과 출력
if errors:
    print("FAIL:")
    for e in errors:
        print(f"  - {e}")
    for path in [md_path, html_path]:
        if os.path.exists(path):
            os.remove(path)
            print(f"  삭제됨: {path}")
    sys.exit(1)
else:
    parts = [f"MD {md_poc}/{expected}, HTML {html_poc}/{expected}"]
    if check_chain:
        parts.append("chain-analysis ✓")
    print(f"PASS: {', '.join(parts)}")
    sys.exit(0)
