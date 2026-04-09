# Noah SAST

> Claude Code 스킬 기반의 자동화된 소스코드 취약점 분석 시스템.
> 37개 개별 스캐너를 오케스트레이션하여 정적 분석 → 연계 분석 → 동적 테스트 → 보고서 생성까지 수행합니다.

---

## 목차

- [개요](#개요)
- [아키텍처](#아키텍처)
- [실행 프로세스](#실행-프로세스)
- [스캐너 목록](#스캐너-목록)
- [개별 스캐너 구조](#개별-스캐너-구조)
- [분석 방법론](#분석-방법론)
- [보고서 파이프라인](#보고서-파이프라인)
- [사용법](#사용법)
- [디렉토리 구조](#디렉토리-구조)

---

## 개요

Noah SAST는 Claude Code의 **스킬(Skill)** 시스템 위에 구축된 통합 취약점 분석 프레임워크입니다.

| 설계 원칙 | 설명 |
|-----------|------|
| **중복 탐색 방지** | Step 0에서 모든 grep 패턴을 사전 인덱싱하여 개별 스캐너가 코드베이스를 중복 탐색하지 않음 |
| **병렬 실행** | 스캐너 그룹을 Agent 도구로 동시 실행 (grep 히트 수 기반 동적 리밸런싱) |
| **단일 진실 원천** | 후보 마스터 목록이 전체 프로세스의 유일한 상태 저장소 |
| **오탐 방지** | Sink-first + Source-first 병행 분석, 보고서 작성 후 소스코드 대조 검증 |
| **증분 분석** | `.noah-sast-cache/`에 grep 인덱스를 캐싱하여 변경된 파일만 재스캔 |
| **다국어 지원** | Node.js, Python, Ruby, Java 매니페스트에서 의존성을 파싱하여 정확한 스캐너 선별 |

**지원 범위:** Kotlin, Java, TypeScript, JavaScript, Python, Go, Ruby, PHP, C# 등 80+ 확장자. Spring Boot, React, Vue, Django, Express 등 주요 프레임워크의 보안 패턴 인식.

---

## 아키텍처

### 전체 흐름

```mermaid
flowchart TB
    subgraph Orchestrator["메인 에이전트 (Orchestrator)"]
        S0["Step 0\n패턴 인덱싱"]
        S1["Step 1\n스택 파악"]
        S2["Step 2\n스캐너 선별"]
        S3["Step 3\n분석 실행"]
        S4["Step 4\n보고서 생성"]
        S0 --> S1 --> S2 --> S3 --> S4
    end

    S0 -->|위임| GrepAgent["grep 인덱싱\n에이전트"]
    GrepAgent -->|저장| IndexDir[("패턴 인덱스\n(스캐너별 JSON)")]

    S2 -->|실행| Selector["tools/scanner-selector.py\n(다국어 의존성 파싱 + 그룹 리밸런싱)"]

    S3 -->|병렬 실행| P1["Phase 1 정적 분석\n(12개 그룹 에이전트)"]
    P1 -->|후보 2건+| Chain["연계 분석\n에이전트"]
    Chain --> P2["Phase 2 동적 분석\n(순차 실행)"]

    S4 -->|위임| Report["scan-report\n스킬"]
    Report --> Review["scan-report-review\n정확성 검증"]
    Review --> HTML["HTML 변환\n+ 검증"]

    style Orchestrator fill:#1a1a2e,stroke:#e94560,color:#eee
    style GrepAgent fill:#16213e,stroke:#0f3460,color:#eee
    style IndexDir fill:#0f3460,stroke:#533483,color:#eee
    style P1 fill:#16213e,stroke:#0f3460,color:#eee
    style Chain fill:#16213e,stroke:#0f3460,color:#eee
    style P2 fill:#16213e,stroke:#0f3460,color:#eee
    style Report fill:#1a1a2e,stroke:#533483,color:#eee
    style Review fill:#1a1a2e,stroke:#533483,color:#eee
    style HTML fill:#1a1a2e,stroke:#533483,color:#eee
    style Selector fill:#0f3460,stroke:#533483,color:#eee
```

---

## 실행 프로세스

### Step 0: 패턴 사전 인덱싱

개별 스캐너가 코드베이스를 중복 탐색하는 것을 방지하기 위해, 37개 스캐너의 grep 패턴을 일괄 실행하여 인덱스를 생성합니다.

```mermaid
flowchart LR
    Cache{"캐시 확인\ncache_manager.py status"}
    Cache -->|CACHE_HIT| Skip["grep 스킵\n기존 인덱스 재사용"]
    Cache -->|CACHE_STALE| Inc["변경 파일만\n증분 grep"]
    Cache -->|CACHE_MISS| Full["전체 grep 실행"]

    Full --> Agent["grep 인덱싱 에이전트\n(prompts/grep-agent.md)"]
    Inc --> Agent
    Agent -->|"37개 phase1.md\nfrontmatter 파싱"| Grep["grep -rn 일괄 실행\n80+ 확장자 화이트리스트"]
    Grep -->|스캐너별 JSON 저장| Dir[("패턴 인덱스\nxss-scanner.json\nssrf-scanner.json\n...")]
    Dir --> Save["캐시 저장\ncache_manager.py save"]

    style Cache fill:#533483,stroke:#533483,color:#fff
    style Agent fill:#16213e,stroke:#0f3460,color:#eee
    style Grep fill:#0f3460,stroke:#533483,color:#eee
    style Dir fill:#1a1a2e,stroke:#e94560,color:#eee
    style Skip fill:#0f3460,stroke:#0f3460,color:#eee
    style Inc fill:#0f3460,stroke:#0f3460,color:#eee
    style Full fill:#0f3460,stroke:#0f3460,color:#eee
    style Save fill:#16213e,stroke:#0f3460,color:#eee
```

#### Step 0-0: 캐시 확인

이전 실행의 grep 인덱스가 `.noah-sast-cache/`에 캐싱되어 있으면 재사용합니다.

```bash
python3 tools/cache_manager.py status <PROJECT_ROOT>
```

| 출력 | 의미 | 조치 |
|------|------|------|
| `CACHE_HIT` | 코드 변경 없음 | 기존 인덱스 재사용, Step 0-1 스킵 |
| `CACHE_STALE` | 일부 파일 변경 | 변경 파일만 증분 grep |
| `CACHE_MISS` | 캐시 없음 | 전체 grep 실행 |

#### Step 0-1: grep 인덱싱 에이전트 실행

메인 에이전트가 `PATTERN_INDEX_DIR` 경로를 생성하고, `prompts/grep-agent.md`의 지시를 따르는 서브 에이전트를 생성합니다. 이 에이전트가 수행하는 작업:

1. 37개 스캐너의 `phase1.md` frontmatter에서 `grep_patterns:` 추출
2. 80+ 확장자 화이트리스트로 프로젝트 전체 grep 실행
3. 스캐너별 JSON 파일로 결과 저장

**패턴 인덱스 파일 형식:**

```json
{
  "innerHTML": ["src/components/Comment.tsx:18", "src/components/Post.tsx:55"],
  "dangerouslySetInnerHTML": ["src/components/Comment.tsx:42"],
  "html_safe": []
}
```

- `파일경로:라인번호` 형식 (코드 내용 미포함)
- 히트 없는 패턴도 빈 배열로 포함
- 개별 스캐너 에이전트는 자신의 JSON 파일만 읽어 분석 시작

#### Step 0-2: 카운트 요약 수신 및 캐시 저장

grep 에이전트가 반환한 스캐너별 히트 건수를 보관합니다. 풀 스캔 또는 증분 완료 후 `cache_manager.py save/merge`로 캐시를 저장하여 다음 실행에서 재사용할 수 있도록 합니다.

---

### Step 1: 프로젝트 스택 파악

모든 스캐너에 공통으로 필요한 프로젝트 정보를 파악합니다:

| 파악 항목 | 확인 대상 |
|-----------|----------|
| 프레임워크/언어 | `package.json`, `build.gradle.kts`, `requirements.txt`, `Gemfile`, `pom.xml` 등 |
| DB 종류 | MySQL, PostgreSQL, MongoDB, Redis, LDAP 등 |
| 인증 방식 | 세션 기반, JWT, OAuth, SAML 등 |
| 인프라 구조 | 프록시, CDN, 로드밸런서, 마이크로서비스 여부 |

이 정보는 모든 그룹 에이전트 프롬프트에 공통 컨텍스트로 전달됩니다.

---

### Step 2: 스캐너 선별

#### Step 2-1: 자동 선별 (scanner-selector.py)

`tools/scanner-selector.py`가 grep 인덱스 + 프로젝트 의존성을 기반으로 자동 선별합니다.

```bash
python3 tools/scanner-selector.py <PATTERN_INDEX_DIR> <PROJECT_ROOT>
```

| 조건 | 판정 |
|------|------|
| grep 히트 1건 이상 | **반드시 포함** |
| grep 히트 0건 + 관련 라이브러리 존재 | 포함 |
| grep 히트 0건 + 관련 라이브러리 없음 | 제외 (사유 명시) |

**다국어 의존성 파싱:** `package.json`(Node.js)뿐 아니라 `requirements.txt`/`Pipfile`/`pyproject.toml`(Python), `Gemfile`(Ruby), `pom.xml`/`build.gradle`(Java)에서도 실제 패키지명을 파싱합니다.

스크립트 출력:
- 적용/제외 판정 테이블 (grep 히트 건수 + 사유)
- 적용 스캐너 목록
- **그룹 편성** (grep 히트 수 기반 동적 리밸런싱)

#### Step 2-2: AI 검토

스크립트는 라이브러리 의존성 + grep 히트 수만으로 판단하므로, 메인 에이전트가 제외된 스캐너를 추가 검토합니다:

- 표준 라이브러리로 직접 구현한 경우 (예: `fetch()`로 SSRF, `xml.etree`로 XXE)
- 프레임워크 내장 기능 (예: Spring `RestTemplate`, Django ORM `raw()`)
- 멀티 언어 프로젝트에서 다른 서브프로젝트의 의존성

> **기본 원칙: 포함이 기본이고, 제외에는 근거가 필요합니다.**

---

### Step 3: 분석 실행

#### Step 3-1: Phase 1 정적 분석 (병렬)

선별된 스캐너를 의미적 연관성 기반 그룹으로 묶어 **단일 응답에서 모든 그룹의 Agent를 동시 호출**합니다. 과부하 그룹(grep 히트 합계 150건 초과 또는 5개 이상)은 자동 분할됩니다.

**기본 그룹 (과부하 시 자동 분할):**

| 그룹 | 스캐너 |
|------|--------|
| url-navigation | xss, dom-xss, open-redirect |
| response-header | crlf-injection, host-header, http-method-tampering |
| db-query | sqli, nosqli |
| process-execution | command-injection, ssti |
| server-request | ssrf, pdf-generation |
| file-system | path-traversal, file-upload, zipslip |
| xml-serialization | xxe, xslt-injection, deserialization |
| auth-protocol | jwt, oauth, saml, csrf, idor |
| client-rendering | redos, css-injection, prototype-pollution |
| infra-config | http-smuggling, sourcemap, subdomain-takeover, security-headers |
| data-export | csv-injection |
| protocol-check | graphql, websocket, soapaction-spoofing, ldap-injection |
| business-logic | business-logic |

각 그룹 에이전트(`prompts/phase1-group-agent.md`)의 분석 흐름:

1. `prompts/guidelines-phase1.md` (공통 지침) 읽기
2. 그룹 내 각 스캐너의 `phase1.md` 읽기 → Sink 의미론, 안전 패턴 카탈로그 파악
3. 패턴 인덱스 JSON 읽기 → 분석 대상 파일 확정
4. **Sink-first 분석**: 패턴 인덱스의 모든 파일을 전수 분석 (하한선)
5. **Source-first 분석**: 사용자 입력 Source에서 위험 함수까지 추적
6. **래퍼 함수 재귀 추적**: 유틸리티 파일의 Sink를 호출하는 코드까지 최대 3단계 추적
7. 후보 목록을 `===SCANNER_BOUNDARY===` 구분자 + `[스캐너명]` 태그로 반환

**결과 수집:** 모든 그룹 에이전트의 결과를 통합하여 **후보 마스터 목록**을 생성합니다. 각 후보에 고유 ID(예: `XSS-1`, `SSRF-2`)를 부여하며, 이 마스터 목록이 이후 모든 단계의 단일 진실 원천입니다.

#### Step 3-2: 연계 분석

Phase 1 후보가 2건 이상이면 `sub-skills/chain-analysis/SKILL.md`에 따라 연계 분석 에이전트를 실행합니다.

```mermaid
flowchart LR
    P["전제조건\n매트릭스"] --> M["연계\n매트릭스"]
    M --> R["R1~R5\n규칙 검사"]
    R -->|통과| C["공격 체인\n구성"]
    R -->|폐기| I["독립 후보\n정리"]

    style P fill:#16213e,stroke:#0f3460,color:#eee
    style M fill:#16213e,stroke:#0f3460,color:#eee
    style R fill:#533483,stroke:#533483,color:#fff
    style C fill:#e94560,stroke:#e94560,color:#fff
    style I fill:#0f3460,stroke:#0f3460,color:#eee
```

| 단계 | 설명 |
|------|------|
| 전제조건 매트릭스 | 각 후보의 트리거 전제조건을 `[권한]`/`[데이터]`/`[네트워크]`/`[환경]`으로 분류 |
| 연계 매트릭스 | "후보 A의 출력이 후보 B의 입력 sink에 코드 경로로 도달하는가?" (파일:라인 2개 이상 필수) |
| 체인 구성 규칙 검사 | R1(포함 관계), R2(정찰 결함), R3(동일 권한 잉여), R4(데이터 흐름 부재), R5(Narrative 의존) — 1개라도 해당 시 폐기 |
| 공격 체인 구성 | 규칙 검사 통과한 것만 "완전 체인" 또는 "부분 체인"으로 작성 |
| 독립 후보 정리 | 체인에 미포함된 후보별 사유 테이블 |

> 체인 0건은 정상 결과입니다. 억지 체인 1건보다 무체인 결론이 우월합니다.

#### Step 3-3: 동적 분석 정보 요청

Phase 1 후보가 발견되면, 동적 테스트에 필요한 정보를 한번에 사용자에게 요청합니다:

```
## 동적 테스트 진행을 위해 필요한 정보

1. **테스트 환경 URL**: https://sandbox-...
2. **세션 쿠키/인증 토큰**: (로그인 후 쿠키 값)
3. **[XSS 후보 2건]**: 추가 정보 불필요
4. **[SSRF 후보 1건]**: 외부 콜백 서비스 URL (webhook.site 등)
5. **[OAuth 후보 1건]**: OAuth 인가 코드 (수동 획득 필요)
```

이 시점에서 사용자의 응답을 기다립니다. 사용자가 명시적으로 거부한 경우에만 동적 분석을 건너뜁니다.

#### Step 3-4: 도구 권한 사전 확인

동적 테스트에 필요한 도구(`curl`, `node`, `npx`, `python3`) 권한이 Claude Code `settings.json`의 `permissions.allow`에 포함되어 있는지 확인합니다. 누락 시 사용자에게 추가 여부를 묻습니다.

#### Step 3-5: Phase 2 동적 분석 (Tier 기반 병렬화)

후보가 발견된 모든 스캐너에 대해 동적 테스트를 수행합니다. 인증 컨텍스트에 따라 3개 Tier로 분류하여, Tier 간 병렬 실행합니다.

| Tier | 특성 | 해당 스캐너 | 실행 방식 |
|------|------|------------|----------|
| **A** | 인증 불요 | security-headers, http-smuggling, host-header, http-method-tampering, crlf-injection, sourcemap, subdomain-takeover | Tier 내 순차, 다른 Tier와 **병렬** |
| **B** | 공유 세션 | xss, sqli, ssrf 등 대부분의 스캐너 | Tier 내 **순차** |
| **C** | 독립 인증 | oauth, saml, jwt | Tier 내 순차, Tier B와 **병렬** |

각 스캐너 에이전트는:
1. `prompts/guidelines-phase2.md` (공통 지침) 읽기
2. 해당 스캐너의 `phase2.md` 읽기
3. **도메인 분류** (sandbox만 허용, prod/cbt/staging 차단)
4. 모든 후보에 대해 curl/Playwright로 테스트 실행
5. 결과를 `확인됨`/`후보`/`안전`으로 판정

**도메인 안전 규칙:** sandbox/dev 키워드가 있는 도메인만 테스트 허용. prod, cbt, staging 도메인에서는 동적 테스트를 절대 수행하지 않습니다.

#### Step 3-6: 결과 검증

모든 동적 분석 완료 후, **보고서 작성 전에** 체크리스트를 출력합니다:

```
| ID | 후보 제목 | 테스트 수행 | 결과 | 미수행 사유 |
|----|----------|------------|------|------------|
| XSS-1 | Comment innerHTML | ✓ | 확인됨 | — |
| SSRF-2 | Webhook URL fetch | ✗ | — | [환경 제한] |
```

미수행 항목에 대한 즉시 조치:

| 사유 태그 | 조치 |
|-----------|------|
| `[도구 한계]` | 메인 에이전트가 직접 해당 테스트를 재실행 |
| `[정보 부족]` | 사용자에게 추가 정보 요청 |
| `[환경 제한]` | "후보"로 보고서에 포함 (사유 명시) |

**최종 점검:** 모든 항목에 상태가 부여되고, 모든 후보에 실제 URL 경로가 확정된 후에만 Step 4로 진행합니다.

---

### Step 4: 보고서 생성

`sub-skills/scan-report/SKILL.md`에 따라 통합 보고서를 생성합니다. 상세 흐름은 [보고서 파이프라인](#보고서-파이프라인) 참조.

---

## 스캐너 목록

### 37개 취약점 스캐너

| # | 스캐너 | 취약점 유형 | 그룹 |
|---|--------|-----------|------|
| 1 | xss-scanner | Cross-Site Scripting (Reflected/Stored) | url-navigation |
| 2 | dom-xss-scanner | DOM-based XSS | url-navigation |
| 3 | open-redirect-scanner | Open Redirect | url-navigation |
| 4 | crlf-injection-scanner | CRLF Injection / HTTP Response Splitting | response-header |
| 5 | host-header-scanner | Host Header Attack / IP Spoofing | response-header |
| 6 | http-method-tampering-scanner | HTTP Method Tampering | response-header |
| 7 | sqli-scanner | SQL Injection | db-query |
| 8 | nosqli-scanner | NoSQL Injection | db-query |
| 9 | command-injection-scanner | OS Command Injection | process-execution |
| 10 | ssti-scanner | Server-Side Template Injection | process-execution |
| 11 | ssrf-scanner | Server-Side Request Forgery | server-request |
| 12 | pdf-generation-scanner | PDF Generation SSRF/LFI | server-request |
| 13 | path-traversal-scanner | Path Traversal / LFI | file-system |
| 14 | file-upload-scanner | Unrestricted File Upload | file-system |
| 15 | zipslip-scanner | Zip Slip (Archive Path Traversal) | file-system |
| 16 | xxe-scanner | XML External Entity | xml-serialization |
| 17 | xslt-injection-scanner | XSLT Injection | xml-serialization |
| 18 | deserialization-scanner | Insecure Deserialization | xml-serialization |
| 19 | jwt-scanner | JWT Tampering | auth-protocol |
| 20 | oauth-scanner | OAuth Authentication Bypass | auth-protocol |
| 21 | saml-scanner | SAML Authentication Bypass | auth-protocol |
| 22 | csrf-scanner | Cross-Site Request Forgery | auth-protocol |
| 23 | idor-scanner | Insecure Direct Object Reference | auth-protocol |
| 24 | redos-scanner | Regular Expression DoS | client-rendering |
| 25 | css-injection-scanner | CSS Injection | client-rendering |
| 26 | prototype-pollution-scanner | Prototype Pollution | client-rendering |
| 27 | http-smuggling-scanner | HTTP Request Smuggling | infra-config |
| 28 | sourcemap-scanner | Source Map Exposure | infra-config |
| 29 | subdomain-takeover-scanner | Subdomain Takeover | infra-config |
| 30 | csv-injection-scanner | CSV / Formula Injection | data-export |
| 31 | graphql-scanner | GraphQL Vulnerabilities | protocol-check |
| 32 | websocket-scanner | WebSocket Vulnerabilities | protocol-check |
| 33 | soapaction-spoofing-scanner | SOAPAction Spoofing | protocol-check |
| 34 | ldap-injection-scanner | LDAP Injection | protocol-check |
| 35 | xpath-injection-scanner | XPath Injection | protocol-check |
| 36 | security-headers-scanner | Security Headers (CSP, CORS, HSTS 등) | infra-config |
| 37 | business-logic-scanner | Business Logic Vulnerabilities | business-logic |

---

## 개별 스캐너 구조

각 스캐너는 동일한 디렉토리 구조를 따릅니다:

```
noah-sast/scanners/{scanner-name}/
├── phase1.md      # 정적 분석 지침 (frontmatter grep_patterns + Sink 의미·판정·안전 패턴)
└── phase2.md      # 동적 테스트 지침 (테스트 절차, 도구, 스캐너별 확인됨 조건)
```

> grep 패턴은 각 스캐너의 `phase1.md` 최상단 YAML frontmatter (`grep_patterns:`)에 정의되어 있다. Step 0 grep 인덱싱 에이전트가 37개 phase1.md frontmatter를 직접 파싱하여 사용한다. 별도 통합 yml 파일은 없다.

### phase1.md 핵심 구조

```markdown
---
grep_patterns:
  - "innerHTML"
  - "dangerouslySetInnerHTML"
  - "\\.html\\s*\\("
  # ...
---

> ## 핵심 원칙: "..."

## Sink 의미론
## Source-first 추가 패턴
## 자주 놓치는 패턴 (Frequently Missed)
## 안전 패턴 카탈로그 (FP Guard)
## 후보 판정 의사결정
## 후보 판정 제한
```

---

## 분석 방법론

### Sink-first + Source-first 병행

```mermaid
flowchart TB
    subgraph SinkFirst["Sink-first (패턴 인덱스 기반)"]
        SI1["패턴 인덱스에서\nSink 위치 확인"]
        SI2["Sink 코드를\nRead로 확인"]
        SI3["Source(사용자 입력)까지\n역방향 추적"]
    end

    subgraph SourceFirst["Source-first (입력값 추적)"]
        SO1["@RequestParam, req.query 등\n입력 지점에서 출발"]
        SO2["입력값이 위험 함수에\n도달하는지 추적"]
        SO3["패턴 인덱스에 없는\nSink도 발견 가능"]
    end

    SI1 --> SI2 --> SI3
    SO1 --> SO2 --> SO3
    SI3 --> Result["후보 판정"]
    SO3 --> Result

    style SinkFirst fill:#16213e,stroke:#e94560,color:#eee
    style SourceFirst fill:#16213e,stroke:#533483,color:#eee
    style Result fill:#e94560,stroke:#e94560,color:#fff
```

### 판정 기준

| 판정 | 조건 |
|------|------|
| **후보** | Source→Sink 경로가 존재하고 중간에 검증/살균이 없음 |
| **안전** | 프레임워크 내장 방어, 명시적 sanitize, 타입 제약 등으로 방어됨 |
| **확인됨** | 동적 테스트에서 실제 트리거 확인 (코드 경로별 개별 증거 필요) |

---

## 보고서 파이프라인

보고서 생성은 `scan-report` 스킬이 담당하며, 5단계 파이프라인으로 구성됩니다.

| 단계 | 처리 | 담당 |
|------|------|------|
| Step 1 | 스켈레톤 작성 (헤더, 요약, 플레이스홀더) | 메인 에이전트 |
| Step 2 | 스캐너별 상세 섹션 병렬 작성 | 서브에이전트 |
| Step 3 | `assemble_report.py`로 MD 조립 + 요약 테이블 자동 생성 | Python 스크립트 |
| Step 4 | `scan-report-review`로 소스코드 대조 검증 → `md_to_html.py` HTML 변환 | 검증 에이전트 + 스크립트 |
| Step 5 | `validate_links.py` + `validate_report.py` 정량 검증 | Python 스크립트 |

### 보고서 출력물

| 파일 | 설명 |
|------|------|
| `noah-sast-report.md` | 마크다운 원본 |
| `noah-sast-report.html` | 브라우저용 HTML (단일 파일, 외부 의존성 없음) |

---

## 사용법

### 기본 실행

Claude Code에서 다음 중 하나를 입력합니다:

```
/noah-sast
sast
소스코드 취약점 스캔
```

### 실행 흐름

```mermaid
flowchart TD
    User["사용자: /noah-sast"] --> S0["Step 0: 캐시 확인 → grep 인덱싱"]
    S0 --> S1["Step 1: 프로젝트 스택 분석"]
    S1 --> S2["Step 2: 스캐너 선별\n(다국어 의존성 + AI 검토)"]
    S2 --> S3["Step 3-1: Phase 1 정적 분석\n(그룹 병렬 실행)"]
    S3 --> Check{후보 발견?}
    Check -->|0건| S4["Step 4: 보고서 생성"]
    Check -->|2건+| Chain["Step 3-2: 연계 분석\n(R1~R5 규칙 검사)"]
    Check -->|1건| Ask
    Chain --> Ask["Step 3-3: 동적 테스트 정보 요청"]
    Ask --> UserReply{사용자 응답}
    UserReply -->|정보 제공| Perm["Step 3-4: 도구 권한 확인"]
    UserReply -->|거부| S4
    Perm --> Dynamic["Step 3-5: 동적 분석\n(Tier A/B/C 병렬)"]
    Dynamic --> Verify["Step 3-6: 결과 검증\n(미수행 항목 보완)"]
    Verify --> S4
    S4 --> Open["브라우저에서 보고서 열기"]

    style User fill:#e94560,stroke:#e94560,color:#fff
    style Open fill:#e94560,stroke:#e94560,color:#fff
    style Check fill:#533483,stroke:#533483,color:#fff
    style UserReply fill:#533483,stroke:#533483,color:#fff
```

### 설치

`skills/noah-sast/` 디렉토리를 `~/.claude/skills/` 또는 프로젝트의 `.claude/skills/`에 복사합니다:

```bash
cp -r skills/noah-sast ~/.claude/skills/
```

---

## 디렉토리 구조

```
~/.claude/skills/noah-sast/
├── SKILL.md                          # 통합 오케스트레이터
│
├── prompts/                          # 서브 에이전트 지시 문서 (공통 지침 + 프롬프트)
│   ├── guidelines-phase1.md          # 정적 분석 공통 지침
│   ├── guidelines-phase2.md          # 동적 분석 공통 지침
│   ├── grep-agent.md                 # grep 인덱싱 에이전트 프롬프트
│   └── phase1-group-agent.md         # Phase 1 그룹 에이전트 프롬프트
│
├── scanners/                         # 37개 취약점 스캐너
│   ├── xss-scanner/
│   │   ├── phase1.md                 # 정적 분석 지침 (핵심 원칙 포함)
│   │   └── phase2.md                 # 동적 테스트 지침
│   ├── sqli-scanner/
│   └── ... (37개)
│
├── tools/                            # Python 유틸리티 스크립트
│   ├── scanner-selector.py           # 스캐너 선별 + 그룹 리밸런싱
│   ├── build-master-list.py          # Phase 1 결과 → master-list.json
│   ├── cache_manager.py              # grep 인덱스 증분 캐시
│   └── parse_phase1_output.py        # Phase 1 출력 파서
│
├── sub-skills/                       # SKILL.md 기반 서브스킬
│   ├── scan-report/                  # 보고서 작성
│   │   ├── SKILL.md
│   │   ├── assemble_report.py        # MD 조립
│   │   ├── md_to_html.py             # HTML 변환
│   │   ├── validate_links.py         # 앵커 링크 검증
│   │   ├── validate_report.py        # 정량 검증
│   │   └── vuln-format.md            # 취약점 상세 형식 템플릿
│   ├── scan-report-review/           # 보고서 정확성 검증
│   │   ├── SKILL.md
│   │   └── checklist.md
│   ├── chain-analysis/               # 연계 분석
│   │   ├── SKILL.md
│   │   └── chain-construction-rules.md
│   └── webapp-testing/               # Playwright 동적 테스트 도구
│       └── SKILL.md
│
└── tests/                            # grep 패턴 커버리지 테스트
    └── grep-coverage/
        ├── run_coverage.py
        └── fixtures/                 # 35개 스캐너별 must_hit.txt
```
