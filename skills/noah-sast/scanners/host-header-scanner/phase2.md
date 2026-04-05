### Phase 2: 동적 테스트 (검증)

Phase 1 소스코드 분석이 완료되면 후보 목록을 사용자에게 보여준다. 후보가 존재하는 경우에만 동적 테스트를 진행한다. 후보가 0건이면 동적 테스트 없이 바로 보고서를 작성한다.

**동적 테스트 정보 획득:**

사용자에게는 테스트 대상 도메인(Host)과 직접 획득이 불가능한 정보(외부 콜백 서비스 URL, 프로덕션 전용 자격 증명 등)만 요청한다. 그 외의 정보는 소스코드 분석 또는 관련 엔드포인트에 직접 HTTP 요청을 보내 획득한다.

사용자가 동적 테스트를 원하지 않거나 정보를 제공하지 않으면, 소스코드 분석 결과의 모든 후보를 "후보"로 유지한 채 Phase 3으로 진행한다.

**Host Header Injection 테스트:**
```
# Host 헤더 변조 — 응답에 변조된 Host가 반영되는지 확인
curl "https://target.com/" -H "Host: evil.com" -v

# X-Forwarded-Host 변조
curl "https://target.com/" -H "X-Forwarded-Host: evil.com" -v

# 패스워드 리셋 — Host 변조 후 이메일에 변조된 URL이 포함되는지
curl -X POST "https://target.com/api/password-reset" \
  -H "Host: evil.com" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com"}'

# 가상 호스트 접근 — 다른 호스트명으로 내부 페이지 접근 시도
curl "https://target.com/admin" -H "Host: internal.target.com" -v
curl "https://target.com/admin" -H "Host: localhost" -v
```

**IP Spoofing 테스트:**
```
# X-Forwarded-For 변조 — 내부 IP로 위장
curl "https://target.com/admin" -H "X-Forwarded-For: 127.0.0.1" -v
curl "https://target.com/admin" -H "X-Forwarded-For: 10.0.0.1" -v
curl "https://target.com/admin" -H "X-Forwarded-For: 192.168.0.1" -v

# X-Real-IP 변조
curl "https://target.com/admin" -H "X-Real-IP: 127.0.0.1" -v

# X-CLUSTER-CLIENT-IP 변조
curl "https://target.com/admin" -H "X-CLUSTER-CLIENT-IP: 127.0.0.1" -v

# X-Client-IP 변조
curl "https://target.com/admin" -H "X-Client-IP: 127.0.0.1" -v

# True-Client-IP 변조 (Akamai)
curl "https://target.com/admin" -H "True-Client-IP: 127.0.0.1" -v

# CF-Connecting-IP 변조 (Cloudflare)
curl "https://target.com/admin" -H "CF-Connecting-IP: 127.0.0.1" -v

# X-Original-URL / X-Rewrite-URL — 경로 우회
curl "https://target.com/" -H "X-Original-URL: /admin" -v
curl "https://target.com/" -H "X-Rewrite-URL: /admin" -v

# 복합 헤더 변조
curl "https://target.com/admin" \
  -H "X-Forwarded-For: 127.0.0.1" \
  -H "X-Real-IP: 127.0.0.1" \
  -H "X-Client-IP: 127.0.0.1" -v
```

**검증 기준:**
- **확인됨**: 동적 테스트로 헤더 변조를 통해 보안이 우회된 것을 직접 확인함 (내부 자산 접근, 응답에 변조된 Host 반영, IP 접근제어 우회 등)
- **후보**: 동적 테스트를 수행하지 않았거나, 동적 테스트로 확인이 불가하여 수동 확인이 필요한 경우
- **"확인됨"은 동적 테스트를 통해서만 부여할 수 있다**: 소스코드 분석만으로는 아무리 취약해 보여도 "확인됨"으로 보고하지 않는다. 동적 테스트로 실제 트리거를 확인한 경우에만 "확인됨"이다. 동적 테스트를 수행하지 않았으면 모든 결과는 "후보"이다.
- **보고서 제외**: 동적 테스트 결과 취약하지 않은 것으로 확인된 경우는 보고서에 포함하지 않는다
