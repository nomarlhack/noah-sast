### Phase 2: 동적 테스트 (검증)


**서버사이드 리다이렉트 테스트:**
1. curl에 `-v` 또는 `-I` 플래그를 사용하여 응답 헤더 확인 (리다이렉트를 따라가지 않음)
2. `Location` 헤더에 외부 도메인이 반영되는지 확인
3. HTML `meta refresh`의 경우 응답 본문에서 외부 URL이 삽입되는지 확인

**클라이언트사이드 리다이렉트 테스트:**
- curl로는 재현 불가. webapp-testing 스킬이나 Playwright 등 브라우저 자동화 도구가 있으면 활용한다.
- 브라우저 도구가 없으면 "후보 (브라우저 테스트 필요)"로 보고한다.

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
