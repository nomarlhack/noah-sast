> ## 핵심 원칙: "헤더 변조로 보안이 우회되지 않으면 취약점이 아니다"
>
> Host 헤더를 변조할 수 있다는 것만으로는 취약점이 아니다. 변조된 헤더가 실제로 보안에 영향을 미치는 것(내부 자산 접근, 캐시 포이즈닝, URL 조작 등)을 확인해야 취약점이다.
>

### Phase 1: 정찰 (소스코드 분석)

Host 헤더와 IP 관련 헤더 처리 로직을 분석하여 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: 프레임워크/웹 서버/프록시 구조 확인

2. **Host 헤더 사용처 분석**:

   **URL 생성에 Host 헤더 사용:**
   - 패스워드 리셋 이메일의 URL 생성 로직
   - 이메일 인증 링크 생성 로직
   - OAuth 콜백 URL 동적 생성
   - 절대 URL 생성 시 `req.headers.host` 사용 여부

   **Node.js/Express:**
   - `req.headers.host`, `req.hostname`, `req.get('host')`
   - `req.protocol + '://' + req.get('host') + req.originalUrl`

   **Python/Django:**
   - `request.get_host()`, `request.META['HTTP_HOST']`
   - `request.build_absolute_uri()`
   - `ALLOWED_HOSTS` 설정 확인

   **Python/Flask:**
   - `request.host`, `request.host_url`
   - `url_for(..., _external=True)`

   **Java/Spring:**
   - `request.getServerName()`, `request.getHeader("Host")`
   - `ServletUriComponentsBuilder.fromCurrentRequest()`

   **Ruby/Rails:**
   - `request.host`, `request.host_with_port`
   - `config.action_mailer.default_url_options`

3. **IP 관련 헤더 사용처 분석**:

   **IP 기반 접근제어:**
   - 관리자 페이지 접근 시 IP 화이트리스트 검사 로직
   - Rate Limiting에서 클라이언트 IP 식별 로직
   - 내부 API 접근 시 IP 검증 로직
   - 지역 기반 접근제어 (Geo-blocking)

   **Node.js/Express:**
   - `req.ip`, `req.ips` — Express의 `trust proxy` 설정에 의존
   - `req.headers['x-forwarded-for']`
   - `req.headers['x-real-ip']`
   - `req.headers['x-client-ip']`
   - `req.headers['x-cluster-client-ip']`
   - `req.connection.remoteAddress`

   **Python/Django:**
   - `request.META['REMOTE_ADDR']`
   - `request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0]`
   - `django-ipware` 라이브러리의 `get_client_ip()`

   **Python/Flask:**
   - `request.remote_addr`
   - `request.access_route` — `X-Forwarded-For` 기반
   - `ProxyFix` 미들웨어 설정

   **Java/Spring:**
   - `request.getRemoteAddr()`
   - `request.getHeader("X-Forwarded-For")`

4. **프록시 설정 확인**:
   - Express `trust proxy` 설정 (`app.set('trust proxy', ...)`)
   - nginx `set_real_ip_from`, `real_ip_header` 설정
   - Django `ALLOWED_HOSTS` 설정
   - `X-Forwarded-For` 헤더에서 첫 번째 IP만 사용하는지, 마지막 IP를 사용하는지

5. **후보 목록 작성**: 각 후보에 대해 "어떤 헤더를 어떻게 변조하면 어떤 보안이 우회되는지"를 구체적으로 구상. 데이터 흐름 추적을 완료한 뒤에도 공격 경로가 없으면 버린다. 추적 없이 직관으로 버리지 않는다..

## 후보 판정 제한

클라이언트 제어 가능 헤더를 IP 판별/접근제어에 사용하는 경우 후보.
