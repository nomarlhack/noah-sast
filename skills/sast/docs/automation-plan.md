# SKILL.md 자동화 스크립트

메인 에이전트 지침에서 스크립트로 이관한 결정론적 처리 부분 목록. 에이전트에게 절차를 설명하는 대신 스크립트 호출 한 줄로 대체한다.

## 원칙

- 동일 입력에 대해 동일 결과를 주는 작업은 지침이 아니라 스크립트로 처리한다.
- 사람(에이전트)의 판단이 필요한 부분만 지침에 남긴다 (예: `[도구 한계]` 미수행 항목의 직접 실행 여부, AI 검토 시 커스텀 구현 인지).
- 새 스크립트 생성보다 기존 스크립트 확장을 우선한다.

---

## Tier 분류 — `select_scanners.py`

Phase 2 동적 분석의 인증 컨텍스트 기반 병렬화(Tier A/B/C)를 스크립트가 결정한다. `TIER_A`, `TIER_C` 상수를 참조해 Tier 요약을 stdout에 출력한다.

**SKILL.md 영향**: Step 3-5에 Tier 표를 두지 않고 `--- Tier 요약 ---` 섹션을 참조하도록 지시한다.

## Step 4 후처리 — `report_finalize.sh`

`validate_report.py` → `lint_reader_layer.py` → `md_to_html.py` → `validate_links.py` → `open` 순차 실행. 실패 시 `set -e`로 중단, stdout에 단계명 프린트.

**SKILL.md 영향**: Step 4 후처리 5단계가 스크립트 한 줄 호출로 대체된다.

**제약**: 호출 시 작업 디렉토리가 `noah-sast-report.md` 위치(= `assemble_report.py` 출력 위치)여야 한다 (`md_to_html.py`가 `os.getcwd()` 기준).

## grep 인덱싱 래퍼 — `grep_index.sh`

`grep_index.py` 호출 + JSON 카운트 검증 + 예상 카운트 비교. 항상 exit 0으로 종료하여 Bash tool UI 경고를 방지하고 실제 결과는 stdout의 `run_grep_index_exit=N` 줄에서 읽는다.

**SKILL.md 영향**: Step 0-2 Bash 블록 8줄이 스크립트 한 줄 호출로 대체된다.

---

## 자동화하지 않은 항목

### Phase 2 체크리스트 생성

Step 3-7의 결과 체크리스트 테이블 자동 생성은 보류. "동적 테스트 실행 결과 파트 존재 여부" 판정이 phase2 manifest의 `responses.body_excerpt`만으로 결정되지 않을 수 있어 false positive/negative 위험이 있다. 현재는 메인 에이전트가 에이전트 반환 + manifest를 종합해 직접 작성한다.

### AI 후보 재번호

단일 탐색 기본 시나리오에서는 AI 에이전트가 처음부터 `AI-1, AI-2, ...` 순서로 직접 부여하면 충분하다. `[INCOMPLETE]` 후속 탐색 시에는 메인 에이전트가 "이전 마지막 AI-N"을 continued 에이전트에 전달하여 ID 충돌 없이 이어 번호 매긴다. 별도 renumber 스크립트 불필요.

---

## 자기 비판

- **스크립트 추가 = 유지보수 대상 증가**: 세 항목의 유지보수 비용이 지침 절감 이득보다 크면 실익 없음. Tier 매핑과 후처리 순서는 자주 바뀌지 않는 구조라 안전하다고 판단.
- **쉘스크립트 포팅**: `report_finalize.sh`, `grep_index.sh` 모두 macOS/Linux 공통 POSIX 명령만 사용.
