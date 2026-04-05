
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

