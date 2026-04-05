
# DOM XSS Scanner

서버를 경유하지 않는 클라이언트사이드 XSS 취약점을 탐지하는 스킬이다. 소스(Source)가 전적으로 브라우저 환경에 존재하고, Sink까지의 데이터 흐름이 서버를 거치지 않는 경우만 이 스킬이 담당한다.

## 범위 정의

**이 스킬이 다루는 것 (DOM XSS):**
- Source가 `location.hash`, `window.name`, `document.referrer`, `postMessage` 등 서버가 관여하지 않는 클라이언트사이드 값
- Sink가 JS 코드에서 직접 DOM을 조작하는 지점 (`innerHTML`, `eval` 등)
- 서버에 페이로드가 도달하지 않아 curl로 재현이 구조적으로 불가능한 경우

**이 스킬이 다루지 않는 것 (xss-scanner 담당):**
- HTTP 파라미터, 폼 필드 등 서버가 수신하는 Source
- 서버 응답에서 사용자 입력이 반영되는 Reflected/Stored XSS
- API 응답 데이터를 `dangerouslySetInnerHTML`로 렌더링하는 경우 (서버 경유)

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

