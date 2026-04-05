> **호출부 추적 — 실제 URL 경로 확정**: 모든 후보에 대해 라우트 정의 파일을 Read로 읽어 실제 URL 경로를 확정한다. 컴포넌트/파일 이름에서 경로를 유추하는 것은 확정이 아니다. 절차: (1) Sink의 호출부를 Grep → 최종 페이지 컴포넌트/컨트롤러 식별 (2) 라우트 정의(routes/index.tsx, @RequestMapping 등)를 Read로 읽어 경로 문자열 확인 (3) 후보 반환 시 근거 포함: `실제 경로: /home/apply (src/routes/index.tsx:42)`

### Phase 1: 정찰 (소스코드 분석)

사용자 입력 → XSLT 변환 경로를 추적하여 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: XSLT 프로세서/라이브러리 확인

   **Node.js:**
   - `xslt-processor` — 순수 JS 구현, 확장 기능 제한적
   - `libxslt` / `node-libxslt` — libxslt 바인딩, 확장 기능 가능
   - `saxon-js` — Saxon XSLT 3.0 프로세서
   - `xslt3` — XSLT 3.0 지원

   **Python:**
   - `lxml.etree.XSLT` — libxslt 기반
   - `xml.etree.ElementTree` — XSLT 미지원 (안전)
   - `saxonpy` — Saxon XSLT 프로세서

   **Java:**
   - `javax.xml.transform.TransformerFactory` — JAXP
   - `net.sf.saxon.TransformerFactoryImpl` — Saxon
   - `org.apache.xalan.processor.TransformerFactoryImpl` — Xalan

   **PHP:**
   - `XSLTProcessor` — libxslt 기반, `registerPHPFunctions()` 시 PHP 함수 호출 가능

   **.NET:**
   - `System.Xml.Xsl.XslCompiledTransform`
   - `System.Xml.Xsl.XslTransform` (deprecated)
   - `XsltSettings.EnableScript` — 스크립트 실행 허용 여부

2. **Source 식별**: 사용자가 제어 가능한 입력 중 XSLT에 반영될 수 있는 것
   - XML 데이터 입력 (XML 파일 업로드, XML API 요청)
   - XSLT 파라미터로 전달되는 사용자 입력
   - XSLT 스타일시트 자체를 업로드하거나 선택하는 기능
   - XSL-FO 변환 (PDF 생성 등)에 사용되는 입력

3. **Sink 식별**: XSLT 변환을 수행하는 코드

   **사용자 입력이 XSLT 스타일시트에 삽입 (위험):**
   ```java
   // Java — 사용자 입력으로 XSLT 문자열 생성
   String xslt = "<xsl:stylesheet>" + userInput + "</xsl:stylesheet>";
   Transformer transformer = factory.newTransformer(new StreamSource(new StringReader(xslt)));
   ```

   **사용자가 XSLT 파일을 선택/업로드 (위험):**
   ```python
   # Python — 사용자가 지정한 XSLT 파일 사용
   xslt = etree.parse(user_specified_xslt_path)
   transform = etree.XSLT(xslt)
   ```

   **사용자 입력이 XSLT 파라미터로 전달 (상대적으로 안전):**
   ```java
   // Java — 파라미터로 전달 (스타일시트는 고정)
   transformer.setParameter("name", userInput);
   ```

   **안전한 패턴:**
   - 고정된 XSLT 스타일시트 파일 사용 + 사용자 입력은 XML 데이터로만 전달
   - XSLT 파라미터를 통한 값 전달 (스타일시트 구조 변경 불가)
   - XSLT 확장 기능 비활성화

4. **프로세서 보안 설정 확인**:
   - Java: `TransformerFactory.setFeature()` — 확장 기능 비활성화 여부
   - .NET: `XsltSettings.EnableScript = false` (기본값) 확인
   - PHP: `XSLTProcessor::registerPHPFunctions()` 호출 여부 — 호출하지 않으면 PHP 함수 실행 불가
   - `document()` 함수 허용 여부
   - `xsl:include` / `xsl:import` 허용 여부

5. **후보 목록 작성**: 각 후보에 대해 "어떤 입력으로 어떻게 XSLT 변환을 조작할 수 있는지"를 구체적으로 구상. 데이터 흐름 추적을 완료한 뒤에도 공격 경로가 없으면 버린다. 추적 없이 직관으로 버리지 않는다..

## 후보 판정 제한

XSLT 변환 코드에 사용자 입력이 삽입되는 경우만 후보.
