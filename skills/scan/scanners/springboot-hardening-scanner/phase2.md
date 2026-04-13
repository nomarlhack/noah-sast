## 동적 검증

Phase 1에서 후보로 판정된 항목 중 동적 검증이 가능한 항목을 curl로 테스트한다. **Playwright 불필요 — curl만 사용한다.**

### 동적 테스트 전 필수 사항

actuator endpoint 테스트 시, 반드시 아래 가드 스크립트를 먼저 실행한다:

```bash
python3 <NOAH_SAST_DIR>/tools/validate_actuator.py "<테스트URL>" && curl -sI "<테스트URL>"
```

`validate_actuator.py`가 exit 1을 반환하면 curl이 실행되지 않는다. **`/actuator/shutdown`에 대한 HTTP 요청(GET/POST 모두)은 절대 수행하지 않는다.**

---

### 항목별 동적 검증

#### TRACE_ENABLED

```bash
curl -sI -X TRACE https://<host>/<path>
```

| 응답 | 판정 |
|------|------|
| 200 OK + `Content-Type: message/http` | 확인됨 |
| 405 Method Not Allowed | 제외 |
| 501 Not Implemented | 제외 |

#### WHITELABEL_ENABLED

존재하지 않는 경로로 요청하여 Whitelabel 에러 페이지 노출을 확인한다:

```bash
curl -s https://<host>/nonexistent_path_$(date +%s)
```

| 응답 | 판정 |
|------|------|
| 응답에 "Whitelabel Error Page" 문자열 포함 | 확인됨 |
| 커스텀 에러 페이지 또는 JSON 에러 응답 | 제외 |

#### STACKTRACE_EXPOSED

에러를 유발하여 스택트레이스 노출을 확인한다:

```bash
curl -s https://<host>/nonexistent_path_$(date +%s)
curl -s "https://<host>/<existing-path>?invalid_param[=broken"
```

| 응답 | 판정 |
|------|------|
| 응답에 `java.lang.`, `at org.springframework`, `.java:` 등 스택트레이스 패턴 | 확인됨 |
| 스택트레이스 없는 에러 응답 | 제외 |

#### SWAGGER_ENABLED

```bash
curl -sI https://<host>/swagger-ui.html
curl -sI https://<host>/swagger-ui/index.html
curl -sI https://<host>/v3/api-docs
curl -sI https://<host>/v2/api-docs
```

| 응답 | 판정 |
|------|------|
| 200 OK (하나라도) | 확인됨 |
| 모두 404 또는 401/403 | 제외 |

#### ACTUATOR_EXPOSED

```bash
python3 <NOAH_SAST_DIR>/tools/validate_actuator.py "https://<host>/actuator" && \
curl -s https://<host>/actuator
```

| 응답 | 판정 |
|------|------|
| 200 OK + JSON에 `_links` 포함 | 확인됨 |
| 404 또는 401/403 | 제외 |

#### ACTUATOR_OVEREXPOSED

actuator가 노출된 경우, 불필요한 endpoint 접근을 확인한다. **shutdown,refresh endpoint는 테스트하지 않는다.**

```bash
python3 <NOAH_SAST_DIR>/tools/validate_actuator.py "https://<host>/actuator/env" && \
curl -sI https://<host>/actuator/env

python3 <NOAH_SAST_DIR>/tools/validate_actuator.py "https://<host>/actuator/beans" && \
curl -sI https://<host>/actuator/beans

python3 <NOAH_SAST_DIR>/tools/validate_actuator.py "https://<host>/actuator/configprops" && \
curl -sI https://<host>/actuator/configprops

python3 <NOAH_SAST_DIR>/tools/validate_actuator.py "https://<host>/actuator/mappings" && \
curl -sI https://<host>/actuator/mappings

python3 <NOAH_SAST_DIR>/tools/validate_actuator.py "https://<host>/actuator/prometheus" && \
curl -sI https://<host>/actuator/prometheus
```

| 응답 | 판정 |
|------|------|
| 200 OK (하나라도) | 확인됨 (노출된 endpoint 목록 기재) |
| 모두 404 또는 401/403 | 제외 |

**shutdown / refresh endpoint 판정**: 동적 테스트를 수행하지 않는다. Phase 1 설정 파일 분석 결과만으로 판정한다.

#### H2_CONSOLE_ENABLED

```bash
curl -sI https://<host>/h2-console
curl -sI https://<host>/h2-console/
```

| 응답 | 판정 |
|------|------|
| 200 OK 또는 302 redirect (h2-console 관련 경로) | 확인됨 |
| 404 또는 401/403 | 제외 |

---

### 동적 검증 불가 항목

아래 항목은 Phase 1 분석 결과를 그대로 유지한다:

| 항목 | 사유 |
|------|------|
| `DAEMON_ROOT` | 런타임 프로세스 권한 확인 필요 (원격 테스트 불가) |
| `LOG_PERMISSION` | 파일시스템 권한 확인 필요 |
| `ADMIN_MBEAN_ENABLED` | JMX 포트 접근 필요 |
| `DEVTOOLS_PROD` | 빌드 설정 분석 결과 유지 |
| `OUTDATED_DEPS` | 버전 분석 결과 유지 |
