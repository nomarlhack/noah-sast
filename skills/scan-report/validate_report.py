#!/usr/bin/env python3
"""validate_report.py — 보고서 정량 검증. FAIL 시 보고서 파일을 삭제한다.

Usage:
    python3 validate_report.py [확인됨+후보 건수] [보고서명(선택)]
    예: python3 validate_report.py 15
    예: python3 validate_report.py 15 xss-scan-report
"""
import sys, os

if len(sys.argv) < 2:
    print("Usage: python3 validate_report.py [확인됨+후보 건수] [보고서명]")
    sys.exit(1)

expected = int(sys.argv[1])
report_name = sys.argv[2] if len(sys.argv) > 2 else "noah-sast-report"
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

# 2. HTML POC 건수 검증
if os.path.exists(html_path):
    with open(html_path, encoding="utf-8") as f:
        html_content = f.read()
    html_poc = html_content.count("재현 방법 및 POC")
    if html_poc != expected:
        errors.append(f"HTML POC {html_poc}건 != 기대 {expected}건 (누락 {expected - html_poc}건)")
else:
    errors.append(f"{html_path} 파일 없음")

# 3. 심각도 표시 금지 검증
if os.path.exists(md_path):
    for keyword in ["HIGH", "MEDIUM", "LOW", "CRITICAL"]:
        lines = md_content.split("\n")
        for i, line in enumerate(lines):
            if keyword in line and not line.strip().startswith(("```", "`", "#", "|")):
                if f"**{keyword}**" in line or f": {keyword}" in line:
                    errors.append(f"심각도 표시 발견: 라인 {i+1}: {line.strip()[:80]}")

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
    print(f"PASS: MD {md_poc}/{expected}, HTML {html_poc}/{expected}")
    sys.exit(0)
