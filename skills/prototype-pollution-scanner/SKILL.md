---
name: prototype-pollution-scanner
description: "소스코드 분석과 동적 테스트를 통해 Prototype Pollution 취약점을 탐지하는 스킬. 사용자 입력이 객체의 프로토타입 체인을 오염시켜 애플리케이션 동작을 변조하거나, 이를 가젯(gadget)과 연결하여 XSS/RCE 등으로 이어질 수 있는지 분석하고 검증한다. 사용자가 'prototype pollution 찾아줘', '프로토타입 오염', 'prototype pollution 스캔', '__proto__ 취약점', 'constructor pollution', 'prototype pollution audit', '프로토타입 체인 오염' 등을 요청할 때 이 스킬을 사용한다."
grep_patterns:
  - "__proto__"
  - "constructor\\.prototype"
  - "merge("
  - "extend("
  - "deepMerge("
  - "deepCopy("
  - "defaultsDeep("
  - "lodash\\.merge"
  - "lodash\\.set"
  - "jQuery\\.extend"
  - "Object\\.assign("
  - "dot-prop"
  - "set-value"
  - "object-path"
---

# Prototype Pollution Scanner

소스코드 분석으로 Prototype Pollution 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 프로토타입 체인이 오염되어 애플리케이션 동작이 변조되는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "프로토타입이 오염되지 않으면 취약점이 아니다"

소스코드에서 `merge`, `extend`, `defaultsDeep` 같은 함수가 있다고 바로 취약점으로 보고하지 않는다. 사용자가 제어한 입력으로 실제로 `Object.prototype`이나 다른 객체의 프로토타입에 속성이 추가/변경되는 것을 확인해야 취약점이다.

가정 기반의 취약점 보고는 도움이 되지 않는다. "라이브러리에 알려진 취약점이 있으므로 위험" 같은 보고는 실제 코드에서 해당 취약 경로가 도달 가능한지를 확인한 뒤에야 의미가 있다.

## Prototype Pollution의 원리

JavaScript에서 모든 객체는 프로토타입 체인을 통해 상위 객체의 속성을 상속받는다. 공격자가 `__proto__`, `constructor.prototype`, 또는 `prototype` 속성을 통해 `Object.prototype`에 임의 속성을 추가하면, 이후 생성되는 모든 객체에 해당 속성이 존재하게 된다.

```javascript
// 공격 예시
const payload = JSON.parse('{"__proto__": {"isAdmin": true}}');
merge({}, payload);

// 이후 모든 객체에 isAdmin이 true로 존재
const user = {};
console.log(user.isAdmin); // true
```

## Prototype Pollution의 유형

### 서버사이드 Prototype Pollution (SSPP)
Node.js 서버에서 발생하는 Prototype Pollution. RCE, 인증 우회, DoS 등으로 이어질 수 있다. 가젯 체인이 존재하면 심각도가 매우 높다.

### 클라이언트사이드 Prototype Pollution (CSPP)
브라우저 JavaScript에서 발생하는 Prototype Pollution. XSS 가젯과 결합하면 스크립트 실행이 가능하다. DOM Clobbering과 유사한 공격 경로를 가진다.

### Gadget 기반 공격
Prototype Pollution 자체는 속성 추가/변경이지만, 이를 활용하는 코드(gadget)가 있어야 실제 영향이 발생한다. 예를 들어 `obj.innerHTML`이 오염된 속성을 참조하면 XSS가 된다.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 이 스킬과 같은 skills 디렉토리 내의 `noah-sast/agent-guidelines.md`를 참조한다. 이 파일의 위치를 기준으로 `../noah-sast/agent-guidelines.md` 경로로 접근할 수 있다.
