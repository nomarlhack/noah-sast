> ## 핵심 원칙: "악성 파일이 업로드되고 접근 가능하지 않으면 취약점이 아니다"
>
> 파일 업로드 기능이 있다고 바로 취약점으로 보고하지 않는다. 다음 조건이 모두 충족되어야 취약점이다:
> 1. 위험한 파일(웹셸, 실행 파일 등)이 업로드됨
> 2. 업로드된 파일에 접근할 수 있음 (URL로 직접 접근 가능)
> 3. 파일이 서버에서 실행되거나, 다른 사용자에게 서빙됨
>
> 검증 없이 "업로드 기능에 확장자 검증이 없다"고만 보고하는 것은 부족하다. 업로드된 파일이 어디에 저장되고, 어떻게 서빙되는지까지 추적해야 한다.
>

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
