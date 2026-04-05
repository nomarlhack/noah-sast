---
name: idor-scanner
description: "소스코드 분석과 동적 테스트를 통해 IDOR(Insecure Direct Object Reference) 취약점을 탐지하는 스킬. 사용자가 제공한 객체 식별자(ID, UUID 등)로 다른 사용자의 리소스에 접근할 수 있는지 분석하고 검증한다. 사용자가 'IDOR 찾아줘', 'IDOR 스캔', '권한 검증 미흡', '접근 제어 점검', 'broken access control', '인가 우회', '타인 데이터 접근', 'IDOR audit' 등을 요청할 때 이 스킬을 사용한다."
grep_patterns:
  # 엔드포인트 파라미터 (식별자 수신 지점)
  - "@PathVariable"
  - "@RequestParam"
  - "@RequestBody"
  - "req\\.params"
  - "req\\.query"
  - "request\\.args"
  - "params\\[:"
  # 데이터 접근 (식별자로 객체 조회)
  - "findById"
  - "findOne"
  - "getById"
  - "getOne"
  - "findByPk"
  - "Model\\.find("
  - "repository\\."
  # 접근 제어 설정
  - "permitAll"
  - "hasAnyRole"
  - "@PreAuthorize"
  - "@Secured"
  - "authorize"
---

# IDOR Scanner

소스코드 분석으로 객체 식별자를 받아 리소스에 접근하는 엔드포인트에서 소유권/권한 검증이 누락된 곳을 식별한 뒤, 동적 테스트로 실제로 다른 사용자의 리소스에 접근 가능한지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "다른 사용자의 리소스에 접근할 수 없으면 취약점이 아니다"

소스코드에서 `findById(id)`가 있다고 바로 IDOR로 보고하지 않는다. 실제로 사용자 A의 인증 정보로 사용자 B의 리소스 식별자를 전송했을 때, 서버가 사용자 B의 리소스를 반환하는 것을 확인해야 취약점이다.

## IDOR의 유형

### 수평적 권한 상승
동일 권한 수준의 다른 사용자 리소스에 접근하는 경우. 사용자 A가 사용자 B의 주문 내역, 파일, 개인정보 등에 접근.

### 수직적 권한 상승
낮은 권한의 사용자가 높은 권한의 리소스나 기능에 접근하는 경우. 일반 사용자가 관리자 전용 API를 호출.

### 간접 참조 미적용
예측 가능한 순차 ID(1, 2, 3...)를 사용하여 리소스를 열거할 수 있는 경우. UUID 등 비예측 식별자를 사용하더라도 소유권 검증이 없으면 취약하다.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 이 스킬과 같은 skills 디렉토리 내의 `noah-sast/agent-guidelines.md`를 참조한다. 이 파일의 위치를 기준으로 `../noah-sast/agent-guidelines.md` 경로로 접근할 수 있다.
