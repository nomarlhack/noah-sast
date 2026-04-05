> **호출부 추적 — 실제 URL 경로 확정**: 모든 후보에 대해 라우트 정의 파일을 Read로 읽어 실제 URL 경로를 확정한다. 컴포넌트/파일 이름에서 경로를 유추하는 것은 확정이 아니다. 절차: (1) Sink의 호출부를 Grep → 최종 페이지 컴포넌트/컨트롤러 식별 (2) 라우트 정의(routes/index.tsx, @RequestMapping 등)를 Read로 읽어 경로 문자열 확인 (3) 후보 반환 시 근거 포함: `실제 경로: /home/apply (src/routes/index.tsx:42)`

### Phase 1: 정찰 (소스코드 분석)

사용자 입력 → 리다이렉트 대상 URL 경로를 추적하여 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: package.json, Gemfile, requirements.txt 등에서 프레임워크/언어 확인

2. **Source 식별**: 사용자가 제어 가능한 입력 중 리다이렉트 URL로 사용될 수 있는 것

   **직접 소스** (요청 시점에 공격자가 제어 가능):
   - HTTP 파라미터: `redirect`, `redirectUrl`, `returnUrl`, `return_to`, `next`, `url`, `goto`, `target`, `destination`, `continue`, `callback`, `redir`, `redirect_uri`, `return`, `out`, `link`
   - HTTP Referer 헤더
   - URL 경로 자체 (catch-all 라우트)

   **간접 소스** (이전 단계에서 저장된 값을 경유):
   - 쿠키에 저장된 redirect URL
   - 세션에 저장된 redirect URL
   - DB에 저장된 URL (프로필 URL, 콜백 URL 등)

   간접 소스는 "리다이렉트 Sink에서 값을 읽는 시점"이 아니라 "그 값이 최초로 저장되는 시점"까지 추적해야 한다. 자세한 분석 방법은 아래 "간접 소스 공격 체인 검증"을 참고한다.

3. **Sink 식별**: 리다이렉트를 수행하는 코드

   **서버사이드:**
   - **Node.js/Express**: `res.redirect()`, `res.writeHead(302, {location: url})`, `res.setHeader('Location', url)`
   - **Next.js**: `getServerSideProps`에서 `redirect: { destination: url }`, `ctx.res.writeHead(302)`
   - **Python/Django**: `HttpResponseRedirect()`, `redirect()`, `RedirectView`
   - **Python/Flask**: `redirect()`, `make_response()` with Location header
   - **Java/Spring**: `RedirectView`, `redirect:` prefix, `HttpServletResponse.sendRedirect()`
   - **Ruby/Rails**: `redirect_to`, `redirect_back`
   - **PHP**: `header('Location: ' . $url)`
   - **HTML**: `<meta http-equiv="refresh" content="0; url=...">`

   **클라이언트사이드:**
   - `window.location.href = url`
   - `window.location.replace(url)`
   - `window.location.assign(url)`
   - `window.location = url`
   - `window.open(url)`
   - `document.location = url`
   - `form.action = url` + `form.submit()`
   - `<a href={url}>` (React에서 사용자 입력이 href에 직접 삽입되는 경우)

   **커스텀 네비게이션 함수 판정 기준:**
   URL을 인자로 받아 해당 URL의 콘텐츠를 로드하거나 해당 URL로 이동하는 모든 함수는 리다이렉트 Sink이다. 브라우저 표준 API뿐 아니라 앱 네이티브 브리지, WebView API, iframe src 할당, 커스텀 네비게이션 함수를 포함한다. 함수명이나 타입 정의에서 첫 번째 인자가 URL이고 페이지 로드/이동 동작을 수행하면 Sink로 판정한다. 목록에 없다는 이유로 제외하지 않는다.

4. **경로 추적**: Source에서 Sink까지 데이터가 URL 검증 없이 도달하는 경로 확인. 다음을 점검:
   - URL 검증 로직 존재 여부 (도메인 화이트리스트, 프로토콜 제한 등)
   - 상대 경로만 허용하는지 (절대 URL 차단)
   - `//evil.com` 같은 프로토콜 상대 URL 차단 여부
   - URL 파싱 우회 가능 여부 (`https://allowed.com@evil.com`, `https://allowed.com.evil.com` 등)

5. **간접 소스 공격 체인 검증**: 리다이렉트 URL이 쿠키, 세션, DB 등 간접 소스에서 오는 경우, 공격자가 피해자의 브라우저에서 해당 값을 외부 URL로 설정할 수 있는 체인이 존재하는지 반드시 검증한다.

   Open Redirect의 핵심은 "공격자가 피해자에게 피싱 URL을 전달하여 외부 도메인으로 이동시키는 것"이다. 쿠키/세션/DB 기반 리다이렉트는 공격자가 해당 값을 피해자 브라우저에 설정할 수 있는 방법이 없으면 실질적인 Open Redirect가 아니다.

   **검증 절차:**
   1. 간접 소스 값이 **최초로 저장되는 코드**를 모두 찾는다 (예: `setCookie(key, value)`, `session[:return_to] = url`, DB INSERT/UPDATE)
   2. 저장되는 값의 원본이 무엇인지 추적한다:
      - `location.href` (현재 페이지 URL) → 항상 같은 도메인이므로 공격자가 외부 URL을 삽입 불가 → **안전, 제외**
      - URL 파라미터 (`params[:redirect_url]`) → 공격자가 URL에 포함시켜 피해자에게 전달 가능 → **취약**
      - 하드코딩된 값 → **안전, 제외**
      - 서버 응답 데이터 → 공격자가 직접 제어 불가 (별도 백엔드 취약점 필요) → **안전, 제외**
   3. 취약한 체인이 존재하는 경우에만 후보로 보고한다. 구체적인 공격 시나리오를 기술할 때 "값 저장 단계 → 리다이렉트 단계"의 전체 흐름을 포함한다.
   4. 안전한 체인만 존재하는 경우, 해당 항목은 보고서에서 제외한다.

   **예시 - 취약한 체인:**
   ```
   1단계: GET /login?return_to=https://evil.com
          → 서버가 session[:return_to] = params[:return_to] 저장
   2단계: OAuth 인증 완료 후 redirect_to session[:return_to]
   → 공격자가 1단계 URL을 피해자에게 전달하면 전체 체인 성립
   ```

   **예시 - 안전한 체인:**
   ```
   1단계: JS에서 setCookie('redirect', location.href)
          → location.href는 현재 페이지(같은 도메인)이므로 외부 URL 불가
   2단계: OAuth 인증 완료 후 redirect_to cookies[:redirect]
   → 쿠키 값이 항상 같은 도메인이므로 공격자가 외부 URL을 삽입할 체인 없음
   ```

6. **후보 목록 작성**: 각 후보에 대해 "어떤 입력으로 어떻게 외부 도메인 리다이렉트를 유발할 수 있는지"를 구체적으로 구상. 데이터 흐름 추적을 완료한 뒤에도 공격 경로가 없으면 버린다. 추적 없이 직관으로 버리지 않는다..

## 후보 판정 제한

사용자 입력이 리다이렉트 대상에 반영되는 경우 후보. 서버 응답 URL이 source인 경우, 서버 코드에서 URL 검증이 확인되면 제외. 확인 불가하면 후보 유지.
