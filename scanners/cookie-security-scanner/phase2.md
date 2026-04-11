## 동적 검증

Phase 1에서 후보로 판정된 항목을 curl로 테스트한다. **curl만 사용한다.**

---

### Step 1: Set-Cookie 헤더 일괄 수집

인증/로그인 엔드포인트에 요청하여 Set-Cookie 헤더를 수집한다:

```bash
# 로그인 요청 (세션 쿠키 발행)
curl -si -X POST https://<host>/<login-path> \
  -d "username=<user>&password=<pass>" 2>&1 | grep -i 'set-cookie'

# 기존 세션으로 요청 (세션 갱신 시)
curl -sI https://<host>/ -H "Cookie: <세션쿠키>" 2>&1 | grep -i 'set-cookie'
```

수집된 각 Set-Cookie 헤더에서 쿠키 이름, 속성(Secure, HttpOnly, SameSite, Max-Age, Expires, Domain, Path)을 파싱한다.

---

### Step 2: 라벨별 검증

#### COOKIE_NO_SECURE

| 응답 | 판정 |
|------|------|
| 민감 쿠키의 Set-Cookie에 `Secure` 속성 없음 | 확인됨 |
| `Secure` 속성 존재 | 제외 |

#### COOKIE_NO_HTTPONLY

| 응답 | 판정 |
|------|------|
| 세션/인증 쿠키의 Set-Cookie에 `HttpOnly` 속성 없음 | 확인됨 |
| `HttpOnly` 속성 존재 | 제외 |

#### COOKIE_SAMESITE_NONE

| 응답 | 판정 |
|------|------|
| Set-Cookie에 `SameSite=None` 명시 | 확인됨 |
| `SameSite=Lax` 또는 `SameSite=Strict` | 제외 |
| `SameSite` 미명시 (브라우저 기본 Lax) | 제외 |

#### COOKIE_PERSISTENT

| 응답 | 판정 |
|------|------|
| 세션/인증 쿠키에 `Max-Age=N` (N > 604800, 7일) 또는 장기 `Expires` | 확인됨 |
| `Max-Age` / `Expires` 없음 (세션 쿠키) | 제외 |

#### COOKIE_LOOSE_SCOPE

| 응답 | 판정 |
|------|------|
| Set-Cookie에 `Domain=.example.com` (상위 도메인) | 확인됨 |
| `Domain` 미설정 또는 현재 호스트와 일치 | 제외 |

#### COOKIE_PREFIX_MISUSE

| 응답 | 판정 |
|------|------|
| `__Host-` 접두사 쿠키에 `Domain` 속성 존재 | 확인됨 |
| `__Secure-` 접두사 쿠키에 `Secure` 속성 없음 | 확인됨 |
| 접두사 조건 충족 | 제외 |

---

### 유의사항

- Set-Cookie 헤더는 **로그인/세션 생성 시점**에 발행된다. 이미 세션이 있는 상태에서 일반 페이지를 요청하면 Set-Cookie가 없을 수 있다.
- 여러 Set-Cookie 헤더가 반환될 수 있다. 각각을 개별로 판정한다.
- 민감 쿠키 이름 기준: `JSESSIONID`, `connect.sid`, `sessionid`, `session`, `token`, `auth`, `remember`, `PHPSESSID`, `_session`.
