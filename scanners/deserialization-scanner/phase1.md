> **호출부 추적 — 실제 URL 경로 확정**: 모든 후보에 대해 라우트 정의 파일을 Read로 읽어 실제 URL 경로를 확정한다. 컴포넌트/파일 이름에서 경로를 유추하는 것은 확정이 아니다. 절차: (1) Sink의 호출부를 Grep → 최종 페이지 컴포넌트/컨트롤러 식별 (2) 라우트 정의(routes/index.tsx, @RequestMapping 등)를 Read로 읽어 경로 문자열 확인 (3) 후보 반환 시 근거 포함: `실제 경로: /home/apply (src/routes/index.tsx:42)`

### Phase 1: 정찰 (소스코드 분석)

사용자 입력 → 역직렬화 경로를 추적하여 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: 프레임워크/언어 확인 및 직렬화 라이브러리 의존성 확인

2. **Source 식별**: 사용자가 제어 가능한 직렬화된 데이터 입력
   - HTTP 쿠키에 저장된 직렬화 데이터 (Base64 인코딩된 Java/PHP 객체 등)
   - HTTP 요청 본문 (`Content-Type: application/x-java-serialized-object` 등)
   - 파일 업로드 (직렬화된 객체를 포함한 파일)
   - 메시지 큐에서 수신한 데이터
   - 캐시(Redis, Memcached)에서 읽은 직렬화 데이터 (사용자가 캐시 키를 제어할 수 있는 경우)
   - ViewState (.NET)
   - JWT 토큰의 페이로드 (커스텀 역직렬화를 사용하는 경우)

3. **Sink 식별**: 위험한 역직렬화를 수행하는 코드

   **Java:**
   - `ObjectInputStream.readObject()` / `readUnshared()` — 가장 위험
   - `XMLDecoder.readObject()`
   - `XStream.fromXML()` — 화이트리스트 미적용 시 위험
   - `SnakeYAML.load()` — unsafe Loader 사용 시 위험
   - `Kryo.readObject()` / `readClassAndObject()` — 등록되지 않은 클래스 허용 시 위험
   - `readResolve()`, `readExternal()` — 커스텀 역직렬화 메서드

   **Python:**
   - `pickle.loads()`, `pickle.load()` — 임의 코드 실행 가능
   - `cPickle.loads()` — pickle과 동일
   - `shelve.open()` — 내부적으로 pickle 사용
   - `yaml.load(data)` — Loader 미지정 또는 `yaml.UnsafeLoader` 시 위험
   - `marshal.loads()` — 코드 실행 가능
   - `jsonpickle.decode()` — pickle 기반

   **PHP:**
   - `unserialize()` — `__wakeup()`, `__destruct()` 등 매직 메서드 체인으로 RCE 가능
   - `maybe_unserialize()` — WordPress 등에서 사용

   **Ruby:**
   - `Marshal.load()` — 임의 객체 생성 가능
   - `YAML.load()` — `YAML.safe_load()` 대신 사용 시 위험

   **Node.js:**
   - `serialize.unserialize()` (node-serialize) — `_$$ND_FUNC$$_` 패턴으로 코드 실행 가능
   - `cryo.parse()` — 함수 역직렬화 가능

   **.NET:**
   - `BinaryFormatter.Deserialize()` — Microsoft에서 사용 중단 권고
   - `ObjectStateFormatter.Deserialize()` — ViewState
   - `TypeNameHandling.All/Auto` (Json.NET) — 타입 정보 포함 시 위험

4. **경로 추적**: Source에서 Sink까지 데이터 흐름 확인
   - 사용자 입력이 역직렬화 함수에 직접 전달되는지
   - Base64 디코딩 → 역직렬화 패턴이 있는지
   - 쿠키/세션에서 읽은 값을 역직렬화하는지
   - 역직렬화 전에 서명 검증(HMAC 등)이 있는지 — 서명 검증이 있으면 사용자가 데이터를 변조할 수 없으므로 안전
   - 화이트리스트 기반 타입 필터링이 있는지

5. **후보 목록 작성**: 각 후보에 대해 "어떤 입력을 변조하면 어떻게 임의 객체를 생성할 수 있는지"를 구체적으로 구상. 데이터 흐름 추적을 완료한 뒤에도 공격 경로가 없으면 버린다. 추적 없이 직관으로 버리지 않는다..

## 후보 판정 제한

default typing 또는 다형성 역직렬화가 활성화된 경우만 후보. 비활성화가 확인되면 제외.
