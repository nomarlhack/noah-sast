---
grep_patterns:
  - "devtool"
  - "sourcemap"
  - "source-map"
  - "productionBrowserSourceMaps"
  - "productionSourceMap"
  - "GENERATE_SOURCEMAP"
  - "sourceMappingURL"
  - "build\\.sourcemap"
  - "webpack"
---

# Source Map Scanner

웹 애플리케이션에서 Source Map(.map) 파일이 프로덕션 환경에 노출되어 있는지 확인하고, 노출된 Source Map에서 민감한 정보를 탐지하여 보고하는 스킬이다.

## 핵심 원칙: "민감한 정보가 노출되지 않으면 취약점이 아니다"

Source Map 파일이 다운로드 가능하다는 것 자체가 취약점이지만, 실제 영향도는 포함된 내용에 따라 다르다. Source Map에서 API 키, 시크릿, 내부 API 경로, 주석에 포함된 자격 증명 등 민감한 정보가 발견되면 심각도가 높아진다.

## Source Map이란

JavaScript/CSS 빌드 시 생성되는 매핑 파일로, 난독화/압축된 코드를 원본 소스코드로 역추적할 수 있게 한다. 프로덕션 환경에서 노출되면 공격자가 전체 프론트엔드 소스코드를 복원하여 취약점을 분석할 수 있다.

## 취약점의 유형

### Source Map 파일 노출
프로덕션 빌드에서 `.map` 파일이 웹 서버에 배포되어 외부에서 다운로드 가능한 경우.

### 원본 소스코드 노출
Source Map을 통해 복원된 원본 소스코드에서 비즈니스 로직, 인증 흐름, API 구조가 노출되는 경우.

### 민감 정보 노출
Source Map에 포함된 원본 코드나 주석에서 다음과 같은 민감 정보가 발견되는 경우:
- API 키, 시크릿 키 (하드코딩된 값)
- 내부 API 엔드포인트 URL
- 데이터베이스 연결 문자열
- 관리자 페이지 경로
- 주석에 포함된 TODO/FIXME에 보안 관련 메모
- 환경변수 참조 (`process.env.SECRET_KEY` 등의 값이 빌드 시 인라인됨)
- 개발자 이메일, 내부 도메인

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

