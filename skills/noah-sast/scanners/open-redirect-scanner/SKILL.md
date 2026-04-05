
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

