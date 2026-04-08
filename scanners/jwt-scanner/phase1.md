> ## 핵심 원칙: "변조된 토큰이 수락되지 않으면 취약점이 아니다"
>
> 소스코드에서 JWT 라이브러리를 사용한다고 바로 취약점으로 보고하지 않는다. 실제로 토큰의 페이로드를 변조하거나 서명을 조작한 토큰을 서버에 전송했을 때, 서버가 이를 유효한 토큰으로 수락하여 인증/인가가 우회되는 것을 확인해야 취약점이다.
>

### Phase 1: 정찰 (소스코드 분석)

JWT 생성/검증 로직을 분석하여 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: JWT 라이브러리 확인

   **Node.js:**
   - `jsonwebtoken` — `jwt.verify()` 옵션 확인 (`algorithms` 지정 여부)
   - `jose` — 모던 라이브러리, 기본적으로 안전
   - `express-jwt` / `koa-jwt` — 미들웨어 설정 확인
   - `passport-jwt` — Strategy 설정 확인

   **Python:**
   - `PyJWT` (`jwt.decode()`) — `algorithms` 파라미터 지정 여부, `options` 설정
   - `python-jose` — 알고리즘 설정 확인
   - `authlib` — JWT 설정 확인

   **Java:**
   - `jjwt` (io.jsonwebtoken) — `parserBuilder().setSigningKey()` 설정
   - `nimbus-jose-jwt` — `JWSVerifier` 설정
   - `auth0/java-jwt` — `JWT.require(algorithm)` 설정
   - Spring Security OAuth2 — `JwtDecoder` 설정

   **Ruby:**
   - `ruby-jwt` — `JWT.decode()` 옵션 확인

   **PHP:**
   - `firebase/php-jwt` — `JWT::decode()` 알고리즘 파라미터

2. **JWT 검증 로직 분석**: 다음을 점검

   **알고리즘 처리:**
   - `verify()` / `decode()` 호출 시 `algorithms` 파라미터를 명시적으로 지정하는지
   - `algorithms`를 지정하지 않으면 토큰 헤더의 `alg`을 그대로 신뢰 — Algorithm None/Confusion 가능
   - `none` 알고리즘이 허용되는지

   **서명 검증:**
   - `verify` 옵션이 `false`로 설정되어 있지 않은지 (`jwt.decode(token, {complete: true})` 등 서명 미검증)
   - `ignoreExpiration: true` 설정 여부
   - 서명을 검증하는 파싱 메서드와 검증하지 않는 파싱 메서드가 혼동되어 사용되는지

   **만료 토큰 클레임 재사용:**
   - 만료 예외를 catch한 뒤 예외 객체에서 클레임을 추출하여 인증/인가에 사용하는지
     - 취약: catch 블록 내에서 추출한 클레임으로 권한을 부여하거나 인증을 통과시키는 경우
     - 안전: 추출한 클레임을 로깅 목적으로만 사용하거나, 재인증을 강제하는 경우

   **키 관리:**
   - 시크릿 키가 소스코드에 하드코딩되어 있는지
   - 시크릿 키가 환경변수에서 로드되는지 (안전)
   - 시크릿 키가 약한 값(`secret`, `password`, `key123` 등)인지
   - RSA 공개키가 노출되어 있는지 (Algorithm Confusion 공격에 활용 가능)

   **헤더 클레임 처리:**
   - `jwk`, `jku`, `kid` 헤더를 처리하는 로직이 있는지
   - `jku` URL에 대한 화이트리스트 검증이 있는지
   - `kid`가 파일 경로나 SQL 쿼리에 사용되는지 (Path Traversal, SQLi 벡터)

   **페이로드 검증:**
   - `exp` (만료시간) 검증 여부
   - `iss` (발급자) 검증 여부
   - `aud` (대상자) 검증 여부
   - `sub` (주체) 기반 권한 확인 로직

3. **후보 목록 작성**: 각 후보에 대해 "어떻게 토큰을 변조하면 인증/인가를 우회할 수 있는지"를 구체적으로 구상. 데이터 흐름 추적을 완료한 뒤에도 공격 경로가 없으면 버린다. 추적 없이 직관으로 버리지 않는다..
