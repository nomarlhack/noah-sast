# Scan Report Review — 검증 에이전트 체크리스트

이 파일은 `scan-report-review/SKILL.md` Step 3의 검증 서브에이전트가 Read한다. 메인 에이전트는 본 파일을 인라인으로 복사하지 않는다.

---

## 검증 에이전트 프롬프트 본체

당신은 보안 보고서 검증 에이전트입니다.

아래 보고서 항목이 실제 소스코드와 일치하는지 검증하세요. 프로젝트 루트는 메인 에이전트가 프롬프트 끝에 전달한 `<PROJECT_ROOT>`를 사용합니다.

## 검증 체크리스트 (각 항목마다 수행)

1. 파일 존재 확인: 보고서가 참조하는 파일 경로가 실제로 존재하는가?
2. 코드 스니펫 정확성: 인용된 코드가 해당 파일의 해당 라인에 실제로 존재하는가?
3. 데이터 흐름 정확성: Source→Sink 경로 설명이 실제 코드의 호출 관계와 일치하는가?
4. 부재 주장 검증: "검증이 없다", "sanitize하지 않는다" 등의 주장이 사실인가?
   해당 함수 전후 ±30줄과 호출자/피호출자 체인을 반드시 확인한다.
   프레임워크 내장 방어(Spring Security, React 자동 이스케이프 등)도 고려한다.
5. 검증 로직 누락 여부: 보고서가 언급하지 않은 검증 로직이 실제로 존재하는가?
6. 이상 없음 판정 검증 (해당 시): "안전" 근거가 타당한가? 놓친 취약 경로가 있는가?
7. 복수 요소 커버리지: 후보가 인용한 설정값/코드에 복수의 요소가 있거나 동일 결함이 복수의 파일·라인에서 발견될 때, 제목·본문·POC가 모든 요소를 반영하는가? 인용된 원본을 Read하여 해당 스캐너 phase1.md 기준으로 누락 여부를 확인한다 (guidelines-phase1.md 지침 11).

8. 동일 file:line 다층 관점 통합: 보고서에 서로 다른 스캐너가 **같은 file:line**을 지적하는 후보가 2건 이상 존재하는지 확인한다. 존재하면 아래 절차를 수행한다.
   - 해당 후보들의 Phase 1 결과 파일을 Read하여 각 스캐너가 어떤 관점(레이어/원인-결과/방법론)에서 탐지했는지 확인한다.
   - **의사 테스트**: 한 후보의 권장 조치만 적용해도 다른 후보의 결함이 해소되는가? 부분 해소면 "아니오".
   - **통합 조건**: 의사 테스트가 "예"이고 두 후보가 같은 근본 결함을 서로 다른 층위(프레임워크/서비스, 원인/결과 등)에서 기술하고 있으면 통합한다. 불확실하면 분리 유지 (false merge가 false split보다 위험).
   - **통합 시 MD 수정**: 두 독립 블록을 하나의 블록으로 합친다. 각 관점의 원본 기술(소스코드 분석, POC, 권장 조치)을 `##### ` 하위 섹션으로 보존하며 어느 한쪽도 축소/흡수하지 않는다. 통합 블록에 `**발견 스캐너**:` 필드를 추가하여 복수 스캐너를 나열한다. 총괄 요약 테이블의 건수도 갱신한다.
   - **분리 유지 시**: 수정 없음. placeholder 공유(`:1` 라인 등)나 서로 다른 취약점 카테고리는 분리가 기본.

9. Source 도달성: 후보의 Sink 인자가 실제로 사용자 제어 가능한 Source에서 유도되는가?
   Sink 호출부의 인자 변수를 역추적하여 최초 대입 지점을 확인한다. 대입 지점이
   컴파일 타임 상수·하드코딩 리터럴·내부 생성값(UUID, 서버 시간, 고정 내부 ID 등)
   이면 `Source 도달성: ✗ 폐기`로 판정한다. guidelines-phase1.md 지침 8과
   동일한 기준을 적용한다. (실제 재분류는 메인 에이전트가 Step 5에서 수행한다.)

## 반환 형식

각 항목에 대해:

```
=== 항목: [항목 제목] ===
Source 도달성: ✗ 폐기 (근거) / ✓ 유지 (source: <소스_표현식>, <파일>:<라인>) / ? 불명확 (해당 조건) / — 해당 없음
판정: ✓ 정확 / ✗ 부정확 / ⚠ 부분 수정 필요
[부정확 또는 부분 수정인 경우]
문제: [구체적으로 무엇이 틀렸는지]
실제: [소스코드에서 확인한 실제 내용]
수정안: [보고서에 반영할 수정 내용]
```

### 혼합 케이스 반환 형식

Sink가 여러 호출 경로를 가지며 Source 도달성 판정이 경로마다 다른 경우, 아래 형식을 사용한다:

```
=== 항목: [항목 제목] ===
Source 도달성 [혼합]:
  - 경로 1: ✓ 유지 (source: request.getParameter("q"), MixedCaller.java:16 → write():12)
  - 경로 2: ✗ 폐기 (인자가 HTML 리터럴 "<b>Fixed banner</b>", MixedCaller.java:21)
판정: ⚠ 부분 수정 필요
문제: 후보가 모든 호출 경로를 구분하지 않고 기술
수정안: ✓ 경로만 후보로 유지하고 호출 경로 정보를 후보 기술에 포함. ✗ 경로는 후보에서 제거.
```

메인 에이전트는 `[혼합]` 태그를 인식하여:
- ✓ 경로가 1개 이상이면 후보를 유지하되, 후보 기술을 ✓ 경로만으로 한정
- 모든 경로가 ✗이면 폐기로 처리
- Step 4.5 집계에서는 ✓ 경로가 있으면 유지_count, 없으면 폐기_count에 반영

### 반환 형식 필수 규칙

- `Source 도달성:` 라인은 후보/확인됨 항목에서 생략할 수 없다. 이 라인이 없는 항목이 포함된 반환은 메인 에이전트가 거부하고 해당 항목을 재검증 요청한다. 이상 없음 항목은 `— 해당 없음`을 사용한다.
- `✗ 폐기` 판정에는 반드시 근거가 동반되어야 한다: `✗ 폐기 (인자 X가 static final 상수 "abc"로 대입, line 42)` 형태. 근거 없는 폐기는 무효이며 메인 에이전트가 거부한다.
- `✓ 유지` 판정에는 반드시 실제 역추적한 Source 지점이 동반되어야 한다: `✓ 유지 (source: request.getParameter("url"), UserController.java:42)` 형태. Source 지점 없는 유지는 무효이며 메인 에이전트가 거부한다.
- `? 불명확` 판정에는 §4-1(e)의 불명확 케이스 3개 조건 중 해당하는 것을 명시해야 한다: `? 불명확 (역추적 3단계 내 확정 불가: IoC 컨테이너 주입)` 형태. 조건 미명시는 무효이며 메인 에이전트가 거부한다.
- 혼합 케이스(여러 호출 경로에서 판정이 다른 경우)는 `Source 도달성 [혼합]:` 형식을 사용한다. 경로별 판정을 개별 나열하며, 각 경로에 ✓ 유지 / ✗ 폐기 근거를 포함한다.

---

## 검증 유형별 상세 지침

### 4-1. 후보/확인됨 항목 검증

**a) 코드 스니펫 검증**
- 보고서의 코드 블록을 실제 파일에서 Read로 읽은 내용과 비교
- 라인 번호 오차 ±5줄까지 허용 (리팩토링으로 인한 이동)
- 내용이 다르면 실제 코드로 교체

**b) Source→Sink 흐름 검증**
- 보고서가 기술한 각 단계를 실제 코드에서 추적
- 호출 관계가 끊기거나 중간에 검증 로직이 있으면 보고
- 메서드명, 클래스명, 파라미터명이 실제와 다르면 수정

**c) 부재 주장 검증 — 가장 중요**

보고서에서 "~가 없다", "~하지 않는다"라고 주장하는 모든 곳을 검증한다. Phase 1 에이전트가 코드를 읽을 때 검증 로직을 놓치는 경우가 실제로 발생하기 때문이다 (예: 스킴만 검증하는데 "검증 없음"으로 기술, 상위 레이어의 필터를 놓침).

검증 방법:
- 해당 함수/메서드의 전후 컨텍스트를 충분히 읽음 (최소 ±30줄)
- 같은 클래스/파일 내 다른 메서드에서 검증하는지 확인
- 호출자 체인을 거슬러 올라가며 상위 레이어의 검증 확인
- 프레임워크 내장 방어 확인 (버전별 차이 주의)
- 설정 파일(SecurityConfig, WebMvcConfig 등)의 전역 필터 확인

실제로 검증 로직이 존재하면:
- 검증이 완전하여 취약점이 아닌 경우 → 후보에서 제거, 이상 없음으로 재분류
- 검증이 존재하지만 우회 가능한 경우 → 검증 로직을 보고서에 명시하되, 우회 방법을 기술하여 후보 유지
- 검증이 존재하지만 불완전한 경우 (예: 스킴만 검증, 호스트 미검증) → 보고서 내용을 정확하게 수정

**d) POC 검증**
- curl 엔드포인트 경로가 실제 라우트 정의(@RequestMapping, @GetMapping 등)와 일치하는지
- HTTP 메서드가 실제와 일치하는지
- 파라미터명이 실제 @RequestParam/@RequestBody 필드명과 일치하는지

**e) Source 도달성 검증**

Sink 인자의 출처가 사용자 제어 가능한지를 독립 항목으로 검증한다. Phase 1이
Sink 패턴 매칭까지만 하고 인자 출처를 소홀히 한 경우를 잡는 백업이다.

검증 방법:
- Sink 호출부에서 사용된 인자 변수를 선택
- 같은 함수 내에서 그 변수의 최초 대입 지점을 역추적 (Read로 함수 전체 확인)
- 함수 파라미터에서 시작했으면 호출자를 Grep하여 호출자에서 어떤 값을 넘기는지
  확인 (최대 3단계 재귀)

판정 원칙 (`guidelines-phase1.md` §6-A 87줄 "Sink 판정은 패턴 목록이 아닌 의미
기반" 원칙을 Source 판정에도 동일 적용. **목록·표·열거 대신 의미를 기준으로
판정한다. 어떤 enum도 모든 스택·프로토콜·채널을 망라할 수 없다.**):

**✗ 폐기 원칙**: 최초 대입 지점이 외부 행위자의 영향과 **인과적으로 분리**되어,
프로그램 내부에서 결정론적으로 산출되는 값일 때. 즉 같은 빌드의 같은 코드 경로를
실행하면 외부 입력 없이도 동일하게 도출되는 값 (리터럴, 내부 시계/난수, 모듈 내
계산 결과 등).

**✓ 유지 원칙**: 최초 대입 지점이 **외부 행위자(공격자, 다른 사용자, 외부 시스템,
외부에서 쓰기 가능한 저장소)에 의해 직접 또는 간접으로 제어 가능한 모든 채널**.
프로토콜·프레임워크·스택을 가리지 않는다. 새로운 입력 데코레이터/요청 객체/메시지
프로토콜이라도 "그 값이 외부에서 결정되는가"가 유일한 기준이다.

판단 방법: 최초 대입 지점에 대해 다음을 자문한다 — *"이 값을 외부 행위자가
의도적으로 다르게 만들 방법이 코드 외부에 존재하는가?"* 존재하면 ✓ 유지,
존재하지 않음을 코드로 입증할 수 있으면 ✗ 폐기, 입증 불가하면 불명확 케이스로
보낸다.

혼합 케이스: Sink가 여러 호출부를 가지며 일부는 ✓ 일부는 ✗이면, 각 호출 경로를
분리해 ✓ 경로만 후보로 유지하고 호출 경로 정보를 후보 기술에 포함한다.

**불명확 케이스 — 보수적 유지가 기본** (확신 없는 폐기보다 안전):
- 외부 제어 가능성을 확신할 수 없지만 배제도 못 하는 경우
- 역추적이 리플렉션·동적 dispatch·IoC 컨테이너 주입·메타프로그래밍 등으로
  3단계 내 확정 불가
- 스택/프레임워크가 낯설어 판정 자체가 불확실

위 중 하나라도 해당하면 후보를 폐기하지 말고 유지하며, "Source 도달성 불명확"을
후보 기술에 명시한다.

### 4-2. 이상 없음 판정 검증

각 "안전" 판정 항목에 대해:
- 근거로 제시된 방어 메커니즘이 실제로 적용되어 있는지 확인
- 보고서가 놓친 Sink나 Source 경로가 없는지 확인
- 프레임워크 버전에 따른 방어 기능 차이 확인

놓친 취약 경로가 발견되면 → 이상 없음에서 후보로 승격하고, 취약점 상세 섹션을 새로 작성

### 4-3. 공격 시나리오 검증 (M_chains > 0이면 필수)

`<NOAH_SAST_DIR>/sub-skills/chain-analysis/chain-construction-rules.md`를 Read 도구로 읽어, chain-analysis가 적용한 동일한 5개 규칙(R1~R5)을 보고서의 모든 체인에 독립적으로 재적용한다. 1차 작성자가 통과시킨 체인이라도 review에서 다시 검사한다.

각 체인에 대해 코드로 입증한다:
(a) Step N의 출력이 Step N+1의 입력으로 도달하는 코드 경로 (파일경로:라인번호 최소 2개 지점)
(b) Step N+1이 Step N 없이 실행 가능하면 체인 무효
(c) "만약/~라면" 가정 분기가 2개 이상이면 체인 무효

판정:
- ✓ 통과: 5개 규칙 모두 해당 없음 + 데이터 흐름 코드 입증 완료
- ⚠ 약화: 일부 단계만 유효 → 유효 단계만 부분 체인/독립 후보로 분리
- ✗ 폐기: 규칙 1개 이상 해당 → 체인 삭제, 관련 후보를 모두 독립 후보로 재분류

수정 시 함께 갱신: 총괄 요약, 위험도 등급, 독립 후보 섹션.

---

## "수정 없음" 결과의 신뢰성

"수정 사항 없음" 반환 전 아래 5개를 모두 통과해야 한다. 하나라도 실패 → 추가 검증 후 재시도.

| # | 자가 검증 항목 |
|---|--------------|
| 1 | 후보/확인됨 100% Read 검증 완료 |
| 2 | 부재 주장 항목 ±30줄 + 호출자 체인 확인 |
| 3 | 모든 체인에 R1~R5 검사 통과 |
| 4 | 검증 커버리지 표 N == M |
| 5 | 모든 후보에 Source 도달성 검증을 적용했고 폐기(근거)/유지(source 지점)/불명확(해당 조건) 판정이 근거와 함께 명시적으로 내려짐 |

## 주의사항

- Read 도구로 소스코드를 직접 읽어서 확인한다. 이전 분석 결과나 기억에 의존하지 않는다.
- 부재 주장 검증 시, 해당 함수뿐 아니라 호출자/피호출자 체인도 확인한다. 상위 레이어에서 검증이 이루어질 수 있다.
- 프레임워크 내장 방어는 버전별로 다를 수 있으므로, build.gradle.kts나 package.json에서 실제 버전을 확인한다.

---

**[필수] 모든 후보/확인됨 항목의 반환에 `Source 도달성:` 라인(판정 + 근거/source 지점)이 누락되면 해당 항목의 반환이 거부된다. 이 규칙에 예외는 없다.**

---

## §10. Phase 2 증거 기반 status 할당 (mode=evaluate 전용)

`scan-report-review`가 `mode=evaluate`로 호출되면 Phase 2 결과 파일(`*-phase2.md`)의 evidence를 해석해 `master-list.json`의 `status` 필드를 직접 할당한다. 메인 오케스트레이터는 status를 할당하지 않는다.

### 판정 플로우

```
evidence.commands 또는 evidence.responses 존재?
  No → candidate (태그 매트릭스에서 선택)
  Yes → 공격 성공 지표 존재? (alert 발화, 데이터 반환, 상태 변경 등)
      Yes → confirmed
      No  → 차단됨
          → 응답이 공격 벡터를 구체적으로 언급?
              + defense_code_hints를 리뷰가 독립 Read로 확인했는가?
              Yes → safe (verified_defense 필드 기록, rederivation_performed=true)
              No  → candidate (차단)
```

### 판정×태그별 필수 필드 매트릭스

| 판정 | 태그 | 필수 필드 | 금지 |
|------|------|-----------|------|
| confirmed | — | commands, responses, observations | null placeholder |
| safe | — | commands, responses, verified_defense (리뷰가 추가하는 {file, lines, content_hash}) | Phase 2 에이전트의 사전 확정 |
| candidate | 도구 한계 | commands (실패 로그), observations (도구 오류 메시지) | 빈 responses placeholder |
| candidate | 정보 부족 | observations (요청한 정보 목록) | — |
| candidate | 환경 제한 | commands, responses, observations (제한 유형 명시) | — |
| candidate | 차단 | commands, responses, blocking_layer_hint | verified_defense 기록 금지 (safe 경로) |

**복합 태그**: 두 태그가 동시에 해당하면 각 태그의 필수 필드를 **union**하여 요구한다.

**해당 없는 필드는 `null` 대신 필드 자체를 생략**한다. null placeholder는 기록을 위한 기록으로 간주해 거부한다.

### 양방향 증거 요건

- confirmed 승격: 공격 성공 지표가 응답/관찰에 명시되어야 함. "성공한 것 같다" 같은 수식어 금지.
- safe 강등: verified_defense에 Read로 확인한 파일 경로·라인 범위·sha256 해시 기록 필수. hint 필드(Phase 2 산출)를 그대로 복사 금지.
- candidate 유지: "애매하면 candidate"는 금지. 사유 태그 + 해당 태그의 필수 필드 충족 필수.

### rederivation_performed 필드

리뷰 산출물에 `rederivation_performed: bool` 필드를 의무화한다.

- `true`: 리뷰가 Phase 2 hint와 **독립적으로** 방어 코드를 Read하여 재확인
- `false`: Phase 2 hint를 그대로 승격 (편향 의심 신호)

`false` 비율이 safe 판정 전체의 30%를 초과하면 Step 4 assert에서 경고를 발생시킨다.

---

## §11. master-list.json 갱신 규약

### 단일 writer 규약

- `mode=evaluate`의 scan-report-review 에이전트만 master-list.json의 `status` 필드를 쓴다.
- 메인 오케스트레이터는 Read만 수행한다.
- Phase 2 에이전트는 `*-phase2.md`에 evidence만 기록하고 master-list.json을 직접 쓰지 않는다.

### DISCARD 보호 가드 (#3)

`mode=evaluate`는 아래 후보를 발견하면 **status·evidence 필드를 변경하지 않는다**:
- `phase1_discarded_reason != null` 이고 `status == "safe"` 인 후보

evaluate 서브에이전트 프롬프트에도 이 규칙을 명시한다. Phase 2 evidence가 존재하더라도 DISCARD가 이미 확정된 후보는 건너뛰며, 해당 후보의 evidence는 `phase1_quality_notes`에 "Phase 2 evidence가 있으나 DISCARD 상태라 미반영 (사유: phase1_discarded_reason)"으로만 기록한다.

단, `phase1_eval_state.reopen == true` 인 경우는 예외로, §10-A 교차 검증 재호출 경로에 해당하므로 DISCARD 철회 가능성을 열어둔다 (evaluate_phase1 재호출 시 재판정).

### DISCARD 경로 safe_category 면제 규칙

`phase1_discarded_reason != null`인 후보는 **`validate_safe_consistency`의 defense_verified↔verified_defense 상호 검증에서 제외**된다.

- DISCARD 경로는 `safe_category` 기록 의무 없음 (§12-C §9 참조)
- `assemble_report.py:_classify_safe()`가 키워드 휴리스틱으로 자동 분류
- 분류 실패 시 exit 7 (safe_bucket_unclassified)로 경고 — `phase1_discarded_reason` 키워드 보완 요구

**의도**: Phase 1 DISCARD는 Phase 2 evidence 없이 구조적 이유로 판정되므로 `verified_defense` 필드가 존재할 수 없다. 강제하면 모든 DISCARD safe가 FAIL 처리되어 기존 정상 흐름을 블로킹한다.

### evaluate safe 판정 시 safe_category 필수 기록

`mode=evaluate`가 `status: safe` 할당 시 (동적 방어 입증 경로) **`safe_category: "defense_verified"`를 반드시 기록**하고 `verified_defense` 객체에 `{file, lines, content_hash}`를 함께 채운다.

- 이 경로는 DISCARD가 아니므로 면제 규칙 대상 아님
- `validate_safe_consistency`가 `defense_verified ↔ verified_defense` 정합성 검증 수행
- 불일치 시 exit 1 (incomplete/invalid state)

### 갱신 후 각 후보 필드

```json
{
  "id": "XSS-2",
  "title": "...",
  "scanner": "...",
  "status": "confirmed" | "candidate" | "safe",
  "tag": null | "도구 한계" | "정보 부족" | "환경 제한" | "차단",
  "evidence_summary": "판정 근거 요약 (≤2KB)",
  "verified_defense": null | {"file": "...", "lines": "40-52", "content_hash": "sha256:..."},
  "rederivation_performed": true | false,
  "source_phase2_file": "/tmp/phase1_results_.../xss-scanner-phase2.md",
  "source_phase2_hash": "sha256:..."
}
```

### 크기 상한

- `evidence_summary` ≤ 2KB
- `verified_defense` 본문은 해시만 기록 (파일 내용 전체 기록 금지)

### 재평가 트리거

- `source_phase2_file`의 해시가 달라지면 자동 재평가 대상으로 표시
- 메인 오케스트레이터는 mode=evaluate를 재호출하여 갱신

### mode=review와의 역할 분리

- `mode=evaluate`: master-list.json writer
- `mode=review`: 보고서 MD 검증자 (mode=evaluate 결과를 읽기만 함, status 건드리지 않음)
- 두 모드가 같은 세션에서 호출되어도 **서로의 산출물을 직접 수정하지 않는** 계약

### §10 커버리지 규약 (#1 해결)

`mode=evaluate`의 커버리지는 master-list.json의 모든 후보가 아니라 아래 조건을 만족하는 후보에 **한정**한다:

- `phase1_discarded_reason == null` (Phase 1에서 DISCARD되지 않음)
- **또는** `phase1_eval_state.reopen == true` (재평가 요청 플래그가 설정됨 — 이 경우 DISCARD도 예외적으로 재평가 대상)

즉 일반적으로 DISCARD된 후보는 evaluate가 건너뛰며, 오직 §10-A 교차 검증이 reopen을 요청했을 때만 재평가한다. 이 우선순위는 `reopen == true` > `phase1_discarded_reason != null` 순서로 해석한다.

evaluate 서브에이전트 프롬프트에 이 커버리지 규칙을 명시하고, skip된 후보는 status 및 evidence 필드를 일체 변경하지 않는다.

### §10-A. Phase 1 교차 검증 (mode=evaluate에서 수행)

evaluate가 Phase 2 evidence를 해석할 때, master-list.json의 Phase 1 기술과 교차 검증한다.

**교차 검증 항목**:
- Phase 1 Source 주장 ↔ Phase 2 evidence.responses의 입력 경로
- Phase 1 Sink 위치 ↔ Phase 2 evidence.commands의 호출 대상
- Phase 1 미확인 사유 ↔ Phase 2 observations의 실제 결과

**모순 발견 시 처리**:
- **1회차 모순**: 해당 후보의 `phase1_eval_state.reopen = true` 기록. evaluate_phase1 재호출을 main에 요청.
- **2회차 모순**: `phase1_eval_state.requires_human_review = true` + `phase1_eval_state.conflicts` 배열에 모순 내역 기록. status는 `candidate` + `tag: "교차검증_모순"`으로 고정.
- **재실행 상한 2회**: `phase1_eval_state.retries == 2` 도달 시 더 이상 재호출 금지. 사용자 에스컬레이션으로 이관.

---

## §12. Phase 1 결과 평가 (mode=evaluate_phase1 전용)

mode=evaluate_phase1은 Phase 1 결과 파일의 **정적 분석 품질**을 검증한다. Phase 2 이전에 수행되어 부정확한 후보를 조기에 정제한다.

### 입력/출력 분리 (Phase 1 원본 불변 원칙)

- **입력**: `<PHASE1_RESULTS_DIR>/<scanner-name>.md` (Read만 허용, Edit·Write 금지), `master-list.json`
- **출력 1 (단일 진실 원천)**: `<PHASE1_RESULTS_DIR>/evaluation/<scanner-name>-eval.md`
  - Phase 2는 Phase 1 원본 MD가 아닌 이 eval MD를 참조한다 (§12-E 참조)
- **출력 2**: `master-list.json`에 아래 필드 갱신
  - `phase1_validated: bool`
  - `phase1_discarded_reason: str | null`
  - `phase1_eval_state: {reopen: bool, retries: int, conflicts: [...], requires_human_review: bool}`

### §12-A. 관점 분리 (Source 역추적 중심)

Phase 1 에이전트가 **Sink 패턴 매칭**으로 후보를 수집했다면, evaluate_phase1은 **Source 역추적 중심**으로 접근한다.

- Sink 호출부의 인자 변수를 선택 → 같은 함수 내 최초 대입 지점 Read로 확인
- 함수 파라미터에서 시작했으면 호출자를 Grep하여 최대 3단계 재귀
- 프레임워크 내장 방어(Spring Security, React 자동 이스케이프, OWASP ESAPI 등) 확인
- 설정 파일(SecurityConfig, WebMvcConfig 등)의 전역 필터 확인

### §12-B. blind eval 메커니즘 (확증 편향 완화)

**목표**: blind eval의 목적은 "**완전 독립 재판정**"이 아니라 "**확증 편향 완화**"이다. 판정 근거가 Phase 1 서술에 녹아 있는 자연어 누설은 원리적으로 완전 차단 불가능하나, 구조적 단서(Decision 필드) 제거로 판단 과정의 초기 고정을 늦춘다.

**절차**:
1. Phase 1 MD를 `tools/blind_read_phase1_md.py`로 로드. 헬퍼가 다음 섹션을 `<MASKED until independent judgment>`로 대체한 뷰 반환:
   - `### Decision`
   - `### Confidence`
   - `### 판정 요약`
2. 평가자는 마스킹된 뷰만 보고 §12-C의 4개 필수 축을 독립 적용
3. 독립 판정 완료 후 마스킹 해제 → Phase 1 결론과 대조 → `CONFIRM` / `OVERRIDE` / `DISCARD` 기록

### §12-C. 필수 적용 축 (4개)

- **§2 코드 스니펫 정확성**: 인용된 코드가 실제 파일·라인에 존재
- **§3 Source→Sink 흐름**: 호출 관계가 끊기지 않음, 중간 검증 로직 파악
- **§4 부재 주장 검증**: "검증이 없다"·"sanitize하지 않는다" 주장을 반드시 검증
  - **§4 의무 절차**:
    1. 해당 함수/메서드의 전후 컨텍스트를 최소 ±30줄 Read
    2. 같은 클래스/파일 내 다른 메서드에서 검증하는지 확인
    3. 호출자 체인을 거슬러 올라가며 상위 레이어 검증 확인
    4. 프레임워크 내장 방어 확인 (버전별 차이 주의)
    5. 결과를 `phase1_quality_notes`에 기록
- **§9 Source 도달성**: Sink 인자가 외부 행위자 제어 가능한지 판정
  - `✗ 폐기` 판정 시: master-list.json의 해당 후보를 `status: safe` + `tag: "Source 도달성 폐기"`로 **즉시 할당** (Phase 2 낭비 방지)
    - **[필수] `phase1_validated: true` 함께 설정** — 평가 자체는 완료된 상태임을 표시 (DISCARD도 "평가 pass 여부"가 아니라 "평가 완료 여부"로 집계)
    - `phase1_discarded_reason`에 폐기 근거 기록 (어떤 근거로 Source 도달성 ✗인지 코드 경로 포함)
    - **`safe_category` 기록은 선택사항 (자동 유추 허용)**. 에이전트가 명시적으로 기록하면 우선되며, 기록하지 않으면 `assemble_report.py:_classify_safe()`가 `phase1_discarded_reason` 키워드 휴리스틱으로 분류한다. 이 경로의 safe 후보는 `validate_safe_consistency`에서 "defense_verified↔verified_defense" 상호 검증을 skip한다 (§11 DISCARD 면제 규칙).
    - 이후 evaluate/보고서 렌더러는 `status=safe` + `phase1_discarded_reason` 조합을 "재평가 대상 아님"으로 인식
  - `? 불명확` 판정 시: 보수적으로 `phase1_validated: true` 유지 (CONFIRM으로 취급)

### §12-D. 선택 적용 축 (효율)

- §7 복수 요소 커버리지
- §8 동일 file:line 다층 관점 통합

후보가 이미 참조하는 파일을 Read한 김에 겸사 적용한다. 단독 Read는 비효율.

### §12-E. eval MD 형식 (Phase 2의 단일 진실 원천)

```markdown
# <scanner-name> Phase 1 평가본

## <ID>: <후보 제목>

### Phase 1 원본 판정
[Phase 1 MD에서 복사, 변경 없음]

### 평가자 독립 판정 (blind eval 후)
[§12-C의 4개 축 적용 결과 요약]

### Override 여부
CONFIRM | OVERRIDE | DISCARD

### 수정 권고 (Phase 2에 전달)
[Phase 2가 반영해야 할 Source·Sink·테스트 경로 수정 사항]

### phase1_quality_notes
[§4 taint 분석 요약 + §9 Source 도달성 근거 + §2·§3 정확성 판정]
```

Phase 2 에이전트 프롬프트는 Phase 1 원본(`<scanner>.md`)이 아닌 eval MD(`evaluation/<scanner>-eval.md`)를 Phase 1 결과로 참조한다.

### §12-F. 파일 간 일관성 검사

evaluate_phase1의 마지막 단계:
- 동일 `file:line`을 지적하는 모든 스캐너의 eval MD를 교차 확인
- 상충된 판정(A 스캐너는 CONFIRM, B 스캐너는 DISCARD) 발견 시 `phase1_eval_state.conflicts`에 기록
- 해당 후보들을 `requires_human_review: true`로 표시

### §12-G. 원본 해시 검증

evaluate_phase1 실행 후 `evaluation/<scanner>-eval.md` 생성 시:
- 해당 Phase 1 MD의 sha256 해시를 eval MD 상단에 `<!-- SOURCE_HASH: sha256:... -->` 주석으로 기록
- assert 단계에서 Phase 1 원본과 해시가 일치하는지 검증. 불일치 시 eval 고아 상태로 간주하여 `phase1_validated` 자동 false 처리

### §12-H. Phase 1 직접 참조 금지 (C1)

Phase 2 에이전트 프롬프트 및 연계 분석 에이전트 프롬프트에서 `<PHASE1_RESULTS_DIR>/<scanner>.md` 직접 참조는 금지한다. 반드시 `<PHASE1_RESULTS_DIR>/evaluation/<scanner>-eval.md`를 참조한다.

assert 스크립트가 lint 형태로 이 규칙을 검사한다.

---

## §11-A. master-list.json 스키마 확장 (evaluate_phase1용)

§11 기존 규약에 다음 3개 필드를 추가한다 (모두 옵션, 하위 호환).

```json
{
  "id": "XSS-2",
  ...,
  "phase1_validated": true,
  "phase1_discarded_reason": null,
  "phase1_eval_state": {
    "reopen": false,
    "retries": 0,
    "conflicts": [],
    "requires_human_review": false
  },
  "safe_category": null
}
```

- `phase1_validated`: evaluate_phase1이 완료했는지 (true) 또는 미완/고아 (false)
- `phase1_discarded_reason`: §9 Source 도달성 ✗로 safe 처리된 경우의 근거 (그 외엔 null)
- `phase1_eval_state`: 교차 검증 상태 추적 객체
  - `retries`: §10-A **교차 검증 모순** 재호출 카운터 (상한 2, 초과 시 `requires_human_review=true`). safe_category 교정 재호출도 이 카운터에 합산되어 동일 상한을 공유한다.
- `safe_category`: safe 판정 시 4분류 중 하나 (enum: `"no_external_path" | "defense_verified" | "not_applicable" | "false_positive"`) **또는 `null`**. 메인 오케스트레이터가 `assemble_report.py`의 "안전 판정 항목" 섹션 자동 생성 시 소비한다.
  - **`null` sentinel 허용**: 초기화 상태 또는 Phase 1 DISCARD 경로(§12-C §9)에서 자동 유추 대상임을 표시. enum 위반으로 간주하지 않는다.
  - 미설정(null) 시 `assemble_report.py`가 `verified_defense`/`phase1_discarded_reason` 키워드로 휴리스틱 추정한다 (vuln-format.md "safe 판정 4분류" 규약 참조).

### Writer 권한 규약 (#23)

각 필드를 수정할 수 있는 모드는 아래로 제한된다. 권한 없는 모드가 필드를 변경하면 master-list.json의 단일 진실 원천 원칙이 무너진다.

| 필드 | Writer 모드 | Reader 모드 |
|------|------------|------------|
| `status`, `tag`, `evidence_summary`, `verified_defense`, `rederivation_performed` | `evaluate` (DISCARD 보호 가드 내에서만) | `review`, 연계 분석 |
| `phase1_validated`, `phase1_discarded_reason`, `phase1_eval_state`, `safe_category` | `evaluate_phase1` | `evaluate`, `review`, 연계 분석 |

**`mode=review`는 어떤 필드도 쓰지 않는다.** review가 §9 Source 도달성 재검증 결과 "후보→이상 없음 재분류" 권고가 필요하면 직접 수정이 아니라 `phase1_eval_state.reopen=true` 기록으로 evaluate_phase1 재호출을 요청한다. 요청을 수행하는 것은 메인 오케스트레이터이며, 실제 필드 갱신은 evaluate_phase1이 담당한다.

### safe 후보 0건 처리 (#30)

master-list.json의 `status=safe` 후보가 0건인 경우 `assemble_report.py:build_safe_section()`은 **빈 문자열을 반환**하며, `<!-- SAFE_SECTION_HERE -->` 플레이스홀더는 빈 값으로 치환되어 **`## 안전 판정 항목` 섹션 자체가 보고서에 나타나지 않는다**.

- `validate_report.py`는 safe 후보 0건이면 "안전 판정 항목 섹션 부재"를 오류로 처리하지 않는다 (허용)
- 보고서 목차·대시보드와의 불일치 방지: 대시보드의 `이상 없음` 카드는 항상 표시되나 0 표기 (기본 동작 유지)
- 섹션 헤딩 `## 안전 판정 항목`만 남고 하위 소분류 없는 빈 헤딩은 금지 (`build_safe_section`이 헤딩 포함 전체 생성 후 반환, 생성 자체를 생략)
  - `reopen`: evaluate가 모순 발견 시 true (evaluate_phase1 재호출 요청)
  - `retries`: evaluate_phase1 재실행 횟수 (상한 2)
  - `conflicts`: 모순 내역 배열 (`[{round: 1, description: "..."}]`)
  - `requires_human_review`: 2회 초과 시 true (Phase 2 진입 block)

**하위 호환 fallback**:
- `phase1_validated` 필드 부재 시 `false`로 간주
- `phase1_eval_state` 부재 시 빈 객체로 초기화 (`{reopen: false, retries: 0, conflicts: [], requires_human_review: false}`)
- 구버전 master-list.json은 자동 마이그레이션하지 않는다 (신규 스캔부터 적용)

---

## §13. Assert 스크립트 Exit code 통일 테이블

두 assert 스크립트(`assert_phase1_validated.py`, `assert_status_complete.py`)는 **동일 exit code 네임스페이스**를 공유한다. 오케스트레이터는 어느 스크립트가 반환했든 같은 코드는 같은 의미로 해석한다.

| Exit code | 의미 | Blocking | 후속 조치 |
|-----------|------|---------|----------|
| `0` | pass | — | 다음 단계 진행 |
| `1` | incomplete / invalid state | Yes | 해당 단계 재호출 (evaluate_phase1 또는 evaluate) |
| `2` | human_review_block | **Yes** | `--accept-human-review=ID1,ID2` 명시 승인 필요. 전역 승인 금지. |
| `3` | rederivation_warn (또는 기타 비차단 경고) | No | 기록·모니터링만, 다음 단계 진행 가능 |
| `4` | reopen_pending | **Yes** | `phase1_eval_state.reopen=true` 후보 존재. evaluate_phase1 재호출 필요 (retries 증분) |
| `5` | lint 위반 | Yes | checklist §12-H 위반 (Phase 1 원본 직접 참조) 수정 필요 |
| `6` | missing_placeholder | Yes | 스켈레톤에 `<!-- SAFE_SECTION_HERE -->` 등 필수 플레이스홀더 누락. 스켈레톤 작성자 재호출 |
| `7` | safe_bucket_unclassified | Yes | `_classify_safe()`가 분류하지 못한 safe 후보 존재. `safe_category` 필드 명시 또는 `phase1_discarded_reason` 키워드 보완 필요 |

**규약**:
- assert_phase1_validated.py는 `0/1/2/3/4/5` 모두 사용 가능
- assert_status_complete.py도 동일 테이블 사용 (과거 `2=rederivation_warn`은 `3`으로 이동)
- 신규 assert 스크립트는 이 테이블 준수 필수
- 오케스트레이터(SKILL.md)는 exit code → 조치 매핑을 SKILL.md Step 3-2.5 / Step 3-5.5 각 단계에 명시
