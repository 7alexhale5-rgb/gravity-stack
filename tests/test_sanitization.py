"""External pattern files must never silently skip checks."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parent / "test_sanitization.sh"


class ExternalPatterns(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gravity-scan-test-")
        self.addCleanup(self.temp.cleanup)
        self.caller = Path(self.temp.name)
        self.repo = self.caller / "repo"
        (self.repo / "tests").mkdir(parents=True)
        shutil.copy2(SOURCE, self.repo / "tests/test_sanitization.sh")
        (self.repo / "tests/sanitization-patterns.txt").write_text("GENERIC_TEST_TOKEN\n")
        (self.repo / "sample.txt").write_text("SYNTHETIC_PRIVATE_TOKEN\n")
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.patterns = self.caller / "external.txt"

    def scan(self, value):
        env = dict(os.environ, GRAVITY_PRIVATE_PATTERNS=str(value))
        return subprocess.run(["bash", str(self.repo / "tests/test_sanitization.sh")],
                              cwd=self.caller, env=env, capture_output=True,
                              text=True, timeout=15)

    def test_relative_external_path_from_another_directory(self):
        self.patterns.write_text("SYNTHETIC_PRIVATE_TOKEN\n")
        self.assertEqual(self.scan("external.txt").returncode, 1)

    def test_final_pattern_without_newline(self):
        self.patterns.write_text("SYNTHETIC_PRIVATE_TOKEN")
        self.assertEqual(self.scan(self.patterns).returncode, 1)

    def test_clean_external_profile(self):
        self.patterns.write_text("A_DIFFERENT_SYNTHETIC_TOKEN\n")
        self.assertEqual(self.scan(self.patterns).returncode, 0)

    def test_missing_external_profile_is_error(self):
        self.assertEqual(self.scan(self.patterns).returncode, 2)

    def test_invalid_regex_is_error(self):
        self.patterns.write_text("[\n")
        self.assertEqual(self.scan(self.patterns).returncode, 2)

    def test_matched_private_pattern_is_not_printed(self):
        self.patterns.write_text("SYNTHETIC_PRIVATE_TOKEN\n")
        result = self.scan(self.patterns)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("SYNTHETIC_PRIVATE_TOKEN", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
