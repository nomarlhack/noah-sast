---
name: http-method-tampering-scanner
description: "소스코드 분석과 동적 테스트를 통해 HTTP Method Tampering 취약점을 탐지하는 스킬. HTTP 메서드를 변경하여 인증/인가 로직을 우회할 수 있는지 분석하고 검증한다. 사용자가 'HTTP method tampering', 'HTTP 메서드 변조', 'HTTP verb tampering', '메서드 우회', 'HTTP method override 취약점', 'PUT/DELETE 메서드 허용 여부' 등을 요청할 때 이 스킬을 사용한다."
grep_patterns:
  - "method-override"
  - "X-HTTP-Method-Override"
  - "X-Method-Override"
  - "_method"
  - "app\\.all("
  - "Rack::MethodOverride"
  - "limit_except"
  - "<Limit"
  - "<LimitExcept"
  - "http_method_names"
---

# HTTP Method Tampering Scanner

소스코드 분석으로 HTTP 메서드 변조를 통해 인증/인가를 우회할 수 있는 후보를 식별한 뒤, 동적 테스트로 실제로 우회가 가능한지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "우회되지 않으면 취약점이 아니다"

HTTP 메서드를 변경했을 때 인증이나 인가가 실제로 우회되어 보호된 리소스에 접근하거나 상태를 변경할 수 있는 것을 확인해야 취약점이다. 단순히 405(Method Not Allowed)가 아닌 200을 받았다는 것만으로는 취약점이 아니다. 보호된 기능이 실제로 동작해야 한다.

## HTTP Method Tampering의 유형

### 인증 우회 (Authentication Bypass)
특정 HTTP 메서드에만 인증 검사가 적용되어, 다른 메서드로 요청하면 인증 없이 접근 가능한 경우.
- 예: POST에만 인증 미들웨어 적용 → HEAD/PUT으로 같은 엔드포인트 접근 시 인증 우회
- 예: `.htaccess`에서 `<LimitExcept GET POST>` 설정 → PUT으로 우회

### 인가 우회 (Authorization Bypass)
특정 HTTP 메서드에만 권한 검사가 적용되어, 다른 메서드로 요청하면 권한 없이 접근 가능한 경우.
- 예: DELETE 요청에만 관리자 권한 검사 → PATCH로 같은 리소스 삭제 가능

### Method Override를 통한 우회
`X-HTTP-Method-Override`, `X-Method-Override`, `_method` 파라미터 등을 사용하여 실제 HTTP 메서드를 변경하는 경우. WAF나 프록시가 GET/POST만 검사할 때 Override 헤더로 DELETE/PUT을 실행.

### 불필요한 메서드 허용
TRACE, OPTIONS, CONNECT 등 불필요한 HTTP 메서드가 허용되어 정보 노출이나 추가 공격이 가능한 경우.
- TRACE: 요청 헤더가 그대로 반환 → 쿠키/인증 헤더 탈취 (Cross-Site Tracing)
- OPTIONS: 서버 설정 정보 노출

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 `~/.claude/skills/noah-sast/agent-guidelines.md`를 참조한다.
