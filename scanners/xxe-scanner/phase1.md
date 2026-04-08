---
grep_patterns:
  - "Nokogiri"
  - "REXML"
  - "xml2js"
  - "libxmljs"
  - "xmldom"
  - "fast-xml-parser"
  - "DocumentBuilderFactory"
  - "SAXParserFactory"
  - "XMLInputFactory"
  - "simplexml_load_string"
  - "DOMDocument"
  - "lxml\\.etree"
  - "xml\\.etree"
  - "noent"
  - "resolve_entities"
  - "parseXML"
  - "XMLReader"
  - "load_external_dtd"
  - "external-general-entities"
  - "external-parameter-entities"
  - "DOCTYPE"
  - "SYSTEM\\s+['\"]"
  - "setExpandEntityReferences"
---

> ## 핵심 원칙: "외부 엔티티가 처리되지 않으면 취약점이 아니다"
>
> XML 파서 사용 자체는 XXE가 아니다. `<!DOCTYPE>` 외부 엔티티가 파서에 의해 실제로 해석되어 파일/SSRF가 발생해야 한다. 대부분의 최신 파서는 기본적으로 외부 엔티티를 비활성화한다 — **파서 종류와 버전, 그리고 명시 옵션**을 확인해야 한다.

## Sink 의미론

XXE sink는 "사용자 제어 XML이 파서에 입력되고, 그 파서가 외부 엔티티/DTD를 해석하도록 설정된 지점"이다. 핵심은 **파서 설정**이다. 같은 라이브러리도 옵션에 따라 안전/위험이 갈린다.

| 언어 | 라이브러리 | 기본값 | 위험 옵션 |
|---|---|---|---|
| Node.js | `xml2js` | 안전 | (외부 엔티티 미지원) |
| Node.js | `libxmljs` | 안전 | `noent: true` 또는 `dtdload: true` |
| Node.js | `@xmldom/xmldom` | 부분적 안전 | DOCTYPE 처리 확인 필요 |
| Node.js | `fast-xml-parser` | 안전 | — |
| Python | `xml.etree.ElementTree` (3.7.1+) | 안전 | 구버전 위험 |
| Python | `lxml.etree` | 위험 | `resolve_entities=True` (기본), `no_network=False` |
| Python | `xml.dom.minidom` | 부분 위험 | DTD 처리 |
| Python | `xml.sax` | 위험 | `feature_external_ges=True` |
| Python | `defusedxml` | 안전 | (안전 래퍼) |
| Java | `DocumentBuilderFactory` | **위험 (기본)** | `disallow-doctype-decl=false` |
| Java | `SAXParserFactory` | **위험 (기본)** | `external-general-entities=true` |
| Java | `XMLInputFactory` (StAX) | 위험 | `IS_SUPPORTING_EXTERNAL_ENTITIES=true` |
| Java | `TransformerFactory` (XSLT) | 위험 | `ACCESS_EXTERNAL_DTD/STYLESHEET` |
| Java | JAXB `Unmarshaller` | 위험 | XMLStreamReader 설정에 의존 |
| Ruby | `Nokogiri` | 안전 | `Nokogiri::XML::ParseOptions::NONET` 미적용 + DTDLOAD |
| Ruby | `REXML` | 위험 | DTD 엔티티 확장 |
| PHP | `simplexml_load_string` | 안전 | `LIBXML_NOENT` 옵션 |
| PHP | `DOMDocument::loadXML` | 안전 (PHP 8.0+) | `LIBXML_NOENT` 또는 PHP < 8 + `libxml_disable_entity_loader(false)` |

## Source-first 추가 패턴

- `Content-Type: application/xml`/`text/xml` 엔드포인트
- SOAP API
- XML 기반 파일 업로드: SVG, XLSX/DOCX/PPTX (Office Open XML), RSS/Atom
- XML-RPC
- SAML SSO assertion 처리
- 사용자 업로드 설정 XML
- KML/GPX 등 도메인 XML

## 자주 놓치는 패턴 (Frequently Missed)

- **OOXML 파일 업로드 (XLSX/DOCX/PPTX)**: 내부적으로 XML. zip 해제 후 XML 파싱 시 XXE.
- **SVG 업로드**: SVG는 XML. `<svg><image href="file:///etc/passwd"/></svg>` + 이미지 처리 라이브러리.
- **SAML XXE**: SAML response를 파싱할 때. 인증 우회로도 이어짐.
- **XInclude 공격**: `<xi:include href="file:///etc/passwd"/>` — DOCTYPE 차단해도 XInclude가 활성화되어 있으면 우회.
- **Parameter entity (OOB XXE)**: `<!ENTITY % x SYSTEM "...">` — 일반 엔티티만 차단하고 parameter entity 미차단 케이스. Java에서 흔함.
- **Blind XXE → SSRF**: 외부 DTD를 fetch하여 내부 IP 스캔.
- **Java SAXParser의 setFeature 누락**: `disallow-doctype-decl`, `external-general-entities`, `external-parameter-entities`, `load-external-dtd` 4개 모두 설정해야 안전. 1개만 누락해도 우회 가능.
- **XSLT 처리기**: TransformerFactory도 XML 파싱하므로 동일 설정 필요.
- **JAXB Unmarshaller**: 내부적으로 SAX/StAX 사용. XMLStreamReader 직접 생성 후 전달해야 안전.
- **Nokogiri의 `parse(io)` vs `parse(string)`** 옵션 차이.
- **PHP < 8.0의 `libxml_disable_entity_loader`**: PHP 8에서 deprecated/no-op. PHP 8 코드에 이 함수가 있다면 방어가 안 됨.
- **XML signature wrapping (XSW)**: SAML 등에서 서명 검증과 파싱 노드가 다르면 우회.
- **DTD validation 활성화**: `setValidating(true)`만으로도 외부 DTD fetch.

## 안전 패턴 카탈로그 (FP Guard)

- **`defusedxml` 사용** (Python).
- **`Nokogiri`** 기본 옵션 (Ruby).
- **Java DocumentBuilderFactory**:
  ```
  factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
  factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
  factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
  factory.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
  factory.setXIncludeAware(false);
  factory.setExpandEntityReferences(false);
  ```
  — **6개 모두** 적용 확인 필요.
- **lxml `etree.XMLParser(resolve_entities=False, no_network=True, dtd_validation=False, load_dtd=False)`**.
- **`xml2js`/`fast-xml-parser`** 기본값 (Node).

## 후보 판정 의사결정

| 조건 | 판정 |
|---|---|
| Java DocumentBuilderFactory/SAXParserFactory + 위 6개 setFeature 누락 | 후보 |
| lxml + `resolve_entities=True` (또는 옵션 미지정) + 사용자 입력 파싱 | 후보 |
| `defusedxml`/`Nokogiri` 기본 사용 | 제외 |
| SVG/OOXML 업로드 처리 + 내부 XML 파서 미설정 | 후보 (라벨: `OOXML_XXE`) |
| SAML response 파싱 + 파서 설정 미확인 | 후보 (라벨: `SAML_XXE`) |
| `libxml_disable_entity_loader(true)` 호출하지만 PHP 8.0+ | 후보 (no-op이므로 방어 없음) |
| 정적 XML만 파싱 (사용자 입력 없음) | 제외 |

## 후보 판정 제한

사용자 입력 XML을 파싱하는 코드가 있는 경우만 분석 대상. XML 생성만 하는 경우 제외.
