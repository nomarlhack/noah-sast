---
name: noah-sast
description: "35개 취약점 스캐너 스킬을 한번에 실행하고 결과를 통합 보고서로 작성하는 스킬. XSS, SSRF, SQLi, CSRF 등 모든 취약점 유형을 소스코드 분석과 동적 테스트로 점검한다. 사용자가 'noah-sast', 'noah sast', 'sast', '소스코드 취약점 스캔' 등을 요청할 때 이 스킬을 사용한다."
---

# Noah SAST — 통합 취약점 스캐너

35개 개별 취약점 스캐너를 순차적으로 실행하고, 모든 결과를 하나의 통합 보고서로 작성하는 스킬이다.

> `[필수]`는 과거 위반 이력이 있어 추가 강조된 항목이다. 태그가 없는 항목도 모두 준수 의무가 있다.

## 실행 프로세스

### Step -1: SKILLS_DIR 경로 결정

**[필수] 모든 Step보다 먼저 실행한다.** 이 스킬과 개별 스캐너들이 설치된 skills 디렉토리의 절대 경로를 결정한다.

아래 Bash 명령을 실행하여 `SKILLS_DIR`을 결정한다:

```bash
if [ -d ".claude/skills/noah-sast" ]; then
  echo "$(cd .claude/skills && pwd)"
elif [ -d "$HOME/.claude/skills/noah-sast" ]; then
  echo "$HOME/.claude/skills"
fi
```

이 출력값을 `SKILLS_DIR` 변수로 보관한다. 이후 모든 Step에서 스킬/스캐너 경로 참조 시 `<SKILLS_DIR>/`을 접두어로 사용한다. 하드코딩된 `<SKILLS_DIR>/`를 사용하지 않는다.

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

Agent 도구로 grep 인덱싱 에이전트를 생성한다. 프롬프트는 아래 내용을 그대로 사용하되, `<PROJECT_ROOT>`와 `<PATTERN_INDEX_DIR>`를 실제 값으로 치환한다:

---
**[grep 인덱싱 에이전트 프롬프트]**

당신은 grep 전용 에이전트입니다. 아래 지시를 정확히 따르세요.

## 임무

34개 취약점 스캐너의 grep 패턴을 각 SKILL.md frontmatter에서 읽어,
프로젝트 전체를 grep한 뒤 결과를 파일로 저장한다.

## 단계 1: 각 스캐너 SKILL.md frontmatter에서 grep_patterns 추출

아래 34개 파일의 첫 60줄만 Read 도구로 읽어 YAML frontmatter의
grep_patterns 배열을 추출한다. 60줄을 초과하여 읽지 않는다.

읽을 파일 목록 (모두 <SKILLS_DIR>/ 하위):
xss-scanner/SKILL.md, dom-xss-scanner/SKILL.md, ssrf-scanner/SKILL.md,
open-redirect-scanner/SKILL.md, crlf-injection-scanner/SKILL.md,
csrf-scanner/SKILL.md, path-traversal-scanner/SKILL.md,
file-upload-scanner/SKILL.md, command-injection-scanner/SKILL.md,
sqli-scanner/SKILL.md, http-method-tampering-scanner/SKILL.md,
xxe-scanner/SKILL.md, deserialization-scanner/SKILL.md,
ssti-scanner/SKILL.md, jwt-scanner/SKILL.md, oauth-scanner/SKILL.md,
nosqli-scanner/SKILL.md, ldap-injection-scanner/SKILL.md,
host-header-scanner/SKILL.md, xslt-injection-scanner/SKILL.md,
css-injection-scanner/SKILL.md, xpath-injection-scanner/SKILL.md,
soapaction-spoofing-scanner/SKILL.md, redos-scanner/SKILL.md,
pdf-generation-scanner/SKILL.md, saml-scanner/SKILL.md,
http-smuggling-scanner/SKILL.md, zipslip-scanner/SKILL.md,
graphql-scanner/SKILL.md, sourcemap-scanner/SKILL.md,
csv-injection-scanner/SKILL.md, prototype-pollution-scanner/SKILL.md,
websocket-scanner/SKILL.md, subdomain-takeover-scanner/SKILL.md,
idor-scanner/SKILL.md

## 단계 2: 패턴 일괄 grep 실행

추출한 모든 패턴을 <PROJECT_ROOT> 전체에 Bash로 실행한다.

grep 규칙:
- 명령 형식: grep -rn --binary-files=without-match <INCLUDE_OPTIONS> <EXCLUDE_DIR_OPTIONS> "<패턴>" <PROJECT_ROOT>
- --include 화이트리스트로 소스코드 파일만 대상으로 한다 (아래 목록 참조)
- --exclude-dir로 비소스 디렉토리를 제외한다
- 수집 형식: 파일경로:라인번호 (코드 내용 제외)
- 결과 예시: app/components/Comment.jsx:18

<INCLUDE_OPTIONS> — 소스코드 확장자 화이트리스트 (한 줄로 이어 붙여 사용):
```
--include="*.js" --include="*.jsx" --include="*.mjs" --include="*.cjs"
--include="*.ts" --include="*.tsx" --include="*.mts" --include="*.cts"
--include="*.java" --include="*.kt" --include="*.kts" --include="*.scala" --include="*.groovy" --include="*.clj" --include="*.cljs"
--include="*.py" --include="*.pyw"
--include="*.rb" --include="*.erb" --include="*.rake"
--include="*.php" --include="*.phtml"
--include="*.go"
--include="*.rs"
--include="*.c" --include="*.cpp" --include="*.cc" --include="*.cxx" --include="*.h" --include="*.hpp" --include="*.hxx"
--include="*.cs" --include="*.cshtml" --include="*.razor"
--include="*.swift" --include="*.m" --include="*.mm"
--include="*.dart"
--include="*.ex" --include="*.exs" --include="*.erl" --include="*.hrl"
--include="*.pl" --include="*.pm"
--include="*.lua"
--include="*.ps1" --include="*.psm1"
--include="*.hs"
--include="*.fs" --include="*.fsx" --include="*.ml" --include="*.mli"
--include="*.r" --include="*.R" --include="*.jl" --include="*.nim" --include="*.cr" --include="*.zig" --include="*.d" --include="*.v"
--include="*.sol" --include="*.coffee" --include="*.elm" --include="*.re" --include="*.res"
--include="*.cob" --include="*.cbl" --include="*.f90" --include="*.f95" --include="*.for" --include="*.pas" --include="*.dpr"
--include="*.adb" --include="*.ads" --include="*.vb" --include="*.vbs"
--include="*.scm" --include="*.rkt" --include="*.lisp" --include="*.cl" --include="*.tcl" --include="*.hack" --include="*.abap"
--include="*.cls" --include="*.trigger" --include="*.cfm" --include="*.cfc" --include="*.pp"
--include="*.html" --include="*.htm" --include="*.vue" --include="*.svelte" --include="*.astro" --include="*.marko" --include="*.mdx"
--include="*.jsp" --include="*.asp" --include="*.aspx" --include="*.ejs" --include="*.hbs" --include="*.pug" --include="*.jade"
--include="*.jinja" --include="*.jinja2" --include="*.twig" --include="*.ftl" --include="*.mustache" --include="*.liquid" --include="*.njk" --include="*.vm"
--include="*.conf" --include="*.yaml" --include="*.yml" --include="*.json" --include="*.xml" --include="*.sql"
--include="*.tf" --include="*.tfvars" --include="*.hcl"
--include="*.graphql" --include="*.gql" --include="*.proto"
--include="*.sh" --include="*.bash" --include="*.zsh"
--include="*.lock"
```

<EXCLUDE_DIR_OPTIONS> — 비소스 디렉토리 제외:
```
--exclude-dir="node_modules" --exclude-dir=".git" --exclude-dir="dist" --exclude-dir="build"
--exclude-dir="target" --exclude-dir="out" --exclude-dir=".next" --exclude-dir=".nuxt" --exclude-dir=".cache"
--exclude-dir=".gradle" --exclude-dir="__pycache__" --exclude-dir="vendor" --exclude-dir="Pods" --exclude-dir="bower_components"
--exclude-dir=".idea" --exclude-dir=".vscode" --exclude-dir=".husky"
--exclude-dir="coverage" --exclude-dir=".nyc_output" --exclude-dir=".pytest_cache" --exclude-dir=".mypy_cache" --exclude-dir=".tox"
--exclude-dir=".eggs" --exclude-dir="*.egg-info" --exclude-dir=".terraform" --exclude-dir=".serverless"
--exclude-dir=".parcel-cache" --exclude-dir=".turbo" --exclude-dir=".svn" --exclude-dir=".hg" --exclude-dir="storybook-static"
```

## 단계 3: 스캐너별 패턴 인덱스 파일 저장

먼저 Bash로 디렉토리를 생성한다:
```bash
mkdir -p <PATTERN_INDEX_DIR>
```

각 스캐너의 grep 결과를 **스캐너별 개별 파일**로 Write 도구를 사용해 저장한다.

파일 경로 형식: `<PATTERN_INDEX_DIR>/<스캐너명>.json`

예시:
- `<PATTERN_INDEX_DIR>/xss-scanner.json`
- `<PATTERN_INDEX_DIR>/sqli-scanner.json`
- ... (34개 전체)

각 파일의 저장 형식 (해당 스캐너의 패턴만 포함):
```json
{
  "innerHTML": ["app/components/Comment.jsx:18", "app/components/Post.jsx:55"],
  "dangerouslySetInnerHTML": ["app/components/Comment.jsx:18"],
  "html_safe": []
}
```

저장 시 주의사항:
- 파일경로:라인번호 형식 유지. 코드 내용 포함 금지.
- 히트 없는 패턴도 빈 배열로 포함.
- 34개 스캐너 전체 각각 저장. 누락 금지.

## 단계 4: 카운트 요약만 응답으로 반환

파일 저장 완료 후, 아래 형식의 카운트 요약만 반환한다.
각 스캐너의 JSON 파일 내용 전체를 응답에 포함하지 않는다.

반환 형식:
파일 저장 완료: <PATTERN_INDEX_DIR>/

스캐너별 히트 건수 (파일경로:라인번호 기준):
xss-scanner: N건
dom-xss-scanner: N건
...(34개 전체)...

---

#### Step 0-2: 패턴 인덱스 디렉토리 경로 및 카운트 요약 수신

grep 인덱싱 에이전트가 반환한 **카운트 요약**을 보관한다. 디렉토리 경로는 Step 0-1에서 메인 에이전트가 직접 생성한 `PATTERN_INDEX_DIR` 값을 그대로 사용한다.

- 카운트 요약 → Step 2-1 테이블에 사용
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

#### Step 2-1: **[필수]** 패턴 인덱스 기반 결과 테이블 출력

**Step 0에서 수집한 패턴 인덱스를 기반으로** 스캐너별 grep 결과 건수 테이블을 출력한다. **테이블을 출력하지 않으면 Step 2-2로 진행할 수 없다.**

Step 0에서 grep 인덱싱 에이전트가 이미 모든 패턴을 실행하고 카운트 요약을 반환했으므로 이 단계에서 grep을 추가로 실행하지 않는다. Step 0-2에서 수신한 카운트 요약을 그대로 사용하여 아래 형식으로 출력한다.

**[필수] Step 2-1 출력 형식 (모든 34개 스캐너 포함):**

```
| 스캐너 | grep 결과 건수 |
|--------|-------------|
| (스캐너명) | (패턴 인덱스 집계 건수) |
...
```

#### Step 2-2: 제외 여부 결정 (자동화 스크립트)

`scanner-selector.py`를 실행하여 grep 인덱스 + 프로젝트 아키텍처 기반으로 자동 선별한다:

```bash
python3 <SKILLS_DIR>/noah-sast/scanner-selector.py <PATTERN_INDEX_DIR> <PROJECT_ROOT>
```

스크립트 출력:
- 적용/제외 판정 테이블 (grep 히트 건수 + 사유 포함)
- 적용 스캐너 목록

**기본 원칙: 포함이 기본이고, 제외에는 근거가 필요하다.**
- grep 결과 1건 이상 → 반드시 포함
- grep 결과 0건 → 스크립트가 아키텍처 조건을 검사하여 제외 가능 여부 판단

스크립트 결과를 검토한 후, 필요하면 수동으로 조정한다 (예: 스크립트가 제외했으나 포함이 필요한 경우).

### Step 3: 정적 분석 → 연계 분석 → 동적 분석

정적 분석(Step 3-1)은 선별된 모든 스캐너 에이전트를 **단일 응답에서 동시에** Agent 도구로 실행한다. 연계 분석(Step 3-2)은 정적 분석 결과를 연계하여 공격 시나리오를 도출한다. 동적 분석(Step 3-5)은 세션 충돌 방지를 위해 순차 실행한다. 각 스캐너는 개별 SKILL.md의 Phase 1(소스코드 분석) → Phase 2(동적 테스트) 프로세스를 따른다.

#### Step 3-1: 정적 분석 (개별 스캐너의 Phase 1 실행)

**[필수] 선별된 스캐너를 아래 그룹 정의에 따라 묶어, 그룹당 1개 에이전트로 실행한다.**

**스캐너 그룹 정의:**

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
| infra-config | http-smuggling, sourcemap, subdomain-takeover |
| data-export | csv-injection |
| protocol-check | graphql, websocket, soapaction-spoofing, ldap-injection |

선별 결과 그룹 내 스캐너가 모두 제외된 그룹은 에이전트를 생성하지 않는다.

**[필수] Phase 1 에이전트는 단일 메시지 안에서 모든 그룹의 Agent 도구를 동시에 호출하여 병렬 실행한다.** 모든 에이전트가 완료된 후에만 Step 3-2로 진행한다. 완료 후 그룹 수와 수신된 결과 수를 대조하여, 누락된 에이전트가 있으면 해당 그룹만 재실행한다.

각 그룹 에이전트 프롬프트에는 다음을 포함한다:
- Phase 1 공통 지침: `<SKILLS_DIR>/noah-sast/agent-guidelines-phase1.md`
- 그룹 내 각 스캐너의 phase1.md 경로
- 그룹 내 각 스캐너의 패턴 인덱스 파일 경로 (`<PATTERN_INDEX_DIR>/<scanner-name>.json`)

에이전트 프롬프트 예시:

```
당신은 취약점 분석 에이전트입니다.

먼저 아래 파일을 읽으세요:
- <SKILLS_DIR>/noah-sast/agent-guidelines-phase1.md

아래 스캐너를 순서대로 실행하세요.
각 스캐너마다 해당 phase1.md를 읽고, 패턴 인덱스를 읽고, 분석을 수행하세요.
이미 읽은 파일은 다시 읽지 마세요.
결과는 스캐너별로 === 스캐너명 === 구분자로 나누어 반환하세요.

스캐너 1: xss-scanner
- phase1.md: <SKILLS_DIR>/xss-scanner/phase1.md
- 패턴 인덱스: <PATTERN_INDEX_DIR>/xss-scanner.json

스캐너 2: dom-xss-scanner
- phase1.md: <SKILLS_DIR>/dom-xss-scanner/phase1.md
- 패턴 인덱스: <PATTERN_INDEX_DIR>/dom-xss-scanner.json

스캐너 3: open-redirect-scanner
- phase1.md: <SKILLS_DIR>/open-redirect-scanner/phase1.md
- 패턴 인덱스: <PATTERN_INDEX_DIR>/open-redirect-scanner.json
```

> **주의: Phase 1 완료 시점에서 보고서 파일(.md/.html)을 생성하지 않는다.** 보고서는 Step 4에서만 작성한다.

**Phase 1 결과 수집 및 추적:**
- 그룹 에이전트가 반환한 결과를 `=== 스캐너명 ===` 구분자로 분리하여, 각 스캐너의 후보를 개별적으로 추출한다.
- 추출한 모든 후보를 하나의 **후보 마스터 목록**으로 통합한다.
- 후보 마스터 목록은 스캐너별로 구분하고, 각 후보에 고유 ID를 부여한다 (예: `XSS-1`, `SSRF-2`, `OAuth-1`).
- 이 마스터 목록은 연계 분석(Step 3-2), 동적 분석(Step 3-5), 리포팅(Step 4) 전체에서 **단일 진실 원천(single source of truth)**으로 사용한다.
- **마스터 목록에 있는 후보는 동적 분석에서 "안전"으로 판정되지 않는 한, 반드시 최종 보고서에 포함되어야 한다.**

#### Step 3-2: 연계 분석

Phase 1에서 후보가 2건 이상 발견된 경우, `<SKILLS_DIR>/chain-analysis/SKILL.md`에 정의된 프로세스에 따라 **연계 분석 에이전트**를 실행한다. 후보가 1건 이하이면 이 단계를 건너뛴다.

에이전트 프롬프트에는 chain-analysis SKILL.md 경로, 후보 마스터 목록, 프로젝트 컨텍스트, 이상 없음 요약을 포함한다.

**연계 분석 결과 활용:**
- **Step 4 (보고서)**: 공격 체인을 보고서의 핵심 섹션으로 포함한다.
- **Step 3-3 (동적 테스트 안내)**: 공격 체인의 테스트 순서와 전제조건을 사용자에게 제시하여, 체인 단위 테스트를 대화형으로 진행한다. 개별 스캐너 에이전트로는 체인 테스트를 자동화하지 않는다.

#### Step 3-3: 동적 분석 정보 일괄 요청 → 사용자 응답 대기

Phase 1에서 후보가 발견된 스캐너들의 동적 테스트에 필요한 정보를 한번에 정리하여 사용자에게 요청한다. 연계 분석(Step 3-2)에서 공격 체인이 도출된 경우, 체인별 테스트 시나리오도 함께 제시한다. **이 시점에서 사용자의 응답을 기다린다. 보고서를 작성하지 않는다.**

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

사용자가 필요한 정보를 제공하면, 후보가 발견된 모든 스캐너에 대해 동적 분석을 수행한다. **[필수] 스캐너당 1 에이전트 원칙을 따른다. 여러 스캐너의 동적 분석을 하나의 에이전트에 묶지 않는다.** 각 에이전트 프롬프트에는 `<SKILLS_DIR>/<scanner-name>/phase2.md`와 `<SKILLS_DIR>/noah-sast/agent-guidelines-phase2.md` 경로를 포함한다.

**[필수] 동적 분석은 반드시 순차 실행을 유지한다. 정적 분석의 병렬 실행 방식을 적용하지 않는다.** 동적 테스트는 동일 테스트 서버에 동시 HTTP 요청을 보내면 세션 충돌이 발생할 수 있으므로, 개별 취약점 스캐너 에이전트를 하나씩 순서대로 실행한다.

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

Step 3에서 수집한 모든 개별 스캐너의 결과를 **`scan-report` 스킬(`<SKILLS_DIR>/scan-report/SKILL.md`)에 전달**하여 통합 보고서를 생성한다.

**전달하는 데이터:**
- 후보 마스터 목록 (각 후보의 최종 상태: 확인됨/후보/안전)
- 스캐너별 Phase 1 소스코드 분석 결과 (Source→Sink 경로, 코드 스니펫)
- 스캐너별 동적 분석 결과 (curl 요청/응답 또는 Playwright 실행 결과 증거)
- 이상 없음 스캐너의 점검 항목 요약
- 미적용 스캐너 목록 및 제외 사유

scan-report SKILL.md를 읽고, 그 스킬이 정의하는 보고서 작성 프로세스를 수행한다. **noah-sast는 보고서를 직접 작성하지 않는다.**

**[필수] scan-report의 Step 3(MD 조립) 완료 후, Step 4(HTML 변환) 이전에 `scan-report-review` 스킬을 실행하여 보고서 정확성을 검증한다.** `<SKILLS_DIR>/scan-report-review/SKILL.md`를 읽고, 보고서 MD 파일 경로와 프로젝트 루트 경로를 전달한다. 리뷰에서 부정확한 내용이 발견되면 MD 파일이 수정된 후 HTML 변환으로 진행한다.

## 유의사항 (메인 에이전트 — 일반)

- 모든 동적 테스트는 sandbox 도메인에서만 수행한다. 사용자가 제공한 도메인이 sandbox인지 불분명하면 반드시 확인한다.
- Phase 1에서 후보가 발견되면 반드시 사용자에게 동적 테스트 진행 여부를 물어본다. 사용자가 명시적으로 거부한 경우에만 건너뛴다.
- 사용자에게 진행 상황을 주기적으로 알린다.
- 각 스캐너의 분석 방법론(판정 기준, 테스트 도구 선택, 세션 관리 등)은 개별 SKILL.md의 규칙을 따른다. noah-sast는 이를 중복 정의하지 않는다.
- 미적용 스캐너는 "해당 없음" 사유와 함께 미적용 목록에 기재한다.
- 테스트 대상 도메인(Host)은 사용자에게 확인받는다. 그 외 동적 정보는 소스코드 분석 또는 HTTP 요청으로 획득하고, 직접 획득이 불가능한 정보만 사용자에게 한번에 요청한다.

## 유의사항 (메인 에이전트 — 개별 취약점 스캐너 에이전트 관리)

정적 분석/동적 분석의 개별 취약점 스캐너 에이전트를 실행·관리하는 메인 에이전트가 따르는 지침.

### 지침 A: 동적 분석 에이전트에 모든 후보 전달

> **동적 분석 에이전트 프롬프트에는 해당 스캐너의 정적 분석에서 발견된 모든 후보를 빠짐없이 포함한다.** 후보 수가 많아 프롬프트가 길어지더라도 생략하지 않는다.

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
- Phase 1 에이전트: `<SKILLS_DIR>/noah-sast/agent-guidelines-phase1.md`
- Phase 2 에이전트: `<SKILLS_DIR>/noah-sast/agent-guidelines-phase2.md`

에이전트 프롬프트에 해당 Phase의 지침 파일 경로를 포함하여, 에이전트가 Read 도구로 읽고 지침을 따르도록 한다. 에이전트 프롬프트에 지침 내용을 인라인으로 복사하지 않는다.

