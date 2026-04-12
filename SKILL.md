---
name: noah-sast
description: "41개 취약점 스캐너 스킬을 한번에 실행하고 결과를 통합 보고서로 작성하는 스킬. XSS, SSRF, SQLi, CSRF, TLS, 비즈니스 로직 등 모든 취약점 유형을 소스코드 분석과 동적 테스트로 점검한다. 사용자가 'noah-sast', 'noah sast', 'sast', '소스코드 취약점 스캔' 등을 요청할 때 이 스킬을 사용한다."
---

# Noah SAST — 통합 취약점 스캐너

41개 개별 취약점 스캐너를 순차적으로 실행하고, 모든 결과를 하나의 통합 보고서로 작성하는 스킬이다.

> `[필수]`는 과거 위반 이력이 있어 추가 강조된 항목이다. 태그가 없는 항목도 모두 준수 의무가 있다.

## 실행 프로세스

### Step -1: NOAH_SAST_DIR 경로 결정

**[필수] 모든 Step보다 먼저 실행한다.** 이 스킬의 루트 디렉토리 절대 경로를 결정한다. 모든 스캐너와 유틸리티가 이 디렉토리 하위에 있다.

아래 Bash 명령을 실행하여 `NOAH_SAST_DIR`을 결정한다:

```bash
if [ -d ".claude/skills/noah-sast" ]; then
  echo "$(cd .claude/skills/noah-sast && pwd)"
elif [ -d "$HOME/.claude/skills/noah-sast" ]; then
  echo "$HOME/.claude/skills/noah-sast"
fi
```

이 출력값을 `NOAH_SAST_DIR` 변수로 보관한다. 이후 모든 경로 참조에 사용한다. 서브 에이전트 프롬프트에는 `<NOAH_SAST_DIR>`을 변수명이 아닌 **resolve된 실제 경로 문자열**로 치환하여 삽입한다. 서브 에이전트가 경로를 스스로 결정하거나 해석하도록 맡기지 않는다.

**디렉토리 구조:**
```
<NOAH_SAST_DIR>/
  SKILL.md                          ← 이 파일 (오케스트레이터)
  prompts/                          ← 서브 에이전트 지시 문서
    guidelines-phase1.md            ← Phase 1 공통 지침
    guidelines-phase2.md            ← Phase 2 공통 지침
    grep-agent.md                   ← grep 인덱싱 에이전트 프롬프트
    phase1-group-agent.md           ← Phase 1 그룹 에이전트 프롬프트
  scanners/                         ← 41개 취약점 스캐너
    xss-scanner/
    sqli-scanner/
    ...
  tools/                            ← Python 유틸리티 스크립트
    scanner-selector.py
    build-master-list.py
  sub-skills/                       ← SKILL.md 기반 서브스킬
    scan-report/
    scan-report-review/
    chain-analysis/
    webapp-testing/
  tests/                            ← grep 커버리지 테스트
```

### Step -0.5: 멀티 프로젝트 감지

**작업 디렉토리(`pwd`)에 독립된 프로젝트가 여러 개 존재하는지 확인한다.** 멀티 프로젝트 디렉토리는 루트에 자체 매니페스트(`package.json`, `build.gradle`, `pom.xml` 등)가 없고, 하위 디렉토리 각각이 독립된 매니페스트를 가진 구조이다.

판별 기준:
1. `ls`로 루트 디렉토리의 하위 항목을 확인한다.
2. 루트에 매니페스트 파일이 **없고**, 하위 디렉토리 2개 이상이 각각 매니페스트를 보유 → **멀티 프로젝트**
3. 루트에 매니페스트가 있거나, 하위 디렉토리가 1개만 매니페스트를 보유 → **단일 프로젝트** (기존 흐름)

> **모노레포(monorepo)와 멀티 프로젝트의 구분**: 루트에 `package.json`(workspaces), `settings.gradle`, `pom.xml`(modules) 등 상위 매니페스트가 있으면 모노레포이다. 모노레포는 단일 프로젝트로 취급하여 전체를 한 번에 스캔한다. 상위 매니페스트 없이 하위 디렉토리가 독립적으로 존재하면 멀티 프로젝트이다.

**멀티 프로젝트가 감지된 경우:**

감지된 프로젝트 목록을 `PROJECT_LIST` 변수에 보관한다 (예: `["hubrix-main", "reacto-main", "winery-main"]`). 이후 **Step 0 ~ Step 3-1을 각 프로젝트 단위로 반복 실행**한다.

```
for PROJECT in PROJECT_LIST:
    PROJECT_ROOT = <작업 디렉토리>/<PROJECT>
    Step 0: grep 인덱싱 (PROJECT_ROOT 대상)
    Step 1: 프로젝트 스택 파악
    Step 2: 스캐너 선별
    Step 3-1: Phase 1 정적 분석
```

Phase 1 완료 후, **모든 프로젝트의 후보를 하나의 후보 마스터 목록으로 통합**한다.

**통합 절차:**
1. 각 프로젝트의 Step 3-1에서 이미 생성된 `master-list.json`을 로드한다 (각 프로젝트의 `<PHASE1_RESULTS_DIR>/master-list.json`).
2. 후보 ID에 프로젝트 약칭을 하이픈 접두사로 부여하여 충돌을 방지한다 (예: `SSRF-1` → `hubrix-SSRF-1`, `reacto-JWT-2`). 하이픈 연결이므로 기존 ID regex `[A-Za-z0-9_-]+`와 호환된다.
3. 통합된 `master-list.json`을 작업 디렉토리에 저장한다.

이후 Step 3-2(연계 분석) ~ Step 4(보고서)는 통합된 마스터 목록으로 **한 번만** 실행하여 **단일 보고서**를 생성한다. 보고서의 `**위치**:` 필드에 프로젝트 경로가 포함되어 독자가 어떤 프로젝트의 발견인지 식별할 수 있다.

**단일 프로젝트인 경우:** 기존 흐름과 동일하게 `PROJECT_ROOT = pwd`로 진행한다.

---

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

---

### Step 1: 프로젝트 스택 파악

모든 스캐너에 공통으로 필요한 프로젝트 정보를 먼저 파악한다:
- `package.json`, `requirements.txt`, `pom.xml`, `Gemfile` 등에서 프레임워크/언어/라이브러리 확인
- 프로젝트 구조 파악 (서버, 클라이언트, 설정 파일 위치)
- 인증 방식 확인 (세션, JWT, OAuth, SAML 등)
- DB 종류 확인 (SQL, NoSQL, LDAP 등)
- 프록시/CDN/로드밸런서 구조 확인

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

### Step 3: 정적 분석 → 연계 분석 → 동적 분석

정적 분석(Step 3-1)은 선별된 모든 스캐너 에이전트를 **단일 응답에서 동시에** Agent 도구로 실행한다. 연계 분석(Step 3-2)은 정적 분석 결과를 연계하여 공격 시나리오를 도출한다. 동적 분석(Step 3-5)은 세션 충돌 방지를 위해 순차 실행한다. 각 스캐너는 자신의 phase1.md(소스코드 분석) → phase2.md(동적 테스트) 프로세스를 따른다.

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

**[필수] Phase 1 에이전트는 단일 메시지 안에서 모든 그룹의 Agent 도구를 동시에 호출하여 병렬 실행한다.** 모든 에이전트가 완료된 후에만 Step 3-2로 진행한다. 완료 후 그룹 수와 수신된 결과 수를 대조하여, 누락된 에이전트가 있으면 해당 그룹만 재실행한다.

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

생성된 `<PHASE1_RESULTS_DIR>/master-list.json`은 연계 분석(Step 3-2), 동적 분석(Step 3-5), 리포팅(Step 4) 전체에서 **단일 진실 원천(single source of truth)**으로 사용한다. **마스터 목록에 있는 후보는 동적 분석에서 "안전"으로 판정되지 않는 한, 반드시 최종 보고서에 포함되어야 한다.**

#### Step 3-2: 연계 분석

Phase 1에서 후보가 2건 이상 발견된 경우, `<NOAH_SAST_DIR>/sub-skills/chain-analysis/SKILL.md`에 정의된 프로세스에 따라 **연계 분석 에이전트**를 실행한다. 후보가 1건 이하이면 이 단계를 건너뛴다.

에이전트 프롬프트에는 chain-analysis SKILL.md 경로, 후보 마스터 목록(`<PHASE1_RESULTS_DIR>/master-list.json`), Phase 1 결과 디렉토리(`<PHASE1_RESULTS_DIR>`), 프로젝트 컨텍스트, 이상 없음 요약을 포함한다.

**연계 분석 결과 활용:**
- **Step 4 (보고서)**: 공격 체인을 보고서의 핵심 섹션으로 포함한다.
- **Step 3-3 (동적 테스트 안내)**: 공격 체인의 테스트 순서와 전제조건을 사용자에게 제시하여, 체인 단위 테스트를 대화형으로 진행한다. 개별 스캐너 에이전트로는 체인 테스트를 자동화하지 않는다.

#### Step 3-3: 동적 분석 정보 일괄 요청 → 사용자 응답 대기

`<PHASE1_RESULTS_DIR>/master-list.json`을 읽어 후보 목록을 확인하고, 동적 테스트에 필요한 정보를 한번에 정리하여 사용자에게 요청한다. 연계 분석(Step 3-2)에서 공격 체인이 도출된 경우, 체인별 테스트 시나리오도 함께 제시한다. **이 시점에서 사용자의 응답을 기다린다. 보고서를 작성하지 않는다.**

```
## 동적 테스트 진행을 위해 필요한 정보

소스코드 분석 결과, 다음 취약점에서 후보가 발견되었습니다.
동적 테스트를 진행하려면 아래 정보를 제공해주세요:

1. **테스트 환경 URL**: https://sandbox-...
2. **세션 쿠키/인증 토큰**: (로그인 후 쿠키 값)
3. **[XSS 후보 2건]**: 추가 정보 불필요
4. **[SSRF 후보 1건]**: 외부 콜백 서비스 URL (webhook.site 등)
5. **[OAuth 후보 1건]**: OAuth 인가 코드 (수동 획득 필요)
...

동적 테스트를 진행하시겠습니까? 필요한 정보를 제공해주세요.
```

#### Step 3-4: 동적 테스트 도구 권한 사전 확인

**절차:**

1. `~/.claude/settings.json` 및 프로젝트 `.claude/settings.json`을 **Read 도구로** 읽어 `permissions.allow` 배열을 확인한다.
2. 다음 기본 패턴이 `permissions.allow`에 포함되어 있는지 검사한다:
   - `Bash(curl:*)` — HTTP 요청 테스트 (모든 스캐너 동적 분석 필수)
   - `Bash(node:*)` — Playwright/Node.js 테스트 (XSS, ReDoS 등 클라이언트 측 테스트 필요 시)
   - `Bash(npx:*)` — npx playwright 실행 (Playwright 필요 시, `Bash(node:*)`로 대체 가능)
   - `Bash(python3:*)` — 검증 스크립트 실행 (보고서 검증 시)
3. 누락된 패턴이 있으면 사용자에게 추가 여부를 묻고, 동의하면 직접 `settings.json`에 추가한다.

#### Step 3-5: 동적 분석 (개별 스캐너의 Phase 2 실행)

사용자가 필요한 정보를 제공하면, 후보가 발견된 모든 스캐너에 대해 동적 분석을 수행한다. **[필수] 스캐너당 1 에이전트 원칙을 따른다. 여러 스캐너의 동적 분석을 하나의 에이전트에 묶지 않는다.** 각 에이전트 프롬프트에는 `<NOAH_SAST_DIR>/scanners/<scanner-name>/phase2.md`, `<NOAH_SAST_DIR>/prompts/guidelines-phase2.md` 경로, 그리고 Phase 1 결과 파일 경로 `<PHASE1_RESULTS_DIR>/<scanner-name>.md`를 포함한다. Phase 2 에이전트는 이 파일에서 해당 스캐너의 모든 후보를 직접 읽는다.

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
3. **모든 Tier가 완료된 후** Step 3-6(결과 검증)으로 진행한다.

**Tier 병렬화 조건**: Tier A와 Tier C에 후보가 있는 스캐너가 각각 1개 이상 존재할 때에만 병렬화한다. Tier B만 존재하면 기존과 동일하게 순차 실행한다.

> **주의**: Tier 병렬화는 서로 다른 인증 컨텍스트 간의 병렬이다. 동일 세션을 사용하는 스캐너끼리의 병렬 실행은 여전히 금지된다.

사용자가 동적 테스트를 명시적으로 거부한 경우("동적 테스트 안 해도 돼", "소스코드 분석만 해줘" 등)에만 동적 분석을 건너뛰고 Step 4로 진행한다.

#### Step 3-6: 결과 검증 (보고서 작성 전 필수)

동적 분석 완료 후, Step 4(보고서 작성)로 넘어가기 **전에** 다음을 검증한다.

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

**[필수] 체크리스트의 미수행(✗) 항목은 사유 태그에 따라 아래 조치를 즉시 수행한다. "인지했다"에서 멈추지 않는다.**

| 사유 태그 | 메인 에이전트 조치 |
|-----------|-----------------|
| `[도구 한계]` | 메인 에이전트가 직접 해당 테스트를 실행한다. 도구 설치 여부 확인 없이 바로 실행하며, 실행이 실패하면 그때 `[환경 제한]`으로 재분류한다. |
| `[정보 부족]` | 사용자에게 추가 정보 요청. 획득 불가 시 "후보"로 보고서에 포함. |
| `[환경 제한]` | "후보"로 보고서에 포함 (제한 사유 명시). |

> **`[환경 제한]` 유효 범위**: 테스터가 직접 해결할 수 없는 외부 제약에만 사용한다 (예: 관리자 권한 없음, OTP 필요, 프로덕션 전용 인프라). 테스트 데이터(댓글, 게시글, 파일 등)가 없어서 테스트가 불가능한 경우는 해당하지 않는다 — 데이터를 직접 생성한 뒤 테스트를 진행해야 한다.

체크리스트에 ✗ 항목이 없을 때(모두 ✓)에 한해 아래 최종 점검 후 Step 4로 진행한다:

0. **[필수] ✓ 항목의 실행 여부를 검증한다.** 개별 취약점 스캐너 에이전트 반환 결과에 각 항목의 **동적 테스트 실행 결과** 파트가 존재하는지 확인한다. 해당 파트가 없거나 비어 있으면 ✓가 아니라 ✗(`[도구 한계]`)로 재분류하고 메인 에이전트가 직접 재테스트한다.

1. **후보 마스터 목록의 모든 항목에 최종 상태가 부여되었는가?**
   - "확인됨": 동적 테스트에서 실제 트리거 확인. **[필수] 개별 취약점 스캐너 에이전트 반환 결과에 해당 항목의 "동적 테스트 실행 결과" 파트(실제 실행한 명령 + 응답/출력)가 존재하는 경우에만 "확인됨"으로 인정한다. 개별 취약점 스캐너 에이전트가 "확인됨"이라고 기술했더라도 실행 결과 파트가 없으면 메인 에이전트가 직접 동적 테스트를 수행한다. 직접 테스트 후에도 트리거를 확인할 수 없으면 "후보"로 재분류한다.** 또한, 확인됨 판정은 코드 경로(Source→Sink) 단위로 개별 적용한다. 동일 취약점 클래스(예: html_safe 미살균, dangerouslySetInnerHTML)라도 코드 경로가 다른 항목은 별도의 동적 테스트 증거가 있어야 한다. 한 경로의 확인 결과를 다른 경로에 전파하지 않는다.
   - "후보": 동적 테스트 미수행 또는 결과 불확실
   - "안전": 동적 테스트에서 방어 확인
2. **"안전"으로 판정되지 않은 모든 항목이 보고서에 포함될 준비가 되었는가?**
3. **Phase 1에서 발견된 후보 중 누락된 것이 없는가?** — Phase 1 결과를 다시 대조한다.
4. **모든 후보에 실제 URL 경로가 확정되어 있는가?** — 경로가 누락된 항목이 있으면 메인 에이전트가 직접 호출부를 추적한다(Sink 함수명으로 Grep → import하는 컴포넌트 식별 → 라우트 정의를 Read로 읽어 경로 확정). 모든 후보의 경로가 확정된 후에만 Step 4로 진행한다.

### Step 4: scan-report 스킬에 결과 전달 및 보고서 생성

> **전제 조건**: Step 3-5(동적 분석)이 완료되었거나, 사용자가 동적 테스트를 명시적으로 거부한 경우에만 이 단계를 수행한다. 정적 분석만 완료된 상태에서 이 단계로 넘어가지 않는다.

Step 3에서 수집한 모든 개별 스캐너의 결과를 **`scan-report` 스킬(`<NOAH_SAST_DIR>/sub-skills/scan-report/SKILL.md`)에 전달**하여 통합 보고서를 생성한다.

**전달하는 데이터:**
- 후보 마스터 목록: `<PHASE1_RESULTS_DIR>/master-list.json` (각 후보의 최종 상태: 확인됨/후보/안전)
- 스캐너별 Phase 1 소스코드 분석 결과: `<PHASE1_RESULTS_DIR>/<scanner-name>.md` 파일들
- 스캐너별 동적 분석 결과 (curl 요청/응답 또는 Playwright 실행 결과 증거)
- 연계 분석 결과 (전제조건 매트릭스, 연계 매트릭스, 공격 체인 또는 "체인 없음" 판정 사유, 독립 후보 정리, 위험도 재평가)
- 이상 없음 스캐너의 점검 항목 요약
- 미적용 스캐너 목록 및 제외 사유

scan-report SKILL.md를 읽고, 그 스킬이 정의하는 보고서 작성 프로세스를 수행한다. **noah-sast는 보고서를 직접 작성하지 않는다.**

**[필수] scan-report의 Step 3(MD 조립) 완료 후, Step 4(HTML 변환) 이전에 `scan-report-review` 스킬을 실행하여 보고서 정확성을 검증한다.** `<NOAH_SAST_DIR>/sub-skills/scan-report-review/SKILL.md`를 읽고, 보고서 MD 파일 경로와 프로젝트 루트 경로를 전달한다. 리뷰에서 부정확한 내용이 발견되면 MD 파일이 수정된 후 HTML 변환으로 진행한다.

**[필수] scan-report-review 완료 후, HTML 변환 직전에 MD 파일에 리뷰 섹션이 잔류하지 않았는지 확인한다.** `grep "^## .*리뷰\|^## .*검증 결과" noah-sast-report.md`를 실행하여 매칭이 있으면 Edit 도구로 해당 섹션을 제거한다. (`md_to_html.py`가 방어적 제거를 수행하지만, MD 원본도 깨끗하게 유지해야 한다.)

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

> 모든 동적 분석 에이전트가 반환된 후, 메인 에이전트는 **Step 3-6의 체크리스트를 출력하고**, 사유 태그별 조치 테이블에 따라 즉시 후속 처리를 수행한다.
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