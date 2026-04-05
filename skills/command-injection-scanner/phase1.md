> **호출부 추적 — 실제 URL 경로 확정**: 모든 후보에 대해 라우트 정의 파일을 Read로 읽어 실제 URL 경로를 확정한다. 컴포넌트/파일 이름에서 경로를 유추하는 것은 확정이 아니다. 절차: (1) Sink의 호출부를 Grep → 최종 페이지 컴포넌트/컨트롤러 식별 (2) 라우트 정의(routes/index.tsx, @RequestMapping 등)를 Read로 읽어 경로 문자열 확인 (3) 후보 반환 시 근거 포함: `실제 경로: /home/apply (src/routes/index.tsx:42)`

### Phase 1: 정찰 (소스코드 분석)

사용자 입력 → 시스템 명령어 실행 경로를 추적하여 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: 프레임워크/언어 확인

2. **Source 식별**: 사용자가 제어 가능한 입력 중 명령어에 사용될 수 있는 것
   - HTTP 파라미터: `host`, `ip`, `address`, `domain`, `cmd`, `command`, `filename`, `path`, `url`, `ping`, `target`
   - 파일 업로드의 파일명 (파일 처리 명령어에 사용되는 경우)
   - API 요청 본문의 필드

3. **Sink 식별**: 시스템 명령어를 실행하는 코드

   **Node.js:**
   - `child_process.exec()` — 셸을 통해 실행, 가장 위험
   - `child_process.execSync()`
   - `child_process.spawn()` — `shell: true` 옵션 시 위험
   - `child_process.spawnSync()` — `shell: true` 옵션 시 위험
   - `child_process.execFile()` — 셸 미사용, 상대적으로 안전
   - `child_process.fork()` — Node.js 모듈 실행
   - `` require('child_process') `` 전체

   **Python:**
   - `os.system()`
   - `os.popen()`
   - `subprocess.call()`, `subprocess.run()`, `subprocess.Popen()` — `shell=True` 시 위험
   - `subprocess.check_output()` — `shell=True` 시 위험
   - `commands.getoutput()` (Python 2)

   **Java:**
   - `Runtime.getRuntime().exec()`
   - `ProcessBuilder`
   - `new ProcessBuilder().command()`

   **Ruby:**
   - `` `command` `` (backtick)
   - `system()`, `exec()`
   - `IO.popen()`, `Open3.capture3()`
   - `%x{command}`

   **PHP:**
   - `exec()`, `system()`, `passthru()`, `shell_exec()`
   - `` `command` `` (backtick)
   - `proc_open()`, `popen()`
   - `pcntl_exec()`

4. **경로 추적**: Source에서 Sink까지 데이터가 명령어 이스케이프 없이 도달하는 경로 확인. 다음을 점검:
   - 명령어 구분자(`;`, `|`, `&&`, `||`, `` ` ``, `$()`, `\n`) 필터링 여부
   - `exec()` 대신 `execFile()`/`spawn()`(shell: false) 사용 여부 — 인자 배열 방식은 안전
   - `escapeshellarg()` / `escapeshellcmd()` (PHP) 사용 여부
   - `shlex.quote()` (Python) 사용 여부
   - 입력값 화이트리스트 검증 (예: IP 주소 정규식 검증)

5. **후보 목록 작성**: 각 후보에 대해 "어떤 입력으로 어떻게 추가 명령어를 실행할 수 있는지"를 구체적으로 구상. 데이터 흐름 추적을 완료한 뒤에도 공격 경로가 없으면 버린다. 추적 없이 직관으로 버리지 않는다..

#### 안전한 패턴 (취약하지 않은 코드)

- `spawn('ping', ['-c', '1', userInput])` — shell: false(기본값), 인자 배열 → 안전
- `execFile('/usr/bin/ping', [userInput])` — 셸 미사용 → 안전
- `exec("ping " + ip)` where ip is validated with `/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/` → 안전
- `subprocess.run(['ping', '-c', '1', user_input])` — shell=False(기본값), 리스트 → 안전

## 후보 판정 제한

사용자 HTTP 입력이 명령어 인자에 도달하는 경우만 후보. 빌드 스크립트, 개발 도구는 제외.
