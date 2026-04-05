# Noah SAST

Claude Code 기반 정적/동적 통합 취약점 스캐너 스킬 모음.

35개 개별 취약점 스캐너를 순차적으로 실행하고, 모든 결과를 하나의 통합 보고서로 작성합니다.

## 설치

`skills/` 디렉토리의 내용을 `~/.claude/skills/`에 복사합니다.

```bash
cp -r skills/* ~/.claude/skills/
```

## 스킬 구성

### 메인 스킬
| 스킬 | 설명 |
|------|------|
| `noah-sast` | 35개 스캐너 통합 실행 및 보고서 생성 |
| `scan-report` | 스캔 결과를 Markdown/HTML 보고서로 작성 |
| `scan-report-review` | 보고서 정확성을 소스코드와 대조 검증 |
| `chain-analysis` | 개별 취약점 간 연계 공격 시나리오 분석 |
| `webapp-testing` | Playwright 기반 동적 테스트 도구 |

### 취약점 스캐너 (35개)
| 카테고리 | 스캐너 |
|----------|--------|
| **Injection** | `sqli-scanner`, `nosqli-scanner`, `command-injection-scanner`, `ldap-injection-scanner`, `xpath-injection-scanner`, `xslt-injection-scanner`, `ssti-scanner` |
| **XSS** | `xss-scanner`, `dom-xss-scanner`, `css-injection-scanner` |
| **Request Forgery** | `ssrf-scanner`, `csrf-scanner` |
| **파일/경로** | `path-traversal-scanner`, `file-upload-scanner`, `zipslip-scanner` |
| **인증/인가** | `jwt-scanner`, `oauth-scanner`, `saml-scanner`, `idor-scanner` |
| **HTTP** | `http-method-tampering-scanner`, `http-smuggling-scanner`, `crlf-injection-scanner`, `host-header-scanner`, `open-redirect-scanner` |
| **XML/데이터** | `xxe-scanner`, `deserialization-scanner`, `csv-injection-scanner`, `prototype-pollution-scanner` |
| **API/프로토콜** | `graphql-scanner`, `websocket-scanner`, `soapaction-spoofing-scanner` |
| **기타** | `redos-scanner`, `pdf-generation-scanner`, `sourcemap-scanner`, `subdomain-takeover-scanner` |

## 사용법

Claude Code에서:

```
noah-sast
```

또는 개별 스캐너 실행:

```
xss-scanner
sqli-scanner
```

## 라이선스

Internal use only.
