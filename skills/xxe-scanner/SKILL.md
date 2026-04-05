---
name: xxe-scanner
description: "소스코드 분석과 동적 테스트를 통해 XXE(XML External Entity) 취약점을 탐지하는 스킬. XML 파서가 외부 엔티티를 처리하도록 설정되어 있는지 분석하고, 실제로 외부 엔티티를 통해 파일 읽기나 SSRF가 가능한지 검증한다. 사용자가 'XXE 찾아줘', 'XXE 스캔', 'XML external entity', 'XXE injection', 'XXE 점검', 'XML 파싱 취약점' 등을 요청할 때 이 스킬을 사용한다."
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
---

# XXE Scanner

소스코드 분석으로 XXE 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 외부 엔티티가 처리되어 파일 읽기나 SSRF가 발생하는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "외부 엔티티가 처리되지 않으면 취약점이 아니다"

소스코드에서 XML 파서를 사용한다고 바로 XXE로 보고하지 않는다. 실제로 `<!DOCTYPE>` 선언에 외부 엔티티를 정의하고, 해당 엔티티가 파서에 의해 해석되어 파일 내용이 반환되거나 외부 요청이 발생하는 것을 확인해야 취약점이다.

대부분의 최신 XML 파서는 기본적으로 외부 엔티티를 비활성화하고 있다. 파서 버전과 설정을 반드시 확인해야 한다.

## XXE의 유형

### Classic XXE (In-band)
외부 엔티티의 내용이 응답에 직접 반환되는 경우. `file:///etc/passwd` 같은 로컬 파일 내용을 읽을 수 있다.

### Blind XXE (Out-of-band)
외부 엔티티의 내용이 응답에 반환되지 않는 경우. 외부 서버로 데이터를 전송하는 파라미터 엔티티를 사용하거나, 에러 메시지를 통해 데이터를 유출한다.

### XXE를 통한 SSRF
외부 엔티티의 URL로 내부 네트워크 서비스에 요청을 보내는 경우. `http://169.254.169.254/` 같은 클라우드 메타데이터에 접근할 수 있다.

### XXE를 통한 DoS (Billion Laughs)
재귀적 엔티티 정의로 메모리를 고갈시키는 공격. 이 스캐너에서는 소스코드 분석만 수행하고 실제 DoS 테스트는 하지 않는다.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 이 스킬과 같은 skills 디렉토리 내의 `noah-sast/agent-guidelines.md`를 참조한다. 이 파일의 위치를 기준으로 `../noah-sast/agent-guidelines.md` 경로로 접근할 수 있다.
