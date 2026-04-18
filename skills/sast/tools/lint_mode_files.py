#!/usr/bin/env python3
"""
scan-report-review 모드 파일 구조 lint.

3모드 파일(evaluate_phase1.md / evaluate.md / review.md)이 다음 불변 속성을
유지하는지 검사한다:

1. MODE GUARD 첫 줄에 `# MODE GUARD: 이 파일은 mode=<X> 전용` 포함
2. `[STOP]` 경고 문구 존재 (잘못된 모드 진입 차단)
3. `_principles.md`와 `_contracts.md` Read 지시가 본문에 존재
4. 다른 모드 파일에 대한 리다이렉트 링크 존재

Exit code:
  0: pass
  1: lint 위반
  2: CLI 인자 오류

Usage:
  python3 lint_mode_files.py <scan-report-review-dir>
"""

import sys
from pathlib import Path

MODES = ("evaluate_phase1", "evaluate", "review")

REQUIRED_PATTERNS = {
    "mode_guard_header": "MODE GUARD: 이 파일은 mode={mode} 전용",
    "stop_phrase": "[STOP]",
    "principles_read": "_principles.md",
    "contracts_read": "_contracts.md",
}


def lint_one(path: Path, mode: str) -> list[str]:
    """한 모드 파일의 위반 목록 반환."""
    text = path.read_text(encoding="utf-8")
    violations: list[str] = []

    header = REQUIRED_PATTERNS["mode_guard_header"].format(mode=mode)
    if header not in text:
        violations.append(f"MODE GUARD 헤더 누락 또는 mode 불일치: '{header}'")

    if REQUIRED_PATTERNS["stop_phrase"] not in text:
        violations.append("[STOP] 경고 문구 누락")

    if REQUIRED_PATTERNS["principles_read"] not in text:
        violations.append("_principles.md Read 지시 누락")

    if REQUIRED_PATTERNS["contracts_read"] not in text:
        violations.append("_contracts.md Read 지시 누락")

    # 다른 모드 리다이렉트 링크
    for other in MODES:
        if other == mode:
            continue
        redirect = f"{other}.md"
        if redirect not in text:
            violations.append(f"다른 모드 리다이렉트 누락: '{redirect}'")

    return violations


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <scan-report-review-dir>", file=sys.stderr)
        return 2

    base = Path(sys.argv[1])
    if not base.is_dir():
        print(f"디렉토리 아님: {base}", file=sys.stderr)
        return 2

    all_violations: dict[str, list[str]] = {}
    for mode in MODES:
        path = base / f"{mode}.md"
        if not path.exists():
            all_violations[mode] = [f"파일 부재: {path}"]
            continue
        v = lint_one(path, mode)
        if v:
            all_violations[mode] = v

    if all_violations:
        print("FAIL: 모드 파일 구조 위반")
        for mode, vs in all_violations.items():
            print(f"  [{mode}.md]")
            for v in vs:
                print(f"    - {v}")
        return 1

    print(f"OK: {len(MODES)}개 모드 파일 구조 정합")
    return 0


if __name__ == "__main__":
    sys.exit(main())
