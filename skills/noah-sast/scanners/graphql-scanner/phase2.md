### Phase 2: 동적 테스트 (검증)

Phase 1 소스코드 분석이 완료되면 후보 목록을 사용자에게 보여준다. 후보가 존재하는 경우에만 동적 테스트를 진행한다. 후보가 0건이면 동적 테스트 없이 바로 보고서를 작성한다.

**동적 테스트 정보 획득:**

사용자에게는 테스트 대상 도메인(Host)과 직접 획득이 불가능한 정보(외부 콜백 서비스 URL, 프로덕션 전용 자격 증명 등)만 요청한다. 그 외의 정보는 소스코드 분석 또는 관련 엔드포인트에 직접 HTTP 요청을 보내 획득한다.

사용자가 동적 테스트를 원하지 않거나 정보를 제공하지 않으면, 소스코드 분석 결과의 모든 후보를 "후보"로 유지한 채 Phase 3으로 진행한다.

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
- **후보**: 동적 테스트를 수행하지 않았거나, 동적 테스트로 확인이 불가하여 수동 확인이 필요한 경우
- **"확인됨"은 동적 테스트를 통해서만 부여할 수 있다**: 소스코드 분석만으로는 아무리 취약해 보여도 "확인됨"으로 보고하지 않는다. 동적 테스트로 실제 트리거를 확인한 경우에만 "확인됨"이다. 동적 테스트를 수행하지 않았으면 모든 결과는 "후보"이다.
- **보고서 제외**: 동적 테스트 결과 취약하지 않은 것으로 확인된 경우는 보고서에 포함하지 않는다
