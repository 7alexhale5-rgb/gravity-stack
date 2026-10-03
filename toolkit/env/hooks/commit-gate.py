#!/usr/bin/env python3
"""Claude PreToolUse hook: block commits when TypeScript checking cannot pass."""

import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys


def shell_continuations(command):
    """Remove shell comments/continuations, preserving literal words and newlines."""
    output = []
    quote = ""
    comment = False
    word_start = True
    position = 0
    while position < len(command):
        char = command[position]
        if comment:
            if char == "\n":
                output.append(char)
                comment = False
                word_start = True
        elif char == "\\" and quote != chr(39) and position + 1 < len(command):
            following = command[position + 1]
            if following != "\n":
                output.extend((char, following))
                word_start = False
            position += 2
            continue
        elif quote:
            output.append(char)
            if char == quote:
                quote = ""
        elif char in (chr(39), chr(34)):
            output.append(char)
            quote = char
            word_start = False
        elif char == "#" and word_start:
            comment = True
        else:
            output.append(char)
            word_start = char in " \t\r\n;&|()<>"
        position += 1
    return "".join(output)


def git_executable(word):
    return word == "git" or (Path(word).is_absolute() and Path(word).name == "git")


def shell_tokens(command):
    """Keep literal punctuation distinct from shell operators after decoding."""
    marker = "\ue000"
    if marker in command:
        raise ValueError("reserved shell marker")
    marked = []
    quote = ""
    escaped = False
    for char in shell_continuations(command):
        if escaped:
            escaped = False
        elif char == "\\" and quote != chr(39):
            if not quote:
                marked.append(marker)
            escaped = True
        elif quote:
            if char == quote:
                quote = ""
        elif char in (chr(39), chr(34)):
            quote = char
            marked.append(marker)
        marked.append(char)
    lexer = shlex.shlex("".join(marked), posix=True, punctuation_chars=";&|()<>\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = ""
    return [
        (word.replace(marker, ""), bool(word) and all(c in ";&|()<>\n" for c in word))
        for word in lexer
    ]


def commit_directories(command, base):
    """Resolve literal cd/Git options; never execute the submitted shell command."""
    tokens = shell_tokens(command)
    if any(
        not operator
        and not git_executable(word)
        and re.search(r"(?:^|[^A-Za-z0-9_.-])git\s+[^;\n]*\bcommit\b", shell_continuations(word))
        for word, operator in tokens
    ):
        raise ValueError(
            "quoted or compound Git commit cannot be inspected; use literal Git"
        )
    if not any(git_executable(word) for word, operator in tokens if not operator):
        return []
    segments = []
    segment = []
    unsupported = False
    conditional = False
    for word, operator in tokens:
        if operator:
            unsupported |= word.strip("\n") not in ("", ";", "&&")
            segments.append((segment, conditional))
            segment = []
            separator = word.strip("\n")
            conditional = separator in ("&&", "||") or (conditional and not separator)
        else:
            segment.append(word)
    segments.append((segment, conditional))
    targets = []
    directory = base
    uncertain_cwd = False
    for args, conditional in segments:
        if not args:
            continue
        if args[0] == "cd":
            if (
                conditional
                or len(args) != 2
                or args[1].startswith("-")
                or any(c in args[1] for c in "$`~")
            ):
                uncertain_cwd = True
            else:
                directory = (directory / args[1]).resolve()
            continue
        if args[0] in ("pushd", "popd", "eval", "source", ".", "export"):
            uncertain_cwd = True
        if not git_executable(args[0]):
            if any(git_executable(word) for word in args) and "commit" in args:
                raise ValueError(
                    "use a literal Git command so the commit directory can be checked"
                )
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
                "--no-pager",
                "--paginate",
                "--no-optional-locks",
                "--literal-pathspecs",
                "--no-lazy-fetch",
                "--bare",
            ):
                position += 1
            else:
                if flag.startswith("-") and "commit" in args[position:]:
                    raise ValueError(
                        "unsupported Git option; use literal -C or --work-tree"
                    )
                break
        if position < len(args) and args[position] == "commit":
            if (gitdir or config_worktree) and worktree is None:
                raise ValueError(
                    "explicit --work-tree required with alternate Git directory configuration"
                )
            if (
                unsupported
                or uncertain_cwd
                or any(c in str(target) + (worktree or "") for c in "$`~")
            ):
                raise ValueError(
                    "use literal cd/Git options without pipes, subshells or background commands"
                )
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
