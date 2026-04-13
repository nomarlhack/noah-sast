---
grep_patterns:
  - "pickle\\.loads\\s*\\("
  - "pickle\\.load\\s*\\("
  - "yaml\\.load\\s*\\("
  - "Marshal\\.load\\s*\\("
  - "unserialize\\s*\\("
  - "ObjectInputStream"
  - "readObject\\s*\\("
  - "XMLDecoder"
  - "XStream\\.fromXML\\s*\\("
  - "BinaryFormatter"
  - "node-serialize"
  - "cryo\\.parse\\s*\\("
  - "jsonpickle\\.decode\\s*\\("
  - "maybe_unserialize\\s*\\("
  - "shelve\\.open\\s*\\("
  - "activateDefaultTyping"
  - "enableDefaultTyping"
  - "@JsonTypeInfo"
  - "GenericJackson2JsonRedisSerializer"
  - "fastjson"
  - "parseObject\\s*\\("
  - "SnakeYaml"
  - "new Yaml\\s*\\("
  - "BinaryFormatter\\.Deserialize"
  - "TypeNameHandling"
  - "phpggc"
---

> ## 핵심 원칙: "역직렬화로 의도하지 않은 동작이 발생하지 않으면 취약점이 아니다"
>
> `JSON.parse()`는 데이터만 표현하므로 코드 실행으로 이어지지 않는다 (단, prototype pollution 별도 점검). 취약한 역직렬화는 **객체/타입 정보를 포함하는 직렬화 포맷** (Java ObjectInputStream, Python pickle, PHP unserialize, Ruby Marshal, .NET BinaryFormatter, node-serialize, YAML unsafe loader 등)에서 발생한다.

## Sink 의미론

Deserialization sink는 "사용자 제어 바이트가 타입/객체 정보를 복원하는 디코더에 입력되는 지점"이다. 핵심 구분: 디코더가 **임의 클래스 인스턴스화 + 메서드 호출**을 허용하는가.

| 언어 | 위험 sink | 비고 |
|---|---|---|
| Java | `ObjectInputStream.readObject/readUnshared`, `XMLDecoder.readObject`, `XStream.fromXML` (화이트리스트 없음), `SnakeYAML.load` (unsafe Loader), `Kryo.readClassAndObject` (등록 없음) | gadget chain (CommonsCollections, Spring AOP) 활용 |
| Python | `pickle.loads/load`, `cPickle.loads`, `shelve.open`, `yaml.load` (Loader 미지정 또는 unsafe), `marshal.loads`, `jsonpickle.decode` | `__reduce__` 메서드로 RCE |
| PHP | `unserialize`, `maybe_unserialize` | `__wakeup`/`__destruct` 매직 메서드 체인 (POP chain) |
| Ruby | `Marshal.load`, `YAML.load` (vs `safe_load`) | `_load`/`init_with` 체인 |
| Node.js | `node-serialize` `unserialize`, `cryo.parse` | `_$$ND_FUNC$$_` 패턴 |
| .NET | `BinaryFormatter.Deserialize`, `ObjectStateFormatter.Deserialize` (ViewState), `Json.NET TypeNameHandling.All/Auto`, `LosFormatter`, `SoapFormatter` | Microsoft 사용 중단 권고 |

## Source-first 추가 패턴

- HTTP 쿠키에 base64 직렬화 페이로드 (Java/PHP 레거시 세션)
- `Content-Type: application/x-java-serialized-object` (RMI, JMX)
- ViewState (.NET WebForms `__VIEWSTATE`)
- 메시지 큐 (Kafka/RabbitMQ/SQS) consumer가 외부 메시지 역직렬화
- 캐시(Redis/Memcached)에서 읽은 직렬화 값 + 캐시 키가 사용자 제어
- 파일 업로드 후 `pickle.load(f)` (사용자 데이터 저장 → 후속 처리)
- JWT custom 페이로드를 base64 디코딩 후 unserialize
- 채팅/게임 클라이언트 ↔ 서버 바이너리 프로토콜

## 자주 놓치는 패턴 (Frequently Missed)

- **YAML `load` 기본 인자**: PyYAML 5.1 미만은 `Loader` 미지정 시 unsafe. `yaml.safe_load` 필수.
- **Jackson `enableDefaultTyping()`** 또는 `@JsonTypeInfo`: JSON처럼 보여도 polymorphic typing이 켜져 있으면 RCE.
- **Json.NET `TypeNameHandling.All`/`Auto`**: `$type` 필드로 임의 타입 인스턴스화.
- **XStream**: 화이트리스트(`addPermission`) 없이 `fromXML` → 다수 CVE.
- **Spring 메시지 컨버터** (`ObjectInputStream` 기반 RMI/HTTP invoker).
- **SnakeYAML `Yaml().load(...)`**: 명시적 `SafeConstructor` 없으면 RCE (CVE-2022-1471).
- **Kryo without `setRegistrationRequired(true)`**.
- **PHP phar deserialization**: `file_exists("phar://...")` 만으로도 unserialize 트리거.
- **.NET BinaryFormatter는 deprecated이지만 잔존 코드**: WCF/Remoting/ViewState.
- **JWT none algo + 역직렬화 페이로드**: jwt-scanner와 겹치지만 페이로드가 클래스 정보를 담은 경우.
- **gadget chain 라이브러리 의존성**: `commons-collections`/`commons-beanutils`가 classpath에 있는지 확인 — 영향도 평가에 사용.
- **`ObjectInputStream` 서브클래스로 `resolveClass` 오버라이드한 화이트리스트**: 화이트리스트가 충분히 좁은지 확인.

## 안전 패턴 카탈로그 (FP Guard)

- **JSON-only 데이터** (Jackson `disableDefaultTyping`, Json.NET 기본 `TypeNameHandling.None`).
- **`yaml.safe_load`** (Python).
- **YAML `SafeConstructor`** (SnakeYAML).
- **HMAC 서명 검증 후 역직렬화**: 사용자가 페이로드를 변조 못 함 (서명 키 안전 가정).
- **`Marshal.load` 입력이 trusted 파일** (서버가 직접 생성한 캐시 파일).
- **타입 화이트리스트** (`XStream.addPermission(NoTypePermission.NONE); xstream.allowTypes(...)`).
- **Kryo `setRegistrationRequired(true)` + 명시적 등록**.

## 후보 판정 의사결정

| 조건 | 판정 |
|---|---|
| 위 표의 위험 sink + 사용자 입력 도달 + 화이트리스트/서명 없음 | 후보 |
| Jackson/Json.NET polymorphic typing 활성 + 외부 입력 | 후보 (라벨: `POLYMORPHIC`) |
| YAML `load` (Loader 미지정) + Python | 후보 |
| HMAC 서명 검증 확인 (key 별도 관리) | 제외 |
| 화이트리스트 적용 확인 (충분히 좁음) | 제외 |
| 입력이 trusted 내부 출처만 (예: 서버가 만든 캐시 파일) | 제외, 단 캐시 키가 사용자 제어이면 후보 |
| `BinaryFormatter` 잔존 (.NET) + 외부 입력 | 후보 (라벨: `DEPRECATED_FORMATTER`) |

## 후보 판정 제한

default typing 또는 다형성 역직렬화가 활성화된 경우만 후보. 비활성화가 확인되면 제외.
