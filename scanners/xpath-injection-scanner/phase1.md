> **호출부 추적 — 실제 URL 경로 확정**: 모든 후보에 대해 라우트 정의 파일을 Read로 읽어 실제 URL 경로를 확정한다. 컴포넌트/파일 이름에서 경로를 유추하는 것은 확정이 아니다. 절차: (1) Sink의 호출부를 Grep → 최종 페이지 컴포넌트/컨트롤러 식별 (2) 라우트 정의(routes/index.tsx, @RequestMapping 등)를 Read로 읽어 경로 문자열 확인 (3) 후보 반환 시 근거 포함: `실제 경로: /home/apply (src/routes/index.tsx:42)`

### Phase 1: 정찰 (소스코드 분석)

사용자 입력 → XPath 쿼리 경로를 추적하여 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: XML 처리 라이브러리/XPath 엔진 확인

   **Node.js:**
   - `xpath` — XPath 쿼리 라이브러리
   - `xmldom` + `xpath` — DOM 파싱 + XPath
   - `libxmljs` — `doc.find()`, `doc.get()` (XPath)
   - `cheerio` — CSS 선택자 (XPath 아님, 안전)

   **Python:**
   - `lxml.etree.xpath()` — XPath 쿼리
   - `xml.etree.ElementTree.findall()` — 제한된 XPath 지원 (기본적으로 안전)
   - `defusedxml` — 안전한 래퍼

   **Java:**
   - `javax.xml.xpath.XPath.evaluate()` — JAXP XPath
   - `javax.xml.xpath.XPath.compile()` — 컴파일된 XPath
   - `org.w3c.dom.Document` + XPath — DOM + XPath
   - `XPathFactory.newInstance()` — XPath 엔진 생성

   **PHP:**
   - `DOMXPath::query()` — DOM XPath
   - `DOMXPath::evaluate()` — XPath 평가
   - `SimpleXMLElement::xpath()` — SimpleXML XPath

   **Ruby:**
   - `Nokogiri::XML::Node#xpath()` — Nokogiri XPath
   - `REXML::XPath.match()` — REXML XPath

2. **Source 식별**: 사용자가 제어 가능한 입력 중 XPath 쿼리에 사용될 수 있는 것
   - 로그인 폼의 username/password (XML 기반 인증 시)
   - 검색 기능의 검색어
   - XML 데이터 조회 파라미터
   - API 요청의 필터/조건 파라미터

3. **Sink 식별**: XPath 쿼리를 실행하는 코드

   **문자열 연결로 XPath 구성 (위험):**
   ```java
   // Java
   String xpath = "//users/user[username='" + username + "' and password='" + password + "']";
   XPath xPath = XPathFactory.newInstance().newXPath();
   xPath.evaluate(xpath, document);
   ```

   ```python
   # Python
   result = doc.xpath(f"//users/user[username='{username}' and password='{password}']")
   ```

   ```php
   // PHP
   $query = "//users/user[username='" . $username . "' and password='" . $password . "']";
   $result = $xpath->query($query);
   ```

   ```javascript
   // Node.js
   const nodes = xpath.select(`//users/user[username='${username}']`, doc);
   ```

   **안전한 패턴:**
   ```java
   // Java — 파라미터화된 XPath (XPathVariableResolver)
   xPath.setXPathVariableResolver(new XPathVariableResolver() {
     public Object resolveVariable(QName name) {
       if ("username".equals(name.getLocalPart())) return username;
       return null;
     }
   });
   xPath.evaluate("//users/user[username=$username]", document);
   ```

   ```python
   # Python — lxml 변수 바인딩
   result = doc.xpath("//users/user[username=$name]", name=username)
   ```

4. **경로 추적**: Source에서 Sink까지 데이터 흐름 확인
   - XPath 메타문자(`'`, `"`, `[`, `]`, `/`, `|`, `and`, `or`) 이스케이프 여부
   - 파라미터화된 XPath 사용 여부 (`$variable` 바인딩)
   - 입력값 화이트리스트 검증 (영문자/숫자만 허용 등)
   - XML 기반 인증을 사용하는지 (대부분의 현대 앱은 DB 기반)

5. **후보 목록 작성**: 각 후보에 대해 "어떤 입력으로 어떻게 XPath 로직을 변경할 수 있는지"를 구체적으로 구상. 데이터 흐름 추적을 완료한 뒤에도 공격 경로가 없으면 버린다. 추적 없이 직관으로 버리지 않는다..

## 후보 판정 제한

사용자 입력이 XPath 쿼리 문자열에 연결되는 경우만 후보.
