### Phase 2: 동적 테스트 (검증)

> 공통 시작 절차 / 공통 검증 기준은 `prompts/guidelines-phase2.md` 지침 7에 정의되어 있다. 이 파일은 validation-logic 스캐너의 고유 절차만 다룬다.

**도구 선택:** API 검증 테스트이므로 **curl만 사용**한다. Playwright는 사용하지 않는다.

---

## 기본 원칙

- 모든 테스트는 **서버 응답 동작**으로 판정한다. 소스코드에서 검증이 누락된 것처럼 보여도 서버가 올바르게 거부하면 **보고서 제외**.
- **쓰기 작업 안전 수칙**: 상태 변경 API 테스트 시, 테스트 데이터만 사용하고 기존 데이터를 변경하지 않는다. 가능하면 먼저 테스트용 리소스를 생성한 후 해당 리소스로 테스트한다.
- 각 라벨의 Phase 1 후보별로 개별 테스트를 수행한다. 하나의 테스트로 여러 후보를 일괄 판정하지 않는다.
- **비교 기준 수립 필수**: 각 테스트 전에 정상 요청의 응답을 먼저 캡처하여 비교 기준으로 사용한다.

---

## Test 1: VALIDATION_MISMATCH — 클라이언트 검증 우회

Phase 1에서 "클라이언트에만 검증 존재 + 서버 검증 누락"으로 판정된 후보를 테스트한다.

### 절차

1. **정상 요청 캡처**: 클라이언트 검증 규칙에 부합하는 정상 데이터로 요청을 보낸다.
```bash
curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "https://<host>/api/<endpoint>" \
  -H "Content-Type: application/json" \
  -H "Cookie: <session>" \
  -d '{"email":"valid@example.com","age":25,"name":"TestUser"}'
```

2. **검증 규칙 위반 요청**: 클라이언트 검증 규칙을 의도적으로 위반한 데이터를 직접 API로 전송한다.
```bash
# 형식 위반 (이메일 형식 없이)
curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "https://<host>/api/<endpoint>" \
  -H "Content-Type: application/json" \
  -H "Cookie: <session>" \
  -d '{"email":"not-an-email","age":25,"name":"TestUser"}'

# 범위 위반 (음수 나이)
curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "https://<host>/api/<endpoint>" \
  -H "Content-Type: application/json" \
  -H "Cookie: <session>" \
  -d '{"email":"valid@example.com","age":-1,"name":"TestUser"}'

# 길이 위반 (빈 문자열 / 극단적 길이)
curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "https://<host>/api/<endpoint>" \
  -H "Content-Type: application/json" \
  -H "Cookie: <session>" \
  -d '{"email":"valid@example.com","age":25,"name":""}'
```

### 검증 기준

| 응답 | 판정 |
|------|------|
| 200/201 + 데이터 저장 성공 (검증 규칙 위반 데이터가 수용됨) | 확인됨 |
| 400/422 + 검증 에러 메시지 | 안전 (서버 검증 동작) |
| 500 에러 (검증 없이 DB 제약조건에서 실패) | 확인됨 (서버 검증 누락, DB에 의존) |

---

## Test 2: TYPE_CONFUSION — 타입 혼동 테스트

Phase 1에서 loose comparison 또는 타입 미검증으로 판정된 후보를 테스트한다.

### 절차

1. **기대 타입과 다른 타입 전송**: 서버가 기대하는 타입과 다른 타입을 전송하여 동작 변화를 관찰한다.

```bash
# 문자열 → 배열 (NoSQLi와 겹치면 nosqli-scanner에 위임)
curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "https://<host>/api/<endpoint>" \
  -H "Content-Type: application/json" \
  -H "Cookie: <session>" \
  -d '{"username":["admin"],"password":"test"}'

# 문자열 → 숫자
curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "https://<host>/api/<endpoint>" \
  -H "Content-Type: application/json" \
  -H "Cookie: <session>" \
  -d '{"username":0,"password":"test"}'

# 문자열 → boolean
curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "https://<host>/api/<endpoint>" \
  -H "Content-Type: application/json" \
  -H "Cookie: <session>" \
  -d '{"username":true,"password":"test"}'

# 숫자 → 문자열 (숫자 필드에 문자열)
curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "https://<host>/api/<endpoint>" \
  -H "Content-Type: application/json" \
  -H "Cookie: <session>" \
  -d '{"quantity":"1abc","product_id":123}'
```

2. **타입 강제 변환 악용**: 특정 언어의 타입 강제 변환 특성을 이용한 테스트.

```bash
# 빈 문자열 (falsy in JS — 인증/권한 검사 우회 시도)
curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "https://<host>/api/<endpoint>" \
  -H "Content-Type: application/json" \
  -H "Cookie: <session>" \
  -d '{"token":"","admin":""}'

# 숫자 0 (falsy in JS — 검증 우회 시도)
curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "https://<host>/api/<endpoint>" \
  -H "Content-Type: application/json" \
  -H "Cookie: <session>" \
  -d '{"count":0,"verified":0}'
```

### 검증 기준

| 응답 | 판정 |
|------|------|
| 200 + 예상과 다른 동작 (인증 우회, 권한 변경, 데이터 변조) | 확인됨 |
| 200 + 입력이 그대로 처리됨 (의도치 않은 형변환) | 확인됨 |
| 400/422 + 타입 에러 메시지 ("expected string, got array" 등) | 안전 |
| 500 + 타입 에러 스택트레이스 | 확인됨 (미처리 타입 에러 — 서비스 장애 유발 가능) |

---

## Test 3: NULL_SAFETY — Null/Undefined 처리 테스트

Phase 1에서 null 참조 또는 결함 있는 null 검사로 판정된 후보를 테스트한다.

### 절차

```bash
# null 값 전송
curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "https://<host>/api/<endpoint>" \
  -H "Content-Type: application/json" \
  -H "Cookie: <session>" \
  -d '{"username":null,"role":null}'

# 필드 자체를 누락
curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "https://<host>/api/<endpoint>" \
  -H "Content-Type: application/json" \
  -H "Cookie: <session>" \
  -d '{}'

# 필수 필드 일부만 제공
curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "https://<host>/api/<endpoint>" \
  -H "Content-Type: application/json" \
  -H "Cookie: <session>" \
  -d '{"username":"admin"}'

# 중첩 객체를 null로
curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "https://<host>/api/<endpoint>" \
  -H "Content-Type: application/json" \
  -H "Cookie: <session>" \
  -d '{"user":null,"settings":null}'
```

### 검증 기준

| 응답 | 판정 |
|------|------|
| 200 + null이 기본 권한/역할로 대체되어 의도치 않은 접근 허용 | 확인됨 |
| 200 + 필수 필드 null인 채로 데이터 저장 | 확인됨 |
| 500 + NullPointerException / TypeError 스택트레이스 | 확인됨 (미처리 null — 서비스 장애 유발) |
| 400/422 + "field is required" / "must not be null" | 안전 |
| 500 + 일반 에러 (스택트레이스 없음) | 후보 (서버 에러지만 상세 확인 불가) |

---

## Test 4: SCHEMA_DEFECT — 스키마 검증 결함 테스트

Phase 1에서 스키마에 미정의 필드 수용 가능성이 판정된 후보를 테스트한다.

### 절차

1. **미정의 필드 주입**: API 스키마에 정의되지 않은 필드를 요청에 포함한다.

```bash
# 일반적인 미정의 필드 주입
curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "https://<host>/api/<endpoint>" \
  -H "Content-Type: application/json" \
  -H "Cookie: <session>" \
  -d '{"name":"test","email":"test@test.com","role":"admin","isAdmin":true,"__internal_flag":true}'

# 중첩 객체에 미정의 필드
curl -s -w "\nHTTP_CODE:%{http_code}" -X PUT "https://<host>/api/<endpoint>/<id>" \
  -H "Content-Type: application/json" \
  -H "Cookie: <session>" \
  -d '{"profile":{"name":"test","verified":true,"admin_override":true}}'
```

2. **필수 필드 누락 테스트**: 필수로 표시된 필드를 의도적으로 누락한다.

```bash
# 필수 필드 누락
curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "https://<host>/api/<endpoint>" \
  -H "Content-Type: application/json" \
  -H "Cookie: <session>" \
  -d '{"optional_field":"value"}'
```

3. **Content-Type 불일치**: 서버가 기대하는 것과 다른 Content-Type으로 요청한다.

```bash
# JSON 엔드포인트에 form-urlencoded
curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "https://<host>/api/<endpoint>" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Cookie: <session>" \
  -d 'name=test&role=admin&isAdmin=true'
```

### 검증 기준

| 응답 | 판정 |
|------|------|
| 200/201 + 미정의 필드가 저장/반영됨 (응답에 `role`/`isAdmin` 포함) | 확인됨 |
| 200/201 + 미정의 필드가 무시됨 (응답에 미포함) | 안전 (서버가 무시) |
| 200/201 + 필수 필드 누락인데 기본값으로 저장됨 | 확인됨 (기본값이 보안상 위험한 경우) |
| 400/422 + "additional properties not allowed" / "unknown field" | 안전 |
| 400/422 + "field is required" | 안전 |
| form-urlencoded로 보낸 요청이 JSON과 동일하게 처리됨 | 확인됨 (Content-Type 검증 누락) |
| 415 Unsupported Media Type | 안전 |

---

## 유의사항

- **Mass assignment 경계**: `role`, `isAdmin`, `admin` 등 권한 관련 필드가 주입되어 실제 권한이 변경되면, 본 스캐너에서 SCHEMA_DEFECT로 보고하되 `business-logic-scanner`(PRIV_ESCALATION) 또는 `idor-scanner`(MASS_ASSIGNMENT)와 중복 가능성을 보고서에 명시한다.
- **NoSQLi 경계**: 배열/객체 주입 시 MongoDB 쿼리 연산자(`$gt`, `$ne`, `$regex`)가 포함된 응답이 관찰되면, TYPE_CONFUSION이 아닌 `nosqli-scanner` 영역임을 명시한다.
- **비파괴적 테스트 원칙**: 상태 변경 API 테스트 시 기존 데이터를 변경하지 않는다. 가능하면 테스트 전용 리소스를 생성하고, 그 리소스에 대해 테스트한다.
- **정상 동작 비교 필수**: 모든 테스트에서 비정상 입력의 응답을 정상 입력의 응답과 비교한다. 서버가 모든 요청에 200을 반환하는 경우(API 설계상), 응답 본문의 내용을 기준으로 판정한다.
