# Phase 2 동적 테스트 에이전트 공통 지침

Phase 2(동적 테스트)를 에이전트로 실행할 때 따르는 공통 지침이다.

> `[필수]`는 과거 위반 이력이 있어 추가 강조된 항목이다. 태그가 없는 항목도 모두 준수 의무가 있다.

## 지침 1: 보고서 파일 생성 금지 + 결과 파일 저장

**최종 보고서 파일(noah-sast-report.md/html)을 절대 생성하지 않는다.** 단, 동적 테스트 결과를 `<PHASE1_RESULTS_DIR>/<scanner-name>-phase2.md`에 Write 도구로 저장한다. 저장 후 텍스트로 후보 건수 요약도 반환한다.

## 지침 2: 개별 스캐너 phase2.md의 유의사항 준수

**[필수] 해당 스캐너의 phase2.md를 반드시 읽고, 그 안의 유의사항(세션 관리, 판정 기준, 테스트 도구 선택 기준 등)을 그대로 따른다.**

**[필수] phase2.md가 Playwright를 요구하는 경우(SPA XSS, DOM XSS 등), `playwright` 또는 `npx playwright` 명령을 직접 실행하여 테스트한다. 실행이 성공하면 테스트를 완료한다. curl로만 테스트하고 "확인 불가"로 남기지 않는다. Playwright 명령이 실제로 실패(command not found, 설치 오류)한 경우에만 `[도구 한계]`로 표시할 수 있다.**

## 지침 3: 모든 후보 빠짐없이 테스트 및 반환

**[필수] Phase 2 테스트 시작 전, 테스트에 필요한 식별자(포스트 ID, 채널 ID 등)를 소스코드 분석 또는 HTTP 요청으로 먼저 획득한다. `<placeholder>` 형태를 curl 명령에 남기지 않는다.** 직접 획득이 불가능한 정보(외부 콜백 URL, OTP 등)만 사용자에게 요청한다.

**[필수] 각 취약점의 재현 방법 및 POC는 반드시 두 파트로 나눠 작성한다:**

```
**재현 방법 및 POC**:
[실제 실행한 curl 명령 또는 Playwright 스크립트 — 플레이스홀더 없이]

**동적 테스트 실행 결과**:
[curl: HTTP 상태코드 + Content-Type + 응답 본문 중 취약점 증거 포함 부분 발췌]
[Playwright: alert 발화 메시지 또는 DOM에 페이로드 삽입 확인 출력]
```

**동적 테스트 실행 결과** 파트가 없거나 비어 있으면 테스트를 실행하지 않은 것으로 간주한다.

**[필수] Phase 2 결과는 반드시 아래 형식의 테이블을 포함하여 반환한다.**

```
## Phase 2 테스트 결과 요약

| ID | 후보 제목 | 테스트 수행 | 결과 | 미수행 사유 |
|----|----------|------------|------|------------|
| [스캐너ID] | [후보 제목] | ✓ 또는 ✗ | [결과 또는 —] | [사유 또는 —] |
...
```

- 테스트 수행 ✓: 동적 테스트를 실제 실행한 경우. 미수행 사유 칸은 `—`.
- 테스트 수행 ✗: 반드시 `[도구 한계]`/`[정보 부족]`/`[환경 제한]` 중 하나를 사유로 명시. 실행을 시도하지 않고 미설치로 추정하여 `[도구 한계]`로 표시하는 것은 허용하지 않는다.

### 결과 파일 저장 (지침 1 참조)

모든 테스트 완료 후, 결과를 `<PHASE1_RESULTS_DIR>/<scanner-name>-phase2.md`에 Write 도구로 저장한다. 파일 형식:

```markdown
# <scanner-name> Phase 2 결과

## <ID>: <후보 제목>
### POC
[실행한 curl/Playwright 명령]
### 실행 결과
[응답 status + body 발췌]
### 관찰 사항
[alert 발화 여부, DOM 변경, 차단 응답 등]

(각 후보마다 반복)

<!-- NOAH-SAST PHASE2 MANIFEST v2 -->
```json
{
  "scanner": "<scanner-name>",
  "schema_version": 2,
  "results": [
    {
      "id": "XSS-1",
      "evidence": {
        "commands": ["curl -X GET 'https://sandbox-developers.kakao.com/...' -H 'Cookie: ...'", "playwright script ..."],
        "responses": {"http_status": 200, "body_excerpt": "...<img onerror=alert(1)>..."},
        "observations": ["alert fired twice", "window.__xss_fired=true", "DOM contains raw onerror"]
      }
    },
    {
      "id": "XSS-2",
      "evidence": {
        "commands": ["curl -X POST 'https://sandbox-developers.kakao.com/api/..' ..."],
        "responses": {"http_status": 403, "body_excerpt": "Query depth exceeds maximum"},
        "observations": ["blocked with specific vector reference"],
        "blocking_layer_hint": {"suspected": "gateway", "rationale": "response mentions depth limit"},
        "defense_code_hints": [{"file": "...", "lines": "40-52", "reason": "suspected block logic"}]
      }
    },
    {
      "id": "XSS-3",
      "evidence": {
        "commands": ["curl -X POST ..."],
        "responses": {"http_status": 400, "body_excerpt": "-"},
        "observations": ["generic error, no vector reference"],
        "blocking_layer_hint": {"suspected": "backend", "rationale": "generic 400"}
      }
    }
  ]
}
```
<!-- /NOAH-SAST PHASE2 MANIFEST -->
```

**[필수] status 필드를 manifest에 기록하지 않는다.** status 할당은 `scan-report-review`가 `mode=evaluate`로 호출될 때 수행한다 (`sub-skills/scan-report-review/evaluate.md` §판정 플로우, `_contracts.md §5` 판정×태그별 필수 필드 매트릭스).

**evidence 객체 스키마 (v2)**:
- `commands` (필수): 실행한 curl/Playwright 등 명령 리터럴 배열
- `responses` (필수): `{http_status: int, body_excerpt: str ≤512B}` (과도하면 hash + 길이만)
- `observations` (필수): 관찰 사실 배열 (≤10개 항목). "성공한 것 같다" 같은 수식어 금지, 사실만
- `blocking_layer_hint` (선택, 차단된 경우): `{suspected: str, rationale: str}` — Phase 2의 **힌트**이며 확정 아님
- `defense_code_hints` (선택, 방어 코드 의심): `[{file, lines, reason}]` — 해시/확정은 리뷰 전속

**크기 상한**: 후보당 evidence JSON ≤ 4KB. 초과 시 `body_excerpt`를 해시로 대체.

**해당 없는 필드는 생략**한다. `null` placeholder 금지 (`sub-skills/scan-report-review/_contracts.md §4` Phase 2 Manifest v2 스키마 제약: "기록을 위한 기록" 방지).

파일 저장 후 텍스트 반환에는 **후보별 실행 요약(1~2줄)과 건수 통계**만 포함하며, 스스로 "확인됨/안전/후보" 판정을 내리지 않는다. 판정은 별도 평가 리뷰 단계가 수행한다.

## 지침 4: 심각도 평가 금지

**취약점에 심각도(High, Medium, Low, Critical 등)를 부여하지 않는다. 상태는 "확인됨", "후보", "안전"으로만 구분한다.**

## 지침 5: Bash 호출 순차 실행

**[필수] Bash(curl) 호출을 1건씩 순차적으로 실행한다. 병렬 curl 호출 금지.** (순차 실행 시 첫 승인 이후 자동 승인. 병렬 호출 시 1건 거부로 전체 연쇄 취소)

**예외 — Race Condition 테스트**: 단일 Bash 도구 호출 내부에서 쉘 백그라운드(`&` + `wait`)로 동일 요청을 동시 발사하는 것은 허용한다. 이는 race/TOCTOU 재현에 필수이며 도구 승인 단위는 여전히 1건이다. 별도 Bash 도구 호출을 동시에 발사하는 것만 금지된다.

## 지침 6: 내용 없는 빈 섹션 반환 금지

**[필수] 해당 스캐너에서 테스트 결과가 모두 "안전"인 경우, 결과 테이블만 반환한다.**

---

## 지침 7: 모든 스캐너 phase2.md에 자동 적용되는 공통 절차/기준

> 아래 절차와 검증 기준은 41개 스캐너 phase2.md 어디에도 더 이상 인라인으로 기재되지 않는다. 모든 phase2.md에 자동 적용된다.

**공통 시작 절차 (Phase 2 진입):**
- **[필수] 프롬프트에 제공된 Phase 1 평가본 경로(`<PHASE1_RESULTS_DIR>/evaluation/<scanner-name>-eval.md`)를 Read 도구로 읽어 테스트할 후보 목록을 확인한다.** 이 파일에 해당 스캐너의 모든 후보와 `evaluate_phase1`이 부여한 `CONFIRM` / `OVERRIDE` / `DISCARD` 판정이 기록되어 있다. Phase 1 원본(`<PHASE1_RESULTS_DIR>/<scanner-name>.md`) 직접 참조는 금지(`sub-skills/scan-report-review/_contracts.md §6` C1 lint). 평가본이 부재하면 원본을 fallback으로 사용하되 반환에 `[FALLBACK: eval MD 부재]` 표기.
- **[필수] DISCARD 판정 후보는 동적 테스트 대상에서 제외한다.** 평가본의 `### Override 여부` 섹션이 `DISCARD`인 후보는 이미 `status: safe`로 확정되었으며 Phase 2 테스트 수행은 토큰 낭비. 반환 테이블에 "DISCARD skip: N건 (ID 목록)"으로만 표기한다.
- 후보가 존재하는 경우에만 동적 테스트를 진행한다. 후보가 0건이면 동적 테스트 없이 결과를 반환한다.
- 사용자에게는 테스트 대상 도메인(Host)과 직접 획득이 불가능한 정보(외부 콜백 서비스 URL, 프로덕션 전용 자격 증명 등)만 요청한다. 그 외의 정보는 소스코드 분석 또는 관련 엔드포인트에 직접 HTTP 요청을 보내 획득한다.
- 사용자가 동적 테스트를 원하지 않거나 정보를 제공하지 않으면, 소스코드 분석 결과의 모든 후보를 evidence 없음(미수행)으로 기록한 채 결과를 반환한다. status 할당은 별도 평가 리뷰가 수행한다.

**판정 책임의 분리 (v2 스키마)**:

- Phase 2 에이전트는 **증거 수집자**이다. status 필드(확인됨/후보/안전)를 할당하지 않는다.
- status 할당은 `scan-report-review`가 `mode=evaluate`로 수행한다 (`sub-skills/scan-report-review/evaluate.md`, `_contracts.md §1` Writer 권한 및 `§5` 판정×태그 매트릭스).
- Phase 2 에이전트는 **evidence 생성 품질**에 책임을 진다: 판정자가 confirmed/safe를 내릴 수 있을 만큼 충분한 정보(공격 성공 지표, 차단 계층, 방어 코드 의심 위치)를 evidence 객체에 담아야 한다.

**evidence 생성 품질 가이드 (판정에 필요한 정보 사전 수집)**:

Phase 2 에이전트가 수집해야 할 정보는 판정자가 `sub-skills/scan-report-review/evaluate.md` §판정 플로우를 수행할 수 있는 수준이어야 한다.

1. **공격 성공 가능성이 있는 경우** (확인됨 후보):
   - `commands`: 실제 실행한 명령 리터럴
   - `responses`: HTTP 상태 + 본문 발췌 (공격 성공 지표 포함 구간)
   - `observations`: alert 발화, DOM 변경, 데이터 반환 등 관찰 사실

2. **차단된 경우** (safe 또는 candidate 차단 후보):
   - 응답이 공격 벡터를 구체적으로 언급하면 (예: `"Query depth exceeds maximum"`) `blocking_layer_hint.rationale`에 인용
   - 제네릭 에러(400/500)면 `blocking_layer_hint.rationale`에 "generic error, no vector reference" 기록
   - 방어 코드가 분석 대상 프로젝트 내에 있으면 `defense_code_hints`에 file/lines/reason 기록 (해시는 리뷰가 확정)
   - 프로젝트 외부 서비스(백엔드 resolver 등)이면 `blocking_layer_hint.suspected: "external"` 명시

3. **테스트 미수행** (candidate 후보):
   - 도구 미설치: `commands`에 시도 명령 + `observations`에 도구 오류 메시지
   - 정보 부족: `observations`에 "요청한 정보: <목록>"
   - 환경 제한: `commands` + `responses` + `observations`에 제한 유형 명시

**원칙**: Phase 2 에이전트는 "차단이 유효한지" 자기 판단하지 않는다. 차단의 근거(응답 본문, 의심되는 방어 코드)를 evidence로 남기고, 최종 safe/candidate 판정은 리뷰에게 맡긴다. Phase 1의 "불명확 → 보수적 유지"와 동일 원칙이 Phase 2에도 적용된다.

## 지침 8: 공통 에러 핸들링

동적 테스트 중 발생하는 HTTP 에러와 연결 문제에 대한 대응 절차이다.

### HTTP 상태 코드별 대응

| 상태 코드 | 의미 | 대응 |
|-----------|------|------|
| 403 Forbidden | WAF 차단 또는 접근 거부 | 아래 WAF 차단 대응 절차를 따른다 |
| 429 Too Many Requests | Rate Limit | `Retry-After` 헤더 확인 → 해당 시간만큼 대기 후 재시도. 헤더 없으면 10초 대기. 요청 간 최소 2초 간격 유지 |
| 301/302 → 로그인 페이지 | 세션 만료 또는 미인증 | 지침 9의 세션 갱신 절차를 따른다 |
| 500 Internal Server Error | 서버 에러 | **에러 메시지를 분석한다** — SQL 에러, 스택 트레이스, 역직렬화 에러 등은 취약점 지표일 수 있다. 에러 내용을 후보 판정에 활용한다 |
| 400 Bad Request | 입력 검증 실패 | 에러 메시지 확인 — 입력 검증에 의한 차단이면 우회 기법을 시도한다. 형식 오류면 페이로드 형식을 수정한다 |

### WAF 차단 대응 절차

WAF 차단 시그니처: `403` + 응답 본문에 Cloudflare/AWS WAF/Akamai/ModSecurity 등의 식별자

1. 기본 페이로드가 차단되면, 해당 스캐너 phase2.md의 **우회 페이로드** 섹션을 시도한다
2. 우회 페이로드도 차단되면, 인코딩 변형을 시도한다: URL encoding → double encoding → Unicode encoding
3. 모든 우회 시도가 차단되면 `후보 (WAF 차단, 우회 실패)`로 보고한다. 테스트를 포기하되 `[도구 한계]`가 아닌 구체적 사유를 기재한다

### 연결 에러 대응

| 에러 | 대응 |
|------|------|
| Connection refused | 포트/프로토콜 확인 (HTTP vs HTTPS). 소스코드에서 서버 바인딩 포트 확인. 1회 재시도 |
| Connection timeout | `-m 30` 타임아웃 옵션 추가. 1회 재시도. 실패 시 `[환경 제한]` |
| SSL certificate error | sandbox 도메인이면 `-k` 플래그 사용 가능. 사용자에게 확인 후 진행 |

---

## 지침 9: 공통 인증/세션 획득 절차

동적 테스트에 필요한 인증 세션을 획득하는 공통 절차이다.

### 세션 획득 우선순위

1. **사용자 제공 세션 사용** (가장 확실): 사용자가 Step 3-3에서 제공한 쿠키/토큰을 사용한다
2. **curl로 로그인 API 호출**: 소스코드에서 로그인 엔드포인트(`/auth/login`, `/api/login` 등)를 파악하고, curl로 로그인하여 세션 쿠키/토큰을 추출한다
   ```
   # 세션 쿠키 추출 예시
   curl -v -X POST "https://target.com/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"testpass"}' 2>&1 | grep -i "set-cookie"
   ```
3. **Playwright로 로그인 플로우 자동화**: SSO, OAuth, SAML 등 복잡한 인증은 Playwright로 브라우저 로그인 후 쿠키를 추출한다

### 세션 만료 시 갱신

1. refresh token이 있으면 자동 갱신을 시도한다
2. 자동 갱신 실패 시 위 획득 우선순위의 2번(curl 로그인)을 재시도한다
3. 2번도 실패하면 사용자에게 새 세션을 요청한다

### 다중 계정 테스트 (IDOR, CSRF 등)

- 계정 A와 계정 B의 세션을 별도 변수로 관리한다
- 계정 A의 세션으로 계정 B의 리소스에 접근하는 패턴으로 테스트한다
- 사용자에게 2개 계정의 자격 증명을 한번에 요청한다

---

## 지침 10: 응답 분석 공통 원칙

동적 테스트 응답을 분석하여 확인됨/안전을 판정하는 공통 원칙이다.

### Time-based 테스트 (SQLi, Command Injection, ReDoS 등)

1. **기준선 측정 필수**: 페이로드 없는 정상 요청의 응답 시간을 먼저 3회 측정한다
2. **유의미한 차이 기준**: 기준선 대비 3초 이상 지연이 있어야 양성으로 판단한다
3. **3회 반복 측정**: 양성 의심 시 동일 페이로드로 3회 반복하여 일관된 지연이 관찰되는지 확인한다
4. **curl 시간 측정**: 모든 time-based 테스트에 `-w "\ntime_total: %{time_total}\n"` 옵션을 추가한다

### 오탐 식별 기준

| 응답 유형 | 판단 |
|-----------|------|
| WAF 차단 페이지 (403 + 보안 벤더 시그니처) | 안전이 아닌 "차단됨" — 우회 시도 필요 |
| 입력 검증 에러 메시지 ("invalid format", "validation failed") | 안전 (입력 검증이 동작) |
| 페이로드가 이스케이프되어 반영 (`&lt;script&gt;`) | 안전 (출력 인코딩이 동작) |
| 페이로드가 그대로 반영되지만 실행되지 않음 (Content-Type: application/json) | 컨텍스트 확인 필요 |
| 500 에러 + 기술적 에러 메시지 | **취약점 지표일 수 있음** — 에러 메시지를 분석한다 |

### 응답 비교 방법론 (Boolean-based 테스트)

1. 참 조건(`1=1`)과 거짓 조건(`1=2`)의 응답을 각각 캡처한다
2. 비교 항목: (a) HTTP 상태 코드, (b) 응답 본문 길이, (c) 응답 본문 내용
3. 상태 코드 또는 본문 길이에서 유의미한 차이가 있으면 양성 의심
4. 거짓 양성 배제: 정상 파라미터와 비정상 파라미터(숫자가 아닌 문자열 등)의 응답도 비교하여, 단순 입력 오류와 SQL 조건 차이를 구분한다

---

## 지침 11: 도메인 분류 및 prod 환경 차단

**[필수] 동적 테스트의 첫 curl/Playwright 실행 전에, 사용자가 제공한 도메인을 분류한다. prod 환경으로 분류되면 동적 테스트를 수행하지 않는다.**

### 도메인 분류 기준

**sandbox/dev 지표** (하나 이상 해당 → sandbox 가능):
- 호스트명에 `sandbox`, `dev`, `test`, `local`, `qa`, `stg`, `alpha`, `beta`, `canary` 포함
- `localhost`, `127.0.0.1`, `0.0.0.0`, `10.*`, `172.16-31.*`, `192.168.*` 대역
- 포트가 비표준(`3000`, `8080`, `8443`, `9000` 등)

**prod/금지 환경** (하나 이상 해당 → **동적 테스트 절대 금지**):
- 호스트명이 `www.`, `api.`, `app.`, `m.` + 프로덕션 도메인 (예: `api.example.com`, `www.example.com`)
- 호스트명에 sandbox/dev 키워드가 전혀 없는 공개 도메인
- `cbt` 포함 — 고객 수용 테스트 환경은 prod 데이터를 사용하므로 **prod와 동일하게 금지**
- `staging` 포함 — prod 데이터를 복제한 환경일 수 있으므로 **금지**
- 알려진 프로덕션 CDN/도메인 (사내 도메인 정책에 따라 판단)

### 분류 절차

1. 사용자가 도메인을 제공하면, 위 기준으로 분류한다.
2. **sandbox 확정** → 동적 테스트 진행.
3. **prod/cbt/staging 확정** → 동적 테스트 **절대 금지**. 사용자에게 sandbox URL 제공을 요청한다.
4. **분류 불명** → 사용자에게 명시적으로 확인: "제공하신 `<domain>`이 sandbox 환경이 맞습니까? prod/cbt/staging 환경에서는 동적 테스트를 수행하지 않습니다." 사용자가 sandbox라고 확인한 경우에만 진행.

### curl 실행 전 도메인 체크

모든 curl/Playwright 명령 실행 전, 요청 URL의 호스트가 분류 완료된 sandbox 도메인과 일치하는지 확인한다. 분류되지 않은 도메인으로의 요청은 실행하지 않는다 (예: 리다이렉트로 다른 호스트에 도달한 경우).

---

## 공통 유의사항

- **[필수] 모든 동적 테스트는 지침 11의 분류 절차를 통과한 sandbox 도메인에서만 수행한다. prod, cbt, staging 도메인에서는 동적 테스트를 절대 수행하지 않는다.**
- 동적 테스트 시 파괴적인 행위를 절대 수행하지 않는다 (회원탈퇴, 데이터 삭제, 비밀번호 변경 등).
- 동적 테스트 중 세션이 만료된 경우, 자동 갱신 가능한 모든 경로를 시도한다. 자동 갱신이 불가능하면 즉시 사용자에게 새 세션을 요청하고, 새 세션을 받은 후 중단된 테스트를 이어서 수행한다. 세션 만료를 이유로 동적 테스트를 포기하지 않는다.
- **"확인됨"은 동적 테스트에서 실제 트리거를 확인한 경우에만 부여한다.**
- 동적 테스트 중 도구 실행이 차단되면, 사용자에게 해당 도구의 권한 허용을 요청한다. 도구 차단을 이유로 동적 테스트를 포기하지 않는다.
