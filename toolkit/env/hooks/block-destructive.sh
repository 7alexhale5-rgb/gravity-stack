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

try:
    tokens = shell_tokens(command)
except ValueError:
    deny("shell command cannot be inspected")

for index, (word, operator) in enumerate(tokens):
    if operator or not git_executable(word):
        continue
    args = []
    for part, operator in tokens[index + 1:]:
        if operator:
            break
        args.append(part)
    pos = 0
    inline_config = False
    while pos < len(args):
        flag = args[pos]
        if flag in ("-c", "-C", "--git-dir", "--work-tree", "--config-env", "--namespace"):
            inline_config |= flag in ("-c", "--config-env")
            pos += 2
        elif flag.startswith(("-c", "-C", "--git-dir=", "--work-tree=", "--config-env=", "--namespace=", "--exec-path=", "--attr-source=")):
            inline_config |= flag.startswith(("-c", "--config-env="))
            pos += 1
        elif flag in ("-P", "-p", "--no-advice", "--no-pager", "--paginate", "--no-optional-locks", "--literal-pathspecs", "--glob-pathspecs", "--noglob-pathspecs", "--icase-pathspecs", "--no-replace-objects", "--no-lazy-fetch", "--bare"):
            pos += 1
        else:
            if flag.startswith("-") and "push" in args[pos:]:
                deny("unsupported Git option before push")
            break
    if pos >= len(args) or args[pos] != "push":
        continue
    if inline_config:
        deny("inline Git configuration can change push effects; use a literal push")
    push_args = args[pos + 1:]
    positionals = []
    remote_option = False
    lease = False
    all_refs = False
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
        elif arg in ("--force", "--mirror") or (arg.startswith("-") and not arg.startswith("--") and "f" in arg[1:]):
            deny("unprotected force push")
        elif arg == "--force-with-lease" or arg.startswith("--force-with-lease="):
            lease = True
        elif arg in ("--all", "--tags", "--follow-tags", "--prune", "--delete", "-d"):
            all_refs = True
        elif arg in (
            "-u", "--set-upstream", "-n", "--dry-run",
            "-v", "--verbose", "-q", "--quiet", "--atomic", "--signed",
            "--no-signed", "--verify", "--no-verify", "--porcelain", "--progress",
        ):
            pass
        elif arg.startswith("-"):
            deny("unsupported push option; use full option names")
        else:
            positionals.append(arg)
        position += 1
    if any(ref.startswith("+") for ref in positionals):
        deny("implicit force push")
    if not lease:
        continue
    if remote_option or all_refs:
        deny("lease push needs a positional repository and explicit destination")
    refs = positionals[1:]
    if not refs:
        deny("force push has no explicit feature ref")
    for ref in refs:
        if ref.count(":") != 1:
            deny("lease push needs an explicit destination refspec")
        source, destination = ref.split(":")
        if not re.fullmatch(r"[A-Za-z0-9_./-]+", source) or not re.fullmatch(r"refs/heads/[A-Za-z0-9_./-]+", destination):
            deny("lease push needs literal source and full branch destination")
        dest = destination.removeprefix("refs/heads/")
        if dest in ("main", "master", "HEAD") or "*" in dest or not dest:
            deny("force push may update a protected or unknown ref")
'
