"""Offline regressions for shipped stdin hooks and credential transport."""

import importlib.util
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from urllib.error import URLError


ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "toolkit/env/hooks"
COMMIT_HOOKS = [HOOKS / "commit-gate.py", ROOT / "toolkit/configs/commit-gate.py"]


class DestructiveHookTests(unittest.TestCase):
    def decision(self, command):
        run = subprocess.run(
            ["bash", str(HOOKS / "block-destructive.sh")],
            input=json.dumps({"tool_input": {"command": command}}),
            text=True,
            capture_output=True,
            check=True,
        )
        return (
            json.loads(run.stdout)["hookSpecificOutput"]["permissionDecision"]
            if run.stdout
            else "allow"
        )

    def test_force_push_forms_are_denied_without_running_git(self):
        for command in (
            "git push -f origin main",
            "git push origin main -f",
            "git -c push.default=current push --force origin main",
            "git push --force-with-lease origin refs/heads/main",
            "git push --force-with-lease origin HEAD:main",
            "git push --force-with-lease origin",
            "git push --force origin feature",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), "deny")

    def test_safe_push_forms_remain_allowed(self):
        for command in (
            "git push origin main",
            "git push --force-with-lease origin feature",
            "git push origin feature --force-with-lease",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), "allow")


class CommitGateTests(unittest.TestCase):
    def test_both_shipped_copies_are_identical(self):
        self.assertEqual(COMMIT_HOOKS[0].read_bytes(), COMMIT_HOOKS[1].read_bytes())

    def run_hook(self, hook, command, result=None, error=None, with_tsconfig=True):
        with tempfile.TemporaryDirectory(prefix="gravity-hook-") as directory:
            root = Path(directory)
            if with_tsconfig:
                (root / "tsconfig.json").write_text("{}")
            payload = {"cwd": str(root), "tool_input": {"command": command}}
            fake = mock.Mock(
                return_value=result or subprocess.CompletedProcess([], 0, "", "")
            )
            if error is not None:
                fake.side_effect = error
            with (
                mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                mock.patch("subprocess.run", fake),
                mock.patch.dict(os.environ, {}, clear=False),
            ):
                try:
                    runpy.run_path(str(hook), run_name="__main__")
                except SystemExit as exc:
                    code = exc.code
                else:
                    code = 0
            return code, fake.call_count

    def test_noncommit_and_clean_check_allow(self):
        for hook in COMMIT_HOOKS:
            self.assertEqual(self.run_hook(hook, "git status")[0], 0)
            self.assertEqual(self.run_hook(hook, "git -C . commit -m test")[0], 0)

    def test_failed_check_blocks_regardless_of_output_channel(self):
        for hook in COMMIT_HOOKS:
            for stdout, stderr in (
                ("error TS1000", ""),
                ("", "failed"),
                (".next/dev/types stale", ""),
            ):
                with self.subTest(hook=hook, stdout=stdout, stderr=stderr):
                    result = subprocess.CompletedProcess([], 1, stdout, stderr)
                    self.assertEqual(
                        self.run_hook(hook, "git -C . commit -m test", result)[0],
                        2,
                    )

    def test_timeout_and_missing_tool_block(self):
        for hook in COMMIT_HOOKS:
            for error in (
                subprocess.TimeoutExpired(["npx"], 60),
                FileNotFoundError("npx"),
            ):
                with self.subTest(hook=hook, error=type(error).__name__):
                    self.assertEqual(
                        self.run_hook(hook, "git commit -m test", error=error)[0], 2
                    )


class GroqTransportTests(unittest.TestCase):
    def test_request_keeps_dummy_key_and_prompt_out_of_argv(self):
        spec = importlib.util.spec_from_file_location(
            "gravity_groq_test", HOOKS / "groq_client.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        body = {"choices": [{"message": {"content": '{"ok": true}'}}]}
        reply = io.BytesIO(json.dumps(body).encode())
        with (
            mock.patch.object(module, "_load_api_key", return_value="AUDIT_DUMMY_KEY"),
            mock.patch.object(
                subprocess, "run", side_effect=AssertionError("argv transport")
            ),
            mock.patch.object(module, "urlopen", return_value=reply) as fetch,
        ):
            self.assertEqual(module.call_groq("AUDIT_DUMMY_PROMPT"), {"ok": True})
        request = fetch.call_args.args[0]
        self.assertIn("AUDIT_DUMMY_KEY", request.get_header("Authorization"))
        self.assertIn("AUDIT_DUMMY_PROMPT", request.data.decode())

    def test_network_error_log_omits_secret_and_prompt(self):
        spec = importlib.util.spec_from_file_location(
            "gravity_groq_error_test", HOOKS / "groq_client.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with (
            mock.patch.object(module, "_load_api_key", return_value="AUDIT_DUMMY_KEY"),
            mock.patch.object(
                module,
                "urlopen",
                side_effect=URLError("AUDIT_DUMMY_KEY AUDIT_DUMMY_PROMPT"),
            ),
            mock.patch.object(module, "log_failure") as log,
        ):
            self.assertIsNone(module.call_groq("AUDIT_DUMMY_PROMPT"))
        reason = log.call_args.args[0]
        self.assertNotIn("AUDIT_DUMMY_KEY", reason)
        self.assertNotIn("AUDIT_DUMMY_PROMPT", reason)


class CarlLegacyPolicyTests(unittest.TestCase):
    def test_legacy_model_policy_does_not_load_for_current_sessions(self):
        spec = importlib.util.spec_from_file_location(
            "gravity_carl", HOOKS / "carl-hook.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        domains, exclusions, _ = module.parse_manifest(
            ROOT / "toolkit/env/carl/manifest"
        )
        loaded = [
            name
            for name, config in domains.items()
            if config.get("state") and (config.get("always_on") or name == "GLOBAL")
        ]
        self.assertIn("GLOBAL", loaded)
        self.assertNotIn("OPUS-4-7", loaded)
        self.assertFalse(domains["OPUS-4-7"]["state"])


if __name__ == "__main__":
    unittest.main()
