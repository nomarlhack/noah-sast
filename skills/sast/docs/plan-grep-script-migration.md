# Plan: grep 인덱싱 에이전트 → 스크립트 전환

**상태:** Draft (승인 대기)
**작성일:** 2026-04-18
**영향 범위:** `SKILL.md` Step 0, `prompts/grep-agent.md`(삭제 예정), `tools/run_grep_index.py`(신규)

---

## 1. 배경

### 1-1. 현재 구조
`SKILL.md` Step 0은 **서브에이전트**(`prompts/grep-agent.md`)를 생성하여 41개 스캐너의 grep 패턴을 프로젝트 전체에 실행하고, 스캐너별 JSON 인덱스를 생성한다.

### 1-2. 관찰된 문제
서브에이전트가 **"grep 호출을 수행할 Python 스크립트(`run_scan.py`)를 작성만 하고 실행하지 않은 채 종료"**하는 드리프트가 재발한다. 과거 세션 4건 중 2건에서 `_runner.py`, `_run_grep.py`, `_batch*.json` 같은 부산물이 확인됐고, 최근 세션은 **JSON 인덱스 0개** 상태로 종료되어 파이프라인이 시작점에서 멈춤.

### 1-3. 근본 원인
- grep 실행은 **판단이 필요 없는 기계적 작업**. LLM 에이전트에게 위임할 이유가 없음
- 41 스캐너 × 평균 ~20 패턴 = ~820 grep 호출 부담에 에이전트가 "스크립트화하여 한 번에 실행"이라는 단축 경로를 택하는 것이 반복 재현됨
- 지침(`grep-agent.md`)에 "스크립트 작성만 하고 종료 금지" 조항을 추가해도 이는 대증 요법 — 구조적으로 에이전트가 할 일이 아님

---

## 2. 목표와 비목표

### 목표
- grep 인덱싱을 결정적 스크립트(`tools/run_grep_index.py`)로 대체
- 기존 JSON 포맷 바이트 호환 유지 (`scanner-selector.py` 계약 보존)
- 개별 스캐너 실패의 영향을 격리 (전체 중단 방지)

### 비목표 (YAGNI)
- `--only` 선택 실행 옵션 (1버전 미포함)
- `--workers` 병렬화 옵션 (직렬 벤치마크 후 판단)
- 전용 문서 `docs/run-grep-index.md` 신설 (`--help` + SKILL.md 주석으로 충분)

---

## 3. 전체 흐름도

### 3-1. Before vs After

```
Before (현재)                         After (제안)
━━━━━━━━━━━━━━━━━━━━━━━━━━━         ━━━━━━━━━━━━━━━━━━━━━━━━━━━

[메인 에이전트]                       [메인 에이전트]
      │                                     │
      │ PATTERN_INDEX_DIR 경로 생성          │ PATTERN_INDEX_DIR 경로 생성
      │                                     │
      ▼                                     ▼
┌────────────────────┐              ┌────────────────────┐
│ Agent 도구 호출     │              │ Bash 도구 호출      │
│ grep-agent.md Read │              │ run_grep_index.py  │
└────────────────────┘              └────────────────────┘
      │                                     │
      ▼                                     ▼
[서브 에이전트 (LLM)]                  [Python 프로세스]
  · phase1.md Read × 41                · yaml.safe_load × 41
  · grep 명령 구성                      · subprocess.run(grep) × ~820
  · Bash 실행 (때때로 스크립트만 작성)   · JSON 저장 × 41
  · Write JSON × 41                    · stdout 카운트 요약
  · 반환 텍스트 카운트 요약              · exit 0/1/2
      │                                     │
      │ ← 드리프트 발생 지점                 │ ← 결정적, 드리프트 개념 없음
      │                                     │
      ▼                                     ▼
[메인 에이전트]                       [메인 에이전트]
  · 반환 파싱                           · exit code 분기
  · 드리프트 감지 Bash 가드              · 무결성 가드 (ls | wc -l)
  · [INCOMPLETE] 재실행                 · _failures.json 확인 → 재실행
      │                                     │
      ▼                                     ▼
┌────────────────────┐              ┌────────────────────┐
│ scanner-selector   │              │ scanner-selector   │  ← 동일 (JSON 포맷 불변)
└────────────────────┘              └────────────────────┘
```

### 3-2. 스크립트 내부 흐름 (`run_grep_index.py`)

```
┌──────────────────────────────────────────────┐
│  START                                        │
│    args: --scanners-dir --project-root        │
│          --out-dir                            │
└──────────────────────────────────────────────┘
                     │
                     ▼
         ┌──────────────────────┐
         │  grep --version 확인  │ ─── 실패 ──► exit 1
         └──────────────────────┘
                     │ 성공
                     ▼
         ┌──────────────────────┐
         │  out-dir mkdir -p    │
         └──────────────────────┘
                     │
                     ▼
    ┌──────────────────────────────────┐
    │ FOR scanner IN 41개 스캐너:       │
    │                                  │
    │   phase1.md Read                 │
    │      │                           │
    │      ├── YAML parse 실패         │──► _failures.json
    │      │                           │   reason=yaml_parse_error
    │      │                           │   빈 {} 저장, 다음 스캐너
    │      │                           │
    │      ▼                           │
    │   grep_patterns 추출             │
    │      │                           │
    │      ▼                           │
    │   FOR pattern IN grep_patterns:  │
    │     subprocess.run([grep, ...]   │
    │                    shell=False,  │
    │                    timeout=120)  │
    │      │                           │
    │      ├── timeout / crash         │──► _failures.json
    │      │                           │   reason=grep_timeout
    │      │                           │   이 패턴만 빈 배열
    │      │                           │
    │      ├── regex error             │──► _failures.json
    │      │                           │   reason=regex_error
    │      │                           │
    │      └── 성공                     │──► 결과 누적
    │                                  │
    │   <scanner>.json Write           │
    │                                  │
    └──────────────────────────────────┘
                     │
                     ▼
    ┌──────────────────────────────────┐
    │ 무결성 검증                       │
    │   ls *.json == 41?              │─── no ──► exit 1
    │                                  │
    │ _failures.json 있음?             │─── yes ─► exit 2
    └──────────────────────────────────┘
                     │ 성공
                     ▼
         ┌──────────────────────┐
         │  stdout: 카운트 요약  │
         │  exit 0              │
         └──────────────────────┘
```

### 3-3. SKILL.md Step 0 흐름 (After)

```
Step 0: 패턴 인덱싱
━━━━━━━━━━━━━━━━━━
  1. PATTERN_INDEX_DIR 경로 생성 (Bash date)
  2. run_grep_index.py 실행 (Bash)
        │
        ▼
     exit code?
      ├─ 0 ─► Step 1 진행
      ├─ 2 ─► _failures.json 확인
      │        │
      │        ├─ regex_error 다수 → phase1.md 패턴 수정 필요 (버그)
      │        ├─ grep_timeout 다수 → 프로젝트 규모 분할 검토
      │        └─ io_error → 파일 시스템 진단 후 재실행
      │
      └─ 1 ─► 환경 점검 (grep/python3 부재, out-dir 권한 등)
  3. 무결성 검증 (ls *.json == 41)
  4. Step 1로 전달
```

---

## 4. 불변 제약 (모든 단계에서 지킬 것)

| 제약 | 이유 |
|------|------|
| JSON 포맷 바이트 호환: `{pattern: [file:line, ...]}` | `scanner-selector.py`와의 계약 (파싱 경로 불변) |
| 히트 0인 패턴도 빈 배열로 명시 저장 | 기존 agent 동작 호환 |
| 단일 진실 원천 — `prompts/grep-agent.md` 완전 제거 | 이중 경로는 드리프트 유인 |
| 개별 스캐너 실패가 전체 중단을 유발하지 않음 | phase1.md 한 파일 오타로 스캔 전체 마비 방지 |
| `subprocess.run` `shell=False` + argv 전달 | regex 메타문자 셸 해석 오염 방지 |

---

## 5. 스크립트 상세 사양

### 5-1. CLI
```bash
python3 tools/run_grep_index.py \
  --scanners-dir <NOAH_SAST_DIR>/scanners \
  --project-root <PROJECT_ROOT> \
  --out-dir <PATTERN_INDEX_DIR>
```

### 5-2. 입력 파싱
- `<scanners-dir>/*/phase1.md` 41개 순회
- 상단 `---` ~ `---` frontmatter 블록을 `yaml.safe_load`로 파싱
- `grep_patterns:` 리스트 추출 (누락/빈 리스트도 허용)

### 5-3. grep 실행
- 각 패턴에 대해 1회 `subprocess.run(["grep", "-rn", ...])` (배치 안 함 — 매치 패턴 식별 불가 문제)
- `--include`, `--exclude-dir`는 `grep-agent.md`의 리스트 그대로 재사용
- `timeout=120`, `shell=False`, `check=False`
- 출력 라인을 `파일경로:라인번호` 형식으로 파싱 (코드 내용 제거)

### 5-4. 저장 포맷

**`<PATTERN_INDEX_DIR>/<scanner>.json`:**
```json
{
  "innerHTML": ["app/components/Comment.jsx:18", "app/components/Post.jsx:55"],
  "dangerouslySetInnerHTML": ["app/components/Comment.jsx:18"],
  "html_safe": []
}
```

**`<PATTERN_INDEX_DIR>/_failures.json` (실패 발생 시에만):**
```json
{
  "xss-scanner": [
    {"pattern": "(?bad)", "reason": "regex_error", "detail": "..."}
  ],
  "business-logic-scanner": [
    {"scanner": "business-logic-scanner", "reason": "yaml_parse_error", "detail": "..."}
  ]
}
```

### 5-5. stdout 형식 (기존 agent 반환과 동일)
```
파일 저장 완료: /tmp/scan_index_.../

스캐너별 히트 건수 (파일경로:라인번호 기준):
xss-scanner: 127건
dom-xss-scanner: 43건
...
```

### 5-6. Exit Code

| exit | 의미 | 메인 에이전트 조치 |
|------|------|-------------------|
| `0` | 41개 JSON 모두 정상 저장, 실패 없음 | Step 1 진행 |
| `1` | 환경/CLI 오류 (grep 부재, 권한, 경로 오타 등) | 진단 후 재실행 |
| `2` | 부분 실패 (`_failures.json` 생성됨) | reason별 조치 후 재실행 |

---

## 6. 테스트 전략

### 6-1. 합성 fixture 단위 테스트 (신규)
경로: `tests/run-grep-index/`

```
tests/run-grep-index/
  fixtures/
    case_01_basic/
      project/           ← 미니 프로젝트
      scanners/
        dummy-scanner/
          phase1.md      ← grep_patterns 정의
      expected.json      ← 예상 JSON
    case_02_empty_patterns/    ← business-logic-scanner 케이스
    case_03_regex_meta/        ← $, |, \ 등 메타문자 패턴
    case_04_unicode_path/      ← 한글 경로
    case_05_yaml_malformed/    ← YAML 오류 → _failures.json 검증
  run_tests.py
```

각 케이스: 스크립트 실행 → `actual.json` == `expected.json` 또는 `_failures.json`에 예상 오류 있음.

### 6-2. 하류 호환 검증
- 합성 fixture 출력으로 `scanner-selector.py` 실행
- 기존 agent 결과와 그룹 편성 **출력 텍스트 일치** 확인

### 6-3. 실전 비교 (참고용, 판정 기준 아님)
- `/tmp/scan_index_developers_1776435354/`를 레퍼런스로 diff
- 판정 기준으로 쓰지 않는 이유: agent 결과물 정확성 자체 미검증

---

## 7. SKILL.md 변경

### 7-1. Step 0 재작성
Before: Agent 생성 블록 + 드리프트 감지 Bash 가드
After: Bash 한 블록 + 무결성 가드

### 7-2. 변경 전후 요약

| 요소 | Before | After |
|------|--------|-------|
| 실행 주체 | 서브에이전트 | Python 스크립트 |
| 호출 방식 | `Agent` 도구 | `Bash` 도구 |
| 재실행 트리거 | `[INCOMPLETE: scanner-name]` 텍스트 라벨 | `_failures.json` + exit 2 |
| 카운트 요약 | 에이전트 반환 텍스트 | 스크립트 stdout |
| 드리프트 가드 | "run_scan.py 존재 여부" 검사 | (제거) |
| 무결성 가드 | — | `ls *.json == 41` |

---

## 8. 제거 대상

| 파일/블록 | 처리 | 이유 |
|-----------|------|------|
| `prompts/grep-agent.md` | 삭제 | 단일 진실 원천 — 스크립트로 완전 대체 |
| 커밋 `7571f6b`의 드리프트 특화 Bash 블록 (SKILL.md Step 0-2) | 제거 | 스크립트 체계에서 의미 상실 (무결성 가드로 대체) |
| SKILL.md "grep 에이전트" 모든 언급 | 정리 | 용어 일관성 |

**주의:** 커밋 `7571f6b`의 `grep-agent.md` 내 "실행 규약" 섹션도 파일 자체가 삭제되므로 자동 제거됨.

---

## 9. 커밋 전략

병합 전 2개 커밋으로 분리:

### 커밋 1: `feat(sast): run_grep_index.py 및 합성 fixture 테스트`
- `tools/run_grep_index.py` 신규
- `tests/run-grep-index/` 신규 (fixture + runner)
- 스크립트가 동작함은 테스트로 입증, SKILL.md는 변경 안 함 → **기존 에이전트 경로 유지, 새 경로 준비만**

### 커밋 2: `refactor(sast): grep 에이전트를 스크립트로 교체`
- `SKILL.md` Step 0 재작성 (드리프트 가드 제거 + Bash 스크립트 호출로 교체)
- `prompts/grep-agent.md` 삭제
- SKILL.md 다른 위치의 grep-agent 언급 정리

**분리 이유:** 회귀 발생 시 커밋 2만 revert하면 기존 에이전트 경로로 복귀 가능 (커밋 1의 스크립트는 독립 자산으로 남음).

---

## 10. 롤백 계획

| 시나리오 | 대응 |
|----------|------|
| 스크립트가 회귀 fixture는 통과하지만 실전 프로젝트에서 실패 | 커밋 2 revert → 에이전트 경로 복귀, 스크립트 버그 수정 후 재적용 |
| `scanner-selector.py`가 스크립트 출력을 거부 | JSON 포맷 diff 확인, 스크립트 수정 |
| macOS에서는 통과, Linux에서 실패 (또는 역순) | `grep --version` 가드에 OS 분기 추가 |

---

## 11. 편향·오용·모순 방어

| 유형 | 위험 | 방어 |
|------|------|------|
| 편향 | "스크립트 = 항상 빠르다" | 배치 포기 (패턴별 호출), 병렬화 보류 |
| 편향 | "기존 agent 결과물 = 정답" | 합성 fixture로 독립 검증, agent diff는 참고용 |
| 편향 | macOS 단일 환경 가정 | `grep --version` 런타임 체크 |
| 오용 | YAML 파싱 오류 → 전체 중단 | 스캐너 단위 격리, `_failures.json`에 기록 후 계속 |
| 오용 | `[INCOMPLETE]`와 스크립트 failure 동일시 | `_failures.json`에 `reason` 필드로 유형 구분 |
| 오용 | `--only` 1버전 도입 | YAGNI, 보류 |
| 모순 | 바이트 호환 ↔ 배치 grep | 배치 포기로 해소 |
| 모순 | 드리프트 없음 ↔ 스크립트 실패 가능 | 용어만 변경 (드리프트 → 무결성), 가드 유지 |
| 내재 한계 | 단일 실패 지점 | 합성 fixture + 하류 호환 테스트로 보완 |

---

## 12. 진행 순서 체크리스트

- [ ] 합성 fixture 설계 (6-1의 5개 케이스)
- [ ] `tools/run_grep_index.py` 작성
- [ ] `tests/run-grep-index/run_tests.py` 작성
- [ ] 로컬에서 fixture 테스트 모두 통과 확인
- [ ] `scanner-selector.py`로 하류 호환 확인
- [ ] 실전 프로젝트(developers/) 1회 실행 → 기존 결과와 diff (참고용)
- [ ] 커밋 1 (스크립트 + 테스트)
- [ ] SKILL.md Step 0 재작성
- [ ] `prompts/grep-agent.md` 삭제
- [ ] 커밋 2 (SKILL.md + grep-agent.md 삭제)
- [ ] Push

---

## 13. 관련 자산

- **현재 agent 프롬프트** (삭제 예정): `prompts/grep-agent.md`
- **JSON 소비자** (변경 없음): `tools/scanner-selector.py` 42-53행
- **하류 에이전트** (JSON 경로만 전달, 파싱 자율): `prompts/phase1-group-agent.md`
- **독립 회귀 테스트** (영향 없음): `tests/grep-coverage/run_coverage.py`
- **재발 동기**: 최근 세션 `/tmp/scan_index_developers_1776498641/run_scan.py`
