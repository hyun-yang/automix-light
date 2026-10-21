"""Windows Python 안내가 세 도구에서 다시 어긋나지 않는지 검사한다."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]


class PythonGuidanceTest(unittest.TestCase):
    def test_all_command_guides_select_runnable_python(self):
        for tool, folder in (("claude-code", "commands"), ("codex", "skills"), ("copilot", "skills")):
            for command in ("go", "doctor", "status"):
                path = ROOT / tool / "aml" / folder / (f"{command}.md" if folder == "commands" else f"{command}/SKILL.md")
                with self.subTest(path=str(path.relative_to(ROOT))):
                    content = path.read_text(encoding="utf-8")
                    self.assertIn("py -3", content)
                    self.assertIn("python -c", content)
                    self.assertNotRegex(content, r"(?m)^\s*python3\s+[^\n]*observe\.py")
                    self.assertNotIn("command -v python3", content)

    def test_measurement_examples_use_selected_python(self):
        for tool in ("codex", "copilot"):
            path = ROOT / tool / "aml/references/telemetry.md"
            with self.subTest(tool=tool):
                content = path.read_text(encoding="utf-8")
                self.assertIn("py -3", content)
                self.assertNotRegex(content, r"(?m)^python3\s+[^\n]*observe\.py")

    def test_windows_readmes_explain_measurement_fallback(self):
        for path in (ROOT / "README.md", *(ROOT / tool / "README.md" for tool in ("claude-code", "codex", "copilot"))):
            with self.subTest(path=str(path.relative_to(ROOT))):
                content = path.read_text(encoding="utf-8")
                self.assertIn("py -3", content)
                self.assertRegex(content, re.compile(r"python.{0,120}측정|측정.{0,120}python", re.DOTALL | re.IGNORECASE))


if __name__ == "__main__":
    unittest.main()
