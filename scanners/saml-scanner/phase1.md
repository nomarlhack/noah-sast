> ## 핵심 원칙: "변조된 SAML Response로 인증이 우회되지 않으면 취약점이 아니다"
>
> SAML을 사용한다고 바로 취약점으로 보고하지 않는다. 실제로 SAML Response의 서명을 제거하거나, Assertion을 변조하거나, XML 서명 래핑 공격을 수행하여 다른 사용자로 인증이 되는 것을 확인해야 취약점이다.
>

### Phase 1: 정찰 (소스코드 분석)

SAML SP(Service Provider) 구현을 분석하여 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: SAML 라이브러리 확인

   **Node.js:**
   - `passport-saml` / `@node-saml/passport-saml`
   - `saml2-js`
   - `samlify`
   - 직접 구현 (XML 파싱 + 서명 검증)

   **Python:**
   - `python3-saml` (OneLogin)
   - `pysaml2`
   - `django-saml2-auth`

   **Java:**
   - Spring Security SAML (`spring-security-saml2-service-provider`)
   - OpenSAML
   - OneLogin SAML Java Toolkit

   **Ruby:**
   - `ruby-saml`
   - `omniauth-saml`

   **PHP:**
   - `onelogin/php-saml`
   - `simplesamlphp`
   - `lightsaml`

2. **SAML Response 처리 로직 분석**:

   **서명 검증:**
   - Response 서명 검증 여부
   - Assertion 서명 검증 여부
   - 서명이 없는 Response/Assertion 거부 여부 (`wantAssertionsSigned`, `wantResponseSigned`)
   - `<ds:Reference URI>` 검증 — 서명이 실제 Assertion/Response를 가리키는지 확인
   - 여러 Assertion이 있을 때 어떤 것을 사용하는지

   **XML 파싱:**
   - XML 파서 설정 (XXE 방어 여부)
   - XML 정규화(Canonicalization) 방식
   - Comment 처리 방식

   **Assertion 검증:**
   - `NotBefore` / `NotOnOrAfter` 시간 검증
   - `InResponseTo` 검증 (Replay 방어)
   - `Audience` / `AudienceRestriction` 검증
   - `Recipient` / `Destination` 검증
   - `Issuer` 검증

   **속성 추출:**
   - NameID 추출 방식
   - Attribute 추출 방식 (어떤 Assertion에서 읽는지)

3. **SAML 설정 확인**:
   - `wantAssertionsSigned: true/false`
   - `wantResponseSigned: true/false`
   - `strict: true/false`
   - IdP 인증서/메타데이터 설정
   - ACS (Assertion Consumer Service) 엔드포인트

4. **후보 목록 작성**: 각 후보에 대해 "어떻게 SAML Response를 변조하면 인증을 우회할 수 있는지"를 구체적으로 구상.

## 후보 판정 제한

SAML 라이브러리를 직접 사용하는 코드가 있는 경우만 분석 대상. 외부 서비스에 위임하는 경우 제외.
