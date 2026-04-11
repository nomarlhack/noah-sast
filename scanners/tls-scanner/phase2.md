### Phase 2: 동적 테스트 (검증)

> 공통 시작 절차 / 공통 검증 기준은 `prompts/guidelines-phase2.md` 지침 7에 정의되어 있다. 이 파일은 TLS 스캐너의 고유 절차만 다룬다.

**도구 선택:** TLS 핸드셰이크 직접 검사가 필요하므로 **openssl s_client + curl**을 사용한다. Playwright는 사용하지 않는다.

---

## 기본 원칙

- 모든 판정은 **실제 TLS 핸드셰이크 결과**로 한다. 코드/설정 파일에서 "취약할 것 같다"는 이유만으로 확인됨 판정하지 않는다.
- 코드/설정에 취약 설정이 있어도 서버가 실제로 거부하면 **보고서 제외** (인프라 계층 보강). 코드에 없어도 서버가 수락하면 **확인됨**.
- 각 테스트는 `timeout 10`을 붙여 10초 내 응답이 없으면 중단한다.
- HSTS 헤더 검사는 수행하지 않는다 — `security-headers-scanner`가 담당한다.

---

## Test 1: 프로토콜 버전 스캔

Phase 1 후보 중 `TLS_WEAK_VERSION`, `TLS_DOWNGRADE` 라벨에 해당하는 항목을 검증한다.

각 취약 프로토콜에 대해 핸드셰이크를 시도하여 서버 수락 여부를 확인한다.

```bash
echo | timeout 10 openssl s_client -connect <host>:443 -ssl3 2>&1 | grep -E "Protocol|alert|handshake failure"
echo | timeout 10 openssl s_client -connect <host>:443 -tls1 2>&1 | grep -E "Protocol|alert|handshake failure"
echo | timeout 10 openssl s_client -connect <host>:443 -tls1_1 2>&1 | grep -E "Protocol|alert|handshake failure"
```

안전한 프로토콜 지원 확인:
```bash
echo | timeout 10 openssl s_client -connect <host>:443 -tls1_2 2>&1 | grep -E "Protocol|Cipher"
echo | timeout 10 openssl s_client -connect <host>:443 -tls1_3 2>&1 | grep -E "Protocol|Cipher"
```

**검증 기준:**

| 응답 | 판정 |
|------|------|
| SSLv3, TLS 1.0, TLS 1.1 핸드셰이크 성공 (`Protocol  : TLSv1` 등 출력) | 확인됨 |
| `alert protocol version` 또는 `handshake failure` | 안전 (해당 프로토콜 거부) |
| TLS 1.2, TLS 1.3 모두 실패 | 별도 보고 (서버 접근 불가 가능성) |

---

## Test 2: Cipher Suite 점검

Phase 1 후보 중 `TLS_WEAK_CIPHER`, `TLS_NO_PFS`, `TLS_PADDING_ORACLE` 라벨에 해당하는 항목을 검증한다.

```bash
# NULL/익명 cipher 수락 여부
echo | timeout 10 openssl s_client -connect <host>:443 -cipher 'NULL:eNULL:aNULL' 2>&1 | grep -E "Cipher|alert|handshake failure"

# EXPORT 등급 cipher
echo | timeout 10 openssl s_client -connect <host>:443 -cipher 'EXPORT' 2>&1 | grep -E "Cipher|alert|handshake failure"

# DES/3DES
echo | timeout 10 openssl s_client -connect <host>:443 -cipher 'DES:3DES' 2>&1 | grep -E "Cipher|alert|handshake failure"

# RC4
echo | timeout 10 openssl s_client -connect <host>:443 -cipher 'RC4' 2>&1 | grep -E "Cipher|alert|handshake failure"

# 현재 협상된 cipher 확인
echo | timeout 10 openssl s_client -connect <host>:443 2>&1 | grep -E "Cipher    :|Protocol  :"
```

**검증 기준:**

| 응답 | 판정 |
|------|------|
| 약한 cipher로 핸드셰이크 성공 (`Cipher    : RC4-SHA` 등) | 확인됨 |
| `handshake failure` 또는 `no ciphers available` | 안전 (해당 cipher 거부) |
| 현재 cipher가 PFS 미지원 (ECDHE/DHE 없는 RSA 키 교환) | 확인됨 (TLS_NO_PFS) |

---

## Test 3: 인증서 체인 검증

Phase 1 후보 중 `TLS_NO_CERT_VERIFY`, `TLS_TRUST_ALL`, `TLS_WEAK_KEY` 라벨의 서버 측 인증서를 검증한다.

```bash
echo | timeout 10 openssl s_client -connect <host>:443 -showcerts 2>&1 | grep -E "Verify return code|subject=|issuer=|notAfter"
```

인증서 상세 정보 (키 강도 포함):
```bash
echo | timeout 10 openssl s_client -connect <host>:443 2>&1 | openssl x509 -noout -text 2>&1 | grep -E "Public-Key:|ASN1 OID:|Signature Algorithm:|Not After"
```

**검증 기준:**

| 응답 | 판정 |
|------|------|
| `Verify return code: 0 (ok)` | 인증서 체인 정상 |
| `Verify return code: 18 (self-signed certificate)` | 확인됨 (자체서명 — 프로덕션 서버인 경우) |
| `Verify return code: 10 (certificate has expired)` | 확인됨 (만료) |
| `Verify return code: 21 (unable to verify the first certificate)` | 확인됨 (불완전 체인) |
| `Public-Key: (1024 bit)` (RSA < 2048) | 확인됨 (TLS_WEAK_KEY) |
| `ASN1 OID: prime192v1` (ECDSA < 256비트) | 확인됨 (TLS_WEAK_KEY) |
| `Public-Key: (2048 bit)` 이상 또는 `ASN1 OID: prime256v1` 이상 | 안전 |

---

## Test 4: Heartbleed (CVE-2014-0160)

Phase 1 후보 중 `TLS_HEARTBLEED_VER` 라벨에 해당하는 항목을 검증한다.

```bash
# heartbeat 확장 지원 여부 확인
echo | timeout 10 openssl s_client -connect <host>:443 -tlsextdebug 2>&1 | grep -i "heartbeat"

# 서버 OpenSSL 버전 확인 (가능한 경우)
echo | timeout 10 openssl s_client -connect <host>:443 2>&1 | grep -i "Server.*OpenSSL"
```

**검증 기준:**

| 응답 | 판정 |
|------|------|
| heartbeat 확장 활성화 + OpenSSL 1.0.1 ~ 1.0.1f 버전 확인 | 확인됨 |
| heartbeat 확장 활성화 + 버전 확인 불가 | 후보 (수동 확인 필요) |
| heartbeat 확장 미지원 | 안전 |
| OpenSSL 1.0.1g 이상 | 안전 |

---

## Test 5: TLS 압축 (CRIME)

Phase 1 후보 중 `TLS_COMPRESSION` 라벨에 해당하는 항목을 검증한다.

```bash
echo | timeout 10 openssl s_client -connect <host>:443 2>&1 | grep "Compression:"
```

**검증 기준:**

| 응답 | 판정 |
|------|------|
| `Compression: zlib` 또는 `NONE` 이외의 값 | 확인됨 |
| `Compression: NONE` | 안전 |

---

## Test 6: TLS Renegotiation

클라이언트 주도 안전하지 않은 재협상 가능 여부를 확인한다.

```bash
echo "R" | timeout 10 openssl s_client -connect <host>:443 2>&1 | grep -E "Secure Renegotiation|renegotiation"
```

**검증 기준:**

| 응답 | 판정 |
|------|------|
| `Secure Renegotiation IS NOT supported` | 확인됨 (안전하지 않은 재협상) |
| `Secure Renegotiation IS supported` | 안전 |

---

## Test 7: SSL 스트리핑 방어 (HSTS + HTTP→HTTPS 리다이렉트)

SSL 스트리핑 방어는 **리다이렉트 + HSTS** 두 가지가 함께 있어야 완성된다. 리다이렉트만으로는 중간자가 응답을 가로챌 수 있으므로, HSTS가 브라우저에 "이 도메인은 무조건 HTTPS"를 기억시켜야 방어가 완성된다.

**7-1: HTTP→HTTPS 리다이렉트 확인**
```bash
curl -sI -o /dev/null -w "%{http_code} %{redirect_url}" "http://<host>/" 2>&1
```

**7-2: HSTS 헤더 확인**
```bash
curl -sI "https://<host>/" | grep -i '^strict-transport-security:'
```

**검증 기준:**

| 응답 | 판정 |
|------|------|
| HTTP 리다이렉트 없음 (200) + HSTS 없음 | 확인됨 (SSL 스트리핑 완전 노출) |
| HTTP 리다이렉트 있음 + HSTS 없음 | 확인됨 (HSTS_MISSING — 리다이렉트만으로 sslstrip 방어 불가) |
| HTTP 리다이렉트 있음 + HSTS `max-age` < 31536000 | 확인됨 (HSTS_SHORT_MAXAGE) |
| HTTP 리다이렉트 있음 + HSTS `max-age` >= 31536000 | 안전 |
| 연결 거부 (포트 80 미운영) + HSTS 있음 | 안전 |
| 연결 거부 (포트 80 미운영) + HSTS 없음 | 후보 (HTTP 미운영이지만 HSTS 미설정) |

---

## 유의사항

- `openssl s_client` 명령이 시스템에 설치되어 있지 않은 경우 `[도구 한계]`로 표시한다. 설치 시도는 하지 않는다.
- 비표준 포트(8443 등)를 사용하는 경우 Phase 1 소스코드 분석에서 확인된 포트로 테스트한다.
- 서버가 SNI를 요구하는 경우 `-servername <host>` 옵션을 추가한다:
  ```bash
  echo | timeout 10 openssl s_client -connect <host>:443 -servername <host> 2>&1
  ```
- 로컬 openssl 버전이 낮아 `-tls1_3` 옵션을 지원하지 않는 경우, 해당 테스트만 건너뛰고 사유를 기재한다.
