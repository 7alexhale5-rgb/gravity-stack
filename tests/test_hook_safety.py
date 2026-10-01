"""Offline regressions for shipped stdin hooks and credential transport."""

import ast
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
    def test_push_option_value_is_not_a_force_flag(self):
        for option in ("-oflag", "-o flag", "--push-option=flag", "--push-option flag"):
            with self.subTest(option=option):
                self.assertEqual(
                    self.decision(f"git push {option} origin main"), "allow"
                )
                self.assertEqual(
                    self.decision(
                        f"git push {option} --force-with-lease origin feature:refs/heads/feature"
                    ),
                    "allow",
                )
        for flag in ("-f", "-vf"):
            self.assertEqual(self.decision(f"git push {flag} origin main"), "deny")

    def test_lease_push_cannot_add_implicit_destination_options(self):
        self.assertEqual(self.decision("git push --tags origin"), "allow")
        for option in ("--tags", "--follow-tags", "--prune", "--delete", "-d"):
            with self.subTest(option=option):
                self.assertEqual(
                    self.decision(
                        "git push --force-with-lease=refs/tags/v1:abc123 "
                        f"{option} origin feature:refs/heads/feature"
                    ),
                    "deny",
                )

    def test_literal_punctuation_cannot_hide_push_arguments(self):
        for value in ("';'", '";"', r"\;", "'&&'", r"\&\&", "'\n'"):
            with self.subTest(value=value):
                self.assertEqual(
                    self.decision(f"git -C {value} push --force origin main"), "deny"
                )
                self.assertEqual(
                    self.decision(f"git -C {value} push origin main"), "allow"
                )
        for separator in (";", "\n", "&&"):
            self.assertEqual(
                self.decision(f"git status{separator}git push --force origin main"),
                "deny",
            )

    def test_lease_requires_supported_options_and_explicit_destination(self):
        for command in (
            "git push --force-with-l origin main",
            "git push --for origin main",
            "git push --force-with-lease --repo=origin origin",
            "git push --force-with-lease --repo origin origin",
            "git push --force-with-lease origin feature",
            "git push --force-with-lease origin feature:main",
            "git push --force-with-lease origin feature:refs/heads/main",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), "deny")
        self.assertEqual(
            self.decision(
                "git push --force-with-lease origin feature:refs/heads/feature"
            ),
            "allow",
        )

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
            "git push origin +HEAD:main",
            "git push --mirror origin",
            "git push --force-with-lease origin +main",
            "git --no-pager push --force origin main",
            "git --config-env=push.default=FIXTURE push --force origin main",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), "deny")

    def test_safe_push_forms_remain_allowed(self):
        for command in (
            "git push origin main",
            "git --no-pager push origin main",
            "git --no-pager push --force-with-lease origin feature:refs/heads/feature",
            "git push --force-with-lease origin feature:refs/heads/feature",
            "git push origin feature:refs/heads/feature --force-with-lease",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), "allow")

    def test_absolute_and_continued_pushes_are_denied(self):
        for command in (
            "/usr/bin/git push --force origin main",
            "/opt/homebrew/bin/git --no-pager push --force origin main",
            "git \\\npush --force origin main",
            "git \\\n  push --force origin main",
            "git push --force-with-lease origin\ntrue",
            "git push --force-with-lease origin # inspect\ntrue",
            "git push --force-with-lease origin\ngit status",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), "deny")
        self.assertEqual(
            self.decision(
                "git push --force-with-lease origin feature:refs/heads/feature\ntrue"
            ),
            "allow",
        )

    def test_literal_hashes_do_not_hide_guarded_commands(self):
        for value in ("#", "'#'", '"#"', "\\#"):
            with self.subTest(value=value):
                self.assertEqual(
                    self.decision(
                        f"git -c core.commentChar={value} push --force origin main"
                    ),
                    "deny",
                )

    def test_push_option_values_do_not_supply_fake_refspecs(self):
        for option in (
            "-o ci.skip",
            "--push-option ci.skip",
            "--push-option=ci.skip",
            "-oci.skip",
        ):
            for placement in (f"{option} origin", f"origin {option}"):
                with self.subTest(option=option, placement=placement):
                    self.assertEqual(
                        self.decision(f"git push --force-with-lease {placement}"),
                        "deny",
                    )
                    self.assertEqual(
                        self.decision(
                            f"git push --force-with-lease {placement} feature:refs/heads/feature"
                        ),
                        "allow",
                    )
        self.assertEqual(
            self.decision("git push --force-with-lease --unknown value origin"), "deny"
        )

    def test_global_git_options_cannot_skip_push_inspection(self):
        for option in ("-P", "-p", "--no-advice", "--future-global"):
            with self.subTest(option=option):
                self.assertEqual(
                    self.decision(f"git {option} push --force origin main"), "deny"
                )
        for option in ("-P", "-p", "--no-advice"):
            self.assertEqual(self.decision(f"git {option} push origin main"), "allow")


class CommitGateTests(unittest.TestCase):
    def test_quoted_punctuation_directory_still_runs_compilation(self):
        for hook in COMMIT_HOOKS:
            for name, token in ((";", "';'"), (";", r"\;"), ("&&", "'&&'")):
                with (
                    self.subTest(hook=hook, token=token),
                    tempfile.TemporaryDirectory() as tmp,
                ):
                    root = Path(tmp).resolve()
                    target = root / name
                    target.mkdir()
                    (target / "tsconfig.json").write_text("{}")
                    payload = {
                        "cwd": str(root),
                        "tool_input": {"command": f"git -C {token} commit -m test"},
                    }
                    with (
                        mock.patch.object(
                            sys, "stdin", io.StringIO(json.dumps(payload))
                        ),
                        mock.patch(
                            "subprocess.run",
                            return_value=subprocess.CompletedProcess(
                                [], 1, "failed", ""
                            ),
                        ) as compiler,
                        mock.patch.object(sys, "stderr", io.StringIO()),
                    ):
                        with self.assertRaises(SystemExit) as exit:
                            runpy.run_path(str(hook), run_name="__main__")
                    self.assertEqual(exit.exception.code, 2)
                    self.assertEqual(
                        [call.kwargs["cwd"] for call in compiler.call_args_list],
                        [str(target)],
                    )

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

    def test_literal_commit_targets_use_actual_working_directories(self):
        for hook in COMMIT_HOOKS:
            for form in (
                "cd",
                "worktree",
                "worktree-split",
                "multiple",
                "newline",
                "comment",
                "cd-comment",
                "and-newline",
                "semicolon-newline",
            ):
                with (
                    self.subTest(hook=hook, form=form),
                    tempfile.TemporaryDirectory() as tmp,
                ):
                    root = Path(tmp).resolve()
                    site = root / "site"
                    site.mkdir()
                    (site / "tsconfig.json").write_text("{}")
                    second = root / "second"
                    second.mkdir()
                    (second / "tsconfig.json").write_text("{}")
                    command = {
                        "cd": "cd site && git commit -m test",
                        "worktree": f"git --work-tree={site} commit -m test",
                        "worktree-split": f"git --work-tree {site} commit -m test",
                        "newline": "cd site\ngit commit -m test",
                        "comment": "git status # inspect\ngit -C site commit -m test",
                        "cd-comment": "cd site # enter project\ngit commit -m test",
                        "and-newline": "cd site &&\ngit commit -m test",
                        "semicolon-newline": "cd site;\ngit commit -m test",
                        "multiple": "git -C site commit -m one && git -C second commit -m two",
                    }[form]
                    payload = {"cwd": str(root), "tool_input": {"command": command}}
                    failure = subprocess.CompletedProcess([], 1, "failed fixture", "")
                    results = (
                        [subprocess.CompletedProcess([], 0, "", ""), failure]
                        if form == "multiple"
                        else [failure]
                    )
                    with (
                        mock.patch.object(
                            sys, "stdin", io.StringIO(json.dumps(payload))
                        ),
                        mock.patch("subprocess.run", side_effect=results) as compiler,
                        mock.patch.object(sys, "stderr", io.StringIO()),
                    ):
                        with self.assertRaises(SystemExit) as exit:
                            runpy.run_path(str(hook), run_name="__main__")
                    self.assertEqual(exit.exception.code, 2)
                    expected = (
                        [str(site), str(second)] if form == "multiple" else [str(site)]
                    )
                    self.assertEqual(
                        [call.kwargs["cwd"] for call in compiler.call_args_list],
                        expected,
                    )

    def test_unsupported_commit_contexts_refuse_before_compilation(self):
        for hook in COMMIT_HOOKS:
            for command in (
                "git commit -m test | cat",
                "git commit -m test &",
                "GIT_WORK_TREE=site git commit -m test",
                "git -c core.worktree=site commit -m test",
                "git --config-env=core.worktree=FIXTURE commit -m test",
            ):
                with self.subTest(hook=hook, command=command):
                    code, calls = self.run_hook(hook, command)
                    self.assertEqual(code, 2)
                    self.assertEqual(calls, 0)

    def test_noncommit_and_clean_check_allow(self):
        for hook in COMMIT_HOOKS:
            self.assertEqual(self.run_hook(hook, "git status")[0], 0)
            self.assertEqual(self.run_hook(hook, "git -C . commit -m test")[0], 0)

    def test_absolute_and_continued_commits_run_compilation(self):
        failure = subprocess.CompletedProcess([], 1, "fixture failure", "")
        for hook in COMMIT_HOOKS:
            for command in (
                "/usr/bin/git commit -m test",
                "/opt/homebrew/bin/git -C . commit -m test",
                "git \\\ncommit -m test",
                "git \\\n  commit -m test",
            ):
                with self.subTest(hook=hook, command=command):
                    self.assertEqual(self.run_hook(hook, command, failure), (2, 1))

    def test_literal_hashes_do_not_hide_compilation(self):
        failure = subprocess.CompletedProcess([], 1, "fixture failure", "")
        for hook in COMMIT_HOOKS:
            for value in ("#", "'#'", '"#"', "\\#"):
                with self.subTest(hook=hook, value=value):
                    self.assertEqual(
                        self.run_hook(
                            hook,
                            f"git -c core.commentChar={value} commit -m test",
                            failure,
                        ),
                        (2, 1),
                    )

    def test_continuations_preserve_shell_literal_content(self):
        sources = [hook.read_text() for hook in COMMIT_HOOKS]
        sources.append(
            (HOOKS / "block-destructive.sh")
            .read_text()
            .split("python3 -c '\n", 1)[1]
            .rsplit("'", 1)[0]
        )
        cases = (
            ("git \\\ncommit", "git commit"),
            ('git -C "si\\\nte" commit', 'git -C "site" commit'),
            ("git -C 'si\\\nte' commit", "git -C 'si\\\nte' commit"),
            (
                "git status # inspect\\\n git commit",
                "git status \n git commit",
            ),
            ("git status \\\\\ngit commit", "git status \\\\\ngit commit"),
        )
        for source in sources:
            function = next(
                node
                for node in ast.parse(source).body
                if isinstance(node, ast.FunctionDef)
                and node.name == "shell_continuations"
            )
            namespace = {}
            exec(
                compile(
                    ast.Module(body=[function], type_ignores=[]),
                    "hook-continuations",
                    "exec",
                ),
                namespace,
            )
            for command, expected in cases:
                with self.subTest(command=command):
                    self.assertEqual(
                        namespace["shell_continuations"](command), expected
                    )

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
