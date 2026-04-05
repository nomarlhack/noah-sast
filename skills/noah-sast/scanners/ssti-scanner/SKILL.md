---
name: ssti-scanner
description: "소스코드 분석과 동적 테스트를 통해 SSTI(Server-Side Template Injection) 취약점을 탐지하는 스킬. 사용자 입력이 서버사이드 템플릿 엔진에 직접 삽입되는 경로를 추적하고, 실제로 템플릿 표현식이 실행되는지 검증한다. 사용자가 'SSTI 찾아줘', 'SSTI 스캔', 'template injection', '템플릿 인젝션', 'SSTI audit', 'SSTI 점검', 'Jinja2 injection', 'EJS injection' 등을 요청할 때 이 스킬을 사용한다."
grep_patterns:
  - "ejs\\.render("
  - "pug\\.render("
  - "nunjucks\\.renderString("
  - "render_template_string("
  - "ERB\\.new("
  - "Liquid::Template\\.parse"
  - "Template("
  - "renderString("
  - "render_string("
  - "template_string"
  - "parseExpression("
  - "SpelExpressionParser"
  - "Freemarker"
  # Source patterns
  - "@RequestParam"
  - "@RequestBody"
  - "req\\.query"
  - "req\\.body"
---

# SSTI Scanner

소스코드 분석으로 SSTI 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 템플릿 표현식이 서버에서 실행되는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "템플릿 표현식이 실행되지 않으면 취약점이 아니다"

소스코드에서 템플릿 엔진을 사용한다고 바로 SSTI로 보고하지 않는다. SSTI는 사용자 입력이 **템플릿 문자열 자체**에 삽입되어 템플릿 엔진이 이를 코드로 해석·실행하는 경우에만 발생한다. 템플릿의 **변수**로 전달되는 것은 SSTI가 아니다.

```
# 안전 — 사용자 입력이 변수로 전달됨
render('hello.ejs', { name: userInput })

# 위험 — 사용자 입력이 템플릿 문자열에 삽입됨
ejs.render('Hello ' + userInput)
```

## SSTI vs XSS 구분

- **SSTI**: 서버사이드 템플릿 엔진이 표현식을 실행. 서버에서 코드가 실행되므로 RCE로 이어질 수 있다.
- **XSS**: 클라이언트 브라우저에서 스크립트가 실행. 서버 코드 실행과 무관.

SSTI 스캐너는 서버사이드 템플릿 표현식 실행만 보고한다. 템플릿 출력에서 HTML이 이스케이프 없이 렌더링되는 것은 XSS 스캐너의 범위이다.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 `../../agent-guidelines.md` (이 파일 기준 상대 경로)를 참조한다.
