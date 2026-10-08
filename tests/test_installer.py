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
from unittest import mock

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
    def test_relative_profile_memory_path_survives_changed_cwd(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = root / "profile"
            profile.mkdir()
            binary = root / "bin"
            binary.mkdir()
            stub = binary / "claude"
            stub.write_text("""#!/usr/bin/env python3
import json,os,sys
from pathlib import Path
store=Path(os.environ['CLAUDE_CONFIG_DIR'])/'.claude.json'
name=sys.argv[sys.argv.index('--scope')+2]
data=json.loads(store.read_text()) if store.exists() else {'mcpServers':{}}
entry={'command':'fixture'}
if '--env' in sys.argv:
    key,value=sys.argv[sys.argv.index('--env')+1].split('=',1)
    entry['env']={key:value}
data['mcpServers'][name]=entry
store.write_text(json.dumps(data))
""")
            stub.chmod(0o755)
            env = dict(
                os.environ,
                HOME=str(root),
                CLAUDE_CONFIG_DIR="./profile",
                PATH=str(binary) + os.pathsep + os.environ["PATH"],
            )
            result = subprocess.run(
                ["bash", str(SOURCE / "toolkit/scripts/03-mcp-servers.sh")],
                cwd=root,
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            store = profile / ".claude.json"
            before = store.read_bytes()
            path = json.loads(before)["mcpServers"]["memory"]["env"]["MEMORY_FILE_PATH"]
            self.assertEqual(path, str(profile.resolve() / "memory/graph.json"))
            elsewhere = root / "other-project"
            elsewhere.mkdir()
            env["CLAUDE_CONFIG_DIR"] = str(profile.resolve())
            again = subprocess.run(
                ["bash", str(SOURCE / "toolkit/scripts/03-mcp-servers.sh")],
                cwd=elsewhere,
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(again.returncode, 0, again.stderr)
            self.assertEqual(store.read_bytes(), before)
            for invalid_path in ("./memory/graph.json", 17):
                existing = json.loads(before)
                existing["mcpServers"]["memory"]["env"]["MEMORY_FILE_PATH"] = (
                    invalid_path
                )
                store.write_text(json.dumps(existing))
                invalid_bytes = store.read_bytes()
                rejected = subprocess.run(
                    ["bash", str(SOURCE / "toolkit/scripts/03-mcp-servers.sh")],
                    cwd=elsewhere,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertNotEqual(rejected.returncode, 0)
                self.assertEqual(store.read_bytes(), invalid_bytes)
                self.assertIn("memory (preserved)", rejected.stderr)

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
    def test_review37_baseline_ignores_inherited_profile(self):
        unrelated = self.root / "unrelated-profile"
        unrelated.mkdir()
        unrelated_settings = unrelated / "settings.json"
        unrelated_settings.write_text('{"private_fixture": "unchanged"}\n')
        before = unrelated_settings.read_bytes()
        with mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(unrelated)}):
            fixture = PhaseSix("test_real_verifier_reaches_optional_install")
            fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.real_verifier()
        result = fixture.run_installer("--skip-dev-protocol")
        with self.subTest(case="fixture-environment"):
            self.assertTrue("CLAUDE_CONFIG_DIR" not in fixture.env, "baseline fixture inherited a custom profile")
        with self.subTest(case="owned-baseline"):
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        (fixture.home / ".claude/settings.json").unlink()
        missing = fixture.run_installer("--skip-dev-protocol")
        with self.subTest(case="owned-settings-required"):
            self.assertEqual(missing.returncode, 1, missing.stdout + missing.stderr)
        self.assertEqual(unrelated_settings.read_bytes(), before)

    def test_review36_preserved_unsafe_home_requires_quoted_expansion(self):
        self.home = self.root / "Alex Hale"
        self.home.mkdir()
        self.env["HOME"] = str(self.home)
        self.real_verifier()
        store = self.home / ".claude/settings.json"
        baseline = json.loads(store.read_text())
        for spelling, expected in (
            ("$HOME", 1),
            ("${HOME}", 1),
            ('"$HOME/.claude/hooks/commit-gate.py"', 0),
            ('"${HOME}/.claude/hooks/commit-gate.py"', 0),
        ):
            settings = json.loads(json.dumps(baseline))
            command = "python3 " + (
                spelling
                if spelling.startswith('"')
                else spelling + "/.claude/hooks/commit-gate.py"
            )
            settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"] = command
            original = json.dumps(settings)
            store.write_text(original)
            result = self.run_installer("--skip-dev-protocol")
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
            self.assertEqual(store.read_text(), original)

    def test_review35_handler_interpreter_must_match_verified_runtime(self):
        self.real_verifier()
        self.script("python", "#!/bin/sh\nprintf 'Python 2.7.18\\n'\nexit 1\n")
        store = self.home / ".claude/settings.json"
        baseline = json.loads(store.read_text())
        absolute = str(self.home / ".claude/hooks/commit-gate.py")
        for argv_form in (False, True):
            settings = json.loads(json.dumps(baseline))
            handler = settings["hooks"]["PreToolUse"][0]["hooks"][0]
            handler["command"] = (
                "python" if argv_form else "python " + shlex.quote(absolute)
            )
            if argv_form:
                handler["args"] = [absolute]
            original = json.dumps(settings)
            store.write_text(original)
            result = self.run_installer("--skip-dev-protocol")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertEqual(store.read_text(), original)

    def test_review33_literal_dollar_profile_shell_spelling(self):
        self.real_verifier()
        profile = self.root / "$PROFILE"
        shutil.copytree(self.home / ".claude", profile)
        self.env["CLAUDE_CONFIG_DIR"] = str(profile)
        store = profile / "settings.json"
        for quoted, expected in ((False, 1), (True, 0)):
            settings = json.loads(store.read_text())
            absolute = str(profile / "hooks/commit-gate.py")
            spelling = shlex.quote(absolute) if quoted else '"' + absolute + '"'
            settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"] = (
                "python3 " + spelling
            )
            original = json.dumps(settings)
            store.write_text(original)
            result = self.run_installer("--skip-dev-protocol")
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
            self.assertEqual(store.read_text(), original)

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
        self.env.pop("CLAUDE_CONFIG_DIR", None)

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
                                        "timeout": 70,
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

    def test_selected_profile_cannot_borrow_default_gate(self):
        self.real_verifier()
        profile = self.root / "selected profile"
        (profile / "hooks").mkdir(parents=True)
        (profile / "memory").mkdir()
        (profile / "settings.json").write_text("{}")
        self.env["CLAUDE_CONFIG_DIR"] = str(profile)
        result = self.run_installer("--skip-dev-protocol")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Commit gate file and registration", result.stdout)

    def test_profile_setup_and_verification_share_root(self):
        self.real_verifier()
        for script in ["02-claude-code.sh", "04-hooks.sh"]:
            shutil.copy2(
                SOURCE / "toolkit/scripts" / script, self.toolkit / "scripts" / script
            )
        shutil.copytree(SOURCE / "toolkit/configs", self.toolkit / "configs")
        profile = self.root / "selected profile's config"
        self.env["CLAUDE_CONFIG_DIR"] = str(profile)
        default = self.home / ".claude/settings.json"
        before = default.read_bytes()
        for _ in range(2):
            result = self.run_installer("--skip-dev-protocol")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((profile / "hooks/commit-gate.py").is_file())
            self.assertTrue((profile / "memory").is_dir())
            self.assertEqual(default.read_bytes(), before)
            settings = json.loads((profile / "settings.json").read_text())
            command = settings["hooks"]["PreToolUse"][1]["hooks"][0]["command"]
            self.assertEqual(
                shlex.split(command),
                ["python3", str(profile.resolve() / "hooks/commit-gate.py")],
            )
            (profile / "current-session.jsonl").write_text("active profile proof\n")
            backup_command = settings["hooks"]["PreCompact"][0]["hooks"][0]["command"]
            copied = subprocess.run(
                ["bash", "-c", backup_command],
                env=self.env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(copied.returncode, 0, copied.stderr)
            backups = list((profile / "backups").glob("session-*.jsonl"))
            self.assertTrue(backups)
            self.assertEqual(backups[-1].read_text(), "active profile proof\n")
            self.assertFalse((self.home / ".claude/backups").exists())

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
            ("Bash,Read", "python3 $HOME/.claude/hooks/commit-gate.py", 1),
            ("Bash ", "python3 $HOME/.claude/hooks/commit-gate.py", 1),
            ("Bash|Read", "python3 $HOME/.claude/hooks/commit-gate.py", 0),
            ("Bash", "python3 ~/.claude/hooks/commit-gate.py", 0),
            ("Bash", f"python3 {self.home}/.claude/hooks/commit-gate.py", 0),
            ("Bash", 'python3 "$HOME/.claude/hooks/commit-gate.py"', 0),
            ("Bash", "python3 '$HOME/.claude/hooks/commit-gate.py'", 1),
            ("Read", "python3 $HOME/.claude/hooks/commit-gate.py", 1),
            ("[", "python3 $HOME/.claude/hooks/commit-gate.py", 1),
            ("Bash", "echo $HOME/.claude/hooks/commit-gate.py", 1),
            ("Bash", "python3 $HOME/.claude/hooks/commit-gate.py.bak", 1),
            ("Bash", "python3 $HOME/.claude/hooks/commit-gate.py || true", 1),
            ("Bash", "python3 $HOME/.claude/hooks/commit-gate.py &", 1),
            ("Bash", "python3 $HOME/.claude/hooks/commit-gate.py; true", 1),
            ("Bash", "/missing/python3 $HOME/.claude/hooks/commit-gate.py", 1),
            ("Bash", "python3.999 $HOME/.claude/hooks/commit-gate.py", 1),
        ):
            with self.subTest(matcher=matcher, command=command):
                original = json.dumps(
                    {
                        "hooks": {
                            "PreToolUse": [
                                {
                                    "matcher": matcher,
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": command,
                                            "timeout": 70,
                                        }
                                    ],
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

    def test_hookstate32_disabled_or_async_gate_is_not_verified(self):
        self.real_verifier()
        store = self.home / ".claude/settings.json"
        baseline = json.loads(store.read_text())
        for field, value, expected in (
            ("disableAllHooks", True, 1),
            ("disableAllHooks", False, 0),
            ("async", True, 1),
            ("async", False, 0),
            ("async", "false", 1),
            ("asyncRewake", True, 1),
        ):
            with self.subTest(field=field, value=value):
                current = json.loads(json.dumps(baseline))
                target = (
                    current
                    if field == "disableAllHooks"
                    else current["hooks"]["PreToolUse"][0]["hooks"][0]
                )
                target[field] = value
                original = json.dumps(current)
                store.write_text(original)
                result = self.run_installer("--skip-dev-protocol")
                self.assertEqual(
                    result.returncode, expected, result.stdout + result.stderr
                )
                self.assertEqual(store.read_text(), original)

    def test_hookstate32_current_handler_fields_match_actual_invocation(self):
        self.real_verifier()
        store = self.home / ".claude/settings.json"
        baseline = json.loads(store.read_text())
        absolute = str(self.home / ".claude/hooks/commit-gate.py")
        for fields, expected in (
            ({"args": []}, 1),
            ({"if": "Bash(npm *)"}, 1),
            ({"shell": "powershell"}, 1),
            ({"command": "python3", "args": [absolute]}, 0),
            ({"command": "python3", "args": ["-u", absolute]}, 0),
            ({"command": "python3", "args": [absolute + ".bak"]}, 1),
            ({"command": "python3", "args": [absolute, "ignored"]}, 1),
        ):
            with self.subTest(fields=fields):
                current = json.loads(json.dumps(baseline))
                current["hooks"]["PreToolUse"][0]["hooks"][0].update(fields)
                original = json.dumps(current)
                store.write_text(original)
                result = self.run_installer("--skip-dev-protocol")
                self.assertEqual(
                    result.returncode, expected, result.stdout + result.stderr
                )
                self.assertEqual(store.read_text(), original)

    def test_commit_gate_timeout_exceeds_compiler_timeout(self):
        self.real_verifier()
        store = self.home / ".claude/settings.json"
        value = json.loads(store.read_text())
        hook = value["hooks"]["PreToolUse"][0]["hooks"][0]
        for timeout, expected in (
            (61, 1),
            (63, 1),
            (69, 1),
            (None, 1),
            (0, 1),
            (60, 1),
            ("70", 1),
            (True, 1),
            (70, 0),
        ):
            with self.subTest(timeout=timeout):
                hook.pop("timeout", None)
                if timeout is not None:
                    hook["timeout"] = timeout
                store.write_text(json.dumps(value))
                result = self.run_installer("--skip-dev-protocol")
                self.assertEqual(
                    result.returncode, expected, result.stdout + result.stderr
                )

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
