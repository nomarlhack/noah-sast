#!/usr/bin/env python3
"""
Step 3-6 (연계 분석) 진입 가드.

모든 후보가 status 필드를 가지는지, mode=evaluate 완료 이후에 연계 분석이
실행되는지, §10-A 교차 검증 결과(reopen·requires_human_review)가 해소됐는지
런타임 assert한다.

Usage:
  python3 assert_status_complete.py <master-list.json> <phase1_results_dir>
                                    [--accept-human-review=ID1,ID2,...]

Exit code (checklist.md §13 통일 테이블):
  0: 통과
  1: incomplete / invalid state (status 미완결, enum 위반 등)
  2: human_review_block — 명시 승인 필요
  3: rederivation_warn — 비차단 경고
  4: reopen_pending — evaluate_phase1 재호출 필요
"""

import argparse
import json
import os
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("master_list")
    parser.add_argument("phase1_dir")
    parser.add_argument(
        "--accept-human-review",
        default="",
        help="쉼표로 구분된 후보 ID 목록. 'all'은 금지.",
    )
    args = parser.parse_args()

    master_list_path = args.master_list
    phase1_results_dir = args.phase1_dir

    with open(master_list_path) as f:
        m = json.load(f)

    candidates = m.get("candidates", [])
    if not candidates:
        print("FAIL: candidates 배열이 비어 있음")
        return 1

    # 1. 모든 후보가 status 필드를 가지는가
    missing = [
        c["id"] for c in candidates
        if "status" not in c or c["status"] is None or c["status"] == ""
    ]
    if missing:
        print(
            f"FAIL: {len(missing)}개 후보가 status 없음: {missing[:10]}"
            f"{' …' if len(missing) > 10 else ''}"
        )
        print("mode=evaluate가 완료되지 않았거나 갱신에 실패했다.")
        return 1

    # 2. status 값이 enum에 속하는가
    allowed = {"confirmed", "candidate", "safe"}
    invalid = [
        (c["id"], c["status"]) for c in candidates
        if c["status"] not in allowed
    ]
    if invalid:
        print(f"FAIL: 비정형 status 값: {invalid[:5]}")
        return 1

    # 3. candidate 판정은 tag 필드 필수
    cand_no_tag = [
        c["id"] for c in candidates
        if c["status"] == "candidate"
        and (c.get("tag") is None or c.get("tag") == "")
    ]
    if cand_no_tag:
        print(
            f"FAIL: {len(cand_no_tag)}개 candidate가 tag 없음: "
            f"{cand_no_tag[:5]}"
        )
        print("checklist.md §10 매트릭스 위반.")
        return 1

    # 4. master-list.json의 mtime이 Phase 2 파일보다 나중인가
    master_mtime = os.path.getmtime(master_list_path)
    phase2_files = list(Path(phase1_results_dir).glob("*-phase2.md"))
    if phase2_files:
        latest_phase2 = max(os.path.getmtime(p) for p in phase2_files)
        if master_mtime < latest_phase2:
            print(
                f"FAIL: master-list.json mtime({master_mtime})이 "
                f"Phase 2 파일({latest_phase2})보다 이르다."
            )
            print("evaluate 단계가 Phase 2보다 먼저 실행되었거나 누락되었다.")
            return 1

    # 5. reopen_pending 체크 — exit 4
    #    evaluate가 §10-A 교차 검증에서 모순 발견 후 reopen=true 세팅한 후보가 있으면
    #    evaluate_phase1 재호출 필요.
    reopen_pending = [
        c["id"] for c in candidates
        if c.get("phase1_eval_state", {}).get("reopen")
    ]
    if reopen_pending:
        print(
            f"BLOCK: {len(reopen_pending)}개 후보가 reopen_pending: {reopen_pending[:10]}"
        )
        print("evaluate_phase1 재호출이 필요. SKILL.md 'reopen 재호출 원자성' 절차 수행.")
        return 4

    # 6. requires_human_review 체크 — exit 2
    human_review_needed = [
        c["id"] for c in candidates
        if c.get("phase1_eval_state", {}).get("requires_human_review")
    ]
    if human_review_needed:
        approved_raw = (args.accept_human_review or "").strip()
        if approved_raw.lower() == "all":
            print("FAIL: --accept-human-review=all은 금지. 후보 ID를 명시하라.")
            return 2
        approved = {x.strip() for x in approved_raw.split(",") if x.strip()}
        unapproved = [cid for cid in human_review_needed if cid not in approved]
        if unapproved:
            print(
                f"BLOCK: {len(unapproved)}개 후보가 인간 검토 필요: {unapproved}\n"
                f"--accept-human-review=ID1,ID2 플래그로 ID 명시 승인 필요 "
                f"(전역 승인 'all' 금지)"
            )
            return 2

    # 7. rederivation_performed 편향 관측 — safe 판정 중 §9 Source 도달성 폐기가 아닌
    #    항목만 분모로 사용 (false alarm 방지).
    #    phase1_discarded_reason 있는 safe는 구조적 폐기로 rederivation 개념 비적용.
    safe_items = [
        c for c in candidates
        if c["status"] == "safe"
        and not c.get("phase1_discarded_reason")
    ]
    if safe_items:
        no_rederivation = [
            c["id"] for c in safe_items
            if not c.get("rederivation_performed", False)
        ]
        ratio = len(no_rederivation) / len(safe_items)
        if ratio > 0.30:
            print(
                f"WARN: evaluate-safe 판정 중 rederivation_performed=false 비율 "
                f"{ratio:.1%} > 30% 경고선."
            )
            print(f"편향 의심 항목: {no_rederivation}")
            _summary(candidates)
            # non-blocking 경고 — exit 3
            return 3

    # 통과
    _summary(candidates)
    return 0


def _summary(candidates: list) -> None:
    dist = {"confirmed": 0, "candidate": 0, "safe": 0}
    for c in candidates:
        dist[c["status"]] = dist.get(c["status"], 0) + 1
    print(
        f"OK: 후보 {len(candidates)}건 "
        f"(confirmed={dist['confirmed']}, "
        f"candidate={dist['candidate']}, "
        f"safe={dist['safe']})"
    )


if __name__ == "__main__":
    sys.exit(main())
