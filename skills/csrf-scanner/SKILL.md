---
name: csrf-scanner
description: "소스코드 분석과 동적 테스트를 통해 CSRF(Cross-Site Request Forgery) 취약점을 탐지하는 스킬. 상태 변경 요청(POST/PUT/DELETE 등)에 CSRF 토큰이나 기타 방어 메커니즘이 적용되어 있는지 분석하고, 실제로 외부 사이트에서 위조된 요청이 처리되는지 검증한다. 사용자가 'CSRF 취약점 찾아줘', 'CSRF 스캔', 'CSRF 점검', 'csrf audit', '크로스사이트 요청 위조' 등을 요청할 때 이 스킬을 사용한다."
grep_patterns:
  - "csrf_exempt"
  - "skip_before_action.*verify_authenticity_token"
  - "csrf\\.disable"
  - "csurf"
  - "csrf-csrf"
  - "csrf-sync"
  - "protect_from_forgery"
  - "SameSite"
  - "X-CSRF-Token"
  - "X-Requested-With"
  - "verify_authenticity_token"
  - "@csrf_exempt"
---

# CSRF Scanner

소스코드 분석으로 CSRF 방어가 누락된 상태 변경 엔드포인트를 식별한 뒤, 동적 테스트로 실제로 외부 사이트에서 위조된 요청이 처리되는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "위조된 요청이 처리되지 않으면 취약점이 아니다"

CSRF 토큰이 없다고 바로 취약점으로 보고하지 않는다. 토큰이 없더라도 SameSite 쿠키, Origin/Referer 검증, 커스텀 헤더 검증 등 다른 방어 메커니즘이 존재할 수 있다. 실제로 외부 사이트에서 위조된 요청을 보냈을 때 서버가 이를 처리하는 것을 확인해야 취약점이다.

## CSRF 방어 메커니즘

스캔 시 다음 방어 메커니즘이 존재하는지 확인한다. 하나라도 올바르게 적용되어 있으면 CSRF 방어가 된 것이다:

1. **CSRF 토큰**: 폼이나 요청에 서버가 발급한 토큰을 포함하고 서버에서 검증
2. **SameSite 쿠키 속성**: `SameSite=Strict` 또는 `SameSite=Lax`로 설정된 세션 쿠키 (Lax는 GET 요청에서는 전송되므로 GET으로 상태 변경하지 않는지도 확인)
3. **Origin/Referer 헤더 검증**: 서버에서 요청의 Origin 또는 Referer 헤더를 검증
4. **커스텀 헤더 요구**: API가 `X-Requested-With`, `X-CSRF-Token` 등 커스텀 헤더를 요구 (CORS preflight로 방어)
5. **Re-authentication**: 중요 작업에 비밀번호 재입력 요구

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 이 스킬과 같은 skills 디렉토리 내의 `noah-sast/agent-guidelines.md`를 참조한다. 이 파일의 위치를 기준으로 `../noah-sast/agent-guidelines.md` 경로로 접근할 수 있다.
