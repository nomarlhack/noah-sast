---
name: graphql-scanner
description: "소스코드 분석과 동적 테스트를 통해 GraphQL 취약점을 탐지하는 스킬. Introspection 노출, 인가 우회, 쿼리 복잡도 DoS, Batch 공격, Field Suggestion 정보 노출 등을 분석하고 검증한다. 사용자가 'GraphQL 취약점 찾아줘', 'GraphQL 스캔', 'GraphQL introspection', 'GraphQL 인가 우회', 'GraphQL DoS', 'GraphQL audit', 'GraphQL 점검' 등을 요청할 때 이 스킬을 사용한다."
grep_patterns:
  - "graphql"
  - "GraphQL"
  - "apollo-server"
  - "express-graphql"
  - "graphql-yoga"
  - "graphene"
  - "strawberry"
  - "ariadne"
  - "graphql-java"
  - "graphql-ruby"
  - "__schema"
  - "introspection"
  - "/graphql"
---

# GraphQL Scanner

소스코드 분석으로 GraphQL API의 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 보안이 우회되거나 정보가 노출되는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "정보가 노출되거나 보안이 우회되지 않으면 취약점이 아니다"

GraphQL을 사용한다고 바로 취약점으로 보고하지 않는다. Introspection이 활성화되어 있어도 프로덕션 환경에서 의도적으로 공개하는 경우가 있다. 실제로 의도하지 않은 스키마 노출, 인가 우회, DoS가 발생하는 것을 확인해야 취약점이다.

## GraphQL 취약점의 유형

### Introspection 노출
프로덕션 환경에서 Introspection 쿼리가 활성화되어 전체 스키마(타입, 필드, 뮤테이션, 인자)가 노출되는 경우. 공격자가 API 구조를 파악하여 후속 공격에 활용할 수 있다.

### 인가 우회 (Authorization Bypass)
GraphQL resolver에서 필드/타입 수준의 인가 검사가 누락되어, 인증된 사용자가 다른 사용자의 데이터에 접근하거나 관리자 전용 쿼리/뮤테이션을 실행할 수 있는 경우. REST API와 달리 GraphQL은 단일 엔드포인트에서 다양한 데이터를 요청할 수 있어 인가 누락이 발생하기 쉽다.

### 쿼리 복잡도 DoS (Query Complexity Attack)
깊이 제한, 복잡도 제한, 비용 분석이 없어 중첩 쿼리나 대량 데이터 요청으로 서버 리소스를 고갈시킬 수 있는 경우.

```graphql
# 중첩 쿼리 DoS 예시
{
  users {
    posts {
      comments {
        author {
          posts {
            comments {
              author { ... }
            }
          }
        }
      }
    }
  }
}
```

### Batch 쿼리 공격
단일 요청에 여러 쿼리를 배열로 전송(`[{query1}, {query2}, ...]`)하여 Rate Limiting을 우회하거나, 브루트포스 공격(OTP, 패스워드 등)을 수행하는 경우.

### Field Suggestion 정보 노출
존재하지 않는 필드를 쿼리했을 때 에러 메시지에서 유사한 필드명을 제안(`Did you mean ...?`)하여 스키마 정보가 노출되는 경우. Introspection이 비활성화되어 있어도 필드명을 추론할 수 있다.

### SQL/NoSQL Injection via GraphQL
GraphQL 인자(arguments)가 백엔드 DB 쿼리에 직접 삽입되는 경우. GraphQL 자체의 취약점은 아니지만 GraphQL 인자를 통한 인젝션 경로를 점검한다.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 이 스킬과 같은 skills 디렉토리 내의 `noah-sast/agent-guidelines.md`를 참조한다. 이 파일의 위치를 기준으로 `../noah-sast/agent-guidelines.md` 경로로 접근할 수 있다.
