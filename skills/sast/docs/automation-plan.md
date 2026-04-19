# SKILL.md 기계화 계획

메인 에이전트 지침이 아닌, **스크립트가 결정론적으로 처리 가능한 부분**을 분리하여 SKILL.md의 지침 부피를 줄인다. 에이전트에게 절차를 설명하는 대신, 스크립트 호출 한 줄로 대체한다.

## 원칙

- 스크립트가 동일 입력에 대해 동일 결과를 주는 작업은 지침이 아니라 스크립트로 처리한다.
- 사람(에이전트)의 판단이 필요한 부분만 지침에 남긴다 (예: `[도구 한계]` 미수행 시 직접 실행 여부, 커스텀 구현 인지).
- 새 스크립트 생성보다 **기존 스크립트 확장**을 우선한다 (유지보수 비용 최소화).

---

## 항목 B: `scanner-selector.py`에 Tier 컬럼 추가

### 현재 지침 (SKILL.md Step 3-5, 약 20줄)

Tier A/B/C 분류 테이블 전체가 SKILL.md에 인라인:

| Tier | 특성 | 해당 스캐너 | 실행 방식 |
|------|------|------------|----------|
| A | 인증 불요 | security-headers, http-smuggling, host-header, ... | Tier 내 순차, 다른 Tier와 병렬 |
| B | 공유 세션 | xss, sqli, ssrf, idor, csrf, redos, ... (30개) | Tier 내 순차 |
| C | 독립 인증 | oauth, saml, jwt | Tier 내 순차, B와 병렬 |

메인 에이전트가 이 표를 수동으로 보고 Tier를 결정한다.

### 스크립트화

`scanner-selector.py` 출력에 Tier 필드를 추가:

```
--- 그룹 편성 ---
그룹: auth-protocol (Tier C)
  - oauth-scanner
  - saml-scanner
  - jwt-scanner

그룹: db-query (Tier B)
  - sqli-scanner
  - nosqli-scanner
...

--- Tier 요약 ---
Tier A: 5개 스캐너 (Tier 내 순차, 다른 Tier와 병렬)
Tier B: 12개 스캐너 (Tier 내 순차)
Tier C: 3개 스캐너 (Tier 내 순차, B와 병렬)
```

스크립트 내부에 Tier 매핑 딕셔너리(`TIER_A`, `TIER_B`, `TIER_C`) 하드코딩. 스캐너 추가 시 이 딕셔너리만 갱신.

### SKILL.md 영향

Step 3-5의 Tier 표 삭제 → `scanner-selector.py`가 출력하는 Tier 정보 사용하도록 1줄 지침:

> Tier 분류는 `scanner-selector.py` 출력의 `--- Tier 요약 ---` 섹션을 따른다. 메인 에이전트는 Tier 간 병렬, Tier 내 순차로 Phase 2 에이전트를 디스패치한다.

**절감: ~20줄**

### 트레이드오프

- 장점: Tier 매핑이 코드로 관리되어 스캐너 추가 시 문서·코드 동기화 불필요.
- 단점: 기존 `scanner-selector.py`에 상수 딕셔너리 추가. 테스트 fixture 갱신 필요.

---

## 항목 A: `finalize_report.sh` 쉘스크립트

### 현재 지침 (SKILL.md Step 4 후처리, 약 25줄)

6단계가 순서대로 기술되어 있음:
1. report-review 에이전트 호출 (조건부: status ∈ {confirmed, candidate} 1건 이상)
2. `validate_report.py` 정량 검증
3. `lint_reader_layer.py` 독자 레이어 lint
4. `md_to_html.py` HTML 변환
5. `validate_links.py` 링크 검증
6. `open noah-sast-report.html` 브라우저 열기

각 단계에 실패 시 대응 규칙 포함.

### 스크립트화

`tools/finalize_report.sh`:

```bash
#!/bin/bash
# Usage: finalize_report.sh <NOAH_SAST_DIR> <PHASE1_RESULTS_DIR> <confirmed_candidate_count>

set -e
NOAH_SAST_DIR="$1"
PHASE1_RESULTS_DIR="$2"
COUNT="$3"

# 2~5단계만 스크립트가 처리. 1단계(report-review)는 조건부 에이전트 호출이라 메인 에이전트가 수행.
python3 "$NOAH_SAST_DIR/sub-skills/scan-report/validate_report.py" "$COUNT" \
  --master-list "$PHASE1_RESULTS_DIR/master-list.json"
python3 "$NOAH_SAST_DIR/tools/lint_reader_layer.py" noah-sast-report.md
python3 "$NOAH_SAST_DIR/sub-skills/scan-report/md_to_html.py"
python3 "$NOAH_SAST_DIR/sub-skills/scan-report/validate_links.py" noah-sast-report.html
open noah-sast-report.html
```

실패 시 해당 단계에서 `set -e`로 중단. 메인 에이전트는 에러 메시지만 보고 재시도 결정.

### SKILL.md 영향

Step 4 후처리 섹션을:

```
1. [조건부] report-review 에이전트 호출 (status ∈ {confirmed, candidate} 후보 1건+)
2. 나머지 검증·변환·열기: `finalize_report.sh <NOAH_SAST_DIR> <PHASE1_RESULTS_DIR> <confirmed+candidate 건수>`
```

실패 대응 규칙은 스크립트 에러 메시지가 설명.

**절감: ~20줄** (report-review 에이전트 호출 블록은 유지하므로 전체 25줄에서 5줄은 남음)

### 트레이드오프

- 장점: 후처리 순서가 코드에 박혀 있어 지침 drift 방지.
- 단점: 실패 시 어느 단계에서 실패했는지 에러 메시지만으로 판별. 단, `set -e` + 각 단계별 프린트로 충분 식별 가능.

---

## 항목 D: `run_grep_index.sh` 래퍼

### 현재 지침 (SKILL.md Step 0-2, 약 10줄)

Bash 래퍼 형식이 지침에 예시로 명시:

```bash
python3 .../run_grep_index.py ... ; RC=$?
JSON_COUNT=$(ls -1 <PATTERN_INDEX_DIR>/*-scanner.json 2>/dev/null | wc -l | tr -d ' ')
EXPECTED=$(ls -1d <NOAH_SAST_DIR>/scanners/*-scanner 2>/dev/null | wc -l | tr -d ' ')
echo "run_grep_index_exit=$RC"
echo "json_count=$JSON_COUNT"
echo "expected=$EXPECTED"
```

메인 에이전트가 매번 이 블록을 복사한다. "마지막 명령이 `echo`이므로 Bash tool의 최종 exit는 항상 `0`" 같은 meta 설명 포함.

### 스크립트화

`tools/run_grep_index.sh`:

```bash
#!/bin/bash
# 래퍼. run_grep_index.py 호출 + 카운트 검증.
# 항상 exit 0으로 종료 (메인 에이전트의 Bash tool UI 경고 방지).

NOAH_SAST_DIR="$1"; PROJECT_ROOT="$2"; OUT_DIR="$3"
python3 "$NOAH_SAST_DIR/tools/run_grep_index.py" \
  --scanners-dir "$NOAH_SAST_DIR/scanners" \
  --project-root "$PROJECT_ROOT" \
  --out-dir "$OUT_DIR"
RC=$?
JSON_COUNT=$(ls -1 "$OUT_DIR"/*-scanner.json 2>/dev/null | wc -l | tr -d ' ')
EXPECTED=$(ls -1d "$NOAH_SAST_DIR"/scanners/*-scanner 2>/dev/null | wc -l | tr -d ' ')
echo "run_grep_index_exit=$RC"
echo "json_count=$JSON_COUNT"
echo "expected=$EXPECTED"
exit 0
```

### SKILL.md 영향

Step 0-2 호출을 한 줄로:

```bash
bash <NOAH_SAST_DIR>/tools/run_grep_index.sh <NOAH_SAST_DIR> <PROJECT_ROOT> <PATTERN_INDEX_DIR>
```

meta 설명(exit 0 트릭) 제거.

**절감: ~10줄**

### 트레이드오프

- 장점: 복사 실수 방지. 메인 에이전트 프롬프트 단순화.
- 단점: 매우 단순한 래퍼 파일 하나 추가. 거의 없음.

---

## 항목 C: `renumber_ai_candidates.py`

### 현재 지침 (SKILL.md Step 3-2, 약 3줄)

> `AI-PENDING-N`을 `AI-1`, `AI-2`, ... 형식의 고유 ID로 재번호한다. `ai-discovery.md`의 `## AI-PENDING-N:` 헤더와 manifest ID도 함께 갱신한다.

메인 에이전트가 수동으로 sed/Edit 수행.

### 스크립트화

`tools/renumber_ai_candidates.py`:

```python
# ai-discovery.md를 읽어 AI-PENDING-1, AI-PENDING-2, ... 를
# AI-1, AI-2, ... 로 재번호. manifest JSON과 prose 헤더 동시 갱신.
```

50줄 내외. Idempotent — 이미 재번호되었으면 no-op.

### SKILL.md 영향

Step 3-2의 재번호 지시를 한 줄로:

```bash
python3 <NOAH_SAST_DIR>/tools/renumber_ai_candidates.py <PHASE1_RESULTS_DIR>/ai-discovery.md
```

**절감: ~3줄**

### 트레이드오프

- 장점: Edit 실수로 헤더와 manifest 불일치 발생 가능성 제거.
- 단점: 작은 스크립트 추가. 거의 없음.

---

## 종합 효과 (항목 B + A + D + C)

| 항목 | 신규/확장 | SKILL.md 절감 |
|------|----------|---------------|
| B | scanner-selector.py 확장 | ~20줄 |
| A | finalize_report.sh 신규 | ~20줄 |
| D | run_grep_index.sh 신규 | ~10줄 |
| C | renumber_ai_candidates.py 신규 | ~3줄 |
| **합계** | **신규 3 + 확장 1** | **~53줄** |

SKILL.md 598 → **약 545줄**

500줄 이하까지는 45줄 더 절감 필요. 추가로 `Step 3-7 결과 체크리스트 → docs/result-checklist.md 분리`(약 50줄 절감)를 병행하면 495줄로 진입 가능.

---

## 보류 항목 (E: `phase2_checklist.py`)

### 이유

"동적 테스트 실행 결과 파트 존재 여부" 판정이 phase2 manifest의 `responses.body_excerpt` 존재 여부만으로 결정되지 않을 수 있음. 부분 기록·fallback 케이스에서 false positive/negative 발생 가능.

### 대안

`assert_status_complete.py`에 체크리스트 출력 플래그 추가 (`--print-checklist`)만으로도 상당 부분 해결 가능. 다만 이건 체크리스트의 "동적 테스트 실행 결과 파트 검증" 부분을 완전히 자동화하지는 못함.

지금은 보류하고, 실제 사용 중 false positive 패턴이 보이면 그때 추가.

---

## 자기 비판

- **스크립트 추가 = 유지보수 대상 증가**: 4개 신규/확장의 유지보수 비용이 지침 절감 이득보다 크면 실익 없음. Tier 매핑(B)과 후처리 순서(A)는 자주 바뀌지 않는 구조라 안전. D, C는 단순 래퍼라 추가 비용 거의 없음.
- **쉘스크립트 포팅 이슈**: `finalize_report.sh`, `run_grep_index.sh` 모두 macOS/Linux 양쪽 동작 필요. `ls`, `wc`, `tr` 같은 POSIX 명령만 사용해 호환성 확보.
- **500줄 목표 자체의 타당성**: "500줄 이하가 성능 좋다"는 일반론이고, 실제 어떤 임계값에서 효과가 나는지는 경험적. 500 근방에서 쥐어짜느라 분리·스크립트화를 무리하게 진행하면 오히려 파편화로 가독성 저하. **비슷한 수준(540 정도)**으로 유지해도 큰 차이 없을 가능성.

---

## 승인 요청

본 계획대로 진행할지, 항목 가감할지 결정 부탁드립니다. 진행 승인 시 B → A → D → C 순으로 반영 예정.
