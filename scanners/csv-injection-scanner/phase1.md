> ## 핵심 원칙: "수식이 CSV에 포함되지 않으면 취약점이 아니다"
>
> 사용자 입력이 CSV로 내보내지는 기능이 있다고 바로 취약점으로 보고하지 않는다. 실제로 `=`, `+`, `-`, `@`, `\t`, `\r` 같은 수식 시작 문자가 이스케이프 없이 CSV 셀에 포함되어, 스프레드시트 프로그램(Excel, Google Sheets 등)에서 열었을 때 수식이 실행되는 것을 확인해야 취약점이다.
>

### Phase 1: 정찰 (소스코드 분석)

CSV/Excel 내보내기 기능을 분석하여 사용자 입력이 이스케이프 없이 셀에 삽입되는 경로를 식별한다.

1. **내보내기 기능 식별**: CSV/Excel 파일 생성 코드 찾기

   **Node.js:**
   - `json2csv`, `csv-stringify`, `csv-writer` — CSV 생성 라이브러리
   - `exceljs`, `xlsx`, `xlsx-populate` — Excel 생성 라이브러리
   - 직접 문자열 연결로 CSV 생성 (`res.setHeader('Content-Type', 'text/csv')`)

   **Python:**
   - `csv.writer`, `csv.DictWriter` — 표준 라이브러리
   - `pandas.to_csv()`, `pandas.to_excel()` — Pandas
   - `openpyxl`, `xlsxwriter` — Excel 생성

   **Java:**
   - Apache POI — Excel 생성
   - OpenCSV — CSV 생성
   - 직접 문자열 연결

   **PHP:**
   - `fputcsv()` — 내장 함수
   - PhpSpreadsheet — Excel 생성

2. **Source 식별**: CSV에 포함될 수 있는 사용자 입력
   - 사용자가 입력한 이름, 이메일, 주소, 메모 등의 필드
   - 댓글, 리뷰, 피드백 내용
   - 폼 제출 데이터가 관리자 대시보드에서 CSV로 내보내지는 경우
   - 사용자 프로필 정보가 보고서에 포함되는 경우
   - **백엔드 API proxy 패턴 (중요)**: 앱 자체가 CSV를 생성하지 않고 `file.body`, `response.body` 등 백엔드 API 응답을 `Content-Type: text/csv`로 그대로 전달하는 경우도 포함한다. 백엔드가 댓글·게시글·사용자 입력 등을 CSV로 변환하는 과정에서 수식 문자(`=`, `+`, `-`, `@`)를 이스케이프하지 않을 수 있다. "앱이 직접 CSV를 생성하지 않으므로 해당 없음"은 잘못된 판단이다. 백엔드 코드를 확인할 수 없으면 동적 테스트(페이로드 입력 후 CSV 다운로드)로 반드시 검증한다.

3. **Sink 식별**: CSV 셀에 값을 쓰는 코드

   **취약한 패턴 (이스케이프 없이 직접 삽입):**
   ```javascript
   // Node.js — 직접 CSV 생성
   const csv = data.map(row => `${row.name},${row.email}`).join('\n');
   ```

   ```python
   # Python — csv.writer에 이스케이프 없이 전달
   writer.writerow([user_input_name, user_input_email])
   ```

   **안전한 패턴:**
   ```javascript
   // 수식 시작 문자를 이스케이프
   function sanitizeCsvCell(value) {
     if (/^[=+\-@\t\r]/.test(value)) {
       return "'" + value;  // 작은따옴표 접두사로 수식 실행 방지
     }
     return value;
   }
   ```

4. **이스케이프 로직 확인**:
   - 셀 값이 `=`, `+`, `-`, `@`, `\t`, `\r`로 시작할 때 접두사 추가 (`'`, `\t` 등)
   - 라이브러리 자체의 수식 이스케이프 옵션 사용 여부
   - `exceljs`의 `worksheet.getCell().value` vs `worksheet.getCell().formula` 구분

5. **후보 목록 작성**: 이스케이프 없이 사용자 입력이 CSV 셀에 삽입되는 경로를 정리.

## 후보 판정 제한

외부 입력이 셀에 기록되고 수식 시작 문자 이스케이프가 없는 경우만 후보.
