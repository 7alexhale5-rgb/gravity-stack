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
            word_start = char in " \t\n;&|()<>"
        position += 1
    return "".join(output)


def git_executable(word):
    return Path(word).name == "git"


def shell_tokens(command):
    """Keep literal punctuation distinct from shell operators after decoding."""

    def literal_test_bracket(text, position):
        """Recognize standalone Bash test syntax, retaining glob uncertainty."""
        start = position - 1 if position and text[position - 1] == "[" else position
        end = start + (2 if text.startswith("[[", start) else 1)
        boundary = " \t\n;&|()<>"
        return (not start or text[start - 1] in boundary) and (end == len(text) or text[end] in boundary)

    def literal_arithmetic(expression):
        # Numeric literals and one simple assignment have no indirect variable
        # or array lookup whose runtime value could execute substitutions.
        value = re.sub(r"^\s*[A-Za-z_][A-Za-z0-9_]*\s*=(?!=)", "", expression, count=1)
        return bool(value.strip()) and bool(re.fullmatch(r"[0-9 \t+*/%()<>|&^!~=.-]+", value))

    def inspect_substitutions(text, depth=0, quote_sensitive=True):
        """Recursively inspect executable substitutions, retaining word expansion."""
        if depth > 16:
            raise ValueError("shell nesting exceeds inspection limit")
        rewritten = []
        quote = ""
        position = 0
        while position < len(text):
            char = text[position]
            if char == "\\" and quote != chr(39):
                rewritten.append("\ue003")
                rewritten.append(text[position : position + 2])
                position += 2
                continue
            if quote == chr(39):
                rewritten.append(char)
                if char == quote:
                    quote = ""
                position += 1
                continue
            bare_arithmetic = not quote and text.startswith("((", position)
            if text.startswith("$((", position) or bare_arithmetic:
                # Arithmetic quotes do not prevent command substitution. Inspect
                # its entire body under arithmetic expansion rules before any
                # ordinary-shell no-Git fast path can discard the expression.
                beginning = position + (2 if bare_arithmetic else 3)
                ending = beginning
                balance = 2
                arithmetic_quote = ""
                while ending < len(text):
                    current = text[ending]
                    if current == "\\":
                        ending += 2
                        continue
                    # Quotes delimit literal parentheses, but the subsequent
                    # expansion inspection deliberately ignores their shielding.
                    if arithmetic_quote:
                        if current == arithmetic_quote:
                            arithmetic_quote = ""
                    elif current in (chr(39), chr(34)):
                        arithmetic_quote = current
                    elif current == "(":
                        balance += 1
                    elif current == ")":
                        balance -= 1
                        if not balance:
                            break
                    ending += 1
                if ending >= len(text):
                    raise ValueError("unterminated arithmetic expansion")
                _, guarded = inspect_substitutions(
                    text[beginning : ending - 1], depth + 1, quote_sensitive=False
                )
                if guarded:
                    raise ValueError(
                        "guarded arithmetic substitution cannot be inspected"
                    )
                if not literal_arithmetic(text[beginning : ending - 1]):
                    raise ValueError("unresolved arithmetic command cannot be inspected")
                rewritten.append("\ue003true" if bare_arithmetic else "\ue002ARITHMETIC")
                position = ending + 1
                continue
            opening = text[position : position + 2]
            substitution = opening in ("$(", "<(", ">(") and not text.startswith(
                "$((", position
            )
            if char == "`" or substitution:
                beginning = position + (1 if char == "`" else 2)
                ending = beginning
                balance = 1
                inner_quote = ""
                while ending < len(text):
                    current = text[ending]
                    if current == "\\" and inner_quote != chr(39):
                        ending += 2
                        continue
                    if char == "`":
                        if current == "`":
                            break
                    elif inner_quote:
                        if current == inner_quote:
                            inner_quote = ""
                    elif current in (chr(39), chr(34)):
                        inner_quote = current
                    elif current == "(":
                        balance += 1
                    elif current == ")":
                        balance -= 1
                        if not balance:
                            break
                    ending += 1
                if ending >= len(text):
                    raise ValueError("unterminated executable shell substitution")
                if possible_guarded(text[beginning:ending], depth + 1):
                    return text, True
                # Output is unknown, even when the generating command is safe.
                rewritten.append("\ue002SUBSTITUTION")
                position = ending + 1
                continue
            if quote_sensitive and char in (chr(39), chr(34)):
                if not quote:
                    rewritten.append("\ue003")
                quote = "" if quote == char else (quote or char)
            if (
                char == "$"
                and quote != chr(39)
                or (
                    not quote
                    and char in "*?[{~"
                    and not (char == "[" and literal_test_bracket(text, position))
                    and not (
                        char == "{"
                        and position + 1 < len(text)
                        and text[position + 1] in " \t\n;"
                    )
                )
            ):
                rewritten.append("\ue002")
            rewritten.append(char)
            position += 1
        return "".join(rewritten), False

    def possible_guarded(text, depth=0, supplied_program=False):
        """Classify executable positions, not diagnostic names or printed data."""
        prepared, hidden = inspect_substitutions(shell_continuations(text), depth)
        if hidden:
            return True
        lexer = shlex.shlex(prepared, posix=True, punctuation_chars=";&|()<>\n")
        lexer.whitespace = " \t"
        lexer.whitespace_split = True
        lexer.commenters = ""
        words = list(lexer)
        head = True
        redirection_operand = False
        wrapper = ""
        wrapper_operand = False
        index = 0
        while index < len(words):
            raw = words[index]
            word = raw.replace("\ue002", "").replace("\ue003", "")
            expanded = "\ue002" in raw
            index += 1
            if redirection_operand:
                redirection_operand = False
                continue
            if raw and all(c in ";&|()<>\n" for c in raw):
                if wrapper_operand:
                    return True
                if any(c in "<>" for c in raw):
                    redirection_operand = True
                else:
                    head, wrapper = True, ""
                continue
            if not head:
                continue
            if (
                word.isdigit()
                and index < len(words)
                and any(c in "<>" for c in words[index])
            ):
                continue
            if wrapper_operand:
                if expanded:
                    return True
                wrapper_operand = False
                continue
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", word):
                # Literal array contents are data; executable substitutions were
                # already inspected recursively before this token walk.
                if index < len(words) and words[index] == "(":
                    balance = 1
                    index += 1
                    while index < len(words) and balance:
                        punctuation = words[index]
                        if punctuation and all(c in ";&|()<>\n" for c in punctuation):
                            for offset, char in enumerate(punctuation):
                                balance += (char == "(") - (char == ")")
                                if not balance:
                                    tail = punctuation[offset + 1 :]
                                    if tail:
                                        words.insert(index + 1, tail)
                                    break
                        index += 1
                    if balance:
                        return True
                continue
            if expanded:
                return True
            name = word if word == "." else Path(word).name
            if name in {
                "if",
                "then",
                "else",
                "elif",
                "fi",
                "while",
                "until",
                "for",
                "select",
                "case",
                "esac",
                "in",
                "do",
                "done",
                "!",
                "{",
                "}",
            }:
                continue
            if name == "coproc":
                # Async contexts need inspection before the no-Git fast path.
                # Bash permits a name before a compound body; the name is data.
                if index + 1 < len(words) and words[index + 1].replace("\ue003", "") in ("{", "("):
                    index += 1
                head = True
                continue
            if name in {"env", "exec", "command", "builtin", "time"}:
                wrapper = name
                continue
            if wrapper and word.startswith("-"):
                if wrapper == "command" and word in ("-v", "-V"):
                    head = False  # command lookup prints names; it does not run them.
                    continue
                if (
                    word in {"-u", "--unset"}
                    and wrapper == "env"
                    or word == "-a"
                    and wrapper == "exec"
                ):
                    wrapper_operand = True
                elif word == "--" or word in {
                    "-i",
                    "--ignore-environment",
                    "-c",
                    "-l",
                    "-p",
                    "-v",
                    "-V",
                }:
                    pass
                elif wrapper == "env" and (
                    word.startswith("--unset=")
                    or word.startswith("-u")
                    and len(word) > 2
                ):
                    pass
                else:
                    return True
                continue
            if name == "let":
                for operand in words[index:]:
                    if operand and all(c in ";&|()<>\n" for c in operand):
                        break
                    expression = operand.replace("\ue003", "")
                    if expression == "--":
                        continue
                    _, guarded = inspect_substitutions(expression, depth + 1, quote_sensitive=False)
                    if guarded or not literal_arithmetic(expression):
                        raise ValueError("unresolved arithmetic builtin cannot be inspected")
                head = False
                continue
            if supplied_program and name in {"bash", "sh", "zsh", "dash", "ksh", "python", "python3", "node", "perl", "ruby", "awk", "watch"}:
                raise ValueError("xargs supplied interpreter program cannot be inspected")
            if supplied_program and git_executable(word):
                # Appended stdin may supply Git options or its entire subcommand.
                # Inspecting only the fixed argv cannot prove the resulting call.
                raise ValueError("xargs supplied Git arguments cannot be inspected")
            if name in {"nice", "nohup", "timeout", "sudo", "setsid", "stdbuf", "chrt", "ionice", "taskset", "doas", "runuser", "xargs", "watch"}:
                # These programs execute a child. Keep their child executable
                # visible before the unrelated-command fast path. We refuse
                # guarded children rather than guessing altered cwd/env/options.
                operands = {
                    "nice": {"-n", "--adjustment"},
                    "timeout": {"-s", "--signal", "-k", "--kill-after"},
                    "sudo": {"-u", "--user", "-g", "--group", "-h", "--host", "-p", "--prompt", "-C", "--close-from", "-T", "--command-timeout", "-R", "--chroot", "-D", "--chdir"},
                    "stdbuf": {"-i", "--input", "-o", "--output", "-e", "--error"},
                    "chrt": {"-T", "--sched-runtime", "-P", "--sched-period", "-D", "--sched-deadline"},
                    "ionice": {"-c", "--class", "-n", "--classdata", "-p", "--pid", "-P", "--pgid", "-u", "--uid"},
                    "doas": {"-u", "-C"},
                    "runuser": {"-u", "--user", "-g", "--group", "-G", "--supp-group"},
                    "xargs": {"-I", "-L", "--max-lines", "-n", "--max-args", "-P", "--max-procs", "-s", "--max-chars", "-E", "--eof", "-d", "--delimiter", "-a", "--arg-file"},
                    "watch": {"-n", "--interval"},
                }.get(name, set())
                child = index
                unresolved = False
                while child < len(words):
                    option = words[child].replace("\ue003", "")
                    if "\ue002" in option or (option and all(c in ";&|()<>\n" for c in option)):
                        unresolved = True
                        break
                    if option == "--":
                        child += 1
                        break
                    if not option.startswith("-") or option == "-":
                        break
                    child += 1
                    if option in operands:
                        if child >= len(words) or "\ue002" in words[child] or all(c in ";&|()<>\n" for c in words[child]):
                            unresolved = True
                            break
                        child += 1
                    elif option in {"--help", "--version"} or option in {
                        "timeout": {"--foreground", "--preserve-status", "-v", "--verbose"},
                        "sudo": {"-n", "--non-interactive", "-E", "--preserve-env", "-H", "--set-home", "-S", "--stdin", "-b", "--background", "-i", "--login", "-s", "--shell"},
                        "setsid": {"-f", "--fork", "-w", "--wait", "-c", "--ctty"},
                        "chrt": {"-p", "--pid", "-a", "--all-tasks", "-f", "--fifo", "-r", "--rr", "-o", "--other", "-b", "--batch", "-i", "--idle", "-d", "--deadline", "-v", "--verbose"},
                        "ionice": {"-t", "--ignore"},
                        "taskset": {"-c", "--cpu-list", "-p", "--pid", "-a", "--all-tasks"},
                        "doas": {"-n", "-s"},
                        "xargs": {"--replace", "-0", "--null", "-r", "--no-run-if-empty", "-t", "--verbose", "-x", "--exit", "-p", "--interactive"},
                        "watch": {"-t", "--no-title", "-d", "--differences", "-e", "--errexit", "-g", "--chgexit", "-c", "--color", "-x", "--exec", "-p", "--precise"},
                    }.get(name, set()):
                        pass
                    elif any(option.startswith(value + "=") for value in operands if value.startswith("--")) or any(option.startswith(value) and len(option) > len(value) for value in operands if len(value) == 2):
                        pass
                    elif name == "xargs" and option.startswith("--replace="):
                        pass
                    elif name == "nice" and re.fullmatch(r"-[0-9]+", option):
                        pass
                    else:
                        unresolved = True
                        break
                if name in {"timeout", "chrt", "taskset"}:
                    if child >= len(words) or "\ue002" in words[child] or all(c in ";&|()<>\n" for c in words[child]):
                        unresolved = True
                    else:
                        child += 1  # literal duration, priority or CPU mask
                if unresolved:
                    if name == "xargs":
                        raise ValueError("unresolved xargs executable rewriting cannot be inspected")
                    if any("\ue002" in value or git_executable(value.replace("\ue003", "")) or possible_guarded(value.replace("\ue003", ""), depth + 1) for value in words[index:]):
                        raise ValueError("unresolved executable wrapper cannot inspect guarded work")
                    head = False
                    continue
                if name == "xargs":
                    replacements = []
                    for offset, raw_option in enumerate(words[index:child]):
                        option = raw_option.replace("\ue003", "")
                        if option == "-I" and index + offset + 1 < child:
                            replacements.append(words[index + offset + 1].replace("\ue003", ""))
                        elif option.startswith("-I") and len(option) > 2:
                            replacements.append(option[2:])
                        elif option == "--replace":
                            replacements.append("{}")
                        elif option.startswith("--replace="):
                            replacements.append(option.split("=", 1)[1])
                    if replacements:
                        executable = words[child].replace("\ue003", "") if child < len(words) else "echo"
                        if Path(executable).name not in {"echo", "printf"} or any(not token for token in replacements):
                            raise ValueError("xargs rewritten executable or program cannot be inspected")
                watch_shell = name == "watch" and not any(value.replace("\ue003", "") in {"-x", "--exec"} for value in words[index:child])
                if watch_shell:
                    # Default watch concatenates argv without shell quoting.
                    # Reconstruct that program, not shlex.join protected data.
                    if any("\ue002" in value for value in words[child:]):
                        raise ValueError("expanded watch shell program cannot be inspected")
                    program = " ".join(value.replace("\ue003", "") for value in words[child:])
                    if possible_guarded(program, depth + 1):
                        raise ValueError("guarded watch shell program requires a separate literal Git invocation")
                opaque_shell = name == "sudo" and any(value.replace("\ue003", "") in {"-s", "--shell", "-i", "--login"} for value in words[index:child])
                if opaque_shell and child < len(words) and possible_guarded(words[child].replace("\ue003", ""), depth + 1):
                    raise ValueError("opaque wrapper shell program cannot inspect guarded work")
                if possible_guarded(shlex.join(words[child:]), depth + 1, supplied_program=supplied_program or name == "xargs"):
                    raise ValueError("guarded child execution wrapper requires a separate literal Git invocation")
                head = False
                continue
            if name == "function":
                if index >= len(words) or "\ue002" in words[index] or all(c in ";&|()<>\n" for c in words[index]):
                    return True
                # The declaration name is data; the body starts a new executable
                # context. Function bodies containing guarded work are refused.
                index += 1
                head = True
                continue
            if name in {"eval", "source", "."}:
                return True
            if name in {"bash", "sh", "zsh", "dash", "ksh"}:
                # Only inspect a literal -c program; files, stdin and expanded
                # program strings are opaque and remain conservatively guarded.
                for program_index in range(index, len(words)):
                    option = words[program_index].replace("\ue003", "")
                    if option == "--command" or re.fullmatch(
                        r"-[A-Za-z]*c[A-Za-z]*", option
                    ):
                        if program_index + 1 >= len(words):
                            return True
                        program = words[program_index + 1]
                        if "\ue002" in program or possible_guarded(program, depth + 1):
                            return True
                        head = False
                        break
                    if all(c in ";&|()<>\n" for c in option) or not option.startswith(
                        "-"
                    ):
                        break
                if head:
                    return True
                continue
            if git_executable(word):
                while index < len(words):
                    argument = words[index].replace("\ue003", "")
                    if "\ue002" in argument:
                        return True
                    if any(c in "<>" for c in argument) or (
                        argument.isdigit()
                        and index + 1 < len(words)
                        and any(c in "<>" for c in words[index + 1])
                    ):
                        return True
                    if argument and all(c in ";&|()<>\n" for c in words[index]):
                        break
                    if argument in ("-C", "-c", "--git-dir", "--work-tree"):
                        if index + 1 >= len(words) or "\ue002" in words[index + 1] or (words[index + 1] and all(c in ";&|()<>\n" for c in words[index + 1])):
                            return True
                        index += 2
                    elif argument.startswith(
                        ("-C", "-c", "--git-dir=", "--work-tree=")
                    ) or argument in (
                        "--no-pager",
                        "--paginate",
                        "--no-optional-locks",
                        "--literal-pathspecs",
                        "--no-lazy-fetch",
                        "--bare",
                    ):
                        index += 1
                    elif argument in ("--version", "--help", "-h"):
                        break
                    else:
                        if argument.startswith("-") or argument in ("commit", "push"):
                            return True
                        break
            head = False
        return False

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
        wrapper = ""
        operand_pending = False
        for token in words:
            word, operator = (
                token
                if isinstance(token, tuple)
                else (token, bool(token) and all(char in ";&|\n" for char in token))
            )
            if operator:
                if operand_pending:
                    raise ValueError("missing wrapper option operand")
                if any(char in "<>" for char in word) and (
                    at_head or (len(heads) == 1 and heads[0].isdigit())
                ):
                    raise ValueError("unsupported leading shell redirection")
                at_head = True
                wrapped = False
                wrapper = ""
            elif at_head:
                if operand_pending:
                    if getattr(word, "expanded", False):
                        raise ValueError("expanded wrapper option operand")
                    operand_pending = False
                    continue
                if getattr(word, "expanded", False) and not re.match(
                    r"^[A-Za-z_][A-Za-z0-9_]*=", word
                ):
                    raise ValueError("expanded executable cannot be inspected")
                if Path(word).is_absolute():
                    word = Path(word).name
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
                    "coproc",
                    "{",
                    "}",
                }:
                    raise ValueError("unsupported shell control structure")
                if word in {"!", "time"}:
                    wrapped = wrapped or word == "time"
                    if word == "time":
                        wrapper = "time"
                    continue
                if word in {"env", "exec", "command", "builtin"} or re.match(
                    r"^[A-Za-z_][A-Za-z0-9_]*=", word
                ):
                    if word in {"env", "exec"}:
                        heads.append(word)
                    wrapped |= word in {"env", "exec", "command", "builtin"}
                    if word in {"env", "exec", "command", "builtin"}:
                        wrapper = word
                    continue
                if wrapped and word.startswith("-"):
                    operands = {"env": {"-u", "--unset"}, "exec": {"-a"}}
                    flags = {
                        "env": {"-i", "--ignore-environment"},
                        "exec": {"-c", "-l"},
                        "command": {"-p", "-v", "-V"},
                        "builtin": set(),
                        "time": {"-p"},
                    }
                    if word in operands.get(wrapper, set()):
                        operand_pending = True
                    elif word == "--" or word in flags.get(wrapper, set()):
                        pass
                    elif wrapper == "env" and (
                        word.startswith("--unset=")
                        or word.startswith("-u")
                        and len(word) > 2
                    ):
                        pass
                    elif wrapper == "exec" and word.startswith("-a") and len(word) > 2:
                        pass
                    else:
                        raise ValueError("unsupported wrapper option")
                    continue
                heads.append(word if word == "." else Path(word).name)
                at_head = False
        if operand_pending:
            raise ValueError("missing wrapper option operand")
        return heads

    # Heredoc bodies are data unless fed to a shell or containing executable
    # substitutions in an unquoted heredoc. Unsupported delimiter syntax refuses.
    parts = command.split("\n")
    lines = [value + "\n" for value in parts[:-1]] + [parts[-1]]
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
                position == 0 or header[position - 1] in " \t\n;&|()<>"
            ):
                break
            elif header.startswith("<<<", position):
                position += 3
                continue
            elif header.startswith("<<", position):
                match = re.match(
                    r"<<(-?)[ \t]*([\x27][^\x27]*[\x27]|[\x22][^\x22]*[\x22]|[A-Za-z0-9_]+)(?=[ \t\n]|[;&|<>]|$)",
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
            if header_substitution and possible_guarded(header):
                raise ValueError(
                    "heredoc in executable substitution cannot be inspected"
                )
            if quote_state:
                raise ValueError("multiline quoted heredoc header cannot be inspected")
            lexer = shlex.shlex(shell_continuations(header), posix=True, punctuation_chars=";&|<>\n")
            lexer.whitespace = " \t"
            lexer.whitespace_split = True
            lexer.commenters = ""
            if possible_guarded(header) and any(
                head in shells for head in executable_heads(list(lexer))
            ):
                raise ValueError(
                    "heredoc supplied to executable shell cannot be inspected"
                )
        for delimiter, strip_tabs, quoted in documents:
            while line_index < len(lines):
                body = lines[line_index]
                line_index += 1
                code.append("\n")
                literal_body = body[:-1] if body.endswith("\n") else body
                if (literal_body.lstrip("\t") if strip_tabs else literal_body) == delimiter:
                    break
                if (
                    not quoted
                    and ("$(" in body or "`" in body)
                    and inspect_substitutions(body, quote_sensitive=False)[1]
                ):
                    raise ValueError(
                        "executable heredoc substitution cannot be inspected"
                    )
            else:
                raise ValueError("unterminated heredoc")
    command = "".join(code)
    if not possible_guarded(command):
        return []
    if had_documents:
        lexer = shlex.shlex(shell_continuations(command), posix=True, punctuation_chars=";&|<>\n")
        lexer.whitespace = " \t"
        lexer.whitespace_split = True
        lexer.commenters = ""
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
        elif char in "$*?[{~" and not (char == "[" and literal_test_bracket(normalized, position)):
            marked.append(expansion_marker)
        marked.append(char)
    if substitution:
        raise ValueError("executable shell substitution cannot be inspected")
    lexer = shlex.shlex("".join(marked), posix=True, punctuation_chars=";&|()<>\n")
    lexer.whitespace = " \t"
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
    pipeline_pending = False
    for word, operator in tokens + [(";", True)]:
        if operator and word.replace("\n", "") in ("|", "|&"):
            group.append((word, operator))
            pipeline_pending = True
            continue
        if operator and not word.replace("\n", "") and pipeline_pending:
            group.append((word, operator))
            continue
        pipeline_pending = False
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
    mutating_printf = False
    previous_head = ""
    for word, operator in tokens:
        if operator:
            at_head = True
            previous_head = ""
        elif at_head:
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", word):
                continue
            name = word if word == "." else Path(word).name
            if name in ("builtin", "command") or word in ("--", "-p"):
                continue
            heads.append(name)
            previous_head = name
            at_head = False
        elif previous_head:
            mutating_printf |= previous_head == "printf" and word.startswith("-v")
            previous_head = ""
    mutators = ("source", ".", "export", "eval", "env", "exec", "command", "declare", "typeset", "readonly", "local", "unset", "read", "mapfile", "readarray", "set", "setopt", "unsetopt")
    if (any(not operator and word.startswith("GIT_CONFIG") for word, operator in tokens)
            or any(word in mutators for word in heads) or mutating_printf):
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
            if pos + 1 >= len(args) or getattr(args[pos + 1], "expanded", False):
                deny("missing or expanded Git option operand cannot be inspected")
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
