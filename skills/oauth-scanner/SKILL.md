---
name: oauth-scanner
description: "소스코드 분석과 동적 테스트를 통해 OAuth 인증 취약점을 탐지하는 스킬. OAuth 2.0 / OpenID Connect 구현에서 state 파라미터 검증, redirect_uri 검증, 토큰 처리, PKCE 적용 등의 미흡을 분석하고 검증한다. 사용자가 'OAuth 취약점 찾아줘', 'OAuth 스캔', 'OAuth 인증 점검', 'OIDC 취약점', 'OAuth redirect_uri', 'state 파라미터 검증', 'OAuth audit' 등을 요청할 때 이 스킬을 사용한다."
grep_patterns:
  - "oauth"
  - "OAuth"
  - "omniauth"
  - "authorization_code"
  - "access_token"
  - "redirect_uri"
  - "client_secret"
  - "code_verifier"
  - "code_challenge"
  - "passport-oauth"
  - "openid-client"
  - "next-auth"
  - "authlib"
---

# OAuth Scanner

소스코드 분석으로 OAuth 2.0 / OpenID Connect 구현의 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 인증을 우회하거나 다른 사용자의 계정을 탈취할 수 있는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "인증이 우회되지 않으면 취약점이 아니다"

소스코드에서 `state` 파라미터를 검증하지 않는다고 바로 취약점으로 보고하지 않는다. 실제로 공격자가 OAuth 흐름을 조작하여 다른 사용자의 계정에 접근하거나, 인가 코드를 탈취하여 악용할 수 있는 것을 확인해야 취약점이다.

## OAuth 취약점의 유형

### CSRF를 통한 계정 연결 공격 (Missing State Parameter)
`state` 파라미터가 없거나 검증되지 않으면, 공격자가 자신의 인가 코드를 포함한 콜백 URL을 피해자에게 전송하여 피해자의 계정에 공격자의 OAuth 계정을 연결할 수 있다.

### Open Redirect via redirect_uri
`redirect_uri` 검증이 미흡하면, 인가 코드나 토큰이 공격자의 서버로 전송될 수 있다. 정확한 URI 매칭이 아닌 부분 매칭(prefix, subdomain)을 사용하면 우회 가능.

### Authorization Code Injection
인가 코드를 다른 클라이언트에서 사용하는 공격. PKCE 미적용 시 취약.

### Token Leakage
- `response_type=token` (Implicit Flow)에서 토큰이 URL fragment에 노출
- Referer 헤더를 통한 토큰 유출
- 서버 로그에 토큰 기록

### Insufficient Scope Validation
토큰의 scope를 검증하지 않아 의도하지 않은 리소스에 접근 가능.

### PKCE Downgrade
PKCE를 지원하지만 강제하지 않아, 공격자가 PKCE 없이 인가 코드를 사용할 수 있는 경우.

### Client Secret Exposure
클라이언트 시크릿이 프론트엔드 코드나 공개 저장소에 노출.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 이 스킬과 같은 skills 디렉토리 내의 `noah-sast/agent-guidelines.md`를 참조한다. 이 파일의 위치를 기준으로 `../noah-sast/agent-guidelines.md` 경로로 접근할 수 있다.
