---
name: redos-scanner
description: "소스코드 분석과 동적 테스트를 통해 ReDoS(Regular Expression Denial of Service) 취약점을 탐지하는 스킬. 사용자 입력이 취약한 정규식에 매칭되는 경로를 추적하고, 실제로 악의적 입력으로 지수적 역추적이 발생하여 서비스 거부가 가능한지 검증한다. 사용자가 'ReDoS 찾아줘', 'ReDoS 스캔', '정규식 DoS', 'regex denial of service', 'catastrophic backtracking', 'ReDoS audit', '정규식 취약점' 등을 요청할 때 이 스킬을 사용한다."
grep_patterns:
  - "\\.test("
  - "\\.match("
  - "new RegExp("
  - "re\\.match("
  - "re\\.search("
  - "re\\.findall("
  - "Pattern\\.compile("
  - "String\\.matches("
  - "String\\.replaceAll("
  - "=~"
  - "\\.scan("
  - "Regexp\\.new("
  - "\\.toRegex("
  - "\\.replace("
  # Source patterns
  - "@RequestParam"
  - "@RequestBody"
  - "req\\.query"
  - "req\\.body"
---

# ReDoS Scanner

소스코드 분석으로 ReDoS 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 악의적 입력이 지수적 역추적을 유발하여 응답 지연이 발생하는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "응답 지연이 발생하지 않으면 취약점이 아니다"

소스코드에서 취약해 보이는 정규식이 있다고 바로 ReDoS로 보고하지 않는다. 해당 정규식에 사용자가 제어하는 입력이 매칭되고, 실제로 악의적 입력으로 유의미한 응답 지연(수 초 이상)이 발생하는 것을 확인해야 취약점이다.

## ReDoS의 원리

정규식 엔진(NFA 기반)이 역추적(backtracking)을 수행할 때, 특정 패턴과 입력 조합에서 지수적 시간이 소요되는 현상. 짧은 입력 증가로도 처리 시간이 급격히 증가하여 서비스 거부를 유발한다.

### 취약한 정규식 패턴

**중첩 반복 (Nested Quantifiers):**
- `(a+)+` — `a` 반복의 반복
- `(a*)*` — 빈 매칭 포함 반복의 반복
- `(a|a)+` — 동일 문자의 교대 반복
- `(.*a){x}` — 욕심많은 매칭 + 반복

**겹치는 교대 (Overlapping Alternation):**
- `(a|ab)+` — `a`와 `ab` 겹침
- `(\w+\s*)+` — 단어+공백의 반복에서 경계 모호

**일반적인 취약 패턴:**
- `^(a+)+$` + 입력: `aaaaaaaaaaaaaaaaX`
- `^(\d+\.?\d*)+$` + 입력: `1.1.1.1.1.1.1.1X`
- `^([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.)+$` + 악의적 이메일

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 이 스킬과 같은 skills 디렉토리 내의 `noah-sast/agent-guidelines.md`를 참조한다. 이 파일의 위치를 기준으로 `../noah-sast/agent-guidelines.md` 경로로 접근할 수 있다.
