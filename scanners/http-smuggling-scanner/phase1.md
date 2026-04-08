> ## 핵심 원칙: "요청 경계 불일치가 발생하지 않으면 취약점이 아니다"
>
> 프록시와 백엔드 서버가 있다고 바로 취약점으로 보고하지 않는다. 실제로 `Content-Length`와 `Transfer-Encoding` 헤더의 해석 차이로 인해 하나의 HTTP 요청 안에 숨겨진 두 번째 요청이 백엔드에서 별도로 처리되는 것을 확인해야 취약점이다.
>

### Phase 1: 정찰 (소스코드/설정 분석)

인프라 구성과 HTTP 처리 로직을 분석하여 취약점 **후보**를 식별한다.

1. **인프라 구조 파악**: 프론트엔드/백엔드 구성 확인
   - 리버스 프록시: nginx, Apache, HAProxy, AWS ALB/ELB, Cloudflare, Akamai
   - 백엔드 서버: Express/Node.js, Gunicorn, Tomcat, IIS, Puma
   - CDN/WAF: Cloudflare, AWS CloudFront, Fastly
   - HTTP/2 → HTTP/1.1 다운그레이드 여부

2. **프록시 설정 분석**:
   - nginx: `proxy_pass` 설정, `proxy_http_version` (1.0 vs 1.1), `proxy_set_header Connection`
   - Apache: `ProxyPass` 설정, `mod_proxy` 동작
   - HAProxy: `http-reuse`, `option http-server-close` 설정
   - Express `http-proxy-middleware`: `changeOrigin`, 커넥션 풀링

3. **백엔드 HTTP 파서 확인**:
   - Node.js (`http` 모듈): `--insecure-http-parser` 플래그 사용 여부
   - Python (Gunicorn/uWSGI): HTTP 파서 엄격성
   - Java (Tomcat/Jetty): `Transfer-Encoding` 처리 방식
   - `Content-Length`와 `Transfer-Encoding` 동시 존재 시 처리 방식

4. **취약 조건 분석**:
   - 프론트엔드와 백엔드가 같은 커넥션을 재사용하는지 (HTTP keep-alive/pipelining)
   - `Transfer-Encoding: chunked`를 프론트엔드와 백엔드가 다르게 처리하는지
   - `Content-Length`와 `Transfer-Encoding`이 동시에 존재하면 어떻게 처리하는지
   - HTTP/2 → HTTP/1.1 변환 시 헤더 매핑 방식

5. **후보 목록 작성**: 각 후보에 대해 "어떤 CL/TE 조합으로 어떻게 요청을 밀수할 수 있는지"를 구체적으로 구상.

**주의: 소스코드에 프록시 설정 파일이 없더라도 Phase 1을 "해당 없음"으로 종료하지 않는다.** 프록시 설정은 인프라 레벨에서 관리되어 소스코드에 포함되지 않는 것이 일반적이다. 테스트 환경 URL이 제공되어 있으면 반드시 Phase 2 동적 테스트를 진행한다.

## 후보 판정 제한

프록시 체인이 존재하고 설정 미흡이 확인되면 후보.
