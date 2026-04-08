> ## 핵심 원칙: "의도하지 않은 리소스에 접근하지 못하면 취약점이 아니다"
>
> 소스코드에서 `fs.readFile(userInput)`이 있다고 바로 LFI로 보고하지 않는다. 실제로 `../` 등 경로 조작 문자를 삽입하여 의도하지 않은 파일의 내용을 읽거나, 내부 API의 다른 엔드포인트를 호출할 수 있는 것을 확인해야 취약점이다.
>

### Phase 1: 정찰 (소스코드 분석)

사용자 입력 → 파일 시스템 접근 경로를 추적하여 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: 프레임워크/언어 확인

2. **Source 식별**: 사용자가 제어 가능한 입력 중 파일 경로로 사용될 수 있는 것
   - HTTP 파라미터: `file`, `path`, `page`, `template`, `include`, `doc`, `document`, `folder`, `root`, `dir`, `name`, `filename`, `download`, `lang`, `locale`, `view`, `content`, `log`
   - URL 경로 자체 (동적 라우트 파라미터)
   - 파일 업로드의 파일명
   - API 요청 본문의 파일 경로 필드

3. **Sink 식별**: 파일 시스템 또는 내부 API에 접근하는 코드

   **파일 시스템 Sink:**

   **Node.js:**
   - `fs.readFile()`, `fs.readFileSync()`, `fs.createReadStream()`
   - `fs.readdir()`, `fs.stat()`, `fs.access()`
   - `path.join()`, `path.resolve()` (이것 자체는 안전하지만, 결과가 fs 함수에 전달되면 Sink)
   - `require()`, `import()` (동적 모듈 로딩)
   - `res.sendFile()`, `res.download()` (Express 파일 전송)
   - `ejs.renderFile()`, `pug.renderFile()` 등 템플릿 엔진의 파일 렌더링

   **Python:**
   - `open()`, `os.path.join()` → `open()`
   - `send_file()`, `send_from_directory()` (Flask)
   - `FileResponse()` (Django/FastAPI)
   - `importlib.import_module()`, `__import__()`

   **Java:**
   - `new File()`, `Files.readAllBytes()`, `FileInputStream()`
   - `ClassLoader.getResource()`, `getResourceAsStream()`
   - `RequestDispatcher.include()`, `RequestDispatcher.forward()`

   **Ruby:**
   - `File.read()`, `File.open()`, `IO.read()`
   - `send_file`, `render file:`

   **PHP:**
   - `include()`, `require()`, `include_once()`, `require_once()`
   - `file_get_contents()`, `fopen()`, `readfile()`

   **내부 API Path Traversal Sink:**

   URL 경로 파라미터(`@PathVariable`, `req.params` 등)가 내부 HTTP 클라이언트의 URL에 삽입되어 다른 서비스로 요청이 전달되는 코드. 프록시 체인(서비스 A → 게이트웨이 B → 백엔드 C) 구조에서 경로 파라미터에 `%2f`(URL 인코딩된 `/`)나 `#`(fragment)를 삽입하면 백엔드 서비스의 다른 API를 호출할 수 있다.

   - **Java/Spring**: `@PathVariable`이 `WebClient.get().uri("$host/v2/bots/$botId/...")` 같은 내부 HTTP 요청 URL에 삽입되는 경우
   - **Node.js**: `req.params.id`가 `axios.get(\`${host}/api/${id}/data\`)` 같은 내부 요청에 삽입되는 경우
   - **Python**: `path_param`이 `requests.get(f"{host}/api/{param}/data")` 같은 내부 요청에 삽입되는 경우
   - **프록시 미들웨어**: `http-proxy-middleware`, `nginx proxy_pass` 등에서 경로가 그대로 전달되는 경우

   **내부 API Path Traversal 탐지 포인트:**
   - `@PathVariable`/`req.params` 값이 내부 HTTP 클라이언트 URL에 문자열 연결/템플릿으로 삽입되는지
   - 경로 파라미터에 대한 입력 검증(정규식, 화이트리스트)이 있는지
   - 프록시/게이트웨이가 URL 인코딩된 경로 구분자(`%2f`, `%5c`)를 디코딩 후 전달하는지
   - `#`(fragment)를 사용하여 뒤의 경로를 무효화할 수 있는지

4. **경로 추적**: Source에서 Sink까지 데이터가 경로 검증 없이 도달하는 경로 확인. 다음을 점검:

   **파일 시스템 Path Traversal:**
   - `../` 필터링 여부
   - `path.join()` / `path.resolve()`로 정규화 후 기준 디렉토리 안에 있는지 검증 (path prefix check)
   - 허용 파일 목록(화이트리스트) 존재 여부
   - 확장자 제한 여부
   - null byte (`%00`) 우회 가능 여부 (구 버전 PHP/Node.js)
   - URL 인코딩된 `../` (`%2e%2e%2f`, `..%2f`, `%2e%2e/`) 처리 여부
   - Express `res.sendFile()`의 `root` 옵션 사용 여부 (root 없이 절대경로 사용 시 취약)

   **내부 API Path Traversal:**
   - `@PathVariable`/경로 파라미터에 대한 입력 검증 여부 (정규식, 허용 문자 제한)
   - 프록시/게이트웨이 단계에서 URL 인코딩 디코딩 시점 (double decoding 여부)
   - 내부 HTTP 클라이언트가 URL을 정규화하는지 (`../`를 resolve하는지)
   - `%2f` → `/` 디코딩이 프록시 단계에서 발생하는지 애플리케이션 단계에서 발생하는지
   - `#`(fragment)로 뒤의 경로를 잘라낼 수 있는지 (HTTP 클라이언트가 fragment를 서버로 전송하는지)
   - 서비스 간 인증/인가가 있는지 (내부 API를 직접 호출해도 인증이 필요한지)

5. **후보 목록 작성**: 각 후보에 대해 "어떤 입력으로 어떻게 의도하지 않은 파일이나 내부 API에 접근할 수 있는지"를 구체적으로 구상. 데이터 흐름 추적을 완료한 뒤에도 공격 경로가 없으면 버린다. 추적 없이 직관으로 버리지 않는다..

## 후보 판정 제한

사용자 입력이 파일 시스템 경로나 내부 API 경로에 문자열 연결로 삽입되는 경우만 후보. 프레임워크 URI 템플릿이나 정수 타입 변수는 제외.
