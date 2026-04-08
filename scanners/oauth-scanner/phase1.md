> ## 핵심 원칙: "인증이 우회되지 않으면 취약점이 아니다"
>
> 소스코드에서 `state` 파라미터를 검증하지 않는다고 바로 취약점으로 보고하지 않는다. 실제로 공격자가 OAuth 흐름을 조작하여 다른 사용자의 계정에 접근하거나, 인가 코드를 탈취하여 악용할 수 있는 것을 확인해야 취약점이다.
>

### Phase 1: 정찰 (소스코드 분석)

OAuth 구현을 분석하여 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: OAuth 라이브러리/프레임워크 확인

   **Node.js:**
   - `passport` + `passport-oauth2`, `passport-kakao`, `passport-google-oauth20` 등
   - `openid-client` — OIDC 클라이언트
   - `next-auth` / `auth.js` — Next.js 인증
   - `grant` — OAuth 미들웨어
   - 직접 구현 (axios/fetch로 OAuth 엔드포인트 호출)

   **Python:**
   - `authlib` — OAuth/OIDC 라이브러리
   - `python-social-auth` / `social-django`
   - `oauthlib` + `requests-oauthlib`
   - `Flask-OAuthlib`, `Flask-Dance`

   **Java:**
   - Spring Security OAuth2 (`spring-boot-starter-oauth2-client`)
   - `scribejava`

   **Ruby:**
   - `omniauth` + provider gems

2. **OAuth 흐름 분석**: 사용 중인 OAuth 흐름과 설정 확인

   **인가 요청 (Authorization Request):**
   - `state` 파라미터를 생성하고 세션에 저장하는지
   - `state`를 콜백에서 검증하는지 (세션의 값과 비교)
   - `nonce` 파라미터 사용 여부 (OIDC)
   - PKCE (`code_challenge`, `code_verifier`) 적용 여부
   - `redirect_uri`를 명시적으로 지정하는지

   **콜백 처리 (Callback):**
   - `state` 파라미터 검증 로직
   - 인가 코드를 토큰으로 교환하는 로직
   - `redirect_uri`가 토큰 교환 요청에도 포함되는지
   - 에러 응답 처리 (`error`, `error_description`)

   **redirect_uri 검증 (OAuth 서버 구현 시):**
   - 정확한 URI 매칭 (exact match) vs 부분 매칭
   - 와일드카드 허용 여부
   - localhost/127.0.0.1 허용 여부
   - 등록된 redirect_uri 목록과 비교하는지

   **토큰 처리:**
   - Access Token 저장 위치 (쿠키, localStorage, 메모리)
   - Refresh Token 처리
   - `id_token` 검증 (서명, iss, aud, exp, nonce)
   - Token scope 검증

3. **클라이언트 시크릿 확인**:
   - 소스코드에 하드코딩되어 있는지
   - 환경변수에서 로드되는지
   - 프론트엔드(SPA) 코드에 노출되어 있는지

4. **후보 목록 작성**: 각 후보에 대해 "어떻게 OAuth 흐름을 조작하면 인증을 우회할 수 있는지"를 구체적으로 구상. 데이터 흐름 추적을 완료한 뒤에도 공격 경로가 없으면 버린다. 추적 없이 직관으로 버리지 않는다..

## 후보 판정 제한

OAuth 프로토콜을 직접 구현하는 코드가 있는 경우만 분석 대상. 외부 서비스에 위임하는 경우 제외.
