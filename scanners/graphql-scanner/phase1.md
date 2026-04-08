> ## 핵심 원칙: "정보가 노출되거나 보안이 우회되지 않으면 취약점이 아니다"
>
> GraphQL을 사용한다고 바로 취약점으로 보고하지 않는다. Introspection이 활성화되어 있어도 프로덕션 환경에서 의도적으로 공개하는 경우가 있다. 실제로 의도하지 않은 스키마 노출, 인가 우회, DoS가 발생하는 것을 확인해야 취약점이다.
>

### Phase 1: 정찰 (소스코드 분석)

GraphQL API 구현을 분석하여 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: GraphQL 프레임워크/라이브러리 확인

   **Node.js:**
   - `apollo-server` / `@apollo/server` — Apollo Server
   - `express-graphql` — Express GraphQL (deprecated)
   - `graphql-yoga` — Yoga
   - `mercurius` — Fastify GraphQL
   - `graphql-js` — 참조 구현

   **Python:**
   - `graphene` / `graphene-django`
   - `strawberry-graphql`
   - `ariadne`

   **Java:**
   - `graphql-java`
   - `Spring for GraphQL` (`spring-boot-starter-graphql`)
   - `Netflix DGS`

   **Ruby:**
   - `graphql-ruby`

2. **Introspection 설정 확인**:
   - Apollo Server: `introspection: false` 옵션 설정 여부 (프로덕션 기본 비활성화)
   - Yoga: `maskedErrors`, introspection 설정
   - Django Graphene: `GRAPHENE.MIDDLEWARE`에서 introspection 차단 여부
   - 환경별(dev/prod) introspection 분기 여부

3. **인가 로직 분석**:
   - resolver별 인가 검사 존재 여부
   - `@auth`, `@permission` 등 디렉티브 기반 인가
   - 미들웨어/가드 레벨의 인가 (모든 resolver에 적용되는지)
   - 뮤테이션에 대한 인가와 쿼리에 대한 인가가 동일한 수준인지
   - 중첩 resolver에서의 인가 누락 (부모 resolver에만 인가가 있고 자식에는 없는 경우)

4. **쿼리 복잡도 제한 확인**:
   - `depthLimit` / `queryDepth` 제한 설정 여부
   - `graphql-query-complexity`, `graphql-validation-complexity` 등 복잡도 분석 라이브러리 사용 여부
   - `maxFieldCount`, `maxAliases` 제한
   - 타임아웃 설정

5. **Batch 쿼리 설정 확인**:
   - 배열 쿼리 허용 여부 (`allowBatchedHttpRequests`)
   - Batch 크기 제한
   - Alias 기반 batch (`{ a1: user(id:1) { ... } a2: user(id:2) { ... } }`) 제한

6. **에러 처리 확인**:
   - 프로덕션 환경에서 상세 에러 메시지 노출 여부
   - Field suggestion 비활성화 여부 (`NoSchemaIntrospectionCustomRule` 등)
   - 스택 트레이스 노출 여부

7. **후보 목록 작성**: 각 후보에 대해 "어떻게 GraphQL 쿼리를 조작하면 보안을 우회할 수 있는지"를 구체적으로 구상.

## 후보 판정 제한

GraphQL 엔드포인트를 직접 구현하는 코드가 있는 경우만 분석 대상. 전이 의존성은 제외.
