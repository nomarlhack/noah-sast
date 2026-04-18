---
grep_patterns:
  - "\\beval\\s*\\("
  - "\\$\\{.*\\}"
  - "\\|\\s*safe"
---

# Meta Scanner

정규식 메타문자($, |, \, 공백) 포함 패턴. shell 해석 없이 argv로 전달되는지 검증.
