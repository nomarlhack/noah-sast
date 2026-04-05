> **호출부 추적 — 실제 URL 경로 확정**: 모든 후보에 대해 라우트 정의 파일을 Read로 읽어 실제 URL 경로를 확정한다. 컴포넌트/파일 이름에서 경로를 유추하는 것은 확정이 아니다. 절차: (1) Sink의 호출부를 Grep → 최종 페이지 컴포넌트/컨트롤러 식별 (2) 라우트 정의(routes/index.tsx, @RequestMapping 등)를 Read로 읽어 경로 문자열 확인 (3) 후보 반환 시 근거 포함: `실제 경로: /home/apply (src/routes/index.tsx:42)`

### Phase 1: 정찰 (소스코드 분석)

사용자 입력 → LDAP 쿼리 경로를 추적하여 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: LDAP 라이브러리 확인

   **Node.js:**
   - `ldapjs` — `client.search(base, { filter: ... })`
   - `activedirectory2` — Active Directory 래퍼
   - `passport-ldapauth` — LDAP 인증 미들웨어

   **Python:**
   - `python-ldap` (`ldap.search_s()`)
   - `ldap3` (`connection.search()`)
   - `django-auth-ldap` — Django LDAP 인증

   **Java:**
   - `javax.naming.directory` — JNDI (`DirContext.search()`)
   - `Spring LDAP` (`LdapTemplate.search()`)
   - `UnboundID LDAP SDK`

   **Ruby:**
   - `net-ldap` (`Net::LDAP#search`)
   - `ruby-ldap`

   **PHP:**
   - `ldap_search()`, `ldap_bind()`
   - `Adldap2` — Active Directory 래퍼

2. **Source 식별**: 사용자가 제어 가능한 입력 중 LDAP 쿼리에 사용될 수 있는 것
   - 로그인 폼의 username/password — LDAP 인증 시 필터에 삽입
   - 사용자 검색 기능의 검색어
   - 그룹/조직 조회 파라미터
   - API 요청 본문의 사용자 식별 필드

3. **Sink 식별**: LDAP 쿼리를 실행하는 코드

   **문자열 연결로 필터 구성 (위험):**
   ```javascript
   // Node.js — ldapjs
   const filter = `(&(uid=${username})(userPassword=${password}))`;
   client.search(baseDN, { filter: filter });
   ```

   ```python
   # Python — ldap3
   search_filter = f"(&(uid={username})(userPassword={password}))"
   conn.search(base_dn, search_filter)
   ```

   ```java
   // Java — JNDI
   String filter = "(&(uid=" + username + ")(userPassword=" + password + "))";
   ctx.search(baseDN, filter, searchControls);
   ```

   ```php
   // PHP
   $filter = "(&(uid=$username)(userPassword=$password))";
   ldap_search($conn, $baseDN, $filter);
   ```

   **안전한 패턴:**
   ```java
   // Java — 파라미터화된 LDAP 필터
   String filter = "(&(uid={0})(userPassword={1}))";
   ctx.search(baseDN, filter, new Object[]{username, password}, searchControls);
   ```

   ```python
   # Python — ldap3 이스케이프
   from ldap3.utils.conv import escape_filter_chars
   safe_username = escape_filter_chars(username)
   search_filter = f"(&(uid={safe_username}))"
   ```

   ```javascript
   // Node.js — ldapjs 필터 객체
   const filter = new ldap.AndFilter({
     filters: [
       new ldap.EqualityFilter({ attribute: 'uid', value: username }),
       new ldap.EqualityFilter({ attribute: 'userPassword', value: password })
     ]
   });
   ```

4. **경로 추적**: Source에서 Sink까지 데이터 흐름 확인
   - LDAP 필터 메타문자(`*`, `(`, `)`, `\`, `|`, `&`, `!`) 이스케이프 여부
   - 파라미터화된 필터 사용 여부 (Java JNDI의 `{0}` 플레이스홀더)
   - 필터 객체 API 사용 여부 (ldapjs의 `EqualityFilter` 등)
   - `ldap3.utils.conv.escape_filter_chars()` 같은 이스케이프 함수 사용 여부
   - 입력값 화이트리스트 검증 (영문자/숫자만 허용 등)

5. **후보 목록 작성**: 각 후보에 대해 "어떤 입력으로 어떻게 LDAP 필터를 변경할 수 있는지"를 구체적으로 구상. 데이터 흐름 추적을 완료한 뒤에도 공격 경로가 없으면 버린다. 추적 없이 직관으로 버리지 않는다..

## 후보 판정 제한

LDAP 서버에 직접 연결하여 필터를 구성하는 코드가 있는 경우만 후보. REST API 위임은 제외.
