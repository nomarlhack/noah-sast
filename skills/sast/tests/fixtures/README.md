# Scan-report Regression Fixtures

`validate_report.py`와 `assemble_report.py`의 결정적 failure mode 재현용 pinned fixture.

## 구성

각 케이스는 **MD 파일 + 대응 master-list.json** 쌍으로 구성. toy 규모(2~3건).

| Case | 시나리오 | 기대 validate 경고 |
|------|---------|-----------------|
| A | 상세 섹션에 `**ID**:` 필드 모두 결측 | "ID 필드 누락" N건 + 양방향 집합 차 누락 N건 |
| B | `**ID**:` 오타 (master-list에 없는 ID 사용) | "ID '...'가 master-list에 없음" 1건 |
| C | master-list에 있는 ID 중 하나가 상세에서 누락 | "master-list ID '...' 상세 섹션 누락" 1건 |
| D | 섹션 경계 부제 모호 (`#### 재현 방법 및 POC` 가 경계로 오인되는지) | 파싱 성공, 경고 0건 |
| E | `**ID**:` 필드가 섹션 중간에 배치 | 파싱 성공 (정규식은 섹션 범위 내 첫 매치 수용) |
| F | `**ID**:` 필드가 섹션 내 2회 등장 | "**ID** 필드가 2회 등장" 경고 1건 |

## 실행

```bash
# 각 케이스 실행
for case in A B C D E F; do
  python3 ../../sub-skills/scan-report/validate_report.py 2 "round_case_$case" \
    --master-list "round_case_${case}_master.json" \
    --json-output "/tmp/regression_${case}.json"
  echo "Case $case exit=$?"
done
```

## 향후 확장

- 대형 규모 fixture (60건 master-list)
- 유니코드 제목/중복 ID/빈 제목 등 엣지 케이스
- 자동 assertion 스크립트 (pytest 또는 shell)
