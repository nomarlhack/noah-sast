---
name: file-upload-scanner
description: "소스코드 분석과 동적 테스트를 통해 File Upload 취약점을 탐지하는 스킬. 파일 업로드 기능에서 파일 유형/확장자/크기 검증이 누락되어 웹셸이나 악성 파일이 업로드·실행될 수 있는지 분석하고 검증한다. 사용자가 '파일 업로드 취약점 찾아줘', 'file upload 스캔', '업로드 취약점 점검', '웹셸 업로드', 'unrestricted file upload', '파일 업로드 audit' 등을 요청할 때 이 스킬을 사용한다."
grep_patterns:
  - "multer"
  - "formidable"
  - "busboy"
  - "multiparty"
  - "express-fileupload"
  - "FileField"
  - "ImageField"
  - "request\\.files"
  - "UploadFile"
  - "MultipartFile"
  - "move_uploaded_file"
  - "ActiveStorage"
  - "CarrierWave"
  - "Shrine"
  - "multipart/form-data"
  - "content_type"
  - "@RequestPart"
  - "contentType"
---

# File Upload Scanner

소스코드 분석으로 파일 업로드 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 위험한 파일이 업로드되고 접근/실행될 수 있는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "악성 파일이 업로드되고 접근 가능하지 않으면 취약점이 아니다"

파일 업로드 기능이 있다고 바로 취약점으로 보고하지 않는다. 다음 조건이 모두 충족되어야 취약점이다:
1. 위험한 파일(웹셸, 실행 파일 등)이 업로드됨
2. 업로드된 파일에 접근할 수 있음 (URL로 직접 접근 가능)
3. 파일이 서버에서 실행되거나, 다른 사용자에게 서빙됨

검증 없이 "업로드 기능에 확장자 검증이 없다"고만 보고하는 것은 부족하다. 업로드된 파일이 어디에 저장되고, 어떻게 서빙되는지까지 추적해야 한다.

## File Upload 취약점의 유형

### 웹셸 업로드
서버사이드 스크립트(.php, .jsp, .asp 등)를 업로드하고 웹 서버가 이를 실행하는 경우. 서버 완전 장악으로 이어진다.

### 악성 콘텐츠 업로드
HTML/SVG 파일을 업로드하고 같은 도메인에서 서빙되어 Stored XSS가 발생하는 경우. 또는 .exe, .bat 등 실행 파일이 다른 사용자에게 다운로드되는 경우.

### 경로 조작을 통한 업로드
업로드 파일명에 `../`를 삽입하여 의도하지 않은 디렉토리에 파일을 저장하는 경우 (Zip Slip 포함).

### 서비스 거부 (DoS)
파일 크기 제한이 없어 대용량 파일 업로드로 서버 리소스를 고갈시키는 경우. 이 스캐너에서는 소스코드 분석만 수행하고 실제 DoS 테스트는 하지 않는다.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 이 스킬과 같은 skills 디렉토리 내의 `noah-sast/agent-guidelines.md`를 참조한다. 이 파일의 위치를 기준으로 `../noah-sast/agent-guidelines.md` 경로로 접근할 수 있다.
