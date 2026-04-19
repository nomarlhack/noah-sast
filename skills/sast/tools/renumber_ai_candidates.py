#!/usr/bin/env python3
"""
ai-discovery.md의 AI-PENDING-N을 AI-1, AI-2, ... 순번으로 재번호한다.

manifest JSON 내 `candidates[].id`와 prose `## AI-PENDING-N:` 헤더를 함께 갱신한다.
Idempotent — 이미 AI-1, AI-2 형태로 번호가 부여된 경우 no-op.

Usage:
  python3 renumber_ai_candidates.py <ai-discovery.md 경로>

Exit code:
  0: 재번호 완료 또는 no-op
  1: 입력 오류 (파일 부재, manifest 파싱 실패 등)
"""

import json
import re
import sys
from pathlib import Path

MANIFEST_RE = re.compile(
    r"(<!-- NOAH-SAST MANIFEST v1 -->\s*```json\s*)(\{.*?\})(\s*```\s*<!-- /NOAH-SAST MANIFEST -->)",
    re.S,
)
PENDING_HEADER_RE = re.compile(r"^## AI-PENDING-(\d+):", re.M)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: renumber_ai_candidates.py <ai-discovery.md 경로>", file=sys.stderr)
        return 1

    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"ERROR: {path} 파일 없음", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8")

    # manifest 추출
    mm = MANIFEST_RE.search(text)
    if not mm:
        print("ERROR: NOAH-SAST MANIFEST v1 블록 없음", file=sys.stderr)
        return 1
    try:
        manifest = json.loads(mm.group(2))
    except json.JSONDecodeError as e:
        print(f"ERROR: manifest JSON 파싱 실패 — {e}", file=sys.stderr)
        return 1

    cands = manifest.get("candidates", [])
    pending_ids = [c["id"] for c in cands if c.get("id", "").startswith("AI-PENDING-")]
    if not pending_ids:
        print(f"NO-OP: AI-PENDING-* ID 없음 (이미 재번호된 것으로 추정).")
        return 0

    # AI-PENDING-N을 manifest 순서대로 AI-1, AI-2, ...로 매핑
    mapping: dict[str, str] = {}
    counter = 1
    for c in cands:
        cid = c.get("id", "")
        if cid.startswith("AI-PENDING-"):
            mapping[cid] = f"AI-{counter}"
            counter += 1

    # manifest 갱신
    for c in cands:
        if c.get("id") in mapping:
            c["id"] = mapping[c["id"]]
    new_manifest_json = json.dumps(manifest, ensure_ascii=False, indent=2)
    text = text[: mm.start(2)] + new_manifest_json + text[mm.end(2) :]

    # prose 헤더 갱신
    def repl(m: re.Match) -> str:
        old_id = f"AI-PENDING-{m.group(1)}"
        new_id = mapping.get(old_id, old_id)
        return f"## {new_id}:"

    text = PENDING_HEADER_RE.sub(repl, text)

    path.write_text(text, encoding="utf-8")
    print(f"OK: {len(mapping)}개 후보 재번호 완료 — {', '.join(f'{k}→{v}' for k, v in mapping.items())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
