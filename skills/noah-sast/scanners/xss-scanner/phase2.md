### Phase 2: 동적 테스트 (검증)

Phase 1 소스코드 분석이 완료되면 후보 목록을 사용자에게 보여준다. 후보가 존재하는 경우에만 동적 테스트를 진행한다. 후보가 0건이면 동적 테스트 없이 바로 보고서를 작성한다.

**동적 테스트 정보 획득:**

사용자에게는 테스트 대상 도메인(Host)과 직접 획득이 불가능한 정보(외부 콜백 서비스 URL, 프로덕션 전용 자격 증명 등)만 요청한다. 그 외의 정보는 소스코드 분석 또는 관련 엔드포인트에 직접 HTTP 요청을 보내 획득한다.

사용자가 동적 테스트를 원하지 않거나 정보를 제공하지 않으면, 소스코드 분석 결과의 모든 후보를 "후보"로 유지한 채 Phase 3으로 진행한다.

**도구 선택 기준: 렌더링 방식에 따라 결정한다**

XSS 유형(Reflected/Stored/DOM)이 아니라 **Sink가 서버사이드에서 렌더링되는가, 클라이언트사이드에서 렌더링되는가**에 따라 도구를 선택한다.

| 렌더링 방식 | 도구 | 판정 근거 |
|------------|------|----------|
| 서버사이드 렌더링 (ERB, Slim, Jinja2 등 템플릿이 HTML 생성) | **curl** | HTTP 응답 본문에서 페이로드 이스케이프 여부 직접 확인 가능 |
| 클라이언트사이드 렌더링 (React `dangerouslySetInnerHTML`, Vue `v-html`, jQuery `.html()` 등 브라우저 JS가 DOM 조작) | **Playwright** | curl은 JSON API 응답만 반환하므로 DOM 렌더링 결과를 확인할 수 없음 |

**curl 테스트 (서버사이드 렌더링):**
1. curl로 XSS 페이로드가 포함된 요청을 전송
2. `Content-Type: text/html` 응답 본문에서 페이로드가 이스케이프 없이 반영되는지 확인
3. Stored XSS의 경우: 페이로드 저장 요청 → 해당 데이터를 출력하는 HTML 페이지 요청 → 응답 본문 확인
4. **JSON API 응답만 확인하고 끝내지 않는다.** `html_safe`, `raw` 등으로 인한 XSS는 HTML 뷰에서 발생하므로, 반드시 HTML 페이지(`Accept: text/html`)를 요청하여 확인한다.

**Playwright 테스트 (클라이언트사이드 렌더링):**

SPA/React 프로젝트에서 `dangerouslySetInnerHTML`, jQuery `.html()` 등 클라이언트사이드 Sink가 관여하는 경우, Stored XSS라도 브라우저 실행 없이는 검증할 수 없다. 반드시 Playwright를 사용한다.

```javascript
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  let alertFired = false;
  let alertMessage = '';

  page.on('dialog', async dialog => {
    alertFired = true;
    alertMessage = dialog.message();
    await dialog.dismiss();
  });

  // 세션 쿠키 설정
  await context.addCookies([
    { name: 'SESSION', value: '<세션값>', domain: '<대상도메인>', path: '/' }
  ]);

  // 페이로드가 렌더링되는 페이지 방문
  await page.goto('https://<대상>/path');
  await page.waitForTimeout(2000);

  if (alertFired) {
    console.log('XSS 확인됨:', alertMessage);
  } else {
    const dangerous = await page.evaluate(() =>
      document.body.innerHTML.includes('<img src=x')
    );
    console.log('DOM 삽입 여부:', dangerous);
  }

  await browser.close();
})();
```

Stored XSS Playwright 테스트 절차:
1. curl로 페이로드 저장 (`<img src=x onerror=alert(document.domain)>`)
2. Playwright로 해당 데이터를 렌더링하는 페이지 방문
3. `alert()` 발화 또는 페이로드가 이스케이프 없이 DOM에 삽입되는지 확인

**순수 DOM XSS (서버 미경유) 테스트:**
- Source가 `location.hash`, `window.name`, `postMessage` 등 서버를 전혀 경유하지 않는 경우는 `dom-xss-scanner` 스킬에 위임한다.


**검증 기준:**
- **확인됨**: 아래 중 하나가 동적 테스트에서 직접 확인된 경우
  - (curl) `Content-Type: text/html` 응답 본문에 페이로드가 이스케이프 없이 포함됨
  - (Playwright) `alert()` 발화 확인
  - (Playwright) 페이로드(`<img src=x onerror=...>` 등)가 이스케이프 없이 DOM에 삽입됨
- **후보**: 동적 테스트를 수행하지 않았거나 (사용자가 정보 미제공), 동적 테스트로 확인이 불가하여 수동 확인이 필요한 경우
- **"확인됨"은 동적 테스트를 통해서만 부여할 수 있다**: 소스코드 분석만으로는 아무리 취약해 보여도 "확인됨"으로 보고하지 않는다. 동적 테스트로 실제 트리거를 확인한 경우에만 "확인됨"이다. 동적 테스트를 수행하지 않았으면 모든 결과는 "후보"이다.
- **보고서 제외**: 동적 테스트 결과 취약하지 않은 것으로 확인된 경우 (서버사이드 검증으로 차단, 필터링 우회 불가 등)는 보고서에 포함하지 않는다
