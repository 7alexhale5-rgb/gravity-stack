#!/usr/bin/env python3
"""Run: python3 -m unittest discover -s tests -p test_installer.py

Exercises the real master installer. Only prerequisite phases and external git
are stubbed; HOME/PATH are subprocess-local. No network or host installation.
"""

import os
import json
from pathlib import Path
import shutil
import shlex
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]


class EvaluationRunner(unittest.TestCase):
    def run_case(self, stats=None, cli_exit=0, write_result=True):
        with tempfile.TemporaryDirectory(prefix="gravity-eval-") as directory:
            root = Path(directory)
            (root / "configs").mkdir()
            (root / "promptfooconfig.yaml").write_text("fixture")
            (root / "configs/another.yaml").write_text("fixture")
            shutil.copy2(SOURCE / ".promptfoo/run-all.sh", root / "run-all.sh")
            binary = root / "bin"
            binary.mkdir()
            stub = binary / "promptfoo"
            stub.write_text(
                "#!/usr/bin/env python3\nimport json,os,sys\nfrom pathlib import Path\n"
                'with open(os.environ["CALLS"],"a") as f: f.write("called\\n")\n'
                'if os.environ["WRITE_RESULT"]=="1" and "--output" in sys.argv:\n'
                ' Path(sys.argv[sys.argv.index("--output")+1]).write_text(os.environ["RESULT"])\n'
                'print("0 passed, 1 failed, 0 errors")\n'
                'sys.exit(int(os.environ["CLI_EXIT"]))\n'
            )
            stub.chmod(0o755)
            env = dict(
                os.environ,
                PATH=str(binary) + os.pathsep + os.environ["PATH"],
                CALLS=str(root / "calls"),
                RESULT=json.dumps({"results": {"stats": stats}}),
                CLI_EXIT=str(cli_exit),
                WRITE_RESULT=str(int(write_result)),
            )
            result = subprocess.run(
                ["bash", str(root / "run-all.sh")],
                env=env,
                capture_output=True,
                text=True,
                timeout=15,
            )
            return result, (root / "calls").read_text().count("called")

    def test_failed_assertions_fail_even_when_cli_succeeds(self):
        result, calls = self.run_case({"successes": 0, "failures": 1, "errors": 0})
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertEqual(calls, 2)

    def test_positive_result_uses_json_not_console_wording(self):
        result, calls = self.run_case({"successes": 1, "failures": 0, "errors": 0})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("2/2 passed", result.stdout)
        self.assertEqual(calls, 2)

    def test_no_cases_or_invalid_counts_never_pass(self):
        for stats in (
            None,
            {},
            {"successes": 0, "failures": 0, "errors": 0},
            {"successes": True, "failures": 0, "errors": 0},
            {"successes": -1, "failures": 0, "errors": 0},
        ):
            with self.subTest(stats=stats):
                result, _ = self.run_case(stats)
                self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_cli_error_does_not_skip_other_configs(self):
        result, calls = self.run_case(
            {"successes": 1, "failures": 0, "errors": 0}, cli_exit=2
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, 2)

    def test_missing_result_fails(self):
        result, _ = self.run_case(write_result=False)
        self.assertNotEqual(result.returncode, 0)


class McpRegistration(unittest.TestCase):
    def test_registration_preserves_existing_entries_and_second_run_is_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / "bin"
            binary.mkdir()
            store = root / ".claude.json"
            original = {"command": "custom-server", "args": ["--custom"]}
            store.write_text(json.dumps({"mcpServers": {"playwright": original}}))
            stub = binary / "claude"
            stub.write_text("""#!/usr/bin/env python3
import json,os,sys
from pathlib import Path
root=Path(os.environ['HOME']);store=root/'.claude.json'
if sys.argv[1:3] != ['mcp','add']: sys.exit(3)
name=sys.argv[sys.argv.index('--scope')+2]
d=json.loads(store.read_text());d['mcpServers'][name]={'command':'fixture'}
store.write_text(json.dumps(d))
with (root/'calls').open('a') as f:f.write(name+'\\n')
""")
            stub.chmod(0o755)
            env = dict(
                os.environ,
                HOME=str(root),
                PATH=str(binary) + os.pathsep + os.environ["PATH"],
                GRAVITY_INSTALL_OPENAI_DOCS="1",
            )
            env.pop("CLAUDE_CONFIG_DIR", None)
            for _ in range(2):
                run = subprocess.run(
                    ["bash", str(SOURCE / "toolkit/scripts/03-mcp-servers.sh")],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(
                json.loads(store.read_text())["mcpServers"]["playwright"], original
            )
            self.assertEqual(len((root / "calls").read_text().splitlines()), 5)
            self.assertIn("openai-docs", json.loads(store.read_text())["mcpServers"])


class PhaseSix(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gravity-phase6-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.toolkit = self.root / "toolkit"
        (self.toolkit / "scripts").mkdir(parents=True)
        shutil.copy2(SOURCE / "toolkit/install.sh", self.toolkit / "install.sh")
        for name in [
            "01-foundation.sh",
            "02-claude-code.sh",
            "03-mcp-servers.sh",
            "04-hooks.sh",
            "05-verify.sh",
        ]:
            (self.toolkit / "scripts" / name).write_text(
                "#!/usr/bin/env bash\nexit 0\n"
            )
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.script(
            "uname",
            '#!/bin/sh\nif [ "${1:-}" = -m ]; then echo arm64; else echo Darwin; fi\n',
        )
        self.script(
            "git",
            """#!/usr/bin/env bash
set -eu
printf 'clone\\n' >> "$HOME/calls"
dest="${@: -1}"
mkdir -p "$dest"
cat > "$dest/install.sh" <<'INSTALL'
#!/usr/bin/env bash
set -eu
printf '%s\\n' "$*" >> "$HOME/installed-args"
INSTALL
chmod +x "$dest/install.sh"
""",
        )
        self.env = dict(
            os.environ,
            HOME=str(self.home),
            PATH=str(self.bin) + os.pathsep + os.environ["PATH"],
        )

    def script(self, name, content):
        path = self.bin / name
        path.write_text(content)
        path.chmod(0o755)

    def run_installer(self, *args):
        return subprocess.run(
            ["bash", str(self.toolkit / "install.sh"), *args],
            env=self.env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=15,
        )

    def no_install(self, *args):
        before = sorted(str(p.relative_to(self.home)) for p in self.home.rglob("*"))
        result = self.run_installer(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            before, sorted(str(p.relative_to(self.home)) for p in self.home.rglob("*"))
        )
        return result.stdout

    def real_verifier(self):
        shutil.copy2(
            SOURCE / "toolkit/scripts/05-verify.sh",
            self.toolkit / "scripts/05-verify.sh",
        )
        for name in ["brew", "docker", "gh", "claude"]:
            self.script(name, "#!/bin/sh\necho stub-version\n")
        self.script(
            "node",
            '#!/bin/sh\nif [ "${1:-}" = -e ]; then exec '
            + shlex.quote(shutil.which("node"))
            + ' "$@"; fi\necho stub-version\n',
        )
        for directory in ["hooks", "memory"]:
            (self.home / ".claude" / directory).mkdir(parents=True)
        (self.home / ".claude/settings.json").write_text(
            json.dumps(
                {
                    "hooks": {
                        "PreToolUse": [
                            {
                                "matcher": "Bash",
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": "python3 $HOME/.claude/hooks/commit-gate.py",
                                    }
                                ],
                            }
                        ]
                    }
                }
            )
        )
        (self.home / ".claude/hooks/commit-gate.py").write_text("# fixture hook")

    def test_real_verifier_reaches_optional_install(self):
        self.real_verifier()
        result = self.run_installer("--yes")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("11/11 passed", result.stdout)
        self.assertTrue((self.home / "installed-args").is_file())

    def test_literal_matchers_do_not_need_node_evaluation(self):
        self.real_verifier()
        self.script(
            "node",
            '#!/bin/sh\nif [ "${1:-}" = -e ]; then printf "called\\n" >> "$HOME/node-calls"; exit 97; fi\necho stub-version\n',
        )
        store = self.home / ".claude/settings.json"
        original = json.loads(store.read_text())
        for matcher, expected in (
            ("Bash", 0),
            ("Bash|Read", 0),
            ("*", 0),
            ("", 0),
            ("Read", 1),
        ):
            with self.subTest(matcher=matcher):
                original["hooks"]["PreToolUse"][0]["matcher"] = matcher
                store.write_text(json.dumps(original))
                result = self.run_installer("--skip-dev-protocol")
                self.assertEqual(
                    result.returncode, expected, result.stdout + result.stderr
                )
        self.assertFalse((self.home / "node-calls").exists())

    def test_regex_matcher_still_refuses_when_engine_is_unavailable(self):
        self.real_verifier()
        store = self.home / ".claude/settings.json"
        value = json.loads(store.read_text())
        value["hooks"]["PreToolUse"][0]["matcher"] = "^Bash$"
        store.write_text(json.dumps(value))
        for failure in ("exit 97", "exec python3 -c 'import time; time.sleep(10)'"):
            with self.subTest(failure=failure):
                self.script(
                    "node",
                    f'#!/bin/sh\nif [ "${{1:-}}" = -e ]; then {failure}; fi\necho stub-version\n',
                )
                result = self.run_installer("--skip-dev-protocol")
                self.assertEqual(result.returncode, 1)
                self.assertIn("10/11 passed", result.stdout)

    def test_verifier_regex_matcher_and_exact_invoked_script(self):
        self.real_verifier()
        store = self.home / ".claude/settings.json"
        for matcher, command, expected in (
            ("^Bash$", "python3 $HOME/.claude/hooks/commit-gate.py", 0),
            ("Bash|Read", "python3 $HOME/.claude/hooks/commit-gate.py", 0),
            ("Bash", "python3 ~/.claude/hooks/commit-gate.py", 0),
            ("Bash", f"python3 {self.home}/.claude/hooks/commit-gate.py", 0),
            ("Bash", 'python3 "$HOME/.claude/hooks/commit-gate.py"', 0),
            ("Bash", "python3 '$HOME/.claude/hooks/commit-gate.py'", 1),
            ("Read", "python3 $HOME/.claude/hooks/commit-gate.py", 1),
            ("[", "python3 $HOME/.claude/hooks/commit-gate.py", 1),
            ("Bash", "echo $HOME/.claude/hooks/commit-gate.py", 1),
            ("Bash", "python3 $HOME/.claude/hooks/commit-gate.py.bak", 1),
        ):
            with self.subTest(matcher=matcher, command=command):
                original = json.dumps(
                    {
                        "hooks": {
                            "PreToolUse": [
                                {
                                    "matcher": matcher,
                                    "hooks": [{"type": "command", "command": command}],
                                }
                            ]
                        }
                    }
                )
                store.write_text(original)
                result = self.run_installer("--skip-dev-protocol")
                self.assertEqual(
                    result.returncode, expected, result.stdout + result.stderr
                )
                self.assertEqual(store.read_text(), original)

    def test_real_verifier_counts_all_failures(self):
        self.real_verifier()
        (self.home / ".claude/settings.json").unlink()
        result = self.run_installer("--yes")
        self.assertEqual(result.returncode, 1)
        self.assertIn("9/11 passed", result.stdout)
        self.assertFalse((self.home / "installed-args").exists())

    def test_missing_hook_registration_is_not_healthy(self):
        self.real_verifier()
        (self.home / ".claude/settings.json").write_text("{}")
        result = self.run_installer("--yes")
        self.assertEqual(result.returncode, 1)
        self.assertIn("10/11 passed", result.stdout)
        self.assertFalse((self.home / "installed-args").exists())

    def test_closed_stdin_skips(self):
        self.assertIn("No terminal to ask on. Skipping", self.no_install())

    def test_explicit_skip(self):
        self.assertIn(
            "Skipped (--skip-dev-protocol)", self.no_install("--skip-dev-protocol")
        )

    def test_skip_overrides_yes(self):
        self.assertIn(
            "Skipped (--skip-dev-protocol)",
            self.no_install("--yes", "--skip-dev-protocol"),
        )

    def test_dry_run(self):
        self.assertIn("would ask:", self.no_install("--dry-run"))

    def test_dry_yes_claude(self):
        self.assertIn("--target claude --yes", self.no_install("--dry-run", "--yes"))

    def test_dry_yes_both(self):
        (self.home / ".agents").mkdir()
        self.assertIn("--target both --yes", self.no_install("--dry-run", "--yes"))

    def test_dry_skip(self):
        self.assertIn(
            "Skipped (--skip-dev-protocol)",
            self.no_install("--dry-run", "--skip-dev-protocol"),
        )

    def test_yes_default_claude(self):
        result = self.run_installer("--yes")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            (self.home / "installed-args").read_text(), "--target claude --yes\n"
        )
        self.assertEqual((self.home / "calls").read_text(), "clone\n")

    def test_yes_existing_agents_both(self):
        (self.home / ".agents").mkdir()
        result = self.run_installer("--yes")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            (self.home / "installed-args").read_text(), "--target both --yes\n"
        )
        self.assertEqual((self.home / "calls").read_text(), "clone\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
