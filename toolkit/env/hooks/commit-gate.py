#!/usr/bin/env python3
"""Claude PreToolUse hook: block commits when TypeScript checking cannot pass."""

import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time


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
            if text.startswith("${", position):
                end = text.find("}", position + 2)
                reference = text[position + 2 : end] if end >= 0 else ""
                indexed = re.match(r"^[A-Za-z_][A-Za-z0-9_]*\[(.*)\]", reference)
                if (
                    indexed
                    and indexed.group(1) not in ("@", "*")
                    and not literal_arithmetic(indexed.group(1))
                ):
                    raise ValueError(
                        "unresolved arithmetic array reference cannot be inspected"
                    )
                sliced = re.match(
                    r"^(?:[A-Za-z_][A-Za-z0-9_]*(?:\[.*?\])?|[@*]):(.*)$", reference
                )
                if sliced and not sliced.group(1).startswith(("-", "+", "=", "?")):
                    parts = sliced.group(1).split(":")
                    if len(parts) > 2 or any(
                        not literal_arithmetic(value or "0") for value in parts
                    ):
                        raise ValueError(
                            "unresolved parameter slice arithmetic cannot be inspected"
                        )
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
        integer_names = set()
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
            indexed_assignment = re.match(
                r"^([A-Za-z_][A-Za-z0-9_]*)\[(.*)\](?:\+?=)", word
            )
            if indexed_assignment and not literal_arithmetic(
                indexed_assignment.group(2)
            ):
                raise ValueError(
                    "unresolved arithmetic array assignment cannot be inspected"
                )
            if indexed_assignment:
                if indexed_assignment.group(
                    1
                ) in integer_names and not literal_arithmetic(
                    word[indexed_assignment.end() :]
                ):
                    raise ValueError(
                        "unresolved integer array value cannot be inspected"
                    )
                continue
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*\+?=", word):
                variable, value = word.split("=", 1)
                variable = variable.rstrip("+")
                if variable in integer_names and (
                    expanded or not literal_arithmetic(value)
                ):
                    raise ValueError(
                        "unresolved integer variable assignment cannot be inspected"
                    )
                # Literal array contents are data; executable substitutions were
                # already inspected recursively before this token walk.
                if index < len(words) and words[index] == "(":
                    balance = 1
                    index += 1
                    while index < len(words) and balance:
                        punctuation = words[index]
                        # Unquoted [index]=value in a compound assignment
                        # evaluates the index. Whole quoted words remain data.
                        if not punctuation.startswith("\ue003"):
                            indexed = re.match(
                                r"^\[(.*)\]\+?=",
                                punctuation.replace("\ue002", "").replace("\ue003", ""),
                            )
                            if indexed and not literal_arithmetic(indexed.group(1)):
                                raise ValueError(
                                    "unresolved compound array index cannot be inspected"
                                )
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
            if name in {"[[", "[", "test"}:
                end = index
                terminator = "]]" if name == "[[" else "]"
                while end < len(words):
                    token = words[end].replace("\ue003", "")
                    if name != "test" and token == terminator:
                        break
                    if words[end] and all(c in ";&|()<>\n" for c in words[end]):
                        if name == "[":
                            raise ValueError("single-bracket condition crossed shell boundary")
                        if name == "test":
                            break
                    end += 1
                if name != "test" and end == len(words):
                    raise ValueError("unterminated conditional cannot be inspected")
                operands = words[index:end]
                for offset, operand in enumerate(operands):
                    if operand.replace("\ue003", "") in {"-v", "-R"}:
                        if offset + 1 == len(operands):
                            raise ValueError("missing conditional variable target")
                        target = operands[offset + 1].replace("\ue003", "")
                        indexed = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)\[(.*)\]", target)
                        if indexed:
                            if not literal_arithmetic(indexed.group(2)):
                                raise ValueError("unresolved conditional variable index cannot be inspected")
                        elif not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", target):
                            raise ValueError("unresolved conditional variable target cannot be inspected")
                    if operand.replace("\ue003", "") in {
                        "-eq",
                        "-ne",
                        "-lt",
                        "-le",
                        "-gt",
                        "-ge",
                    }:
                        if (
                            offset == 0
                            or offset + 1 == len(operands)
                            or any(
                                "\ue002" in value
                                or not literal_arithmetic(value.replace("\ue003", ""))
                                for value in (
                                    operands[offset - 1],
                                    operands[offset + 1],
                                )
                            )
                        ):
                            raise ValueError(
                                "unresolved conditional arithmetic cannot be inspected"
                            )
                index = end if name == "test" else end + 1
                head = False
                continue
            if name in {"declare", "typeset", "local", "export", "readonly", "unset"}:
                end = index
                while end < len(words) and not (
                    words[end] and all(c in ";&|()<>\n" for c in words[end])
                ):
                    end += 1
                arguments = [value.replace("\ue003", "") for value in words[index:end]]
                integer = any(
                    value.startswith("-") and "i" in value for value in arguments
                )
                if any(value.startswith("-") and "n" in value for value in arguments):
                    raise ValueError(
                        "indirect variable declaration cannot be inspected"
                    )
                for argument in arguments:
                    if argument.startswith("-") or argument == "--":
                        continue
                    indexed = re.match(
                        r"^(?:[A-Za-z_][A-Za-z0-9_]*)?\[(.*)\](?:\+?=.*)?$", argument
                    )
                    if indexed and not literal_arithmetic(indexed.group(1)):
                        raise ValueError(
                            "unresolved builtin arithmetic array index cannot be inspected"
                        )
                    if integer:
                        variable, separator, value = argument.partition("=")
                        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", variable) or (
                            separator
                            and ("\ue002" in value or not literal_arithmetic(value))
                        ):
                            raise ValueError(
                                "unresolved integer declaration cannot be inspected"
                            )
                        integer_names.add(variable)
                index = end
                head = False
                continue
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
            if name in {"printf", "read", "mapfile", "readarray"}:
                end = index
                while end < len(words) and not (
                    words[end] and all(c in ";&|()<>\n" for c in words[end])
                ):
                    end += 1
                operands = [value.replace("\ue003", "") for value in words[index:end]]
                if name == "printf" and operands and operands[0].startswith("-v"):
                    if operands[0] == "-v":
                        if len(operands) < 2:
                            raise ValueError("missing printf variable target")
                        target, values = operands[1], operands[2:]
                    else:
                        target, values = operands[0][2:], operands[1:]
                    indexed = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)\[(.*)\]", target)
                    if indexed:
                        if not literal_arithmetic(indexed.group(2)):
                            raise ValueError("unresolved printf arithmetic array target")
                        variable = indexed.group(1)
                    elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", target):
                        variable = target
                    else:
                        raise ValueError("unresolved printf variable target")
                    # Integer variable writes evaluate the resulting string as
                    # Bash arithmetic. Prove only this simple literal format;
                    # unresolved formats/values run in a separate invocation.
                    if variable in integer_names and not (
                        len(values) == 2 and values[0] == "%s"
                        and literal_arithmetic(values[1])
                    ):
                        raise ValueError("unresolved printf integer assignment")
                elif name != "printf":
                    # Parse builtin option operands before treating remaining
                    # words as destinations. Prompt/delimiter text stays data;
                    # callback options are execution and are always refused.
                    targets = []
                    position = 0
                    value_options = "adinNptu" if name == "read" else "nOsucCd"
                    while position < len(operands):
                        option = operands[position]
                        position += 1
                        if option == "--":
                            targets.extend(operands[position:])
                            break
                        if not option.startswith("-") or option == "-":
                            targets.extend(operands[position - 1:])
                            break
                        for offset, flag in enumerate(option[1:], 1):
                            if name != "read" and flag == "C":
                                raise ValueError("input builtin callback execution cannot be inspected")
                            if flag in value_options:
                                value = option[offset + 1:]
                                if not value:
                                    if position >= len(operands):
                                        raise ValueError("missing input builtin option operand")
                                    value = operands[position]
                                    position += 1
                                if name == "read" and flag == "a":
                                    targets.append(value)
                                break
                    targets = targets or (["REPLY"] if name == "read" else ["MAPFILE"])
                    for target in targets:
                        indexed = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)\[(.*)\]", target)
                        variable = indexed.group(1) if indexed else target
                        if indexed:
                            _, guarded = inspect_substitutions(indexed.group(2), depth + 1, quote_sensitive=False)
                            if guarded or not literal_arithmetic(indexed.group(2)):
                                raise ValueError("unresolved input destination arithmetic cannot be inspected")
                        elif not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", target):
                            raise ValueError("unresolved input builtin variable target")
                        if variable in integer_names:
                            raise ValueError("unresolved input builtin integer assignment")
                head = False
                continue
            if name == "trap":
                end = index
                while end < len(words) and not (
                    words[end] and all(c in ";&|()<>\n" for c in words[end])
                ):
                    end += 1
                operands = [value.replace("\ue003", "") for value in words[index:end]]
                if operands and operands[0] == "--":
                    operands = operands[1:]
                if operands and operands[0] not in {"-p", "-l", "-", ""}:
                    if any("\ue002" in value for value in operands) or possible_guarded(
                        operands[0], depth + 1, supplied_program=True
                    ):
                        raise ValueError(
                            "trap callback requires a separate literal invocation"
                        )
                index = end
                head = False
                continue
            if name == "find":
                position = index
                valued = {
                    "-name",
                    "-iname",
                    "-path",
                    "-ipath",
                    "-wholename",
                    "-iwholename",
                    "-regex",
                    "-iregex",
                    "-type",
                    "-xtype",
                    "-user",
                    "-uid",
                    "-group",
                    "-gid",
                    "-perm",
                    "-size",
                    "-links",
                    "-inum",
                    "-samefile",
                    "-newer",
                    "-anewer",
                    "-cnewer",
                    "-newermt",
                    "-maxdepth",
                    "-mindepth",
                    "-mtime",
                    "-ctime",
                    "-atime",
                    "-mmin",
                    "-cmin",
                    "-amin",
                    "-fstype",
                    "-printf",
                    "-fprint",
                    "-fprint0",
                    "-fls",
                }
                while position < len(words):
                    option = words[position].replace("\ue003", "")
                    if option in {";", "&", "&&", "|", "||", "\n"}:
                        break
                    position += 1
                    if option in valued or option == "-fprintf":
                        count = 2 if option == "-fprintf" else 1
                        for unused in range(count):
                            if position >= len(words) or (
                                words[position]
                                and all(char in ";&|()<>\n" for char in words[position])
                            ):
                                raise ValueError(
                                    "missing find operand before shell boundary"
                                )
                            position += 1
                    elif option in {"-exec", "-execdir", "-ok", "-okdir"}:
                        child = position
                        while position < len(words) and words[position].replace(
                            "\ue003", ""
                        ) not in {";", "+"}:
                            if words[position] and all(
                                char in ";&|()<>\n" for char in words[position]
                            ):
                                raise ValueError("find action crossed shell boundary")
                            position += 1
                        if position == len(words) or child == position:
                            raise ValueError("unresolved find execution action")
                        if words[position] == ";":
                            raise ValueError(
                                "unescaped find action terminator is a shell boundary"
                            )
                        argv = [
                            value.replace("\ue003", "")
                            for value in words[child:position]
                        ]
                        if any("\ue002" in value for value in argv) or possible_guarded(
                            shlex.join(argv), depth + 1, supplied_program=True
                        ):
                            raise ValueError(
                                "find callback requires a separate literal invocation"
                            )
                        position += 1
                index = position
                head = False
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
                    executable = (
                        words[child].replace("\ue003", "")
                        if child < len(words)
                        else "echo"
                    )
                    if "\ue002" in executable or Path(executable).name not in {
                        "echo",
                        "printf",
                    }:
                        raise ValueError(
                            "xargs supplied execution is not proven inert printing"
                        )
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
                for operand in words[index:]:
                    if operand and all(c in ";&|()<>\n" for c in operand):
                        break
                    option = operand.replace("\ue003", "")
                    option_name = option.partition("=")[0]
                    if len(option_name) > 2 and any(
                        flag.startswith(option_name)
                        for flag in ("--receive-pack", "--exec")
                    ):
                        raise ValueError(
                            "custom Git transport programs cannot be inspected"
                        )
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
                    if argument == "-c" or (argument.startswith("-c") and len(argument) > 2):
                        value = argument[2:]
                        if argument == "-c":
                            if index + 1 >= len(words):
                                raise ValueError("missing inline Git configuration")
                            index += 1
                            value = words[index].replace("\ue003", "")
                        if "\ue002" in value or not value.lower().startswith("core.commentchar="):
                            raise ValueError("inline Git configuration effects cannot be inspected")
                        index += 1
                    elif argument in ("-C", "--git-dir", "--work-tree"):
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
                # Bash joins unquoted heredoc continuations before expansion or
                # delimiter recognition. Inspect the same logical line.
                while (
                    not quoted
                    and body.endswith("\n")
                    and (len(body[:-1]) - len(body[:-1].rstrip(chr(92)))) % 2
                ):
                    if line_index >= len(lines):
                        raise ValueError("unterminated heredoc continuation")
                    body = body[:-2] + lines[line_index]
                    line_index += 1
                    code.append("\n")
                literal_body = body[:-1] if body.endswith("\n") else body
                if (literal_body.lstrip("\t") if strip_tabs else literal_body) == delimiter:
                    break
                if (
                    not quoted
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
    git_queries = {}
    readonly_contexts = {}
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
        if (
            len(effective_args) > 1
            and effective_args[0] == "printf"
            and effective_args[1].startswith("-v")
        ):
            uncertain_cwd = True
        if assignment_count and assigned_args:
            if assigned_args[0] in ("cd", "pushd", "popd") or (
                assigned_args[0] in ("builtin", "command")
                and any(word in ("cd", "pushd", "popd") for word in assigned_args[1:])
            ):
                uncertain_cwd = True
        if not assigned_args and any(word.split("=", 1)[0] in ("CDPATH", "HOME", "XDG_CONFIG_HOME", "OLDPWD", "PWD") or word.split("=", 1)[0].startswith("GIT_") for word in args[:assignment_count]) or (
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
            # Expanded preambles can assign shell variables (${NAME:=value})
            # even when their executable only prints. Unknown expansions run
            # separately so directory and Git environment state remain bound.
            if any(getattr(word, "expanded", False) for word in args):
                uncertain_cwd = True
            if effective_args and effective_args[0] == "printf":
                format_args = effective_args[1:]
                if format_args and format_args[0] == "--":
                    format_args = format_args[1:]
                if format_args and re.search(r"%(?:[0-9]+\$)?[-+ #0]*(?:[0-9]+|\*)?(?:\.(?:[0-9]+|\*))?n", format_args[0].replace("%%", "")):
                    uncertain_cwd = True
            # A preceding program could alter Git configuration between this
            # read-only query and the later commit. Keep uncertain programs in
            # separate hook invocations; unrelated commands without commits are
            # unaffected. Literal printing and simple tests do not mutate state.
            if effective_args and effective_args[0] not in ("printf", "echo", "pwd", "true", "false", "test", "["):
                uncertain_cwd = True
            if any(git_executable(word) for word in args) and "commit" in args:
                raise ValueError(
                    "use a literal Git command so the commit directory can be checked"
                )
            continue
        target = directory
        worktree = None
        gitdir = None
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
                    gitdir = value
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
                gitdir = flag.split("=", 1)[1]
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
        if position < len(args) and args[position] != "commit":
            subcommand = args[position]
            options = args[position + 1:]
            literal = not any(getattr(word, "expanded", False) for word in options)
            no_pager = "--no-pager" in args[1:position]
            safe_status = {"--short", "-s", "--branch", "-b", "--porcelain", "--porcelain=v1", "--porcelain=v2", "--untracked-files=no", "-uno", "--ignored=no", "--no-renames", "--ignore-submodules=all"}
            safe_diff = {"--no-ext-diff", "--no-textconv", "--stat", "--name-only", "--name-status", "--no-patch", "-s", "--oneline", "--no-color", "--color=never", "--no-renames"}
            readonly = False
            if subcommand == "status":
                readonly = literal and all(word in safe_status for word in options)
            elif subcommand == "config":
                readonly = literal and len(options) == 2 and options[0] in ("--get", "--get-all") and bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9.-]*", options[1]))
            elif subcommand == "rev-parse":
                readonly = literal and bool(options) and all(word in ("--show-toplevel", "--show-prefix", "--is-inside-work-tree", "--git-dir") for word in options)
            elif subcommand in ("diff", "show", "log"):
                # Diff drivers, textconv and pagers can execute programs by default.
                # Output paths and unknown options cannot be considered read-only.
                readonly = literal and no_pager and "--no-ext-diff" in options and "--no-textconv" in options and all(word in safe_diff for word in options)
            # grep and every unresolved command/option use separate invocations.
            readonly &= not config_worktree
            uncertain_cwd |= not readonly
            if readonly:
                prefix = ["git", "--no-pager", "-C", str(target)]
                if gitdir is not None:
                    prefix += ["--git-dir", str((target / gitdir).resolve())]
                if worktree is not None:
                    prefix += ["--work-tree", str((target / worktree).resolve())]
                keys = ["core.fsmonitor"] + ([] if no_pager else ["pager." + subcommand])
                pattern = "^(" + "|".join(re.escape(key) for key in keys) + ")$"
                readonly_contexts[(tuple(prefix), pattern)] = keys
        if position < len(args) and args[position] == "commit":
            if any(getattr(word, "expanded", False) for word in args[position + 1:]):
                raise ValueError("expanded commit operands cannot establish unchanged Git environment")
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
            invocation_directory = target
            if worktree is not None:
                target = (target / worktree).resolve()
            if not target.is_dir():
                raise ValueError("commit directory does not exist")
            target_record = (target, worktree is not None)
            query = ["git", "-C", str(invocation_directory)]
            if gitdir is not None:
                query += ["--git-dir", str((invocation_directory / gitdir).resolve())]
            if worktree is not None:
                query += ["--work-tree", str(target)]
            git_queries[target_record] = query + ["rev-parse", "--show-toplevel"]
            if target_record not in targets:
                targets.append(target_record)
    if len(targets) > 1:
        raise ValueError(
            "multiple distinct commit targets require separate hook invocations"
        )
    if not targets:
        return []
    # Every read-only Git probe shares one three-second budget, followed by the
    # existing sixty-second compiler budget. A long command chain cannot multiply
    # query timeouts past the documented seventy-second hook minimum.
    query_deadline = time.monotonic() + 3
    def git_probe(query):
        remaining = query_deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("Git inspection budget exhausted")
        process = subprocess.Popen(query, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, stderr = process.communicate(timeout=remaining)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=1)
            raise ValueError("Git worktree query timed out")
        return process.returncode, stdout, stderr
    for (prefix, pattern), keys in readonly_contexts.items():
        code, output, error = git_probe(list(prefix) + ["config", "--null", "--get-regexp", pattern])
        if code == 1 or code == 128 and error.startswith(b"fatal: not a git repository"):
            continue
        if code != 0:
            raise ValueError("prior Git configured execution cannot be established")
        for entry in os.fsdecode(output).rstrip("\0").split("\0"):
            key, separator, value = entry.partition("\n")
            if not separator or key not in keys or value.strip().lower() not in ("false", "0", "no", "off"):
                raise ValueError("prior Git configured execution requires a separate invocation")
    resolved_targets = []
    for target, explicit in targets:
        code, stdout, stderr = git_probe(git_queries[(target, explicit)])
        if code:
            # Git discovery itself, rather than a missing .git child, establishes
            # a nonrepository. Other failures remain an explicit refusal.
            if code == 128 and not stdout and stderr.startswith(b"fatal: not a git repository"):
                resolved_targets.append((target, explicit))
                continue
            raise ValueError("actual Git worktree cannot be established")
        if not stdout.endswith(b"\n") or stdout.count(b"\n") != 1 or not stdout[:-1]:
            raise ValueError("actual Git worktree output is ambiguous")
        actual = Path(os.fsdecode(stdout[:-1])).resolve(strict=True)
        if not actual.is_dir():
            raise ValueError("actual Git worktree is not a directory")
        # Preserve package/subdirectory selection within the verified worktree.
        # Stored core.worktree may instead redirect to a separate directory.
        direct_git_directory = False
        for ancestor in (target, *target.parents):
            if ancestor == actual:
                break
            if (ancestor / "HEAD").is_file() and ((ancestor / "objects").is_dir() or (ancestor / "commondir").is_file()):
                direct_git_directory = True
                break
        if explicit or direct_git_directory or actual not in (target, *target.parents):
            target, explicit = actual, True
        resolved_targets.append((target, actual))
    return resolved_targets


def typescript_directory(directory, worktree_boundary):
    """Preserve package selection within Git's verified actual worktree root."""
    boundary = worktree_boundary if isinstance(worktree_boundary, Path) else (directory if worktree_boundary else None)
    # A proven nonrepository may retain a standalone direct compiler probe, but
    # never discover unrelated parent projects from independent .git markers.
    if boundary is None:
        return directory if (directory / "tsconfig.json").is_file() else None
    if boundary not in (directory, *directory.parents):
        raise ValueError("compiler path lies outside verified Git worktree")
    for candidate in (directory, *directory.parents):
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
            errors="replace",
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
