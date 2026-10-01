#!/bin/bash
# Claude PreToolUse Bash hook. Inspect literal commands; do not execute them.
python3 -c '
import json
import io
from pathlib import Path
import re
import shlex
import sys

try:
    command = json.load(sys.stdin).get("tool_input", {}).get("command", "")
except (ValueError, TypeError):
    sys.exit(0)

def deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": "BLOCKED: " + reason}}))
    sys.exit(0)

if re.search(r"rm\s+-r[f]?\s+(/|~|\$HOME|\.\.|/Users)", command):
    deny("recursive delete on sensitive path")
if re.search(r"DROP\s+(TABLE|DATABASE|SCHEMA)", command, re.I):
    deny("DROP statement detected; use migrations")
if re.search(r"git\s+reset\s+--hard", command):
    deny("git reset --hard discards uncommitted work")
if re.search(r"git\s+clean\s+-[a-zA-Z]*f", command):
    deny("git clean -f deletes untracked files")
if re.search(r"echo.*(_KEY|_SECRET|_TOKEN|PASSWORD).*\|", command):
    deny("possible credential exposure through a pipe")

class CommentBoundaryStream(io.StringIO):
    """shlex may consume a comment, but must leave its shell newline separator."""

    def readline(self, size=-1):
        line = super().readline(size)
        if line.endswith("\n"):
            self.seek(self.tell() - 1)
            return line[:-1]
        return line


def shell_continuations(command):
    """Remove shell line continuations without altering quoted literals or comments."""
    output = []
    quote = ""
    comment = False
    position = 0
    while position < len(command):
        char = command[position]
        if comment:
            output.append(char)
            comment = char != "\n"
        elif char == "\\" and quote != chr(39) and position + 1 < len(command):
            following = command[position + 1]
            if following != "\n":
                output.extend((char, following))
            position += 2
            continue
        else:
            if char in (chr(39), chr(34)):
                if not quote:
                    quote = char
                elif quote == char:
                    quote = ""
            elif (
                char == "#"
                and not quote
                and (not output or output[-1] in " \t\r\n;&|()<>")
            ):
                comment = True
            output.append(char)
        position += 1
    return "".join(output)


def git_executable(word):
    return word == "git" or (Path(word).is_absolute() and Path(word).name == "git")


try:
    lexer = shlex.shlex(CommentBoundaryStream(shell_continuations(command)), posix=True, punctuation_chars=";&|()<>\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    words = list(lexer)
except ValueError:
    sys.exit(0)

for index, word in enumerate(words):
    if not git_executable(word):
        continue
    args = []
    for part in words[index + 1:]:
        if part and all(char in ";&|()<>\n" for char in part):
            break
        args.append(part)
    pos = 0
    while pos < len(args):
        flag = args[pos]
        if flag in ("-c", "-C", "--git-dir", "--work-tree", "--config-env", "--namespace"):
            pos += 2
        elif flag.startswith(("-c", "-C", "--git-dir=", "--work-tree=", "--config-env=", "--namespace=", "--exec-path=", "--attr-source=")):
            pos += 1
        elif flag in ("--no-pager", "--paginate", "--no-optional-locks", "--literal-pathspecs", "--glob-pathspecs", "--noglob-pathspecs", "--icase-pathspecs", "--no-replace-objects", "--no-lazy-fetch", "--bare"):
            pos += 1
        else:
            break
    if pos >= len(args) or args[pos] != "push":
        continue
    push_args = args[pos + 1:]
    if "--mirror" in push_args or any(a.startswith("+") for a in push_args):
        deny("implicit force push")
    hard_force = any(a == "--force" or (a.startswith("-") and not a.startswith("--") and "f" in a[1:]) for a in push_args)
    lease = any(a == "--force-with-lease" or a.startswith("--force-with-lease=") for a in push_args)
    if not (hard_force or lease):
        continue
    if hard_force or any(a in ("--all", "--mirror") for a in push_args):
        deny("unprotected force push")
    positionals = [a for a in push_args if not a.startswith("-")]
    refs = positionals[1:]  # first positional is the remote
    if not refs:
        deny("force push has no explicit feature ref")
    for ref in refs:
        dest = ref.removeprefix("+").rsplit(":", 1)[-1].removeprefix("refs/heads/")
        if dest in ("main", "master", "HEAD") or "*" in dest or not dest:
            deny("force push may update a protected or unknown ref")
'
