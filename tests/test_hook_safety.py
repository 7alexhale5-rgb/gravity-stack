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
    def test_quoted_git_inside_executable_backticks_refuses(self):
        self.assertEqual(self.decision('echo `"git" push --force origin main`'), "deny")
        self.assertEqual(
            self.decision(r'echo \`"git" push --force origin main\`'), "allow"
        )

    def test_leading_redirections_cannot_hide_shell_programs(self):
        for command in (
            ">/dev/null bash -c 'git push --force origin main'",
            "2>/dev/null bash -c 'git push --force origin main'",
        ):
            self.assertEqual(self.decision(command), "deny")

    def test_unsupported_shell_control_structures_refuse(self):
        for command in (
            "if true; then bash -c 'git push --force origin main'; fi",
            "while true; do bash -c 'git push --force origin main'; done",
            "if false; then echo safe; else bash -c 'git push --force origin main'; fi",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), "deny")

    def test_negated_or_quoted_shell_programs_cannot_hide_pushes(self):
        for command in (
            "! bash -c 'git push --force origin main'",
            "time bash -c '\"git\" push --force origin main'",
            "bash -c '\"git\" push --force origin main'",
            "command bash -lc '$PROGRAM'",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), "deny")

    def test_builtin_shell_programs_refuse_but_wrapped_print_data_is_safe(self):
        for command in (
            "builtin eval 'git push --force origin main'",
            "command builtin eval 'git push --force origin main'",
            "builtin command -p eval 'git push --force origin main'",
            "builtin source hidden-push.sh",
            "command builtin . hidden-push.sh",
            "builtin eval '$PROGRAM'",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), "deny")
        for command in (
            "builtin printf '%s' 'git push --force origin main'",
            "command printf '%s' 'git push --force origin main'",
            "command -p printf '%s' 'git push --force origin main'",
            "builtin command printf '%s' 'git push --force origin main'",
            "command rg 'git push' docs/",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), "allow")

    def test_arithmetic_shifts_are_data_but_command_substitutions_are_guarded(self):
        for command in (
            "echo $((1 << 2))",
            "echo $((8 >> 1))",
            "echo $((1 << (2 + 1)))",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), "allow")
        self.assertEqual(
            self.decision("echo $((1 << $(git push --force origin main)))"), "deny"
        )

    def test_push_expansions_refuse_but_literal_dollar_refs_remain_data(self):
        for command in (
            "PUSH_FLAGS=--force; git push origin $PUSH_FLAGS main",
            'git push origin "$PUSH_FLAGS" main',
            "git $SUBCOMMAND origin main",
            "git push origin feature:*",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), "deny")
        for command in ("git push origin '$literal'", r"git push origin \$literal"):
            self.assertEqual(self.decision(command), "allow")

    def test_here_strings_preserve_data_and_refuse_executable_substitutions(self):
        for command in (
            'cat <<< "hello"',
            "cat <<< 'git push'",
            'cat <<< "hello"; git status',
        ):
            self.assertEqual(self.decision(command), "allow")
        for command in (
            'cat <<< "$(git push --force origin main)"',
            "bash <<< 'git push --force origin main'",
            'cat <<< "hello"; git push --force origin main',
        ):
            self.assertEqual(self.decision(command), "deny")

    def test_quoted_git_push_patterns_and_literal_heredocs_are_data(self):
        for command in (
            "rg 'git push' docs/",
            "rg '|' bash 'git push' docs/",
            "printf '%s' 'git push --force origin main'",
            "cat <<'EOF'\nDon't forget git push --force origin main\nEOF",
            "cat <<EOF\nDon't forget\nEOF",
            "cat <<-'EOF'\n\tDon't forget\n\tEOF",
            "cat <<'EOF' # note <<FAKE\nDon't forget\nEOF",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), "allow")
        for command in (
            "cat <<'EOF'\nDon't forget\nEOF\ngit push --force origin main",
            "bash <<'EOF'\ngit push --force origin main\nEOF",
            "cat <<'EOF' | bash\ngit push --force origin main\nEOF",
            "cat <<EOF\n$(git push --force origin main)\nEOF",
            "env -i bash <<'EOF'\ngit push --force origin main\nEOF",
            'echo "$(git push --force origin main)"',
            "$(cat <<'EOF'\ngit\nEOF\n) push --force origin main",
            "cat <<'EOF' >script.sh\ngit push --force origin main\nEOF\nbash script.sh",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), "deny")

    def test_git_environment_configuration_cannot_hide_mirror_push(self):
        for command in (
            "GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=remote.origin.mirror GIT_CONFIG_VALUE_0=true git push origin",
            "env GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=remote.origin.mirror GIT_CONFIG_VALUE_0=true git push origin",
            "export GIT_CONFIG_COUNT=1; git push origin",
            "source push-config.sh; git push origin",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), "deny")
        with mock.patch.dict(
            os.environ,
            {
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "remote.origin.mirror",
                "GIT_CONFIG_VALUE_0": "true",
            },
        ):
            self.assertEqual(self.decision("git push origin"), "deny")

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
    def test_quoted_git_inside_executable_backticks_refuses(self):
        for hook in COMMIT_HOOKS:
            self.assertEqual(self.run_hook(hook, 'echo `"git" commit -am x`'), (2, 0))
            self.assertEqual(
                self.run_hook(hook, r'echo \`"git" commit -am x\`'), (0, 0)
            )

    def test_glob_cd_does_not_compile_literal_pattern_directory(self):
        for hook in COMMIT_HOOKS:
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                for name in ("[ab]", "a"):
                    directory = root / name
                    directory.mkdir()
                    (directory / "tsconfig.json").write_text("{}")
                for command, expected_calls in (
                    ("cd [ab] && git commit -am x", 0),
                    ("cd '[ab]' && git commit -am x", 1),
                ):
                    payload = {"cwd": str(root), "tool_input": {"command": command}}
                    with (
                        mock.patch.object(
                            sys, "stdin", io.StringIO(json.dumps(payload))
                        ),
                        mock.patch(
                            "subprocess.run",
                            return_value=subprocess.CompletedProcess(
                                [], 1, "failure", ""
                            ),
                        ) as compiler,
                        mock.patch.object(sys, "stderr", io.StringIO()),
                    ):
                        with self.assertRaises(SystemExit) as result:
                            runpy.run_path(str(hook), run_name="__main__")
                    self.assertEqual(result.exception.code, 2)
                    self.assertEqual(compiler.call_count, expected_calls)

    def test_prefixed_commits_and_redirected_shells_refuse(self):
        for hook in COMMIT_HOOKS:
            for command in (
                "time git commit -m test",
                "! git commit -m test",
                ">/dev/null bash -c 'git commit -m test'",
                "2>/dev/null bash -c 'git commit -m test'",
            ):
                with self.subTest(hook=hook, command=command):
                    self.assertEqual(self.run_hook(hook, command), (2, 0))

    def test_unsupported_controls_and_negated_directory_changes_refuse(self):
        for hook in COMMIT_HOOKS:
            for command in (
                "if true; then bash -c 'git commit -m test'; fi",
                "while true; do bash -c 'git commit -m test'; done",
                "if false; then echo safe; else bash -c 'git commit -m test'; fi",
                "! cd ../broken; git commit -am test",
                "time cd ../broken; git commit -am test",
            ):
                with self.subTest(hook=hook, command=command):
                    self.assertEqual(self.run_hook(hook, command), (2, 0))

    def test_negated_or_quoted_shell_programs_cannot_hide_commits(self):
        for hook in COMMIT_HOOKS:
            for command in (
                "! bash -c 'git commit -m x'",
                "time bash -c '\"git\" commit -m x'",
                "bash -c '\"git\" commit -m x'",
                "command bash -lc '$PROGRAM'",
            ):
                with self.subTest(hook=hook, command=command):
                    self.assertEqual(self.run_hook(hook, command), (2, 0))

    def test_builtin_shell_programs_refuse_but_wrapped_print_data_is_safe(self):
        for hook in COMMIT_HOOKS:
            for command in (
                "builtin eval 'git commit -m x'",
                "command builtin eval 'git commit -m x'",
                "builtin command -p eval 'git commit -m x'",
                "builtin source hidden-commit.sh",
                "command builtin . hidden-commit.sh",
                "builtin eval '$PROGRAM'",
            ):
                with self.subTest(hook=hook, command=command):
                    self.assertEqual(self.run_hook(hook, command), (2, 0))
            for command in (
                "builtin printf '%s' 'git commit -m x'",
                "command printf '%s' 'git commit -m x'",
                "command -p printf '%s' 'git commit -m x'",
                "builtin command printf '%s' 'git commit -m x'",
                "command rg 'git commit' docs/",
            ):
                with self.subTest(hook=hook, command=command):
                    self.assertEqual(self.run_hook(hook, command), (0, 0))

    def test_environment_mutating_builtins_cannot_compile_wrong_repository(self):
        for hook in COMMIT_HOOKS:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                clean, broken = root / "clean", root / "broken"
                for repo in (clean, broken):
                    repo.mkdir()
                    (repo / ".git").mkdir()
                    (repo / "tsconfig.json").write_text("{}")
                for mutation in (
                    "declare -x",
                    "typeset -x",
                    "export",
                    "readonly",
                    "builtin declare -x",
                    "command builtin typeset -x",
                    "builtin command -p readonly",
                    "set -a;",
                    "builtin set -a;",
                ):
                    with self.subTest(hook=hook, mutation=mutation):
                        command = f"{mutation} GIT_DIR={broken}/.git GIT_WORK_TREE={broken}; git commit -m x"
                        payload = {
                            "cwd": str(clean),
                            "tool_input": {"command": command},
                        }

                        def compile_types(*args, **kwargs):
                            return subprocess.CompletedProcess(
                                [],
                                0 if Path(kwargs["cwd"]) == clean else 1,
                                "fixture",
                                "",
                            )

                        with (
                            mock.patch.object(
                                sys, "stdin", io.StringIO(json.dumps(payload))
                            ),
                            mock.patch(
                                "subprocess.run", side_effect=compile_types
                            ) as compiler,
                            mock.patch.object(sys, "stderr", io.StringIO()),
                        ):
                            with self.assertRaises(SystemExit) as exit:
                                runpy.run_path(str(hook), run_name="__main__")
                        self.assertEqual(exit.exception.code, 2)
                        compiler.assert_not_called()

    def test_unresolved_git_subcommands_and_executables_refuse(self):
        for hook in COMMIT_HOOKS:
            for command in (
                'subcommand=commit; git "$subcommand" -m test',
                "git $SUBCOMMAND -m test",
                'git "$FLAGS" commit -m test',
                '"$GIT" commit -m test',
            ):
                with self.subTest(hook=hook, command=command):
                    self.assertEqual(self.run_hook(hook, command), (2, 0))
            for command in ("git '$literal' -m test", r"git \$literal -m test"):
                with self.subTest(hook=hook, command=command):
                    self.assertEqual(self.run_hook(hook, command), (0, 0))

    def test_assignment_prefixed_home_cd_cannot_compile_the_wrong_repo(self):
        for hook in COMMIT_HOOKS:
            self.assertEqual(
                self.run_hook(hook, "HOME=/tmp printf cd; git commit -m x"), (0, 1)
            )
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                clean, broken = root / "clean", root / "broken"
                for repo in (clean, broken):
                    repo.mkdir()
                    (repo / ".git").mkdir()
                    (repo / "tsconfig.json").write_text("{}")
                payload = {
                    "cwd": str(clean),
                    "tool_input": {
                        "command": f"HOME={broken} cd && git commit -m test"
                    },
                }

                def compile_types(*args, **kwargs):
                    return subprocess.CompletedProcess(
                        [], 0 if Path(kwargs["cwd"]) == clean else 1, "fixture", ""
                    )

                with (
                    mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                    mock.patch("subprocess.run", side_effect=compile_types) as compiler,
                    mock.patch.object(sys, "stderr", io.StringIO()),
                ):
                    with self.assertRaises(SystemExit) as exit:
                        runpy.run_path(str(hook), run_name="__main__")
                self.assertEqual(exit.exception.code, 2)
                compiler.assert_not_called()

    def test_arithmetic_shifts_do_not_block_unrelated_commands(self):
        for hook in COMMIT_HOOKS:
            for command in (
                "echo $((1 << 2))",
                "echo $((8 >> 1))",
                "echo $((1 << (2 + 1)))",
            ):
                with self.subTest(hook=hook, command=command):
                    self.assertEqual(self.run_hook(hook, command), (0, 0))
            self.assertEqual(
                self.run_hook(hook, "echo $((1 << $(git commit -m x)))"), (2, 0)
            )

    def test_wrapped_cd_and_cdpath_cannot_change_unchecked_worktree(self):
        for hook in COMMIT_HOOKS:
            for command in (
                "builtin cd /tmp; git commit -m x",
                "command cd /tmp; git commit -m x",
                "CDPATH=/tmp; cd .; git commit -m x",
            ):
                self.assertEqual(self.run_hook(hook, command), (2, 0))
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "docs").mkdir()
                payload = {
                    "cwd": str(root),
                    "tool_input": {"command": "cd docs && git commit -m x"},
                }
                with (
                    mock.patch.dict(os.environ, {"CDPATH": "/tmp"}),
                    mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                    mock.patch("subprocess.run") as compiler,
                    mock.patch.object(sys, "stderr", io.StringIO()),
                ):
                    with self.assertRaises(SystemExit) as exit:
                        runpy.run_path(str(hook), run_name="__main__")
                self.assertEqual(exit.exception.code, 2)
                compiler.assert_not_called()

    def test_included_git_configuration_refuses_even_explicit_worktree(self):
        for hook in COMMIT_HOOKS:
            for command in (
                "git -c include.path=/tmp/worktree.conf commit -m x",
                "git -cinclude.path=/tmp/worktree.conf --work-tree=. commit -m x",
                "git -c core.worktree=site --work-tree=. commit -m x",
            ):
                self.assertEqual(self.run_hook(hook, command), (2, 0))

    def test_here_strings_are_data_unless_they_execute_git(self):
        for hook in COMMIT_HOOKS:
            for command in (
                'cat <<< "hello"',
                "cat <<< 'git commit'",
                'cat <<< "hello"; git status',
            ):
                self.assertEqual(self.run_hook(hook, command), (0, 0))
            for command in (
                'cat <<< "$(git commit -m x)"',
                "bash <<< 'git commit -m x'",
                'cat <<< "hello"; git commit -m x',
            ):
                self.assertEqual(self.run_hook(hook, command), (2, 0))

    def test_quoted_git_commit_patterns_and_literal_heredocs_are_data(self):
        for hook in COMMIT_HOOKS:
            for command in (
                "rg 'git commit' docs/",
                "printf '%s' 'git commit -m x'",
                "cat <<'EOF'\nDon't forget git commit -m x\nEOF",
                "cat <<EOF\nDon't forget\nEOF",
                "cat <<'A' <<'B'\nDon't forget\nA\ngit commit\nB",
            ):
                with self.subTest(hook=hook, command=command):
                    self.assertEqual(self.run_hook(hook, command), (0, 0))
            for command in (
                "cat <<'EOF'\nDon't forget\nEOF\ngit commit -m x",
                "bash <<'EOF'\ngit commit -m x\nEOF",
                "cat <<'EOF' | bash\ngit commit -m x\nEOF",
                "cat <<EOF\n$(git commit -m x)\nEOF",
            ):
                with self.subTest(hook=hook, command=command):
                    self.assertEqual(self.run_hook(hook, command), (2, 0))

    def test_raw_git_c_expansions_are_rejected_before_normalization(self):
        for hook in COMMIT_HOOKS:
            for command in (
                'git -C "$DEST/.." commit -m test',
                'git -C"$DEST/.." commit -m test',
                "git -C '$DEST/..' commit -m test",
                "git -C '~/..' commit -m test",
            ):
                with self.subTest(hook=hook, command=command):
                    self.assertEqual(self.run_hook(hook, command), (2, 0))

    def test_failed_cd_and_inherited_git_environment_are_not_trusted(self):
        for hook in COMMIT_HOOKS:
            for command in (
                "cd missing; cd ..; git commit -m test",
                "git commit -m test",
            ):
                with (
                    self.subTest(hook=hook, command=command),
                    tempfile.TemporaryDirectory() as td,
                ):
                    root = Path(td)
                    (root / ".git").mkdir()
                    (root / "tsconfig.json").write_text("{}")
                    nested = root / "nested"
                    nested.mkdir()
                    (nested / ".git").mkdir()
                    payload = {"cwd": str(nested), "tool_input": {"command": command}}
                    config = (
                        {"GIT_DIR": str(root / ".git"), "GIT_WORK_TREE": str(root)}
                        if command == "git commit -m test"
                        else {}
                    )
                    with (
                        mock.patch.dict(os.environ, config),
                        mock.patch("sys.stdin", io.StringIO(json.dumps(payload))),
                        mock.patch("subprocess.run") as run,
                    ):
                        with self.assertRaises(SystemExit) as exit_result:
                            runpy.run_path(str(hook), run_name="__main__")
                        self.assertEqual(exit_result.exception.code, 2)
                        run.assert_not_called()

    def test_git_redirection_before_commit_cannot_skip_compilation(self):
        for hook in COMMIT_HOOKS:
            for command in (
                "git 2>/dev/null commit -m test",
                "git -C . 2>/dev/null commit -m test",
                "git 2>/dev/null -C . commit -m test",
                "git commit -m test >commit.log",
            ):
                with self.subTest(hook=hook, command=command):
                    self.assertEqual(self.run_hook(hook, command), (2, 0))

    def test_symlink_cd_then_logical_parent_cannot_skip_compilation(self):
        for hook in COMMIT_HOOKS:
            with self.subTest(hook=hook), tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp).resolve()
                repo, outside = base / "repo", base / "outside"
                repo.mkdir()
                (outside / "child").mkdir(parents=True)
                (repo / "tsconfig.json").write_text("{}")
                (repo / "link").symlink_to(outside / "child", target_is_directory=True)
                payload = {
                    "cwd": str(repo),
                    "tool_input": {"command": "cd link; cd ..; git commit -m test"},
                }
                with (
                    mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                    mock.patch("subprocess.run") as compiler,
                    mock.patch.object(sys, "stderr", io.StringIO()),
                ):
                    with self.assertRaises(SystemExit) as exit:
                        runpy.run_path(str(hook), run_name="__main__")
                self.assertEqual(exit.exception.code, 2)
                compiler.assert_not_called()

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
            "! bash -c 'git push --force origin main'",
            "! bash -c 'git commit -m x'",
            "time bash -c '\"git\" push --force origin main'",
            "time bash -c '\"git\" commit -m x'",
            "bash -c '\"git\" push --force origin main'",
            "bash -c '\"git\" commit -m x'",
            "command bash -lc '$PROGRAM'",
            "builtin eval 'git push --force origin main'",
            "command builtin eval 'git commit -m x'",
            "builtin command -p eval 'git commit -m x'",
            "builtin source script.sh",
            "command builtin . script.sh",
            "builtin printf '%s' 'git commit -m x'",
            "command -p printf '%s' 'git push --force origin main'",
            "echo $((1 << 2))",
            "echo $((8 >> 1))",
            "echo $((1 << (2 + 1)))",
            "echo $((1 << $(git commit -m x)))",
            "echo $((1 << $(git push --force origin main)))",
            'subcommand=commit; git "$subcommand" -m test',
            'cat <<< "hello"',
            "cat <<< 'git push'",
            'cat <<< "$(git commit -m x)"',
            'git push origin "$PUSH_FLAGS" main',
            "git push origin '$literal'",
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
                if outputs[0][0] != "error":
                    expansion_flags = [
                        [getattr(word, "expanded", False) for word, _ in output]
                        for output in outputs
                    ]
                    self.assertEqual(expansion_flags[0], expansion_flags[1])
                    self.assertEqual(expansion_flags[0], expansion_flags[2])
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
    def test_real_slow_drip_response_stops_at_overall_deadline(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        import threading
        import time

        spec = importlib.util.spec_from_file_location(
            "gravity_groq_drip", HOOKS / "groq_client.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        class Drip(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length", "0")))
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                try:
                    for byte in b'{"choices":[{"message":{"content":"{}"}}]}':
                        self.wfile.write(bytes([byte]))
                        self.wfile.flush()
                        time.sleep(0.025)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Drip)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with (
                mock.patch.object(
                    module, "_load_api_key", return_value="AUDIT_DUMMY_KEY"
                ),
                mock.patch.object(
                    module, "API_URL", f"http://127.0.0.1:{server.server_port}/"
                ),
                mock.patch.object(module, "log_failure"),
            ):
                started = time.monotonic()
                self.assertIsNone(module.call_groq("LOCAL_DUMMY_PROMPT", timeout=0.15))
                self.assertLess(time.monotonic() - started, 0.8)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1)

    def test_entire_transport_has_a_deadline_without_secret_argv(self):
        spec = importlib.util.spec_from_file_location(
            "gravity_groq_deadline", HOOKS / "groq_client.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        body = {"choices": [{"message": {"content": '{"ok": true}'}}]}
        with (
            mock.patch.object(module, "_load_api_key", return_value="AUDIT_DUMMY_KEY"),
            mock.patch(
                "subprocess.run", side_effect=subprocess.TimeoutExpired(["curl"], 0.01)
            ) as run,
            mock.patch.object(module, "log_failure"),
        ):
            self.assertIsNone(module.call_groq("AUDIT_DUMMY_PROMPT", timeout=0.01))
        self.assertLessEqual(run.call_args.kwargs["timeout"], 0.01)
        self.assertNotIn("AUDIT_DUMMY_KEY", str(run.call_args.args))
        self.assertNotIn("AUDIT_DUMMY_PROMPT", str(run.call_args.args))
        self.assertIn("AUDIT_DUMMY_KEY", run.call_args.kwargs["input"])

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
                subprocess,
                "run",
                return_value=subprocess.CompletedProcess(
                    ["curl"], 0, json.dumps(body), ""
                ),
            ) as fetch,
        ):
            self.assertEqual(module.call_groq("AUDIT_DUMMY_PROMPT"), {"ok": True})
        self.assertNotIn("AUDIT_DUMMY_KEY", str(fetch.call_args.args))
        self.assertNotIn("AUDIT_DUMMY_PROMPT", str(fetch.call_args.args))
        self.assertIn("AUDIT_DUMMY_KEY", fetch.call_args.kwargs["input"])
        self.assertIn("AUDIT_DUMMY_PROMPT", fetch.call_args.kwargs["input"])

    def test_network_error_log_omits_secret_and_prompt(self):
        spec = importlib.util.spec_from_file_location(
            "gravity_groq_error_test", HOOKS / "groq_client.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with (
            mock.patch.object(module, "_load_api_key", return_value="AUDIT_DUMMY_KEY"),
            mock.patch.object(
                subprocess,
                "run",
                side_effect=OSError("AUDIT_DUMMY_KEY AUDIT_DUMMY_PROMPT"),
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
