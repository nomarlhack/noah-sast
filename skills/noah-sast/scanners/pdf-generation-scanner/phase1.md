> **호출부 추적 — 실제 URL 경로 확정**: 모든 후보에 대해 라우트 정의 파일을 Read로 읽어 실제 URL 경로를 확정한다. 컴포넌트/파일 이름에서 경로를 유추하는 것은 확정이 아니다. 절차: (1) Sink의 호출부를 Grep → 최종 페이지 컴포넌트/컨트롤러 식별 (2) 라우트 정의(routes/index.tsx, @RequestMapping 등)를 Read로 읽어 경로 문자열 확인 (3) 후보 반환 시 근거 포함: `실제 경로: /home/apply (src/routes/index.tsx:42)`

### Phase 1: 정찰 (소스코드 분석)

PDF 생성 로직을 분석하여 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: PDF 생성 라이브러리 확인

   **Node.js:**
   - `puppeteer` / `playwright` — Chromium 기반, JavaScript 실행 가능, `file://` 접근 가능
   - `wkhtmltopdf` / `node-wkhtmltopdf` — WebKit 기반, JavaScript 실행 가능
   - `html-pdf` — PhantomJS 기반 (deprecated), 취약
   - `pdf-lib` — PDF 직접 생성 (HTML 렌더링 없음, 안전)
   - `pdfkit` — PDF 직접 생성 (안전)
   - `pdfmake` — PDF 직접 생성 (안전)

   **Python:**
   - `weasyprint` — CSS 기반 렌더링, JavaScript 미실행, `file://` 접근 가능
   - `wkhtmltopdf` / `pdfkit` — wkhtmltopdf 래퍼
   - `xhtml2pdf` / `pisa` — HTML 렌더링, 제한적 리소스 로딩
   - `reportlab` — PDF 직접 생성 (안전)

   **Java:**
   - `Flying Saucer` (xhtmlrenderer) — HTML/CSS 렌더링, JavaScript 미실행
   - `iText` / `OpenPDF` — PDF 직접 생성, HTML 파싱 시 리소스 로딩 가능
   - `Apache FOP` — XSL-FO 기반
   - `pd4ml` — HTML to PDF, `<pd4ml:attachment>` 태그 지원

   **PHP:**
   - `dompdf` — HTML 렌더링, `file://` 접근 가능 (설정에 따라)
   - `mpdf` — HTML 렌더링
   - `tcpdf` — PDF 직접 생성
   - `wkhtmltopdf` 래퍼

   **.NET:**
   - `Puppeteer Sharp` — Chromium 기반
   - `wkhtmltopdf` 래퍼
   - `IronPDF` — Chromium 기반

2. **Source 식별**: 사용자 입력이 PDF 생성 HTML에 삽입되는 경로
   - 사용자가 입력한 텍스트가 PDF 내용에 포함되는 경우 (이름, 주소, 메모 등)
   - 사용자가 HTML/마크다운을 직접 입력하는 경우
   - URL 파라미터가 PDF 생성에 사용되는 경우
   - 사용자가 PDF 템플릿을 선택하거나 커스터마이징하는 경우

3. **Sink 식별**: PDF 생성을 수행하는 코드

   **위험한 패턴 (사용자 입력이 HTML에 직접 삽입):**
   ```javascript
   // Puppeteer — 사용자 입력으로 HTML 생성 후 PDF 변환
   const html = `<h1>${userInput}</h1>`;
   await page.setContent(html);
   await page.pdf({ path: 'output.pdf' });
   ```

   ```python
   # WeasyPrint — 사용자 입력이 HTML에 삽입
   html = f"<h1>{user_input}</h1>"
   HTML(string=html).write_pdf('output.pdf')
   ```

   **안전한 패턴:**
   ```javascript
   // 사용자 입력을 HTML 이스케이프 후 삽입
   const escaped = escapeHtml(userInput);
   const html = `<h1>${escaped}</h1>`;
   ```

   ```javascript
   // PDF 직접 생성 (HTML 렌더링 없음)
   const doc = new PDFDocument();
   doc.text(userInput); // 텍스트로만 삽입, HTML 해석 없음
   ```

4. **PDF 라이브러리 설정 확인**:
   - `puppeteer`: `page.setContent()` 시 `waitUntil` 옵션, `--no-sandbox` 플래그
   - `wkhtmltopdf`: `--disable-local-file-access`, `--disable-javascript` 옵션
   - `weasyprint`: `url_fetcher` 커스터마이징으로 `file://` 차단 여부
   - `dompdf`: `DOMPDF_ENABLE_REMOTE`, `DOMPDF_ENABLE_PHP` 설정
   - HTML sanitization 적용 여부 (DOMPurify 등)

5. **후보 목록 작성**: 각 후보에 대해 "어떤 입력으로 어떻게 PDF에 의도하지 않은 내용을 포함시킬 수 있는지"를 구체적으로 구상. 데이터 흐름 추적을 완료한 뒤에도 공격 경로가 없으면 버린다. 추적 없이 직관으로 버리지 않는다..

## 후보 판정 제한

사용자 입력이 HTML→PDF 변환의 입력에 포함되는 경우만 후보.
