---
name: command-injection-scanner
description: "소스코드 분석과 동적 테스트를 통해 Command Injection(OS Command Injection) 취약점을 탐지하는 스킬. 사용자 입력이 시스템 명령어에 반영되는 경로를 추적하고, 실제로 임의 명령어가 실행될 수 있는지 검증한다. 사용자가 'command injection 찾아줘', '커맨드 인젝션 스캔', 'OS command injection', '명령어 삽입 취약점', 'RCE 점검', 'command injection audit' 등을 요청할 때 이 스킬을 사용한다."
grep_patterns:
  - "child_process"
  - "exec("
  - "execSync("
  - "spawn("
  - "spawnSync("
  - "os\\.system("
  - "os\\.popen("
  - "subprocess\\.call("
  - "subprocess\\.run("
  - "subprocess\\.Popen("
  - "Runtime\\.getRuntime"
  - "ProcessBuilder"
  - "%x{"
  - "shell: true"
  - "shell=True"
  # Source patterns
  - "@RequestParam"
  - "@RequestBody"
  - "req\\.query"
  - "req\\.body"
---

# Command Injection Scanner

소스코드 분석으로 Command Injection 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 임의 명령어가 실행될 수 있는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "명령어가 실행되지 않으면 취약점이 아니다"

소스코드에서 `exec(userInput)`이 있다고 바로 Command Injection으로 보고하지 않는다. 실제로 사용자가 제어한 입력에 `;`, `|`, `&&`, `` ` `` 등 명령어 구분자를 삽입하여 추가 명령어가 실행되는 것을 확인해야 취약점이다.

## Command Injection의 유형

### Direct Command Injection
사용자 입력이 시스템 명령어 문자열에 직접 삽입되는 경우. `exec("ping " + userInput)` 형태.

### Indirect Command Injection
사용자 입력이 파일, 환경변수, 데이터베이스 등을 거쳐 시스템 명령어에 도달하는 경우. 소스코드만으로는 추적이 어려울 수 있다.

### Argument Injection
명령어 자체는 고정이지만 인자(argument)를 사용자가 제어하는 경우. `--output=/etc/crontab` 같은 옵션 삽입으로 의도하지 않은 동작을 유발.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 이 스킬과 같은 skills 디렉토리 내의 `noah-sast/agent-guidelines.md`를 참조한다. 이 파일의 위치를 기준으로 `../noah-sast/agent-guidelines.md` 경로로 접근할 수 있다.
