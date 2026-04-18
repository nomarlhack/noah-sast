#!/usr/bin/env python3
"""validate_report.py 기본 테스트.

테스트 케이스:
  1. PASS — MD/HTML POC 건수 일치
  2. FAIL — POC 건수 불일치 → 파일 삭제
  3. 잘못된 인자 (비정수) → exit 1
"""
import os, subprocess, tempfile, unittest

SCRIPT = os.path.join(
    os.path.dirname(__file__), "..", "..", "sub-skills", "scan-report", "validate_report.py"
)


def _make_report(directory, name, poc_count, chain=False):
    """지정된 POC 건수를 가진 MD/HTML 픽스처 생성."""
    poc_block = "\n".join([f"#### {i+1}. 취약점 {i+1}\n\n**재현 방법 및 POC**:\ncurl ...\n" for i in range(poc_count)])
    chain_block = "\n## 연계 시나리오\n\n체인 내용\n" if chain else ""
    content = f"# 보고서\n\n{poc_block}{chain_block}"

    with open(os.path.join(directory, f"{name}.md"), "w", encoding="utf-8") as f:
        f.write(content)
    with open(os.path.join(directory, f"{name}.html"), "w", encoding="utf-8") as f:
        f.write(f"<html><body>{content}</body></html>")


class TestValidateReport(unittest.TestCase):
    def _run(self, args, cwd):
        return subprocess.run(
            ["python3", SCRIPT] + args,
            capture_output=True, text=True, timeout=10, cwd=cwd,
        )

    def test_pass(self):
        """POC 건수 일치 → PASS + exit 0"""
        with tempfile.TemporaryDirectory() as d:
            _make_report(d, "noah-sast-report", 3)
            r = self._run(["3"], d)
            self.assertEqual(r.returncode, 0, f"stdout: {r.stdout}")
            self.assertIn("PASS", r.stdout)

    def test_fail_deletes_files(self):
        """POC 건수 불일치 → FAIL + 파일 삭제 + exit 1"""
        with tempfile.TemporaryDirectory() as d:
            _make_report(d, "noah-sast-report", 2)
            md_path = os.path.join(d, "noah-sast-report.md")
            html_path = os.path.join(d, "noah-sast-report.html")
            self.assertTrue(os.path.exists(md_path))

            r = self._run(["5"], d)
            self.assertEqual(r.returncode, 1)
            self.assertIn("FAIL", r.stdout)
            self.assertFalse(os.path.exists(md_path), "MD 파일이 삭제되어야 함")
            self.assertFalse(os.path.exists(html_path), "HTML 파일이 삭제되어야 함")

    def test_chain_analysis_pass(self):
        """--chain-analysis + 연계 시나리오 섹션 존재 → PASS"""
        with tempfile.TemporaryDirectory() as d:
            _make_report(d, "noah-sast-report", 2, chain=True)
            r = self._run(["2", "--chain-analysis"], d)
            self.assertEqual(r.returncode, 0, f"stdout: {r.stdout}")
            self.assertIn("chain-analysis", r.stdout)

    def test_invalid_arg(self):
        """비정수 인자 → exit 1"""
        with tempfile.TemporaryDirectory() as d:
            r = self._run(["abc"], d)
            self.assertEqual(r.returncode, 1)
            self.assertIn("정수", r.stderr)

    def test_no_args(self):
        """인자 없이 실행 → Usage + exit 1"""
        with tempfile.TemporaryDirectory() as d:
            r = self._run([], d)
            self.assertEqual(r.returncode, 1)
            self.assertIn("Usage", r.stdout)


if __name__ == "__main__":
    unittest.main()
