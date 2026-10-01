#!/bin/bash
# Claude PreToolUse Bash hook. Inspect literal commands; do not execute them.
python3 -c '
import json
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


try:
    lexer = shlex.shlex(shell_continuations(command), posix=True, punctuation_chars=";&|()<>\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = ""
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
        elif flag in ("-P", "-p", "--no-advice", "--no-pager", "--paginate", "--no-optional-locks", "--literal-pathspecs", "--glob-pathspecs", "--noglob-pathspecs", "--icase-pathspecs", "--no-replace-objects", "--no-lazy-fetch", "--bare"):
            pos += 1
        else:
            if flag.startswith("-") and "push" in args[pos:]:
                deny("unsupported Git option before push")
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
    positionals = []
    remote_option = False
    position = 0
    while position < len(push_args):
        arg = push_args[position]
        if arg == "--":
            positionals.extend(push_args[position + 1:])
            break
        if arg in ("-o", "--push-option", "--repo", "--receive-pack", "--exec"):
            if position + 1 >= len(push_args):
                deny("push option needs a value")
            remote_option |= arg == "--repo"
            position += 2
            continue
        if arg.startswith(("--push-option=", "--repo=", "--receive-pack=", "--exec=")) or (arg.startswith("-o") and len(arg) > 2):
            remote_option |= arg.startswith("--repo=")
        elif arg.startswith("--force-with-lease=") or arg in (
            "--force-with-lease", "-u", "--set-upstream", "-n", "--dry-run",
            "-v", "--verbose", "-q", "--quiet", "--atomic", "--signed",
            "--no-signed", "--verify", "--no-verify", "--follow-tags",
        ):
            pass
        elif arg.startswith("-"):
            deny("unsupported force-push option; use explicit ordinary refs")
        else:
            positionals.append(arg)
        position += 1
    refs = positionals if remote_option else positionals[1:]
    if not refs:
        deny("force push has no explicit feature ref")
    for ref in refs:
        dest = ref.removeprefix("+").rsplit(":", 1)[-1].removeprefix("refs/heads/")
        if dest in ("main", "master", "HEAD") or "*" in dest or not dest:
            deny("force push may update a protected or unknown ref")
'
