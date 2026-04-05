> **호출부 추적 — 실제 URL 경로 확정**: 모든 후보에 대해 라우트 정의 파일을 Read로 읽어 실제 URL 경로를 확정한다. 컴포넌트/파일 이름에서 경로를 유추하는 것은 확정이 아니다. 절차: (1) Sink의 호출부를 Grep → 최종 페이지 컴포넌트/컨트롤러 식별 (2) 라우트 정의(routes/index.tsx, @RequestMapping 등)를 Read로 읽어 경로 문자열 확인 (3) 후보 반환 시 근거 포함: `실제 경로: /home/apply (src/routes/index.tsx:42)`

### Phase 1: 정찰 (소스코드 분석)

사용자 입력 → HTTP 응답 헤더 경로를 추적하여 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: 프레임워크/언어/HTTP 라이브러리 버전 확인. 특히 CRLF 방어 여부를 체크:
   - **Node.js**: v4.6.0+ 이후 `http.ServerResponse`에서 헤더 값의 개행 문자 차단 (`ERR_INVALID_CHAR`)
   - **Express**: Node.js 내장 HTTP 모듈을 사용하므로 Node.js 버전에 의존
   - **Next.js**: Node.js 기반이므로 동일
   - **Python/Django**: 1.x 이후 `HttpResponse`에서 헤더 값 개행 차단
   - **Python/Flask/Werkzeug**: 0.9+ 이후 차단
   - **Java/Spring**: 5.x+ 이후 `HttpServletResponse`에서 차단
   - **Ruby/Rails**: 5.x+ 이후 차단
   - **PHP**: 5.1.2+ 이후 `header()` 함수에서 개행 차단 (8.0부터 완전 차단)

2. **Source 식별**: 사용자가 제어 가능한 입력 중 HTTP 헤더에 반영될 수 있는 것
   - HTTP 파라미터가 리다이렉트 URL에 사용되는 경우 (`Location` 헤더)
   - 사용자 입력이 `Set-Cookie` 값에 반영되는 경우
   - 사용자 입력이 커스텀 응답 헤더에 반영되는 경우
   - 사용자 입력이 `Content-Disposition` 헤더 (파일 다운로드명)에 반영되는 경우
   - 사용자 입력이 `Content-Type` 헤더에 반영되는 경우

3. **Sink 식별**: HTTP 응답 헤더를 설정하는 코드
   - **Node.js/Express**: `res.setHeader()`, `res.writeHead()`, `res.header()`, `res.set()`, `res.redirect()`, `res.cookie()`, `res.attachment()`
   - **Next.js**: `ctx.res.setHeader()`, `getServerSideProps`에서 `headers` 설정, `next.config.js`의 `headers()`
   - **Python/Django**: `HttpResponse['Header']`, `response.set_cookie()`, `HttpResponseRedirect()`
   - **Python/Flask**: `response.headers['Header']`, `make_response()`, `redirect()`
   - **Java/Spring**: `response.setHeader()`, `response.addHeader()`, `response.sendRedirect()`
   - **Ruby/Rails**: `response.headers['Header']`, `redirect_to`, `cookies[]`
   - **PHP**: `header()`, `setcookie()`

4. **경로 추적**: Source에서 Sink까지 데이터가 개행 문자 필터링 없이 도달하는 경로 확인. 다음을 점검:
   - 프레임워크/런타임의 내장 CRLF 방어 여부 (버전 확인이 핵심)
   - 사용자 입력에 대한 개행 문자 제거/인코딩 로직
   - URL 인코딩된 CRLF (`%0d%0a`)가 디코딩 후 헤더에 삽입되는지
   - 더블 인코딩 (`%250d%250a`)으로 우회 가능한지

5. **후보 목록 작성**: 각 후보에 대해 "어떤 입력으로 어떻게 헤더를 조작할 수 있는지"를 구체적으로 구상. 프레임워크가 내장 방어를 제공하는 버전이면 후보에서 제외.

## 후보 판정 제한

사용자 입력이 HTTP 응답 헤더에 반영되는 경우 후보. 프레임워크 내장 방어 + 인코딩 적용이 확인되면 제외. 확인 불가하면 후보 유지.
