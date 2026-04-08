### Phase 2: 동적 테스트 (검증)


**테스트 방법:**
1. curl에 `-v` 또는 `-I` 플래그를 사용하여 응답 헤더를 확인
2. CRLF 페이로드가 포함된 요청을 전송
3. 응답 헤더에 주입한 헤더가 나타나는지 확인

**일반적인 페이로드:**
- `%0d%0aInjected-Header:true` — 새로운 헤더 추가
- `%0d%0aSet-Cookie:session=hacked` — 쿠키 주입
- `%0d%0a%0d%0a<script>alert(1)</script>` — 응답 본문 주입 (XSS)
- `%0d%0aContent-Type:text/html%0d%0a%0d%0a<html>` — Content-Type 변경 + 본문 주입

**더블 인코딩 페이로드 (서버가 1차 디코딩하는 경우):**
- `%250d%250aInjected-Header:true`

**검증 기준:**
- **확인됨**: 동적 테스트로 응답 헤더에 주입한 헤더가 실제로 나타난 것을 직접 확인함
