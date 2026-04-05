#!/usr/bin/env python3
"""validate_links.py — HTML 보고서의 앵커 링크 유효성 검증.

Usage:
    python3 validate_links.py [HTML파일명]
    예: python3 validate_links.py noah-sast-report.html
"""
import re, sys

html_path = sys.argv[1] if len(sys.argv) > 1 else "noah-sast-report.html"
html = open(html_path, encoding='utf-8').read()

# 요약 테이블의 href="#vuln-N" 링크 추출
hrefs = set(re.findall(r'href="#(vuln-\d+)"', html))
# HTML 내 id="vuln-N" 요소 추출
ids = set(re.findall(r'id="(vuln-\d+)"', html))

missing_ids = hrefs - ids   # 링크는 있으나 앵커 없음
orphan_ids = ids - hrefs    # 앵커는 있으나 링크 없음

if missing_ids:
    print("LINK FAIL — 앵커 없는 링크:", sorted(missing_ids, key=lambda x: int(x.split('-')[1])))
    print("→ MD에서 해당 항목 헤딩 형식을 #### N. 제목으로 수정 후 HTML 재생성 필요")
    sys.exit(1)
elif orphan_ids:
    print(f"LINK WARN — 링크 없는 앵커 {len(orphan_ids)}건 (무해)")
    print("LINK OK")
    sys.exit(0)
else:
    print(f"LINK OK — {len(ids)}개 앵커 전부 연결됨")
    sys.exit(0)
