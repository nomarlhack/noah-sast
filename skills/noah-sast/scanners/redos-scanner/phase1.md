> **호출부 추적 — 실제 URL 경로 확정**: 모든 후보에 대해 라우트 정의 파일을 Read로 읽어 실제 URL 경로를 확정한다. 컴포넌트/파일 이름에서 경로를 유추하는 것은 확정이 아니다. 절차: (1) Sink의 호출부를 Grep → 최종 페이지 컴포넌트/컨트롤러 식별 (2) 라우트 정의(routes/index.tsx, @RequestMapping 등)를 Read로 읽어 경로 문자열 확인 (3) 후보 반환 시 근거 포함: `실제 경로: /home/apply (src/routes/index.tsx:42)`

### Phase 1: 정찰 (소스코드 분석)

정규식 사용처를 찾고, 사용자 입력이 취약한 정규식에 매칭되는 경로를 식별한다.

1. **프로젝트 스택 파악**: 정규식 엔진 특성 확인
   - **JavaScript (V8)**: NFA 기반, ReDoS에 취약. Node.js는 메인 스레드 블로킹으로 전체 서비스 영향.
   - **Python (re)**: NFA 기반, ReDoS에 취약. `re2` 라이브러리는 안전.
   - **Java (java.util.regex)**: NFA 기반, ReDoS에 취약.
   - **Go (regexp)**: RE2 기반 (DFA), 선형 시간 보장 — ReDoS에 안전.
   - **Rust (regex)**: RE2 기반, 안전.
   - **Ruby**: Oniguruma/Onigmo 엔진, NFA 기반, 취약.
   - **PHP (PCRE)**: NFA 기반, 취약. 단, `pcre.backtrack_limit` 설정으로 완화 가능.

2. **Source 식별**: 사용자가 제어 가능한 입력 중 정규식 매칭에 사용되는 것
   - HTTP 요청 본문 (이메일, URL, 전화번호 등 사용자 입력 검증)
   - 검색 기능의 검색어
   - 파일명/경로
   - 사용자가 직접 정규식을 입력하는 기능 (검색 필터 등)

3. **Sink 식별**: 정규식 매칭을 수행하는 코드

   **JavaScript:**
   - `regex.test(userInput)`
   - `string.match(regex)`
   - `string.replace(regex, ...)`
   - `string.split(regex)`
   - `new RegExp(pattern).test(userInput)`

   **Python:**
   - `re.match(pattern, user_input)`
   - `re.search(pattern, user_input)`
   - `re.findall(pattern, user_input)`
   - `re.sub(pattern, repl, user_input)`

   **Java:**
   - `Pattern.compile(pattern).matcher(userInput).matches()`
   - `String.matches(pattern)`
   - `String.replaceAll(pattern, replacement)`

4. **취약 정규식 패턴 탐지**: 다음 패턴을 검색
   - 중첩 반복: `(x+)+`, `(x*)*`, `(x+)*`, `(x*)+`
   - 겹치는 교대 + 반복: `(a|ab)+`, `(a|a?)+`
   - 욕심많은 매칭 + 역참조: `(.*a){n}` where n > 1
   - 복잡한 이메일/URL 검증 정규식
   - 사용자 입력이 `new RegExp(userInput)`으로 정규식 자체에 삽입되는 경우 (ReDoS + Regex Injection)

5. **후보 목록 작성**: 각 후보에 대해 "어떤 입력으로 어떻게 역추적을 유발할 수 있는지"를 구체적으로 구상. 데이터 흐름 추적을 완료한 뒤에도 공격 경로가 없으면 버린다. 추적 없이 직관으로 버리지 않는다..

## 후보 판정 제한

중첩 반복 + 모호 교대 패턴이 있고, 사용자 입력이 매칭 대상으로 도달하는 경우만 후보.
