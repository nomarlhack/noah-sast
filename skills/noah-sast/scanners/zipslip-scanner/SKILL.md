---
name: zipslip-scanner
description: "소스코드 분석과 동적 테스트를 통해 Zip Slip(Archive Path Traversal) 취약점을 탐지하는 스킬. 압축 파일(ZIP, TAR, JAR 등) 해제 시 엔트리 경로에 대한 검증이 누락되어 의도하지 않은 디렉토리에 파일이 덮어쓰여질 수 있는지 분석하고 검증한다. 사용자가 'Zip Slip 찾아줘', 'ZipSlip 스캔', 'archive path traversal', '압축 해제 취약점', 'Zip Slip audit', 'tar slip', 'zip 경로 조작' 등을 요청할 때 이 스킬을 사용한다."
grep_patterns:
  - "adm-zip"
  - "unzipper"
  - "unzip-stream"
  - "yauzl"
  - "decompress"
  - "zipfile\\.extractall("
  - "zipfile\\.extract("
  - "tarfile\\.extractall("
  - "ZipInputStream"
  - "ZipFile"
  - "ZipArchive::extractTo("
  - "extractAllTo("
  - "extractEntryTo("
  - "Zip::"
  - "tar\\.extract"
---

# Zip Slip Scanner

소스코드 분석으로 Zip Slip 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 압축 해제 시 의도하지 않은 경로에 파일이 생성되는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "의도하지 않은 경로에 파일이 생성되지 않으면 취약점이 아니다"

소스코드에서 압축 해제 기능이 있다고 바로 취약점으로 보고하지 않는다. 실제로 `../../../etc/cron.d/malicious` 같은 경로를 가진 엔트리가 포함된 악성 압축 파일을 업로드하여 대상 디렉토리 밖에 파일이 생성되는 것을 확인해야 취약점이다.

## Zip Slip의 원리

압축 파일(ZIP, TAR, JAR, WAR, CPIO 등)의 엔트리 이름에는 `../`가 포함될 수 있다. 압축 해제 시 엔트리 이름을 그대로 파일 경로로 사용하면, `../../malicious.sh` 같은 엔트리가 해제 대상 디렉토리 밖의 임의 위치에 파일을 생성하거나 기존 파일을 덮어쓸 수 있다.

```
# 정상 ZIP 엔트리
data/report.csv → /tmp/extract/data/report.csv

# 악성 ZIP 엔트리 (Zip Slip)
../../../etc/cron.d/backdoor → /etc/cron.d/backdoor
```

## 취약점의 유형

### 파일 덮어쓰기 (Arbitrary File Overwrite)
기존 시스템 파일이나 설정 파일을 덮어써서 RCE나 권한 상승으로 이어지는 경우. `cron`, `.bashrc`, `.ssh/authorized_keys`, 웹 루트의 파일 등을 대상으로 한다.

### 웹셸 배치
웹 루트 디렉토리에 악성 스크립트를 배치하여 원격 코드 실행을 달성하는 경우.

### 설정 파일 변조
애플리케이션 설정 파일을 변조하여 동작을 변경하는 경우.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 `../../agent-guidelines.md` (이 파일 기준 상대 경로)를 참조한다.
