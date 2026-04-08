> ## 핵심 원칙: "인가가 우회되지 않으면 취약점이 아니다"
>
> SOAPAction 헤더를 변조할 수 있다는 것만으로는 취약점이 아니다. 변조된 SOAPAction 헤더로 인해 권한이 없는 오퍼레이션이 실제로 실행되거나, 인증/인가가 우회되는 것을 확인해야 취약점이다.
>

### Phase 1: 정찰 (소스코드 분석)

SOAP 서비스 구현을 분석하여 SOAPAction 검증 미흡을 식별한다.

1. **프로젝트 스택 파악**: SOAP 프레임워크/라이브러리 확인

   **Java:**
   - JAX-WS (`@WebService`, `@WebMethod`)
   - Apache CXF
   - Apache Axis / Axis2
   - Spring-WS (`@Endpoint`, `@PayloadRoot`)

   **Python:**
   - `zeep` — SOAP 클라이언트
   - `spyne` — SOAP 서버
   - `suds` — SOAP 클라이언트

   **Node.js:**
   - `soap` — SOAP 서버/클라이언트
   - `strong-soap`
   - `express` + XML 파싱으로 직접 구현

   **.NET:**
   - WCF (Windows Communication Foundation)
   - ASP.NET Web Services (.asmx)

   **PHP:**
   - `SoapServer` — 내장 SOAP 서버
   - `NuSOAP`

2. **WSDL 분석**: WSDL 파일에서 오퍼레이션 목록과 SOAPAction 매핑 확인
   - 각 오퍼레이션에 할당된 SOAPAction 값
   - 관리자 전용 오퍼레이션 식별
   - 인증/인가가 필요한 오퍼레이션 식별

3. **SOAPAction 처리 로직 분석**:
   - 서버가 SOAPAction 헤더를 어떻게 사용하는지 (라우팅, 인가, 무시)
   - SOAPAction과 SOAP Body의 오퍼레이션 일치 검증 여부
   - WAF/게이트웨이에서 SOAPAction 기반 필터링이 있는지

4. **인가 로직 분석**:
   - 오퍼레이션별 권한 검사가 SOAPAction 기반인지, SOAP Body 기반인지
   - 미들웨어/인터셉터에서 SOAPAction으로 인가를 판단하는지
   - WS-Security 적용 여부

5. **후보 목록 작성**: 각 후보에 대해 "어떤 SOAPAction 변조로 어떤 제한된 오퍼레이션을 실행할 수 있는지"를 구체적으로 구상. 데이터 흐름 추적을 완료한 뒤에도 공격 경로가 없으면 버린다. 추적 없이 직관으로 버리지 않는다..

## 후보 판정 제한

SOAP 엔드포인트를 직접 구현하는 코드가 있는 경우만 분석.
