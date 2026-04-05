> **호출부 추적 — 실제 URL 경로 확정**: 모든 후보에 대해 라우트 정의 파일을 Read로 읽어 실제 URL 경로를 확정한다. 컴포넌트/파일 이름에서 경로를 유추하는 것은 확정이 아니다. 절차: (1) Sink의 호출부를 Grep → 최종 페이지 컴포넌트/컨트롤러 식별 (2) 라우트 정의(routes/index.tsx, @RequestMapping 등)를 Read로 읽어 경로 문자열 확인 (3) 후보 반환 시 근거 포함: `실제 경로: /home/apply (src/routes/index.tsx:42)`

### Phase 1: 정찰 (소스코드 분석)

사용자 입력 → SQL 쿼리 경로를 추적하여 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: 프레임워크/언어/DB/ORM 확인
   - ORM 사용 여부: Sequelize, TypeORM, Prisma, Knex, Django ORM, SQLAlchemy, ActiveRecord, Hibernate, JPA
   - Raw query 사용 여부: `sequelize.query()`, `knex.raw()`, `prisma.$queryRaw()`, `connection.query()` 등

2. **Source 식별**: 사용자가 제어 가능한 입력 중 SQL 쿼리에 사용될 수 있는 것
   - HTTP 파라미터: `id`, `name`, `search`, `query`, `sort`, `order`, `filter`, `category`, `page`, `limit`, `offset`, `where`, `column`
   - URL 경로 파라미터
   - HTTP 헤더 (X-Forwarded-For 등이 로깅 쿼리에 사용되는 경우)
   - 쿠키 값

3. **Sink 식별**: SQL 쿼리를 실행하는 코드

   **Node.js:**
   - `connection.query("SELECT ... " + userInput)` — mysql/mysql2 직접 쿼리
   - `sequelize.query("SELECT ... " + userInput)` — Sequelize raw query
   - `knex.raw("SELECT ... " + userInput)` — Knex raw query
   - `prisma.$queryRaw\`SELECT ... ${userInput}\`` — Prisma raw query (tagged template은 안전, 문자열 연결은 위험)
   - `prisma.$queryRawUnsafe("SELECT ... " + userInput)` — Prisma unsafe raw query
   - `pool.query("SELECT ... " + userInput)` — pg(PostgreSQL) 직접 쿼리
   - `db.run("SELECT ... " + userInput)` — better-sqlite3, sqlite3

   **Python:**
   - `cursor.execute("SELECT ... " + user_input)` — 직접 쿼리
   - `cursor.execute("SELECT ... %s" % user_input)` — 포맷 문자열 (위험)
   - `cursor.execute(f"SELECT ... {user_input}")` — f-string (위험)
   - `Model.objects.raw("SELECT ... " + user_input)` — Django raw query
   - `Model.objects.extra(where=[user_input])` — Django extra (위험)
   - `session.execute(text("SELECT ... " + user_input))` — SQLAlchemy raw

   **Java:**
   - `statement.executeQuery("SELECT ... " + userInput)` — Statement (위험)
   - `entityManager.createNativeQuery("SELECT ... " + userInput)` — JPA native query
   - `jdbcTemplate.query("SELECT ... " + userInput)` — Spring JdbcTemplate

   **Ruby:**
   - `Model.where("column = '" + user_input + "'")` — Rails string condition
   - `ActiveRecord::Base.connection.execute("SELECT ... " + user_input)` — 직접 쿼리
   - `Model.find_by_sql("SELECT ... " + user_input)` — raw SQL

   **PHP:**
   - `mysqli_query($conn, "SELECT ... " . $user_input)` — 직접 쿼리
   - `$pdo->query("SELECT ... " . $user_input)` — PDO 직접 쿼리

4. **경로 추적**: Source에서 Sink까지 데이터가 파라미터 바인딩 없이 도달하는 경로 확인. 다음을 점검:
   - Prepared Statement / 파라미터 바인딩 사용 여부 (`?` 또는 `:param` 플레이스홀더)
   - ORM 메서드 사용 여부 (`.where({column: value})` 형태는 안전)
   - 입력값 이스케이프/인코딩 여부
   - 숫자 타입 변환 (parseInt, Number 등) 후 쿼리에 사용하면 안전
   - ORDER BY, LIMIT 등에 사용자 입력이 삽입되는 경우 (파라미터 바인딩이 불가능한 위치)

5. **후보 목록 작성**: 각 후보에 대해 "어떤 입력으로 어떻게 SQL 구조를 변경할 수 있는지"를 구체적으로 구상. 데이터 흐름 추적을 완료한 뒤에도 공격 경로가 없으면 버린다. 추적 없이 직관으로 버리지 않는다..

#### 안전한 패턴 (취약하지 않은 코드)

- `connection.query("SELECT * FROM users WHERE id = ?", [userId])` — 파라미터 바인딩
- `User.findOne({ where: { id: userId } })` — ORM 메서드
- `cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))` — 파라미터 바인딩
- `PreparedStatement.setString(1, userInput)` — Java Prepared Statement
- `const id = parseInt(req.params.id); query("SELECT ... WHERE id = " + id)` — 숫자 변환 후 사용

#### 주의가 필요한 패턴

- `knex.orderBy(userInput)` — ORDER BY 컬럼명에 사용자 입력이 들어가면 Injection 가능
- `sequelize.query("SELECT ... ORDER BY " + sortColumn)` — 정렬 컬럼의 동적 지정
- `Model.objects.extra(where=[...])` — Django extra는 raw SQL을 허용

## 후보 판정 제한

사용자 입력이 문자열 연결로 쿼리에 삽입되는 경우만 후보. 프레임워크 파라미터 바인딩 적용 시 제외. HTTP 입력과 무관한 경로도 제외.
