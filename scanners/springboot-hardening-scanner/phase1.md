---
grep_patterns:
  - "spring\\.mvc\\.dispatch-trace-request"
  - "dispatch-trace-request"
  - "server\\.error\\.whitelabel"
  - "whitelabel"
  - "server\\.error\\.include-stacktrace"
  - "include-stacktrace"
  - "springdoc"
  - "swagger"
  - "api-docs"
  - "management\\.endpoints"
  - "management\\.endpoint"
  - "actuator"
  - "spring-boot-starter-actuator"
  - "spring\\.application\\.admin\\.enabled"
  - "spring\\.devtools"
  - "spring-boot-devtools"
  - "devtools\\.remote\\.secret"
  - "spring\\.h2\\.console"
  - "h2database"
  - "h2\\.console\\.enabled"
  - "server\\.tomcat\\.accesslog"
  - "server\\.jetty\\.accesslog"
  - "server\\.undertow\\.accesslog"
  - "EndpointRequest"
  - "management\\.server\\.port"
  - "enabled-by-default"
  - "shutdown\\.enabled"
---

> ## 핵심 원칙: "Prod 환경의 effective config가 안전하지 않으면 후보이다"
>
> 이 스캐너는 Source→Sink 코드 취약점이 아닌 **Spring Boot 설정 파일 기반 보안 구성**을 점검한다. Spring Boot의 프로파일 시스템(`application.yml` vs `application-prod.yml`)을 고려하여, prod 환경의 effective config(base + prod override 병합 결과)를 기준으로 판정한다.

## 분석 방법 — Prod 프로파일 해석 모델

### Step A: Spring Boot 프로젝트 식별

`pom.xml` 또는 `build.gradle`/`build.gradle.kts`에서 `spring-boot` 관련 dependency를 확인한다. Spring Boot 프로젝트가 아니면 "이상 없음" 반환.

### Step B: 설정 파일 수집 및 Prod 프로파일 해석

1. 프로젝트 전체에서 설정 파일을 탐색:
   - `application.yml`, `application.yaml`, `application.properties`
   - `application-{profile}.yml/yaml/properties`
   - `bootstrap.yml/yaml/properties`, `bootstrap-{profile}.yml/yaml/properties`
   - `src/main/resources/` 하위 포함

2. **Prod 프로파일 식별** — 아래 이름을 prod 프로파일로 간주:
   - `prod`, `production`, `prd`, `release`, `live`, `real`

3. **Effective config 산출**: base 설정(`application.yml`)에 prod 프로파일 설정을 overlay한 결과를 effective config으로 간주. **prod 프로파일에 명시된 값이 base 값을 override한다.**

4. prod 프로파일 설정 파일이 없으면, base 설정만으로 점검하되 "prod 프로파일 설정 파일 부재" 사실을 후보 설명에 기재.

### Step C: 빌드 파일 분석

`pom.xml` / `build.gradle`에서 dependency 존재 여부와 scope를 확인한다:
- `spring-boot-devtools`의 scope (`developmentOnly`, `optional`)
- `h2database`의 scope (`runtime`, `test`)
- `spring-boot-starter-actuator` 존재 여부

### Step D: 항목별 점검

아래 12개 항목 각각에 대해, grep 패턴 인덱스에서 관련 파일 위치를 확인하고 Read로 읽어 effective config 값을 판정한다.

---

## 점검 항목 및 판정 테이블

### D-1: 데몬 root 실행 (`DAEMON_ROOT`)

Dockerfile 또는 docker-compose.yml을 확인한다.

| 패턴 | 판정 |
|------|------|
| Dockerfile에 `USER` 지시어 없음 (기본 root) | 후보 |
| `USER root` 명시 | 후보 |
| `USER nobody`, `USER daemon`, `USER appuser` 등 비root 계정 | 제외 |
| Dockerfile 자체가 없음 | 점검 불가 — 후보에서 제외하되 "Dockerfile 부재로 미점검" 기재 |

### D-2: 액세스 로그 (`LOG_PERMISSION`)

Effective config에서 embedded 서버 종류에 맞는 액세스 로그 설정을 확인한다.

| 패턴 | 판정 |
|------|------|
| `server.tomcat.accesslog.enabled=true` | 제외 |
| `server.jetty.accesslog.enabled=true` | 제외 |
| `server.undertow.accesslog.enabled=true` | 제외 |
| 위 설정이 모두 없음 (embedded 서버에 맞는 로그 미활성화) | 후보 |

### D-3: TRACE 메서드 허용 (`TRACE_ENABLED`)

Spring Boot의 기본값은 `spring.mvc.dispatch-trace-request=false`(TRACE 미처리, embedded Tomcat은 자체적으로 TRACE 반환). Jetty/Undertow는 이 설정으로 차단 가능.

| 패턴 | 판정 |
|------|------|
| effective config에 `spring.mvc.dispatch-trace-request` 설정 없음 + embedded Tomcat | 후보 (Tomcat 기본 동작이 TRACE 응답) |
| `spring.mvc.dispatch-trace-request=true` + Jetty 또는 Undertow | 제외 (405/500 반환) |
| `spring.mvc.dispatch-trace-request=true` + Tomcat | 후보 (Tomcat은 이 설정으로도 TRACE 차단 안 됨, 별도 Connector 설정 필요) |
| 웹서버(Nginx/Apache)에서 TRACE 차단 설정 확인됨 | 제외 |

### D-4: Whitelabel 에러페이지 (`WHITELABEL_ENABLED`)

기본값은 `server.error.whitelabel.enabled=true`.

| 패턴 | 판정 |
|------|------|
| effective config에 `server.error.whitelabel.enabled` 없음 (기본값 true) | 후보 |
| `server.error.whitelabel.enabled=true` | 후보 |
| `server.error.whitelabel.enabled=false` | 제외 |
| 커스텀 ErrorController 구현 확인 | 제외 |

### D-5: StackTrace 노출 (`STACKTRACE_EXPOSED`)

기본값은 `server.error.include-stacktrace=never` (Spring Boot 2.3+). 2.3 미만은 `on-trace-param`.

| 패턴 | 판정 |
|------|------|
| effective config에 `server.error.include-stacktrace=always` | 후보 |
| `server.error.include-stacktrace=on-param` 또는 `on-trace-param` | 후보 |
| `server.error.include-stacktrace=never` 또는 설정 없음 (Spring Boot 2.3+) | 제외 |
| 설정 없음 + Spring Boot 2.3 미만 | 후보 (기본값이 `on-trace-param`) |

### D-6: Swagger docs 노출 (`SWAGGER_ENABLED`)

빌드 파일에서 springdoc/swagger 의존성을 확인하고, 설정 파일에서 비활성화 여부를 확인한다.

| 패턴 | 판정 |
|------|------|
| springdoc/springfox 의존성 없음 | 제외 |
| 의존성 존재 + `springdoc.api-docs.enabled=false` | 제외 |
| 의존성 존재 + 비활성화 설정 없음 | 후보 |
| 의존성 존재 + Spring Security로 swagger 경로에 인증 적용 | 제외 |

### D-7: Actuator 외부 노출 (`ACTUATOR_EXPOSED`)

| 패턴 | 판정 |
|------|------|
| `spring-boot-starter-actuator` 의존성 없음 | 제외 |
| 의존성 존재 + `management.server.port`로 별도 포트 분리 | 제외 |
| 의존성 존재 + Spring Security로 actuator endpoint에 인증 적용 (`EndpointRequest` 사용) | 제외 |
| 의존성 존재 + 접근 제어 없음 | 후보 |

### D-8: 불필요 Actuator endpoint 활성화 (`ACTUATOR_OVEREXPOSED`)

| 패턴 | 판정 |
|------|------|
| `management.endpoints.enabled-by-default=false` + 필요 endpoint만 활성화 | 제외 |
| `management.endpoints.web.exposure.include=health` (또는 최소 목록) | 제외 |
| `management.endpoints.web.exposure.include=*` | 후보 |
| `management.endpoint.shutdown.enabled=true` | 후보 (**shutdown 활성화는 단독 후보**) |
| 노출 설정 없음 (Spring Boot 버전 기본값에 따라 판단) | Spring Boot 2.x: web은 health만 기본 노출 → 제외. Spring Boot 1.x: 전체 노출 → 후보 |

### D-9: Admin MBean 활성화 (`ADMIN_MBEAN_ENABLED`)

기본값은 `spring.application.admin.enabled=false`.

| 패턴 | 판정 |
|------|------|
| `spring.application.admin.enabled=true` | 후보 |
| 설정 없음 (기본값 false) | 제외 |

### D-10: DevTools 운영 포함 (`DEVTOOLS_PROD`)

| 패턴 | 판정 |
|------|------|
| `spring-boot-devtools` 의존성 없음 | 제외 |
| 의존성 scope가 `developmentOnly` (Gradle) 또는 `optional=true` (Maven) | 제외 |
| 의존성 scope가 `compile`/`implementation` (운영 포함) | 후보 |
| `spring.devtools.remote.secret` 설정 존재 | 후보 (**원격 접속 활성화**) |

### D-11: H2 Console 활성화 (`H2_CONSOLE_ENABLED`)

기본값은 `spring.h2.console.enabled=false`.

| 패턴 | 판정 |
|------|------|
| `h2database` 의존성 없음 | 제외 |
| 의존성 scope가 `test` | 제외 |
| `spring.h2.console.enabled=true` (effective config) | 후보 |
| 의존성 존재 + 설정 없음 (기본값 false) | 제외 |

### D-12: 취약 버전 사용 (`OUTDATED_DEPS`)

빌드 파일에서 Spring Boot 버전과 주요 dependency 버전을 확인한다.

| 패턴 | 판정 |
|------|------|
| Spring Boot 버전이 현재 지원 종료(EOL) 브랜치 | 후보 |
| 알려진 CVE가 있는 dependency 버전 사용 | 후보 |
| 최신 패치 버전 사용 중 | 제외 |

**참고**: 버전 판정은 에이전트의 학습 데이터 기준이므로, 최신 CVE 정보와 차이가 있을 수 있다. "정확한 취약 버전 목록은 OSS 도구(OWASP Dependency-Check 등)로 별도 확인을 권장한다"는 안내를 후보 설명에 포함한다.

---

## 안전 패턴 카탈로그 (FP Guard)

- **Spring Security actuator 보호**: `EndpointRequest.toAnyEndpoint()` + `.hasRole()` 설정 확인
- **별도 management 포트**: `management.server.port`로 내부 포트 분리
- **프로파일 override**: base에서 `true`지만 prod 프로파일에서 `false`로 override된 경우 → 제외
- **커스텀 ErrorController**: `BasicErrorController`를 상속/대체하는 클래스가 존재하면 Whitelabel 판정에서 제외
- **웹서버 레벨 차단**: Nginx/Apache 설정에서 TRACE 차단, actuator 경로 차단 등 확인

## 후보 판정 제한

- **프로파일 분리 존중**: `application-dev.yml`에만 있는 설정(예: `spring.h2.console.enabled=true`)은 prod effective config에 포함되지 않으므로 후보가 아니다.
- **기본값 숙지**: Spring Boot 버전별 기본값이 다르다. 설정 파일에 명시되지 않은 항목은 해당 버전의 기본값으로 판정한다.
- **scope 존중**: `developmentOnly`/`testOnly` scope의 dependency는 운영 환경에 포함되지 않으므로 후보가 아니다.
