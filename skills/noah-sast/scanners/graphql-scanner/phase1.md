> **호출부 추적 — 실제 URL 경로 확정**: 모든 후보에 대해 라우트 정의 파일을 Read로 읽어 실제 URL 경로를 확정한다. 컴포넌트/파일 이름에서 경로를 유추하는 것은 확정이 아니다. 절차: (1) Sink의 호출부를 Grep → 최종 페이지 컴포넌트/컨트롤러 식별 (2) 라우트 정의(routes/index.tsx, @RequestMapping 등)를 Read로 읽어 경로 문자열 확인 (3) 후보 반환 시 근거 포함: `실제 경로: /home/apply (src/routes/index.tsx:42)`

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
