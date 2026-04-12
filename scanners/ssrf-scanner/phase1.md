---
grep_patterns:
  - "axios"
  - "node-fetch"
  - "http\\.get\\s*\\("
  - "https\\.get\\s*\\("
  - "http\\.request\\s*\\("
  - "urllib"
  - "httpx"
  - "aiohttp"
  - "HttpURLConnection"
  - "RestTemplate"
  - "WebClient"
  - "Net::HTTP"
  - "open-uri"
  - "HTTParty"
  - "Faraday"
  - "RestClient"
  - "http-proxy-middleware"
  - "requests\\.get\\s*\\("
  - "requests\\.post\\s*\\("
  - "OkHttpClient"
  - "Retrofit"
  - "HttpClient"
  - "fetch\\s*\\("
  - "got\\s*\\("
  - "urlopen\\s*\\("
  - "new URL\\s*\\("
  - "URL\\s*\\("
  - "curl_exec\\s*\\("
  - "curl_init\\s*\\("
  - "Guzzle"
  - "GuzzleHttp"
  - "WebRequest\\.Create"
  - "undici"
  - "superagent"
  - "http\\.NewRequest"
  - "resty\\.New"
  - "searchParams\\.get\\s*\\("
  - "@RequestParam"
  - "@RequestBody"
  - "req\\.query"
  - "req\\.body"
---

> ## 핵심 원칙: "서버가 요청을 보내지 않으면 취약점이 아니다"
>
> `axios.get(userInput)`이 있다고 SSRF가 아니다. 서버가 사용자 제어 URL로 실제로 요청을 보내야 한다. "내부 API가 노출되면 위험" 같은 가정은 취약점이 아니다.

## Sink 의미론

SSRF sink는 "URL의 호스트/스킴/경로 일부가 사용자 입력에 의해 결정되고, 그 URL로 서버가 발신 요청을 보내는 지점"이다. **요청 주체가 서버인지 클라이언트인지** 구분이 핵심 — presigned URL 생성처럼 클라이언트가 요청자라면 SSRF 아님.

| 언어 | 일반 sink |
|---|---|
| Node.js | `axios`, `node-fetch`, `got`, `request`, `http.get/request`, `https.get/request`, `undici`, `urllib` |
| Python | `requests`, `urllib`, `urllib3`, `httpx`, `aiohttp`, `http.client` |
| Java | `HttpURLConnection`, `HttpClient` (JDK11+), `OkHttp`, `RestTemplate`, `WebClient`, `Jsoup.connect` |
| Ruby | `Net::HTTP`, `open-uri`, `HTTParty`, `Faraday`, `RestClient` |
| Go | `http.Get/Post/NewRequest`, `resty` |
| 공통 | proxy 미들웨어 (`http-proxy-middleware`), 이미지 처리/리사이즈, PDF 변환, 웹훅 발송 |

## Source-first 추가 패턴

- HTTP 파라미터: `url`, `link`, `href`, `src`, `dest`, `redirect`, `uri`, `path`, `domain`, `host`, `callback`, `webhook`, `feed`, `proxy`, `target`, `endpoint`, `image`, `avatar`
- 파일 업로드의 "URL로 가져오기" 옵션
- API body의 URL 필드
- Webhook/콜백 URL 등록 기능
- RSS/Atom feed URL
- OpenGraph/메타데이터 크롤링 URL
- OAuth `redirect_uri` (open-redirect와 겹치지만 SSRF로도 평가)
- AWS/GCS bucket name (presigned 만들 때)

## 자주 놓치는 패턴 (Frequently Missed)

- **PDF 생성 (HTML → PDF)**: `puppeteer.goto(userHTML)`, `wkhtmltopdf`, `weasyprint` — 외부 리소스 로딩으로 SSRF.
- **이미지 변환/썸네일**: `sharp`/`imagemagick`/`Pillow`가 URL 입력을 받거나 SVG 내부 `<image href=...>`를 fetch.
- **Webhook 발송**: 사용자 등록 URL로 이벤트 전송. 보통 서버측에서 직접 호출.
- **OAuth/SSO 콜백 동적 redirect_uri**: 서버가 그 URL로 직접 요청하는 케이스.
- **XML 처리 → XXE → SSRF**: `<!DOCTYPE [<!ENTITY x SYSTEM "http://internal/">]>`. xxe-scanner와 겹치지만 SSRF 영향도로도 등록.
- **리버스 프록시 동적 target**: `http-proxy-middleware`의 `target`이 런타임에 결정.
- **Git clone / SVN checkout**: `git clone ${userUrl}` — 특수 URL(`file://`, `ext::`) 가능.
- **`open-uri`** (Ruby) 의 `Kernel#open(url)`: file:// 도 처리.
- **DNS rebinding**: 검증 시점과 요청 시점 사이 DNS 응답이 바뀌는 공격. `127.0.0.1` 검증 후 실제 요청 시 내부 IP. 화이트리스트 검증만으로는 미흡.
- **URL 파싱 차이 (parser confusion)**: `http://evil.com\@127.0.0.1/`을 `URL.parse`/`urlparse`/`Java.net.URL`이 다르게 해석.
- **Redirect 따라가기**: 외부 도메인으로 시작했다가 30x로 내부 IP로 리다이렉트. `followRedirects: true` + 검증을 first hop에서만.
- **gopher://, dict://, file://, ftp://, ldap://** 스킴 (curl/libcurl, PHP `file_get_contents`).
- **이미지 메타데이터 추출 (exiftool)** 입력에 URL.

## 안전 패턴 카탈로그 (FP Guard)

- **Presigned URL 생성**: 서버가 URL 문자열만 만들고 클라이언트에 반환. 서버가 fetch하지 않음.
- **Base URL이 환경변수/상수 + 경로만 사용자 입력**: 그러나 경로 traversal이나 `@` 트릭은 별도 확인.
- **고정 화이트리스트 호스트**: `if (!ALLOWED_HOSTS.includes(parsed.hostname)) reject` — 단, parser confusion 회피 필요.
- **SSRF 방어 라이브러리**: `ssrf-req-filter`, `private-ip`, `is-private-ip` 등이 IP 해석 후 검증.
- **DNS resolution을 직접 수행 후 IP 화이트리스트**: 화이트리스트 통과한 IP만 connect (DNS rebinding 방어).
- **`http://`/`https://` 외 스킴 차단** + Redirect follow 시 매 hop마다 재검증.

## 후보 판정 의사결정

| 조건 | 판정 |
|---|---|
| 사용자 입력 → URL 호스트/스킴 결정 + 검증 없음 | 후보 |
| 사용자 입력 → URL 경로만 결정 (호스트는 상수) + 경로 정규화 없음 | 후보 (라벨: `PATH_ONLY`, 영향도 낮음) |
| 화이트리스트 검증 있으나 DNS resolution 후 검증 안 함 | 후보 (라벨: `DNS_REBINDING`) |
| Redirect follow + first hop만 검증 | 후보 (라벨: `REDIRECT_BYPASS`) |
| Presigned URL 생성 (서버 fetch 없음) | 제외 |
| 사용자 입력이 URL 파라미터(query)에만 들어감, 호스트/경로 고정 | 영향도 낮음, 후보 유지하되 명시 |

## 인접 스캐너 분담

- **OAuth `redirect_uri`** 동적 생성/검증 결함은 **oauth-scanner `REDIRECT_URI_LOOSE`** 단독 담당. 본 스캐너 후보 아님.
- **응답 Location/HTML로 사용자를 리다이렉트**시키는 케이스는 **open-redirect-scanner** 담당. 본 스캐너는 **서버가 직접 fetch**하는 경우만.
- **S3/GCS presigned URL의 동적 호스트** (서버가 SDK로 호출) 는 본 스캐너 단독.

## 후보 판정 제한

사용자 입력이 HTTP 요청의 호스트/스킴을 제어할 수 있는 경우 후보. base URL이 설정 주입이고 경로도 하드코딩이면 제외. 경로에 사용자 입력이 포함되면 후보.
