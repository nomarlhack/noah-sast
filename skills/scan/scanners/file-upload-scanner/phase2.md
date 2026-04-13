### Phase 2: 동적 테스트 (검증)

업로드 기능에 API 키, 서명(Presigned URL), 자격 증명 등이 필요한 경우 소스코드에서 업로드 흐름을 먼저 파악한다. 클라이언트가 서버에서 업로드 토큰/URL을 발급받은 뒤 업로드하는 구조라면, 발급 API를 먼저 호출하여 필요한 자격 증명을 획득한 후 동적 테스트를 진행한다.

**테스트 방법:**
1. curl로 테스트 파일을 업로드
2. 업로드 성공 여부 확인
3. 업로드된 파일에 URL로 접근하여 내용이 반환/실행되는지 확인

**안전한 테스트 파일 (실제 악성 코드가 아닌 무해한 파일):**
- 텍스트 파일: 확장자만 `.php`, `.jsp` 등으로 변경한 `test` 텍스트
- HTML 파일: `<h1>upload-test</h1>` 같은 단순 HTML
- SVG 파일: 스크립트 없는 단순 SVG

**curl 예시:**
```
# 확장자 검증 우회 테스트
curl -X POST "https://target.com/api/upload" \
  -H "Cookie: session=..." \
  -F "file=@test.html;type=image/png"

# 이중 확장자 테스트
curl -X POST "https://target.com/api/upload" \
  -H "Cookie: session=..." \
  -F "file=@test.php.jpg;type=image/jpeg"
```

**확인 사항:**
- 업로드 응답에서 파일 URL/경로가 반환되면 해당 URL에 접근
- 업로드된 HTML 파일에 접근했을 때 브라우저에서 렌더링되는지 확인
- Content-Type이 원본 그대로 서빙되는지, `application/octet-stream`으로 강제되는지 확인

**검증 기준:**
- **확인됨**: 동적 테스트로 위험한 파일이 업로드되고 URL로 접근하여 내용이 반환/실행된 것을 직접 확인함
