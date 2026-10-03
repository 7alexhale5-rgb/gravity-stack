#!/bin/bash
# Claude PreToolUse Bash hook. Inspect literal commands; do not execute them.
python3 -c '
import json
import os
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
    shells = {
        "bash",
        "sh",
        "zsh",
        "dash",
        "ksh",
        "eval",
        "source",
        ".",
        "env",
        "exec",
    }

    def executable_heads(words):
        heads = []
        at_head = True
        wrapped = False
        for token in words:
            word, operator = (
                token
                if isinstance(token, tuple)
                else (token, bool(token) and all(char in ";&|\n" for char in token))
            )
            if operator:
                if any(char in "<>" for char in word) and (
                    at_head or (len(heads) == 1 and heads[0].isdigit())
                ):
                    raise ValueError("unsupported leading shell redirection")
                at_head = True
                wrapped = False
            elif at_head:
                if word in {
                    "if",
                    "then",
                    "else",
                    "elif",
                    "fi",
                    "for",
                    "while",
                    "until",
                    "do",
                    "done",
                    "case",
                    "esac",
                    "select",
                    "function",
                    "{",
                    "}",
                }:
                    raise ValueError("unsupported shell control structure")
                if word in {"!", "time"}:
                    wrapped = wrapped or word == "time"
                    continue
                if word in {"env", "exec", "command", "builtin"} or re.match(
                    r"^[A-Za-z_][A-Za-z0-9_]*=", word
                ):
                    if word in {"env", "exec"}:
                        heads.append(word)
                    wrapped |= word in {"env", "exec", "command", "builtin"}
                    continue
                if wrapped and word.startswith("-"):
                    continue
                heads.append(word if word == "." else Path(word).name)
                at_head = False
        return heads

    # Heredoc bodies are data unless fed to a shell or containing executable
    # substitutions in an unquoted heredoc. Unsupported delimiter syntax refuses.
    lines = command.splitlines(keepends=True)
    code = []
    line_index = 0
    quote_state = ""
    arithmetic_depth = 0
    had_documents = False
    while line_index < len(lines):
        header = lines[line_index]
        line_index += 1
        documents = []
        header_substitution = False
        escaped_header = False
        position = 0
        while position < len(header):
            char = header[position]
            if escaped_header:
                escaped_header = False
            elif char == "\\" and quote_state != chr(39):
                escaped_header = True
            elif arithmetic_depth:
                if char == "`" or header.startswith("$(", position):
                    header_substitution = True
                if char == "(":
                    arithmetic_depth += 1
                elif char == ")":
                    arithmetic_depth -= 1
            elif quote_state:
                if quote_state == chr(34) and (
                    char == "`" or header.startswith("$(", position)
                ):
                    header_substitution = True
                if char == quote_state:
                    quote_state = ""
            elif char in (chr(39), chr(34)):
                quote_state = char
            elif header.startswith("$((", position):
                arithmetic_depth = 2
                position += 3
                continue
            elif char == "`" or header.startswith("$(", position):
                header_substitution = True
            elif char == "#" and (
                position == 0 or header[position - 1] in " \t\r\n;&|()<>"
            ):
                break
            elif header.startswith("<<<", position):
                position += 3
                continue
            elif header.startswith("<<", position):
                match = re.match(
                    r"<<(-?)\s*([\x27][^\x27]*[\x27]|[\x22][^\x22]*[\x22]|[A-Za-z0-9_]+)(?=\s|[;&|<>]|$)",
                    header[position:],
                )
                if match is None:
                    raise ValueError("unsupported heredoc delimiter")
                raw = match.group(2)
                documents.append(
                    (
                        shlex.split(raw)[0],
                        bool(match.group(1)),
                        raw[0] in (chr(39), chr(34)),
                    )
                )
                position += match.end()
                continue
            position += 1
        code.append(header)
        if documents:
            had_documents = True
            if header_substitution:
                raise ValueError(
                    "heredoc in executable substitution cannot be inspected"
                )
            if quote_state:
                raise ValueError("multiline quoted heredoc header cannot be inspected")
            lexer = shlex.shlex(header, posix=True, punctuation_chars=";&|<>\n")
            lexer.whitespace = " \t\r"
            lexer.whitespace_split = True
            lexer.commenters = "#"
            if any(head in shells for head in executable_heads(list(lexer))):
                raise ValueError(
                    "heredoc supplied to executable shell cannot be inspected"
                )
        for delimiter, strip_tabs, quoted in documents:
            while line_index < len(lines):
                body = lines[line_index]
                line_index += 1
                code.append("\n")
                if (body.lstrip("\t") if strip_tabs else body).rstrip(
                    "\r\n"
                ) == delimiter:
                    break
                if not quoted and ("$(" in body or "`" in body):
                    raise ValueError(
                        "executable heredoc substitution cannot be inspected"
                    )
            else:
                raise ValueError("unterminated heredoc")
    command = "".join(code)
    if had_documents:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>\n")
        lexer.whitespace = " \t\r"
        lexer.whitespace_split = True
        lexer.commenters = "#"
        if any(head in shells for head in executable_heads(list(lexer))):
            raise ValueError(
                "heredoc combined with executable shell cannot be inspected"
            )
    marker = "\ue000"
    expansion_marker = "\ue001"
    if marker in command or expansion_marker in command:
        raise ValueError("reserved shell marker")

    class ShellWord(str):
        def __new__(cls, value, expanded):
            word = str.__new__(cls, value)
            word.expanded = expanded
            return word

    marked = []
    quote = ""
    escaped = False
    substitution = False
    normalized = shell_continuations(command)
    for position, char in enumerate(normalized):
        if escaped:
            escaped = False
        elif char == "\\" and quote != chr(39):
            if not quote:
                marked.append(marker)
            escaped = True
        elif quote:
            if quote == chr(34) and char in "$`":
                marked.append(expansion_marker)
            if quote == chr(34) and (
                char == "`"
                or (
                    normalized.startswith("$(", position)
                    and not normalized.startswith("$((", position)
                )
            ):
                substitution = True
            if char == quote:
                quote = ""
        elif char in (chr(39), chr(34)):
            quote = char
            marked.append(marker)
        elif char == "`" or (
            normalized.startswith("$(", position)
            and not normalized.startswith("$((", position)
        ):
            substitution = True
            marked.append(expansion_marker)
        elif char in "$*?[{~":
            marked.append(expansion_marker)
        marked.append(char)
    if substitution:
        raise ValueError("executable shell substitution cannot be inspected")
    lexer = shlex.shlex("".join(marked), posix=True, punctuation_chars=";&|()<>\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = ""
    tokens = [
        (
            ShellWord(
                word.replace(marker, "").replace(expansion_marker, ""),
                expansion_marker in word,
            ),
            bool(word) and all(c in ";&|()<>\n" for c in word),
        )
        for word in lexer
    ]
    if any(operator and word in ("<(", ">(") for word, operator in tokens):
        raise ValueError("executable process substitution cannot be inspected")
    # Only executable wrapper arguments and pipeline inputs are shell programs;
    # search patterns and printed strings containing Git commands are ordinary data.
    group = []
    for word, operator in tokens + [(";", True)]:
        if (
            operator
            and word not in ("|", "|&")
            and any(char in word for char in ";&\n")
        ):
            heads = executable_heads(group)
            if any(
                head in {"bash", "sh", "zsh", "dash", "ksh"} for head in heads
            ) and any(
                is_operator and any(char in value for char in "<|")
                for value, is_operator in group
            ):
                raise ValueError("opaque executable shell input cannot be inspected")
            if any(head in {"eval", "source", "."} for head in heads):
                raise ValueError("opaque eval or source program cannot be inspected")
            if any(
                head in {"bash", "sh", "zsh", "dash", "ksh"} for head in heads
            ) and any(
                value == "--command"
                or re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", value)
                or getattr(value, "expanded", False)
                for value, is_operator in group
                if not is_operator
            ):
                raise ValueError("opaque shell command program cannot be inspected")
            if any(head in shells for head in heads) and any(
                re.search(
                    r"(?:^|[^A-Za-z0-9_.-])git\s+[^;\n]*\b(?:push|commit)\b", value
                )
                for value, _ in group
            ):
                raise ValueError("executable Git shell wrapper cannot be inspected")
            group = []
        else:
            group.append((word, operator))
    return tokens


try:
    tokens = shell_tokens(command)
except ValueError:
    deny("shell command cannot be inspected")

if (any(git_executable(word) for word, operator in tokens if not operator)
        and any(word == "push" for word, operator in tokens if not operator)):
    if any(name.startswith("GIT_CONFIG") for name in os.environ):
        deny("inherited Git configuration environment cannot be safely inspected")
    heads = []
    at_head = True
    for word, operator in tokens:
        if operator:
            at_head = True
        elif at_head:
            heads.append(word)
            at_head = False
    if (any(not operator and word.startswith("GIT_CONFIG") for word, operator in tokens)
            or any(word in ("source", ".", "export", "eval", "env", "exec", "command") for word in heads)):
        deny("Git configuration environment or shell wrapper cannot be safely inspected")

for index, (word, operator) in enumerate(tokens):
    if operator or not git_executable(word):
        continue
    args = []
    redirection = False
    for part, operator in tokens[index + 1:]:
        if operator:
            if "<" in part or ">" in part:
                redirection = True
                continue
            break
        args.append(part)
    if redirection and "push" in args:
        deny("Git push with redirection cannot be fully inspected; use a literal push")
    pos = 0
    inline_config = False
    while pos < len(args):
        flag = args[pos]
        if getattr(flag, "expanded", False):
            deny("expanded Git command or options cannot be inspected")
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
    if any(getattr(arg, "expanded", False) for arg in args):
        deny("expanded push arguments cannot be inspected")
    if inline_config:
        deny("inline Git configuration can change push effects; use a literal push")
    push_args = args[pos + 1:]
    positionals = []
    remote_option = False
    lease = False
    all_refs = False
    delete_refs = False
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
        elif arg == "--prune":
            deny("pruning can delete protected remote refs; use explicit reviewed ref updates")
        elif arg in ("--all", "--tags", "--follow-tags", "--prune", "--delete", "-d"):
            all_refs = True
            delete_refs |= arg in ("--delete", "-d")
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
    deletion_candidates = positionals if remote_option else positionals[1:]
    for ref in deletion_candidates:
        if delete_refs or ref.startswith(":"):
            destination = ref.split(":")[-1]
            for prefix in ("refs/heads/", "heads/", "refs/"):
                if destination.startswith(prefix):
                    destination = destination.removeprefix(prefix)
                    break
            if destination in ("main", "master", "HEAD"):
                deny("deletion of a protected branch")
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
