#!/usr/bin/env python3
"""
Phase 1 결과 파일(markdown + manifest)에서 후보 메타데이터를 추출하여
master-list.json을 생성한다.

Usage: build-master-list.py <phase1_dir> <output_json>

검증 기능:
- manifest JSON 파싱 실패 시 ERROR
- manifest declared_count와 실제 candidates 수 불일치 시 ERROR
- manifest ID와 prose ## <ID>: 헤더 불일치 시 ERROR
- 필수 섹션(Code, Source→Sink Flow 등) 누락/빈약 시 WARNING
- 동일 file:line 후보 자동 그룹핑 (DUPLICATE SINK)
"""
import re
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

if len(sys.argv) < 3:
    print("Usage: python3 build-master-list.py <PHASE1_RESULTS_DIR> <OUTPUT_JSON>", file=sys.stderr)
    sys.exit(1)

phase1_dir = Path(sys.argv[1])
out_path = Path(sys.argv[2])

MANIFEST_RE = re.compile(
    r"<!-- NOAH-SAST MANIFEST v1 -->\s*```json\s*(\{.*?\})\s*```\s*<!-- /NOAH-SAST MANIFEST -->",
    re.S,
)
CANDIDATE_HEADER_RE = re.compile(r"^## ([A-Z]{2,}[A-Z0-9]*-\d+):\s*", re.M)

# Source→Sink Flow / Vulnerability Flow 섹션이 선택적인 스캐너 (설정/구성 기반)
FLOW_OPTIONAL_SCANNERS = {
    "business-logic-scanner",
    "validation-logic-scanner",
    "security-headers-scanner",
    "cookie-security-scanner",
    "springboot-hardening-scanner",
    "tls-scanner",
}

REQUIRED_SECTIONS = [
    ("### Code", 20),
    ("### Source→Sink Flow|### Vulnerability Flow", 50),
    ("### Validation Logic", 80),
    ("### Trigger Conditions", 80),
    ("### Decision", 40),
]

errors = []
warnings = []
candidates = []
clean_scanners = []
skipped_scanners = []

md_files = sorted(f for f in phase1_dir.glob("*.md") if not f.stem.endswith("-phase2"))
if not md_files:
    print(f"ERROR: No .md files found in {phase1_dir}")
    sys.exit(1)

for md in md_files:
    try:
        text = md.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        errors.append(f"[{md.stem}] 파일 읽기 실패: {e}")
        continue
    scanner = md.stem

    # 1. Manifest 추출
    m = MANIFEST_RE.search(text)
    if not m:
        errors.append(f"{scanner}: NO_MANIFEST — manifest 블록이 파일에 없음")
        continue
    try:
        manifest = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        errors.append(f"{scanner}: INVALID_JSON — {e}")
        continue

    declared = manifest.get("declared_count", -1)
    cands = manifest.get("candidates", [])

    # 2. declared_count vs actual count
    if declared != len(cands):
        errors.append(
            f"{scanner}: COUNT_MISMATCH — declared {declared} but manifest has {len(cands)} candidates"
        )
        continue

    if declared == 0:
        clean_scanners.append(scanner)
        continue

    # 3. 각 후보: manifest ID ↔ prose header 대조 + 섹션 품질 검증
    prose_ids = set(CANDIDATE_HEADER_RE.findall(text))

    for cand in cands:
        cid = cand.get("id", "UNKNOWN")

        # manifest ID가 prose에도 있는지
        if cid not in prose_ids:
            errors.append(
                f"{scanner}/{cid}: NO_PROSE_SECTION — manifest에는 있으나 ## {cid}: 헤더가 파일에 없음"
            )
            continue

        # 해당 후보의 prose 섹션 추출
        sect_start_re = re.compile(rf"^## {re.escape(cid)}:\s*(.+?)$", re.M)
        h = sect_start_re.search(text)
        if not h:
            errors.append(f"{scanner}/{cid}: HEADER_PARSE_FAIL")
            continue

        # 다음 ## 또는 manifest 시작까지
        next_h = re.search(r"^## ", text[h.end() :], re.M)
        mf_start = text.find("<!-- NOAH-SAST MANIFEST v1 -->")
        end = h.end() + (next_h.start() if next_h else len(text) - h.end())
        if 0 < mf_start < end:
            end = mf_start
        section = text[h.end() : end]

        # 필수 섹션 품질 검증
        for sub_name, min_len in REQUIRED_SECTIONS:
            # 복수 헤더 허용 ("|"로 구분)
            sub_headers = sub_name.split("|")
            sub_header_pattern = "|".join(re.escape(h) for h in sub_headers)
            sub_re = re.compile(
                rf"^(?:{sub_header_pattern})\s*\n(.*?)(?=^### |\Z)", re.M | re.S
            )
            sm = sub_re.search(section)
            if not sm:
                # 설정 기반 스캐너에서 Source→Sink Flow/Vulnerability Flow 누락은 정상
                is_flow_section = "Source→Sink Flow" in sub_name or "Vulnerability Flow" in sub_name
                if is_flow_section and scanner in FLOW_OPTIONAL_SCANNERS:
                    pass  # 경고 생략
                else:
                    warnings.append(f"{scanner}/{cid}: MISSING_SECTION:{sub_headers[0]}")
            elif len(sm.group(1).strip()) < min_len:
                warnings.append(
                    f"{scanner}/{cid}: SHORT_SECTION:{sub_headers[0]} ({len(sm.group(1).strip())} chars < {min_len})"
                )

        candidates.append(
            {
                "id": cid,
                "scanner": scanner,
                "title": cand.get("title", ""),
                "file": cand.get("file"),
                "line": cand.get("line"),
                "url_path": cand.get("url_path"),
                "source": cand.get("source"),
                "sink": cand.get("sink"),
                "test_prereq": cand.get("test_prereq"),
                "phase1_path": str(md),
                "status": "candidate",
            }
        )

    # prose에는 있으나 manifest에 없는 ID
    manifest_ids = {c.get("id") for c in cands}
    orphan_ids = prose_ids - manifest_ids
    for oid in orphan_ids:
        errors.append(
            f"{scanner}/{oid}: ORPHAN_PROSE — ## {oid}: 헤더가 있으나 manifest에 없음"
        )

# 4. 동일 file:line 후보 그룹핑 (dedup 힌트)
from collections import defaultdict

loc_groups = defaultdict(list)
for c in candidates:
    if c["file"] and c["line"]:
        loc_groups[(c["file"], c["line"])].append(c["id"])
duplicates = {loc: ids for loc, ids in loc_groups.items() if len(ids) > 1}

# 5. master-list.json 출력
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(
    json.dumps(
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "candidates": candidates,
            "clean_scanners": sorted(clean_scanners),
        },
        indent=2,
        ensure_ascii=False,
    )
)

# 6. stdout 출력
if errors:
    for e in errors:
        print(f"ERROR: {e}")

if warnings:
    for w in warnings:
        print(f"WARNING: {w}")

if duplicates:
    for loc, ids in duplicates.items():
        print(f"DUPLICATE SINK at {loc[0]}:{loc[1]}: {', '.join(ids)}")

print(
    f"\nMaster list: {len(candidates)} candidates / {len(clean_scanners)} clean"
)
for c in candidates:
    print(f"- {c['id']}: {c['title']} @ {c['file']}:{c['line']}")

if errors:
    print(f"\n*** {len(errors)} ERROR(s) detected — 메인 에이전트는 해당 스캐너를 재실행해야 합니다 ***")
    sys.exit(1)
if warnings:
    print(f"\n*** {len(warnings)} WARNING(s) detected — 해당 후보의 파일 품질을 확인하세요 ***")
