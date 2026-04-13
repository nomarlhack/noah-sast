### Phase 2: 동적 테스트 (Source Map 다운로드)

**Step 1: JS/CSS 파일 수집**
```
# 메인 페이지의 HTML에서 JS/CSS 파일 URL 추출
curl -s "https://target.com/" | grep -oP '(src|href)="[^"]*\.(js|css)"' | grep -oP '"[^"]*"' | tr -d '"'

# 또는 소스코드의 빌드 출력 디렉토리에서 파일 목록 확인
```

**Step 2: sourceMappingURL 확인**
```
# 각 JS 파일의 마지막 줄에서 sourceMappingURL 확인
curl -s "https://target.com/static/js/main.abc123.js" | tail -5
# //# sourceMappingURL=main.abc123.js.map 이 있으면 Source Map 존재

# CSS 파일도 확인
curl -s "https://target.com/static/css/main.abc123.css" | tail -5
```

**Step 3: Source Map 다운로드**
```
# .map 파일 다운로드 시도
curl -o sourcemap.json "https://target.com/static/js/main.abc123.js.map" -v
# 200 OK이면 다운로드 성공 → 노출 확인

# sourceMappingURL이 없어도 .map 확장자를 붙여 시도
curl -o sourcemap.json "https://target.com/static/js/main.abc123.js.map" -v
```

**Step 4: Source Map에서 원본 소스 복원 및 민감 정보 분석**
다운로드된 Source Map JSON에서 `sourcesContent` 필드를 추출하여 원본 소스코드를 복원한 뒤, 민감 정보를 검색한다.

**검색 대상 패턴:**
- API 키/시크릿: `apiKey`, `api_key`, `secret`, `SECRET_KEY`, `PRIVATE_KEY`, `token`, `password`, `credential`
- AWS 키: `AKIA`, `aws_access_key_id`, `aws_secret_access_key`
- 내부 URL: `internal`, `admin`, `staging`, `dev.`, `localhost`, `127.0.0.1`, `10.0.`, `192.168.`
- DB 연결: `mongodb://`, `postgres://`, `mysql://`, `redis://`
- 주석 메모: `TODO`, `FIXME`, `HACK`, `XXX`, `BUG`, `VULNERABILITY`
- 환경변수 인라인: `process.env.` 뒤에 실제 값이 치환되어 있는 경우
- 하드코딩된 자격 증명: `password=`, `passwd=`, `Basic ` (Base64), `Bearer `

**검증 기준:**
- **확인됨**: Source Map 파일이 다운로드 가능하고, 원본 소스코드가 복원되어 민감 정보가 발견됨
- **후보**: 동적 테스트를 수행하지 않았거나, Source Map은 다운로드되었으나 민감 정보 분석을 수동으로 확인해야 하는 경우
- **보고서 제외**: Source Map이 404로 접근 불가하거나, `sourceMappingURL`이 없고 .map 파일도 존재하지 않는 경우

## Phase 2 완료 조건

다음 항목을 모두 충족해야 Phase 2가 완료된 것으로 간주한다.

- .map 파일 다운로드 시도 여부 및 HTTP 응답 코드
- 다운로드 성공 시, sourcesContent에서 민감 정보 패턴 검색 수행 여부
- 검색 결과 (발견된 민감 정보 목록 또는 "민감 정보 없음")
