당신은 grep 전용 에이전트입니다. 아래 지시를 정확히 따르세요.

> 메인 에이전트 사용법: 이 파일을 서브 에이전트에게 그대로 Read하도록 지시하고, 프롬프트에는 `<NOAH_SAST_DIR>`, `<PROJECT_ROOT>`, `<PATTERN_INDEX_DIR>` 세 변수를 **resolve된 실제 경로 문자열**로 치환한 채 전달한다. 본 파일 내용을 인라인 복사하지 않는다.

## 임무

35개 취약점 스캐너의 grep 패턴을 통합 패턴 파일에서 읽어,
프로젝트 전체를 grep한 뒤 결과를 파일로 저장한다.

## 단계 1: 통합 패턴 파일 읽기

`<NOAH_SAST_DIR>/grep-patterns.yml`을 Read 도구로 읽는다.
이 파일에 35개 스캐너의 모든 grep 패턴이 스캐너별로 정의되어 있다.

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
- ... (35개 전체)

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
- 35개 스캐너 전체 각각 저장. 누락 금지.

## 단계 4: 카운트 요약만 응답으로 반환

파일 저장 완료 후, 아래 형식의 카운트 요약만 반환한다.
각 스캐너의 JSON 파일 내용 전체를 응답에 포함하지 않는다.

반환 형식:
파일 저장 완료: <PATTERN_INDEX_DIR>/

스캐너별 히트 건수 (파일경로:라인번호 기준):
xss-scanner: N건
dom-xss-scanner: N건
...(35개 전체)...
