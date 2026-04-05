---
grep_patterns:
  - "innerHTML"
  - "dangerouslySetInnerHTML"
  - "html_safe"
  - "v-html"
  - "\\.html("
  - "outerHTML"
  - "document\\.write"
  - "insertAdjacentHTML"
  - "\\beval("
  - "raw("
  - "<%=="
  - "bypassSecurityTrustHtml"
  - "\\[innerHTML\\]"
  # Source patterns
  - "searchParams\\.get("
  - "useParams("
  - "@RequestParam"
  - "@PathVariable"
  - "@RequestBody"
  - "req\\.query"
  - "req\\.body"
---

# XSS Scanner

소스코드 분석으로 XSS 취약점 후보를 식별한 뒤, 동적 테스트로 실제 스크립트 실행이 가능한지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "실행되지 않으면 취약점이 아니다"

소스코드에서 위험해 보이는 패턴을 찾는 것만으로는 부족하다. `dangerouslySetInnerHTML`이 있다고, `html_safe`가 있다고 바로 취약점으로 보고하지 않는다. 실제로 XSS 페이로드가 삽입되어 스크립트가 실행되는 것을 확인해야 취약점이다.

가정 기반의 취약점 보고는 모의해킹 담당자에게 도움이 되지 않는다. "서버가 침해되면 XSS 가능", "API 응답이 변조되면 위험" 같은 가정은 취약점이 아니라 아키텍처 의견이다. 사용자가 직접 제어할 수 있는 입력으로 스크립트를 실행시킬 수 있어야 한다.

**단, "즉시 실행되지 않음"을 "결코 실행되지 않음"으로 해석하지 않는다.**
`ReactDOMServer.renderToStaticMarkup()` / `renderToString()` 내부의 `dangerouslySetInnerHTML`은 그 시점에 DOM에 삽입되지 않는다. 그러나 반환된 HTML 문자열이 이후 `$(el).html()`, `innerHTML`, 다른 `dangerouslySetInnerHTML`로 전달되면 XSS가 발생한다. 이 경우 "renderToStaticMarkup 내부이므로 실행되지 않는다"는 판단은 틀렸다. **반환값이 어디로 흘러가는지 추적을 완료하기 전까지 안전하다고 판단하지 않는다.**

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

