> **호출부 추적 — 실제 URL 경로 확정**: 모든 후보에 대해 라우트 정의 파일을 Read로 읽어 실제 URL 경로를 확정한다. 컴포넌트/파일 이름에서 경로를 유추하는 것은 확정이 아니다. 절차: (1) Sink의 호출부를 Grep → 최종 페이지 컴포넌트/컨트롤러 식별 (2) 라우트 정의(routes/index.tsx, @RequestMapping 등)를 Read로 읽어 경로 문자열 확인 (3) 후보 반환 시 근거 포함: `실제 경로: /home/apply (src/routes/index.tsx:42)`

### Phase 1: 정찰 (소스코드 분석)

라우팅 설정과 인증/인가 미들웨어를 분석하여 메서드별 보안 적용 차이를 식별한다.

1. **프로젝트 스택 파악**: 프레임워크/언어/웹 서버/리버스 프록시 확인

2. **라우트 정의 분석**: HTTP 메서드별 라우트 등록 방식 확인

   **Express/Node.js:**
   - `app.get()`, `app.post()`, `app.put()`, `app.delete()` — 메서드별 개별 등록
   - `app.all()` — 모든 메서드 허용 (의도적인지 확인 필요)
   - `app.use()` — 모든 메서드에 미들웨어 적용 (인증이 여기에 있으면 안전)
   - `router.route('/path').get(...).post(...)` — 체이닝 방식

   **Next.js API Routes:**
   - `pages/api/` 핸들러에서 `req.method` 체크 여부
   - 메서드별 분기가 없으면 모든 메서드에서 동일 로직 실행

   **Django:**
   - `@require_http_methods(['GET', 'POST'])` — 허용 메서드 제한
   - `class-based view`의 `http_method_names` — 허용 메서드 목록
   - `if request.method == 'POST':` — 수동 체크

   **Spring:**
   - `@GetMapping`, `@PostMapping`, `@RequestMapping(method=...)` — 메서드 지정
   - `@RequestMapping` (method 미지정) — 모든 메서드 허용

   **Rails:**
   - `routes.rb`의 `get`, `post`, `resources` — RESTful 라우팅
   - `match ... via: [:get, :post]` — 메서드 제한

3. **인증/인가 미들웨어 분석**: 메서드별 보안 적용 범위 확인
   - 인증 미들웨어가 **전역**으로 적용되는지, **라우트별**로 적용되는지
   - 특정 메서드에만 인증을 건너뛰는(skip) 로직이 있는지
   - `app.all('/admin/*', authMiddleware)` vs `app.post('/admin/*', authMiddleware)` — 전자는 안전, 후자는 GET 우회 가능

4. **Method Override 설정 확인**:
   - Express: `method-override` 미들웨어 사용 여부
   - Django: `django.middleware.http.ConditionalGetMiddleware`
   - Rails: `Rack::MethodOverride` (기본 활성화)
   - 커스텀: `X-HTTP-Method-Override`, `X-Method-Override`, `_method` 파라미터 처리 코드

5. **웹 서버/프록시 설정 확인** (접근 가능한 경우):
   - nginx: `limit_except` 디렉티브
   - Apache: `<Limit>`, `<LimitExcept>` 디렉티브
   - `.htaccess` 파일

6. **후보 목록 작성**: 각 후보에 대해 "어떤 메서드로 요청하면 어떤 보안 검사가 우회되는지"를 구체적으로 구상. 데이터 흐름 추적을 완료한 뒤에도 공격 경로가 없으면 버린다. 추적 없이 직관으로 버리지 않는다..
