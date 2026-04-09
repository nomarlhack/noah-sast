### Phase 2: 동적 테스트 (검증)

> 공통 시작 절차 / 공통 검증 기준은 `agent-guidelines-phase2.md` 지침 7에 정의되어 있다. 이 파일은 보안 헤더 스캐너의 고유 절차만 다룬다.

**도구 선택:** 응답 헤더만 확인하면 되므로 **curl만 사용**한다. Playwright는 사용하지 않는다.

---

## 기본 원칙

- 모든 판정은 **실제 응답 헤더**로 한다. 코드/설정 파일에서 "있을 것 같다"는 이유만으로 안전 판정하지 않는다.
- 코드/설정에 없어도 응답에 있으면 **보고서 제외** (CDN/프록시/웹서버 계층 보강). 코드/설정에 있어도 응답에 없으면 **확인됨**.
- HSTS는 **HTTPS 응답에서만 유효**하다. HTTP(80) 응답이나 리다이렉트 중간 응답에서 확인하지 않는다.
- Cache-Control 검증은 반드시 **인증 세션 쿠키를 동반**한 요청으로 수행한다.
- **각 라벨 검증은 phase1.md의 후보 path별로 반복**한다. 루트(`/`) 1회 덤프로 모든 라벨을 판정하지 않는다. SPA shell만 CSP가 붙고 그 외 라우트는 누락되는 경우가 흔하다.

---

## Step 1: 후보 path별 헤더 일괄 조회

phase1.md 후보의 각 URL에 대해 한 번씩 실행한다.

```
curl -sIv "https://<host>/<path>" 2>&1 | grep -iE '^< (content-security-policy|content-security-policy-report-only|strict-transport-security|x-frame-options|x-content-type-options|referrer-policy|permissions-policy|feature-policy|access-control-|cache-control|pragma|expires)'
```

이 출력을 기준으로 아래 라벨별 판정을 수행한다.

---

## Step 2: 라벨별 테스트

### Content-Security-Policy

**`CSP_MISSING` — CSP 헤더 부재**
```
curl -sI "https://<host>/<html-path>" | grep -i '^content-security-policy:'
```
- 확인됨: HTML을 반환하는 페이지 응답에서 출력 없음
- 비 HTML 경로(`/api/*` JSON만 반환)에서는 판정 제외

**`CSP_UNSAFE_INLINE` / `CSP_UNSAFE_EVAL`**
```
curl -sI "https://<host>/<html-path>" | grep -i '^content-security-policy:'
```
- 확인됨: 응답 값의 `script-src` / `default-src` 디렉티브에 `'unsafe-inline'` 또는 `'unsafe-eval'` 포함
- `strict-dynamic` + nonce/hash가 함께 설정된 경우는 strict-dynamic이 unsafe-inline을 무력화하므로 보고서 제외

**`CSP_WILDCARD`**
- 확인됨: `default-src` 또는 `script-src`에 단독 `*` (scheme 제한 없음)

**`CSP_REPORT_ONLY`**
```
curl -sI "https://<host>/<html-path>" | grep -iE '^content-security-policy(-report-only)?:'
```
- 확인됨: `Content-Security-Policy-Report-Only`만 존재하고 강제 `Content-Security-Policy`는 부재

### CORS (Access-Control-Allow-Origin)

CORS 검증은 **정상 GET + 공격자 Origin GET + Preflight OPTIONS** 3회 요청을 비교한다. 실제 정책은 preflight에서 분기되는 경우가 많아 GET만으로는 부족하다.

```
# 정상 Origin
curl -sI -H "Origin: https://<host>" "https://<host>/api/<endpoint>" | grep -iE '^access-control-'

# 공격자 Origin
curl -sI -H "Origin: https://evil.com" "https://<host>/api/<endpoint>" | grep -iE '^access-control-'

# null Origin
curl -sI -H "Origin: null" "https://<host>/api/<endpoint>" | grep -iE '^access-control-'

# Preflight OPTIONS
curl -sI -X OPTIONS \
  -H "Origin: https://evil.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: authorization,content-type" \
  "https://<host>/api/<endpoint>" | grep -iE '^access-control-'
```

**`CORS_WILDCARD_CRED`**
- 확인됨: `Access-Control-Allow-Origin: *` + `Access-Control-Allow-Credentials: true` (브라우저는 거부하지만 서버 응답 자체가 misconfig 지표)

**`CORS_REFLECT`**
- 확인됨: 공격자 Origin 요청에서 `Access-Control-Allow-Origin: https://evil.com` 그대로 반사됨 + `Access-Control-Allow-Credentials: true`

**`CORS_NULL`**
- 확인됨: `Access-Control-Allow-Origin: null` 반사 + Credentials 허용

### Strict-Transport-Security

**`HSTS_MISSING`**
```
curl -sI "https://<host>/" | grep -i '^strict-transport-security:'
```
- 확인됨: HTTPS 응답에 출력 없음

**`HSTS_SHORT_MAXAGE`**
- 확인됨: `max-age` 값이 `31536000`(1년) 미만
- `includeSubDomains` 부재 / `preload` 부재는 정보 수준으로만 기재 (확인됨 아님)

### Clickjacking (X-Frame-Options / CSP frame-ancestors)

**`CLICKJACK_UNPROTECTED`**
```
curl -sI "https://<host>/<html-path>" | grep -iE '^(x-frame-options|content-security-policy):'
```
- 확인됨: `X-Frame-Options` 부재 AND CSP `frame-ancestors` 디렉티브 부재

**`CLICKJACK_ALLOWFROM`**
- 확인됨: `X-Frame-Options: ALLOW-FROM ...` (비표준, 최신 브라우저 미지원)

### X-Content-Type-Options

**`MIME_SNIFF`**

사용자 업로드 파일을 서빙하는 경로를 대상으로 확인한다. 업로드 경로가 phase1에 명시되지 않은 경우 먼저 정상 업로드 API로 파일을 올린 뒤 응답에서 URL을 추출한다.

```
curl -sI "https://<host>/<user-upload-url>" | grep -i '^x-content-type-options:'
```
- 확인됨: 출력 없음 또는 값이 `nosniff`가 아님

### Referrer-Policy

**`REFERRER_LEAK`**
```
curl -sI "https://<host>/" | grep -i '^referrer-policy:'
```
- 확인됨: 출력 없음 (브라우저 기본값에 의존) AND phase1에서 외부 링크에 민감 URL 파라미터가 식별됨

**`REFERRER_UNSAFE`**
- 확인됨: 값이 `unsafe-url` 또는 `no-referrer-when-downgrade`
- `strict-origin-when-cross-origin` 이상은 보고서 제외

### Permissions-Policy (구 Feature-Policy)

**`PERMISSIONS_MISSING`**
```
curl -sI "https://<host>/" | grep -iE '^(permissions-policy|feature-policy):'
```
- 확인됨: 출력 없음 AND phase1에서 민감 기능(카메라/마이크/위치 등) 사용이 식별됨
- 민감 기능 미사용 프로젝트는 보고서 제외

### Cache-Control (민감 응답)

**`CACHE_SENSITIVE`**

반드시 **인증 세션 쿠키를 동반**하여 phase1의 인증 필요 후보 path별로 확인한다.

```
curl -sI -H "Cookie: <세션쿠키>" "https://<host>/<auth-required-path>" | grep -iE '^(cache-control|pragma|expires):'
```
- 확인됨: 인증 필요 응답에 `Cache-Control` 부재이거나 `public` / `max-age>0`
- `no-store` 또는 `private, no-cache` 설정은 보고서 제외

---

**검증 기준 (스캐너 고유 부분만):**
- **확인됨**: 동적 테스트로 실제 응답 헤더에서 결함이 관찰됨. 각 라벨별로 curl 명령 + 응답 헤더 출력을 증거로 첨부한다.
- **보고서 제외 (스캐너 고유)**: 응답 헤더에서 안전한 설정이 확인된 경우 (코드/설정에는 없어도 CDN/프록시/웹서버 계층에서 주입된 경우 포함).
