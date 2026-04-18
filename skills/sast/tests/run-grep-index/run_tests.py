#!/usr/bin/env python3
"""
run_grep_index.py 합성 fixture 회귀 테스트.

각 case 디렉토리 구조:
  case_XX_name/
    scanners/<scanner-name>/phase1.md
    project/<소스 코드>
    expected.json

실행 흐름:
  1. tmp 출력 디렉토리 생성
  2. run_grep_index.py 실행 (--scanners-dir, --project-root, --out-dir)
  3. expected.json과 실제 생성 JSON 비교
  4. expected.json에 expect_failures=true면 _failures.json 존재 및 reason 검증

grep 출력은 절대경로로 나오므로 project_root 접두사 제거 후 비교.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


FIXTURES_DIR = Path(__file__).parent / "fixtures"
SCRIPT_PATH = Path(__file__).parent.parent.parent / "tools" / "run_grep_index.py"


def relativize(matches: list[str], project_root: Path) -> list[str]:
    """grep 절대경로:line → project 상대경로:line 변환."""
    prefix = str(project_root.resolve()) + "/"
    result = []
    for m in matches:
        if m.startswith(prefix):
            result.append(m[len(prefix):])
        else:
            result.append(m)
    return sorted(result)


def compare_matches(actual: list[str], expected: list[str]) -> tuple[bool, str]:
    a_sorted = sorted(actual)
    e_sorted = sorted(expected)
    if a_sorted == e_sorted:
        return True, ""
    return False, f"\n    expected: {e_sorted}\n    actual:   {a_sorted}"


def run_case(case_dir: Path) -> tuple[bool, list[str]]:
    """단일 case 실행. (성공여부, 에러메시지리스트) 반환."""
    name = case_dir.name
    scanners_dir = case_dir / "scanners"
    project_root = case_dir / "project"
    expected_path = case_dir / "expected.json"

    if not scanners_dir.is_dir() or not project_root.is_dir() or not expected_path.is_file():
        return False, [f"{name}: fixture 구조 오류 (scanners/, project/, expected.json 필요)"]

    with open(expected_path, encoding="utf-8") as f:
        expected = json.load(f)

    errors: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp)
        result = subprocess.run(
            [
                sys.executable, str(SCRIPT_PATH),
                "--scanners-dir", str(scanners_dir),
                "--project-root", str(project_root),
                "--out-dir", str(out_dir),
            ],
            capture_output=True, text=True,
        )

        expect_failures = expected.get("expect_failures", False)
        if expect_failures and result.returncode != 2:
            errors.append(
                f"{name}: exit code 기대 2 (부분 실패), 실제 {result.returncode}\n"
                f"  stderr: {result.stderr}"
            )
        elif not expect_failures and result.returncode != 0:
            errors.append(
                f"{name}: exit code 기대 0 (성공), 실제 {result.returncode}\n"
                f"  stderr: {result.stderr}"
            )

        # 각 스캐너별 JSON 비교
        for scanner_name, spec in expected.items():
            if scanner_name in ("expect_failures", "expected_failure_reasons"):
                continue
            json_path = out_dir / f"{scanner_name}.json"
            if not json_path.exists():
                errors.append(f"{name}/{scanner_name}: JSON 파일이 생성되지 않음")
                continue
            with open(json_path, encoding="utf-8") as f:
                actual_data = json.load(f)
            expected_matches = spec.get("matches_by_pattern", {})

            if set(actual_data.keys()) != set(expected_matches.keys()):
                errors.append(
                    f"{name}/{scanner_name}: 패턴 키 불일치\n"
                    f"    expected: {sorted(expected_matches.keys())}\n"
                    f"    actual:   {sorted(actual_data.keys())}"
                )
                continue

            for pattern, expected_m in expected_matches.items():
                actual_m = relativize(actual_data[pattern], project_root)
                ok, msg = compare_matches(actual_m, expected_m)
                if not ok:
                    errors.append(f"{name}/{scanner_name}/'{pattern}': 매치 불일치{msg}")

        # _failures.json 검증
        failures_path = out_dir / "_failures.json"
        if expect_failures:
            if not failures_path.exists():
                errors.append(f"{name}: _failures.json이 생성되어야 함 (expect_failures=true)")
            else:
                with open(failures_path, encoding="utf-8") as f:
                    failures_data = json.load(f)
                expected_reasons = expected.get("expected_failure_reasons", {})
                for scanner_name, reasons in expected_reasons.items():
                    if scanner_name not in failures_data:
                        errors.append(
                            f"{name}: _failures.json에 '{scanner_name}' 누락"
                        )
                        continue
                    actual_reasons = [e["reason"] for e in failures_data[scanner_name]]
                    for r in reasons:
                        if r not in actual_reasons:
                            errors.append(
                                f"{name}/{scanner_name}: 기대 실패 사유 '{r}' 없음 (실제: {actual_reasons})"
                            )
        else:
            if failures_path.exists():
                errors.append(f"{name}: _failures.json이 생성되면 안 됨 (expect_failures=false)")

    return (len(errors) == 0, errors)


def main() -> int:
    cases = sorted(p for p in FIXTURES_DIR.iterdir() if p.is_dir())
    if not cases:
        print("ERROR: fixtures/ 아래 case 디렉토리가 없음")
        return 1

    total_failures = 0
    for case_dir in cases:
        ok, errors = run_case(case_dir)
        if ok:
            print(f"PASS: {case_dir.name}")
        else:
            print(f"FAIL: {case_dir.name}")
            for e in errors:
                print(f"  {e}")
            total_failures += 1

    print()
    print(f"결과: {len(cases) - total_failures}/{len(cases)} 통과")
    return 0 if total_failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
