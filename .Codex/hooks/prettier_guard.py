#!/usr/bin/env python3
"""在项目命令执行前阻止显式 Prettier 调用。"""

from __future__ import annotations

import json
import re
import shlex
import sys
from pathlib import Path
from typing import Iterable, Mapping, TextIO

TARGET_TOOL_NAMES = frozenset(
    {"Bash", "Shell", "exec_command", "functions.exec"}
)
COMMAND_KEYS = ("command", "cmd")
SOURCE_KEYS = ("source", "code", "script", "input")
SHELL_EXECUTABLES = frozenset({"bash", "sh", "zsh"})
PACKAGE_RUNNERS = frozenset({"npx", "bunx"})
PACKAGE_MANAGERS = frozenset({"npm", "pnpm", "yarn"})
PACKAGE_OPTIONS_WITH_VALUE = frozenset(
    {
        "--package",
        "--prefix",
        "--registry",
        "--userconfig",
        "-C",
        "-c",
        "-p",
    }
)
JS_COMMAND_PATTERN = re.compile(
    r"\bcmd\s*:\s*(?P<quote>['\"`])(?P<body>(?:\\.|(?!\1).)*)(?P=quote)",
    re.DOTALL,
)


def _basename(token: str) -> str:
    return Path(token).name.lower()


def _is_prettier_name(token: str) -> bool:
    name = _basename(token)
    return name == "prettier" or name.startswith("prettier@")


def _shell_tokens(text: str) -> list[str]:
    try:
        lexer = shlex.shlex(text, posix=True, punctuation_chars=";&|()")
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer)
    except ValueError:
        return []


def _command_segments(text: str, depth: int = 0) -> list[list[str]]:
    """提取命令位置，并展开常见 Shell 与 ``eval`` 包装。"""
    if depth > 3:
        return []
    tokens = _shell_tokens(text)
    if not tokens:
        return []

    separators = {";", "&&", "||", "|", "(", ")"}
    raw_segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in separators:
            if current:
                raw_segments.append(current)
                current = []
            continue
        current.append(token)
    if current:
        raw_segments.append(current)

    segments: list[list[str]] = []
    for raw in raw_segments:
        index = 0
        while index < len(raw) and re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_]*=.*", raw[index]
        ):
            index += 1
        if index >= len(raw):
            continue

        if _basename(raw[index]) == "env":
            index += 1
            while index < len(raw) and (
                raw[index].startswith("-")
                or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", raw[index])
            ):
                index += 1

        if index < len(raw) and _basename(raw[index]) in {"command", "sudo"}:
            if _basename(raw[index]) == "command" and (
                index + 1 < len(raw) and raw[index + 1] == "-v"
            ):
                continue
            index += 1
            while index < len(raw) and raw[index].startswith("-"):
                index += 1
        if index >= len(raw):
            continue

        argv = raw[index:]
        segments.append(argv)
        executable = _basename(argv[0])
        if executable in SHELL_EXECUTABLES:
            for option_index, option in enumerate(argv[1:], start=1):
                if option in {"-c", "-lc"} and option_index + 1 < len(argv):
                    segments.extend(
                        _command_segments(argv[option_index + 1], depth + 1)
                    )
                    break
        elif executable == "eval" and len(argv) > 1:
            segments.extend(_command_segments(" ".join(argv[1:]), depth + 1))
    return segments


def _skip_options(argv: list[str], start: int) -> int:
    index = start
    while index < len(argv):
        token = argv[index]
        if token == "--":
            return index + 1
        if not token.startswith("-"):
            return index
        option = token.split("=", 1)[0]
        index += 1
        if "=" not in token and option in PACKAGE_OPTIONS_WITH_VALUE:
            index += 1
    return index


def _explicit_prettier_invocation(argv: list[str]) -> bool:
    if not argv:
        return False
    executable = _basename(argv[0])
    if _is_prettier_name(argv[0]):
        return True

    if executable == "corepack" and len(argv) > 1:
        return _explicit_prettier_invocation(argv[1:])

    if executable in PACKAGE_RUNNERS:
        target_index = _skip_options(argv, 1)
        return target_index < len(argv) and _is_prettier_name(argv[target_index])

    if executable not in PACKAGE_MANAGERS:
        if executable in {"node", "nodejs"} and len(argv) > 1:
            normalized = argv[1].replace("\\", "/").lower()
            return "/prettier/bin/prettier" in normalized
        return False

    command_index = _skip_options(argv, 1)
    if command_index >= len(argv):
        return False
    command = argv[command_index].lower()

    if executable == "npm":
        if command in {"exec", "x"}:
            target_index = _skip_options(argv, command_index + 1)
            return target_index < len(argv) and _is_prettier_name(argv[target_index])
        if command in {"run", "run-script"}:
            target_index = _skip_options(argv, command_index + 1)
            return target_index < len(argv) and _is_prettier_name(argv[target_index])
        return False

    if command in {"exec", "dlx", "run"}:
        target_index = _skip_options(argv, command_index + 1)
        return target_index < len(argv) and _is_prettier_name(argv[target_index])
    return _is_prettier_name(argv[command_index])


def inspect_command(text: str) -> bool:
    return any(
        _explicit_prettier_invocation(argv) for argv in _command_segments(text)
    )


def _decode_js_command(quote: str, body: str) -> str:
    if quote == '"':
        try:
            decoded = json.loads(f'"{body}"')
        except json.JSONDecodeError:
            return body
        return decoded if isinstance(decoded, str) else body
    replacements = {
        r"\\'": "'",
        r'\\"': '"',
        r"\\`": "`",
        r"\\\\": "\\",
        r"\\n": "\n",
        r"\\r": "\r",
        r"\\t": "\t",
    }
    decoded = body
    for encoded, value in replacements.items():
        decoded = decoded.replace(encoded, value)
    return decoded


def _text_values(value: object, keys: Iterable[str]) -> list[str]:
    if isinstance(value, str):
        return [value]
    if not isinstance(value, Mapping):
        return []
    return [
        candidate
        for key in keys
        if isinstance((candidate := value.get(key)), str)
    ]


def extract_command_texts(payload: Mapping[str, object]) -> list[str]:
    tool_name = payload.get("tool_name")
    if tool_name not in TARGET_TOOL_NAMES:
        return []
    tool_input = payload.get("tool_input")
    if tool_name != "functions.exec":
        return _text_values(tool_input, COMMAND_KEYS)

    commands: list[str] = []
    for source in _text_values(tool_input, SOURCE_KEYS):
        commands.extend(
            _decode_js_command(match.group("quote"), match.group("body"))
            for match in JS_COMMAND_PATTERN.finditer(source)
        )
    return commands


def deny_output() -> dict[str, object]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "[P0-NO-PRETTIER] 本仓库禁止运行 Prettier，"
                "包括直接调用和常见包管理器包装调用。"
            ),
        }
    }


def handle_hook_input(stream: TextIO) -> dict[str, object] | None:
    try:
        payload = json.load(stream)
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(payload, dict) or payload.get("hook_event_name") not in {
        None,
        "PreToolUse",
    }:
        return None
    return (
        deny_output()
        if any(inspect_command(text) for text in extract_command_texts(payload))
        else None
    )


def main() -> int:
    output = handle_hook_input(sys.stdin)
    if output is not None:
        json.dump(output, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
