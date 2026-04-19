---
id_prefix: SQLI
grep_patterns:
  - "connection\\.query\\s*\\("
  - "sequelize\\.query\\s*\\("
  - "knex\\.raw\\s*\\("
  - "\\$queryRaw"
  - "\\$queryRawUnsafe\\s*\\("
  - "pool\\.query\\s*\\("
  - "cursor\\.execute\\s*\\("
  - "Model\\.objects\\.raw\\s*\\("
  - "Model\\.objects\\.extra\\s*\\("
  - "session\\.execute\\s*\\("
  - "find_by_sql"
  - "connection\\.execute"
  - "db\\.run\\s*\\("
  - "db\\.query\\s*\\("
  - "prepareStatement"
  - "createNativeQuery"
  - "nativeQuery"
  - "jdbcTemplate"
  - "NamedParameterJdbcTemplate"
  - "executeQuery\\s*\\("
  - "Statement\\.execute"
  - "\\.raw\\s*\\("
  - "text\\s*\\("
  - "f\"\\s*SELECT"
  - "f'\\s*SELECT"
  - "@Query"
  - "\\.createQuery\\s*\\("
  - "createQueryBuilder"
  - "Arel\\.sql"
---

> ## 핵심 원칙: "쿼리가 변경되지 않으면 취약점이 아니다"
>
> SQL 문자열 연결이 있다고 바로 SQLi로 보고하지 않는다. 사용자가 제어한 입력으로 쿼리 구조를 실제로 변경할 수 있어야 취약점이다. ORM(Sequelize, TypeORM, Prisma, Django ORM, ActiveRecord 등)은 기본적으로 파라미터화되므로 raw query만 집중 점검한다.

## Sink 의미론

SQLi sink는 "사용자 입력이 SQL 파서에 의해 SQL 토큰(키워드/연산자/식별자)으로 해석될 수 있는 지점"이다. 파라미터 바인딩(`?`/`:param`/`%s` 튜플)은 입력을 리터럴로 강제하므로 sink가 아니다. 반대로 ORDER BY/LIMIT/컬럼명/테이블명은 파라미터 바인딩이 불가능한 위치이므로 ORM을 쓰더라도 sink가 될 수 있다.

| 언어/라이브러리 | 위험 sink |
|---|---|
| Node.js | `connection.query("..." + x)`, `sequelize.query("..." + x)`, `knex.raw("..." + x)`, `prisma.$queryRawUnsafe(...)`, `pool.query(...)`, `db.run(...)` |
| Node.js (안전 한정) | `prisma.$queryRaw\`...${x}\`` (tagged template은 안전, 문자열 연결만 위험) |
| Python | `cursor.execute("..." + x)`, `cursor.execute("...%s" % x)`, `cursor.execute(f"...{x}")`, `Model.objects.raw(...)`, `Model.objects.extra(where=[...])`, `session.execute(text(...))` |
| Java | `Statement.executeQuery(...)`, `entityManager.createNativeQuery(...)`, `jdbcTemplate.query("..." + x)` |
| Ruby | `Model.where("col = '" + x + "'")`, `connection.execute(...)`, `find_by_sql(...)` |
| PHP | `mysqli_query(..., "..." . $x)`, `$pdo->query("..." . $x)` |

## Source-first 추가 패턴

- 헤더값이 로깅/감사 쿼리에 사용되는 경로 (`X-Forwarded-For`, `User-Agent` → audit insert)
- 정렬·페이징 파라미터: `sort`, `order`, `orderBy`, `direction`, `column` — ORDER BY 위치에 들어가는지 확인
- 검색 빌더: `where`, `filter`, `q`, `criteria` 객체가 동적으로 SQL fragment를 만드는 경우
- 관리자 화면의 "쿼리 조건 빌더"
- CSV/Excel import 경로의 컬럼명 매핑
- GraphQL resolver 인자가 raw SQL로 흐르는 경로

## 자주 놓치는 패턴 (Frequently Missed)

- **ORDER BY / GROUP BY 컬럼명 주입**: `knex.orderBy(userInput)`, `sequelize.query("ORDER BY " + sortColumn)` — 파라미터 바인딩 불가 위치. 화이트리스트가 없으면 후보.
- **LIMIT / OFFSET 인젝션**: 일부 DB(MySQL 구버전)는 LIMIT에 표현식을 허용. 정수 캐스트 없으면 후보.
- **테이블/스키마 동적 지정**: 멀티테넌시 코드에서 `tableName`을 사용자 입력에서 받는 경우.
- **`Model.objects.extra(where=[...])`** (Django) — extra는 raw fragment 허용.
- **ActiveRecord string condition**: `Model.where("name = '#{params[:name]}'")` 또는 `Model.where("name = '" + params[:name] + "'")`.
- **JPQL/HQL 문자열 연결**: `entityManager.createQuery("from User where name = '" + name + "'")` — JPA를 쓴다는 사실이 안전을 보장하지 않음.
- **stored procedure 호출의 동적 인자 조립**: `CALL sp_search('${q}')`.
- **2차 SQLi**: 사용자 입력을 일단 DB에 저장한 후 다른 쿼리에서 그 값을 raw로 다시 사용하는 패턴.
- **LIKE 패턴 와일드카드 미이스케이프**: 자체로 SQLi는 아니지만 정보 노출. 구분해서 기록.

## 안전 패턴 카탈로그 (FP Guard)

코드에서 직접 확인된 경우에만 제외:

- **파라미터 바인딩**: `connection.query("... WHERE id = ?", [userId])`, `cursor.execute("... %s", (x,))`, `PreparedStatement.setString(1, x)`.
- **ORM 메서드 호출**: `User.findOne({ where: { id: userId } })`, `User.objects.filter(id=user_id)`, `Model.where(id: user_id)` (해시 형태).
- **Prisma tagged template**: `prisma.$queryRaw\`SELECT ... WHERE id = ${userId}\`` — 백틱 tagged template은 자동 바인딩.
- **숫자 강제 캐스트 후 사용**: `const id = parseInt(req.params.id, 10); query("... WHERE id = " + id)` — 단, NaN 처리 확인.
- **ORDER BY 화이트리스트**: `const SORTABLE = ['id','name']; if (!SORTABLE.includes(col)) throw ...`.
- **DB 권한 분리(읽기 전용 계정)**: SQLi 자체는 가능하나 영향도 라벨링 시 참고. 후보 자체는 유지.

## 후보 판정 의사결정

| 조건 | 판정 |
|---|---|
| 사용자 입력 → 문자열 연결/포맷으로 SQL 본문에 삽입 + 바인딩 없음 | 후보 |
| 사용자 입력 → ORDER BY/LIMIT/식별자 위치 + 화이트리스트 없음 | 후보 (라벨: `IDENTIFIER_INJECTION`) |
| 사용자 입력 → ORM 메서드 인자 (객체 형태) | 제외 |
| 입력이 숫자 캐스트 후 삽입, NaN/오버플로 처리 확인됨 | 제외 |
| 2차 SQLi 의심 (DB값 → raw query) | 후보 (라벨: `SECOND_ORDER`) |
| `prisma.$queryRawUnsafe`/Django `extra`/JPA native query 사용 | 후보 유지하되 주변 검증 확인 |

## 후보 판정 제한

사용자 입력이 문자열 연결로 쿼리에 삽입되는 경우만 후보. 프레임워크 파라미터 바인딩 적용 시 제외. HTTP 입력과 무관한 경로(마이그레이션, 시드, 빌드 스크립트)는 제외.
