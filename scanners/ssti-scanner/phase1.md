> ## 핵심 원칙: "템플릿 표현식이 실행되지 않으면 취약점이 아니다"
>
> 소스코드에서 템플릿 엔진을 사용한다고 바로 SSTI로 보고하지 않는다. SSTI는 사용자 입력이 **템플릿 문자열 자체**에 삽입되어 템플릿 엔진이 이를 코드로 해석·실행하는 경우에만 발생한다. 템플릿의 **변수**로 전달되는 것은 SSTI가 아니다.
>
> ```
> # 안전 — 사용자 입력이 변수로 전달됨
> render('hello.ejs', { name: userInput })
>
> # 위험 — 사용자 입력이 템플릿 문자열에 삽입됨
> ejs.render('Hello ' + userInput)
> ```
>

### Phase 1: 정찰 (소스코드 분석)

사용자 입력 → 템플릿 문자열 삽입 경로를 추적하여 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: 프레임워크/언어/템플릿 엔진 확인

2. **템플릿 엔진 식별**: 사용 중인 템플릿 엔진과 구문 확인

   | 엔진 | 언어 | 표현식 구문 | 테스트 페이로드 |
   |------|------|------------|----------------|
   | Jinja2 | Python | `{{ }}`, `{% %}` | `{{7*7}}` → `49` |
   | Mako | Python | `${expression}` | `${7*7}` → `49` |
   | Django Template | Python | `{{ }}`, `{% %}` | `{{7*7}}` (제한적, 기본 안전) |
   | EJS | Node.js | `<%= %>`, `<%- %>` | `<%= 7*7 %>` → `49` |
   | Pug/Jade | Node.js | `#{expression}` | `#{7*7}` → `49` |
   | Nunjucks | Node.js | `{{ }}`, `{% %}` | `{{7*7}}` → `49` |
   | Handlebars | Node.js | `{{ }}` | 기본적으로 안전 (헬퍼만 호출 가능) |
   | ERB | Ruby | `<%= %>` | `<%= 7*7 %>` → `49` |
   | Thymeleaf | Java | `${expression}` | `${7*7}` → `49` |
   | Freemarker | Java | `${expression}` | `${7*7}` → `49` |
   | Velocity | Java | `$expression` | `$class.forName('java.lang.Runtime')` |
   | Twig | PHP | `{{ }}`, `{% %}` | `{{7*7}}` → `49` |
   | Smarty | PHP | `{expression}` | `{7*7}` → `49` |

3. **Source 식별**: 사용자가 제어 가능한 입력
   - HTTP 파라미터가 템플릿 렌더링에 사용되는 경우
   - URL 경로가 템플릿에 삽입되는 경우
   - 이메일 템플릿에 사용자 입력이 삽입되는 경우
   - 에러 페이지에 사용자 입력이 반영되는 경우
   - CMS에서 사용자가 작성한 콘텐츠가 템플릿으로 처리되는 경우

4. **Sink 식별**: 사용자 입력이 템플릿 문자열에 직접 삽입되는 코드

   **Node.js (EJS):**
   - `ejs.render(userInput)` — 위험: 사용자 입력을 템플릿으로 실행
   - `ejs.render('Hello ' + userInput)` — 위험: 문자열 연결
   - `ejs.render(template, { name: userInput })` — 안전: 변수로 전달
   - `res.render('template', { name: userInput })` — 안전: 파일 템플릿 + 변수

   **Node.js (Pug/Nunjucks):**
   - `pug.render(userInput)` — 위험
   - `nunjucks.renderString(userInput)` — 위험
   - `nunjucks.renderString(template, { name: userInput })` — 주의: template이 고정이면 안전

   **Python (Jinja2):**
   - `Template(userInput).render()` — 위험: 사용자 입력을 템플릿으로 실행
   - `render_template_string(userInput)` — 위험 (Flask)
   - `render_template_string('Hello ' + userInput)` — 위험: 문자열 연결
   - `render_template('template.html', name=userInput)` — 안전: 파일 템플릿 + 변수

   **Python (Mako):**
   - `Template(userInput).render()` — 위험
   - `template.render(name=userInput)` — 안전: 변수로 전달

   **Java (Thymeleaf):**
   - `templateEngine.process(userInput, context)` — 위험: 사용자 입력을 템플릿으로 처리
   - Spring에서 컨트롤러 반환값에 사용자 입력이 삽입되는 경우 — 위험

   **Java (Freemarker):**
   - `new Template("name", new StringReader(userInput), cfg)` — 위험
   - `template.process(dataModel, out)` where dataModel contains userInput — 안전: 변수로 전달

   **Ruby (ERB):**
   - `ERB.new(userInput).result` — 위험
   - `ERB.new(template).result_with_hash(name: userInput)` — 안전: 변수로 전달

   **PHP (Twig):**
   - `$twig->createTemplate(userInput)->render()` — 위험
   - `$twig->render('template.html', ['name' => userInput])` — 안전: 파일 템플릿 + 변수

5. **경로 추적**: Source에서 Sink까지 사용자 입력이 **템플릿 문자열 자체**에 삽입되는지 확인. 핵심 구분:
   - 사용자 입력이 `render(template, {variable: input})`의 **variable**로 전달되면 안전
   - 사용자 입력이 `render(input)` 또는 `render('...' + input)`의 **template**에 삽입되면 위험
   - 파일 기반 템플릿(`render('template.html', data)`)은 사용자가 파일 경로를 제어하지 않는 한 안전

6. **후보 목록 작성**: 각 후보에 대해 "어떤 입력으로 어떻게 템플릿 표현식을 실행할 수 있는지"를 구체적으로 구상. 데이터 흐름 추적을 완료한 뒤에도 공격 경로가 없으면 버린다. 추적 없이 직관으로 버리지 않는다..

## 후보 판정 제한

서버사이드 템플릿 엔진의 렌더링 함수에 사용자 입력이 템플릿 문자열로 삽입되는 경우만 후보. 템플릿 엔진과 무관한 클래스는 제외.
