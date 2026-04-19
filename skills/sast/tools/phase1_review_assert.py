#!/usr/bin/env python3
"""
Step 3-3 (동적 분석 정보 요청) 진입 가드.

phase1-review이 모든 후보에 대해 완료되었는지, eval MD 고아 상태가 없는지,
C1 lint (Phase 1 원본 직접 참조) 위반이 없는지 검증한다.

Usage:
  python3 phase1_review_assert.py <master-list.json> <phase1_results_dir>

Exit code (sub-skills/scan-report-review/_contracts.md §2 Exit Code 통일 테이블):
  0: 통과
  1: 평가 미완료 또는 eval MD 고아 상태
  5: C1 lint 실패 (Phase 1 원본 직접 참조 탐지)
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


C1_LINT_TARGETS = [
    # 보고서 조립·리뷰의 "다운스트림 소비자" 프롬프트만 검사한다.
    # - ai-discovery-agent.md: ai-discovery.md의 "생산자"이므로 제외
    # - chain-analysis/SKILL.md: master-list.json만 소비, MD 원본 참조 안 함 → 제외
    # - phase2-agent.md: Phase 2 실행 주체로서 Phase 1 원본을 합법 참조 → 제외
    "sub-skills/scan-report/SKILL.md",  # 보고서 조립은 eval MD를 참조
]

# Phase 1 원본 MD만 금지 대상으로 제한 (<scanner>-scanner.md, <scanner-name>.md, ai-discovery.md).
# 변수 플레이스홀더(<...>) 표기도 함께 검사한다.
# 연계 분석 산출물(chain-analysis.md 등)이나 master-list.json은 제외.
# 허용 경로는 별도로 C1_LINT_ALLOWED_PATTERN 에서 명시한다.
C1_LINT_BAD_PATTERN = re.compile(
    r"PHASE1_RESULTS_DIR[^\s\"'`]*/"
    r"(?:<[^>\s/]+>|[a-z0-9_-]+-scanner|ai-discovery)\.md",
    re.IGNORECASE,
)

# 의도된 허용 경로: evaluation/ 하위의 *-eval.md 참조.
# 매치된 violation 후보 중 같은 '라인'에 이 패턴이 함께 있으면 허용으로 간주한다.
C1_LINT_ALLOWED_PATTERN = re.compile(
    r"PHASE1_RESULTS_DIR[^\s\"'`]*/evaluation/[^\s\"'`]+-eval\.md",
    re.IGNORECASE,
)

# 라인에 아래 토큰이 함께 있으면 lint 제외 (의도된 fallback 참조)
C1_LINT_WHITELIST_TOKENS = ("fallback", "부재 시", "화이트리스트", "원본 fallback")


def _file_sha256(path: Path) -> str:
    if not path.is_file():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _extract_eval_md_source_hash(eval_md: Path) -> str | None:
    if not eval_md.is_file():
        return None
    text = eval_md.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<!-- SOURCE_HASH:\s*sha256:([0-9a-f]+)\s*-->", text)
    return m.group(1) if m else None


def _c1_lint(skills_root: Path) -> list[str]:
    violations: list[str] = []
    for rel in C1_LINT_TARGETS:
        target = skills_root / rel
        if not target.is_file():
            continue
        text = target.read_text(encoding="utf-8", errors="replace")
        for m in C1_LINT_BAD_PATTERN.finditer(text):
            # 화이트리스트: 같은 라인에 fallback 토큰이 있으면 의도된 참조로 제외
            line_start = text.rfind("\n", 0, m.start()) + 1
            line_end = text.find("\n", m.end())
            if line_end == -1:
                line_end = len(text)
            line = text[line_start:line_end]
            if any(tok in line for tok in C1_LINT_WHITELIST_TOKENS):
                continue
            # 허용 경로(evaluation/*-eval.md)가 같은 매치 지점이면 제외.
            # 같은 라인에 허용 경로와 금지 경로가 공존할 수 있으므로, 매치 자체가 허용 패턴에
            # 해당하는지 확인한다.
            if C1_LINT_ALLOWED_PATTERN.fullmatch(m.group(0)):
                continue
            violations.append(f"{rel}: {m.group(0)}")
    return violations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("master_list")
    parser.add_argument("phase1_dir")
    parser.add_argument(
        "--skip-lint",
        action="store_true",
        help="C1 lint를 건너뛴다 (개발 시 임시 사용).",
    )
    args = parser.parse_args()

    master_list = Path(args.master_list)
    phase1_dir = Path(args.phase1_dir)
    eval_dir = phase1_dir / "evaluation"

    with master_list.open() as f:
        m = json.load(f)
    candidates = m.get("candidates", [])
    if not candidates:
        print("FAIL: candidates 배열이 비어 있음")
        return 1

    # 1) 모든 후보에 phase1_validated 필드 존재 (하위 호환: 부재 시 false)
    missing_validated = [
        c["id"]
        for c in candidates
        if not c.get("phase1_validated")
        and c.get("status") != "safe"  # Source 도달성 폐기로 safe 처리된 건 예외
    ]
    if missing_validated:
        print(
            f"FAIL: {len(missing_validated)}개 후보의 phase1_validated=false: "
            f"{missing_validated[:10]}"
            f"{' ...' if len(missing_validated) > 10 else ''}"
        )
        print("phase1-review이 완료되지 않았거나 갱신에 실패했다.")
        return 1

    # 2) eval MD 파일 존재 + 해시 일치 (§12-G)
    orphan: list[str] = []
    hash_mismatch: list[str] = []
    for c in candidates:
        if not c.get("phase1_validated"):
            continue  # safe 분류된 건 eval MD 불요
        scanner = c.get("scanner", "")
        if not scanner:
            continue
        eval_md = eval_dir / f"{scanner}-eval.md"
        if not eval_md.is_file():
            orphan.append(c["id"])
            continue
        phase1_md = phase1_dir / f"{scanner}.md"
        if phase1_md.is_file():
            actual_hash = _file_sha256(phase1_md)
            recorded_hash = _extract_eval_md_source_hash(eval_md)
            if recorded_hash and actual_hash and recorded_hash != actual_hash:
                hash_mismatch.append(c["id"])

    if orphan:
        print(f"FAIL: {len(orphan)}개 후보의 eval MD 파일 부재(고아): {orphan[:10]}")
        return 1
    if hash_mismatch:
        print(
            f"FAIL: {len(hash_mismatch)}개 후보의 eval MD SOURCE_HASH가 Phase 1 원본과 불일치: "
            f"{hash_mismatch[:10]}"
        )
        print("Phase 1 MD가 변경되었거나 eval MD가 구버전이다. phase1-review 재호출 필요.")
        return 1

    # 3) C1 lint: Phase 1 원본 직접 참조 금지 (checklist §12-H)
    if not args.skip_lint:
        skills_root = Path(__file__).resolve().parent.parent
        violations = _c1_lint(skills_root)
        if violations:
            print(f"FAIL: C1 lint 위반 {len(violations)}건:")
            for v in violations[:20]:
                print(f"  {v}")
            print("Phase 1 원본 직접 참조 금지. evaluation/*-eval.md로 전환하라.")
            return 5

    # 통과 요약
    dist = {"SAFE": 0, "VALIDATED": 0}
    for c in candidates:
        if c.get("status") == "safe":
            dist["SAFE"] += 1
        elif c.get("phase1_validated"):
            dist["VALIDATED"] += 1
    print(
        f"OK: phase1_validated 완결, eval MD 해시 일치, C1 lint 통과. "
        f"분포 {dist}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
