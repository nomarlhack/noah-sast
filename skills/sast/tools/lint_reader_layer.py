#!/usr/bin/env python3
"""
lint_reader_layer.py — 보고서 MD/HTML의 헤딩 및 개요 필드에 내부 규약 용어 노출 검사.

vuln-format.md "safe 판정 4분류" 섹션에 선언된 "독자 레이어 용어 노출 금지" 규약을
자동 검증한다. 보고서 조립·리뷰 후에 호출하며, 헤딩(# ~ ######) 및 개요 섹션의
`**필드**:` 라인에 내부 토큰이 포함되어 있으면 exit 5(lint 위반)로 경고한다.

검사 범위:
  1. MD/HTML 헤딩 (h1 ~ h6)
  2. 개요 블록의 필드명 (보고서 최상단 제목 직후 ~ 첫 `---` 또는 첫 `##` 이전)
     — vuln-format.md의 "통합 보고서 구조" 정의에 따라 개요 필드는 독자에게
     직접 노출되므로 헤딩과 동등한 수준으로 검사한다.

금지 토큰:
  - section-symbol + 숫자 (예: 원단위 기호 + N) — checklist.md 섹션 번호
  - mode명: evaluate_phase1, mode=evaluate, mode=review
  - 내부 라벨: DISCARD, OVERRIDE, CONFIRM (대소문자 무관)
  - Source 도달성, 실질 영향 반증 같은 내부 판정 용어
  - 스크립트명: .py 확장자 포함
  - 내부 메타 서술: 파이프라인, Phase N, 내부 파이프라인

근거 테이블·본문에서는 풀이 형태로 쓰이면 허용 (헤딩·개요 필드명만 검사).

Usage:
  python3 lint_reader_layer.py <report.md> [<report.html>]

Exit code:
  0: pass
  5: lint 위반
"""

import os
import re
import sys

# 금지 토큰 정규식 (헤딩·개요 필드명에서 검사)
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
    (r"파이프라인", "파이프라인 (내부 메타 서술)"),
    (r"Phase\s*\d+", "Phase N (내부 단계 서술)"),
    (r"내부\s*흐름", "내부 흐름"),
]

# 헤딩 패턴: MD는 `^#+\s`, HTML은 `<h\d>`
MD_HEADING = re.compile(r"^(#+)\s+(.*)$", re.MULTILINE)
HTML_HEADING = re.compile(r"<h(\d)[^>]*>(.*?)</h\d>", re.IGNORECASE | re.DOTALL)

# 개요 필드 패턴: **필드명**: 값 — 필드명만 검사 대상
MD_OVERVIEW_FIELD = re.compile(r"^\*\*([^*]+?)\*\*\s*:\s*(.+)$", re.MULTILINE)


def _extract_overview_block(text: str) -> tuple[str, int]:
    """보고서 최상단의 개요 블록을 추출한다.

    두 가지 형태 지원:
    1. `# 제목` 직후 바로 `**필드**:`들이 나오는 형태 (레거시)
    2. `# 제목` → `## 개요` → `**필드**:` 형태 (현재 vuln-format.md 규약)

    범위는 개요 컨텐츠 시작 ~ 첫 `---` 또는 그 다음 `## ...`(개요가 아닌) 이전.
    개요 블록이 없으면 ('', 0) 반환.
    """
    m_title = re.search(r"^#\s+.+$", text, re.MULTILINE)
    if not m_title:
        return ('', 0)
    body_start = m_title.end()

    # `## 개요` 헤딩이 있으면 그 이후를 개요 컨텐츠 시작으로 설정
    m_overview = re.search(r"^##\s+개요\s*$", text[body_start:], re.MULTILINE)
    if m_overview:
        body_start = body_start + m_overview.end()

    after = text[body_start:]
    # 종료 지점: 첫 `---` 또는 (개요 이후) 다음 `## ` 이전
    end_offsets = []
    for pat in (r"^---\s*$", r"^##\s+"):
        em = re.search(pat, after, re.MULTILINE)
        if em:
            end_offsets.append(em.start())
    if not end_offsets:
        return ('', 0)
    end_offset = min(end_offsets)
    block = after[:end_offset]
    start_line = text[:body_start].count("\n") + 1
    return (block, start_line)


def check_md(path: str) -> list[str]:
    if not os.path.isfile(path):
        return []
    text = open(path, encoding="utf-8").read()
    violations = []

    # 1. 헤딩 검사
    for m in MD_HEADING.finditer(text):
        level = len(m.group(1))
        heading = m.group(2).strip()
        for pattern, label in BANNED_PATTERNS:
            hit = re.search(pattern, heading, re.IGNORECASE)
            if hit:
                line_no = text.count("\n", 0, m.start()) + 1
                violations.append(
                    f"{path}:{line_no} (h{level}): 금지 토큰 '{label}' → \"{heading}\""
                )

    # 2. 개요 섹션 필드명 검사 (보고서 최상단 `# 제목` ~ 첫 `---` 또는 `## ` 사이)
    overview_block, overview_start_line = _extract_overview_block(text)
    if overview_block:
        for fm in MD_OVERVIEW_FIELD.finditer(overview_block):
            field_name = fm.group(1).strip()
            # 필드명 자체만 검사 대상 (값은 허용 — 독자 친절 서술 가능)
            for pattern, label in BANNED_PATTERNS:
                hit = re.search(pattern, field_name, re.IGNORECASE)
                if hit:
                    # 블록 내 offset → 전체 텍스트 라인 번호 변환
                    rel_line = overview_block.count("\n", 0, fm.start()) + 1
                    abs_line = overview_start_line + rel_line
                    violations.append(
                        f"{path}:{abs_line} (개요 필드): 금지 토큰 '{label}' → "
                        f"\"**{field_name}**:\""
                    )
    return violations


def check_html(path: str) -> list[str]:
    if not os.path.isfile(path):
        return []
    text = open(path, encoding="utf-8").read()
    violations = []

    # 1. 헤딩 검사
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

    # 2. 개요 섹션 필드명 검사 (HTML: <h1> 이후 첫 <h2>/<hr> 전까지)
    m_h1 = re.search(r"<h1[^>]*>.*?</h1>", text, re.IGNORECASE | re.DOTALL)
    if m_h1:
        body_start = m_h1.end()
        after = text[body_start:]
        end_offsets = []
        for pat in (r"<h2[^>]*>", r"<hr\s*/?>"):
            em = re.search(pat, after, re.IGNORECASE)
            if em:
                end_offsets.append(em.start())
        if end_offsets:
            overview_html = after[:min(end_offsets)]
            # HTML에서 <strong>필드</strong>: 또는 <b>필드</b>: 형식
            for fm in re.finditer(
                r"<(?:strong|b)>([^<]+?)</(?:strong|b)>\s*:",
                overview_html, re.IGNORECASE
            ):
                field_name = fm.group(1).strip()
                for pattern, label in BANNED_PATTERNS:
                    hit = re.search(pattern, field_name, re.IGNORECASE)
                    if hit:
                        abs_offset = body_start + fm.start()
                        line_no = text.count("\n", 0, abs_offset) + 1
                        violations.append(
                            f"{path}:{line_no} (개요 필드): 금지 토큰 '{label}' → "
                            f"\"<strong>{field_name}</strong>:\""
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
