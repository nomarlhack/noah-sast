---
name: xpath-injection-scanner
description: "소스코드 분석과 동적 테스트를 통해 XPath Injection 취약점을 탐지하는 스킬. 사용자 입력이 XPath 쿼리에 반영되는 경로를 추적하고, 실제로 쿼리 로직을 변경하여 인증 우회나 데이터 유출이 가능한지 검증한다. 사용자가 'XPath injection 찾아줘', 'XPath 인젝션 스캔', 'XPath 점검', 'XPath audit', 'XML 쿼리 인젝션' 등을 요청할 때 이 스킬을 사용한다."
grep_patterns:
  - "\\.xpath("
  - "XPath\\.evaluate("
  - "XPath\\.compile("
  - "DOMXPath::query("
  - "DOMXPath::evaluate("
  - "SimpleXMLElement::xpath("
  - "Nokogiri.*xpath"
  - "REXML::XPath"
  - "lxml\\.etree\\.xpath"
  - "XPathFactory"
---

# XPath Injection Scanner

소스코드 분석으로 XPath Injection 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 XPath 쿼리 로직을 변경하여 인증 우회나 데이터 유출이 가능한지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "쿼리 로직이 변경되지 않으면 취약점이 아니다"

소스코드에서 XPath 쿼리를 사용한다고 바로 취약점으로 보고하지 않는다. 실제로 사용자가 제어한 입력에 `'`, `or`, `and` 등 XPath 구문을 삽입하여 쿼리 조건을 변경할 수 있는 것을 확인해야 취약점이다.

## XPath Injection의 유형

### 인증 우회 (Authentication Bypass)
XML 기반 사용자 저장소에서 로그인 시 XPath 쿼리에 `' or '1'='1` 같은 구문을 삽입하여 인증을 우회하는 공격.

```
# 정상 쿼리
//users/user[username='admin' and password='secret']

# 공격: password에 ' or '1'='1 삽입
//users/user[username='admin' and password='' or '1'='1']
→ 항상 참 → 인증 우회
```

### 데이터 유출 (Data Extraction)
XPath 쿼리를 조작하여 XML 문서의 의도하지 않은 노드를 조회하는 공격.

### Blind XPath Injection
쿼리 결과가 직접 반환되지 않지만, 응답 차이(참/거짓)로 XML 문서의 데이터를 한 글자씩 추론하는 공격. `substring()`, `string-length()`, `contains()` 함수를 활용.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 이 스킬과 같은 skills 디렉토리 내의 `noah-sast/agent-guidelines.md`를 참조한다. 이 파일의 위치를 기준으로 `../noah-sast/agent-guidelines.md` 경로로 접근할 수 있다.
