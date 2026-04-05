---
name: jwt-scanner
description: "소스코드 분석과 동적 테스트를 통해 JWT(JSON Web Token) 변조 취약점을 탐지하는 스킬. JWT 서명 검증 로직, 알고리즘 처리, 키 관리를 분석하고, 실제로 토큰을 변조하여 인증/인가를 우회할 수 있는지 검증한다. 사용자가 'JWT 취약점 찾아줘', 'JWT 스캔', 'JWT 변조', 'JWT 검증 우회', 'JWT audit', 'none algorithm', 'JWT 점검' 등을 요청할 때 이 스킬을 사용한다."
grep_patterns:
  - "jwt\\.verify("
  - "jwt\\.decode("
  - "jwt\\.sign("
  - "JWT\\.decode("
  - "JWT\\.encode("
  - "jsonwebtoken"
  - "express-jwt"
  - "passport-jwt"
  - "PyJWT"
  - "python-jose"
  - "ruby-jwt"
  - "firebase/php-jwt"
  - "ignoreExpiration"
  - "algorithms.*none"
  - "bearer"
  - "ExpiredJwtException"
  - "ExpiredSignatureError"
  - "TokenExpiredError"
  - "ExpiredSignature"
  - "parseClaimsJwt"
  - "verify_signature.*false"
---

# JWT Scanner

소스코드 분석으로 JWT 처리 로직의 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 변조된 토큰이 서버에서 수락되는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "변조된 토큰이 수락되지 않으면 취약점이 아니다"

소스코드에서 JWT 라이브러리를 사용한다고 바로 취약점으로 보고하지 않는다. 실제로 토큰의 페이로드를 변조하거나 서명을 조작한 토큰을 서버에 전송했을 때, 서버가 이를 유효한 토큰으로 수락하여 인증/인가가 우회되는 것을 확인해야 취약점이다.

## JWT 변조 취약점의 유형

### Algorithm None Attack
JWT 헤더의 `alg` 필드를 `none`으로 변경하고 서명을 제거하면, 서명 검증을 건너뛰는 라이브러리가 있다. 이를 통해 페이로드를 자유롭게 변조할 수 있다.

### Algorithm Confusion (RS256 → HS256)
서버가 RS256(비대칭)을 사용하는 경우, 공격자가 `alg`을 HS256(대칭)으로 변경하고 공개키로 서명하면 서버가 공개키를 대칭키로 사용하여 서명을 검증할 수 있다.

### Weak Secret Key
HS256 등 대칭 알고리즘에서 약한 시크릿 키(짧은 문자열, 기본값, 추측 가능한 값)를 사용하면 브루트포스로 키를 알아내어 토큰을 위조할 수 있다.

### Missing Signature Verification
서명 검증 로직이 누락되어 서명이 잘못된 토큰도 수락하는 경우.

### JWT Header Injection (jwk/jku/kid)
JWT 헤더의 `jwk`(공개키 직접 포함), `jku`(공개키 URL), `kid`(키 식별자) 필드를 조작하여 공격자가 제어하는 키로 서명을 검증하도록 유도하는 경우.

### Expired Token Acceptance
만료된 토큰(`exp` 클레임 경과)이 수락되는 경우.

### Expired Token Claim Reuse
만료 예외를 catch한 뒤, 예외 객체에서 클레임을 추출하여 인증/인가에 재사용하는 경우. 만료 후에도 클레임 기반으로 권한을 부여하면 토큰 탈취 시 만료와 무관하게 악용이 가능하다.

### Unsigned JWT Parsing
서명이 포함된 JWS가 아닌 서명이 없는 JWT(Unsecured JWT)를 파싱하는 메서드를 사용하는 경우. 공격자가 서명 없이 임의 페이로드를 구성한 토큰을 전송하면 서버가 그대로 수락한다.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 `~/.claude/skills/noah-sast/agent-guidelines.md`를 참조한다.
