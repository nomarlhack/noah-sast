> **호출부 추적 — 실제 URL 경로 확정**: 모든 후보에 대해 라우트 정의 파일을 Read로 읽어 실제 URL 경로를 확정한다. 컴포넌트/파일 이름에서 경로를 유추하는 것은 확정이 아니다. 절차: (1) Sink의 호출부를 Grep → 최종 페이지 컴포넌트/컨트롤러 식별 (2) 라우트 정의(routes/index.tsx, @RequestMapping 등)를 Read로 읽어 경로 문자열 확인 (3) 후보 반환 시 근거 포함: `실제 경로: /home/apply (src/routes/index.tsx:42)`

### Phase 1: 정찰 (소스코드 분석)

사용자 입력 → 객체 병합/복사 함수 → 프로토타입 오염 경로를 추적하여 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: package.json에서 사용 중인 라이브러리 확인. 특히 알려진 취약 버전이 있는 라이브러리에 주의.

2. **Source 식별**: 사용자가 제어 가능한 입력 중 객체/JSON으로 사용되는 것
   - HTTP 요청 본문 (JSON): `req.body`
   - HTTP 쿼리 파라미터 (qs 파서가 중첩 객체 지원): `req.query`
   - URL 파라미터
   - WebSocket 메시지
   - 설정 파일, 사용자 정의 옵션 등

3. **Sink 식별**: 객체 속성을 재귀적으로 복사/병합/설정하는 코드

   **위험한 패턴 (재귀적 병합/복사):**
   - 커스텀 `merge`, `extend`, `deepMerge`, `deepCopy`, `defaultsDeep` 함수
   - `lodash.merge`, `lodash.defaultsDeep`, `lodash.set`, `lodash.setWith` (취약 버전)
   - `jQuery.extend(true, ...)` (deep copy 모드)
   - `hoek.merge`, `hoek.applyToDefaults` (취약 버전)
   - `deap`, `deep-extend`, `merge-deep`, `mixin-deep`, `defaults-deep` 등 npm 패키지
   - `Object.assign`은 1-depth만 복사하므로 직접적으로는 안전하지만, 중첩 구조에서 래핑되면 위험

   **동적 속성 설정:**
   - `obj[key] = value` 패턴에서 `key`가 사용자 입력인 경우
   - `obj[a][b] = c` 패턴에서 `a`, `b`가 사용자 입력인 경우
   - `lodash.set(obj, path, value)` 에서 `path`가 사용자 입력인 경우
   - `_.set`, `dot-prop.set`, `set-value`, `object-path.set` 등

   **키 검증 여부 확인:**
   ```javascript
   // 안전하지 않음 — __proto__ 키를 차단하지 않음
   function merge(target, source) {
     for (let key in source) {
       if (typeof source[key] === 'object') {
         target[key] = merge(target[key] || {}, source[key]);
       } else {
         target[key] = source[key];
       }
     }
   }

   // 안전함 — __proto__, constructor, prototype 키를 차단
   function safeMerge(target, source) {
     for (let key in source) {
       if (key === '__proto__' || key === 'constructor' || key === 'prototype') continue;
       // ...
     }
   }
   ```

4. **경로 추적**: Source에서 Sink까지 데이터가 키 검증 없이 도달하는 경로 확인. 다음을 점검:
   - `__proto__`, `constructor`, `prototype` 키에 대한 필터링 존재 여부
   - `Object.create(null)`로 생성된 프로토타입 없는 객체를 사용하는지
   - `Map`/`Set` 등 프로토타입 체인을 사용하지 않는 자료구조를 쓰는지
   - JSON 파서가 `__proto__` 키를 제거하는지 (일부 보안 JSON 파서)
   - Express의 query parser가 중첩 객체를 허용하는지 (`qs` 기본 설정)

5. **가젯 탐색**: 프로토타입 오염이 가능한 경우, 오염된 속성을 참조하여 위험한 동작을 수행하는 코드(가젯)를 찾는다.

   **서버사이드 가젯 예시:**
   - `child_process.spawn`/`exec` 옵션에서 `shell`, `env`, `cwd` 등이 오염된 속성을 참조
   - `ejs`, `pug`, `handlebars` 등 템플릿 엔진의 컴파일 옵션
   - Express의 `res.render()` 옵션
   - `require` 경로 조작

   **클라이언트사이드 가젯 예시:**
   - `innerHTML`, `outerHTML`에 오염된 속성 값이 삽입
   - `document.createElement` 후 오염된 속성이 attribute로 설정
   - `eval`, `Function`, `setTimeout(string)` 에 오염된 값 전달
   - 라이브러리 초기화 옵션에서 오염된 속성 참조 (sanitizer bypass 등)

6. **후보 목록 작성**: 각 후보에 대해 "어떤 입력으로 어떻게 프로토타입을 오염시킬 수 있는지", 그리고 가능하면 "어떤 가젯을 통해 실제 영향이 발생하는지"를 구체적으로 구상. 데이터 흐름 추적을 완료한 뒤에도 공격 경로가 없으면 버린다. 추적 없이 직관으로 버리지 않는다..

## 후보 판정 제한

소스코드에서 직접 import/호출하는 경우만 분석 대상. lock 파일의 전이 의존성은 제외. `Object.assign`은 1-depth 복사이므로 제외.
