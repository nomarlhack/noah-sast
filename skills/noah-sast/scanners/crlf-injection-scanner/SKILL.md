---
grep_patterns:
  - "res\\.setHeader("
  - "res\\.writeHead("
  - "res\\.header("
  - "res\\.set("
  - "res\\.cookie("
  - "res\\.attachment("
  - "response\\.headers\\["
  - "response\\.set_cookie("
  - "HttpResponseRedirect("
  - "response\\.setHeader("
  - "response\\.addHeader("
  - "redirect_to"
  - "cookies\\["
  - "header("
  - "setcookie("
  # Source patterns
  - "@RequestParam"
  - "@RequestBody"
  - "req\\.query"
  - "req\\.body"
---

# CRLF Injection Scanner

소스코드 분석으로 CRLF Injection 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 HTTP 응답 헤더에 개행 문자가 삽입되어 헤더 조작이 가능한지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "헤더가 조작되지 않으면 취약점이 아니다"

소스코드에서 `res.setHeader('Location', userInput)`이 있다고 바로 CRLF Injection으로 보고하지 않는다. 실제로 `\r\n` (CRLF) 문자가 삽입되어 응답 헤더가 분리되거나 새로운 헤더가 추가되는 것을 확인해야 취약점이다.

대부분의 최신 웹 프레임워크와 HTTP 라이브러리는 헤더 값에 개행 문자가 포함되면 자동으로 차단하거나 제거한다. 따라서 프레임워크 버전과 해당 버전의 CRLF 방어 여부를 반드시 확인해야 한다.

## CRLF Injection의 유형

### HTTP Response Splitting
사용자 입력이 HTTP 응답 헤더에 반영될 때 `\r\n`을 삽입하여 응답을 분리한다. 새로운 헤더를 주입하거나, 빈 줄(`\r\n\r\n`)을 삽입하여 응답 본문까지 조작할 수 있다.

### Header Injection
응답 헤더에 새로운 헤더를 추가한다. `Set-Cookie` 헤더를 주입하여 세션 고정(Session Fixation) 공격이나, `Content-Type` 변경으로 XSS를 유발할 수 있다.

### Log Injection
로그 파일에 기록되는 값에 CRLF를 삽입하여 로그를 위조한다. HTTP 응답과 무관하므로 이 스캐너의 범위에서 제외한다.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

