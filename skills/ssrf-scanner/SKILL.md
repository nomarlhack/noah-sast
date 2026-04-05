---
name: ssrf-scanner
description: "소스코드 분석과 동적 테스트를 통해 SSRF(Server-Side Request Forgery) 취약점을 탐지하는 스킬. 사용자 입력이 서버사이드 HTTP 요청의 URL에 반영되는 경로를 추적하고, 실제로 내부 네트워크나 임의 외부 호스트로 요청이 발생하는지 검증한다. 사용자가 'SSRF 취약점 찾아줘', 'SSRF 스캔', 'SSRF 점검', 'ssrf audit', 'ssrf 검사', '서버사이드 요청 위조' 등을 요청할 때 이 스킬을 사용한다."
grep_patterns:
  - "axios"
  - "node-fetch"
  - "http\\.get("
  - "https\\.get("
  - "http\\.request("
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
  - "requests\\.get("
  - "requests\\.post("
  - "OkHttpClient"
  - "Retrofit"
  - "HttpClient"
  - "fetch("
  - "got("
  # Source patterns
  - "searchParams\\.get("
  - "@RequestParam"
  - "@RequestBody"
  - "req\\.query"
  - "req\\.body"
---

# SSRF Scanner

소스코드 분석으로 SSRF 취약점 후보를 식별한 뒤, 동적 테스트로 서버가 실제로 공격자가 지정한 주소로 요청을 보내는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "서버가 요청을 보내지 않으면 취약점이 아니다"

소스코드에서 `axios.get(userInput)`이 있다고 바로 SSRF로 보고하지 않는다. 실제로 사용자가 제어한 URL로 서버가 HTTP 요청을 보내는 것을 확인해야 취약점이다.

가정 기반의 취약점 보고는 도움이 되지 않는다. "내부 API가 노출되면 위험", "클라우드 메타데이터에 접근 가능할 수 있음" 같은 가정은 취약점이 아니라 아키텍처 의견이다. 사용자가 제어하는 입력으로 서버가 의도하지 않은 목적지로 요청을 보내도록 만들 수 있어야 한다.

## SSRF의 유형

### Basic SSRF
사용자 입력 URL로 서버가 직접 요청을 보내고, 그 응답이 사용자에게 반환되는 경우. 응답 내용을 통해 내부 네트워크 정보를 탈취할 수 있다.

### Blind SSRF
서버가 요청을 보내지만 응답 내용이 사용자에게 반환되지 않는 경우. 서버가 요청을 보냈는지는 외부 콜백(webhook.site 등)이나 응답 시간 차이로 확인한다.

### Partial SSRF
URL의 일부(호스트명, 경로, 포트 등)만 제어 가능한 경우. URL 파싱 차이를 이용한 우회가 핵심이다.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 이 스킬과 같은 skills 디렉토리 내의 `noah-sast/agent-guidelines.md`를 참조한다. 이 파일의 위치를 기준으로 `../noah-sast/agent-guidelines.md` 경로로 접근할 수 있다.
