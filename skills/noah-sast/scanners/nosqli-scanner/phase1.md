> **호출부 추적 — 실제 URL 경로 확정**: 모든 후보에 대해 라우트 정의 파일을 Read로 읽어 실제 URL 경로를 확정한다. 컴포넌트/파일 이름에서 경로를 유추하는 것은 확정이 아니다. 절차: (1) Sink의 호출부를 Grep → 최종 페이지 컴포넌트/컨트롤러 식별 (2) 라우트 정의(routes/index.tsx, @RequestMapping 등)를 Read로 읽어 경로 문자열 확인 (3) 후보 반환 시 근거 포함: `실제 경로: /home/apply (src/routes/index.tsx:42)`

### Phase 1: 정찰 (소스코드 분석)

사용자 입력 → NoSQL 쿼리 경로를 추적하여 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: NoSQL 데이터베이스/드라이버/ODM 확인
   - **MongoDB**: `mongodb` (native driver), `mongoose` (ODM)
   - **Redis**: `redis`, `ioredis`
   - **CouchDB**: `nano`, `pouchdb`
   - **DynamoDB**: `aws-sdk`, `@aws-sdk/client-dynamodb`
   - **Firestore**: `firebase-admin`, `@google-cloud/firestore`

2. **Source 식별**: 사용자가 제어 가능한 입력 중 NoSQL 쿼리에 사용될 수 있는 것
   - HTTP 요청 본문 (JSON) — `req.body.username`, `req.body.password` 등
   - HTTP 쿼리 파라미터 — `req.query.filter`, `req.query.sort` 등
   - URL 경로 파라미터 — `req.params.id`

3. **Sink 식별**: NoSQL 쿼리를 실행하는 코드

   **MongoDB Native Driver:**
   - `collection.find(query)` — query에 사용자 입력이 직접 삽입되면 위험
   - `collection.findOne(query)`
   - `collection.updateOne(query, update)`
   - `collection.deleteOne(query)`
   - `collection.aggregate(pipeline)` — pipeline에 사용자 입력 삽입 시 위험

   **Mongoose:**
   - `Model.find(query)` — query에 사용자 입력이 객체로 전달되면 위험
   - `Model.findOne(query)`
   - `Model.findById(id)` — id가 문자열이면 안전, 객체면 위험
   - `Model.where(field).equals(value)` — 체이닝은 상대적으로 안전
   - `Model.find({ $where: userInput })` — JavaScript 실행, 매우 위험

   **Redis:**
   - `client.eval(script)` — Lua 스크립트에 사용자 입력 삽입 시 위험
   - 키 이름에 사용자 입력이 사용되는 경우 (키 추측/조작)

4. **핵심 취약 패턴 확인**:

   **패턴 1: 요청 본문을 쿼리에 직접 전달**
   ```javascript
   // 위험: req.body가 {"password": {"$ne": ""}} 이면 패스워드 우회
   db.users.findOne({ username: req.body.username, password: req.body.password })
   ```

   **패턴 2: 쿼리 파라미터를 필터로 사용**
   ```javascript
   // 위험: req.query.filter가 {"role": {"$ne": "user"}} 이면 admin 조회
   db.users.find(req.query.filter)
   ```

   **패턴 3: $where에 사용자 입력**
   ```javascript
   // 위험: JavaScript 코드 실행
   db.users.find({ $where: `this.username == '${userInput}'` })
   ```

   **안전한 패턴:**
   ```javascript
   // 안전: 문자열로 명시적 캐스팅
   db.users.findOne({ username: String(req.body.username), password: String(req.body.password) })

   // 안전: mongo-sanitize 사용
   const sanitize = require('mongo-sanitize');
   db.users.findOne({ username: sanitize(req.body.username) })

   // 안전: Mongoose Schema validation으로 타입 강제
   ```

5. **Express 미들웨어/파서 확인**:
   - `express.json()` 또는 `body-parser`가 사용되면 `req.body`에 객체가 들어올 수 있음 (Operator Injection 가능)
   - `qs` 라이브러리의 `allowDots: true` 또는 depth 설정에 따라 쿼리 파라미터에서도 객체 생성 가능
   - `express.urlencoded({ extended: true })` — `qs` 사용, 중첩 객체 가능

6. **후보 목록 작성**: 각 후보에 대해 "어떤 입력으로 어떻게 쿼리 로직을 변경할 수 있는지"를 구체적으로 구상. 데이터 흐름 추적을 완료한 뒤에도 공격 경로가 없으면 버린다. 추적 없이 직관으로 버리지 않는다..

## 후보 판정 제한

사용자 입력이 쿼리 연산자 위치에 삽입되는 경우만 후보. 프레임워크 방어 적용 시 제외.
