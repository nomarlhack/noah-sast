#!/usr/bin/env python3
"""
lint_reader_layer.py — 보고서 MD/HTML의 헤딩에 내부 규약 용어 노출 검사.

vuln-format.md "safe 판정 4분류" 섹션에 선언된 "독자 레이어 용어 노출 금지" 규약을
자동 검증한다. 보고서 조립·리뷰 후에 호출하며, 헤딩(# ~ ######)에 내부 토큰이
포함되어 있으면 exit 5(lint 위반)로 경고한다.

금지 토큰 (헤딩 한정):
  - section-symbol + 숫자 (예: 원단위 기호 + N) — checklist.md 섹션 번호
  - mode명: evaluate_phase1, mode=evaluate, mode=review
  - 내부 라벨: DISCARD, OVERRIDE, CONFIRM (대소문자 무관)
  - Source 도달성, 실질 영향 반증 같은 내부 판정 용어
  - 스크립트명: .py 확장자 포함

근거 테이블·본문에서는 풀이 형태로 쓰이면 허용 (헤딩만 검사).

Usage:
  python3 lint_reader_layer.py <report.md> [<report.html>]

Exit code:
  0: pass
  5: lint 위반
"""

import os
import re
import sys

# 금지 토큰 정규식 (헤딩 줄 전체에서 검사)
BANNED_PATTERNS = [
    (r"§\s*\d+", "§N (checklist 섹션 번호)"),
    (r"\bmode\s*=\s*(evaluate_phase1|evaluate|review)\b", "mode명"),
    (r"\bevaluate_phase1\b", "evaluate_phase1"),
    (r"\b(DISCARD|OVERRIDE|CONFIRM)\b", "내부 라벨 (DISCARD/OVERRIDE/CONFIRM)"),
    (r"Source\s*도달성", "Source 도달성"),
    (r"실질\s*영향\s*반증", "실질 영향 반증"),
    (r"\b[a-z0-9_-]+\.py\b", "스크립트 파일명"),
    (r"phase1_(validated|discarded_reason|eval_state)", "phase1_* 필드명"),
    (r"safe_category", "safe_category 필드명"),
]

# 헤딩 패턴: MD는 `^#+\s`, HTML은 `<h\d>`
MD_HEADING = re.compile(r"^(#+)\s+(.*)$", re.MULTILINE)
HTML_HEADING = re.compile(r"<h(\d)[^>]*>(.*?)</h\d>", re.IGNORECASE | re.DOTALL)


def check_md(path: str) -> list[str]:
    if not os.path.isfile(path):
        return []
    text = open(path, encoding="utf-8").read()
    violations = []
    for m in MD_HEADING.finditer(text):
        level = len(m.group(1))
        heading = m.group(2).strip()
        for pattern, label in BANNED_PATTERNS:
            hit = re.search(pattern, heading, re.IGNORECASE)
            if hit:
                # 라인 번호 추출
                line_no = text.count("\n", 0, m.start()) + 1
                violations.append(
                    f"{path}:{line_no} (h{level}): 금지 토큰 '{label}' → \"{heading}\""
                )
    return violations


def check_html(path: str) -> list[str]:
    if not os.path.isfile(path):
        return []
    text = open(path, encoding="utf-8").read()
    violations = []
    for m in HTML_HEADING.finditer(text):
        level = m.group(1)
        heading = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        for pattern, label in BANNED_PATTERNS:
            hit = re.search(pattern, heading, re.IGNORECASE)
            if hit:
                line_no = text.count("\n", 0, m.start()) + 1
                violations.append(
                    f"{path}:{line_no} (h{level}): 금지 토큰 '{label}' → \"{heading}\""
                )
    return violations


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: lint_reader_layer.py <report.md> [<report.html>]", file=sys.stderr)
        return 1

    all_violations = []
    all_violations.extend(check_md(sys.argv[1]))
    if len(sys.argv) >= 3:
        all_violations.extend(check_html(sys.argv[2]))

    if all_violations:
        print(f"FAIL: 독자 레이어 용어 노출 {len(all_violations)}건", file=sys.stderr)
        for v in all_violations:
            print(f"  - {v}", file=sys.stderr)
        print(
            "\n금지 토큰은 헤딩(# ~ ######)에서만 검사됩니다. 근거 테이블·본문은 풀이 형태로 허용됩니다.\n"
            "vuln-format.md 'safe 판정 4분류' 섹션의 '독자 레이어 노출 금지 용어' 목록 참조.",
            file=sys.stderr,
        )
        return 5  # §13 exit code table: 5 = lint 위반

    print(f"OK: lint 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
