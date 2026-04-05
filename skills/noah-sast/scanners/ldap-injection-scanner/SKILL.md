
# LDAP Injection Scanner

소스코드 분석으로 LDAP Injection 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 LDAP 필터를 변경하여 인증 우회나 정보 유출이 가능한지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "LDAP 필터가 변경되지 않으면 취약점이 아니다"

소스코드에서 LDAP 쿼리를 사용한다고 바로 취약점으로 보고하지 않는다. 실제로 사용자가 제어한 입력에 `*`, `)(`, `|`, `&` 등 LDAP 필터 메타문자를 삽입하여 필터 로직을 변경할 수 있는 것을 확인해야 취약점이다.

## LDAP Injection의 유형

### 인증 우회 (Authentication Bypass)
로그인 시 LDAP 필터에 사용자 입력이 직접 삽입되어, `*)` 같은 와일드카드로 필터 조건을 무효화하는 공격.

```
# 정상 필터
(&(uid=admin)(userPassword=secret))

# 공격: uid에 admin)(| 삽입 → 패스워드 조건 무효화
(&(uid=admin)(|(uid=*))(userPassword=anything))
```

### 정보 유출 (Information Disclosure)
LDAP 검색 필터를 조작하여 의도하지 않은 사용자 정보, 그룹 정보, 디렉토리 구조를 조회하는 공격.

### Blind LDAP Injection
LDAP 쿼리 결과가 직접 반환되지 않지만, 응답 차이(로그인 성공/실패, 결과 유무)로 데이터를 한 글자씩 추론하는 공격. `*` 와일드카드와 문자 조합으로 속성값을 추출.

### DN Injection
Distinguished Name에 사용자 입력이 삽입되어, DN 구조를 변경하는 공격.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

