---
name: open-redirect-scanner
description: "소스코드 분석과 동적 테스트를 통해 Open Redirect 취약점을 탐지하는 스킬. 사용자 입력이 리다이렉트 대상 URL에 반영되는 경로를 추적하고, 실제로 외부 도메인으로 리다이렉트가 발생하는지 검증한다. 사용자가 '오픈리다이렉트 찾아줘', 'open redirect 스캔', '리다이렉트 취약점', 'URL 리다이렉션 점검', 'open redirect audit' 등을 요청할 때 이 스킬을 사용한다."
grep_patterns:
  - "res\\.redirect("
  - "res\\.writeHead("
  - "HttpResponseRedirect("
  - "redirect("
  - "redirect_to"
  - "redirect_back"
  - "header('Location"
  - "window\\.location\\.href\\s*="
  - "window\\.location\\.replace("
  - "window\\.location\\.assign("
  - "window\\.location\\s*="
  - "location\\.href\\s*="
  - "window\\.open("
  - "router\\.push("
  - "router\\.replace("
  - "navigate("
  - "webview_mount("
  - "webview_load("
  - "postMessage("
  # Source patterns
  - "searchParams\\.get("
  - "useParams("
  - "useSearchParams"
  - "@RequestParam"
  - "@PathVariable"
  - "req\\.query"
  - "req\\.params"
---

# Open Redirect Scanner

소스코드 분석으로 Open Redirect 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 외부 도메인으로 리다이렉트가 발생하는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "외부로 리다이렉트되지 않으면 취약점이 아니다"

소스코드에서 `window.location.href = userInput`이 있다고 바로 Open Redirect로 보고하지 않는다. 실제로 사용자가 제어한 URL로 리다이렉트가 발생하여 외부 도메인으로 이동하는 것을 확인해야 취약점이다.

가정 기반의 취약점 보고는 도움이 되지 않는다. URL 검증 로직이 존재하면 우회 가능한지까지 테스트해야 한다.

## Open Redirect의 유형

### 서버사이드 리다이렉트
서버가 HTTP 301/302/303/307/308 응답으로 리다이렉트하는 경우. `res.redirect()`, `Location` 헤더, `meta http-equiv="refresh"` 등. curl로 직접 테스트 가능.

### 클라이언트사이드 리다이렉트
브라우저 JavaScript에서 리다이렉트하는 경우. `window.location.href`, `window.location.replace()`, `window.location.assign()`, `form.action + submit()`, `window.open()` 등. curl로는 재현 불가하며 브라우저 테스트가 필요.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 이 스킬과 같은 skills 디렉토리 내의 `noah-sast/agent-guidelines.md`를 참조한다. 이 파일의 위치를 기준으로 `../noah-sast/agent-guidelines.md` 경로로 접근할 수 있다.
