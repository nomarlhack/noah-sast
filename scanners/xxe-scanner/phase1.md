> ## 핵심 원칙: "외부 엔티티가 처리되지 않으면 취약점이 아니다"
>
> 소스코드에서 XML 파서를 사용한다고 바로 XXE로 보고하지 않는다. 실제로 `<!DOCTYPE>` 선언에 외부 엔티티를 정의하고, 해당 엔티티가 파서에 의해 해석되어 파일 내용이 반환되거나 외부 요청이 발생하는 것을 확인해야 취약점이다.
>
> 대부분의 최신 XML 파서는 기본적으로 외부 엔티티를 비활성화하고 있다. 파서 버전과 설정을 반드시 확인해야 한다.
>

### Phase 1: 정찰 (소스코드 분석)

XML 파서 사용처를 찾고, 외부 엔티티 처리가 활성화되어 있는지 확인한다.

1. **프로젝트 스택 파악**: 프레임워크/언어/XML 파서 라이브러리 확인

2. **XML 입력 경로 식별**: 사용자가 XML을 제출할 수 있는 진입점
   - `Content-Type: application/xml` 또는 `text/xml`을 처리하는 엔드포인트
   - SOAP API 엔드포인트
   - XML 파일 업로드 (SVG, XLSX, DOCX, RSS 피드 등 — XML 기반 포맷 포함)
   - XML-RPC 엔드포인트
   - SAML 인증 처리
   - 설정 파일 파싱 (사용자가 업로드하는 설정 XML)

3. **Sink 식별**: XML을 파싱하는 코드

   **Node.js:**
   - `xml2js` — 기본적으로 외부 엔티티 비활성화 (안전)
   - `libxmljs` — `noent: true` 옵션 시 위험
   - `xmldom` / `@xmldom/xmldom` — 외부 엔티티 처리 여부 확인
   - `fast-xml-parser` — 기본적으로 안전
   - `sax` — 스트리밍 파서, 엔티티 처리 설정 확인
   - `express-xml-bodyparser` — 내부 파서 설정 확인

   **Python:**
   - `xml.etree.ElementTree` — Python 3.8+ 기본 안전, 이전 버전 위험
   - `lxml.etree` — `resolve_entities=True` (기본값) 시 위험
   - `xml.dom.minidom` — 외부 엔티티 처리 가능
   - `xml.sax` — `feature_external_ges` 활성화 시 위험
   - `defusedxml` — 안전한 래퍼 (사용하면 안전)

   **Java:**
   - `DocumentBuilderFactory` — 기본적으로 외부 엔티티 활성화 (위험)
   - `SAXParserFactory` — 기본적으로 위험
   - `XMLInputFactory` (StAX) — `IS_SUPPORTING_EXTERNAL_ENTITIES` 설정 확인
   - `TransformerFactory` — XSLT 처리 시 XXE 가능
   - `javax.xml.bind.Unmarshaller` (JAXB) — 설정에 따라 위험

   **Ruby:**
   - `Nokogiri` — 기본적으로 외부 엔티티 비활성화 (안전), `NONET` 옵션 확인
   - `REXML` — 외부 엔티티 처리 가능

   **PHP:**
   - `simplexml_load_string()` — `LIBXML_NOENT` 플래그 시 위험
   - `DOMDocument::loadXML()` — 기본적으로 외부 엔티티 활성화 (위험)
   - `libxml_disable_entity_loader(true)` — PHP 8.0 이전 방어 함수

4. **파서 설정 확인**: 외부 엔티티 처리가 활성화되어 있는지 확인
   - Java: `setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)` 또는 `setFeature("http://xml.org/sax/features/external-general-entities", false)` 설정 여부
   - Python/lxml: `resolve_entities=False` 설정 여부
   - Node.js: 파서별 옵션 확인
   - PHP: `libxml_disable_entity_loader()` 호출 여부

5. **후보 목록 작성**: 외부 엔티티 처리가 활성화된 XML 파서 사용처를 정리. 파서가 기본 안전 설정이면 후보에서 제외.

## 후보 판정 제한

사용자 입력 XML을 파싱하는 코드가 있는 경우만 분석 대상. XML 생성만 하는 경우 제외.
