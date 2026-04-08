> ## 핵심 원칙: "위조된 요청이 처리되지 않으면 취약점이 아니다"
>
> CSRF 토큰이 없다고 바로 취약점으로 보고하지 않는다. 토큰이 없더라도 SameSite 쿠키, Origin/Referer 검증, 커스텀 헤더 검증 등 다른 방어 메커니즘이 존재할 수 있다. 실제로 외부 사이트에서 위조된 요청을 보냈을 때 서버가 이를 처리하는 것을 확인해야 취약점이다.
>

### Phase 1: 정찰 (소스코드 분석)

상태 변경 엔드포인트에서 CSRF 방어가 누락된 곳을 식별한다.

1. **프로젝트 스택 파악**: 프레임워크/언어 확인 및 내장 CSRF 방어 확인
   - **Next.js/React SPA**: 기본 CSRF 방어 없음. API 라우트에서 별도 구현 필요
   - **Express**: `csurf` 미들웨어 사용 여부 확인 (deprecated — 대안: `csrf-csrf`, `csrf-sync`)
   - **Django**: `CsrfViewMiddleware` 기본 활성화. `@csrf_exempt` 데코레이터로 비활성화하는 곳 확인
   - **Spring**: `CsrfFilter` 기본 활성화. `csrf().disable()` 설정 확인
   - **Rails**: `protect_from_forgery` 기본 활성화. `skip_before_action :verify_authenticity_token` 확인
   - **Laravel**: `VerifyCsrfToken` 미들웨어 기본 활성화. `$except` 배열 확인

2. **상태 변경 엔드포인트 식별**: CSRF 공격 대상이 되는 엔드포인트를 찾는다
   - POST/PUT/DELETE/PATCH 요청을 처리하는 라우트
   - 사용자 정보 변경 (비밀번호, 이메일, 프로필)
   - 권한/역할 변경
   - 결제/주문/취소 처리
   - 설정 변경
   - 데이터 생성/수정/삭제
   - GET 요청으로 상태를 변경하는 엔드포인트 (SameSite=Lax 우회 가능)

3. **CSRF 방어 메커니즘 확인**: 각 엔드포인트에 대해
   - CSRF 토큰 검증 미들웨어/필터 적용 여부
   - 세션 쿠키의 SameSite 속성 설정
   - Origin/Referer 검증 로직
   - 커스텀 헤더 요구 여부
   - API가 쿠키 기반 인증인지 토큰 기반 인증인지 (Bearer 토큰 인증은 CSRF에 면역)

4. **인증 방식 확인**: CSRF는 쿠키 기반 인증에서만 의미가 있다
   - **쿠키 기반 세션**: CSRF 취약 가능 (브라우저가 자동으로 쿠키 첨부)
   - **Authorization 헤더 (Bearer 토큰)**: CSRF 면역 (브라우저가 자동으로 헤더 첨부하지 않음)
   - **혼합**: 일부 엔드포인트만 쿠키 사용하는 경우 해당 엔드포인트만 대상

5. **후보 목록 작성**: CSRF 방어가 누락된 상태 변경 엔드포인트를 정리. Bearer 토큰만 사용하는 API는 후보에서 제외.

## 후보 판정 제한

쿠키만으로 인증이 완료되는 엔드포인트만 후보. 커스텀 헤더 기반 인증은 CSRF 면역이므로 제외.
