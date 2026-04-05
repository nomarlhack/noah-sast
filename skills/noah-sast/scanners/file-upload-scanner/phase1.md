> **호출부 추적 — 실제 URL 경로 확정**: 모든 후보에 대해 라우트 정의 파일을 Read로 읽어 실제 URL 경로를 확정한다. 컴포넌트/파일 이름에서 경로를 유추하는 것은 확정이 아니다. 절차: (1) Sink의 호출부를 Grep → 최종 페이지 컴포넌트/컨트롤러 식별 (2) 라우트 정의(routes/index.tsx, @RequestMapping 등)를 Read로 읽어 경로 문자열 확인 (3) 후보 반환 시 근거 포함: `실제 경로: /home/apply (src/routes/index.tsx:42)`

### Phase 1: 정찰 (소스코드 분석)

파일 업로드 처리 로직을 분석하여 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: 프레임워크/언어 및 파일 업로드 라이브러리 확인
   - **Node.js**: `multer`, `formidable`, `busboy`, `multiparty`, `express-fileupload`
   - **Python**: Django `FileField`/`ImageField`, Flask `request.files`, FastAPI `UploadFile`
   - **Java**: Spring `MultipartFile`, Apache Commons FileUpload
   - **Ruby**: Rails `ActiveStorage`, CarrierWave, Shrine
   - **PHP**: `$_FILES`, `move_uploaded_file()`

2. **업로드 엔드포인트 식별**: 파일 업로드를 처리하는 API/라우트 찾기
   - `multipart/form-data`를 처리하는 라우트
   - 파일 업로드 미들웨어가 적용된 라우트
   - 프론트엔드에서 파일을 전송하는 코드 (FormData, input[type=file])

3. **검증 로직 분석**: 각 업로드 엔드포인트에서 다음을 점검

   **파일 유형 검증:**
   - Content-Type(MIME) 검증 여부 — 클라이언트가 조작 가능하므로 단독으로는 불충분
   - 파일 확장자 검증 여부 — 블랙리스트 vs 화이트리스트
   - 파일 매직 바이트(시그니처) 검증 여부 — 가장 신뢰할 수 있는 방법
   - 이중 확장자 (`file.php.jpg`, `file.jsp.png`) 처리 여부

   **파일명 처리:**
   - 원본 파일명을 그대로 사용하는지, 랜덤 이름으로 변환하는지
   - 파일명에 `../` 등 경로 조작 문자가 포함될 때 필터링 여부
   - null byte (`file.php%00.jpg`) 처리 여부

   **저장 위치:**
   - 웹 루트 안에 저장되는지 (직접 URL 접근 가능)
   - 웹 루트 밖에 저장되는지 (API를 통해서만 접근)
   - 클라우드 스토리지(S3, GCS 등)에 저장되는지
   - CDN을 통해 서빙되는지

   **서빙 방식:**
   - 업로드된 파일이 원본 Content-Type으로 서빙되는지
   - `Content-Disposition: attachment` 헤더 설정 여부
   - `X-Content-Type-Options: nosniff` 헤더 설정 여부

   **크기 제한:**
   - 파일 크기 제한이 설정되어 있는지
   - 업로드 요청 수 제한(Rate Limiting)이 있는지

4. **후보 목록 작성**: 검증이 누락된 업로드 엔드포인트 정리. 각 후보에 대해 "어떤 파일을 업로드하면 어떤 위험이 발생하는지"를 구체적으로 구상.

## 후보 판정 제한

파일 업로드를 파라미터로 받는 엔드포인트가 있는 경우만 후보. import만 있고 호출부가 없으면 제외.
