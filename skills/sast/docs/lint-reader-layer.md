# 독자 레이어 용어 노출 lint (`lint_reader_layer.py`)

보고서 MD/HTML의 **독자 가시 영역**에 내부 규약 용어가 노출되지 않았는지 자동 검사하는 lint 도구.

## 왜 필요한가

보고서는 **개발·운영 리더가 읽고 조치를 결정하는 문서**다. 그러나 스킬 내부 파이프라인(Phase 1/Phase 2/evaluate_phase1 등), 판정 라벨(DISCARD/OVERRIDE/CONFIRM), 스크립트명(`*.py`), checklist 섹션 번호(§N) 같은 **내부 운영 용어**가 독자에게 그대로 노출되면:

- 독자는 용어의 의미를 알지 못해 보고서 이해가 막힌다
- "프로세스가 어떻게 돌아가는지" 같은 내부 메타 정보가 판단 근거와 뒤섞인다
- 과거 보고서 리뷰에서 반복적으로 지적된 결함이다 (예: 개요에 "파이프라인: grep → Phase 1 → ..." 줄 노출)

이 lint는 **메인 에이전트/서브에이전트가 실수로 내부 용어를 독자 가시 영역에 쓸 경우 자동으로 차단**한다.

## 검사 범위

### 1. 헤딩 (MD `#` ~ `######`, HTML `<h1>` ~ `<h6>`)

보고서의 모든 헤딩 텍스트를 검사.

```markdown
## DISCARD 판정 후보    ← 위반 (내부 라벨)
## §12 검증 결과        ← 위반 (checklist 섹션 번호)
## 안전 판정 항목       ← 허용
```

### 2. 개요 섹션 필드명

보고서 최상단 개요 블록 내 `**필드명**:` 형태 라인의 **필드명 부분만** 검사. 값은 자유.

개요 블록 식별:
- 첫 `# 제목` 헤딩 직후 ~ 첫 `---` 또는 다음 `##` 헤딩 이전
- `## 개요` 서브 헤딩이 있으면 그 이후를 개요 컨텐츠 시작으로 간주

```markdown
# 통합 취약점 스캔 보고서

## 개요

**대상**: kakao-developers                       ← 허용
**스캔 일시**: 2026-04-18                         ← 허용
**스캔 방식**: 소스코드 분석 + 동적 테스트         ← 허용
**파이프라인**: grep → Phase 1 → 조립              ← 위반 (내부 메타 서술)
**Phase 2 결과**: sandbox 기반                    ← 위반 (내부 단계 서술)
```

## 금지 토큰 목록

`BANNED_PATTERNS` (정규식) — 헤딩과 개요 필드명 양쪽에 동일 적용:

| 토큰 | 설명 |
|------|------|
| `§\s*\d+` | checklist.md 섹션 번호 (§N) |
| `\bmode\s*=\s*(evaluate_phase1\|evaluate\|review)\b` | mode명 |
| `\bevaluate_phase1\b` | evaluate_phase1 |
| `\b(DISCARD\|OVERRIDE\|CONFIRM)\b` | 내부 판정 라벨 |
| `Source\s*도달성` | 내부 판정 용어 |
| `실질\s*영향\s*반증` | 내부 판정 용어 |
| `\b[a-z0-9_-]+\.py\b` | 스크립트 파일명 |
| `phase1_(validated\|discarded_reason\|eval_state)` | master-list 내부 필드명 |
| `safe_category` | 내부 분류 필드명 |
| `파이프라인` | 내부 메타 서술 |
| `Phase\s*\d+` | Phase N 같은 단계 서술 |
| `내부\s*흐름` | 내부 흐름 서술 |

### 허용되는 경우

- **본문/테이블 근거 서술**에서 풀이 형태로 사용: 허용 (예: "evaluate 평가에서 차단으로 판정됨"은 테이블 cell에서 OK)
- **개요 필드의 값** 부분: 허용 (필드명만 검사)
- **코드 블록·인용 블록**: lint는 라인 단위 매칭이라 기술적으로 헤딩이 아니면 스킵됨

## 사용법

```bash
python3 tools/lint_reader_layer.py <report.md> [<report.html>]
```

예시:

```bash
# MD만 검사
python3 tools/lint_reader_layer.py noah-sast-report.md

# MD + HTML 모두 검사 (권장)
python3 tools/lint_reader_layer.py noah-sast-report.md noah-sast-report.html
```

## Exit Code

| exit | 의미 |
|------|------|
| `0` | pass — 위반 없음 |
| `5` | lint 위반 — 내부 용어가 헤딩/개요 필드에 노출됨 |
| `1` | CLI 인자 오류 |

보고서 생성 파이프라인(scan-report `Step 4`)에서 lint exit 5가 발생하면 수정 후 재조립 필요.

## 실행 예시

### 통과 케이스

```
$ python3 tools/lint_reader_layer.py noah-sast-report.md noah-sast-report.html
OK: lint 통과
```

### 실패 케이스

```
$ python3 tools/lint_reader_layer.py bad-report.md
FAIL: 독자 레이어 용어 노출 2건
  - bad-report.md:11 (개요 필드): 금지 토큰 '파이프라인 (내부 메타 서술)' → "**파이프라인**:"
  - bad-report.md:12 (개요 필드): 금지 토큰 'Phase N (내부 단계 서술)' → "**Phase 2 결과**:"

금지 토큰은 헤딩(# ~ ######)에서만 검사됩니다. 근거 테이블·본문은 풀이 형태로 허용됩니다.
vuln-format.md 'safe 판정 4분류' 섹션의 '독자 레이어 노출 금지 용어' 목록 참조.
```

## 위반 발생 시 대응

1. **개요 필드명 위반**: `vuln-format.md` "통합 보고서 구조"의 허용 필드 5개(대상/스캔 일시/스캔 방식/테스트 환경/스택)만 사용. 내부 메타 서술 필드(`**파이프라인**:`, `**Phase N**:` 등)는 삭제.
2. **헤딩 위반**: 헤딩 텍스트를 독자 친화적 표현으로 교체. 필요한 정보는 본문 근거 테이블에 풀이 형태로 이관.
3. 수정 후 `assemble_report.py` 재실행 → lint 재실행하여 통과 확인.

## 신규 금지 토큰 추가 방법

새로운 내부 용어가 도입되어 독자 레이어에서 차단해야 할 경우:

1. `tools/lint_reader_layer.py`의 `BANNED_PATTERNS` 리스트에 `(정규식, 설명)` 튜플 추가
2. 회귀 테스트: 기존 보고서에 lint 실행하여 false positive 확인
3. 필요 시 `vuln-format.md`의 "독자 레이어 노출 금지 용어" 섹션에도 동기화 기록

## 관련 자산

- `sub-skills/scan-report/vuln-format.md` — 보고서 구조 스펙 + "독자 레이어 노출 금지 용어" 규약
- `sub-skills/scan-report/validate_report.py` — 정량/구조 검증 (POC 개수, ID 필드, URL 일관성)
- `sub-skills/scan-report/validate_links.py` — HTML 앵커 링크 검증
- `docs/review-modes.md` — evaluate/review 모드 상세 가이드

## 확장 이력

- **v1 (초기)**: 헤딩(h1~h6)만 검사. 9개 금지 토큰.
- **v2 (본 문서 기준)**: 개요 섹션 `**필드명**:` 라인 검사 범위 추가. 금지 토큰 3개 추가(`파이프라인`, `Phase N`, `내부 흐름`).
