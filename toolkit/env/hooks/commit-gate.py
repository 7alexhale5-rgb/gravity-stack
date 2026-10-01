#!/usr/bin/env python3
"""Claude PreToolUse hook: block commits when TypeScript checking cannot pass."""

import json
import io
import os
from pathlib import Path
import shlex
import subprocess
import sys


class CommentBoundaryStream(io.StringIO):
    """shlex may consume a comment, but must leave its shell newline separator."""
    def readline(self, size=-1):
        line = super().readline(size)
        if line.endswith("\n"):
            self.seek(self.tell() - 1)
            return line[:-1]
        return line


def commit_directories(command, base):
    """Resolve literal cd/Git options; never execute the submitted shell command."""
    lexer = shlex.shlex(CommentBoundaryStream(command), posix=True, punctuation_chars=";&|()<>\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    words = list(lexer)
    if not any(word == "git" for word in words):
        return []
    segments = []
    segment = []
    unsupported = False
    for word in words:
        if word and all(char in ";&|()<>\n" for char in word):
            unsupported |= word.strip("\n") not in ("", ";", "&&")
            segments.append(segment)
            segment = []
        else:
            segment.append(word)
    segments.append(segment)
    targets = []
    directory = base
    uncertain_cwd = False
    for args in segments:
        if not args:
            continue
        if args[0] == "cd":
            if len(args) != 2 or args[1].startswith("-") or any(c in args[1] for c in "$`~"):
                uncertain_cwd = True
            else:
                directory = (directory / args[1]).resolve()
            continue
        if args[0] in ("pushd", "popd", "eval", "source", ".", "export"):
            uncertain_cwd = True
        if args[0] != "git":
            if "git" in args and "commit" in args:
                raise ValueError("use a literal Git command so the commit directory can be checked")
            continue
        target = directory
        worktree = None
        gitdir = False
        config_worktree = False
        position = 1
        while position < len(args):
            flag = args[position]
            if flag in ("-C", "-c", "--git-dir", "--work-tree"):
                if position + 1 >= len(args):
                    raise ValueError("Git option requires a value")
                value = args[position + 1]
                if flag == "-C":
                    target = (target / value).resolve()
                elif flag == "--work-tree":
                    worktree = value
                elif flag == "--git-dir":
                    gitdir = True
                elif flag == "-c" and value.lower().startswith("core.worktree="):
                    config_worktree = True
                position += 2
            elif flag.startswith("-C") and len(flag) > 2:
                target = (target / flag[2:]).resolve()
                position += 1
            elif flag.startswith("--work-tree="):
                worktree = flag.split("=", 1)[1]
                position += 1
            elif flag.startswith("--git-dir="):
                gitdir = True
                position += 1
            elif flag.startswith("-c") and len(flag) > 2:
                config_worktree |= flag[2:].lower().startswith("core.worktree=")
                position += 1
            elif flag in (
                "--no-pager", "--paginate", "--no-optional-locks", "--literal-pathspecs", "--no-lazy-fetch", "--bare"
            ):
                position += 1
            else:
                if flag.startswith("-") and "commit" in args[position:]:
                    raise ValueError("unsupported Git option; use literal -C or --work-tree")
                break
        if position < len(args) and args[position] == "commit":
            if (gitdir or config_worktree) and worktree is None:
                raise ValueError("explicit --work-tree required with alternate Git directory configuration")
            if unsupported or uncertain_cwd or any(c in str(target) + (worktree or "") for c in "$`~"):
                raise ValueError("use literal cd/Git options without pipes, subshells or background commands")
            if worktree is not None:
                target = (target / worktree).resolve()
            if not target.is_dir():
                raise ValueError("commit directory does not exist")
            if target not in targets:
                targets.append(target)
    return targets


try:
    payload = json.load(sys.stdin)
    tool = payload.get("tool_input", {})
    base = Path(payload.get("cwd") or tool.get("cwd") or os.getcwd()).resolve()
    command = tool.get("command", "")
except (ValueError, TypeError, OSError, AttributeError):
    sys.exit(0)

try:
    directories = commit_directories(command, base)
except (ValueError, OSError) as error:
    print(f"COMMIT BLOCKED: directory check unavailable ({error})", file=sys.stderr)
    sys.exit(2)

for directory in directories:
    if not (directory / "tsconfig.json").is_file():
        continue
    try:
        check = subprocess.run(
            ["npx", "tsc", "--noEmit"],
            cwd=str(directory),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if check.returncode != 0:
            detail = (check.stderr or check.stdout).strip()[:1000]
            print(
                "COMMIT BLOCKED: TypeScript check failed"
                + (":\n" + detail if detail else ""),
                file=sys.stderr,
            )
            sys.exit(2)
    except (OSError, subprocess.TimeoutExpired, subprocess.SubprocessError) as error:
        print(
            f"COMMIT BLOCKED: TypeScript check unavailable ({type(error).__name__})",
            file=sys.stderr,
        )
        sys.exit(2)

sys.exit(0)
