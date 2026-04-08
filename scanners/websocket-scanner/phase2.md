### Phase 2: 동적 테스트 (검증)


**CSWSH (Cross-Site WebSocket Hijacking) 테스트:**
```bash
# 1. 다른 Origin으로 WebSocket 핸드셰이크 시도
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  -H "Origin: https://evil.com" \
  -H "Cookie: session=VICTIM_SESSION_COOKIE" \
  "https://target.com/ws"

# 101 Switching Protocols 응답이 오면 Origin 검증 없음 확인
# 403 또는 연결 거부면 Origin 검증 존재

# 2. Socket.IO의 경우 polling transport로 확인
curl -s "https://target.com/socket.io/?EIO=4&transport=polling" \
  -H "Origin: https://evil.com" \
  -H "Cookie: session=VICTIM_SESSION_COOKIE"
```

**인증 미흡 테스트:**
```bash
# 인증 정보 없이 WebSocket 핸드셰이크 시도
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  "https://target.com/ws"

# 101 응답이 오면 인증 없이 연결 가능

# websocat 사용 가능 시 (사용자에게 설치 여부 확인)
# websocat wss://target.com/ws
# → 연결 성공 후 메시지 송수신 테스트
```

**메시지 인젝션 테스트:**
```bash
# websocat 또는 wscat 사용 가능 시
# 연결 후 조작된 메시지 전송
# wscat -c "wss://target.com/ws" -H "Cookie: session=..."
# > {"type": "chat", "message": "<img src=x onerror=alert(1)>"}
# > {"type": "admin_action", "action": "delete_user", "userId": "123"}

# curl로는 WebSocket 메시지 송수신이 불가하므로,
# 핸드셰이크까지만 확인하고 메시지 테스트는 브라우저/도구 필요로 보고
```

**인가 우회 테스트:**
```bash
# 일반 사용자 세션으로 관리자 채널/네임스페이스 접근 시도
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  -H "Cookie: session=NORMAL_USER_SESSION" \
  "https://target.com/ws/admin"

# Socket.IO 네임스페이스 접근
curl -s "https://target.com/socket.io/?EIO=4&transport=polling&nsp=/admin" \
  -H "Cookie: session=NORMAL_USER_SESSION"
```

**검증 기준:**
- **확인됨**: 동적 테스트로 Origin 검증 우회, 인증 없는 연결, 인가 없는 데이터 접근 등을 직접 확인함
- **후보**: 소스코드상 취약 패턴이 존재하지만 동적 테스트로 확인하지 못함 (WebSocket 클라이언트 도구 미설치, 메시지 레벨 테스트 불가 등)
- **보고서 제외**: 동적 테스트 결과 Origin 검증, 인증, 인가가 정상 동작하는 것을 확인한 경우
