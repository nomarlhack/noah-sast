---
grep_patterns:
  - "valid_pattern"
  : broken YAML here
    - indent mismatch
---

# Broken Scanner

YAML 파싱 실패 시 _failures.json 기록 + 빈 JSON 생성, 다른 스캐너는 계속 진행.
