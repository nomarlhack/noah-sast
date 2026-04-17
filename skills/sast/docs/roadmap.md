# Noah SAST 로드맵

## MVP 완료 (evaluate + evaluate_phase1)

다음 항목은 MVP로 적용 완료:

- [x] mode=evaluate: Phase 2 증거 기반 status 할당 (checklist.md §10·§11)
- [x] mode=evaluate_phase1: Phase 1 결과 품질 평가 (checklist.md §12)
- [x] mode=review: 보고서 정확성 검증 (기존)
- [x] assert_status_complete.py: Step 3-6 진입 가드
- [x] assert_phase1_validated.py: Step 3-3 진입 가드 (+ C1 lint)
- [x] blind_read_phase1_md.py: 확증 편향 완화 헬퍼
- [x] master-list.json 스키마 확장: `phase1_validated`, `phase1_discarded_reason`, `phase1_eval_state`
- [x] Phase 2 manifest v2: status 필드 제거, evidence 구조화 객체

## 후속 작업 (미해소 결함 모니터링)

### due: 2주 내 — Phase 1 프롬프트 편향 감사

**배경**: blind eval은 "확증 편향 완화"가 목적이며, Phase 1 프롬프트 자체의 편향 유발 표현은 구조적으로 미해소. checklist.md 격리는 소비 측 우회이지 생산 측 수정이 아님. 후속 PR이 없으면 blind eval이 영구 우회책으로 고착되어 근본 원인이 남음.

**대상 파일**:
- `prompts/guidelines-phase1.md`
- `prompts/phase1-group-agent.md`
- `prompts/ai-discovery-agent.md`

**검토 항목**:
- Decision / Confidence / 판정 요약 섹션의 편향 유발 표현
- "취약하다", "위험하다" 같은 결론 단정 어휘
- 코드 스니펫 주변 서술이 판정을 암시하는 패턴

**완료 기준**: 편향 어휘 목록과 교정 예시 추가, 각 프롬프트에 "서술보다 사실 기반 관찰" 원칙 명시.

### due: MVP 검증 후 — scan-report-review 3-mode 문서 분리

**배경**: 현재 세 모드가 단일 SKILL.md 내 해석표로 표현되어 있음. 모드별 실행이 안정화되면 별도 서브 문서로 분리하여 가독성 향상.

### due: 미정 — update-phase2-status.py 완전 제거

**배경**: 현재는 deprecated 경고만. 다음 릴리스에서 물리 제거.

**전제**: 기존 v1 manifest를 사용하는 리포지토리가 더 이상 없을 때.

## 관측 대상 (KPI)

- evaluate_phase1 CONFIRM / OVERRIDE / DISCARD 분포
- evaluate의 rederivation_performed=false 비율 (30% 경고선)
- `requires_human_review` 에스컬레이션 발생 빈도
- Phase 1 원본 직접 참조 C1 lint 위반 건수
