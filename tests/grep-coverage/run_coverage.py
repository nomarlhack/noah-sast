#!/usr/bin/env python3
"""run_coverage.py — 각 스캐너의 grep 패턴이 알려진 취약 코드 샘플을 감지하는지 검증.

Usage:
    python3 run_coverage.py [NOAH_SAST_DIR]

기본값: 스크립트 위치 기준 ../../ (noah-sast 루트)

동작:
1. 각 스캐너 phase1.md에서 grep_patterns를 추출
2. fixtures/<scanner>/must_hit.txt의 각 코드 라인에 대해 패턴 매칭
3. 히트되지 않은 라인을 MISS로 보고
4. 스캐너별 커버리지 리포트 출력

Exit code: MISS가 1건이라도 있으면 1, 없으면 0
"""
import os
import re
import sys
import yaml
from pathlib import Path

# --- 경로 설정 ---
if len(sys.argv) > 1:
    NOAH_SAST_DIR = Path(sys.argv[1])
else:
    NOAH_SAST_DIR = Path(__file__).resolve().parent.parent.parent

SCANNERS_DIR = NOAH_SAST_DIR / "scanners"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.S)


def extract_patterns(phase1_path):
    """phase1.md frontmatter에서 grep_patterns 리스트 추출."""
    text = phase1_path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return []
    try:
        fm = yaml.safe_load(m.group(1))
    except Exception:
        # yaml 모듈 없을 경우 간이 파서
        return _parse_patterns_simple(m.group(1))
    if not fm or "grep_patterns" not in fm:
        return []
    return fm["grep_patterns"] or []


def _parse_patterns_simple(yaml_text):
    """yaml 라이브러리 없을 때 간이 추출."""
    patterns = []
    for line in yaml_text.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            pat = line[2:].strip().strip('"').strip("'")
            if pat:
                patterns.append(pat)
    return patterns


def test_scanner(scanner_name, patterns):
    """fixtures/<scanner>/must_hit.txt의 각 라인에 대해 패턴 매칭 테스트."""
    fixture_dir = FIXTURES_DIR / scanner_name
    must_hit_file = fixture_dir / "must_hit.txt"

    if not must_hit_file.exists():
        return None, None, None  # fixture 없음

    lines = must_hit_file.read_text(encoding="utf-8").splitlines()
    hits = []
    misses = []

    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        matched = False
        for pat in patterns:
            try:
                if re.search(pat, line):
                    matched = True
                    break
            except re.error:
                # grep 패턴이 Python regex로 유효하지 않을 수 있음 (괄호 불일치 등)
                # 간이 문자열 매칭 fallback: regex 이스케이프를 모두 제거
                plain = pat
                for esc in ["\\s*", "\\s+", "\\(", "\\)", "\\.", "\\b", "\\[", "\\]"]:
                    plain = plain.replace(esc, esc[-1] if len(esc) == 2 else "")
                # \. → . 변환
                plain = plain.replace("\\.", ".")
                if plain in line:
                    matched = True
                    break

        if matched:
            hits.append((i, line))
        else:
            misses.append((i, line))

    return lines, hits, misses


def main():
    total_scanners = 0
    total_tested = 0
    total_hits = 0
    total_misses = 0
    all_misses = []

    scanner_dirs = sorted(SCANNERS_DIR.iterdir())

    for sd in scanner_dirs:
        if not sd.is_dir():
            continue
        scanner_name = sd.name
        phase1 = sd / "phase1.md"
        if not phase1.exists():
            continue

        total_scanners += 1
        patterns = extract_patterns(phase1)

        if not patterns:
            # grep-less 스캐너 (business-logic 등)
            continue

        lines, hits, misses = test_scanner(scanner_name, patterns)
        if lines is None:
            continue  # fixture 없음

        total_tested += 1
        total_hits += len(hits)
        total_misses += len(misses)

        code_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
        coverage = len(hits) / len(code_lines) * 100 if code_lines else 0

        status = "✅ PASS" if not misses else "❌ MISS"
        print(f"{status} {scanner_name}: {len(hits)}/{len(code_lines)} ({coverage:.0f}%)")

        if misses:
            for line_no, line_text in misses:
                print(f"  MISS line {line_no}: {line_text}")
                all_misses.append((scanner_name, line_no, line_text))

    print()
    print("=" * 60)
    print(f"스캐너: {total_scanners}개 / fixture 있음: {total_tested}개")
    print(f"총 히트: {total_hits}건 / 총 미스: {total_misses}건")

    if total_tested == 0:
        print("\nWARNING: fixture가 없습니다. tests/grep-coverage/fixtures/<scanner>/must_hit.txt를 추가하세요.")
        return 0

    if all_misses:
        print(f"\n*** {len(all_misses)} MISS(es) detected ***")
        return 1
    else:
        print("\n모든 패턴 커버리지 테스트 통과!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
