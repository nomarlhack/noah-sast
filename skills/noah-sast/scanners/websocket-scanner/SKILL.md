---
grep_patterns:
  - "new WebSocket("
  - "socket\\.io"
  - "WebSocket"
  - "ActionCable"
  - "io\\.on('connection'"
  - "io\\.of("
  - "verifyClient"
  - "allowedOrigins"
  - "wss://"
  - "ws://"
  - "express-ws"
  - "gorilla/websocket"
---

# WebSocket Scanner

소스코드 분석으로 WebSocket 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 인증 우회, 메시지 인젝션, 데이터 탈취 등이 가능한지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "악용할 수 없으면 취약점이 아니다"

WebSocket에 Origin 검증이 없다고 바로 취약점으로 보고하지 않는다. 실제로 공격자가 Origin 검증 부재를 이용하여 피해자의 WebSocket 연결을 하이재킹하거나, 인증 없이 민감한 데이터를 조회/조작할 수 있는 것을 확인해야 취약점이다.

## WebSocket 취약점의 유형

### Cross-Site WebSocket Hijacking (CSWSH)
WebSocket 핸드셰이크 시 Origin 헤더를 검증하지 않아, 악성 웹페이지에서 피해자의 브라우저를 통해 WebSocket 연결을 수립하고 메시지를 송수신할 수 있는 취약점. CSRF의 WebSocket 버전이다.

### 인증/인가 미흡
WebSocket 연결 수립 시 또는 메시지 처리 시 인증/인가 검증이 누락되어, 인증 없이 연결하거나 권한 밖의 데이터에 접근할 수 있는 취약점.

### 메시지 인젝션
WebSocket 메시지의 내용이 검증 없이 처리되어, 다른 사용자에게 전달(브로드캐스트)되거나 서버사이드에서 위험한 작업을 유발하는 취약점. XSS, SQL Injection 등 다른 취약점의 진입점이 될 수 있다.

### 정보 노출
WebSocket을 통해 민감한 정보(다른 사용자의 데이터, 내부 시스템 정보 등)가 인가 없이 노출되는 취약점.

### Rate Limiting / DoS
WebSocket 연결 수 제한이나 메시지 속도 제한이 없어 서버 리소스를 고갈시킬 수 있는 경우. 단, 이는 소스코드 분석으로만 확인하고 실제 DoS 테스트는 수행하지 않는다.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

