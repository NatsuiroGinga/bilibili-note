#!/usr/bin/env python3
"""拦截会自匹配的 ``pgrep -f`` / ``pkill -f`` 调用。

``pgrep -f PATTERN`` / ``pkill -f PATTERN`` 按完整命令行匹配进程。发起该命令的
包装 shell（或其父进程）自己的命令行里就原样含有 PATTERN 这段文本，所以只要
PATTERN 是一段静态字面量（不含字符类技巧），这条命令就必然会匹配到自己，
而不只是匹配目标进程。

本条采用**阻断**（deny），不是本仓库默认的「披露优先于阻断」：它防的不是性能
或风格问题，而是**一个错误事实进入推理链**——目标进程其实已经退出，
``pgrep`` 却因为匹配到自己（或包装 shell）而报告「仍在运行」，据此写入的
任何判断（是否重复启动、是否已清理、是否可以继续）都建立在假前提上，
且难以事后察觉（命令本身不报错，只是结果误导）。判定条件本身很精确
（见下）、假阳性可控，修法只需把模式串中任意一个字符包一层字符类
（如 ``x`` -> ``[x]``），一行可改，不构成额外负担。

事故依据：本会话内 ``pgrep -f``/``pkill -f`` 自匹配连续踩坑 5 次，最近一次的
后果是目标进程已死、``pgrep -f lspr24_descriptive_eval`` 却因匹配到发起该
命令的 bash 包装进程而回报「进程仍在运行」，把一个错误事实带进了后续判断。

判定只在**确定会自匹配**时触发，其余一律放行、不猜：

1. 命令中出现 ``pgrep``/``pkill``，且带 ``-f``（含 ``-af``、``-lf`` 等组合
   短选项）。
2. 取出其模式参数（可能带单引号、双引号或裸写，取消引号后的字面内容）。
3. 模式串本身在整条命令原文中确有出现——这一点由「模式是从命令原文中静态
   提取」保证成立，不需要额外证据。
4. 模式已含字符类 ``[...]`` 的（用户已用括号技巧），一律放行。
5. 模式来自变量（含 ``$``、反引号等无法静态展开的片段）或无法静态确定
   options/positional 边界的，一律放行，不猜测其运行时取值。

若本钩子连续两次拦下本可正常进行的命令（即命令实际不会自匹配，或自匹配
不会导致误判），按仓库「披露优先于阻断」的默认规则，应把本钩子降级为
仅注入提醒（不再 deny），不得继续阻断。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Iterable, Mapping, TextIO

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prettier_guard import _basename, _command_segments  # noqa: E402

TARGET_TOOL_NAMES = frozenset({"Bash", "Shell", "exec_command", "functions.exec"})
COMMAND_KEYS = ("command", "cmd")

# 会消耗下一个 token（或本 token 剩余部分）作为取值的短选项字母，取
# BSD（macOS 内置 pgrep/pkill）与 GNU procps-ng 已知取值选项字母的并集。
# 不含小写 'f'，故不会与「是否出现 -f」的判定冲突。
VALUE_TAKING_SHORT_OPTIONS = frozenset({"F", "G", "P", "U", "d", "g", "t", "u", "s"})

# 会消耗独立下一个 token 作为取值的长选项；未在此列表且不含 '=' 的长选项
# 一律当作零参数标志处理（宁可漏检，不可误判）。
VALUE_TAKING_LONG_OPTIONS = frozenset(
    {
        "--pidfile",
        "--group",
        "--pgroup",
        "--parent",
        "--session",
        "--terminal",
        "--euid",
        "--uid",
        "--ns",
        "--nslist",
        "--delimiter",
        "--signal",
    }
)

# 包在字符类里语义不变的「安全字符」：字母、数字、下划线。
_SAFE_BRACKET_CHAR = re.compile(r"[A-Za-z0-9_]")
_REGEX_METACHARS = frozenset(".^$*+?()[]{}|\\")


def _extract_pgrep_pattern(argv: list[str]) -> tuple[bool, str | None]:
    """解析 pgrep/pkill 的 argv，返回 (是否带 -f, 模式位置参数或 None)。

    只做保守解析：任何无法确定的分支都直接停止取值提取（返回
    ``pattern=None``），交由调用方按「无法静态确定即放行」处理。
    """
    has_f = False
    index = 1
    length = len(argv)
    while index < length:
        token = argv[index]
        if token == "--":
            index += 1
            break
        if token.startswith("--"):
            name = token.split("=", 1)[0]
            if name == "--full":
                has_f = True
            if name in VALUE_TAKING_LONG_OPTIONS and "=" not in token:
                index += 1
            index += 1
            continue
        if token.startswith("-") and len(token) > 1:
            letters = token[1:]
            j = 0
            while j < len(letters):
                ch = letters[j]
                if ch == "f":
                    has_f = True
                if ch in VALUE_TAKING_SHORT_OPTIONS:
                    if j == len(letters) - 1:
                        index += 1
                    break
                j += 1
            index += 1
            continue
        break

    pattern = argv[index] if index < length else None
    return has_f, pattern


def _is_dynamic_pattern(pattern: str) -> bool:
    """模式含变量展开、命令替换等无法静态确定的片段。"""
    return "$" in pattern or "`" in pattern


def _has_character_class(pattern: str) -> bool:
    return "[" in pattern and "]" in pattern


def _suggest_bracket_fix(pattern: str) -> str | None:
    """把模式中离中点最近的一个安全字符包成字符类，语义不变。"""
    if not pattern:
        return None
    mid = len(pattern) / 2
    order = sorted(range(len(pattern)), key=lambda i: abs(i - mid))
    for index in order:
        if _SAFE_BRACKET_CHAR.fullmatch(pattern[index]):
            return pattern[:index] + "[" + pattern[index] + "]" + pattern[index + 1 :]
    for index in order:
        if pattern[index] not in _REGEX_METACHARS:
            return pattern[:index] + "[" + pattern[index] + "]" + pattern[index + 1 :]
    return None


def _pgrep_self_match_reason(argv: list[str], full_text: str) -> str | None:
    if not argv or _basename(argv[0]) not in {"pgrep", "pkill"}:
        return None
    has_f, pattern = _extract_pgrep_pattern(argv)
    if not has_f or not pattern:
        return None
    if _is_dynamic_pattern(pattern):
        return None
    if _has_character_class(pattern):
        return None
    if pattern not in full_text:
        return None

    executable = _basename(argv[0])
    suggestion = _suggest_bracket_fix(pattern)
    if suggestion is None:
        return (
            f"{executable} -f 的模式 '{pattern}' 会原样匹配到发起这条命令的 shell "
            "自身，导致目标进程已退出时仍误报「仍在运行」。"
            "请把模式中任意一个字符用字符类包起来（如 x -> [x]）后再运行，"
            "字符类不改变匹配语义。"
        )
    fixed_command = full_text.replace(pattern, suggestion, 1)
    return (
        f"{executable} -f 的模式 '{pattern}' 会原样出现在发起这条命令的 shell 自身"
        "命令行里，因此必然匹配到自己，导致目标进程已退出时仍误报「仍在运行」——"
        "一个错误事实会进入后续判断。"
        f"把模式中一个字符包成字符类即可避免自匹配且不改变匹配语义，"
        f"例如把 '{pattern}' 改成 '{suggestion}'。"
        f"可直接复制的修好命令：{fixed_command}"
    )


def inspect_command(text: str) -> str | None:
    """返回拦截理由；命令可放行时返回 ``None``。"""
    for argv in _command_segments(text):
        reason = _pgrep_self_match_reason(argv, text)
        if reason is not None:
            return reason
    return None


def _text_values(value: object, keys: Iterable[str]) -> list[str]:
    if isinstance(value, str):
        return [value]
    if not isinstance(value, Mapping):
        return []
    return [
        candidate for key in keys if isinstance((candidate := value.get(key)), str)
    ]


def extract_command_texts(payload: Mapping[str, object]) -> list[str]:
    if payload.get("tool_name") not in TARGET_TOOL_NAMES:
        return []
    return _text_values(payload.get("tool_input"), COMMAND_KEYS)


def deny_output(reason: str) -> dict[str, object]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"[P0-NO-PGREP-SELF-MATCH] {reason}",
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
    for text in extract_command_texts(payload):
        reason = inspect_command(text)
        if reason is not None:
            return deny_output(reason)
    return None


def main() -> int:
    output = handle_hook_input(sys.stdin)
    if output is not None:
        json.dump(output, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
