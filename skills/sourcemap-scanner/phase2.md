### Phase 2: 동적 테스트 (Source Map 다운로드)

Phase 1 분석이 완료되면 후보 목록을 사용자에게 보여준다. 후보가 존재하는 경우에만 동적 테스트를 진행한다. 후보가 0건이면 동적 테스트 없이 바로 보고서를 작성한다.

**동적 테스트 정보 획득:**

사용자에게는 테스트 대상 도메인(Host)과 직접 획득이 불가능한 정보(외부 콜백 서비스 URL, 프로덕션 전용 자격 증명 등)만 요청한다. 그 외의 정보는 소스코드 분석 또는 관련 엔드포인트에 직접 HTTP 요청을 보내 획득한다.

사용자가 동적 테스트를 원하지 않거나 정보를 제공하지 않으면, 소스코드 분석 결과의 모든 후보를 "후보"로 유지한 채 Phase 3으로 진행한다.

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
- **"확인됨"은 동적 테스트를 통해서만 부여할 수 있다**: 소스코드 분석만으로는 아무리 취약해 보여도 "확인됨"으로 보고하지 않는다. 동적 테스트로 실제 트리거를 확인한 경우에만 "확인됨"이다. 동적 테스트를 수행하지 않았으면 모든 결과는 "후보"이다.
- **보고서 제외**: Source Map이 404로 접근 불가하거나, `sourceMappingURL`이 없고 .map 파일도 존재하지 않는 경우

## Phase 2 완료 조건

다음 항목을 모두 충족해야 Phase 2가 완료된 것으로 간주한다.

- .map 파일 다운로드 시도 여부 및 HTTP 응답 코드
- 다운로드 성공 시, sourcesContent에서 민감 정보 패턴 검색 수행 여부
- 검색 결과 (발견된 민감 정보 목록 또는 "민감 정보 없음")
