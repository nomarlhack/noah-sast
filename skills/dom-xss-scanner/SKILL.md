---
name: dom-xss-scanner
description: "클라이언트사이드 소스(location.hash, window.name, postMessage 등)에서 DOM Sink로 이어지는 DOM-based XSS 취약점을 탐지하는 스킬. 서버를 경유하지 않는 순수 클라이언트사이드 공격 경로만 다루며, Playwright로만 검증한다. xss-scanner가 커버하는 Reflected/Stored XSS는 이 스킬의 범위가 아니다."
grep_patterns:
  - "location\\.hash"
  - "location\\.search"
  - "document\\.referrer"
  - "window\\.name"
  - "addEventListener.*message"
  - "onmessage"
  - "localStorage\\.getItem"
  - "sessionStorage\\.getItem"
  - "\\.innerHTML"
  - "\\.outerHTML"
  - "document\\.write"
  - "\\beval("
  - "setTimeout("
  - "setInterval("
  - "new Function("
  - "insertAdjacentHTML"
  - "\\.html("
  - "\\.append("
  - "\\.prepend("
  - "location\\.href\\s*="
  - "location\\.assign("
  - "location\\.replace("
  # Source patterns
  - "searchParams\\.get("
  - "useParams("
  - "useSearchParams"
---

# DOM XSS Scanner

서버를 경유하지 않는 클라이언트사이드 XSS 취약점을 탐지하는 스킬이다. 소스(Source)가 전적으로 브라우저 환경에 존재하고, Sink까지의 데이터 흐름이 서버를 거치지 않는 경우만 이 스킬이 담당한다.

## 범위 정의

**이 스킬이 다루는 것 (DOM XSS):**
- Source가 `location.hash`, `window.name`, `document.referrer`, `postMessage` 등 서버가 관여하지 않는 클라이언트사이드 값
- Sink가 JS 코드에서 직접 DOM을 조작하는 지점 (`innerHTML`, `eval` 등)
- 서버에 페이로드가 도달하지 않아 curl로 재현이 구조적으로 불가능한 경우

**이 스킬이 다루지 않는 것 (xss-scanner 담당):**
- HTTP 파라미터, 폼 필드 등 서버가 수신하는 Source
- 서버 응답에서 사용자 입력이 반영되는 Reflected/Stored XSS
- API 응답 데이터를 `dangerouslySetInnerHTML`로 렌더링하는 경우 (서버 경유)

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 `~/.claude/skills/noah-sast/agent-guidelines.md`를 참조한다.
