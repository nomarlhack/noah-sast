# MODE GUARD: 이 파일은 mode=report-review 전용

**[STOP]** 진입 프롬프트에 `MODE=report-review`가 명시되지 않았다면 즉시 종료하고 "모드 불일치"를 보고한다.

**다른 모드라면**:
- mode=phase1-review → `phase1-review.md`
- mode=phase2-review → `phase2-review.md`

**진입 전 필수 Read**: `_principles.md`, `_contracts.md`

**역할**: 보고서 조립 직전, **조립에 들어갈 원천 데이터**(master-list.json + eval MD + Phase 2 manifest + 체인)의 정확성을 독립 에이전트로 cross-check. phase1-review/phase2-review가 이미 수행한 검증을 재확인하며 특히 **cross-scanner 일관성**을 전담한다.

**입력 허용**:
- `<PHASE1_RESULTS_DIR>/master-list.json`
- `<PHASE1_RESULTS_DIR>/evaluation/<scanner>-eval.md`
- `<PHASE1_RESULTS_DIR>/<scanner>-phase2.md`
- `<PHASE1_RESULTS_DIR>/chain-analysis.md` (존재 시)
- 프로젝트 소스코드 (스팟체크용)

**출력**: 반환 텍스트만.

**금지**:
- master-list.json·eval MD·Phase 2 manifest·보고서 MD 일체 쓰기 금지.
- Phase 1 원본 `<scanner>.md` / `ai-discovery.md` 직접 참조 (`_contracts.md §6` C1 lint). eval MD 참조.

---

## 호출 시점

Step 3-6 (연계 분석) 완료 직후, Step 4 (보고서 조립) 진입 전.

---

## Step 1: 대상 추출

- master-list.json에서 `status ∈ {confirmed, candidate}` 후보 = `M_candidates`
- `status = safe` 후보 중 eval MD가 존재하는 건 = `M_safe` (이상 없음 판정 샘플링 대상)
- chain-analysis.md의 체인 수 = `M_chains` (파일 부재 시 0)

---

## Step 2: 검증 (병렬 서브에이전트)

그룹당 최대 5개 후보. 각 서브에이전트가 아래 체크리스트를 각 후보에 적용.

### 체크리스트 10항목

**Cross-scanner 전담 (phase1-review/phase2-review가 단독으로 못 잡는 항목)**:
7. **복수 요소 커버리지**: 복수 설정값/파일·라인 결함 시 master-list 필드·eval MD 본문·Phase 2 manifest가 모든 요소를 반영하는가?
8. **동일 file:line 다층 관점**: 서로 다른 스캐너가 같은 file:line을 지적하면 통합 여부 판단. 의사 테스트로 한 후보의 권장 조치가 다른 후보 결함을 해소하는가 확인.

**스팟체크 (샘플링 재확인, 각 항목당 최대 3개)**:
1. **파일 존재**: master-list.file 경로 실재
2. **코드 스니펫**: eval MD 인용 코드가 실제 라인에 존재 (±5줄 허용)
3. **데이터 흐름**: Source→Sink 경로가 실제 호출 관계와 일치
4. **부재 주장**: `_principles.md §2` 적용. "검증 없음" 주장이 사실
5. **검증 로직 누락**: eval MD가 언급하지 않은 검증 로직 실재 여부
6. **이상 없음 근거**: safe 후보의 `safe_category`·`verified_defense`·`phase1_discarded_reason` 근거 타당
9. **Source 도달성**: `_principles.md §1` 적용. Sink 인자가 외부 제어 가능
10. **POC 검증**: Phase 2 manifest의 commands가 실제 라우트 정의(`@RequestMapping` 등)와 일치

**체인 검증** (M_chains > 0): `<NOAH_SAST_DIR>/sub-skills/chain-analysis/chain-construction-rules.md` R1~R5를 모든 체인에 재적용. 판정 ✓ 통과 / ⚠ 약화 / ✗ 폐기.

### 서브에이전트 반환 형식

```
=== 후보: [ID] [제목] ===
Source 도달성: ✗ 폐기 (근거) / ✓ 유지 (source: <표현식>, <파일>:<라인>) / ? 불명확 (조건) / — 해당 없음
체크리스트 7·8: [전담 항목별 ✓ 또는 ✗ + 설명]
스팟체크 샘플: [적용한 항목 번호와 ✓/✗]
판정: ✓ 정확 / ⚠ 이상 / ✗ 심각
[⚠ 또는 ✗인 경우]
문제: [체크리스트 번호 + 구체 내용]
실제: [소스/데이터에서 확인한 실제]
권장 조치: [Phase 2 재실행 / 수동 확인 / 보고서 조립 전 master-list 수정 요청 등]
```

혼합 케이스는 `_principles.md §3 [혼합]` 포맷.

---

## Step 3: Source 도달성 반환 검증

1. 반환에 `Source 도달성:` 라인이 없는 항목 → 재검증 서브에이전트 디스패치 (`_principles.md §1` + 라인 필수).
2. 재검증에도 누락 시 메인 에이전트가 직접 역추적.
3. **Spot-check**: ✓ 유지 항목에서 최대 3개 샘플링, `(source: <표현식>, <파일>:<라인>)`을 Read로 확인. 실제 위치에 표현식 없으면 **허위 증거**로 간주하고 해당 서브에이전트 반환 전부 재검증.

판정 집계: `폐기_count` / `유지_count` / `불명확_count`.

---

## Step 4: 결과 요약 반환

```
## report-review 검증 결과

### 커버리지
| 종류 | 검증 / 전체 |
|------|-----------|
| 후보/확인됨 | N / M_candidates |
| 공격 체인 | N / M_chains |
| 이상 없음 | N / M_safe |

(N != M이면 결과 반환 거부)

### 체인 검증 결과 (M_chains > 0인 경우)
| 체인 | R1 | R2 | R3 | R4 | R5 | 데이터 흐름 | 판정 |
|------|----|----|----|----|----|------------|------|
| #1 | - | - | - | - | - | ✓ 입증 | ✓ 통과 |

### 판정 분포
- ✓ 정확: N건
- ⚠ 이상: N건
- ✗ 심각: N건

### Source 도달성 집계
| 판정 | 건수 |
|------|------|
| ✗ 폐기 | N |
| ✓ 유지 | N |
| ? 불명확 | N |

**게이트**: `폐기_count + 유지_count + 불명확_count == M_candidates`. 실패 시 반환 거부.

### 사용자 검토 권장 (이상/심각 0건이면 생략)
report-review는 master-list·eval·보고서를 수정할 수 없으므로 아래 항목을 사용자에게 보고한다. 사용자가 Phase 2 재실행 또는 수용 여부를 판단.

| ID | 문제 | 권장 조치 |
|----|------|----------|
| XSS-2 | Source 도달성 ✗ 폐기: code prop이 static 리터럴 (체크리스트 9) | phase2-review 결과 재검토 권장 |
| SSRF-3 | 이상 없음이 실은 취약: URL 파싱 경로 누락 (체크리스트 6) | 해당 후보 대상 Phase 2 동적 테스트 재실행 권장 |
```

---

## 자가 검증 (반환 전 필수)

1. **커버리지 100%** — 후보/확인됨·체인·이상 없음 모두 `검증 N == 전체 M`.
2. **Source 도달성** — 모든 후보에 라인 + 근거 명시.
3. **부재 주장** — `_principles.md §2` 적용.
4. **체인** — M_chains > 0이면 R1~R5 재적용 완료.
5. **Writer 권한** — master-list·eval·보고서·Phase 1 원본 쓰기 없음.
6. **반환 텍스트만** — 어떤 파일도 생성/수정 안 함.
