---
name: soapaction-spoofing-scanner
description: "소스코드 분석과 동적 테스트를 통해 SOAPAction Spoofing 취약점을 탐지하는 스킬. SOAP 웹 서비스에서 SOAPAction 헤더와 실제 SOAP Body의 오퍼레이션이 불일치할 때 인증/인가를 우회할 수 있는지 분석하고 검증한다. 사용자가 'SOAPAction spoofing', 'SOAPAction 변조', 'SOAP 취약점', 'WS-Security 우회', 'SOAP audit', 'SOAP 점검' 등을 요청할 때 이 스킬을 사용한다."
grep_patterns:
  - "SOAPAction"
  - "@WebService"
  - "@WebMethod"
  - "Apache CXF"
  - "Apache Axis"
  - "@Endpoint"
  - "@PayloadRoot"
  - "zeep"
  - "spyne"
  - "SoapServer"
  - "wsdl"
  - "WSDL"
  - "savon"
  - "soap"
  - "SOAP"
---

# SOAPAction Spoofing Scanner

소스코드 분석으로 SOAP 웹 서비스에서 SOAPAction 헤더 검증 미흡을 식별한 뒤, 동적 테스트로 실제로 SOAPAction 변조를 통해 인증/인가를 우회할 수 있는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "인가가 우회되지 않으면 취약점이 아니다"

SOAPAction 헤더를 변조할 수 있다는 것만으로는 취약점이 아니다. 변조된 SOAPAction 헤더로 인해 권한이 없는 오퍼레이션이 실제로 실행되거나, 인증/인가가 우회되는 것을 확인해야 취약점이다.

## SOAPAction Spoofing의 원리

SOAP 1.1에서는 HTTP 헤더의 `SOAPAction`으로 호출할 오퍼레이션을 지정하고, SOAP Body에도 실제 오퍼레이션이 포함된다. 서버가 라우팅이나 인가를 SOAPAction 헤더만으로 판단하고 Body의 오퍼레이션을 검증하지 않으면, 공격자가 SOAPAction을 허용된 오퍼레이션으로 설정하면서 Body에는 제한된 오퍼레이션을 포함하여 인가를 우회할 수 있다.

```
# 정상 요청: getUserInfo (허용된 오퍼레이션)
POST /service HTTP/1.1
SOAPAction: "getUserInfo"

<soap:Body>
  <getUserInfo><userId>123</userId></getUserInfo>
</soap:Body>

# 공격: SOAPAction은 허용된 getUserInfo, Body는 제한된 deleteUser
POST /service HTTP/1.1
SOAPAction: "getUserInfo"          ← 인가 검사는 이것으로 통과

<soap:Body>
  <deleteUser><userId>123</userId></deleteUser>  ← 실제 실행은 이것
</soap:Body>
```

## 취약점의 유형

### SOAPAction 헤더 기반 인가 우회
서버가 SOAPAction 헤더만으로 인가를 판단하고, SOAP Body의 실제 오퍼레이션과 일치하는지 검증하지 않아 제한된 오퍼레이션을 실행할 수 있는 경우.

### SOAPAction 헤더 기반 라우팅 우회
WAF나 API 게이트웨이가 SOAPAction 헤더로 요청을 필터링하지만, 백엔드 SOAP 서버는 Body의 오퍼레이션을 실행하여 필터링을 우회하는 경우.

### SOAP 1.2 Action 파라미터 변조
SOAP 1.2에서는 `Content-Type: application/soap+xml; action="..."` 형태로 Action이 지정된다. 동일한 불일치 공격이 가능.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 `../../agent-guidelines.md` (이 파일 기준 상대 경로)를 참조한다.
