#!/usr/bin/env python3
"""
lint_reader_layer.py — 보고서 MD/HTML의 헤딩 및 개요 필드 검증.

vuln-format.md를 단일 진실 원천으로 사용한다. 두 가지 검증:

1. **헤딩 검사** (h1~h6): checklist.md의 내부 규약 용어(BANNED_PATTERNS)가
   헤딩 텍스트에 노출되지 않았는지 검사. 정규식 블랙리스트 방식.

2. **개요 필드 검사**: 보고서 최상단 개요 블록의 `**필드명**:` 라인을
   vuln-format.md의 "통합 보고서 구조" 섹션에서 파싱한 **허용 필드 집합**과
   대조. 블랙리스트 없이 단일 출처 화이트리스트로 검증하므로 필드 이름이
   단어 변형을 거쳐도 스펙에 없으면 차단된다.

   - 신규 필드가 필요하면 vuln-format.md의 "통합 보고서 구조" 코드 블록을
     먼저 갱신. lint가 다음 실행 시 자동 반영.
   - 스펙 파일을 찾지 못하면 개요 검사는 스킵 (헤딩 검사만 수행).

Exit code:
  0: pass
  5: lint 위반 (헤딩 금지 토큰 또는 스펙 외 개요 필드)
  1: CLI 인자 오류

Usage:
  python3 lint_reader_layer.py <report.md> [<report.html>]
"""

import os
import re
import sys

# 금지 토큰 정규식 (헤딩 한정 — checklist.md 내부 규약 용어 차단용)
# 개요 필드명은 블랙리스트가 아니라 vuln-format.md 스펙 기반 화이트리스트로 검사한다.
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

# 개요 필드 패턴: **필드명**: 값 — 필드명만 검사 대상
MD_OVERVIEW_FIELD = re.compile(r"^\*\*([^*]+?)\*\*\s*:\s*(.+)$", re.MULTILINE)


def _load_allowed_overview_fields():
    """vuln-format.md의 '통합 보고서 구조' 섹션에서 허용 필드 목록 추출.

    반환: 허용 필드 이름 리스트 (순서 유지), 스펙 파싱 실패 시 None.
    스펙 파일 경로는 본 스크립트 기준 상대 경로 resolve.
    """
    spec_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "sub-skills", "scan-report", "vuln-format.md"
    )
    if not os.path.isfile(spec_path):
        return None
    text = open(spec_path, encoding="utf-8").read()
    # "## 통합 보고서 구조" 헤딩 직후 첫 ```markdown 코드 블록 추출
    m = re.search(
        r"##\s+통합\s*보고서\s*구조\s*\n\s*```markdown\s*\n(.*?)\n```",
        text, re.DOTALL
    )
    if not m:
        return None
    block = m.group(1)
    fields = re.findall(r"^\*\*([^*]+?)\*\*\s*:", block, re.MULTILINE)
    return [f.strip() for f in fields]


# 모듈 로드 시 1회만 스펙 파싱 (단일 진실 원천)
ALLOWED_OVERVIEW_FIELDS = _load_allowed_overview_fields()


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

    # 2. 개요 섹션 필드명 검사
    # vuln-format.md 스펙에서 파싱한 허용 집합과 대조 (단일 진실 원천).
    # 단어 변형(예: '파이프 구성', '스캔 단계')에도 강건 — 스펙에 없는 필드는 무조건 차단.
    overview_block, overview_start_line = _extract_overview_block(text)
    if overview_block and ALLOWED_OVERVIEW_FIELDS is not None:
        allowed = {f for f in ALLOWED_OVERVIEW_FIELDS}
        for fm in MD_OVERVIEW_FIELD.finditer(overview_block):
            field_name = fm.group(1).strip()
            if field_name in allowed:
                continue
            rel_line = overview_block.count("\n", 0, fm.start()) + 1
            abs_line = overview_start_line + rel_line
            violations.append(
                f"{path}:{abs_line} (개요 필드): 스펙 외 필드 '**{field_name}**:' — "
                f"허용 필드는 vuln-format.md '통합 보고서 구조' 섹션 참조 "
                f"(현재 허용: {ALLOWED_OVERVIEW_FIELDS})"
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
    # vuln-format.md 스펙 기반 화이트리스트 대조
    if ALLOWED_OVERVIEW_FIELDS is not None:
        allowed = {f for f in ALLOWED_OVERVIEW_FIELDS}
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
                    if field_name in allowed:
                        continue
                    abs_offset = body_start + fm.start()
                    line_no = text.count("\n", 0, abs_offset) + 1
                    violations.append(
                        f"{path}:{line_no} (개요 필드): 스펙 외 필드 "
                        f"'<strong>{field_name}</strong>:' — "
                        f"허용 필드는 vuln-format.md '통합 보고서 구조' 섹션 참조 "
                        f"(현재 허용: {ALLOWED_OVERVIEW_FIELDS})"
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
            "\n검사 범위:\n"
            "  1) 헤딩(# ~ ######): checklist.md 내부 규약 용어 차단 — 본문·테이블은 풀이 형태로 허용.\n"
            "  2) 개요 필드명: vuln-format.md '통합 보고서 구조' 스펙 단일 출처 기반 화이트리스트.\n"
            "     신규 필드가 필요하면 먼저 vuln-format.md 스펙을 갱신하세요.",
            file=sys.stderr,
        )
        return 5  # §13 exit code table: 5 = lint 위반

    print(f"OK: lint 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
