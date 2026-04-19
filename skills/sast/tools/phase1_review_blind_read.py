#!/usr/bin/env python3
"""
phase1_review_blind_read.py — phase1-review 전용 헬퍼.

Phase 1 결과 MD를 읽어 Phase 1 평가자의 구조적 판정 단서를 마스킹한 뷰를 반환한다.
이는 blind eval의 목적인 "확증 편향 완화"를 위한 전처리이다.

Usage:
    python3 phase1_review_blind_read.py <phase1_md_path>   # 마스킹 뷰를 stdout에 출력

Mask 대상 (sub-skills/scan-report-review/phase1-review.md §blind eval 메커니즘):
    - "### Decision"
    - "### Confidence"
    - "### 판정 요약"
    - "### Status"

완전 blind는 자연어 누설 때문에 원리적으로 불가능. 마스킹은 구조적 단서 제거만 수행.
"""

import re
import sys
from pathlib import Path

MASK_PATTERNS = [
    r"### Decision\s*\n.*?(?=\n###|\n##|\Z)",
    r"### Confidence\s*\n.*?(?=\n###|\n##|\Z)",
    r"### 판정 요약\s*\n.*?(?=\n###|\n##|\Z)",
    r"### Status\s*\n.*?(?=\n###|\n##|\Z)",
]

MASK_REPLACEMENT = "<MASKED until independent judgment>\n"


def blind_read(md_path: str) -> str:
    content = Path(md_path).read_text(encoding="utf-8")
    masked = content
    for pat in MASK_PATTERNS:
        masked = re.sub(
            pat,
            lambda m: m.group(0).split("\n", 1)[0] + "\n" + MASK_REPLACEMENT,
            masked,
            flags=re.DOTALL,
        )
    return masked


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: phase1_review_blind_read.py <phase1_md_path>", file=sys.stderr)
        sys.exit(1)
    sys.stdout.write(blind_read(sys.argv[1]))
