---
name: path-traversal-scanner
description: "소스코드 분석과 동적 테스트를 통해 Path Traversal / LFI(Local File Inclusion) 취약점을 탐지하는 스킬. 사용자 입력이 파일 시스템 경로나 내부 API 경로에 반영되는 경로를 추적하고, 실제로 의도하지 않은 파일을 읽거나 내부 API를 호출할 수 있는지 검증한다. 사용자가 'path traversal 찾아줘', '경로 조작 스캔', 'LFI 스캔', '파일 포함 취약점', '디렉토리 트래버설', 'path traversal audit', '내부 API 경로 조작', 'LFI 점검' 등을 요청할 때 이 스킬을 사용한다."
grep_patterns:
  - "fs\\.readFile"
  - "fs\\.readFileSync"
  - "fs\\.createReadStream"
  - "path\\.join("
  - "path\\.resolve("
  - "fs\\.writeFile"
  - "send_file"
  - "render.*file:"
  - "File\\.open"
  - "File\\.read"
  - "file_get_contents("
  - "include("
  - "require("
  - "open("
  - "readFile"
  # Source patterns
  - "searchParams\\.get("
  - "@RequestParam"
  - "@PathVariable"
  - "req\\.query"
  - "req\\.params"
---

# Path Traversal Scanner

소스코드 분석으로 Path Traversal / LFI 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 의도하지 않은 파일에 접근하거나 내부 API를 호출할 수 있는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "의도하지 않은 리소스에 접근하지 못하면 취약점이 아니다"

소스코드에서 `fs.readFile(userInput)`이 있다고 바로 LFI로 보고하지 않는다. 실제로 `../` 등 경로 조작 문자를 삽입하여 의도하지 않은 파일의 내용을 읽거나, 내부 API의 다른 엔드포인트를 호출할 수 있는 것을 확인해야 취약점이다.

## Path Traversal의 유형

### 파일 시스템 Path Traversal
사용자 입력에 `../`를 삽입하여 허용된 디렉토리 밖의 파일을 읽는 공격. 가장 일반적인 LFI 형태.

### File Inclusion
서버사이드 코드에서 사용자 입력을 파일 경로로 사용하여 동적으로 파일을 포함(include)하는 경우. PHP의 `include()`, `require()` 등. Node.js에서는 `require(userInput)` 등.

### Arbitrary File Read
파일 다운로드, 미리보기, 로그 조회 등의 기능에서 사용자가 경로를 조작하여 임의 파일을 읽는 경우.

### 내부 API Path Traversal
사용자 입력이 URL 경로 파라미터(`@PathVariable` 등)로 사용되어 내부 API 호출 URL에 삽입되는 경우. 경로 구분자(`/`, `%2f`)를 삽입하여 프록시 체인을 통해 의도하지 않은 내부 API 엔드포인트를 호출할 수 있다.

**전형적인 공격 패턴:**
서비스 A → 프록시/게이트웨이 B → 백엔드 서비스 C 구조에서, A의 경로 파라미터에 `%2f`(URL 인코딩된 `/`)를 삽입하면 B가 C로 전달하는 URL 경로가 변경되어 C의 다른 API를 호출할 수 있다.

```
# 정상 요청
GET /api/bots/{botId} → 내부: GET /v2/bots/{botId}/alarms

# 경로 조작 요청
GET /api/bots/abc%2f..%2fusers → 내부: GET /v2/bots/abc/../users → GET /v2/users
→ 의도하지 않은 내부 API (/v2/users) 호출 성공
```

이 유형은 URL 인코딩된 경로 구분자(`%2f`, `%5c`)가 프록시/게이트웨이 단계에서 디코딩되면서 발생한다. 프레임워크별 URL 디코딩 시점과 경로 정규화 동작의 차이가 핵심이다.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 `~/.claude/skills/noah-sast/agent-guidelines.md`를 참조한다.
