---
name: nosqli-scanner
description: "소스코드 분석과 동적 테스트를 통해 NoSQL Injection 취약점을 탐지하는 스킬. 사용자 입력이 NoSQL 쿼리에 반영되는 경로를 추적하고, 실제로 쿼리 로직을 변경하여 인증 우회나 데이터 유출이 가능한지 검증한다. 사용자가 'NoSQL injection 찾아줘', 'NoSQLi 스캔', 'MongoDB injection', 'NoSQL 인젝션 점검', 'nosqli audit', 'operator injection' 등을 요청할 때 이 스킬을 사용한다."
grep_patterns:
  - "collection\\.find("
  - "collection\\.findOne("
  - "Model\\.find("
  - "Model\\.findOne("
  - "\\$where"
  - "\\$regex"
  - "\\$ne"
  - "\\$gt"
  - "collection\\.aggregate("
  - "client\\.eval("
  - "mongoose"
  - "mongodb"
---

# NoSQL Injection Scanner

소스코드 분석으로 NoSQL Injection 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 쿼리 로직을 변경하여 인증 우회나 데이터 유출이 가능한지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "쿼리 로직이 변경되지 않으면 취약점이 아니다"

소스코드에서 `db.collection.find(userInput)`이 있다고 바로 NoSQL Injection으로 보고하지 않는다. 실제로 사용자가 제어한 입력으로 쿼리 연산자(`$gt`, `$ne`, `$regex` 등)를 삽입하여 쿼리 로직을 변경할 수 있는 것을 확인해야 취약점이다.

## SQL Injection과의 차이

NoSQL Injection은 SQL Injection과 메커니즘이 다르다:
- SQL Injection: 문자열 연결로 SQL 구문을 삽입
- NoSQL Injection: **객체/연산자 삽입**으로 쿼리 로직을 변경. JSON 객체로 `$gt`, `$ne` 등 연산자를 삽입하거나, JavaScript 코드를 실행(`$where`)

## NoSQL Injection의 유형

### Operator Injection
사용자 입력을 통해 MongoDB 쿼리 연산자(`$gt`, `$ne`, `$regex`, `$in`, `$exists` 등)를 삽입하여 쿼리 조건을 변경하는 공격. 가장 흔한 NoSQL Injection 형태.

```
# 정상 쿼리
db.users.find({ username: "admin", password: "secret" })

# 공격: password에 {"$ne": ""} 삽입 → 빈 문자열이 아닌 모든 패스워드 매칭
db.users.find({ username: "admin", password: {"$ne": ""} })
```

### JavaScript Injection ($where / $function)
MongoDB의 `$where` 연산자나 `$function`에 JavaScript 코드를 삽입하여 서버에서 실행하는 공격.

### Aggregation Pipeline Injection
`$lookup`, `$match`, `$group` 등 Aggregation Pipeline 단계에 사용자 입력이 삽입되어 의도하지 않은 데이터를 조회하는 공격.

### NoSQL Blind Injection
쿼리 결과가 직접 반환되지 않지만, 응답 차이(Boolean 기반)나 시간 차이(Time 기반)로 데이터를 추론하는 공격. `$regex`를 활용한 문자별 추출이 대표적.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 `../../agent-guidelines.md` (이 파일 기준 상대 경로)를 참조한다.
