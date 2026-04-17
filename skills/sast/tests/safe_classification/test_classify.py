#!/usr/bin/env python3
"""safe_classification fixtures 회귀 테스트.

_classify_safe()가 각 fixture 입력에 대해 기대 카테고리를 반환하는지 검증한다.
키워드 수정/가중치 변경 시 기존 분류가 조용히 바뀌는 것을 방지.

Usage:
  python3 test_classify.py

Exit code:
  0: 전부 pass
  1: 1건 이상 실패
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SAST_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(SAST_ROOT, "sub-skills", "scan-report"))

from assemble_report import _classify_safe  # noqa: E402


def main() -> int:
    fixtures_path = os.path.join(HERE, "fixtures.json")
    with open(fixtures_path, encoding="utf-8") as f:
        fixtures = json.load(f)

    passed = 0
    failed = []

    for fix in fixtures:
        actual = _classify_safe(fix["candidate"])
        expected = fix["expected"]
        if actual == expected:
            passed += 1
        else:
            failed.append((fix["case"], expected, actual))

    total = len(fixtures)
    if failed:
        print(f"FAIL: {len(failed)}/{total} 실패, {passed}/{total} 통과", file=sys.stderr)
        for case, expected, actual in failed:
            print(f"  - {case}", file=sys.stderr)
            print(f"    expected: {expected}", file=sys.stderr)
            print(f"    actual:   {actual}", file=sys.stderr)
        return 1

    print(f"OK: {passed}/{total} 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
