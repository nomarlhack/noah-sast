## Phase 1: 소스코드 분석

### 1-1. Source 패턴 grep

아래 패턴을 프론트엔드 JS 코드 전체에서 grep하여 파일 목록을 수집한다.
`--include` 없이 전체 텍스트 파일을 대상으로 한다.

| Source | grep 패턴 |
|--------|-----------|
| URL fragment | `location\.hash` |
| URL query (클라이언트 처리) | `location\.search`, `location\.href` |
| Referrer | `document\.referrer` |
| Window name | `window\.name` |
| postMessage | `addEventListener.*message`, `onmessage` |
| localStorage / sessionStorage | `localStorage\.getItem`, `sessionStorage\.getItem` |

### 1-2. Sink 패턴 grep

아래 패턴을 프론트엔드 JS 코드 전체에서 grep하여 파일 목록을 수집한다.

| Sink | grep 패턴 |
|------|-----------|
| innerHTML / outerHTML | `\.innerHTML`, `\.outerHTML` |
| document.write | `document\.write` |
| eval | `\beval(` |
| setTimeout / setInterval (문자열 인자) | `setTimeout(`, `setInterval(` |
| Function 생성자 | `new Function(` |
| insertAdjacentHTML | `insertAdjacentHTML` |
| jQuery | `\.html(`, `\.append(`, `\.prepend(` |
| location 조작 | `location\.href\s*=`, `location\.assign(`, `location\.replace(` |

### 1-3. Source → Sink 데이터 흐름 추적

Source grep 결과와 Sink grep 결과에서 **같은 파일 또는 동일 데이터 흐름**에 속하는 것을 대조한다.

각 후보에 대해 다음을 반드시 코드에서 읽어 확인한다:

1. Source 값이 어떤 변수에 할당되는가
2. 그 변수가 Sink에 도달하기까지 중간에 인코딩·이스케이프·검증이 적용되는가
3. 공격자가 Source 값을 제어할 수 있는가
   - `location.hash`: URL 뒤 `#` 이후 값 → 공격자가 URL을 제어하면 조작 가능
   - `window.name`: 링크로 열린 탭에서 이전 페이지가 설정 가능 → 제어 가능
   - `postMessage`: 발신 출처(origin) 검증이 없으면 제어 가능
   - `document.referrer`: Referer 헤더 → 제어 가능하나 브라우저 제한 있음
   - `localStorage`: 다른 XSS가 선행돼야 주입 가능 → 2차 공격 경로로 분류

**후보 제외 기준 (코드에서 직접 확인한 경우에만 적용):**
- Source 값이 Sink 도달 전 `encodeURIComponent`, `DOMPurify.sanitize`, `escapeHtml` 등으로 완전히 새니타이징됨이 코드에서 확인된 경우
- Source 값이 Sink에 도달하는 코드 경로가 존재하지 않음이 코드에서 확인된 경우

코드를 읽지 않고 직관이나 추정으로 제외하지 않는다.

## 후보 판정 제한

클라이언트 source에서 DOM sink까지 코드상 연결된 데이터 흐름이 있는 경우만 후보. source를 읽어서 DOM sink에 도달하지 않으면 제외.
