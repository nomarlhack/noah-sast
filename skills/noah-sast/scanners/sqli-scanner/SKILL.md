---
grep_patterns:
  - "connection\\.query("
  - "sequelize\\.query("
  - "knex\\.raw("
  - "\\$queryRaw"
  - "\\$queryRawUnsafe("
  - "pool\\.query("
  - "cursor\\.execute("
  - "Model\\.objects\\.raw("
  - "Model\\.objects\\.extra("
  - "session\\.execute("
  - "find_by_sql"
  - "connection\\.execute"
  - "db\\.run("
  - "db\\.query("
  - "prepareStatement"
  - "createNativeQuery"
  - "nativeQuery"
  - "jdbcTemplate"
  - "NamedParameterJdbcTemplate"
---

# SQL Injection Scanner

소스코드 분석으로 SQL Injection 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 SQL 쿼리 구조를 변경할 수 있는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "쿼리가 변경되지 않으면 취약점이 아니다"

소스코드에서 SQL 문자열 연결이 있다고 바로 SQL Injection으로 보고하지 않는다. 실제로 사용자가 제어한 입력으로 SQL 쿼리 구조를 변경하여 의도하지 않은 결과를 얻을 수 있는 것을 확인해야 취약점이다.

ORM(Sequelize, TypeORM, Prisma, Django ORM 등)을 사용하는 코드는 기본적으로 파라미터화된 쿼리를 생성하므로 안전하다. Raw query를 사용하는 부분만 집중 점검한다.

## SQL Injection의 유형

### Classic (In-band) SQL Injection
쿼리 결과가 응답에 직접 반환되는 경우. UNION 기반 또는 Error 기반으로 데이터를 추출한다.

### Blind SQL Injection
쿼리 결과가 응답에 직접 반환되지 않는 경우. Boolean 기반(참/거짓에 따른 응답 차이) 또는 Time 기반(sleep으로 응답 지연)으로 데이터를 추론한다.

### Second-Order SQL Injection
사용자 입력이 먼저 DB에 저장된 뒤, 다른 쿼리에서 해당 값을 읽어 SQL에 삽입하는 경우. 저장 시점과 실행 시점이 분리되어 있어 추적이 어렵다.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

