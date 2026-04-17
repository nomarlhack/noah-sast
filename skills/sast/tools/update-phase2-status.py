#!/usr/bin/env python3
"""update-phase2-status.py — Phase 2 결과 파일의 manifest를 파싱하여 master-list.json을 갱신한다.

Usage:
    python3 update-phase2-status.py <PHASE1_RESULTS_DIR> <MASTER_LIST_JSON>

동작:
    1. PHASE1_RESULTS_DIR에서 *-phase2.md 파일을 수집
    2. 각 파일의 PHASE2 MANIFEST JSON 블록을 파싱
    3. master-list.json의 해당 후보 status를 갱신 (confirmed/safe/candidate)
    4. 갱신된 master-list.json을 덮어쓰기

종료 코드:
    0: 정상 (갱신 완료 또는 Phase 2 파일 없음, WARNING 없음)
    1: 오류 (인자 부족, master-list.json 파싱 실패, 또는 Phase 2 manifest 누락·파싱 실패로 WARNING 발생)
"""

import json, re, sys
from pathlib import Path

if len(sys.argv) < 3:
    print("Usage: python3 update-phase2-status.py <PHASE1_RESULTS_DIR> <MASTER_LIST_JSON>", file=sys.stderr)
    sys.exit(1)

phase1_dir = Path(sys.argv[1])
master_path = Path(sys.argv[2])

PHASE2_MANIFEST_RE = re.compile(
    r"<!-- NOAH-SAST PHASE2 MANIFEST v1 -->\s*```json\s*(\{.*?\})\s*```\s*<!-- /NOAH-SAST PHASE2 MANIFEST -->",
    re.S,
)

# 1. Phase 2 결과 파일 수집
phase2_files = sorted(phase1_dir.glob("*-phase2.md"))
if not phase2_files:
    print("Phase 2 결과 파일 없음 — 갱신 없이 종료")
    sys.exit(0)

# 2. master-list.json 읽기
try:
    master = json.loads(master_path.read_text(encoding="utf-8"))
except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
    print(f"ERROR: master-list.json 읽기 실패: {e}", file=sys.stderr)
    sys.exit(1)

# 후보 인덱스 구축 (id → candidate dict)
candidates = {c["id"]: c for c in master.get("candidates", [])}

# 3. Phase 2 파일 파싱 및 상태 갱신
updated = 0
errors = []

for f in phase2_files:
    try:
        text = f.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        errors.append(f"[{f.name}] 읽기 실패: {e}")
        continue

    m = PHASE2_MANIFEST_RE.search(text)
    if not m:
        errors.append(f"[{f.name}] PHASE2 MANIFEST 블록 없음")
        continue

    try:
        manifest = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        errors.append(f"[{f.name}] MANIFEST JSON 파싱 실패: {e}")
        continue

    for result in manifest.get("results", []):
        cid = result.get("id")
        status = result.get("status")
        if cid and status and cid in candidates:
            candidates[cid]["status"] = status
            if status == "confirmed":
                candidates[cid]["evidence"] = result.get("evidence", "")
            elif status == "safe":
                candidates[cid]["defense_layer"] = result.get("defense_layer", "")
                candidates[cid]["defense_detail"] = result.get("defense_detail", "")
            elif status == "candidate":
                candidates[cid]["reason"] = result.get("reason", "")
            updated += 1

# 4. 갱신된 master-list.json 저장
master["candidates"] = list(candidates.values())
master_path.write_text(json.dumps(master, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# 5. 결과 출력
print(f"Phase 2 상태 갱신 완료: {updated}건 갱신 ({len(phase2_files)}개 파일)")
if errors:
    for e in errors:
        print(f"  WARNING: {e}", file=sys.stderr)
    print(f"  {len(errors)}건 경고 — 해당 파일을 확인 후 재실행하세요", file=sys.stderr)
    sys.exit(1)
