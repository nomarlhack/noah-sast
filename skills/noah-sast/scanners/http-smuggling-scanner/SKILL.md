
# HTTP Request Smuggling Scanner

소스코드 및 인프라 설정을 분석하여 HTTP Request Smuggling 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 프론트엔드와 백엔드 간 요청 경계 불일치가 발생하는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "요청 경계 불일치가 발생하지 않으면 취약점이 아니다"

프록시와 백엔드 서버가 있다고 바로 취약점으로 보고하지 않는다. 실제로 `Content-Length`와 `Transfer-Encoding` 헤더의 해석 차이로 인해 하나의 HTTP 요청 안에 숨겨진 두 번째 요청이 백엔드에서 별도로 처리되는 것을 확인해야 취약점이다.

## HTTP Request Smuggling의 유형

### CL.TE (Content-Length → Transfer-Encoding)
프론트엔드가 `Content-Length`를 우선하고, 백엔드가 `Transfer-Encoding: chunked`를 우선하는 경우. 프론트엔드는 `Content-Length`만큼 데이터를 전달하지만, 백엔드는 chunked 인코딩 종료(`0\r\n\r\n`) 이후의 데이터를 다음 요청의 시작으로 해석한다.

### TE.CL (Transfer-Encoding → Content-Length)
프론트엔드가 `Transfer-Encoding: chunked`를 우선하고, 백엔드가 `Content-Length`를 우선하는 경우. 프론트엔드는 chunked 종료까지 전달하지만, 백엔드는 `Content-Length`만큼만 읽고 나머지를 다음 요청으로 해석한다.

### TE.TE (Transfer-Encoding 혼동)
프론트엔드와 백엔드 모두 `Transfer-Encoding`을 처리하지만, 변형된 헤더(`Transfer-Encoding: chunked`, `Transfer-Encoding : chunked`, `Transfer-Encoding: xchunked` 등)에 대한 처리가 다른 경우.

### HTTP/2 Downgrade Smuggling (H2.CL / H2.TE)
프론트엔드가 HTTP/2를 처리하고 백엔드로 HTTP/1.1로 변환(downgrade)할 때, HTTP/2의 `:content-length` 의사 헤더와 변환된 HTTP/1.1의 헤더 간 불일치가 발생하는 경우.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

