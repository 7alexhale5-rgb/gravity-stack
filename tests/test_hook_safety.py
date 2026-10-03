"""Offline regressions for shipped stdin hooks and credential transport."""

import ast
import importlib.util
import io
import json
import os
from pathlib import Path
import runpy
import shlex
import shutil
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
    def test_function_keyword_cannot_hide_protected_push_body(self):
        for declaration in (
            "function ship { git push --force origin main; }; ship",
            "function ship() { git push --force origin main; }; ship",
        ):
            self.assertEqual(self.decision(declaration), "deny")
        self.assertEqual(
            self.decision(
                "function greet { printf '%s' 'git push --force origin main'; }; greet"
            ),
            "allow",
        )

    def test_unresolved_global_operand_cannot_expand_into_push(self):
        for option in ("-C", "-c", "--git-dir", "--work-tree"):
            self.assertEqual(self.decision("git " + option + " $ARGS"), "deny")
        self.assertEqual(self.decision("git -C '$ARGS'"), "allow")

    def test_missing_option_operands_cannot_swallow_guarded_commands(self):
        for prefix in ("git -C", "git -c", "env -u", "exec -a"):
            for boundary in (" || ", "; ", "\n"):
                with self.subTest(prefix=prefix, boundary=boundary):
                    self.assertEqual(
                        self.decision(
                            prefix + boundary + "git push --force origin main"
                        ),
                        "deny",
                    )

    def test_relative_git_and_wrapped_expanded_environment_are_guarded(self):
        for executable in ("bin/git", "./bin/git", "../tools/git"):
            self.assertEqual(
                self.decision(executable + " push --force origin main"), "deny"
            )
        for wrapper in ("builtin", "command builtin", "builtin command"):
            command = (
                "cfg=GIT_CONFIG_COUNT; " + wrapper + ' export "$cfg=1"; '
                "cfg=GIT_CONFIG_KEY_0; "
                + wrapper
                + ' export "$cfg=remote.origin.mirror"; '
                "cfg=GIT_CONFIG_VALUE_0; "
                + wrapper
                + ' export "$cfg=true"; git push origin'
            )
            self.assertEqual(self.decision(command), "deny")
        self.assertEqual(
            self.decision("printf '%s' 'builtin export $cfg=1'; git push origin main"),
            "allow",
        )

    def test_general_non_git_substitutions_and_conditionals_are_allowed(self):
        for command in ('echo "$(date)"', "if test -f package.json; then npm test; fi"):
            with self.subTest(command=command):
                self.assertEqual(self.decision(command), "allow")

    def test_wrapper_option_operands_cannot_hide_executables(self):
        for prefix in (
            "env -u GRAVITY_UNUSED",
            "env --unset GRAVITY_UNUSED",
            "/usr/bin/env -u GRAVITY_UNUSED",
            "exec -a diagnostic-name",
        ):
            self.assertEqual(
                self.decision(prefix + " bash -c '\"git\" push --force origin main'"),
                "deny",
            )

    def test_shell_input_channels_with_quoted_git_refuse(self):
        for command in (
            "bash <<< '\"git\" push --force origin main'",
            "printf '%s' '\"git\" push --force origin main' |& bash",
            "printf '%s' '\"git\" push --force origin main' | bash",
            "bash <(printf '%s' '\"git\" push --force origin main')",
        ):
            self.assertEqual(self.decision(command), "deny")

    def test_multiline_pipeline_and_expanded_executable_refuse(self):
        for pipe in ("|", "|&"):
            for gap in ("\n", "\n\n"):
                self.assertEqual(
                    self.decision(
                        "printf '%s' '\"git\" push --force origin main' "
                        + pipe
                        + gap
                        + "bash"
                    ),
                    "deny",
                )
        self.assertEqual(self.decision("$'git' push --force origin main"), "deny")
        self.assertEqual(self.decision("printf '%s' '$git'"), "allow")

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
    def test_actual_inline_git_aliases_cannot_hide_guarded_operations(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root / "repo"
            repo.mkdir()
            real_git = shutil.which("git")
            fake = root / "fake-git"
            log = root / "calls"
            fake.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$FAKE_GIT_LOG"\n')
            fake.chmod(0o755)
            subprocess.run(
                [real_git, "init", str(repo)], check=True, capture_output=True
            )
            subprocess.run(
                [real_git, "-C", str(repo), "config", "user.name", "Fixture"],
                check=True,
            )
            subprocess.run(
                [
                    real_git,
                    "-C",
                    str(repo),
                    "config",
                    "user.email",
                    "fixture@example.invalid",
                ],
                check=True,
            )
            env = dict(os.environ, FAKE_GIT_LOG=str(log))
            for attached in (False, True):
                for wrapper in ("", "command "):
                    value = "alias.ship=!" + str(fake) + " push --force origin main"
                    args = (["-c" + value] if attached else ["-c", value]) + ["ship"]
                    log.write_text("")
                    executed = subprocess.run(
                        [real_git, "-C", str(repo)] + args,
                        env=env,
                        capture_output=True,
                        timeout=3,
                    )
                    if attached:
                        # Git rejects attached -c; parser coverage remains conservative.
                        self.assertNotEqual(executed.returncode, 0)
                        self.assertEqual(log.read_text(), "")
                    else:
                        self.assertEqual(executed.returncode, 0, executed.stderr)
                        self.assertIn("push --force origin main", log.read_text())
                    command = wrapper + shlex.join(["git"] + args)
                    with self.subTest(command=command):
                        self.assertEqual(
                            DestructiveHookTests().decision(command), "deny"
                        )
                (repo / "change.txt").write_text(str(attached))
                subprocess.run([real_git, "-C", str(repo), "add", "."], check=True)
                value = "alias.save=commit"
                args = (["-c" + value] if attached else ["-c", value]) + [
                    "save",
                    "-m",
                    "Fixture alias commit",
                ]
                executed = subprocess.run(
                    [real_git, "-C", str(repo)] + args, capture_output=True, timeout=3
                )
                if attached:
                    self.assertNotEqual(executed.returncode, 0)
                else:
                    self.assertEqual(executed.returncode, 0, executed.stderr)
                command = shlex.join(["git"] + args)
                with self.subTest(command=command):
                    for hook in COMMIT_HOOKS:
                        self.assertEqual(self.run_hook(hook, command), (2, 0))

    def test_conditional_existence_array_indices_are_guarded(self):
        for operation in ("commit -am broken", "push --force origin main"):
            prefix = "a=(0); expression='a[$(git " + operation + "; printf 0)]'; "
            for tail in (
                "[[ -v 'a[expression]' ]]",
                "[[ -R 'a[expression]' ]]",
                "test -v 'a[expression]'",
                "[ -v 'a[expression]' ]",
                "builtin test -v 'a[expression]'",
                "command [ -v 'a[expression]' ]",
            ):
                command = prefix + tail
                with self.subTest(command=command):
                    if operation.startswith("commit"):
                        for hook in COMMIT_HOOKS:
                            self.assertEqual(self.run_hook(hook, command), (2, 0))
                    else:
                        self.assertEqual(
                            DestructiveHookTests().decision(command), "deny"
                        )

    def test_actual_bash4_conditional_existence_executes_fake_git(self):
        candidates = [
            os.environ.get("GRAVITY_TEST_BASH4"),
            shutil.which("bash"),
            "/opt/homebrew/bin/bash",
            "/usr/local/bin/bash",
            "/opt/local/bin/bash",
        ]
        bash4 = None
        for candidate in candidates:
            if candidate and Path(candidate).is_file():
                version = subprocess.run(
                    [candidate, "--version"], capture_output=True, text=True, timeout=3
                ).stdout
                if any(
                    "version " + str(major) + "." in version for major in range(4, 10)
                ):
                    bash4 = candidate
                    break
        if not bash4:
            self.skipTest(
                "Bash4+ unavailable locally: array-existence runtime proof deferred; parser assertions still run"
            )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake = root / "git"
            log = root / "calls"
            fake.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$FAKE_GIT_LOG"\n')
            fake.chmod(0o755)
            env = dict(
                os.environ,
                PATH=str(root) + os.pathsep + os.environ["PATH"],
                FAKE_GIT_LOG=str(log),
            )
            for operation in ("commit -am broken", "push --force origin main"):
                prefix = "a=(0); expression='a[$(git " + operation + "; printf 0)]'; "
                for tail in (
                    "[[ -v 'a[expression]' ]]",
                    "test -v 'a[expression]'",
                    "[ -v 'a[expression]' ]",
                    "builtin test -v 'a[expression]'",
                ):
                    command = prefix + tail
                    log.write_text("")
                    subprocess.run(
                        [bash4, "-c", command], env=env, capture_output=True, timeout=3
                    )
                    self.assertIn(operation, log.read_text(), command)

    def test_literal_conditional_lookups_and_comment_config_remain_allowed(self):
        for command in (
            "[[ -v 'a[0]' ]]",
            "test -v 'a[0]'",
            "builtin [ -v name ]",
            "[[ -R name ]]",
            "git -c core.commentChar='#' status",
            "git -ccore.commentChar=';' status",
            "echo '[[ -v a[expression] ]]'",
        ):
            for hook in COMMIT_HOOKS:
                self.assertEqual(self.run_hook(hook, command), (0, 0), command)
            self.assertEqual(DestructiveHookTests().decision(command), "allow", command)

    def test_actual_read_arithmetic_destinations_are_guarded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            log = root / "calls"
            fake = root / "git"
            fake.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$FAKE_GIT_LOG"\n')
            fake.chmod(0o755)
            env = dict(
                os.environ,
                PATH=str(root) + os.pathsep + os.environ["PATH"],
                FAKE_GIT_LOG=str(log),
            )
            for operation in ("commit -am broken", "push --force origin main"):
                for wrapper in ("", "builtin ", "command ", "command builtin "):
                    for indirect in (False, True):
                        expression = "a[$(git " + operation + "; printf 0)]"
                        prefix = "a=(0); expression='" + expression + "'; "
                        target = "a[expression]" if indirect else expression
                        command = prefix + wrapper + "read '" + target + "' <<< value"
                        log.write_text("")
                        subprocess.run(
                            ["bash", "-c", command],
                            env=env,
                            capture_output=True,
                            timeout=3,
                        )
                        self.assertIn(operation, log.read_text(), command)
                        with self.subTest(command=command):
                            if operation.startswith("commit"):
                                for hook in COMMIT_HOOKS:
                                    self.assertEqual(
                                        self.run_hook(hook, command), (2, 0)
                                    )
                            else:
                                self.assertEqual(
                                    DestructiveHookTests().decision(command), "deny"
                                )

    def test_mapfile_callbacks_are_refused_by_every_guard(self):
        for name in ("mapfile", "readarray"):
            for wrapper in ("", "builtin ", "command "):
                for operation in ("commit -am broken", "push --force origin main"):
                    for option in ("-C ", "-C", "-tC"):
                        command = (
                            wrapper
                            + name
                            + " -c 1 "
                            + option
                            + "'git "
                            + operation
                            + "; #' <<< line"
                        )
                        with self.subTest(command=command):
                            if operation.startswith("commit"):
                                for hook in COMMIT_HOOKS:
                                    self.assertEqual(
                                        self.run_hook(hook, command), (2, 0)
                                    )
                            else:
                                self.assertEqual(
                                    DestructiveHookTests().decision(command), "deny"
                                )

    def test_actual_bash4_mapfile_callbacks_execute_fake_git(self):
        candidates = [
            os.environ.get("GRAVITY_TEST_BASH4"),
            shutil.which("bash"),
            "/opt/homebrew/bin/bash",
            "/usr/local/bin/bash",
        ]
        bash4 = None
        for candidate in candidates:
            if candidate and Path(candidate).is_file():
                version = subprocess.run(
                    [candidate, "--version"], capture_output=True, text=True, timeout=3
                ).stdout
                if any(
                    "version " + str(major) + "." in version for major in range(4, 10)
                ):
                    bash4 = candidate
                    break
        if not bash4:
            self.skipTest(
                "Bash >=4 unavailable: callback parser checks run; actual mapfile/readarray execution remains a runtime gap"
            )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            log = root / "calls"
            fake = root / "git"
            fake.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$FAKE_GIT_LOG"\n')
            fake.chmod(0o755)
            env = dict(
                os.environ,
                PATH=str(root) + os.pathsep + os.environ["PATH"],
                FAKE_GIT_LOG=str(log),
            )
            for name in ("mapfile", "readarray"):
                for wrapper in ("", "builtin ", "command "):
                    for operation in ("commit -am broken", "push --force origin main"):
                        for option in ("-C ", "-C", "-tC"):
                            command = (
                                wrapper
                                + name
                                + " -c 1 "
                                + option
                                + "'git "
                                + operation
                                + "; #' <<< line"
                            )
                            log.write_text("")
                            subprocess.run(
                                [bash4, "-c", command],
                                env=env,
                                capture_output=True,
                                timeout=3,
                            )
                            self.assertIn(operation, log.read_text(), command)

    def test_literal_input_destinations_without_callbacks_remain_allowed(self):
        for command in (
            "a=(0); read 'a[0]' <<< value",
            "read -r label <<< value",
            "read -p 'a[expression]' label <<< value",
            "read -rp '$(git commit -am printed)' label <<< value",
            "mapfile -t rows <<< value",
            "builtin readarray -t rows <<< value",
            "printf '%s' 'mapfile -C callback'",
            "printf '%s' 'read a[expression]'",
        ):
            for hook in COMMIT_HOOKS:
                self.assertEqual(self.run_hook(hook, command), (0, 0), command)
            self.assertEqual(DestructiveHookTests().decision(command), "allow", command)

    def test_actual_heredoc_indirect_expansions_and_integer_writers(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            log = root / "calls"
            fake = root / "git"
            fake.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$FAKE_GIT_LOG"\n')
            fake.chmod(0o755)
            env = dict(
                os.environ,
                PATH=str(root) + os.pathsep + os.environ["PATH"],
                FAKE_GIT_LOG=str(log),
            )
            for operation in ("commit -am broken", "push --force origin main"):
                prefix = "a=(0); expression='a[$(git " + operation + "; printf 0)]'; "
                tails = [
                    "cat <<EOF\n${a[expression]}\nEOF",
                    "value=abc; cat <<EOF\n${value:expression:1}\nEOF",
                ]
                tails += [
                    "declare -i number; " + wrapper + "printf -v number '%s' expression"
                    for wrapper in ("", "builtin ", "command ", "command builtin ")
                ]
                tails += ["declare -i number; read number <<< expression"]
                for tail in tails:
                    command = prefix + tail
                    log.write_text("")
                    subprocess.run(
                        ["bash", "-c", command], env=env, capture_output=True, timeout=3
                    )
                    self.assertIn(operation, log.read_text(), command)
                    with self.subTest(command=command):
                        if operation.startswith("commit"):
                            for hook in COMMIT_HOOKS:
                                self.assertEqual(self.run_hook(hook, command), (2, 0))
                        else:
                            self.assertEqual(
                                DestructiveHookTests().decision(command), "deny"
                            )

    def test_heredoc_literals_and_numeric_integer_writers_remain_data(self):
        for command in (
            "cat <<'EOF'\n${a[expression]}\nEOF",
            "a=(one); cat <<EOF\n${a[0]}\nEOF",
            "value=abc; cat <<EOF\n${value:0:1}\nEOF",
            "declare -i number; printf -v number '%s' 123",
            "declare -i number; builtin printf -vnumber '%s' 123",
            "printf -v label '%s' expression",
            "read label <<< expression",
        ):
            for hook in COMMIT_HOOKS:
                self.assertEqual(self.run_hook(hook, command), (0, 0), command)
            self.assertEqual(DestructiveHookTests().decision(command), "allow", command)

    def test_actual_compound_array_and_parameter_arithmetic(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            log = root / "calls"
            fake = root / "git"
            fake.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$FAKE_GIT_LOG"\n')
            fake.chmod(0o755)
            env = dict(
                os.environ,
                PATH=str(root) + os.pathsep + os.environ["PATH"],
                FAKE_GIT_LOG=str(log),
            )
            for operation in ("commit -am broken", "push --force origin main"):
                prefix = "a=(0); expression='a[$(git " + operation + "; printf 0)]'; "
                for tail in (
                    "arr=([expression]=1)",
                    'value=abc; printf "%s" "${value:expression:1}"',
                    'value=abc; printf "%s" "${value:0:expression}"',
                    'files=(one two); printf "%s" "${files[@]:expression:1}"',
                ):
                    command = prefix + tail
                    log.write_text("")
                    subprocess.run(
                        ["bash", "-c", command], env=env, capture_output=True, timeout=3
                    )
                    self.assertIn(operation, log.read_text(), command)
                    with self.subTest(command=command):
                        if operation.startswith("commit"):
                            for hook in COMMIT_HOOKS:
                                self.assertEqual(self.run_hook(hook, command), (2, 0))
                        else:
                            self.assertEqual(
                                DestructiveHookTests().decision(command), "deny"
                            )

    def test_whole_arrays_and_literal_array_contents_remain_data(self):
        for command in (
            'files=(one two); printf "%s\\n" "${files[@]}"',
            'files=(one two); printf "%s" "${files[*]}"',
            'files=(one two); printf "%s" "${files[@]:0:1}"',
            "files=('[expression]=1' 'git commit -am printed')",
            'value=abc; printf "%s" "${value:0:1}"',
            'value=abc; printf "%s" "${value:-fallback}"',
        ):
            for hook in COMMIT_HOOKS:
                with self.subTest(command=command, hook=hook):
                    self.assertEqual(self.run_hook(hook, command), (0, 0))
            self.assertEqual(DestructiveHookTests().decision(command), "allow")

    def test_actual_local_transport_custom_program_is_guarded(self):
        import shlex

        actual_git = shutil.which("git")
        receiver = shutil.which("git-receive-pack")
        self.assertIsNotNone(receiver)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository, remote, bin_dir = (
                root / "repository",
                root / "remote.git",
                root / "bin",
            )
            bin_dir.mkdir()
            log = root / "calls"
            fake = bin_dir / "git"
            fake.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$FAKE_GIT_LOG"\n')
            fake.chmod(0o755)
            subprocess.run(
                [actual_git, "init", "-q", "--initial-branch=feature", str(repository)],
                check=True,
            )
            subprocess.run(
                [actual_git, "init", "--bare", "-q", str(remote)], check=True
            )
            subprocess.run(
                [
                    actual_git,
                    "-C",
                    str(repository),
                    "-c",
                    "user.name=fixture",
                    "-c",
                    "user.email=fixture@example.test",
                    "commit",
                    "--allow-empty",
                    "-qm",
                    "fixture",
                ],
                check=True,
            )
            env = dict(
                os.environ,
                PATH=str(bin_dir) + os.pathsep + os.environ["PATH"],
                FAKE_GIT_LOG=str(log),
            )
            program = (
                shlex.quote(str(fake))
                + " push --force origin main; "
                + shlex.quote(receiver)
            )
            for flag in ("--receive-pack", "--exec", "--rece", "--exe"):
                for equal in (False, True):
                    option = [flag + "=" + program] if equal else [flag, program]
                    log.write_text("")
                    result = subprocess.run(
                        [actual_git, "push"] + option + [str(remote), "feature"],
                        cwd=repository,
                        env=env,
                        capture_output=True,
                        timeout=5,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("push --force origin main", log.read_text())
                    command = "git push " + shlex.join(
                        option + [str(remote), "feature"]
                    )
                    for hook in COMMIT_HOOKS:
                        with self.subTest(flag=flag, equal=equal, hook=hook):
                            self.assertEqual(self.run_hook(hook, command), (2, 0))
                    with self.subTest(flag=flag, equal=equal, guard="push"):
                        self.assertEqual(
                            DestructiveHookTests().decision(command), "deny"
                        )

    def test_actual_supplied_wrappers_and_arithmetic_contexts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            log = root / "calls"
            fake = root / "git"
            fake.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$FAKE_GIT_LOG"\n')
            fake.chmod(0o755)
            env = dict(
                os.environ,
                PATH=str(root) + os.pathsep + os.environ["PATH"],
                FAKE_GIT_LOG=str(log),
            )
            for operation in ("commit -am broken", "push --force origin main"):
                arithmetic = "expression='a[$(git " + operation + "; printf 0)]'; "
                commands = [
                    "printf '%s\\n' 'git " + operation + "' | xargs " + child
                    for child in ("env", "env env", "nice env")
                ]
                commands += [
                    arithmetic + tail
                    for tail in (
                        "[[ expression -eq 0 ]]",
                        "declare -i number=expression",
                        "typeset -i number=expression",
                        "declare -i number; number=expression",
                        "declare -i number=0; number+=expression",
                        "arr[expression]=1",
                        'echo "${arr[expression]}"',
                        "declare -a 'arr[expression]=1'",
                    )
                ]
                for command in commands:
                    log.write_text("")
                    subprocess.run(
                        ["bash", "-c", command], env=env, capture_output=True, timeout=3
                    )
                    self.assertIn(operation, log.read_text(), command)
                    with self.subTest(command=command):
                        if operation.startswith("commit"):
                            for hook in COMMIT_HOOKS:
                                self.assertEqual(self.run_hook(hook, command), (2, 0))
                        else:
                            self.assertEqual(
                                DestructiveHookTests().decision(command), "deny"
                            )
        for command in (
            "printf '%s\\n' 'git commit -am printed' | xargs echo",
            "[[ 1+2 -eq 3 ]]",
            "declare -i number=1+2",
            "declare -i number; number=2+3",
            "arr[0]=1",
            'echo "${arr[0]}"',
            "printf '%s' '[[ expression -eq 0 ]]'",
        ):
            for hook in COMMIT_HOOKS:
                self.assertEqual(self.run_hook(hook, command), (0, 0))
            self.assertEqual(DestructiveHookTests().decision(command), "allow")

    def test_actual_xargs_git_inputs_and_indirect_arithmetic_are_guarded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            log = root / "calls"
            fake = root / "git"
            fake.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$FAKE_GIT_LOG"\n')
            fake.chmod(0o755)
            env = dict(
                os.environ,
                PATH=str(root) + os.pathsep + os.environ["PATH"],
                FAKE_GIT_LOG=str(log),
            )
            for operation in ("commit -am broken", "push --force origin main"):
                for command in (
                    "printf '%s\\n' '" + operation + "' | xargs git",
                    "xargs git <<'INPUT'\n" + operation + "\nINPUT",
                    "expression='a[$(git "
                    + operation
                    + "; printf 0)]'; echo $((expression))",
                    "first=second; second='a[$(git "
                    + operation
                    + "; printf 0)]'; echo $((first + 1))",
                ):
                    log.write_text("")
                    subprocess.run(
                        ["bash", "-c", command], env=env, capture_output=True, timeout=3
                    )
                    self.assertIn(operation, log.read_text(), command)
                    with self.subTest(command=command):
                        if operation.startswith("commit"):
                            for hook in COMMIT_HOOKS:
                                self.assertEqual(self.run_hook(hook, command), (2, 0))
                        else:
                            self.assertEqual(
                                DestructiveHookTests().decision(command), "deny"
                            )
        for command in (
            "echo $((1+2*3))",
            "echo $((count=1+2))",
            "printf '%s' 'echo $((expression))'",
            "printf '%s' 'xargs git commit -am literal'",
        ):
            for hook in COMMIT_HOOKS:
                self.assertEqual(self.run_hook(hook, command), (0, 0))
            self.assertEqual(DestructiveHookTests().decision(command), "allow")

    def test_arithmetic_command_output_is_unresolved_not_numeric_proof(self):
        command = "echo $(( $(date +%s) + 1 ))"
        for hook in COMMIT_HOOKS:
            self.assertEqual(self.run_hook(hook, command), (2, 0))
        self.assertEqual(DestructiveHookTests().decision(command), "deny")

    def test_xargs_supplied_shell_programs_are_not_literal_data(self):
        for git in ("git commit -am broken", "git push --force origin main"):
            for form in (
                "printf '%s\\n' '{git}' | xargs -I CMD sh -c CMD",
                "xargs --replace=CMD sh -c CMD <<'INPUT'\n{git}\nINPUT",
                "printf '%s\\n' '{git}' | xargs -ICMD nice sh -c CMD",
                "printf '%s\\n' '{git}' | xargs sh -c",
                "printf '%s\\n' '{git}' | xargs -I CMD CMD",
            ):
                command = form.format(git=git)
                with self.subTest(command=command):
                    if "commit" in git:
                        for hook in COMMIT_HOOKS:
                            self.assertEqual(self.run_hook(hook, command), (2, 0))
                    else:
                        self.assertEqual(
                            DestructiveHookTests().decision(command), "deny"
                        )
        command = "printf '%s\\n' 'git commit -am literal; git push --force origin main' | xargs -I CMD printf '%s' CMD"
        for hook in COMMIT_HOOKS:
            self.assertEqual(self.run_hook(hook, command), (0, 0))
        self.assertEqual(DestructiveHookTests().decision(command), "allow")

    def test_actual_bash_xargs_and_let_execute_fake_git(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake = root / "git"
            log = root / "calls"
            fake.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$FAKE_GIT_LOG"\n')
            fake.chmod(0o755)
            env = dict(
                os.environ,
                PATH=str(root) + os.pathsep + os.environ["PATH"],
                FAKE_GIT_LOG=str(log),
            )
            for git in ("git commit -am broken", "git push --force origin main"):
                for form in (
                    "printf '%s\\n' '{git}' | xargs -I CMD sh -c CMD",
                    "xargs -I CMD sh -c CMD <<'INPUT'\n{git}\nINPUT",
                    "let 'a[$({git}; printf 0)]=1'",
                    "builtin let 'a[$({git}; printf 0)]=1'",
                    "(( a[$({git}; printf 0)] = 1 ))",
                ):
                    command = form.format(git=git)
                    log.write_text("")
                    subprocess.run(
                        ["bash", "-c", command], env=env, capture_output=True, timeout=3
                    )
                    self.assertIn(git[4:], log.read_text(), command)
                    with self.subTest(command=command):
                        if "commit" in git:
                            for hook in COMMIT_HOOKS:
                                self.assertEqual(self.run_hook(hook, command), (2, 0))
                        else:
                            self.assertEqual(
                                DestructiveHookTests().decision(command), "deny"
                            )
        for command in (
            "let 'count=1+2'",
            "let 1+2",
            "(( 1 + 2 ))",
            "printf '%s' 'let a[$(git commit -am literal)]=1'",
        ):
            for hook in COMMIT_HOOKS:
                self.assertEqual(self.run_hook(hook, command), (0, 0))
            self.assertEqual(DestructiveHookTests().decision(command), "allow")

    def test_watch_constructed_shell_program_and_direct_mode(self):
        for prefix in ("watch -n 5", "watch -n5", "watch --interval=5"):
            for git in ("git commit -am broken", "git push --force origin main"):
                command = prefix + " echo 'tick; " + git + "'"
                if "commit" in git:
                    for hook in COMMIT_HOOKS:
                        self.assertEqual(self.run_hook(hook, command), (2, 0))
                else:
                    self.assertEqual(DestructiveHookTests().decision(command), "deny")
        for mode in ("-x", "--exec"):
            command = (
                "watch "
                + mode
                + " -n5 echo 'tick; git commit -am literal; git push --force origin main'"
            )
            for hook in COMMIT_HOOKS:
                self.assertEqual(self.run_hook(hook, command), (0, 0))
            self.assertEqual(DestructiveHookTests().decision(command), "allow")
        program = "watch -n5 \"printf '%s' 'tick; git commit -am literal; git push --force origin main'\""
        for hook in COMMIT_HOOKS:
            self.assertEqual(self.run_hook(hook, program), (0, 0))
        self.assertEqual(DestructiveHookTests().decision(program), "allow")

    @unittest.skipUnless(shutil.which("watch"), "actual watch runtime is unavailable")
    def test_actual_watch_shell_concatenation_executes_fake_git(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            log = root / "calls"
            fake = root / "git"
            fake.write_text(
                '#!/bin/sh\nprintf "%s\\n" "$*" >> "$FAKE_GIT_LOG"\nwc -l < "$FAKE_GIT_LOG"\n'
            )
            fake.chmod(0o755)
            env = dict(
                os.environ,
                PATH=str(root) + os.pathsep + os.environ["PATH"],
                FAKE_GIT_LOG=str(log),
                TERM="xterm",
            )
            for git in ("git commit -am broken", "git push --force origin main"):
                log.write_text("")
                result = subprocess.run(
                    ["watch", "-g", "-n", "0.1", "echo", "tick; " + git],
                    env=env,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    timeout=3,
                )
                self.assertIn(result.returncode, (0, 1), result.stderr)
                if result.returncode:
                    self.assertIn(b"Inappropriate ioctl for device", result.stderr)
                self.assertIn(git[4:], log.read_text())
            log.write_text("")
            result = subprocess.run(
                [
                    "watch",
                    "-x",
                    "-q",
                    "1",
                    "-n",
                    "0.1",
                    "echo",
                    "tick; git commit -am literal",
                ],
                env=env,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                timeout=3,
            )
            self.assertIn(result.returncode, (0, 1), result.stderr)
            if result.returncode:
                self.assertIn(b"Inappropriate ioctl for device", result.stderr)
            self.assertEqual(log.read_text(), "")

    def test_commit_argument_expansion_cannot_mutate_git_environment(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            alternate = root / "alternate"
            (alternate / "git").mkdir(parents=True)
            broken = root / "broken"
            broken.mkdir()
            (alternate / "git" / "config").write_text(
                "[core]\nworktree = " + str(broken) + "\n"
            )
            config = subprocess.check_output(
                ["git", "config", "--global", "--get", "core.worktree"],
                env=dict(os.environ, XDG_CONFIG_HOME=str(alternate), HOME=str(root)),
                text=True,
            ).rstrip("\n")
            self.assertEqual(config, str(broken))
            fakebin = root / "fakebin"
            fakebin.mkdir()
            observed = root / "observed-environment"
            executable = fakebin / "git"
            executable.write_text(
                '#!/bin/sh\nprintf \'%s\' "$XDG_CONFIG_HOME" > "$TEST_OBSERVED"\n'
            )
            executable.chmod(0o755)
            subprocess.run(
                ["bash", "-c", 'git commit -am "${XDG_CONFIG_HOME:=$TEST_ALTERNATE}"'],
                env=dict(
                    os.environ,
                    PATH=str(fakebin) + os.pathsep + os.environ["PATH"],
                    XDG_CONFIG_HOME="",
                    TEST_ALTERNATE=str(alternate),
                    TEST_OBSERVED=str(observed),
                ),
                check=True,
                capture_output=True,
                timeout=3,
            )
            self.assertEqual(observed.read_text(), str(alternate))
            for hook in COMMIT_HOOKS:
                for operand in (
                    '"${XDG_CONFIG_HOME:=' + str(alternate) + '}"',
                    '"${HOME:=' + str(alternate) + '}"',
                    '"${GIT_CONFIG_GLOBAL:=' + str(alternate / "git" / "config") + '}"',
                    '"$MESSAGE"',
                ):
                    with (
                        self.subTest(hook=hook, operand=operand),
                        mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": ""}),
                    ):
                        self.assertEqual(
                            self.run_hook(hook, "git commit -am " + operand), (2, 0)
                        )
                for operand in (
                    "'${XDG_CONFIG_HOME:=literal}'",
                    r'"\${XDG_CONFIG_HOME:=literal}"',
                ):
                    self.assertEqual(
                        self.run_hook(hook, "git commit -am " + operand), (0, 1)
                    )

    def test_child_execution_wrappers_cannot_hide_guarded_git(self):
        for program in (
            "sudo -s '{git}'",
            "runuser -c '{git}'",
            "nice sh -c '{git}'",
            "watch '{git}'",
        ):
            for hook in COMMIT_HOOKS:
                self.assertEqual(
                    self.run_hook(hook, program.format(git="git commit -am broken")),
                    (2, 0),
                )
            self.assertEqual(
                DestructiveHookTests().decision(
                    program.format(git="git push --force origin main")
                ),
                "deny",
            )
        for prefix in (
            "nice",
            "nice -n 5",
            "nice --adjustment=5",
            "nohup",
            "timeout 5",
            "timeout -s TERM -k 1 5",
            "sudo -u root",
            "xargs",
            "xargs -I ITEM",
            "xargs -n 1 -P 2",
            "watch -n 5",
            "sudo --user=root",
            "setsid",
            "stdbuf -o L",
            "chrt -p 1",
            "/usr/bin/nice -n 5",
            "nice nohup",
            "nice $OPTIONS",
            "timeout --unknown ARG 5",
            "sudo -u ||",
        ):
            for hook in COMMIT_HOOKS:
                with self.subTest(prefix=prefix, hook=hook):
                    self.assertEqual(
                        self.run_hook(hook, prefix + " git commit -am broken"), (2, 0)
                    )
            with self.subTest(prefix=prefix, guard="push"):
                self.assertEqual(
                    DestructiveHookTests().decision(
                        prefix + " git push --force origin main"
                    ),
                    "deny",
                )
        for prefix in (
            "nice",
            "nohup",
            "timeout 5",
            "sudo -u root",
            "setsid",
            "stdbuf -o L",
            "xargs -n 1",
            "watch -x -n 5",
            "sudo -s",
        ):
            command = (
                prefix
                + " printf '%s' 'git commit -am literal; git push --force origin main'"
            )
            for hook in COMMIT_HOOKS:
                self.assertEqual(self.run_hook(hook, command), (0, 0))
            self.assertEqual(DestructiveHookTests().decision(command), "allow")

    def test_actual_nice_and_nohup_execute_guarded_child(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake = root / "git"
            log = root / "calls"
            fake.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$FAKE_GIT_LOG"\n')
            fake.chmod(0o755)
            env = dict(
                os.environ,
                PATH=str(root) + os.pathsep + os.environ["PATH"],
                FAKE_GIT_LOG=str(log),
            )
            for prefix in ("nice", "nice -n 5", "nohup", "nice nohup"):
                for git in ("git commit -am broken", "git push --force origin main"):
                    command = prefix + " " + git
                    log.write_text("")
                    result = subprocess.run(
                        ["bash", "-c", command],
                        env=env,
                        cwd=root,
                        capture_output=True,
                        timeout=3,
                    )
                    self.assertEqual(result.returncode, 0)
                    self.assertIn(git[4:], log.read_text())
                    if "commit" in git:
                        for hook in COMMIT_HOOKS:
                            self.assertEqual(self.run_hook(hook, command), (2, 0))
                    else:
                        self.assertEqual(
                            DestructiveHookTests().decision(command), "deny"
                        )

    def test_arithmetic_quotes_do_not_hide_executed_git_substitutions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake = root / "git"
            log = root / "calls"
            fake.write_text(
                '#!/bin/sh\nprintf "%s\\n" "$*" >> "$FAKE_GIT_LOG"\nprintf "1"\n'
            )
            fake.chmod(0o755)
            env = dict(
                os.environ,
                PATH=str(root) + os.pathsep + os.environ["PATH"],
                FAKE_GIT_LOG=str(log),
            )
            for git in ("git commit -am broken", "git push --force origin main"):
                for template in (
                    "echo $(( '$(%s)' ))",
                    "echo $(( $(%s) + 1 ))",
                    "echo $(( 'nested$(%s)' ))",
                    "echo $(( ')$(%s)' ))",
                    "echo $(( '($( %s ))' ))",
                ):
                    command = template % git
                    log.write_text("")
                    subprocess.run(
                        ["bash", "-c", command], env=env, capture_output=True, timeout=2
                    )
                    self.assertIn(git[4:], log.read_text())
                    if "commit" in git:
                        for hook in COMMIT_HOOKS:
                            with self.subTest(command=command, hook=hook):
                                self.assertEqual(self.run_hook(hook, command), (2, 0))
                    else:
                        with self.subTest(command=command):
                            self.assertEqual(
                                DestructiveHookTests().decision(command), "deny"
                            )
            for command in (
                "echo $((1 << 2))",
                "echo '$(( $(git commit -am literal) ))'",
            ):
                for hook in COMMIT_HOOKS:
                    self.assertEqual(self.run_hook(hook, command), (0, 0))

    def test_standalone_xdg_assignment_cannot_redirect_git_configuration(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            clean, broken, original, alternate, home = [
                root / name
                for name in ("clean", "broken", "original", "alternate", "home")
            ]
            for directory in (clean, broken, original, alternate / "git", home):
                directory.mkdir(parents=True)
            for directory in (clean, broken):
                (directory / "tsconfig.json").write_text("{}")
            subprocess.run(["git", "init", "-q", str(clean)], check=True)
            (alternate / "git" / "config").write_text(
                "[core]\nworktree = " + str(broken) + "\n"
            )
            env = {"XDG_CONFIG_HOME": str(original), "HOME": str(home)}
            effective = subprocess.check_output(
                ["git", "-C", str(clean), "config", "--get", "core.worktree"],
                env=dict(dict(os.environ, **env), XDG_CONFIG_HOME=str(alternate)),
                text=True,
            ).rstrip("\n")
            self.assertEqual(effective, str(broken))
            for hook in COMMIT_HOOKS:
                payload = {
                    "cwd": str(clean),
                    "tool_input": {
                        "command": "XDG_CONFIG_HOME="
                        + str(alternate)
                        + "; git commit -am broken"
                    },
                }
                with (
                    mock.patch.dict(os.environ, env),
                    mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                    mock.patch(
                        "subprocess.run",
                        return_value=subprocess.CompletedProcess([], 0, "", ""),
                    ) as compiler,
                ):
                    with self.assertRaises(SystemExit) as stopped:
                        runpy.run_path(str(hook), run_name="__main__")
                self.assertEqual(stopped.exception.code, 2)
                compiler.assert_not_called()

    def test_invalid_utf8_compiler_failure_remains_blocking(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "tsconfig.json").write_text("{}")
            executable = root / "npx"
            executable.write_text('#!/bin/sh\nprintf "\\377" >&2\nexit 1\n')
            executable.chmod(0o755)
            env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ["PATH"])
            payload = json.dumps(
                {"cwd": str(root), "tool_input": {"command": "git commit -am broken"}}
            )
            for hook in COMMIT_HOOKS:
                result = subprocess.run(
                    [sys.executable, str(hook)],
                    input=payload.encode(),
                    env=env,
                    capture_output=True,
                    timeout=5,
                )
                self.assertEqual(
                    result.returncode, 2, result.stderr.decode(errors="replace")
                )
                self.assertIn(b"TypeScript check failed", result.stderr)

    def test_coproc_and_control_prefixes_cannot_hide_guarded_work(self):
        destructive = DestructiveHookTests()
        for template in (
            "coproc {git}",
            "coproc WORK {{ {git}; }}",
            "coproc {{ {git}; }}",
            "time -p coproc {{ {git}; }}",
            "for item in one; do {git}; done",
            "select item in one; do {git}; done",
            "case x in x) {git};; esac",
        ):
            for hook in COMMIT_HOOKS:
                with self.subTest(template=template, hook=hook):
                    self.assertEqual(
                        self.run_hook(
                            hook, template.format(git="git commit -am broken")
                        ),
                        (2, 0),
                    )
            with self.subTest(template=template, guard="push"):
                self.assertEqual(
                    destructive.decision(
                        template.format(git="git push --force origin main")
                    ),
                    "deny",
                )
        for command in (
            "coproc echo healthy",
            "coproc WORK { echo healthy; }",
            "for item in one; do echo healthy; done",
            "case x in x) echo healthy;; esac",
        ):
            self.assertEqual(destructive.decision(command), "allow")
            for hook in COMMIT_HOOKS:
                self.assertEqual(self.run_hook(hook, command), (0, 0))

    def test_non_shell_whitespace_cannot_create_comments_or_split_lines(self):
        destructive = DestructiveHookTests()
        for character in ("\r", "\v", "\f", "\x85", "\u2028", "\u2029"):
            for hook in COMMIT_HOOKS:
                with self.subTest(character=repr(character), hook=hook):
                    self.assertEqual(
                        self.run_hook(
                            hook, "echo x" + character + "#; git commit -am broken"
                        ),
                        (0, 1),
                    )
            self.assertEqual(
                destructive.decision(
                    "echo x" + character + "#; git push --force origin main"
                ),
                "deny",
            )

    def test_literal_bracket_conditions_allow_data_and_guard_substitutions(self):
        destructive = DestructiveHookTests()
        for command in (
            "[ -f package.json ] && npm test",
            "[[ -f package.json ]] && npm test",
            "if [[ -n healthy ]]; then npm test; fi",
            '[ "$(date)" ] && npm test',
            '[[ "$(date)" ]] && npm test',
            "[ 'git commit' ] && npm test",
        ):
            for hook in COMMIT_HOOKS:
                with self.subTest(command=command, hook=hook):
                    self.assertEqual(self.run_hook(hook, command), (0, 0))
            self.assertEqual(destructive.decision(command), "allow")
        for template in (
            '[ "$( {git} )" ] && npm test',
            '[[ "$( {git} )" ]] && npm test',
        ):
            for hook in COMMIT_HOOKS:
                self.assertEqual(
                    self.run_hook(hook, template.format(git="git commit -am broken")),
                    (2, 0),
                )
            self.assertEqual(
                destructive.decision(
                    template.format(git="git push --force origin main")
                ),
                "deny",
            )

    def test_actual_bash_fake_git_preserves_literal_control_characters(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake = root / "git"
            log = root / "calls"
            fake.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$FAKE_GIT_LOG"\n')
            fake.chmod(0o755)
            env = dict(
                os.environ,
                PATH=str(root) + os.pathsep + os.environ["PATH"],
                FAKE_GIT_LOG=str(log),
            )
            for character in ("\r", "\v", "\f", "\x85", "\u2028", "\u2029"):
                log.write_text("")
                command = "echo x" + character + "#; git push --force origin main"
                result = subprocess.run(
                    ["bash", "-c", command], env=env, capture_output=True, timeout=2
                )
                self.assertEqual(result.returncode, 0)
                self.assertEqual(
                    log.read_text().splitlines()[-1], "push --force origin main"
                )
                self.assertEqual(DestructiveHookTests().decision(command), "deny")
            bash_major = int(
                subprocess.check_output(
                    ["bash", "-c", 'printf "%s" "${BASH_VERSINFO[0]}"'], text=True
                )
            )
            # macOS system Bash 3 lacks coproc. Guard regressions above always
            # run; actual async command execution needs an existing Bash 4+.
            for command in (
                "coproc git push --force origin main; wait",
                "coproc WORK { git push --force origin main; }; wait",
            ):
                if bash_major >= 4:
                    log.write_text("")
                    self.assertEqual(
                        subprocess.run(
                            ["bash", "-c", command],
                            env=env,
                            capture_output=True,
                            timeout=2,
                        ).returncode,
                        0,
                    )
                    self.assertEqual(
                        log.read_text().splitlines(), ["push --force origin main"]
                    )
                self.assertEqual(DestructiveHookTests().decision(command), "deny")

    def test_timed_options_and_unknown_prefixes_cannot_skip_guards(self):
        destructive = DestructiveHookTests()
        for prefix in ("time -p", "time --unknown", "command time -p", "$PREFIX"):
            for hook in COMMIT_HOOKS:
                with self.subTest(prefix=prefix, hook=hook):
                    self.assertEqual(
                        self.run_hook(hook, prefix + " git commit -am broken"), (2, 0)
                    )
            self.assertEqual(
                destructive.decision(prefix + " git push --force origin main"), "deny"
            )
        self.assertEqual(
            destructive.decision("time -p echo 'git push --force origin main'"), "allow"
        )

    def test_expanded_printing_preambles_cannot_change_commit_target(self):
        import shlex

        for hook in COMMIT_HOOKS:
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                clean, broken = root / "target", root / "other" / "target"
                for repo in (clean, broken):
                    repo.mkdir(parents=True)
                    subprocess.run(["git", "init", "-q", str(repo)], check=True)
                    (repo / "tsconfig.json").write_text("{}")
                for preamble in (
                    'echo "${CDPATH:=' + str(broken.parent) + '}"',
                    'echo "${PWD=' + str(broken.parent) + '}"',
                    'printf "%s" "${CDPATH:=' + str(broken.parent) + '}"',
                    'printf "%n" CDPATH',
                    'builtin printf "%s%n" hello CDPATH',
                ):
                    payload = {
                        "cwd": str(root),
                        "tool_input": {
                            "command": preamble + "; cd target; git commit -am broken"
                        },
                    }
                    with (
                        self.subTest(hook=hook, preamble=preamble),
                        mock.patch.object(
                            sys, "stdin", io.StringIO(json.dumps(payload))
                        ),
                        mock.patch(
                            "subprocess.run",
                            side_effect=lambda *a, **kw: subprocess.CompletedProcess(
                                [], 0 if Path(kw["cwd"]) == clean else 1, "fixture", ""
                            ),
                        ) as compiler,
                        mock.patch.dict(os.environ, {"CDPATH": ""}),
                        mock.patch.object(sys, "stderr", io.StringIO()),
                    ):
                        with self.assertRaises(SystemExit) as stopped:
                            runpy.run_path(str(hook), run_name="__main__")
                    self.assertEqual(stopped.exception.code, 2)
                    compiler.assert_not_called()
                for preamble in (
                    "echo '${CDPATH:=other}'",
                    r'echo "\${CDPATH:=other}"',
                    "printf '%s' '%n'",
                ):
                    payload = {
                        "cwd": str(root),
                        "tool_input": {
                            "command": preamble + "; cd target; git commit -am safe"
                        },
                    }
                    with (
                        mock.patch.object(
                            sys, "stdin", io.StringIO(json.dumps(payload))
                        ),
                        mock.patch(
                            "subprocess.run",
                            return_value=subprocess.CompletedProcess([], 0, "", ""),
                        ) as compiler,
                        mock.patch.dict(os.environ, {"CDPATH": ""}),
                    ):
                        with self.assertRaises(SystemExit) as stopped:
                            runpy.run_path(str(hook), run_name="__main__")
                    self.assertEqual(stopped.exception.code, 0)
                    self.assertEqual(compiler.call_args.kwargs["cwd"], str(clean))

    def test_carriage_return_worktree_path_is_not_normalized(self):
        for hook in COMMIT_HOOKS:
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                clean, broken = root / "project", root / "project\r"
                for repo in (clean, broken):
                    repo.mkdir()
                    subprocess.run(["git", "init", "-q", str(repo)], check=True)
                    (repo / "tsconfig.json").write_text("{}")
                payload = {
                    "cwd": str(broken),
                    "tool_input": {"command": "git commit -am broken"},
                }
                with (
                    mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                    mock.patch(
                        "subprocess.run",
                        side_effect=lambda *a, **kw: subprocess.CompletedProcess(
                            [], 0 if Path(kw["cwd"]) == clean else 1, "fixture", ""
                        ),
                    ) as compiler,
                    mock.patch.object(sys, "stderr", io.StringIO()),
                ):
                    with self.assertRaises(SystemExit) as stopped:
                        runpy.run_path(str(hook), run_name="__main__")
                self.assertEqual(stopped.exception.code, 2)
                self.assertTrue(
                    all(
                        call.kwargs["cwd"] == str(broken)
                        for call in compiler.call_args_list
                    )
                )

    def test_prior_git_configured_execution_is_refused_or_disabled(self):
        for hook in COMMIT_HOOKS:
            for key, prefix, accepted in (
                ("core.fsmonitor", "git status", False),
                ("pager.status", "git status", False),
                ("diff.external", "git diff", False),
                ("diff.fixture.textconv", "git show", False),
                (
                    "diff.external",
                    "git --no-pager diff --no-ext-diff --no-textconv --stat",
                    True,
                ),
                (
                    "diff.fixture.textconv",
                    "git --no-pager show --no-ext-diff --no-textconv --stat",
                    True,
                ),
            ):
                with (
                    self.subTest(hook=hook, key=key, prefix=prefix),
                    tempfile.TemporaryDirectory() as temporary,
                ):
                    root = Path(temporary).resolve()
                    (root / "tsconfig.json").write_text("{}")
                    subprocess.run(["git", "init", "-q", str(root)], check=True)
                    marker = root / "must-not-execute"
                    program = root / "unsafe-execution"
                    program.write_text("#!/bin/sh\ntouch " + str(marker) + "\n")
                    program.chmod(0o755)
                    subprocess.run(
                        ["git", "-C", str(root), "config", key, str(program)],
                        check=True,
                    )
                    payload = {
                        "cwd": str(root),
                        "tool_input": {"command": prefix + "; git commit -am x"},
                    }
                    with (
                        mock.patch.object(
                            sys, "stdin", io.StringIO(json.dumps(payload))
                        ),
                        mock.patch(
                            "subprocess.run",
                            return_value=subprocess.CompletedProcess([], 0, "", ""),
                        ) as compiler,
                    ):
                        with self.assertRaises(SystemExit) as stopped:
                            runpy.run_path(str(hook), run_name="__main__")
                    self.assertEqual(stopped.exception.code, 0 if accepted else 2)
                    self.assertEqual(compiler.call_count, int(accepted))
                    self.assertFalse(marker.exists())

    def test_verified_boundary_preserves_nested_package_checks(self):
        for hook in COMMIT_HOOKS:
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                package = root / "packages" / "site"
                docs = package / "docs"
                docs.mkdir(parents=True)
                (root / "tsconfig.json").write_text("{}")
                (package / "tsconfig.json").write_text("{}")
                subprocess.run(["git", "init", "-q", str(root)], check=True)
                payload = {
                    "cwd": str(docs),
                    "tool_input": {"command": "git commit -am x"},
                }
                with (
                    mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                    mock.patch(
                        "subprocess.run",
                        return_value=subprocess.CompletedProcess(
                            [], 1, "broken package", ""
                        ),
                    ) as compiler,
                ):
                    with self.assertRaises(SystemExit) as stopped:
                        runpy.run_path(str(hook), run_name="__main__")
                self.assertEqual(stopped.exception.code, 2)
                self.assertEqual(compiler.call_args.kwargs["cwd"], str(package))

    def test_function_keyword_cannot_hide_commit_body(self):
        for hook in COMMIT_HOOKS:
            for declaration in (
                "function ship { git commit -am broken; }; ship",
                "function ship() { git commit -am broken; }; ship",
            ):
                self.assertEqual(self.run_hook(hook, declaration), (2, 0))
            self.assertEqual(
                self.run_hook(hook, "function greet { echo healthy; }; greet"), (0, 0)
            )

    def test_verified_ancestor_worktree_boundary_survives_metadata_marker(self):
        for hook in COMMIT_HOOKS:
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                metadata = root / "metadata"
                docs = metadata / "docs"
                docs.mkdir(parents=True)
                (root / "tsconfig.json").write_text("{}")
                subprocess.run(["git", "init", "-q", str(metadata)], check=True)
                subprocess.run(
                    ["git", "-C", str(metadata), "config", "core.worktree", str(root)],
                    check=True,
                )
                payload = {
                    "cwd": str(docs),
                    "tool_input": {"command": "git commit -am broken"},
                }
                with (
                    mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                    mock.patch(
                        "subprocess.run",
                        return_value=subprocess.CompletedProcess(
                            [], 1, "broken actual root", ""
                        ),
                    ) as compiler,
                ):
                    with self.assertRaises(SystemExit) as stopped:
                        runpy.run_path(str(hook), run_name="__main__")
                self.assertEqual(stopped.exception.code, 2)
                self.assertEqual(compiler.call_args.kwargs["cwd"], str(root))

    def test_prior_git_options_cannot_write_or_execute_before_commit(self):
        for hook in COMMIT_HOOKS:
            for prefix in (
                "git diff --no-index --output=src/app.ts /dev/null fixture.ts",
                "git diff --ext-diff",
                "git show --textconv HEAD",
                "git log --output=src/app.ts",
                "git grep --open-files-in-pager pattern",
                "git diff",
                "git show",
                "git log",
            ):
                with self.subTest(hook=hook, prefix=prefix):
                    self.assertEqual(
                        self.run_hook(hook, prefix + "; git commit -am broken"), (2, 0)
                    )
            self.assertEqual(
                self.run_hook(
                    hook,
                    "git --no-pager diff --no-ext-diff --no-textconv --stat; git commit -am x",
                ),
                (0, 1),
            )

    def test_unresolved_global_operand_cannot_expand_into_commit(self):
        for hook in COMMIT_HOOKS:
            for option in ("-C", "-c", "--git-dir", "--work-tree"):
                self.assertEqual(
                    self.run_hook(hook, "git " + option + " $ARGS"), (2, 0)
                )

    def test_direct_git_directory_inside_actual_worktree_checks_root(self):
        for hook in COMMIT_HOOKS:
            with tempfile.TemporaryDirectory() as temporary:
                broken = Path(temporary).resolve()
                repo = broken / "metadata"
                (broken / "tsconfig.json").write_text("{}")
                subprocess.run(["git", "init", "-q", "--bare", str(repo)], check=True)
                for key, value in (
                    ("core.bare", "false"),
                    ("core.worktree", str(broken)),
                ):
                    subprocess.run(
                        ["git", "--git-dir", str(repo), "config", key, value],
                        check=True,
                    )
                payload = {
                    "cwd": str(repo),
                    "tool_input": {"command": "git commit -am x"},
                }
                with (
                    mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                    mock.patch(
                        "subprocess.run",
                        return_value=subprocess.CompletedProcess(
                            [], 1, "broken actual types", ""
                        ),
                    ) as compiler,
                ):
                    with self.assertRaises(SystemExit) as stopped:
                        runpy.run_path(str(hook), run_name="__main__")
                self.assertEqual(stopped.exception.code, 2)
                self.assertEqual(compiler.call_args.kwargs["cwd"], str(broken))

    def test_missing_option_operands_cannot_swallow_commit_checks(self):
        for hook in COMMIT_HOOKS:
            for prefix in ("git -C", "git -c", "env -u", "exec -a"):
                for boundary in (" || ", "; ", "\n"):
                    with self.subTest(hook=hook, prefix=prefix, boundary=boundary):
                        self.assertEqual(
                            self.run_hook(hook, prefix + boundary + "git commit -am x"),
                            (2, 0),
                        )

    def test_trailing_space_worktree_path_is_not_trimmed(self):
        for hook in COMMIT_HOOKS:
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                clean = root / "project"
                broken = root / "project "
                for repo in (clean, broken):
                    repo.mkdir()
                    (repo / "tsconfig.json").write_text("{}")
                    subprocess.run(["git", "init", "-q", str(repo)], check=True)
                payload = {
                    "cwd": str(broken),
                    "tool_input": {"command": "git commit -am x"},
                }

                def result(*args, **kwargs):
                    return subprocess.CompletedProcess(
                        [], 0 if Path(kwargs["cwd"]) == clean else 1, "fixture", ""
                    )

                with (
                    mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                    mock.patch("subprocess.run", side_effect=result) as compiler,
                ):
                    with self.assertRaises(SystemExit) as stopped:
                        runpy.run_path(str(hook), run_name="__main__")
                self.assertEqual(stopped.exception.code, 2)
                self.assertEqual(compiler.call_args.kwargs["cwd"], str(broken))

    def test_direct_git_directory_discovers_external_worktree(self):
        for hook in COMMIT_HOOKS:
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                repo = root / "gitdir"
                broken = root / "broken"
                broken.mkdir()
                (broken / "tsconfig.json").write_text("{}")
                subprocess.run(["git", "init", "-q", "--bare", str(repo)], check=True)
                for key, value in (
                    ("core.bare", "false"),
                    ("core.worktree", str(broken)),
                ):
                    subprocess.run(
                        ["git", "--git-dir", str(repo), "config", key, value],
                        check=True,
                    )
                payload = {
                    "cwd": str(repo),
                    "tool_input": {"command": "git commit -am x"},
                }
                with (
                    mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                    mock.patch(
                        "subprocess.run",
                        return_value=subprocess.CompletedProcess(
                            [], 1, "broken actual types", ""
                        ),
                    ) as compiler,
                ):
                    with self.assertRaises(SystemExit) as stopped:
                        runpy.run_path(str(hook), run_name="__main__")
                self.assertEqual(stopped.exception.code, 2)
                self.assertEqual(compiler.call_args.kwargs["cwd"], str(broken))

    def test_prior_worktree_mutations_require_separate_commit_invocations(self):
        for hook in COMMIT_HOOKS:
            for prefix in (
                "git config core.worktree /tmp/broken",
                "git config --local core.worktree /tmp/broken",
                "git init",
                "git worktree add /tmp/broken",
                "python3 -c 'change_config()'",
                "cp /tmp/config .git/config",
            ):
                with self.subTest(hook=hook, prefix=prefix):
                    self.assertEqual(
                        self.run_hook(hook, prefix + "; git commit -am x"), (2, 0)
                    )
            for prefix in (
                "git status",
                "git config --get core.worktree",
                "printf '%s' 'git config core.worktree /tmp/broken'",
            ):
                self.assertEqual(
                    self.run_hook(hook, prefix + "; git commit -am x"), (0, 1)
                )

    def test_relative_git_commit_requires_compilation(self):
        for hook in COMMIT_HOOKS:
            for executable in ("bin/git", "./bin/git", "../tools/git"):
                self.assertEqual(
                    self.run_hook(
                        hook,
                        executable + " commit -am x",
                        result=subprocess.CompletedProcess([], 1, "broken types", ""),
                    ),
                    (2, 1),
                )
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                subprocess.run(["git", "init", "-q", str(root)], check=True)
                (root / "tsconfig.json").write_text("{}")
                (root / "bin").mkdir()
                import shutil

                (root / "bin/git").symlink_to(shutil.which("git"))
                payload = {
                    "cwd": str(root),
                    "tool_input": {"command": "bin/git commit -am x"},
                }
                with (
                    mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                    mock.patch(
                        "subprocess.run",
                        return_value=subprocess.CompletedProcess(
                            [], 1, "broken types", ""
                        ),
                    ) as compiler,
                ):
                    with self.assertRaises(SystemExit) as stopped:
                        runpy.run_path(str(hook), run_name="__main__")
                self.assertEqual(stopped.exception.code, 2)
                self.assertEqual(compiler.call_args.kwargs["cwd"], str(root))

    def test_all_leading_assignments_cannot_change_cdpath_target(self):
        for hook in COMMIT_HOOKS:
            self.assertEqual(
                self.run_hook(
                    hook, "UNUSED=1 CDPATH=/tmp printf '%s' cd; git commit -am x"
                ),
                (0, 1),
            )
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                clean = root / "target"
                broken = root / "other" / "target"
                for repo in (clean, broken):
                    repo.mkdir(parents=True)
                    (repo / "tsconfig.json").write_text("{}")
                payload = {
                    "cwd": str(root),
                    "tool_input": {
                        "command": f"UNUSED=1 CDPATH={broken.parent}; cd target; git commit -am x"
                    },
                }

                def compile_result(*args, **kwargs):
                    return subprocess.CompletedProcess(
                        [], 0 if Path(kwargs["cwd"]) == clean else 1, "fixture", ""
                    )

                with (
                    mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                    mock.patch(
                        "subprocess.run", side_effect=compile_result
                    ) as compiler,
                    mock.patch.dict(os.environ, {"CDPATH": ""}),
                ):
                    with self.assertRaises(SystemExit) as stopped:
                        runpy.run_path(str(hook), run_name="__main__")
                self.assertEqual(stopped.exception.code, 2)
                compiler.assert_not_called()

    def test_stored_core_worktree_compiles_actual_repository(self):
        for hook in COMMIT_HOOKS:
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                clean = root / "clean"
                broken = root / "broken"
                for repo in (clean, broken):
                    repo.mkdir()
                    (repo / "tsconfig.json").write_text("{}")
                subprocess.run(["git", "init", "-q", str(clean)], check=True)
                subprocess.run(
                    ["git", "-C", str(clean), "config", "core.worktree", str(broken)],
                    check=True,
                )
                payload = {
                    "cwd": str(root),
                    "tool_input": {"command": f"git -C {clean} commit -am x"},
                }

                def compile_result(*args, **kwargs):
                    return subprocess.CompletedProcess(
                        [], 0 if Path(kwargs["cwd"]) == clean else 1, "fixture", ""
                    )

                with (
                    mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                    mock.patch(
                        "subprocess.run", side_effect=compile_result
                    ) as compiler,
                ):
                    with self.assertRaises(SystemExit) as stopped:
                        runpy.run_path(str(hook), run_name="__main__")
                self.assertEqual(stopped.exception.code, 2)
                self.assertEqual(
                    [call.kwargs["cwd"] for call in compiler.call_args_list],
                    [str(broken)],
                )

    def test_unavailable_git_worktree_query_refuses_before_compiler(self):
        for hook in COMMIT_HOOKS:
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                subprocess.run(["git", "init", "-q", str(root)], check=True)
                (root / "tsconfig.json").write_text("{}")
                payload = {
                    "cwd": str(root),
                    "tool_input": {"command": "git commit -am x"},
                }
                process = mock.Mock(returncode=0)
                process.communicate.side_effect = [
                    subprocess.TimeoutExpired(["git"], 3),
                    ("", ""),
                ]
                with (
                    mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                    mock.patch("subprocess.Popen", return_value=process) as query,
                    mock.patch("subprocess.run") as compiler,
                ):
                    with self.assertRaises(SystemExit) as stopped:
                        runpy.run_path(str(hook), run_name="__main__")
                self.assertEqual(stopped.exception.code, 2)
                compiler.assert_not_called()
                process.kill.assert_called_once()
                self.assertEqual(
                    query.call_args.args[0][-2:], ["rev-parse", "--show-toplevel"]
                )

    def test_general_unrelated_shell_syntax_is_not_a_git_operation(self):
        commands = (
            'echo "$(date)"',
            'echo "$(printf \'%s\' "$(date)")"',
            "if test -f package.json; then npm test; fi",
            "if git status; then npm test; fi",
            'for file in a b; do stat "$file"; done',
            "node --version && python3 --version",
            "printf '%s' ';' git commit",
            "if command -v git >/dev/null; then npm test; fi",
            "{ echo ok; date; }",
            "values=('git' 'commit'); printf '%s' \"${values[0]}\"",
            "bash -c 'date'",
            "/usr/bin/env -u GRAVITY_UNUSED bash -c 'date'",
            "echo '$(git commit -am x)'",
            "printf '%s' 'if git commit -am x; then true; fi'",
        )
        destructive = DestructiveHookTests()
        for command in commands:
            with self.subTest(command=command):
                for hook in COMMIT_HOOKS:
                    self.assertEqual(self.run_hook(hook, command), (0, 0))
                self.assertEqual(destructive.decision(command), "allow")
        for command in (
            "bash -c 'date'; git commit -am x",
            "bash -c 'date'; git push --force origin main",
            'echo "$(printf "$(git commit -am x)")"',
            'echo "$(printf "$(git push --force origin main)")"',
            'echo "$(if test -f package.json; then "git" commit -am x; fi)"',
            'echo "$(if test -f package.json; then "git" push --force origin main; fi)"',
        ):
            with self.subTest(hidden=command):
                for hook in COMMIT_HOOKS:
                    self.assertEqual(self.run_hook(hook, command), (2, 0))
                self.assertEqual(destructive.decision(command), "deny")

    def test_printf_variable_cdpath_cannot_compile_clean_wrong_repository(self):
        for hook in COMMIT_HOOKS:
            self.assertEqual(
                self.run_hook(hook, "printf '%s' '-vCDPATH'; git commit -am x"), (0, 1)
            )
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                clean = root / "target"
                broken = root / "other" / "target"
                for repo in (clean, broken):
                    repo.mkdir(parents=True)
                    (repo / ".git").mkdir()
                    (repo / "tsconfig.json").write_text("{}")
                payload = {
                    "cwd": str(root),
                    "tool_input": {
                        "command": "printf -v CDPATH '%s' "
                        + str(broken.parent)
                        + "; cd target; git commit -am x"
                    },
                }

                def compiler_result(*args, **kwargs):
                    return subprocess.CompletedProcess(
                        [], 0 if Path(kwargs["cwd"]) == clean else 1, "fixture", ""
                    )

                with (
                    mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                    mock.patch(
                        "subprocess.run", side_effect=compiler_result
                    ) as compiler,
                    mock.patch.dict(os.environ, {"CDPATH": ""}),
                ):
                    with self.assertRaises(SystemExit) as stopped:
                        runpy.run_path(str(hook), run_name="__main__")
                self.assertEqual(stopped.exception.code, 2)
                compiler.assert_not_called()

    def test_wrapper_option_operands_cannot_hide_executables(self):
        for hook in COMMIT_HOOKS:
            for prefix in (
                "env -u GRAVITY_UNUSED",
                "env --unset GRAVITY_UNUSED",
                "/usr/bin/env -u GRAVITY_UNUSED",
                "exec -a diagnostic-name",
            ):
                self.assertEqual(
                    self.run_hook(hook, prefix + " bash -c '\"git\" commit -am x'"),
                    (2, 0),
                )

    def test_multiline_pipeline_refuses(self):
        for hook in COMMIT_HOOKS:
            for pipe in ("|", "|&"):
                for gap in ("\n", "\n\n"):
                    self.assertEqual(
                        self.run_hook(
                            hook,
                            "printf '%s' '\"git\" commit -am x' " + pipe + gap + "bash",
                        ),
                        (2, 0),
                    )

    def test_unrelated_literal_diagnostics_and_conditionals_remain_usable(self):
        for hook in COMMIT_HOOKS:
            for command in (
                'echo "$(pwd)"',
                "if true; then printf ok; fi",
                "printf '%s' '|&'",
            ):
                with self.subTest(hook=hook, command=command):
                    self.assertEqual(self.run_hook(hook, command), (0, 0))
            for command in (
                "if true; then printf ok; fi; git commit -am x",
                'echo "$(pwd; git commit -am x)"',
            ):
                self.assertEqual(self.run_hook(hook, command), (2, 0))

    def test_shell_input_channels_with_quoted_git_refuse(self):
        for hook in COMMIT_HOOKS:
            for command in (
                "bash <<< '\"git\" commit -am x'",
                "printf '%s' '\"git\" commit -am x' |& bash",
                "printf '%s' '\"git\" commit -am x' | bash",
                "bash <(printf '%s' '\"git\" commit -am x')",
            ):
                self.assertEqual(self.run_hook(hook, command), (2, 0))

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
            "a=(0); expression=x; arr=([expression]=1)",
            'files=(one two); printf "%s" "${files[@]}"',
            'value=abc; printf "%s" "${value:expression:1}"',
            "git push --receive-pack='git push --force origin main' /tmp/fixture.git feature",
            "git push --exe=custom /tmp/fixture.git feature",
            "printf '%s\\n' 'git push --force origin main' | xargs env",
            "expression='a[$(git commit -am broken; printf 0)]'; [[ expression -eq 0 ]]",
            "declare -i number; number+=expression",
            'echo "${arr[expression]}"',
            "printf '%s\\n' 'commit -am broken' | xargs git",
            "xargs git <<'INPUT'\npush --force origin main\nINPUT",
            "expression='a[$(git push --force origin main; printf 0)]'; echo $((expression))",
            "echo $((count=1+2))",
            "git status &&\ncd docs; git commit -m test",
            "printf '%s\\n' 'git push --force origin main' | xargs -I CMD sh -c CMD",
            "let 'a[$(git push --force origin main; printf 0)]=1'",
            "builtin let 'a[$(git commit -am broken; printf 0)]=1'",
            "let 'count=1+2'",
            "(( 1 + 2 ))",
            "watch -n5 echo 'tick; git push --force origin main'",
            "watch --exec -n5 echo 'tick; git push --force origin main'",
            'git commit -am "${XDG_CONFIG_HOME:=/alternate}"',
            "git commit -am '${XDG_CONFIG_HOME:=literal}'",
            "nice git commit -am broken",
            "xargs -n 1 git commit -am broken",
            "watch -n 5 git push --force origin main",
            "timeout -s TERM -k 1 5 git push --force origin main",
            "sudo -s 'git push --force origin main'",
            "nice printf '%s' 'git commit -am printed'",
            "echo $(( '$(git commit -am broken)' ))",
            "echo $(( ')$(git push --force origin main)' ))",
            "echo $((1 << 2))",
            "echo $(( $(date +%s) + 1 ))",
            "echo '$(( $(git commit -am literal) ))'",
            "XDG_CONFIG_HOME=/alternate; git commit -am broken",
            "coproc git commit -am broken",
            "coproc WORK { git push --force origin main; }",
            "coproc WORK { echo healthy; }",
            "for item in one; do git commit -am broken; done",
            "case x in x) git push --force origin main;; esac",
            "echo x\r#; git commit -am broken",
            "echo x\v#; git push --force origin main",
            "echo x\f#; git commit -am broken",
            "echo x\x85#; git push --force origin main",
            "echo x\u2028#; git commit -am broken",
            "echo x\u2029#; git push --force origin main",
            "[ -f package.json ] && npm test",
            "[[ -f package.json ]] && npm test",
            '[ "$(git commit -am broken)" ] && npm test',
            '[[ "$(git push --force origin main)" ]] && npm test',
            "time -p git commit -am broken",
            "time -p git push --force origin main",
            "command time -p git commit -am broken",
            "time --unknown git push --force origin main",
            "time -p echo 'git push --force origin main'",
            'echo "${CDPATH:=other}"; cd target; git commit -am broken',
            "echo '${CDPATH:=other}'; git commit -am safe",
            'printf "%n" CDPATH; git commit -am broken',
            "cat <<EOF\n${a[expression]}\nEOF",
            "cat <<EOF\n${value:expression:1}\nEOF",
            "cat <<'EOF'\n${a[expression]}\nEOF",
            "declare -i number; command builtin printf -v number '%s' expression",
            "declare -i number; builtin printf -vnumber '%s' 123",
            "declare -i number; read number <<< expression",
            "read 'a[expression]' <<< value",
            "builtin read -r 'a[0]' <<< value",
            "mapfile -c 1 -C callback <<< line",
            "command readarray -tCcallback <<< line",
            "read -p 'a[expression]' label <<< value",
            'echo "$(date)"',
            "if test -f package.json; then npm test; fi",
            'echo "$(printf "$(git commit -am x)")"',
            "/usr/bin/env -u UNUSED bash -c '\"git\" push --force origin main'",
            "/usr/bin/env -u UNUSED bash -c '\"git\" commit -am x'",
            "bash -c 'date'; git commit -am x",
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
                if outputs[0] and outputs[0][0] != "error":
                    expansion_flags = [
                        [getattr(word, "expanded", False) for word, _ in output]
                        for output in outputs
                    ]
                    self.assertEqual(expansion_flags[0], expansion_flags[1])
                    self.assertEqual(expansion_flags[0], expansion_flags[2])
                if command.startswith("echo 'literal") or command.startswith(
                    r"echo \`"
                ):
                    self.assertFalse(outputs[0] and outputs[0][0] == "error")

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
