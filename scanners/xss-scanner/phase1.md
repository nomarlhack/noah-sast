> **호출부 추적 — 실제 URL 경로 확정**: 모든 후보에 대해 라우트 정의 파일을 Read로 읽어 실제 URL 경로를 확정한다. 컴포넌트/파일 이름에서 경로를 유추하는 것은 확정이 아니다. 절차: (1) Sink의 호출부를 Grep → 최종 페이지 컴포넌트/컨트롤러 식별 (2) 라우트 정의(routes/index.tsx, @RequestMapping 등)를 Read로 읽어 경로 문자열 확인 (3) 후보 반환 시 근거 포함: `실제 경로: /home/apply (src/routes/index.tsx:42)`

### Phase 1: 정찰 (소스코드 분석)

기존의 Source → Sink 추적 방식으로 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: package.json, Gemfile 등에서 프레임워크/언어 확인. 특히 **렌더링 구조를 판별**한다:
   - **SPA (React/Vue/Angular 등)**: 서버는 JSON API만 제공하고 프론트엔드 JS가 HTML을 렌더링 → **XSS Sink는 프론트엔드 JS 코드에 집중**
   - **SSR (전통적 서버사이드 렌더링)**: 서버 템플릿(ERB, Slim, Jinja2, JSP 등)이 HTML을 렌더링 → XSS Sink는 서버사이드 코드에 집중
   - **하이브리드 (SSR + SPA 혼합)**: 양쪽 모두 검색 필요

   SPA 프로젝트에서 서버사이드 헬퍼에 `html_safe`가 있어도, 그 헬퍼가 실제로 호출되지 않으면 현재 공격 가능한 취약점이 아니다. **"서버에 위험 코드가 있으니 후보"로 멈추지 말고, 실제 렌더링을 담당하는 프론트엔드 코드를 반드시 분석한다.**

2. **Source 식별**: 사용자가 제어 가능한 입력 진입점 (HTTP 파라미터, URL, Cookie, 클립보드, location 등). SPA에서는 API 응답 데이터도 Source에 해당한다. 누가 입력했는지(일반 사용자, 관리자, 파트너, 외부 시스템 등)와 관계없이, **DB를 거쳐 API 응답으로 돌아오는 모든 데이터는 Source로 취급한다.**

3. **Sink 식별**: 서버사이드와 프론트엔드 **양쪽 모두**에서 Sink를 검색한다. 어느 한쪽만 검색하고 넘어가지 않는다.

   **3-A. 프론트엔드 Sink 검색 (SPA/하이브리드 프로젝트에서 필수)**:
   프론트엔드 JS/TS 코드 디렉토리(`app/assets/javascripts/`, `src/`, `pages/`, `components/`, `public/` 등)에서 다음 패턴을 grep한다:

   | 프레임워크 | Sink 패턴 |
   |-----------|----------|
   | React | `dangerouslySetInnerHTML` |
   | Vue | `v-html` |
   | Angular | `[innerHTML]`, `bypassSecurityTrustHtml` |
   | jQuery | `.html(`, `.append(`, `.prepend(`, `.after(`, `.before(`, `.replaceWith(` (변수가 인자인 경우) |
   | Vanilla JS | `innerHTML`, `outerHTML`, `document.write(`, `insertAdjacentHTML(` |
   | iframe | `srcDoc` (sandbox 속성 없으면 same-origin으로 JS 실행 가능) |
   | 공통 | `eval(`, `Function(`, `setTimeout(문자열)`, `setInterval(문자열)` |

   **Sink 목록 수집 절차 (필수):**
   1단계: 위 테이블의 Sink 패턴을 소스코드 전체에서 grep하여 파일 목록을 수집한다.
          **이 단계에서는 grep 결과를 판단·필터링 없이 전부 수집한다.**
          "즉시 취약해 보이지 않는다", "renderToStaticMarkup 내부라서 DOM에 직접 삽입 안 된다",
          "SSR 컴포넌트라서 브라우저에서 실행 안 된다" 등의 이유로 파일을 목록에서 제외하지 않는다.
          취약 여부 판단은 2단계(파일 분석) 이후에만 내릴 수 있다.
   2단계: 목록의 각 파일을 순서대로 직접 열어 데이터 흐름을 추적한다.
   → 같은 이름의 컴포넌트를 다른 파일에서 이미 분석했더라도 2단계는 파일별로 반드시 실행한다.

   **[필수] 파일 분석 중 패턴 인덱스에 없는 다른 Sink를 발견한 경우:** 해당 Sink도 즉시 분석한다. "별도 항목에 해당"이라며 분석을 미루거나 다른 스캐너에 위임하지 않는다. phase1.md의 Sink 테이블에 정의된 Sink라면 발견 경위와 무관하게 이 스캐너에서 분석을 완료한다.

   각 Sink에 대해 **삽입되는 데이터의 출처**를 추적한다. 특히:
   - API 응답 데이터를 `dangerouslySetInnerHTML`로 렌더링하는 경우 → 해당 API 응답에 사용자 입력이 포함되는지 확인
   - 에디터/글쓰기 컴포넌트에서 `$(el).html(content)` 패턴 → content가 어디서 오는지 추적
   - 모달/알림에서 `dangerouslySetInnerHTML={{__html: message}}` → message가 사용자 입력을 포함하는지 확인
   - 같은 컴포넌트 내에서 `escapeHtml()` 등 이스케이프가 적용되는지 확인한다.
   - **`dangerouslySetInnerHTML`이 `ReactDOMServer.renderToStaticMarkup()` / `renderToString()` 내부에서 발견된 경우**: 해당 컴포넌트 분석에서 멈추지 않는다. `renderToStaticMarkup()` 호출 결과를 받는 변수를 찾아, 그 변수가 `$(el).html()` / `innerHTML` / 다른 `dangerouslySetInnerHTML`로 전달되는 경로가 있는지 반드시 추적한다. 또한 중간에 `stripTags` 등 필터가 있더라도 허용 태그(`<img>`, `<a>` 등)에 이벤트 핸들러 속성이 통과되는지 확인한다.

   **`srcDoc` Sink 판정:** `sandbox` 속성이 없거나 `allow-scripts allow-same-origin` 동시 포함 → 후보.

   **[필수] "API 응답 = 서버 데이터 = 안전" 판단 금지:**
   데이터가 서버 API 응답에서 온다는 사실만으로 Sink를 후보에서 제외하지 않는다. API 응답의 특정 필드는 사용자가 제출한 값을 그대로 저장한 것일 수 있다. 제외하려면 서버사이드 컨트롤러 코드에서 해당 파라미터에 대한 검증·sanitize 로직을 직접 확인하여 근거를 명시해야 한다. 코드 확인 없이 "서버에서 오므로 안전"으로 판단하는 것은 허용하지 않는다.

   **3-B. 서버사이드 Sink 검색**:
   서버사이드 코드에서 이스케이프 없이 출력되는 지점을 검색한다:

   | 프레임워크 | Sink 패턴 |
   |-----------|----------|
   | Rails | `html_safe`, `raw()`, `<%== %>` (ERB), `==` (Slim, 이중 등호) |
   | Django | `\|safe`, `mark_safe()`, `{% autoescape off %}` |
   | Spring | `th:utext` (Thymeleaf), JSP `<%= %>` without `c:out` |
   | Express | `res.send(userInput)` (Content-Type: text/html) |

   **Sink 목록 수집 절차 (필수):**
   1단계: 위 테이블의 Sink 패턴을 소스코드 전체에서 grep하여 파일 목록을 수집한다.
          **이 단계에서는 grep 결과를 판단·필터링 없이 전부 수집한다.**
          "즉시 취약해 보이지 않는다", "헬퍼가 호출되지 않을 것 같다" 등의 이유로
          파일을 목록에서 제외하지 않는다. 취약 여부 판단은 2단계 이후에만 내릴 수 있다.
   2단계: 목록의 각 파일을 순서대로 직접 열어 데이터 흐름을 추적한다.
   → 같은 이름의 함수/헬퍼를 다른 파일에서 이미 분석했더라도 2단계는 파일별로 반드시 실행한다.

   파일명·함수명·맥락만 보고 넘기지 않는다. Sink가 직접 변수를 참조하면 그 변수가 어떻게 조립되는지(중간 변환 로직, 문자열 조립, 정규식 replace 등)를 반드시 코드에서 읽어 확인한다.

4. **경로 추적**: Sink 목록의 각 항목에 대해 실제 코드를 읽으며 Source까지 역방향으로 데이터 흐름을 추적한다. 추적 완료 전에 "이건 안전할 것 같다"는 직관으로 건너뛰지 않는다.
5. **후보 목록 작성**: 추적 결과를 바탕으로 취약해 보이는 코드 위치와 예상 공격 벡터를 정리한다. 데이터 흐름 추적을 완료한 뒤에도 사용자가 제어 가능한 입력이 Sink에 도달하는 경로가 없는 것이 코드에서 확인된 경우에만 목록에서 제외한다. 추적하지 않고 직관으로 제외하지 않는다.

## 후보 판정 제한

**서버 내부 설정값**(환경변수, 하드코딩 상수, 인프라 설정)이 source인 경우에만 제외. 그 외 모든 입력(일반 사용자, 관리자, 파트너, 외부 API, 연동 시스템 등)이 source인 경우 후보.
