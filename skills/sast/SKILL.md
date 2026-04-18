---
name: sast
description: "41개 취약점 스캐너 + AI 자율 탐색을 실행하고 결과를 통합 보고서로 작성하는 스킬. XSS, SSRF, SQLi, CSRF, TLS, 비즈니스 로직 등 모든 취약점 유형을 소스코드 분석, AI 자율 탐색, 동적 테스트로 점검한다. 사용자가 'noah-8719:sast', 'sast', '소스코드 취약점 스캔' 등을 요청할 때 이 스킬을 사용한다."
---

# Noah SAST — 통합 취약점 스캐너

41개 개별 취약점 스캐너와 AI 자율 탐색을 실행하고, 모든 결과를 하나의 통합 보고서로 작성하는 스킬이다.

> `[필수]`는 규약 강제 항목이다. 태그가 없는 항목도 모두 준수 의무가 있다.

## 실행 프로세스

### Step -1: NOAH_SAST_DIR 경로 결정

**[필수] 모든 Step보다 먼저 실행한다.** 이 스킬의 루트 디렉토리 절대 경로를 결정한다. 모든 스캐너와 유틸리티가 이 디렉토리 하위에 있다.

`NOAH_SAST_DIR`은 다음 경로이다:

```
${CLAUDE_PLUGIN_ROOT}/skills/sast
```

> `${CLAUDE_PLUGIN_ROOT}`는 Claude Code가 플러그인 로드 시 자동 치환하는 변수이다. 치환되지 않은 경우(리터럴 문자열 그대로 보이는 경우), 아래 Bash fallback을 실행한다:
>
> ```bash
> for base in "$HOME/.claude/skills/noah-8719" "$HOME/.claude/skills/noah-sast" "$HOME/.claude/plugins/noah-8719"; do
>   if [ -d "$base/skills/sast/scanners" ]; then cd "$base/skills/sast" && pwd; break; fi
> done
> ```

이 값을 `NOAH_SAST_DIR` 변수로 보관한다. 이후 모든 경로 참조에 사용한다. 서브 에이전트 프롬프트에는 `<NOAH_SAST_DIR>`을 변수명이 아닌 **resolve된 실제 경로 문자열**로 치환하여 삽입한다. 서브 에이전트가 경로를 스스로 결정하거나 해석하도록 맡기지 않는다.

**디렉토리 구조:**
```
<NOAH_SAST_DIR>/                   ← ${CLAUDE_PLUGIN_ROOT}/skills/sast
  SKILL.md                         ← 이 파일 (오케스트레이터)
  prompts/                         ← 서브 에이전트 지시 문서
    guidelines-phase1.md           ← Phase 1 공통 지침
    guidelines-phase2.md           ← Phase 2 공통 지침
    grep-agent.md                  ← grep 인덱싱 에이전트 프롬프트
    phase1-group-agent.md          ← Phase 1 그룹 에이전트 프롬프트
    ai-discovery-agent.md          ← AI 자율 취약점 탐색 에이전트 프롬프트
    phase2-agent.md                ← Phase 2 동적 테스트 에이전트 프롬프트
  scanners/                        ← 41개 취약점 스캐너
    xss-scanner/
    sqli-scanner/
    ...
  tools/                           ← Python 유틸리티 스크립트
    scanner-selector.py
    build-master-list.py
    update-phase2-status.py
    validate_actuator.py
  sub-skills/                      ← 내부 서브스킬
    scan-report/
    scan-report-review/
    chain-analysis/
  tests/                           ← grep 커버리지 테스트
```

### Step 0: 전체 패턴 사전 인덱싱 (grep 인덱싱 에이전트)

**[필수] Step 1 진입 전에 반드시 완료한다.** 개별 취약점 스캐너 에이전트가 코드베이스를 중복 탐색하는 것을 방지하기 위해, **grep 인덱싱 에이전트**를 생성하여 모든 패턴 인덱싱을 위임한다. 메인 에이전트는 파일 경로와 카운트 요약만 수신한다.

#### Step 0-1: grep 인덱싱 에이전트 생성

**[필수] grep 인덱싱 에이전트 생성 전에 메인 에이전트가 직접 Bash로 고유 경로를 생성한다.**

아래 Bash 명령을 실행하여 완성된 디렉토리 경로 문자열을 얻는다:

```bash
echo "/tmp/scan_index_$(basename <PROJECT_ROOT>)_$(date +%s)"
```

예시 출력: `/tmp/scan_index_storychannel_1711700000`

이 출력값을 `PATTERN_INDEX_DIR` 변수로 보관한다. grep 인덱싱 에이전트 프롬프트에는 이 **완성된 경로 문자열**을 그대로 삽입한다. grep 인덱싱 에이전트가 경로를 스스로 생성하거나 해석하도록 맡기지 않는다.

동일하게 Phase 1 결과 디렉토리 경로도 생성한다:

```bash
echo "/tmp/phase1_results_$(basename <PROJECT_ROOT>)_$(date +%s)"
```

이 출력값을 `PHASE1_RESULTS_DIR` 변수로 보관한다. Phase 1 그룹 에이전트가 스캐너별 분석 결과를 이 디렉토리에 파일로 저장한다. 서브 에이전트 프롬프트에는 `<PHASE1_RESULTS_DIR>`을 **resolve된 실제 경로 문자열**로 치환하여 삽입한다.

Agent 도구로 grep 인덱싱 에이전트를 생성한다. **[필수] 메인 에이전트는 grep 프롬프트 본문을 인라인으로 복사하지 않는다.** 대신 아래 한 줄 프롬프트를 그대로 사용하되, `<NOAH_SAST_DIR>`/`<PROJECT_ROOT>`/`<PATTERN_INDEX_DIR>` 세 변수를 **resolve된 실제 경로 문자열**로 치환한다.

```
<NOAH_SAST_DIR>/prompts/grep-agent.md를 Read 도구로 읽고 그 안의 지시를 정확히 따르세요.
변수: NOAH_SAST_DIR=<NOAH_SAST_DIR>, PROJECT_ROOT=<PROJECT_ROOT>, PATTERN_INDEX_DIR=<PATTERN_INDEX_DIR>
```

`prompts/grep-agent.md`에는 단계 1~4(통합 패턴 파일 읽기, INCLUDE/EXCLUDE 화이트리스트, JSON 저장 형식, 카운트 요약 반환)이 한 글자도 빠지지 않고 정의되어 있으므로, 메인 에이전트는 본문을 절대 축약·재작성·재인용하지 않는다.

---

#### Step 0-2: 패턴 인덱스 디렉토리 경로 및 카운트 요약 수신

grep 인덱싱 에이전트가 반환한 **카운트 요약**을 보관한다. 디렉토리 경로는 Step 0-1에서 메인 에이전트가 직접 생성한 `PATTERN_INDEX_DIR` 값을 그대로 사용한다.

- 카운트 요약 → 보관만 (출력 의무 없음)
- 디렉토리 경로 → 각 개별 취약점 스캐너 에이전트에 전달 (에이전트는 `<PATTERN_INDEX_DIR>/<스캐너명>.json` 파일만 읽음)

**[필수] 메인 에이전트는 패턴 인덱스 파일을 직접 읽지 않는다. 디렉토리 경로만 전달한다.**

**[필수] 반환 직후 드리프트 검증 (Step 1 진입 전 반드시 수행):**

grep 에이전트가 "스크립트 작성 후 실행 없이 종료"하는 드리프트를 보일 수 있으므로, 메인 에이전트가 Bash로 실제 결과물을 검증한다:

```bash
JSON_COUNT=$(ls -1 <PATTERN_INDEX_DIR>/*.json 2>/dev/null | wc -l | tr -d ' ')
STRAY=$(ls -1 <PATTERN_INDEX_DIR> 2>/dev/null | grep -vE '^[a-z0-9-]+-scanner\.json$' | tr '\n' ' ')
echo "json_count=$JSON_COUNT"
echo "stray=$STRAY"
```

판정:
- `json_count` == 적용 스캐너 수 (41 이하, scanner-selector.py 실행 전이면 41 기준) 이면 정상 → Step 1 진행
- `json_count == 0` 또는 `stray`에 `run_scan.py`/`runner*.py`/`_batch*.json` 등 **비-스캐너 파일이 남아있음** → **드리프트**. grep 에이전트를 즉시 재실행한다. 재실행 프롬프트에는 "이전 시도가 스크립트 파일(`run_scan.py` 등)만 남기고 JSON 인덱스를 생성하지 않았음. Bash 도구로 grep을 직접 호출하여 JSON 파일을 실제로 저장할 것"을 명시한다.
- 재실행 후에도 `json_count == 0`이면 프로젝트 크기 분할(서브디렉토리별 PROJECT_ROOT로 나누기)을 검토한다.

그 외 `[INCOMPLETE: scanner-name]`이 반환에 포함된 경우는 해당 스캐너만 별도로 grep을 재실행한다.

---

### Step 1: 프로젝트 스택 파악

모든 스캐너에 공통으로 필요한 프로젝트 정보를 먼저 파악한다:
- `package.json`, `requirements.txt`, `pom.xml`, `Gemfile` 등에서 프레임워크/언어/라이브러리 확인
- 프로젝트 구조 파악 (서버, 클라이언트, 설정 파일 위치)
- 인증 방식 확인 (세션, JWT, OAuth, SAML 등)
- DB 종류 확인 (SQL, NoSQL, LDAP 등)
- 프록시/CDN/로드밸런서 구조 확인
- **sandbox/dev 도메인 추출**: 환경별 설정 파일, 인프라 설정, CORS/OAuth 설정 등에서 sandbox/dev 도메인을 추출하여 `SANDBOX_DOMAINS`에 보관한다. 보고서 POC URL의 호스트 플레이스홀더를 실제 도메인으로 채우는 데 사용한다.

### Step 2: 적용 가능한 스캐너 선별

**기본 원칙: 포함이 기본이고, 제외에는 근거가 필요하다.**

#### Step 2-1: 제외 여부 결정 (자동화 스크립트)

> Step 0-2에서 수신한 카운트 요약은 보관만 하면 되며, 메인 에이전트가 별도 테이블로 출력할 의무는 없다. `scanner-selector.py`가 동일 정보를 더 풍부한 형태로 출력한다.

`scanner-selector.py`를 실행하여 grep 인덱스 + 프로젝트 아키텍처 기반으로 자동 선별한다:

```bash
python3 <NOAH_SAST_DIR>/tools/scanner-selector.py <PATTERN_INDEX_DIR> <PROJECT_ROOT>
```

스크립트 출력:
- 적용/제외 판정 테이블 (grep 히트 건수 + 사유 포함)
- 적용 스캐너 목록

**기본 원칙: 포함이 기본이고, 제외에는 근거가 필요하다.**
- grep 결과 1건 이상 → 반드시 포함
- grep 결과 0건 → 스크립트가 아키텍처 조건을 검사하여 제외 가능 여부 판단

#### Step 2-2: 스캐너 선별 결과 AI 검토

`scanner-selector.py`는 라이브러리 의존성 + grep 히트 수만으로 판단하므로 아래 케이스를 놓친다. 메인 에이전트가 제외된 스캐너 목록을 아래 체크리스트로 검토하여 복원 여부를 결정한다.

**검토 체크리스트 (제외된 각 스캐너에 대해):**

1. **커스텀 구현 확인**: 알려진 라이브러리 없이 네이티브 API로 직접 구현한 경우가 있는가?
   - 예: `fetch()` (Node 18+ 내장)로 서버사이드 HTTP 요청 → SSRF 스캐너 복원
   - 예: `net/http` (Go 표준 라이브러리)로 HTTP 요청 → SSRF 스캐너 복원
   - 예: `string.format()` + `cursor.execute()` (Python 내장)으로 SQL 쿼리 → SQLi 스캐너 복원
   - 예: `xml.etree.ElementTree` (Python 내장)으로 XML 파싱 → XXE 스캐너 복원

2. **프레임워크 내장 기능 확인**: 프레임워크 자체가 해당 기능을 제공하는 경우가 있는가?
   - 예: Spring의 `RestTemplate`/`WebClient` → SSRF 스캐너 복원
   - 예: Rails의 `render inline:` → SSTI 스캐너 복원
   - 예: Django ORM의 `raw()`, `extra()` → SQLi 스캐너 복원

3. **멀티 언어 프로젝트**: `package.json`에 없지만 다른 언어 서브프로젝트에서 사용하는 경우가 있는가?
   - Step 1에서 파악한 프로젝트 스택 정보 활용

**적용**: 체크리스트에 해당하는 스캐너가 있으면 적용 목록에 복원한다. 검토 결과를 1줄 요약으로 기록하고 진행한다.

### Step 3: 정적 분석 → AI 자율 탐색 → 동적 분석 → 연계 분석

정적 분석(Step 3-1)은 선별된 모든 스캐너 에이전트를 **단일 응답에서 동시에** Agent 도구로 실행한다. AI 자율 탐색(Step 3-2)은 구조화된 스캐너가 놓칠 수 있는 취약점을 AI가 코드를 직접 읽으며 발견한다. 동적 분석(Step 3-5)은 세션 충돌 방지를 위해 순차 실행한다. 연계 분석(Step 3-6)은 동적 분석 결과(확인됨/후보/안전)를 반영하여 연계 시나리오를 도출한다. 각 스캐너는 자신의 phase1.md(소스코드 분석) → phase2.md(동적 테스트) 프로세스를 따른다.

#### Step 3-1: 정적 분석 (개별 스캐너의 Phase 1 실행)

**[필수] 선별된 스캐너를 `scanner-selector.py`가 출력한 그룹 편성에 따라 묶어, 그룹당 1개 에이전트로 실행한다.**

**그룹 편성**: Step 2-1에서 실행한 `scanner-selector.py`의 `--- 그룹 편성 ---` 출력을 그대로 사용한다. 이 스크립트는 의미적 연관성 기반 기본 그룹에서 시작하되, grep 히트 수 합계가 150건을 초과하거나 그룹 내 스캐너가 5개 이상이면 자동 분할한다. 적용 스캐너가 없는 그룹은 자동 제거된다.

**기본 그룹 (참고용, 실제 편성은 스크립트 출력을 따름):**

| 그룹 | 스캐너 |
|------|--------|
| url-navigation | xss, dom-xss, open-redirect |
| response-header | crlf-injection, host-header, http-method-tampering |
| db-query | sqli, nosqli |
| process-execution | command-injection, ssti |
| server-request | ssrf, pdf-generation |
| file-system | path-traversal, file-upload, zipslip |
| xml-serialization | xxe, xslt-injection, deserialization |
| auth-protocol | jwt, oauth, saml, csrf, idor, cookie-security |
| client-rendering | redos, css-injection, prototype-pollution |
| infra-config | http-smuggling, sourcemap, subdomain-takeover, security-headers, springboot-hardening, tls |
| data-export | csv-injection |
| protocol-check | graphql, websocket, soapaction-spoofing, ldap-injection, xpath-injection |
| business-logic | business-logic, validation-logic |

과부하 시 분할 예시: `auth-protocol`이 분할되면 → `auth-protocol-1` (jwt, oauth, saml) + `auth-protocol-2` (csrf, idor).

**[필수] Phase 1 에이전트는 단일 메시지 안에서 모든 그룹의 Agent 도구를 동시에 호출하여 병렬 실행한다.** 모든 에이전트가 완료된 후에만 Step 3-2로 진행한다. 완료 후 그룹 수와 수신된 결과 수를 대조하여, 누락된 에이전트가 있으면 해당 그룹만 재실행한다. 반환 요약에 `[INCOMPLETE: scanner-name]`이 있으면 해당 스캐너만 별도 그룹으로 재실행한다.

**Phase 1 결과 디렉토리 생성:** 그룹 에이전트 실행 전에 디렉토리를 생성한다.

```bash
mkdir -p <PHASE1_RESULTS_DIR>
```

**[필수] 메인 에이전트는 그룹 에이전트 프롬프트 본문(절차/결과 형식)을 인라인으로 복사하지 않는다.** 대신 아래 형식의 짧은 프롬프트를 사용한다. `<NOAH_SAST_DIR>`/`<PATTERN_INDEX_DIR>`/`<PHASE1_RESULTS_DIR>`는 resolve된 실제 경로 문자열로 치환한다.

```
<NOAH_SAST_DIR>/prompts/phase1-group-agent.md를 Read 도구로 읽고 그 안의 절차를 정확히 따르세요.
변수: NOAH_SAST_DIR=<NOAH_SAST_DIR>, PHASE1_RESULTS_DIR=<PHASE1_RESULTS_DIR>

이 그룹에서 분석할 스캐너:
- xss-scanner
  - phase1.md: <NOAH_SAST_DIR>/scanners/xss-scanner/phase1.md
  - 패턴 인덱스: <PATTERN_INDEX_DIR>/xss-scanner.json
  - 결과 파일: <PHASE1_RESULTS_DIR>/xss-scanner.md
- dom-xss-scanner
  - phase1.md: <NOAH_SAST_DIR>/scanners/dom-xss-scanner/phase1.md
  - 패턴 인덱스: <PATTERN_INDEX_DIR>/dom-xss-scanner.json
  - 결과 파일: <PHASE1_RESULTS_DIR>/dom-xss-scanner.md
- ...(그룹의 모든 스캐너)
```

`prompts/phase1-group-agent.md`에 파일 작성 형식과 공통 절차가 정의되어 있으므로, 메인 에이전트는 본문을 절대 축약·재작성·재인용하지 않는다.

> **주의: Phase 1 완료 시점에서 보고서 파일(.md/.html)을 생성하지 않는다.** 보고서는 Step 4에서만 작성한다.

**Phase 1 결과 검증 및 마스터 목록 생성:**

모든 그룹 에이전트가 완료되면, `build-master-list.py`를 실행하여 결과를 검증하고 후보 마스터 목록을 생성한다:

```bash
python3 <NOAH_SAST_DIR>/tools/build-master-list.py <PHASE1_RESULTS_DIR> <PHASE1_RESULTS_DIR>/master-list.json
```

스크립트 검증 항목:
- manifest `declared_count`와 실제 `## <ID>:` 헤더 수 일치
- manifest ID와 prose 헤더 교차 대조
- 필수 섹션(`### Code`, `### Source→Sink Flow` 등) 존재 및 최소 길이
- 동일 file:line 후보 그룹핑 (중복 sink 감지)

**ERROR 발생 시**: 해당 스캐너의 그룹 에이전트를 재실행한다.
**WARNING 발생 시**: 해당 후보의 결과 파일(`<PHASE1_RESULTS_DIR>/<scanner-name>.md`)을 확인하고 필요 시 보완한다.

**[필수] `DUPLICATE SINK` 경고 발생 시 — AI 자율 탐색(Step 3-2) 진입 전에 즉시 통합 여부를 결정한다:**

1. 두 후보의 Phase 1 결과 파일을 Read하여 관점 차이를 확인한다.
2. **의사 테스트**: 한 후보의 권장 조치만 적용해도 다른 후보가 해소되면 통합한다. `master-list.json`을 Edit하여 한쪽 후보를 `candidates` 배열에서 제거하고, 남은 쪽의 `scanner` 필드에 양쪽 스캐너를 모두 기록한다.
3. 의사 테스트가 "아니오"이거나 불확실하면 분리 유지한다.

생성된 `<PHASE1_RESULTS_DIR>/master-list.json`은 AI 자율 탐색(Step 3-2), 동적 분석(Step 3-5), 연계 분석(Step 3-6), 리포팅(Step 4) 전체에서 **단일 진실 원천(single source of truth)**으로 사용한다. **마스터 목록에 있는 후보는 동적 분석에서 "안전"으로 판정되지 않는 한, 반드시 최종 보고서에 포함되어야 한다.**

#### Step 3-2: AI 자율 취약점 탐색

Phase 1 정적 분석 완료 후, 구조화된 스캐너가 놓칠 수 있는 취약점을 AI가 자율적으로 탐색한다. 에이전트가 내부적으로 3단계 탐색(자유 탐색 → Phase 1 공백 영역 집중 → 잔여 영역)을 수행하고 결과를 저장한다.

**실행 절차:**

Agent 도구로 AI 자율 탐색 에이전트를 생성한다. `<NOAH_SAST_DIR>`/`<PHASE1_RESULTS_DIR>` 변수를 resolve된 실제 경로 문자열로 치환한다.

```
<NOAH_SAST_DIR>/prompts/ai-discovery-agent.md를 Read 도구로 읽고 그 안의 지시를 정확히 따르세요.
변수: PHASE1_RESULTS_DIR=<PHASE1_RESULTS_DIR>
Phase 1 마스터 목록: <PHASE1_RESULTS_DIR>/master-list.json (Read 도구로 읽어 Phase 1이 발견한 후보의 파일·라인·취약점 유형을 파악하세요)
프로젝트 컨텍스트: <PROJECT_CONTEXT>

3단계 탐색을 내부적으로 수행하세요:
1. 이 프로젝트의 소스코드를 분석하여 보안 취약점을 탐색하세요.
[전환] 1단계 탐색 후, master-list.json을 다시 Read하여 Phase 1이 어떤 스캐너에서 후보를 찾았고 어떤 스캐너가 이상 없음인지 재확인한 뒤 2단계로 넘어가세요.
2. Phase 1 커버리지를 바탕으로, Phase 1이 다루지 않은 영역을 집중 탐색하세요. 특히 비즈니스 로직 결함, 인증·인가 흐름 전체 경로, Race Condition, Mass Assignment처럼 grep 패턴으로는 잡기 어려운 취약점에 집중하세요.
[전환] 2단계 탐색 후, 지금까지 Read 도구로 열어본 파일과 디렉토리를 점검하고, 아직 열어보지 않은 영역을 파악한 뒤 3단계로 넘어가세요.
3. 미탐색 영역을 중심으로 취약점을 탐색하세요.

탐색 완료 후 "후보 등록 제외 기준" 7개 항목을 적용하여 걸러내고, "결과 파일 형식"에 따라 <PHASE1_RESULTS_DIR>/ai-discovery.md에 저장하라. 저장 전 "자기 검증" 절차를 수행하라.
반환 요약에 통과 후보 건수와 필터링 제외 건수를 함께 표기하라 (예: `ai-discovery: 후보 3건 (필터링 제외 2건)`).
```

**결과 파일 저장 및 마스터 목록 갱신:**

에이전트가 `<PHASE1_RESULTS_DIR>/ai-discovery.md`에 결과를 저장하고 후보 건수 요약을 반환한다. 이 파일은 하류의 동적 분석(Step 3-5), 연계 분석(Step 3-6), 보고서(Step 4)에서 Phase 1 스캐너 결과 파일과 동일하게 참조된다.

**`[INCOMPLETE]` 후속 탐색**: 반환에 `[INCOMPLETE]`이 포함된 경우, 탐색이 컨텍스트 한계로 중단된 것이다. 메인 에이전트는 반환의 "미탐색 영역" 정보를 활용하여 후속 탐색 에이전트를 디스패치한다. 후속 에이전트 프롬프트에는:
- 동일한 `ai-discovery-agent.md` Read 지시
- 이전 에이전트가 저장한 `ai-discovery.md`를 Read하여 이미 발견된 후보와 탐색 범위를 파악하라는 지시
- "미탐색 영역을 중심으로 자율 탐색하되, 이전 에이전트가 발견한 후보와 중복되지 않는 새로운 발견에 집중하라"는 안내

후속 에이전트의 결과는 `ai-discovery-continued.md`에 저장하고, 메인 에이전트가 두 파일의 후보를 `ai-discovery.md`로 통합한다. 후속 에이전트도 `[INCOMPLETE]`를 반환하면 저장된 후보만으로 진행한다 (무한 재시도 방지).

에이전트 응답을 확인한 후:

1. `<PHASE1_RESULTS_DIR>/ai-discovery.md`를 Read하여 manifest의 후보를 확인한다.
2. `AI-PENDING-N`을 `AI-1`, `AI-2`, ... 형식의 고유 ID로 재번호한다. `ai-discovery.md`의 `## AI-PENDING-N:` 헤더와 manifest ID도 함께 갱신한다.
3. `build-master-list.py`를 재실행하여 AI 결과를 포함한 전체 마스터 목록을 재생성하고 구조 검증한다:

```bash
python3 <NOAH_SAST_DIR>/tools/build-master-list.py <PHASE1_RESULTS_DIR> <PHASE1_RESULTS_DIR>/master-list.json
```

`ai-discovery.md`가 `<PHASE1_RESULTS_DIR>/` 디렉토리에 있으므로 스크립트가 자동 수집한다. ERROR 발생 시 `ai-discovery.md`의 해당 부분을 수정하고 재실행한다.

**Phase 1과의 중복 제거를 수행하지 않는다.** AI 자율 탐색과 Phase 1 스캐너가 같은 취약점을 발견하면 이중 검증으로 간주한다. 보고서에서 AI 자율 탐색 결과는 별도 섹션(`## AI 자율 탐색 결과`)으로 분리되므로 중복이 혼란을 주지 않는다.

AI 자율 탐색에서 후보가 0건이어도 정상이다. 스캐너가 이미 충분히 커버한 경우이며, "AI 자율 탐색: 추가 후보 없음"으로 기록하고 다음 단계로 진행한다.

#### Step 3-2.5: Phase 1 결과 평가 (evaluate_phase1)

AI 자율 탐색 완료 후, 동적 분석 정보 요청(Step 3-3) 진입 **전에** Phase 1 결과 품질 평가를 수행한다. 잘못된 후보가 Phase 2까지 흘러가는 낭비를 방지하기 위한 정적 정제 단계.

**호출 방식**: `scan-report-review`를 `mode=evaluate_phase1`로 호출.

```
Agent 도구로 평가 에이전트를 생성한다. <NOAH_SAST_DIR>/<PHASE1_RESULTS_DIR>는 resolve된 실제 경로 문자열로 치환.

<NOAH_SAST_DIR>/sub-skills/scan-report-review/SKILL.md를 Read하고 그 안의 mode=evaluate_phase1 절차를 따르세요.
변수: NOAH_SAST_DIR=<NOAH_SAST_DIR>, PHASE1_RESULTS_DIR=<PHASE1_RESULTS_DIR>
대상: master-list.json의 모든 후보
출력:
  1. <PHASE1_RESULTS_DIR>/evaluation/<scanner-name>-eval.md (각 후보의 Override 판정)
  2. master-list.json의 phase1_validated / phase1_discarded_reason / phase1_eval_state 필드 갱신

checklist.md §12의 blind eval 메커니즘을 반드시 적용하세요 (blind_read_phase1_md.py 헬퍼 사용).
```

**완료 후 검증**:
```bash
mkdir -p <PHASE1_RESULTS_DIR>/evaluation
python3 <NOAH_SAST_DIR>/tools/assert_phase1_validated.py \
  <PHASE1_RESULTS_DIR>/master-list.json \
  <PHASE1_RESULTS_DIR>
```

**exit code 처리**:
- `0`: 모든 후보 평가 완료 → Step 3-3 진행
- `1`: 평가 미완료 또는 eval MD 고아 상태 → evaluate_phase1 재호출
- `2`: `requires_human_review` 후보 존재 → 사용자에게 해당 후보 ID 목록 제시, 명시적 승인(`--accept-human-review=ID1,ID2`) 필요. 승인 없이 Step 3-3 진행 금지.

**Phase 2 진입 시 사용할 Phase 1 결과 경로**: `<PHASE1_RESULTS_DIR>/evaluation/<scanner>-eval.md` (Phase 1 원본 MD가 아님). 이후 Step 3-5(Phase 2) 에이전트 프롬프트는 eval MD를 Phase 1 결과로 참조한다 (checklist.md §12-H 강제).

#### Step 3-3: 동적 분석 정보 일괄 요청 → 사용자 응답 대기

`<PHASE1_RESULTS_DIR>/master-list.json`을 읽어 후보 목록을 확인하고(AI 자율 탐색에서 추가된 AI-N 후보 포함), 동적 테스트에 필요한 정보를 한번에 정리하여 사용자에게 요청한다. **이 시점에서 사용자의 응답을 기다린다. 보고서를 작성하지 않는다.**

```
## 동적 테스트 진행을 위해 필요한 정보

소스코드 분석 결과, 다음 취약점에서 후보가 발견되었습니다.
동적 테스트를 진행하려면 아래 정보를 제공해주세요:

1. **테스트 환경 URL (sandbox 도메인)**: https://sandbox-...
   ← 이 값은 보고서 개요 `**테스트 환경**` 필드와 모든 POC curl 명령어
      호스트의 **단일 진실 원천**이 됩니다. Step 1에서 추출된
      `SANDBOX_DOMAINS`가 있으면 그 값을 기본값으로 사용하고,
      비어 있으면 반드시 이 시점에 확정합니다.
2. **세션 쿠키/인증 토큰**: (로그인 후 쿠키 값)
3. **[XSS 후보 2건]**: 추가 정보 불필요
4. **[SSRF 후보 1건]**: 외부 콜백 서비스 URL (webhook.site 등)
5. **[OAuth 후보 1건]**: OAuth 인가 코드 (수동 획득 필요)
...

동적 테스트를 진행하시겠습니까? 필요한 정보를 제공해주세요.
```

사용자가 제공한 sandbox 도메인은 `SANDBOX_DOMAINS` 목록에 추가하고,
scan-report 서브에이전트 프롬프트에 전달하여 POC 호스트로 사용한다.
사용자가 동적 테스트를 명시적으로 거부하여 sandbox 도메인이 확정되지
않은 경우, 보고서 개요 `**테스트 환경**` 필드는 "해당 없음"으로
기재하고 모든 POC curl 호스트는 `<TARGET_HOST>` 플레이스홀더를
유지한다.

#### Step 3-4: 도구 권한 사전 확인

**절차:**

1. `~/.claude/settings.json` 및 프로젝트 `.claude/settings.json`을 **Read 도구로** 읽어 `permissions.allow` 배열을 확인한다.
2. 필요 권한은 경로에 따라 다르다:
   - **동적 테스트 수행 경로**: 아래 4개 모두 필요
     - `Bash(curl:*)` — HTTP 요청 테스트 (모든 스캐너 동적 분석 필수)
     - `Bash(node:*)` — Playwright/Node.js 테스트 (XSS, ReDoS 등 클라이언트 측 테스트 필요 시)
     - `Bash(npx:*)` — npx playwright 실행 (Playwright 필요 시, `Bash(node:*)`로 대체 가능)
     - `Bash(python3:*)` — 검증 스크립트 실행 (보고서 생성·검증 시)
   - **동적 테스트 거부 경로**: **`Bash(python3:*)`만 확인**한다(보고서 생성에 필요). `curl`/`node`/`npx` 확인은 생략한다.
3. 해당 경로에서 필요한 권한이 누락되어 있으면 사용자에게 추가 여부를 묻고, 동의하면 직접 `settings.json`에 추가한다.

#### Step 3-5: 동적 분석 (개별 스캐너의 Phase 2 실행)

사용자가 필요한 정보를 제공하면, 후보가 발견된 모든 스캐너에 대해 동적 분석을 수행한다. **[필수] 스캐너당 1 에이전트 원칙을 따른다.** **[필수] 메인 에이전트는 Phase 2 에이전트 프롬프트 본문을 인라인으로 복사하지 않는다.** 대신 아래 형식의 짧은 프롬프트를 사용하되, 변수를 resolve된 실제 경로 문자열로 치환한다.

```
<NOAH_SAST_DIR>/prompts/phase2-agent.md를 Read 도구로 읽고 그 안의 절차를 정확히 따르세요.
변수: NOAH_SAST_DIR=<NOAH_SAST_DIR>, PHASE1_RESULTS_DIR=<PHASE1_RESULTS_DIR>

스캐너: <scanner-name>
  - phase2.md: <NOAH_SAST_DIR>/scanners/<scanner-name>/phase2.md
  - Phase 1 결과: <PHASE1_RESULTS_DIR>/<scanner-name>.md
세션 정보: <SESSION_INFO>
sandbox 도메인: <SANDBOX_DOMAIN>
```

**AI 자율 탐색 후보(AI-N)의 동적 분석:**
- AI 후보가 기존 스캐너 카테고리(XSS, SQLi 등)에 속하면, 해당 스캐너의 Phase 2 에이전트 프롬프트에 AI 후보 정보를 함께 전달한다.
- 기존 카테고리에 속하지 않는 AI 후보(예: Race Condition, Mass Assignment 등)는 `phase2-agent.md`의 "비카테고리 AI 후보 처리" 절차에 따라 별도 Phase 2 에이전트로 실행한다.

**동적 분석 실행 순서 — Tier 기반 병렬화:**

후보가 발견된 스캐너를 인증 컨텍스트에 따라 Tier로 분류하고, Tier 간에는 병렬 실행한다.

| Tier | 특성 | 해당 스캐너 | 실행 방식 |
|------|------|------------|----------|
| **A** | 인증 불요 (헤더/설정 검사) | security-headers, http-smuggling, host-header, http-method-tampering, crlf-injection, sourcemap, subdomain-takeover, tls | Tier 내 **순차**, 다른 Tier와 **병렬** |
| **B** | 공유 세션 사용 (주요 테스트) | xss, dom-xss, sqli, nosqli, ssrf, ssti, command-injection, path-traversal, file-upload, xxe, xslt-injection, deserialization, open-redirect, csrf, idor, redos, css-injection, prototype-pollution, pdf-generation, zipslip, graphql, websocket, csv-injection, xpath-injection, ldap-injection, soapaction-spoofing, business-logic, cookie-security, springboot-hardening, validation-logic | Tier 내 **순차** |
| **C** | 독립 인증 컨텍스트 | oauth, saml, jwt | Tier 내 **순차**, Tier B와 **병렬** |

**실행 규칙:**
1. Step 3-3에서 사용자가 제공한 세션 정보를 바탕으로 Tier를 확정한다.
2. Tier A, Tier B, Tier C를 **동시에** 시작한다. 각 Tier 내부의 스캐너는 순차 실행을 유지한다.
3. **모든 Tier가 완료된 후** Step 3-6(연계 분석)으로 진행한다.

**Tier 병렬화 조건**: Tier A와 Tier C에 후보가 있는 스캐너가 각각 1개 이상 존재할 때에만 병렬화한다. Tier B만 존재하면 기존과 동일하게 순차 실행한다.

> **주의**: Tier 병렬화는 서로 다른 인증 컨텍스트 간의 병렬이다. 동일 세션을 사용하는 스캐너끼리의 병렬 실행은 여전히 금지된다.

사용자가 동적 테스트를 명시적으로 거부한 경우("동적 테스트 안 해도 돼", "소스코드 분석만 해줘" 등)에만 동적 분석을 건너뛰고 Step 3-6(연계 분석)으로 진행한다.

**Phase 2 결과 수집 및 마스터 목록 갱신:**

모든 동적 분석 에이전트가 완료되면, `update-phase2-status.py`를 실행하여 Phase 2 결과 파일의 manifest를 파싱하고 master-list.json의 status를 갱신한다:

```bash
python3 <NOAH_SAST_DIR>/tools/update-phase2-status.py <PHASE1_RESULTS_DIR> <PHASE1_RESULTS_DIR>/master-list.json
```

이 스크립트가 `*-phase2.md` 파일의 `PHASE2 MANIFEST` 블록에서 각 후보의 상태(confirmed/safe/candidate)를 추출하여 master-list.json의 `"status"` 필드를 갱신한다. 에이전트 반환 텍스트의 테이블은 체크리스트 출력용으로만 사용하고, **상태 갱신의 진실 원천은 결과 파일의 manifest**이다. 연계 분석 에이전트가 master-list.json에서 최종 상태를 직접 읽으므로, 이 갱신이 Step 3-6 진입 전에 완료되어야 한다.

**[필수] assert_status_complete.py로 Step 3-6 진입 가드 실행**:

```bash
python3 <NOAH_SAST_DIR>/tools/assert_status_complete.py \
  <PHASE1_RESULTS_DIR>/master-list.json <PHASE1_RESULTS_DIR>
```

Exit code별 조치 (checklist.md §13 통일 테이블):
- `0`: Step 3-6 진행
- `1`: status 미완결. evaluate 재호출
- `2`: `requires_human_review` 후보 존재. `--accept-human-review=ID1,ID2` 명시 승인 필요. 사용자에게 승인 요청 후 재실행
- `3`: rederivation 비율 경고. 로그만 남기고 진행
- `4`: `phase1_eval_state.reopen=true` 후보 존재. **evaluate_phase1 재호출 필요** (아래 "reopen 재호출 원자성" 참조)

**reopen 재호출 원자성**:

assert가 exit 4를 반환하면 메인 에이전트는 다음 3단계를 **원자적으로** 수행한다:

1. master-list.json Read → `phase1_eval_state.reopen == true` 후보 목록 수집
2. 각 후보의 `phase1_eval_state.retries`가 2 미만인지 확인. 2 도달 시 재호출 중단하고 `requires_human_review=true`로 전환 (exit 2로 재할당).
3. `scan-report-review mode=evaluate_phase1`을 해당 후보 목록에 한정하여 재호출. 완료 후:
   - `phase1_eval_state.reopen = false` 리셋
   - `phase1_eval_state.retries += 1` 증분
   - `phase1_validated = true` 재기록 (§12-C §9 폐기가 아닌 경우)
4. assert_status_complete.py 재실행. 여전히 exit 4면 로그 기록 후 `requires_human_review=true`로 전환.

**[필수] 재호출 중 master-list.json의 status 필드는 건드리지 않는다.** evaluate만 status writer이며, 재호출된 evaluate_phase1은 phase1_* 필드만 갱신한다.

**동적 테스트로 확인됨 증거가 새로 확보된 경우 섹션 갱신 절차**:

메인 에이전트는 **기존 sr_*.md 파일을 수동 sed/편집으로 고치지 않는다**. 대신:

1. `SANDBOX_DOMAINS` 확정(필요 시 사용자 확인)
2. 해당 후보가 속한 스캐너의 **scan-report Step 2 서브에이전트를 재호출**. 프롬프트에 `SANDBOX_DOMAINS`와 확인됨 증거(HTTP 응답, 관찰된 페이로드 등)를 전달
3. 서브에이전트가 확인됨 상태 + 실제 관찰 결과 + sandbox 도메인을 포함한 섹션을 새로 작성하여 반환
4. `assemble_report.py`로 보고서 재조립

#### Step 3-6: 연계 분석

동적 분석 완료 후, "안전" 판정을 제외하고 후보가 2건 이상 남아 있는 경우 `<NOAH_SAST_DIR>/sub-skills/chain-analysis/SKILL.md`에 정의된 프로세스에 따라 **연계 분석 에이전트**를 실행한다. 2건 미만이면 이 단계를 건너뛴다.

에이전트 프롬프트에는 chain-analysis SKILL.md 경로, 후보 마스터 목록(`<PHASE1_RESULTS_DIR>/master-list.json` — 각 후보의 동적 분석 최종 상태 포함), Phase 1 결과 디렉토리(`<PHASE1_RESULTS_DIR>`), 프로젝트 컨텍스트, 이상 없음 요약을 포함한다.

**연계 분석 결과 활용:**
- 에이전트가 `<PHASE1_RESULTS_DIR>/chain-analysis.md` 파일에 결과를 저장하고, 반환 메시지에는 저장 완료 요약 + 체인/독립 후보 건수만 포함한다.
- **Step 4 (보고서)**: 메인 에이전트가 `<PHASE1_RESULTS_DIR>/chain-analysis.md`를 Read하여 파일 끝의 `<!-- NOAH-SAST CHAIN MANIFEST v1 -->` JSON 블록을 파싱한다. 파싱한 JSON 객체를 별도 파일(예: `/tmp/chain.json`)로 저장하고, `assemble_report.py`의 `--chain` 인자로 전달한다.

#### Step 3-7: 결과 검증 (보고서 작성 전 필수)

동적 분석 및 연계 분석 완료 후, Step 4(보고서 작성)로 넘어가기 **전에** 다음을 검증한다.

**"후보" 상태는 소극적 선택지가 아니다.** 동적 테스트를 시도했으나 기술적으로 확인이 불가능한 경우에만 부여한다. 테스트를 시도하지 않은 채 "추가 검증 필요"로 남기는 것은 허용하지 않는다. 후보로 분류하려면 왜 동적 테스트가 불가능했는지 구체적인 사유(`[도구 한계]`/`[정보 부족]`/`[환경 제한]`)가 있어야 한다.

**[필수] 아래 형식의 체크리스트를 반드시 출력한다.** 자율적 판단으로 대체하지 않는다.

**체크리스트는 후보 마스터 목록의 모든 항목을 포함해야 한다.** 테이블에서 항목을 생략하는 것은 허용하지 않는다. 테이블 행 수 = 후보 마스터 목록 항목 수여야 한다.

테이블 형식 (모든 후보 마스터 목록 항목 포함):
```
## 동적 분석 결과 체크리스트

| ID | 후보 제목 | 테스트 수행 | 결과 | 미수행 사유 |
|----|----------|------------|------|------------|
| [스캐너ID] | [후보 제목] | ✓ 또는 ✗ | [결과 또는 —] | [사유 또는 —] |
...
```

- 테스트 수행 ✓: 동적 테스트를 실제 실행한 경우. 미수행 사유 칸은 `—`.
- 테스트 수행 ✗: 테스트를 실행하지 못한 경우. 반드시 `[도구 한계]`/`[정보 부족]`/`[환경 제한]` 중 하나를 사유로 명시. Playwright 등 필요한 도구는 실행을 시도하지 않고 미설치로 추정하여 `[도구 한계]`로 표시하는 것은 허용하지 않는다. 실행을 시도했으나 실제로 실패(command not found 등)한 경우에만 허용한다.

**결과 컬럼 작성 기준:**
- **확인됨**: `확인됨 — [트리거 증거]` (예: `확인됨 — XSS alert 발화 확인`)
- **안전**: `안전 — [방어 계층 + 확인 방법]` (예: `안전 — 게이트웨이 라우팅 차단 확인 (nginx.conf:42)`) — `guidelines-phase2.md` 지침 7 "차단 응답 처리" 절차에 따라 의도적 방어가 입증된 경우에만 부여
- **후보 (차단)**: `후보 — [차단 계층]이 [응답] 반환, 방어 입증 불가` (예: `후보 — 백엔드 400 반환, 의도적 depth 제한 로직 확인 불가`)
- **후보 (환경)**: `후보 — [환경 한계 사유]` (예: `후보 — 내부 서비스 정상 운영으로 에러 조건 미충족`)

**[필수] 체크리스트의 미수행(✗) 항목은 사유 태그에 따라 아래 조치를 즉시 수행한다. "인지했다"에서 멈추지 않는다.**

| 사유 태그 | 메인 에이전트 조치 |
|-----------|-----------------|
| `[도구 한계]` | 메인 에이전트가 직접 해당 테스트를 실행한다. 도구 설치 여부 확인 없이 바로 실행하며, 실행이 실패하면 그때 `[환경 제한]`으로 재분류한다. |
| `[정보 부족]` | 사용자에게 추가 정보 요청. 획득 불가 시 "후보"로 보고서에 포함. |
| `[환경 제한]` | "후보"로 보고서에 포함 (제한 사유 명시). |

> **`[환경 제한]` 유효 범위**: 테스터가 직접 해결할 수 없는 외부 제약에만 사용한다 (예: 관리자 권한 없음, OTP 필요, 프로덕션 전용 인프라). 테스트 데이터(댓글, 게시글, 파일 등)가 없어서 테스트가 불가능한 경우는 해당하지 않는다 — 데이터를 직접 생성한 뒤 테스트를 진행해야 한다.

체크리스트에 ✗ 항목이 없을 때(모두 ✓)에 한해 아래 최종 점검 후 Step 4로 진행한다:

0. **[필수] ✓ 항목의 실행 여부를 검증한다.** 동적 테스트 수행 주체(개별 취약점 스캐너 에이전트 또는 메인 에이전트)의 반환/실행 결과에 각 항목의 **동적 테스트 실행 결과** 파트가 존재하는지 확인한다. 해당 파트가 없거나 비어 있으면 ✓가 아니라 ✗(`[도구 한계]`)로 재분류하고 메인 에이전트가 직접 재테스트한다.

1. **후보 마스터 목록의 모든 항목에 최종 상태가 부여되었는가?** Phase 2 에이전트 반환 테이블의 "결과" 열에서 상태를 판정한다: "확인됨"이 명시되면 confirmed, "안전"/"방어 확인"이면 safe, 그 외(테스트 미수행, 불확실)는 candidate.
   - "확인됨": 동적 테스트에서 실제 트리거 확인. **[필수] 동적 테스트 수행 주체의 결과에 해당 항목의 "동적 테스트 실행 결과" 파트(실제 실행한 명령 + 응답/출력)가 존재하는 경우에만 "확인됨"으로 인정한다. "확인됨"이라고 기술했더라도 실행 결과 파트가 없으면 메인 에이전트가 직접 동적 테스트를 수행한다. 직접 테스트 후에도 트리거를 확인할 수 없으면 "후보"로 재분류한다.** 또한, 확인됨 판정은 취약점 단위로 개별 적용한다. 동일 취약점 클래스라도 코드 경로가 다른 항목은 별도의 동적 테스트 증거가 있어야 한다. 한 경로의 확인 결과를 다른 경로에 전파하지 않는다.
   - "후보": 동적 테스트 미수행, 결과 불확실, 또는 차단되었으나 방어 의도 입증 불가
   - "안전": 동적 테스트에서 의도적 방어가 입증됨 (`guidelines-phase2.md` 지침 7 "차단 응답 처리" 절차 준수)
2. **"안전"으로 판정되지 않은 모든 항목이 보고서에 포함될 준비가 되었는가?**
3. **Phase 1 및 AI 자율 탐색에서 발견된 후보 중 누락된 것이 없는가?** — Phase 1 결과와 AI 자율 탐색 결과를 다시 대조한다.
4. **모든 후보에 실제 URL 경로가 확정되어 있는가?** — 경로가 누락된 항목이 있으면 메인 에이전트가 직접 호출부를 추적한다(Sink 함수명으로 Grep → import하는 컴포넌트 식별 → 라우트 정의를 Read로 읽어 경로 확정). 모든 후보의 경로가 확정된 후에만 Step 4로 진행한다.

### Step 4: scan-report 스킬에 결과 전달 및 보고서 생성

> **전제 조건**: Step 3-7(결과 검증)이 완료되었거나, 사용자가 동적 테스트를 명시적으로 거부한 경우에만 이 단계를 수행한다. 정적 분석만 완료된 상태에서 이 단계로 넘어가지 않는다.

Step 3에서 수집한 모든 개별 스캐너의 결과를 **`scan-report` 스킬(`<NOAH_SAST_DIR>/sub-skills/scan-report/SKILL.md`)에 전달**하여 통합 보고서를 생성한다. **작업 디렉토리에 여러 프로젝트가 존재하더라도 보고서는 반드시 1개(`noah-sast-report.md` + `.html`)만 생성한다. 프로젝트별로 보고서를 분리하지 않는다.**

**sandbox 도메인 자동 적용 (보고서 POC URL용):**

Step 1에서 추출한 `SANDBOX_DOMAINS`가 있으면, 보고서 서브에이전트에 도메인 매핑을 전달하여 POC curl 명령어에 실제 sandbox 도메인을 사용한다. `SANDBOX_DOMAINS`가 비어 있거나 추출 불가한 서비스는 `<TARGET_HOST>` 등 플레이스홀더를 유지한다.

**전달하는 데이터:**
- 후보 마스터 목록: `<PHASE1_RESULTS_DIR>/master-list.json` (각 후보의 최종 상태: 확인됨/후보/안전)
- 스캐너별 Phase 1 소스코드 분석 결과: `<PHASE1_RESULTS_DIR>/<scanner-name>.md` 파일들
- AI 자율 탐색 결과: `<PHASE1_RESULTS_DIR>/ai-discovery.md` (후보 0건이면 생략 가능)
- 스캐너별 동적 분석 결과: 각 Phase 2 에이전트의 반환 텍스트(재현 방법 및 POC + 동적 테스트 실행 결과 파트)를 scan-report Step 2 서브에이전트 프롬프트에 해당 스캐너 데이터로 포함한다
- 연계 분석 결과 (전제조건 매트릭스, 연계 매트릭스, 공격 체인 또는 "체인 없음" 판정 사유, 독립 후보 정리, 위험도 재평가)
- **SANDBOX_DOMAINS**: 확인된 sandbox 도메인 매핑 (확인받은 경우)
- 이상 없음 스캐너의 점검 항목 요약
- 미적용 스캐너 목록 및 제외 사유

scan-report SKILL.md를 읽고, 그 스킬이 정의하는 보고서 작성 프로세스를 수행한다. **noah-sast는 보고서를 직접 작성하지 않는다.**

**[필수] scan-report의 Step 3(MD 조립) 완료 후, Step 4(HTML 변환) 이전에 `scan-report-review` 스킬을 실행하여 보고서 정확성을 검증한다.** scan-report 에이전트 실패로 메인 에이전트가 직접 보고서를 작성한 fallback 시나리오에서도 이 단계를 건너뛰지 않는다. `<NOAH_SAST_DIR>/sub-skills/scan-report-review/SKILL.md`를 읽고, 보고서 MD 파일 경로와 프로젝트 루트 경로를 전달한다. 리뷰에서 부정확한 내용이 발견되면 MD 파일이 수정된 후 HTML 변환으로 진행한다.

**[필수] scan-report-review 완료 후, HTML 변환 직전에 MD 파일에 리뷰 섹션이 잔류하지 않았는지 확인한다.** `grep "^## .*리뷰\|^## .*검증 결과" noah-sast-report.md`를 실행하여 매칭이 있으면 Edit 도구로 해당 섹션을 제거한다. (`md_to_html.py`가 방어적 제거를 수행하지만, MD 원본도 깨끗하게 유지해야 한다.)

**Step 4 후처리 (메인 에이전트 수행):**

1. **HTML 변환**: `python3 <NOAH_SAST_DIR>/sub-skills/scan-report/md_to_html.py` — 실패 시 `vuln-format.md`의 "공통 HTML 보고서 사양"을 참조하여 직접 변환 코드 작성
2. **링크 검증**: `python3 <NOAH_SAST_DIR>/sub-skills/scan-report/validate_links.py noah-sast-report.html` — LINK FAIL 시 `missing_ids`에 해당하는 MD 섹션을 찾아 `**N번 - ID**: 제목` 형식이면 `#### N. 제목`으로 변환, HTML 재생성 후 재검증
3. **정량 검증**: `python3 <NOAH_SAST_DIR>/sub-skills/scan-report/validate_report.py [확인됨+후보 건수] --master-list <PHASE1_RESULTS_DIR>/master-list.json` — FAIL 시 누락 보충 후 재검증. `--master-list` 인자를 반드시 전달해야 `## 안전 판정 항목` 섹션 존재성이 정확히 검증된다. 추가 체크: 확인됨 항목에 실제 값 사용, 후보 항목에 curl 명령어 포함, 테스트 환경 명시
3-B. **독자 레이어 용어 lint**: `python3 <NOAH_SAST_DIR>/tools/lint_reader_layer.py noah-sast-report.md noah-sast-report.html` — exit 5 (lint 위반) 시 헤딩에 노출된 내부 규약 용어를 풀이 형태로 수정하거나 본문 근거 테이블로 이관
4. **브라우저 열기**: `open noah-sast-report.html`

## 유의사항 (메인 에이전트 — 일반)

- **[필수] 모든 동적 테스트는 `prompts/guidelines-phase2.md` 지침 11(도메인 분류)을 통과한 sandbox 도메인에서만 수행한다.** 사용자가 제공한 도메인이 prod/cbt로 분류되면 동적 테스트를 절대 수행하지 않고 sandbox URL을 요청한다. 분류 불명/staging이면 명시적 확인 후에만 진행.
- Phase 1에서 후보가 발견되면 반드시 사용자에게 동적 테스트 진행 여부를 물어본다. 사용자가 명시적으로 거부한 경우에만 건너뛴다.
- 사용자에게 진행 상황을 주기적으로 알린다.
- 각 스캐너의 분석 방법론(판정 기준, 테스트 도구 선택, 세션 관리 등)은 해당 스캐너의 phase1.md/phase2.md 규칙을 따른다. noah-sast는 이를 중복 정의하지 않는다.
- 미적용 스캐너는 "해당 없음" 사유와 함께 미적용 목록에 기재한다.
- 테스트 대상 도메인(Host)은 사용자에게 확인받는다. 그 외 동적 정보는 소스코드 분석 또는 HTTP 요청으로 획득하고, 직접 획득이 불가능한 정보만 사용자에게 한번에 요청한다.

## 유의사항 (메인 에이전트 — 개별 취약점 스캐너 에이전트 관리)

정적 분석/동적 분석의 개별 취약점 스캐너 에이전트를 실행·관리하는 메인 에이전트가 따르는 지침.

### 지침 A: 동적 분석 에이전트에 Phase 1 결과 파일 전달

> **동적 분석 에이전트 프롬프트에 Phase 1 결과 파일 경로(`<PHASE1_RESULTS_DIR>/<scanner-name>.md`)를 포함한다.** 에이전트가 파일을 직접 Read하여 모든 후보를 확인한다. 메인 에이전트가 후보를 프롬프트에 재작성하지 않는다.

### 지침 B: 개별 취약점 스캐너 에이전트 반환 후 미수행 항목 보완

> 모든 동적 분석 에이전트가 반환된 후, 메인 에이전트는 **Step 3-7의 체크리스트를 출력하고**, 사유 태그별 조치 테이블에 따라 즉시 후속 처리를 수행한다.
>
> - `[도구 한계]` 항목: 메인 에이전트가 직접 해당 테스트를 실행한다. 도구 설치 여부 확인 없이 바로 실행하며, 실행이 실패하면 그때 `[환경 제한]`으로 재분류한다.
> - `[정보 부족]` 항목: 사용자에게 추가 정보를 요청하거나 "후보"로 포함한다.
> - `[환경 제한]` 항목: "후보"로 보고서에 포함한다.
>
> **"도구 권한 거부"나 사유 없는 미수행이 최종 상태로 남아있으면 안 된다.**

### 지침 C: 심각도 판단 요청 금지

> 개별 취약점 스캐너 에이전트 프롬프트에 "심각도 판단을 포함하라"를 추가하지 않는다.

## 유의사항 (개별 취약점 스캐너 에이전트 프롬프트 포함 필수)

**공통 지침은 Phase별로 분리되어 있다:**
- Phase 1 에이전트: `<NOAH_SAST_DIR>/prompts/guidelines-phase1.md`
- Phase 2 에이전트: `<NOAH_SAST_DIR>/prompts/guidelines-phase2.md`

에이전트 프롬프트에 해당 Phase의 지침 파일 경로를 포함하여, 에이전트가 Read 도구로 읽고 지침을 따르도록 한다. 에이전트 프롬프트에 지침 내용을 인라인으로 복사하지 않는다.