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

5. **후보 목록 작성**: 각 후보에 대해 아래 "후보 판정 절차"를 반드시 거친 뒤 보고한다. 메서드/입력 위치만으로 self-redirect 단정하지 않고, 응답값/저장소 값은 반드시 원본 Source까지 역추적한다. 데이터 흐름 추적을 완료한 뒤에도 공격 경로가 없으면 버린다. 추적 없이 직관으로 버리지 않는다.

---

## 후보 판정 절차

### Step A: Sink 식별

URL 기반 리다이렉트/네비게이션을 수행하는 모든 Sink를 식별한다. (위 3번 항목과 동일)

### Step B: Sink 입력값의 직접 출처 확인

Sink에 도달하는 값이 다음 중 어디에서 오는지 분류한다:
- (B1) 현재 요청의 query/path/body/header
- (B2) 세션/쿠키/캐시/DB 등 저장소
- (B3) 외부 API 응답값
- (B4) 상수/하드코딩

(B1)이면 Step D로 직진. (B2)~(B3)이면 Step C 역추적 필수. (B4)이면 안전, 종료.

### Step C: Source 역추적 (필수, 깊이 제한 없음)

값의 생성 경로를 따라간다. 다음 조건 중 하나에 도달할 때까지 계속한다:

1. **외부 입력 Source 도달**: HTTP 파라미터/헤더/body, 환경변수 등 → Step D로 진행
2. **상수/하드코딩 값 도달**: 추적 종료, "안전"
3. **이미 방문한 (파일경로:라인) 재방문**: 순환 참조, "추적 한계"로 기록 후 종료
4. **외부 의존성 경계 도달** (외부 라이브러리, 외부 마이크로서비스, 외부 SaaS):
   - 내부 구현은 추적하지 않는다.
   - 단, 그 외부로 **보내는 인자**가 사용자 제어 가능한지 점검한다. 점검 범위는 다음으로 한정한다:
     - Sink로 흘러들어온 값을 생성한 외부 호출문(예: `client.call(arg=...)`)의 인자 표현식
     - 그 인자 표현식이 참조하는 변수의 직전 대입문(같은 함수 스코프 내에서 1회 추적)
   - 인자가 사용자 제어 입력에 닿으면 해당 인자의 Source를 Step D 매트릭스에 입력한다.
   - 인자가 상수/내부 식별자만 포함하면 종료, "안전".

저장소(세션/DB 등) 경로의 경우, 저장소에 값을 쓰는 모든 코드 위치를 Grep으로 찾아 각 쓰기 위치의 입력 출처를 동일한 종료 조건까지 추적한다.

방문한 (파일경로:라인) 집합으로 순환만 막는다. 단계 수는 제한하지 않는다.

### Step D: 트리거 매트릭스 (악용 가능성 분류)

역추적 종점의 최종 Source 위치를 기준으로 분류한다. 이 매트릭스는 **위험도가 아니라 트리거 가능성**을 표현한다. 라벨이 작을수록 위험하다는 의미가 아니다.

| 입력 위치 | HTTP 메서드 | 트리거 라벨 | 외부 공격자 트리거 경로 |
|-----------|------------|-----------|---------------------|
| Query string / URL fragment | GET | `LINK` | 링크 1개로 피해자 트리거 |
| Form body | POST (`application/x-www-form-urlencoded`, `multipart/form-data`) | `FORM` | auto-submit `<form>` (CSRF형) |
| JSON/XML body | POST/PUT/DELETE (`application/json` 등) | `SCRIPT` | preflight 발생, 동일 origin 코드 실행 필요 |
| Header (Referer/Host/Custom) | 무관 | `HEADER` | 직접 HTTP 클라이언트 필요 |
| 인증된 사용자 자신의 입력 | 무관 | `SELF` | 공격자 자신이 입력 (2차 피해자에게 노출되는 Stored 패턴이면 별도 표시) |
| 역추적 종점 도달 못함 | - | `UNKNOWN` | Step C-3 (순환/외부 경계에서 결정 불가) |

### Step E: 트리거 가능성 보정

매트릭스 라벨은 기본값일 뿐이다. 다음 조건을 확인하여 라벨을 보정한다:

- **CSRF 토큰 미적용**: `FORM` 라벨이 사실상 `LINK` 수준으로 격상
- **CORS 정책에서 cross-origin + credentials 허용**: `SCRIPT` 라벨이 사실상 `LINK` 수준으로 격상
- **SameSite=None 또는 미설정 + 쿠키 인증**: `FORM` 라벨이 격상 (Lax/Strict면 유지)
- **Bearer 토큰/Authorization 헤더 인증**: SameSite와 무관, `FORM`/`SCRIPT`도 격상
- **모바일 앱/서버 간 호출이 1차 사용자**: `HEADER` 라벨이 격상 (헤더 변조 자유)
- **CDN/프록시가 헤더를 다시 쓰는 경로**: `HEADER` 라벨이 격상

보정 결과는 보고서에 명시한다 (`SCRIPT → LINK (CORS *,credentials)` 형식).

### Step F: 위협 모델 명시

각 후보에 다음 위협 모델 중 적용되는 것을 모두 표시한다. 단일 모델만 가정하지 않는다.

- **외부 공격자 → 일반 사용자**: 매트릭스 기본 가정
- **악의적 내부자 / 침해된 파트너**: `SELF`/`HEADER` 라벨이라도 위험할 수 있음
- **악의적 사용자 → 다른 사용자 (Stored)**: 한 사용자가 등록한 URL이 다른 사용자에게 노출되는지 확인. Step C에서 저장소 경로가 발견되었고, 읽는 측이 다른 사용자라면 자동 적용
- **서버 간 호출 (S2S)**: 인증된 내부 시스템이 호출 주체. 내부 시스템 침해/오용 시나리오에서만 활성화

### Step G: 판정 및 보고

다음 두 차원을 모두 고려하여 판정한다:

| 보정 후 라벨 | 적용 위협 모델 있음 | 판정 |
|------------|-----------------|------|
| `LINK` | 임의 | **후보 유지** |
| `FORM` (보정 전) | 외부 공격자 | **후보 유지** (보정 결과를 명시) |
| `SCRIPT` (보정 전) | 외부 공격자만 해당 | **후보 제외 가능** (단, 동일 페이지에 XSS 후보 존재 시 "체인 후보"로 유지) |
| `SCRIPT` (보정 후 격상) | 임의 | **후보 유지** |
| `HEADER` | 외부 공격자만 해당 | **후보 제외 가능** |
| `HEADER` (보정 후 격상 또는 S2S/내부자 모델) | 적용 모델 있음 | **후보 유지** |
| `SELF` | Stored 모델 활성화 | **후보 유지** (2차 피해자 대상) |
| `SELF` | Stored 미적용 | **후보 제외** |
| `UNKNOWN` | 임의 | **추적 한계 후보**로 별도 분류 (보고서 별도 섹션) |

**"추적 한계 후보"는 일반 후보와 분리한다.** 분석가가 추적을 회피하는 도피처로 사용되지 않도록, 다음을 함께 명시해야 한다:
- 어디서 추적이 멈췄는가 (파일:라인)
- 멈춘 사유 (Step C의 어느 종료 조건)
- 추가 정보가 있을 경우 후보 재평가가 가능한지

보고서에는 모든 후보에 대해 다음을 기재한다:
1. Source 역추적 경로 (단계별 파일:라인)
2. 최종 도달 Source 위치 + 매트릭스 라벨 (보정 전/후)
3. 적용된 위협 모델 목록
4. 판정 근거 (제외/유지 결정의 근거를 명시)
