### Phase 2: 동적 테스트 (검증)


**서버사이드 리다이렉트 테스트:**
```
# 기본 외부 도메인 리다이렉트
curl -I "https://target.com/redirect?url=https://evil.com"
curl -I "https://target.com/redirect?next=https://evil.com"
curl -I "https://target.com/redirect?returnTo=https://evil.com"

# Location 헤더에서 외부 도메인 확인
curl -v "https://target.com/redirect?url=https://evil.com" 2>&1 | grep -i "location:"
```

**클라이언트사이드 리다이렉트 Playwright 테스트:**
```javascript
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // 클라이언트 리다이렉트 감지 (window.location, meta refresh, JS redirect)
  let redirectedTo = null;
  page.on('framenavigated', frame => {
    if (frame === page.mainFrame()) {
      redirectedTo = frame.url();
    }
  });

  await page.goto('https://target.com/page?redirect=https://evil.com', {
    waitUntil: 'networkidle',
    timeout: 10000
  });

  console.log('Final URL:', page.url());
  if (page.url().includes('evil.com')) {
    console.log('CONFIRMED: Client-side open redirect');
  }

  // hash fragment 기반 리다이렉트
  await page.goto('https://target.com/page#redirect=https://evil.com', {
    waitUntil: 'networkidle',
    timeout: 10000
  });
  console.log('Fragment redirect final URL:', page.url());

  await browser.close();
})();
```

Playwright 실행이 불가능한 경우에만 "후보 (브라우저 테스트 필요)"로 보고한다.

**URL 검증 우회 테스트 (검증 로직이 존재하는 경우):**
- 프로토콜 상대 URL: `//evil.com`
- 유사 도메인: `https://allowed.com.evil.com`
- 인증 정보 삽입: `https://allowed.com@evil.com`
- 백슬래시: `https://allowed.com\@evil.com`, `/\evil.com`
- URL 인코딩: `%2f%2fevil.com`, `%00` null byte
- 대소문자: `javascript:alert(1)` vs `JAVASCRIPT:alert(1)`
- 탭/개행: `java\tscript:`, `java\nscript:`
- data: URI: `data:text/html,<script>...</script>`
- 상대 경로 우회: `///evil.com`, `/\/evil.com`

**검증 기준:**
- **확인됨**: 동적 테스트로 외부 도메인으로 리다이렉트가 발생한 것을 직접 확인함
- **후보**: 동적 테스트를 수행하지 않았거나, 동적 테스트로 확인이 불가하여 수동 확인이 필요한 경우 (클라이언트사이드라 curl 재현 불가 등)
