
# XSLT Injection Scanner

소스코드 분석으로 XSLT Injection 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 XSLT 프로세서에서 의도하지 않은 변환이나 코드 실행이 발생하는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "XSLT 변환이 조작되지 않으면 취약점이 아니다"

소스코드에서 XSLT 변환을 사용한다고 바로 취약점으로 보고하지 않는다. 실제로 사용자가 제어한 입력이 XSLT 스타일시트 또는 XML 데이터에 삽입되어 의도하지 않은 파일 읽기, 코드 실행, 정보 노출이 발생하는 것을 확인해야 취약점이다.

## XSLT Injection의 유형

### XSLT 스타일시트 주입
사용자 입력이 XSLT 스타일시트 자체에 삽입되어 `xsl:value-of`, `document()`, `xsl:include` 등의 XSLT 함수를 조작하는 공격.

### 서버사이드 XSLT를 통한 파일 읽기
XSLT 1.0의 `document()` 함수나 XSLT 2.0+의 `unparsed-text()` 함수로 서버의 로컬 파일을 읽는 공격.

### XSLT를 통한 RCE
XSLT 프로세서의 확장 기능을 이용한 코드 실행:
- **Java (Xalan)**: `<xsl:value-of select="Runtime:exec(...)"/>` — Java Runtime 호출
- **PHP (libxslt)**: `php:function()` — PHP 함수 호출
- **.NET**: `msxsl:script` — C#/VB 코드 실행
- **libxslt**: `http://xmlsoft.org/XSLT/namespace` 확장

### XSLT를 통한 SSRF
`document()` 함수로 외부 URL에 요청을 보내는 공격. XXE와 유사하지만 XSLT 프로세서를 통해 발생.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

