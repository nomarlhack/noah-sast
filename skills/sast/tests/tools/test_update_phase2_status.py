#!/usr/bin/env python3
"""update-phase2-status.py 기본 테스트.

테스트 케이스:
  1. 정상 Phase 2 결과 → master-list.json 상태 갱신
  2. Phase 2 파일 없음 → 갱신 없이 종료
  3. 잘못된 manifest → WARNING + 부분 갱신
"""
import json, os, subprocess, tempfile, unittest

SCRIPT = os.path.join(
    os.path.dirname(__file__), "..", "..", "tools", "update-phase2-status.py"
)

MASTER_LIST = {
    "candidates": [
        {"id": "XSS-1", "title": "Comment XSS", "file": "a.tsx", "line": 1},
        {"id": "XSS-2", "title": "Post XSS", "file": "b.tsx", "line": 2},
        {"id": "SSRF-1", "title": "Webhook SSRF", "file": "c.ts", "line": 3},
    ],
    "clean_scanners": ["sqli-scanner"],
}

PHASE2_RESULT = """\
# xss-scanner Phase 2 결과

## XSS-1: Comment XSS
### Status: 확인됨
### POC
curl -X POST ...
### 실행 결과
HTTP 200 — alert 발화

## XSS-2: Post XSS
### Status: 안전
### POC
curl -X POST ...
### 실행 결과
HTTP 404 — 게이트웨이 차단
### 판정 근거
게이트웨이 라우팅 설정에서 차단 확인

<!-- NOAH-SAST PHASE2 MANIFEST v1 -->
```json
{
  "scanner": "xss-scanner",
  "results": [
    {"id": "XSS-1", "status": "confirmed", "evidence": "XSS alert 발화"},
    {"id": "XSS-2", "status": "safe", "defense_layer": "gateway", "defense_detail": "nginx.conf:42"}
  ]
}
```
<!-- /NOAH-SAST PHASE2 MANIFEST -->
"""

INVALID_PHASE2 = """\
# ssrf-scanner Phase 2 결과

<!-- NOAH-SAST PHASE2 MANIFEST v1 -->
```json
{bad json}
```
<!-- /NOAH-SAST PHASE2 MANIFEST -->
"""


class TestUpdatePhase2Status(unittest.TestCase):
    def _setup_dir(self, phase2_files=None):
        """임시 디렉토리에 master-list.json + Phase 2 파일 생성."""
        d = tempfile.mkdtemp()
        master_path = os.path.join(d, "master-list.json")
        with open(master_path, "w", encoding="utf-8") as f:
            json.dump(MASTER_LIST, f, ensure_ascii=False)
        if phase2_files:
            for name, content in phase2_files.items():
                with open(os.path.join(d, name), "w", encoding="utf-8") as f:
                    f.write(content)
        return d, master_path

    def _run(self, phase1_dir, master_path):
        return subprocess.run(
            ["python3", SCRIPT, phase1_dir, master_path],
            capture_output=True, text=True, timeout=10,
        )

    def test_normal_update(self):
        """정상 Phase 2 결과 → status 갱신"""
        d, mp = self._setup_dir({"xss-scanner-phase2.md": PHASE2_RESULT})
        r = self._run(d, mp)
        self.assertEqual(r.returncode, 0, f"stderr: {r.stderr}")
        self.assertIn("2건 갱신", r.stdout)

        with open(mp, encoding="utf-8") as f:
            data = json.load(f)
        by_id = {c["id"]: c for c in data["candidates"]}
        self.assertEqual(by_id["XSS-1"]["status"], "confirmed")
        self.assertEqual(by_id["XSS-2"]["status"], "safe")
        self.assertNotIn("status", by_id["SSRF-1"])

    def test_no_phase2_files(self):
        """Phase 2 파일 없음 → 갱신 없이 exit 0"""
        d, mp = self._setup_dir()
        r = self._run(d, mp)
        self.assertEqual(r.returncode, 0)
        self.assertIn("파일 없음", r.stdout)

    def test_invalid_manifest(self):
        """잘못된 manifest → WARNING + exit 0"""
        d, mp = self._setup_dir({"ssrf-scanner-phase2.md": INVALID_PHASE2})
        r = self._run(d, mp)
        self.assertEqual(r.returncode, 0)
        self.assertIn("WARNING", r.stderr)

    def test_no_args(self):
        """인자 없이 실행 → Usage + exit 1"""
        r = subprocess.run(
            ["python3", SCRIPT], capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(r.returncode, 1)
        self.assertIn("Usage", r.stderr)


if __name__ == "__main__":
    unittest.main()
