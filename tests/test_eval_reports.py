"""Offline evidence-retention checks; no model or network requests."""

import json
import os
import re
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]


class FreeFallbackAssertions(unittest.TestCase):
    def test_documented_free_fallback_can_pass_literal_assertions(self):
        golden = (SOURCE / ".promptfoo/golden/research-stack.yaml").read_text()
        fixtures = {
            "seo": "## SEO scorecard\nPaid SEO tools were unavailable. Free fallback: web search [WS].",
            "comms": "## Telephony and messaging plan\nPaid comms tools were unavailable. Free fallback: web search [WS].",
        }
        for focus, report in fixtures.items():
            block = next(
                part
                for part in golden.split("- description: ")[1:]
                if "--focus " + focus in part.splitlines()[0]
            )
            assertions = re.findall(r"- type: contains-any\n\s+value: (\[.*\])", block)
            self.assertTrue(assertions)
            for values in assertions:
                self.assertTrue(any(tag in report for tag in json.loads(values)), focus)
            self.assertIn("free fallbacks", block)
            # This tests literal acceptance only; the semantic rubric still needs
            # its configured provider and calibrated evaluation, not this fixture.


class EvaluationReports(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gravity-reports-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "configs").mkdir()
        (self.root / "promptfooconfig.yaml").write_text("fixture")
        (self.root / "configs/another.yaml").write_text("fixture")
        shutil.copy2(SOURCE / ".promptfoo/run-all.sh", self.root / "run-all.sh")
        binary = self.root / "bin"
        binary.mkdir()
        stub = binary / "promptfoo"
        stub.write_text("""#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
if os.environ.get("FIXTURE_ERROR"):
    print("fixture CLI diagnostic", file=sys.stderr)
    sys.exit(2)
Path(sys.argv[sys.argv.index("--output")+1]).write_text(json.dumps({
    "results": {"stats": {"successes": 0, "failures": 1, "errors": 0},
                "cases": [{"reason": "fixture assertion failed"}]}}))
print("fixture complete diagnostic")
sys.exit(int(os.environ.get("FIXTURE_EXIT", "0")))
""")
        stub.chmod(0o755)
        self.env = dict(os.environ, PATH=str(binary) + os.pathsep + os.environ["PATH"])

    def run_batch(self, error=False):
        env = dict(self.env)
        if error:
            env["FIXTURE_ERROR"] = "1"
        return subprocess.run(
            ["bash", str(self.root / "run-all.sh")],
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
        )

    def latest(self):
        pointer = self.root / "reports/latest-run"
        self.assertTrue(pointer.is_symlink(), "latest batch pointer missing")
        target = pointer.resolve(strict=True)
        self.assertEqual(target.parent, self.root / "reports")
        return target

    def test_failed_cases_and_diagnostics_survive_exit_privately(self):
        result = self.run_batch()
        self.assertNotEqual(result.returncode, 0)
        batch = self.latest()
        self.assertIn(str(batch), result.stdout)
        self.assertEqual(stat.S_IMODE(batch.stat().st_mode), 0o700)
        for skill in ("planning-stack", "another"):
            report = batch / (skill + ".json")
            self.assertEqual(
                json.loads(report.read_text())["results"]["cases"][0]["reason"],
                "fixture assertion failed",
            )
            self.assertEqual(stat.S_IMODE(report.stat().st_mode), 0o600)
            log = batch / (skill + ".log")
            self.assertIn("fixture complete diagnostic", log.read_text())
            self.assertEqual(stat.S_IMODE(log.stat().st_mode), 0o600)

    def test_error_batch_retains_logs_without_reusing_stale_results(self):
        self.run_batch()
        previous = self.latest()
        previous_report = (previous / "planning-stack.json").read_bytes()
        result = self.run_batch(error=True)
        self.assertNotEqual(result.returncode, 0)
        latest = self.latest()
        self.assertNotEqual(latest, previous)
        self.assertIn("invalid, missing or empty evaluation result", result.stdout)
        self.assertFalse((latest / "planning-stack.json").exists())
        self.assertIn(
            "fixture CLI diagnostic", (latest / "planning-stack.log").read_text()
        )
        self.assertEqual(
            (previous / "planning-stack.json").read_bytes(), previous_report
        )

    def test_valid_failed_cases_are_not_runner_errors(self):
        self.env["FIXTURE_EXIT"] = "100"
        result = self.run_batch()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("2 failed, 0 errors", result.stdout)
        self.assertIn("0 runner errors", result.stdout)
        self.assertTrue((self.latest() / "planning-stack.json").is_file())


if __name__ == "__main__":
    unittest.main()
