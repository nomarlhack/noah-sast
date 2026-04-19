#!/usr/bin/env python3
"""
Phase 1 재개 판별 스크립트.

중단된 Phase 1 파이프라인(Step 5 스캐너 그룹 + Step 6 AI 자율 탐색)을
재개할 때, 파일 시스템 상태를 판별하여 어떤 스캐너를 재dispatch해야 하는지
결정한다. 메인 에이전트가 수동 판단 없이 이 스크립트 출력만 따라 재개한다.

Usage:
  python3 phase1_resume.py <PHASE1_RESULTS_DIR>

판별 대상:
  - _expected_scanners.json (select_scanners.py 산출)
  - <PHASE1_RESULTS_DIR>/*-scanner.md (Phase 1 결과)
  - <PHASE1_RESULTS_DIR>/ai-discovery.md (AI 자율 탐색 결과)
  - <PHASE1_RESULTS_DIR>/ai-discovery-continued.md (INCOMPLETE 후속)
  - <PHASE1_RESULTS_DIR>/master-list.json (빌드 결과)

Exit code:
  0: 판별 완료. 재개 동작은 RECOMMENDED 섹션 참조.
  1: 입력 오류 (PHASE1_RESULTS_DIR 부재, _expected_scanners.json 부재 등).
"""

import json
import re
import sys
from pathlib import Path

MANIFEST_RE = re.compile(
    r"<!-- NOAH-SAST MANIFEST v1 -->\s*```json\s*(\{.*?\})\s*```\s*<!-- /NOAH-SAST MANIFEST -->",
    re.S,
)
CANDIDATE_HEADER_RE = re.compile(r"^## ([A-Z][A-Z0-9]*-\d+):\s*", re.M)


def classify_scanner_file(path: Path) -> tuple[str, str]:
    """scanner MD 파일 상태를 (category, detail) 튜플로 분류.
    category: complete | invalid
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        return ("invalid", f"READ_FAIL: {e}")

    m = MANIFEST_RE.search(text)
    if not m:
        return ("invalid", "NO_MANIFEST")
    try:
        manifest = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        return ("invalid", f"INVALID_JSON: {e}")

    declared = manifest.get("declared_count", -1)
    cands = manifest.get("candidates", [])
    if declared != len(cands):
        return ("invalid", f"COUNT_MISMATCH: declared={declared} actual={len(cands)}")

    prose_ids = set(CANDIDATE_HEADER_RE.findall(text))
    manifest_ids = {c.get("id") for c in cands}
    if manifest_ids - prose_ids:
        return ("invalid", f"NO_PROSE_SECTION: {sorted(manifest_ids - prose_ids)}")
    if prose_ids - manifest_ids:
        return ("invalid", f"ORPHAN_PROSE: {sorted(prose_ids - manifest_ids)}")

    return ("complete", f"{declared} candidates")


def classify_ai_discovery(path: Path) -> tuple[str, dict]:
    """ai-discovery.md 상태를 (status, details) 튜플로 분류.
    status: not_started | invalid | incomplete | complete
    """
    if not path.is_file():
        return ("not_started", {})
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        return ("invalid", {"reason": f"READ_FAIL: {e}"})

    m = MANIFEST_RE.search(text)
    if not m:
        return ("invalid", {"reason": "NO_MANIFEST"})
    try:
        manifest = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        return ("invalid", {"reason": f"INVALID_JSON: {e}"})

    status = manifest.get("exploration_status")
    declared = manifest.get("declared_count", 0)
    if status == "incomplete":
        return ("incomplete", {"declared_count": declared})
    return ("complete", {"declared_count": declared})


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: phase1_resume.py <PHASE1_RESULTS_DIR>", file=sys.stderr)
        return 1

    phase1_dir = Path(sys.argv[1])
    if not phase1_dir.is_dir():
        print(f"ERROR: {phase1_dir} 디렉토리 없음", file=sys.stderr)
        return 1

    expected_file = phase1_dir / "_expected_scanners.json"
    if not expected_file.is_file():
        print(f"STATE: pre_expected")
        print(f"ACTION: select_scanners.py 미실행. Step 4-1부터 재시작.")
        return 0

    try:
        expected = set(json.loads(expected_file.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError) as e:
        print(f"ERROR: _expected_scanners.json 파싱 실패 — {e}", file=sys.stderr)
        return 1

    scanner_files = sorted(
        f for f in phase1_dir.glob("*-scanner.md")
        if not f.stem.endswith("-phase2")
    )
    actual_stems = {f.stem for f in scanner_files}

    completed: list[tuple[str, str]] = []
    invalid: list[tuple[str, str]] = []
    for f in scanner_files:
        category, detail = classify_scanner_file(f)
        if category == "complete":
            completed.append((f.stem, detail))
        else:
            invalid.append((f.stem, detail))

    missing = sorted(expected - actual_stems)
    redispatch = sorted({s for s, _ in invalid} | set(missing))

    ai_path = phase1_dir / "ai-discovery.md"
    ai_continued_path = phase1_dir / "ai-discovery-continued.md"
    ai_status, ai_details = classify_ai_discovery(ai_path)

    ai_action = None
    if ai_status == "not_started":
        ai_action = "dispatch"
    elif ai_status == "invalid":
        ai_action = "redispatch (파일 손상)"
    elif ai_status == "incomplete":
        if ai_continued_path.is_file():
            cont_status, _ = classify_ai_discovery(ai_continued_path)
            if cont_status in ("complete", "incomplete"):
                ai_action = "merge (ai-discovery.md + ai-discovery-continued.md)"
            else:
                ai_action = "redispatch-continued (continued 파일 손상)"
        else:
            ai_action = "dispatch-continued"

    master_list_path = phase1_dir / "master-list.json"
    master_stale = False
    if master_list_path.is_file() and not redispatch and ai_action is None:
        try:
            ml = json.loads(master_list_path.read_text(encoding="utf-8"))
            ml_scanners = {c.get("scanner") for c in ml.get("candidates", [])}
            ml_scanners.discard(None)
            complete_scanners = {s for s, _ in completed}
            if ai_path.is_file():
                complete_scanners.add("ai-discovery")
            ml_scanners_non_clean = ml_scanners | set(ml.get("clean_scanners", []))
            if complete_scanners - ml_scanners_non_clean:
                master_stale = True
        except (json.JSONDecodeError, OSError):
            master_stale = True

    if completed and not redispatch and ai_action is None:
        state = "complete" if not master_stale else "master_list_stale"
    elif not completed and not redispatch and ai_action == "dispatch":
        state = "initial"
    else:
        state = "partial"

    print(f"STATE: {state}")
    print()
    print("SCANNERS:")
    if completed:
        print("  completed:")
        for name, detail in completed:
            print(f"    - {name} ({detail})")
    if invalid:
        print("  invalid:")
        for name, detail in invalid:
            print(f"    - {name} ({detail})")
    if missing:
        print("  missing:")
        for name in missing:
            print(f"    - {name}")
    print()
    print(f"AI_DISCOVERY:")
    print(f"  status: {ai_status}")
    if ai_details:
        for k, v in ai_details.items():
            print(f"  {k}: {v}")
    if ai_continued_path.is_file():
        print(f"  continued_file: present")
    print()
    print(f"MASTER_LIST:")
    print(f"  exists: {master_list_path.is_file()}")
    print(f"  stale: {master_stale}")
    print()
    print("RECOMMENDED:")
    step = 1
    if not completed and not invalid and not missing:
        print(f"  {step}. select_scanners.py 재실행하여 그룹 편성 복구 후 전체 dispatch")
        step += 1
    elif redispatch:
        print(
            f"  {step}. phase1-group-agent 재dispatch: 남은 스캐너 {redispatch}. "
            "원 그룹 편성이 컨텍스트에 없으면 select_scanners.py 재실행하여 편성 복구"
        )
        step += 1
    if ai_action:
        print(f"  {step}. ai-discovery: {ai_action}")
        step += 1
    if state != "initial" and (redispatch or ai_action or master_stale):
        print(f"  {step}. phase1_build_master_list.py 재실행")
        step += 1
    if state == "complete":
        print(f"  (진행 필요 없음 — Phase 1 완료. Step 7로 진행)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
