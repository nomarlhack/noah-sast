> **호출부 추적 — 실제 URL 경로 확정**: 모든 후보에 대해 라우트 정의 파일을 Read로 읽어 실제 URL 경로를 확정한다. 컴포넌트/파일 이름에서 경로를 유추하는 것은 확정이 아니다. 절차: (1) Sink의 호출부를 Grep → 최종 페이지 컴포넌트/컨트롤러 식별 (2) 라우트 정의(routes/index.tsx, @RequestMapping 등)를 Read로 읽어 경로 문자열 확인 (3) 후보 반환 시 근거 포함: `실제 경로: /home/apply (src/routes/index.tsx:42)`

### Phase 1: 정찰 (소스코드 분석)

사용자 입력 → 서버사이드 HTTP 요청 경로를 추적하여 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: package.json, Gemfile, requirements.txt, pom.xml 등에서 프레임워크/언어/HTTP 클라이언트 라이브러리 확인

2. **Source 식별**: 사용자가 제어 가능한 입력 중 URL로 사용될 수 있는 것
   - HTTP 파라미터 (query, body, header): `url`, `link`, `href`, `src`, `dest`, `redirect`, `uri`, `path`, `domain`, `host`, `callback`, `webhook`, `feed`, `proxy`, `target`, `endpoint`
   - 파일 업로드의 URL 입력 (원격 파일 가져오기)
   - API 요청 본문의 URL 필드
   - Webhook/콜백 URL 등록 기능
   - RSS/Atom 피드 URL
   - OpenGraph/메타데이터 크롤링 URL

3. **Sink 식별**: 서버사이드에서 HTTP 요청을 수행하는 코드
   - **Node.js**: `axios`, `node-fetch`, `got`, `request`, `http.get`, `https.get`, `http.request`, `undici`, `urllib`
   - **Python**: `requests`, `urllib`, `urllib3`, `httpx`, `aiohttp`, `http.client`
   - **Java**: `HttpURLConnection`, `HttpClient`, `OkHttp`, `RestTemplate`, `WebClient`, `Jsoup.connect`
   - **Ruby**: `Net::HTTP`, `open-uri`, `HTTParty`, `Faraday`, `RestClient`
   - **Go**: `http.Get`, `http.Post`, `http.NewRequest`, `resty`
   - **공통**: 프록시 미들웨어 (`http-proxy-middleware`, `http-proxy`), 이미지 리사이즈/처리 라이브러리의 URL 입력

4. **경로 추적**: Source에서 Sink까지 데이터가 URL 검증 없이 도달하는 경로 확인. 다음을 점검:
   - URL 파싱 및 검증 로직 존재 여부
   - 화이트리스트/블랙리스트 도메인 필터링
   - IP 주소 필터링 (내부 IP 대역 차단)
   - 프로토콜 제한 (http/https만 허용하는지)
   - DNS rebinding 방어 여부

5. **후보 목록 작성**: 각 후보에 대해 "어떤 입력으로 어떻게 내부 요청을 유발할 수 있는지"를 구체적으로 구상. 데이터 흐름 추적을 완료한 뒤에도 공격 경로가 없으면 버린다. 추적 없이 직관으로 버리지 않는다..

#### SSRF가 아닌 패턴 (오탐 주의)

- **presigned URL 생성**: 사용자 입력이 presigned URL(S3, GCS 등)의 호스트/경로에 반영되어 클라이언트에 반환되더라도, 서버가 그 URL로 직접 요청하지 않으면 SSRF가 아니다. 요청을 보내는 주체가 클라이언트인지 서버인지를 반드시 확인한다.

#### Sink을 찾을 때 흔히 놓치는 패턴

단순한 `axios.get(url)` 외에도 SSRF가 발생하는 패턴이 많다:

- **프록시/리버스 프록시**: `http-proxy-middleware`에서 `target`이 동적으로 결정되는 경우
- **파일 다운로드**: 원격 URL에서 파일을 가져와 저장하는 기능 (`download`, `fetch`, `import from URL`)
- **이미지 처리**: 이미지 URL을 받아 리사이즈/썸네일 생성 (`sharp`, `imagemagick`, `Pillow`)
- **PDF 생성**: HTML-to-PDF 변환 시 외부 리소스 로딩 (`puppeteer`, `wkhtmltopdf`, `weasyprint`)
- **웹 스크래핑/크롤링**: 사용자 지정 URL의 메타데이터/콘텐츠 가져오기
- **Webhook 발송**: 사용자가 등록한 URL로 이벤트 알림 전송
- **OAuth/SSO 콜백**: 동적으로 구성되는 redirect_uri
- **XML 처리**: XXE를 통한 SSRF (DOCTYPE ENTITY로 외부 리소스 로딩)
- **Git 클론/SVN checkout**: 사용자가 지정한 저장소 URL

## 후보 판정 제한

사용자 입력이 HTTP 요청의 호스트/스킴을 제어할 수 있는 경우 후보. base URL이 설정 주입이고 경로도 하드코딩이면 제외. 경로에 사용자 입력이 포함되면 후보.
