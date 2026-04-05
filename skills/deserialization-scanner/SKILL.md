---
name: deserialization-scanner
description: "소스코드 분석과 동적 테스트를 통해 Insecure Deserialization 취약점을 탐지하는 스킬. 사용자가 제어 가능한 직렬화된 데이터가 역직렬화되는 경로를 추적하고, 실제로 임의 객체 생성이나 코드 실행이 가능한지 검증한다. 사용자가 'deserialization 취약점 찾아줘', '역직렬화 스캔', 'insecure deserialization', '객체 인젝션', 'deserialization audit', 'pickle 취약점', 'Java deserialization' 등을 요청할 때 이 스킬을 사용한다."
grep_patterns:
  - "pickle\\.loads("
  - "pickle\\.load("
  - "yaml\\.load("
  - "Marshal\\.load("
  - "unserialize("
  - "ObjectInputStream"
  - "readObject("
  - "XMLDecoder"
  - "XStream\\.fromXML("
  - "BinaryFormatter"
  - "node-serialize"
  - "cryo\\.parse("
  - "jsonpickle\\.decode("
  - "maybe_unserialize("
  - "shelve\\.open("
  - "activateDefaultTyping"
  - "enableDefaultTyping"
  - "@JsonTypeInfo"
  - "GenericJackson2JsonRedisSerializer"
---

# Deserialization Scanner

소스코드 분석으로 Insecure Deserialization 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 임의 객체 생성이나 코드 실행이 가능한지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "역직렬화로 의도하지 않은 동작이 발생하지 않으면 취약점이 아니다"

소스코드에서 `JSON.parse()`를 사용한다고 바로 Deserialization 취약점으로 보고하지 않는다. JSON은 데이터만 표현하므로 코드 실행으로 이어지지 않는다. 취약한 역직렬화란 **객체 타입 정보를 포함한 직렬화 포맷**(Java ObjectInputStream, Python pickle, PHP unserialize, Ruby Marshal, Node.js node-serialize 등)에서 사용자가 제어한 데이터가 역직렬화되어 임의 객체가 생성되거나 코드가 실행되는 것을 말한다.

## 안전한 포맷 vs 위험한 포맷

### 안전한 포맷 (Deserialization 취약점 아님)
- **JSON** (`JSON.parse()`, `json.loads()`, `Jackson ObjectMapper` 등) — 데이터만 표현, 객체 타입 정보 없음
- **XML** — XXE는 별도 취약점, 역직렬화와 무관
- **Protocol Buffers**, **MessagePack**, **CBOR** — 스키마 기반, 임의 객체 생성 불가
- **YAML** (safe_load) — `yaml.safe_load()`는 안전, `yaml.load()`(Loader 미지정)는 위험

### 위험한 포맷 (Deserialization 취약점 가능)
- **Java**: `ObjectInputStream.readObject()`, `XMLDecoder`, `XStream`, `SnakeYAML`(unsafe), `Kryo`(unsafe)
- **Python**: `pickle.loads()`, `pickle.load()`, `shelve`, `yaml.load()`(unsafe), `marshal.loads()`
- **PHP**: `unserialize()`, `maybe_unserialize()`
- **Ruby**: `Marshal.load()`, `YAML.load()`(unsafe)
- **Node.js**: `node-serialize` (`serialize.unserialize()`), `cryo`
- **.NET**: `BinaryFormatter.Deserialize()`, `ObjectStateFormatter`, `SoapFormatter`, `NetDataContractSerializer`, `JavaScriptSerializer`(TypeNameHandling), `Json.NET`(`TypeNameHandling.All/Auto`)

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

개별 실행 시, 이 디렉토리의 `phase1.md`와 `phase2.md`를 순서대로 읽고 수행한다.
공통 유의사항은 `~/.claude/skills/noah-sast/agent-guidelines.md`를 참조한다.
