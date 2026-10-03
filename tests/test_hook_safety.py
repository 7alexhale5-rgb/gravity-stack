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
    def test_backtick_wrapped_push_is_not_a_literal_git_command(self):
        for command in (
            "echo `git push --force origin main`",
            "`git push --force origin main`",
            'echo "`git push --force origin main`"',
        ):
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), "deny")

    def test_dwim_protected_branch_deletion_is_denied(self):
        for command in (
            "git push origin :heads/main",
            "git push origin --delete heads/master",
            "git push origin :refs/main",
            "git push origin --delete refs/master",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), "deny")

    def test_pruning_cannot_delete_unknown_or_protected_remote_refs(self):
        for command in (
            "git push --prune origin 'refs/heads/*:refs/heads/*'",
            "git push origin --prune",
            "git push --prune origin feature:refs/heads/feature",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), "deny")

    def test_quoted_shell_wrappers_cannot_hide_git_push(self):
        for command in (
            "bash -c 'git push --force origin main'",
            "bash -lc 'git --no-pager push --force origin main'",
            "eval 'git push --force origin main'",
            "printf '%s' 'git push --force origin main' | bash",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), "deny")

    def test_ansi_quoted_push_wrapper_is_not_a_literal_git_command(self):
        self.assertEqual(
            self.decision("bash -c $'git push --force origin main'"), "deny"
        )

    def test_protected_branch_deletion_is_denied(self):
        for command in (
            "git push origin --delete main",
            "git push origin -d master",
            "git push origin :main",
            "git push origin :refs/heads/master",
            "git push origin --delete refs/heads/main",
            "git push origin --delete HEAD",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), "deny")
        self.assertEqual(self.decision("git push origin --delete feature"), "allow")

    def test_redirections_cannot_hide_force_flags_or_protected_refspecs(self):
        for command in (
            "git push origin main >push.log --force",
            "git push origin main 2>push.log -f",
            "git push origin main >>push.log --force",
            "git push origin main >&2 --force",
            "git >push.log push origin main --force",
            "git push --force-with-lease origin feature:refs/heads/feature >push.log feature:refs/heads/main",
            "git push origin feature >push.log +HEAD:refs/heads/main",
            "git push origin main <input.txt --force",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), "deny")

    def test_inline_git_configuration_cannot_hide_push_effects(self):
        for option in (
            "-c remote.origin.mirror=true",
            "-cremote.origin.mirror=true",
            "-c remote.origin.push=+feature:refs/heads/main",
            "--config-env remote.origin.mirror=FIXTURE",
            "--config-env=remote.origin.push=FIXTURE",
        ):
            with self.subTest(option=option):
                self.assertEqual(self.decision(f"git {option} push origin"), "deny")

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
    def test_backtick_wrapped_commit_cannot_hide_compilation_gate(self):
        for hook in COMMIT_HOOKS:
            for command in (
                "`git commit -m x`",
                "echo `git commit -m x`",
                'echo "`git commit -m x`"',
            ):
                with self.subTest(hook=hook, command=command):
                    self.assertEqual(self.run_hook(hook, command), (2, 0))

    def test_commit_from_docs_checks_typescript_ancestor_inside_worktree(self):
        for hook in COMMIT_HOOKS:
            with self.subTest(hook=hook), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                subprocess.run(["git", "init", "-q", str(root)], check=True)
                (root / "tsconfig.json").write_text("{}")
                (root / "docs").mkdir()
                payload = {
                    "cwd": str(root),
                    "tool_input": {"command": "cd docs && git commit -m test"},
                }
                with (
                    mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                    mock.patch(
                        "subprocess.run",
                        return_value=subprocess.CompletedProcess(
                            [], 1, "failing root types", ""
                        ),
                    ) as compiler,
                    mock.patch.object(sys, "stderr", io.StringIO()),
                ):
                    with self.assertRaises(SystemExit) as exit:
                        runpy.run_path(str(hook), run_name="__main__")
                self.assertEqual(exit.exception.code, 2)
                self.assertEqual(
                    [call.kwargs["cwd"] for call in compiler.call_args_list],
                    [str(root)],
                )

    def test_typescript_ancestor_lookup_does_not_leave_nested_worktree(self):
        for hook in COMMIT_HOOKS:
            with self.subTest(hook=hook), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                (root / "tsconfig.json").write_text("{}")
                repo = root / "nested"
                subprocess.run(["git", "init", "-q", str(repo)], check=True)
                (repo / "docs").mkdir()
                payload = {
                    "cwd": str(repo),
                    "tool_input": {"command": "cd docs && git commit -m test"},
                }
                with (
                    mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                    mock.patch("subprocess.run") as compiler,
                ):
                    with self.assertRaises(SystemExit) as exit:
                        runpy.run_path(str(hook), run_name="__main__")
                self.assertEqual(exit.exception.code, 0)
                compiler.assert_not_called()

    def test_multiple_distinct_commit_targets_refuse_before_any_compiler(self):
        for hook in COMMIT_HOOKS:
            with self.subTest(hook=hook), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                for name in ("first", "second"):
                    (root / name).mkdir()
                    (root / name / "tsconfig.json").write_text("{}")
                payload = {
                    "cwd": str(root),
                    "tool_input": {
                        "command": "git -C first commit -m one && git -C second commit -m two"
                    },
                }
                with (
                    mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                    mock.patch(
                        "subprocess.run",
                        return_value=subprocess.CompletedProcess([], 0, "", ""),
                    ) as compiler,
                    mock.patch.object(sys, "stderr", io.StringIO()),
                ):
                    with self.assertRaises(SystemExit) as exit:
                        runpy.run_path(str(hook), run_name="__main__")
                self.assertEqual(exit.exception.code, 2)
                compiler.assert_not_called()
            self.assertEqual(
                self.run_hook(hook, "git commit -m one && git -C . commit -m two"),
                (0, 1),
            )

    def test_quoted_shell_wrappers_cannot_hide_compilation_gate(self):
        for hook in COMMIT_HOOKS:
            for command in (
                "bash -c 'git commit -m x'",
                "bash -lc 'git -C . commit -m x'",
                "eval 'git commit -m x'",
                "printf '%s' 'git commit -m x' | bash",
            ):
                with self.subTest(hook=hook, command=command):
                    self.assertEqual(self.run_hook(hook, command), (2, 0))

    def test_ansi_quoted_commit_wrapper_is_not_a_literal_git_command(self):
        for hook in COMMIT_HOOKS:
            self.assertEqual(self.run_hook(hook, "bash -c $'git commit -m x'"), (2, 0))

    def test_conditionally_skipped_cd_cannot_bypass_root_compilation(self):
        for hook in COMMIT_HOOKS:
            for command in (
                "false && cd docs; git commit -m test",
                "false && cd docs\ngit commit -m test",
                "false &&\ncd docs; git commit -m test",
            ):
                with (
                    self.subTest(hook=hook, command=command),
                    tempfile.TemporaryDirectory() as tmp,
                ):
                    root = Path(tmp)
                    (root / "tsconfig.json").write_text("{}")
                    (root / "docs").mkdir()
                    payload = {"cwd": str(root), "tool_input": {"command": command}}
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
                    self.assertEqual(
                        exit.exception.code,
                        2,
                        "ambiguous skipped cd must not allow a root commit",
                    )
                    # A conservative refusal may avoid compilation entirely; if run,
                    # only the original TypeScript root is a safe check target.
                    self.assertTrue(
                        all(
                            call.kwargs["cwd"] == str(root.resolve())
                            for call in compiler.call_args_list
                        )
                    )

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

    def test_three_tokenizer_copies_have_matching_behavior(self):
        import re
        import shlex

        sources = [hook.read_text() for hook in COMMIT_HOOKS]
        sources.append(
            (HOOKS / "block-destructive.sh")
            .read_text()
            .split("python3 -c '\n", 1)[1]
            .rsplit("'", 1)[0]
        )
        tokenizers = []
        for source in sources:
            functions = [
                node
                for node in ast.parse(source).body
                if isinstance(node, ast.FunctionDef)
                and node.name
                in {"shell_continuations", "git_executable", "shell_tokens"}
            ]
            namespace = {"Path": Path, "shlex": shlex, "re": re}
            exec(
                compile(
                    ast.Module(body=functions, type_ignores=[]),
                    "tokenizer-parity",
                    "exec",
                ),
                namespace,
            )
            tokenizers.append(namespace["shell_tokens"])
        for command in (
            "git status &&\ncd docs; git commit -m test",
            "git push origin main >push.log --force",
            "git push origin main 2>&1 --force",
            "git -C ';' status",
            r"git -C \; status",
            "bash -c 'git commit -m test'",
            "git status # comment\ntrue",
            "git \\\nstatus",
            "echo `git push origin main`",
            "`git commit -m x`",
            'echo "`git commit -m x`"',
            "echo 'literal `date`'",
            r"echo \`date\`",
        ):
            with self.subTest(command=command):
                outputs = []
                for tokenizer in tokenizers:
                    try:
                        outputs.append(tokenizer(command))
                    except ValueError as error:
                        outputs.append(("error", str(error)))
                self.assertEqual(outputs[0], outputs[1])
                self.assertEqual(outputs[0], outputs[2])
                if command.startswith("echo 'literal") or command.startswith(
                    r"echo \`"
                ):
                    self.assertNotEqual(outputs[0][0], "error")

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
                    expected = [] if form == "multiple" else [str(site)]
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
