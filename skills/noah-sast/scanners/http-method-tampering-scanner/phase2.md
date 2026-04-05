### Phase 2: 동적 테스트 (검증)

Phase 1 소스코드 분석이 완료되면 후보 목록을 사용자에게 보여준다. 후보가 존재하는 경우에만 동적 테스트를 진행한다. 후보가 0건이면 동적 테스트 없이 바로 보고서를 작성한다.

**동적 테스트 정보 획득:**

사용자에게는 테스트 대상 도메인(Host)과 직접 획득이 불가능한 정보(외부 콜백 서비스 URL, 프로덕션 전용 자격 증명 등)만 요청한다. 그 외의 정보는 소스코드 분석 또는 관련 엔드포인트에 직접 HTTP 요청을 보내 획득한다.

사용자가 동적 테스트를 원하지 않거나 정보를 제공하지 않으면, 소스코드 분석 결과의 모든 후보를 "후보"로 유지한 채 Phase 3으로 진행한다.

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
- **후보**: 동적 테스트를 수행하지 않았거나, 동적 테스트로 확인이 불가하여 수동 확인이 필요한 경우
- **"확인됨"은 동적 테스트를 통해서만 부여할 수 있다**: 소스코드 분석만으로는 아무리 취약해 보여도 "확인됨"으로 보고하지 않는다. 동적 테스트로 실제 트리거를 확인한 경우에만 "확인됨"이다. 동적 테스트를 수행하지 않았으면 모든 결과는 "후보"이다.
- **보고서 제외**: 동적 테스트 결과 취약하지 않은 것으로 확인된 경우는 보고서에 포함하지 않는다
