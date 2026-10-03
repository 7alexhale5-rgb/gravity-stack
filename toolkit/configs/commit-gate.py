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
                char == "`" or (normalized.startswith("$(", position) and not normalized.startswith("$((", position))
            ):
                substitution = True
            if char == quote:
                quote = ""
        elif char in (chr(39), chr(34)):
            quote = char
            marked.append(marker)
        elif char == "`" or (normalized.startswith("$(", position) and not normalized.startswith("$((", position)):
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
    # Only executable wrapper arguments and pipeline inputs are shell programs;
    # search patterns and printed strings containing Git commands are ordinary data.
    group = []
    for word, operator in tokens + [(";", True)]:
        if operator and any(char in word for char in ";&\n"):
            heads = executable_heads(group)
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


def commit_directories(command, base):
    """Resolve literal cd/Git options; never execute the submitted shell command."""
    tokens = shell_tokens(command)
    at_head = True
    for word, operator in tokens:
        if operator:
            at_head = True
        elif at_head:
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", word):
                continue
            if getattr(word, "expanded", False):
                raise ValueError("expanded executable cannot establish a commit target")
            if word in ("env", "exec", "command", "builtin") or word.startswith("-"):
                continue
            at_head = False
    if (
        any(git_executable(word) for word, operator in tokens if not operator)
        and any(word == "commit" for word, operator in tokens if not operator)
        and any(
            name.startswith("GIT_CONFIG")
            or name
            in {
                "GIT_DIR",
                "GIT_WORK_TREE",
                "GIT_COMMON_DIR",
                "GIT_INDEX_FILE",
                "GIT_OBJECT_DIRECTORY",
                "GIT_ALTERNATE_OBJECT_DIRECTORIES",
                "GIT_CEILING_DIRECTORIES",
                "GIT_DISCOVERY_ACROSS_FILESYSTEM",
            }
            for name in os.environ
        )
    ):
        raise ValueError(
            "inherited Git environment cannot establish the commit worktree"
        )
    if (
        any(git_executable(word) for word, operator in tokens if not operator)
        and any(word == "commit" for word, operator in tokens if not operator)
        and any(operator and ("<" in word or ">" in word) for word, operator in tokens)
    ):
        raise ValueError(
            "Git commit redirections cannot be inspected; use a literal commit"
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
        if args[0] in ("!", "time"):
            # Prefixes change shell flow and can hide stateful directory builtins.
            # Refuse a later commit rather than compiling a guessed directory.
            raise ValueError("unsupported prefix before a possible Git commit")
        assignment_count = 0
        while assignment_count < len(args) and re.match(
            r"^[A-Za-z_][A-Za-z0-9_]*=", args[assignment_count]
        ):
            assignment_count += 1
        assigned_args = args[assignment_count:]
        effective_args = assigned_args
        while effective_args and effective_args[0] in ("builtin", "command"):
            effective_args = effective_args[1:]
            while effective_args and effective_args[0].startswith("-"):
                effective_args = effective_args[1:]
        if effective_args and effective_args[0] in (
            "declare",
            "typeset",
            "export",
            "readonly",
            "local",
            "unset",
            "read",
            "mapfile",
            "readarray",
            "set",
            "setopt",
            "unsetopt",
            "eval",
            "source",
            ".",
        ):
            uncertain_cwd = True
        if assignment_count and assigned_args:
            if assigned_args[0] in ("cd", "pushd", "popd") or (
                assigned_args[0] in ("builtin", "command")
                and any(word in ("cd", "pushd", "popd") for word in assigned_args[1:])
            ):
                uncertain_cwd = True
        if args[0].startswith("CDPATH=") or (
            args[0] in ("builtin", "command")
            and any(word in ("cd", "pushd", "popd") for word in args[1:])
        ):
            uncertain_cwd = True
        if args[0] == "cd":
            if (
                conditional
                or len(args) != 2
                or args[1].startswith("-")
                or any(c in args[1] for c in "$`~")
                or getattr(args[1], "expanded", False)
                or (
                    os.environ.get("CDPATH")
                    and not Path(args[1]).is_absolute()
                    and args[1].split("/", 1)[0] not in (".", "..")
                )
            ):
                uncertain_cwd = True
            else:
                path = directory / args[1]
                if not path.is_dir() or any(
                    part.is_symlink() for part in (path, *path.parents)
                ):
                    uncertain_cwd = True
                else:
                    directory = path.resolve()
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
            if getattr(flag, "expanded", False):
                raise ValueError(
                    "expanded Git subcommand or global option cannot be inspected"
                )
            if flag in ("-C", "-c", "--git-dir", "--work-tree"):
                if position + 1 >= len(args):
                    raise ValueError("Git option requires a value")
                value = args[position + 1]
                if getattr(value, "expanded", False):
                    raise ValueError(
                        "expanded Git global option value cannot be inspected"
                    )
                if flag == "-C":
                    if any(char in value for char in "$`~"):
                        raise ValueError(
                            "raw Git directory expansion cannot be inspected"
                        )
                    target = (target / value).resolve()
                elif flag == "--work-tree":
                    worktree = value
                elif flag == "--git-dir":
                    gitdir = True
                elif flag == "-c":
                    config_worktree |= not value.lower().startswith("core.commentchar=")
                position += 2
            elif flag.startswith("-C") and len(flag) > 2:
                if any(char in flag[2:] for char in "$`~"):
                    raise ValueError("raw Git directory expansion cannot be inspected")
                target = (target / flag[2:]).resolve()
                position += 1
            elif flag.startswith("--work-tree="):
                worktree = flag.split("=", 1)[1]
                position += 1
            elif flag.startswith("--git-dir="):
                gitdir = True
                position += 1
            elif flag.startswith("-c") and len(flag) > 2:
                config_worktree |= not flag[2:].lower().startswith("core.commentchar=")
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
            if config_worktree:
                raise ValueError("inline Git configuration effects cannot be inspected")
            if gitdir and worktree is None:
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
            target_record = (target, worktree is not None)
            if target_record not in targets:
                targets.append(target_record)
    if len(targets) > 1:
        raise ValueError(
            "multiple distinct commit targets require separate hook invocations"
        )
    return targets


def typescript_directory(directory, explicit_worktree):
    """Find the nearest TS project, bounded by a worktree marker or explicit root."""
    ancestors = (directory, *directory.parents)
    boundary = (
        directory
        if explicit_worktree
        else next(
            (candidate for candidate in ancestors if (candidate / ".git").exists()),
            None,
        )
    )
    # Without a worktree boundary, do not inspect unrelated parent projects.
    if boundary is None:
        return directory if (directory / "tsconfig.json").is_file() else None
    for candidate in ancestors:
        if (candidate / "tsconfig.json").is_file():
            return candidate
        if candidate == boundary:
            break
    return None


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

for target, explicit_worktree in directories:
    directory = typescript_directory(target, explicit_worktree)
    if directory is None:
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
