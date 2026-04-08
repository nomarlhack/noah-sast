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
- `Set-Cookie` 응답 헤더에서 SameSite 속성 확인
- `SameSite=None`이거나 속성이 없으면 CSRF 가능
- `SameSite=Lax`이면 GET 요청으로 상태 변경하는 엔드포인트만 취약

**검증 기준:**
- **확인됨**: 동적 테스트로 CSRF 토큰 없이 외부 Origin에서 보낸 요청이 정상 처리된 것을 직접 확인함
