#!/bin/bash
# Claude PreToolUse Bash hook. Inspect literal commands; do not execute them.
python3 -c '
import json
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

try:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
    lexer.whitespace_split = True
    words = list(lexer)
except ValueError:
    sys.exit(0)

for index, word in enumerate(words):
    if word != "git":
        continue
    args = []
    for part in words[index + 1:]:
        if part in (";", "&&", "||", "|", "&", "(", ")"):
            break
        args.append(part)
    pos = 0
    while pos < len(args):
        flag = args[pos]
        if flag in ("-c", "-C", "--git-dir", "--work-tree"):
            pos += 2
        elif flag.startswith(("-c", "-C", "--git-dir=", "--work-tree=")):
            pos += 1
        else:
            break
    if pos >= len(args) or args[pos] != "push":
        continue
    push_args = args[pos + 1:]
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
        dest = ref.rsplit(":", 1)[-1].removeprefix("refs/heads/")
        if dest in ("main", "master", "HEAD") or "*" in dest or not dest:
            deny("force push may update a protected or unknown ref")
'
