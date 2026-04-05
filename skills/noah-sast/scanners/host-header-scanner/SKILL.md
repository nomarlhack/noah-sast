---
name: host-header-scanner
description: "소스코드 분석과 동적 테스트를 통해 Host Header Attack 및 IP Spoofing 취약점을 탐지하는 스킬. Host 헤더 변조를 통한 캐시 포이즈닝, 패스워드 리셋 URL 조작, 내부 자산 접근과 X-Forwarded-For 등 IP 관련 헤더 변조를 통한 IP 기반 접근제어 우회를 분석하고 검증한다. 사용자가 'Host header attack', 'host 헤더 변조', 'IP spoofing', 'X-Forwarded-For 우회', 'host header injection', '호스트 헤더 점검', 'IP 접근제어 우회' 등을 요청할 때 이 스킬을 사용한다."
grep_patterns:
  - "req\\.headers\\.host"
  - "req\\.hostname"
  - "req\\.get('host')"
  - "request\\.get_host("
  - "HTTP_HOST"
  - "request\\.build_absolute_uri("
  - "request\\.host"
  - "request\\.getServerName("
  - "X-Forwarded-For"
  - "X-Real-IP"
  - "X-Forwarded-Host"
  - "remote_ip"
  - "remote_addr"
  - "REMOTE_ADDR"
  - "getHeader("
  - "request\\.remoteAddr"
  - "X-Original-Forwarded-For"
---

# Host Header Scanner

소스코드 분석으로 Host 헤더 및 IP 관련 헤더 처리의 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 헤더 변조를 통해 보안을 우회할 수 있는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "헤더 변조로 보안이 우회되지 않으면 취약점이 아니다"

Host 헤더를 변조할 수 있다는 것만으로는 취약점이 아니다. 변조된 헤더가 실제로 보안에 영향을 미치는 것(내부 자산 접근, 캐시 포이즈닝, URL 조작 등)을 확인해야 취약점이다.

## 취약점의 유형

### Host Header Injection

#### 패스워드 리셋 URL 조작 (Password Reset Poisoning)
패스워드 리셋 이메일에 포함되는 URL이 `Host` 헤더 값을 기반으로 생성되는 경우. 공격자가 `Host: evil.com`으로 변조하면 피해자에게 `https://evil.com/reset?token=...` 링크가 전송되어 토큰이 탈취될 수 있다.

#### 웹 캐시 포이즈닝 (Web Cache Poisoning)
CDN이나 리버스 프록시가 응답을 캐시할 때, `Host` 헤더가 응답 본문(링크, 리소스 URL 등)에 반영되면 공격자가 캐시에 악성 콘텐츠를 삽입할 수 있다.

#### 가상 호스트 라우팅 우회
`Host` 헤더를 변조하여 같은 서버의 다른 가상 호스트(내부 관리 페이지, 스테이징 환경 등)에 접근하는 공격.

#### SSRF via Host Header
서버가 `Host` 헤더 값을 내부 요청의 대상으로 사용하는 경우.

### IP Spoofing (IP 관련 헤더 변조)

#### X-Forwarded-For 우회
서버가 `X-Forwarded-For` 헤더로 클라이언트 IP를 판단하여 접근제어를 수행할 때, 헤더를 변조하여 허용된 IP로 위장하는 공격.

#### 기타 IP 헤더 우회
`X-Forwarded-For` 외에도 다양한 IP 관련 헤더를 조작하여 IP 기반 접근제어를 우회:
- `X-Real-IP`
- `X-Forwarded-Host`
- `X-CLUSTER-CLIENT-IP`
- `X-Client-IP`
- `X-Original-URL`
- `X-Rewrite-URL`
- `Forwarded` (RFC 7239 표준)
- `True-Client-IP` (Akamai)
- `CF-Connecting-IP` (Cloudflare)
- `X-ProxyUser-Ip`

이 공격이 성공하려면 서버가 이 헤더들을 신뢰하여 클라이언트 IP를 판단해야 한다. 프록시/로드밸런서 뒤에서 이 헤더를 올바르게 처리하지 않으면 취약하다.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 `../../agent-guidelines.md` (이 파일 기준 상대 경로)를 참조한다.
