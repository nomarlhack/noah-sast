---
grep_patterns:
  - "@PathVariable"
  - "@RequestParam"
  - "@RequestBody"
  - "req\\.params"
  - "req\\.query"
  - "request\\.args"
  - "params\\[:"
  - "findById"
  - "findOne"
  - "getById"
  - "getOne"
  - "findByPk"
  - "Model\\.find\\s*\\("
  - "repository\\."
  - "permitAll"
  - "hasAnyRole"
  - "@PreAuthorize"
  - "@Secured"
  - "authorize"
---

> ## 핵심 원칙: "다른 사용자 리소스에 실제로 접근할 수 있어야 취약점이다"
>
> `findById(id)` 자체는 취약점이 아니다. 사용자 A의 인증 정보로 사용자 B의 리소스 식별자를 보냈을 때 서버가 B의 리소스를 반환해야 한다.

## Sink 의미론

IDOR sink는 "엔드포인트가 객체 식별자를 받고 그 식별자로 리소스를 조회/수정하는데, 인증된 사용자와 그 객체의 소유 관계를 검증하지 않는 지점"이다. 권한 체크가 라우트 레벨(`role == admin`)만 있고 객체 레벨(`resource.owner == user`)이 없는 케이스가 가장 흔함.

| 카테고리 | 패턴 |
|---|---|
| 경로 파라미터 | `/users/:id`, `/orders/{orderId}`, `/api/v1/posts/{slug}` |
| 쿼리 파라미터 | `?user_id=`, `?account=`, `?org=` |
| 바디 파라미터 | `{userId: ..., action: ...}` (멀티 액션 핸들러) |
| Hidden form field | `<input type=hidden name=id value=...>` |
| 내부 API 노출 | `/internal/...`이 외부 라우트로 누설 |

## Source-first 추가 패턴

- 사용자 ID/주문 ID/문서 ID/게시글 ID를 path/query/body로 받는 모든 라우트
- file ID 다운로드 라우트 (`/files/:id/download`)
- 첨부파일 직접 URL (`/uploads/{uuid}` — UUID 추측 어려움이 보안이 아니라 인가가 필요)
- presigned URL 생성 endpoint
- batch endpoint (`{ids: [...]}`)
- GraphQL `node(id: ...)` resolver
- 검색 endpoint (`?q=...&owner=...`)
- 보고서 export endpoint
- 멀티테넌시 endpoint (org_id를 사용자 입력으로)

## 자주 놓치는 패턴 (Frequently Missed)

- **쿼리에 owner_id 누락**: `WHERE id = ?` (소유자 스코프 없음). `WHERE owner_id = currentUser AND id = ?` 필요.
- **라우트 인증은 통과, 객체 권한 미체크**: `@LoginRequired` + `Order.find(id)` (현재 사용자 무관 조회).
- **간접 참조 매핑 부재**: 사용자 A가 자기 주문 목록에서 ID를 알아낸 후 다른 사람 ID 추측.
- **순차 ID (autoincrement)**: 추측 용이. UUID도 인가가 없으면 동일 — UUID는 보안 아님.
- **GraphQL `node(id:)` global resolver**: 모든 타입을 ID로 조회 → 권한 체크 누락 시 모든 리소스 노출.
- **batch endpoint (`{ids: [1,2,3]}`)**: 일부 ID만 권한 검사 후 전체 반환.
- **PATCH로 owner 변경**: `{id: 1, owner_id: attacker}` → 본인 소유로 만든 후 조작.
- **mass assignment**: `User.update(id, req.body)` — 사용자가 `is_admin: true` 추가.
- **Read는 검증, Update/Delete는 미검증**: 한 라우트만 검사하는 패턴.
- **검색 결과에 권한 외 객체 포함**: 검색은 권한 무시, 사용자가 ID 알아낸 후 직접 조회.
- **export/download가 검증 누락**: PDF/Excel 생성 라우트.
- **첨부파일 URL이 path만 검사**: `?attachment_id=`로 다른 사용자 첨부 다운로드.
- **profile picture URL**: `/users/:id/avatar` — 인가 무시 (공개라 가정).
- **내부 RPC 노출**: 내부용 endpoint가 외부 gateway로 라우팅 누설.
- **Cache 키에 user_id 미포함**: 캐시 응답이 다른 사용자에게 leak.
- **Pagination cursor에 hint 포함**: cursor decode 시 다른 사용자 컨텍스트.
- **WebSocket 채널 구독**: `subscribe('/user/:id/notifications')` — id 검증 없음.
- **Reset password token이 user_id 포함, 서명 없음**.
- **2FA setup endpoint**: `POST /users/:id/2fa/disable` — 본인 인증 없이.
- **Social login link/unlink**: 다른 사용자 계정에 자기 social 연결.
- **`org_id` switch**: 멀티테넌시에서 사용자가 다른 org_id로 요청하면 통과.
- **role/permission 변경 endpoint**: `PUT /users/:id/role`에서 **다른 사용자**의 role을 변경하는 케이스만 본 스캐너 담당(cross-user). 자기 자신 role을 변경하는 mass assignment는 business-logic `PRIV_ESCALATION` 담당.

## 안전 패턴 카탈로그 (FP Guard)

- **쿼리 레벨 owner scope**: `Order.where(user_id: current_user.id).find(id)`.
- **글로벌 미들웨어 owner check**: 모든 `/orders/:id` 진입 시 `before_action :ensure_owner`.
- **Policy 라이브러리** (Pundit, CanCanCan, casl, oso) + 전 라우트 enforce.
- **간접 참조 토큰**: 사용자별 매핑 테이블에서 hash → 실제 ID.
- **Object-level permission framework** (Django Guardian, Spring Security `@PreAuthorize`).
- **공개 리소스**: 설계상 공개 (공개 게시글) — 비즈니스 요구사항 확인.
- **본인 리소스만 반환하는 API**: 식별자 받지만 내부적으로 `current_user`만 조회.
- **GraphQL field-level resolver에 권한 체크**.

## 후보 판정 의사결정

| 조건 | 판정 |
|---|---|
| 식별자 받음 + 소유자 scope 없음 + 객체 권한 체크 없음 | 후보 |
| 라우트 인증만 있고 객체 인가 없음 | 후보 |
| GraphQL global node resolver + 타입별 권한 미체크 | 후보 (라벨: `GRAPHQL_NODE`) |
| Batch endpoint + 일부 ID만 검사 | 후보 (라벨: `BATCH_PARTIAL`) |
| Mass assignment + `owner_id`/`tenant_id` 등 **소유관계 필드** 변경 가능 | 후보 (라벨: `MASS_ASSIGNMENT`) |
| Mass assignment + `role`/`permissions`/`isAdmin` 등 **자기 권한 상승** | **business-logic `PRIV_ESCALATION` 담당** — 본 스캐너 후보 아님 |
| 상태 변경 엔드포인트(approve/cancel/transfer 등)에서 객체 소유권 검증 누락 | 후보 (수직 IDOR로 단독 분류, business-logic STATE_BYPASS와 중복 등재 금지) |
| 글로벌 미들웨어/쿼리 scope 확인 | 제외 |
| 본인 자원만 조회 (식별자 받지만 무시) | 제외 |
| 공개 리소스 (비즈니스 요구사항 확인됨) | 제외 |
| Read는 보호, Update/Delete는 미검증 | 후보 |

## 본 스캐너 담당 아님 (business-logic-scanner 참조)

아래 패턴은 코드 표면이 IDOR과 비슷해 보일 수 있으나 본 스캐너 후보로 등록하지 않는다. 후보 표면이 겹치는 경우 business-logic-scanner 단독으로 보고된다.

- **상태 전이 순서 우회 (워크플로우)**: `order.status = req.body.status` 등 결제/승인 단계 건너뛰기 → `STATE_BYPASS`
- **Race / TOCTOU**: 잔액 차감, 쿠폰 중복 사용, 재고 마이너스 등 비원자적 연산 → `RACE_CONDITION`
- **멱등성 위반**: Idempotency-Key 미사용으로 중복 결제/주문 → `DATA_INTEGRITY`
- **가격·수량·할인 무결성**: 클라이언트가 보낸 가격·수량·쿠폰 값을 서버가 재계산 없이 신뢰 → `PRICE_TAMPER`
- **레이트 리밋·기능 남용**: OTP/SMS/초대/쿠폰 발급의 rate limit 부재 → `FEATURE_ABUSE`
- **자기 자신 권한 상승 (mass assignment)**: 일반 사용자가 `{role: "admin"}` 등으로 자기 role 변경 → `PRIV_ESCALATION`

위 항목은 후보로 등록하지 않고 Source→Sink 추적도 수행하지 않는다.

## 후보 판정 제한

사용자가 제공한 식별자로 **다른 사용자** 리소스에 접근 가능한 경로가 존재하는 경우 후보. 글로벌 미들웨어 소유권 검증 또는 쿼리 사용자 scope 적용 시 제외.
