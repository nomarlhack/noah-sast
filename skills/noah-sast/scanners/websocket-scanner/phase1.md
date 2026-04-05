> **호출부 추적 — 실제 URL 경로 확정**: 모든 후보에 대해 라우트 정의 파일을 Read로 읽어 실제 URL 경로를 확정한다. 컴포넌트/파일 이름에서 경로를 유추하는 것은 확정이 아니다. 절차: (1) Sink의 호출부를 Grep → 최종 페이지 컴포넌트/컨트롤러 식별 (2) 라우트 정의(routes/index.tsx, @RequestMapping 등)를 Read로 읽어 경로 문자열 확인 (3) 후보 반환 시 근거 포함: `실제 경로: /home/apply (src/routes/index.tsx:42)`

### Phase 1: 정찰 (소스코드 분석)

WebSocket 엔드포인트, 핸드셰이크, 메시지 처리 로직을 추적하여 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: WebSocket 라이브러리/프레임워크 확인
   - **Node.js**: `ws`, `socket.io`, `express-ws`, `uWebSockets.js`, `@nestjs/websockets`
   - **Python**: `websockets`, `channels` (Django), `Flask-SocketIO`, `FastAPI WebSocket`
   - **Java**: `javax.websocket`, `Spring WebSocket`, `Netty`
   - **Go**: `gorilla/websocket`, `nhooyr.io/websocket`
   - **Ruby**: `ActionCable` (Rails), `faye-websocket`
   - **프론트엔드**: `new WebSocket()`, `socket.io-client`, `SockJS`

2. **WebSocket 엔드포인트 식별**:
   - 서버에서 WebSocket 엔드포인트를 등록하는 코드 (`ws://`, `wss://` 경로)
   - `upgrade` 핸들러, WebSocket 라우트 설정
   - Socket.IO의 `io.on('connection')`, `io.of('/namespace')`
   - 클라이언트 코드에서 `new WebSocket(url)`, `io.connect(url)` 호출

3. **핸드셰이크 검증 분석**:

   **Origin 검증:**
   - 핸드셰이크 시 `Origin` 헤더를 확인하는 코드가 있는지
   - Socket.IO의 `cors` 설정, `allowedOrigins` 설정
   - `ws` 라이브러리의 `verifyClient` 콜백
   - Origin 검증이 없으면 CSWSH 후보

   **인증 검증:**
   - 핸드셰이크 시 쿠키, 토큰, API 키 등 인증 정보를 확인하는 코드
   - `upgrade` 이벤트에서 세션/토큰 검증
   - Socket.IO의 `io.use()` 미들웨어에서 인증 처리
   - 연결 후 첫 메시지에서 인증하는 패턴 (핸드셰이크 시 인증 없이 연결 가능)

4. **메시지 처리 분석**:

   **입력 검증:**
   - 수신 메시지의 형식/내용을 검증하는 코드
   - JSON 파싱 후 필드 검증, 타입 검사
   - 메시지 내용이 HTML에 삽입되는 경우 (XSS 경로)
   - 메시지 내용이 SQL/NoSQL 쿼리에 삽입되는 경우 (Injection 경로)
   - 메시지 내용이 시스템 명령에 삽입되는 경우

   **인가 검증:**
   - 메시지 유형별/채널별 권한 검사
   - 다른 사용자의 데이터에 접근하는 메시지를 처리할 때 소유권 확인
   - 관리자 전용 메시지 유형에 대한 권한 검사

   **브로드캐스트:**
   - 수신 메시지를 다른 연결된 클라이언트에게 전달하는 코드
   - 전달 전 sanitization 여부
   - `io.emit()`, `socket.broadcast.emit()`, `ws.clients.forEach()`

5. **후보 목록 작성**: 각 후보에 대해 "어떻게 악용할 수 있는지"를 구체적으로 구상. 데이터 흐름 추적을 완료한 뒤에도 공격 경로가 없으면 버린다. 추적 없이 직관으로 버리지 않는다..

## 후보 판정 제한

WebSocket 연결을 직접 생성/관리하는 코드가 있는 경우만 분석.
