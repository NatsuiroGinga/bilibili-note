#!/usr/bin/env python3
"""阻止用 ``sleep`` 空等轮询。

本仓库禁止占住回合空等：等待应当用后台任务（命令自身 ``run_in_background``）或
立即返回的只读检查，让运行时在完成时回调，而不是让代理阻塞在 ``sleep`` 上。

两类拦截：

1. **长 sleep**——单次休眠超过 ``MAX_SLEEP_SECONDS`` 秒。短休眠（例如
   ``pkill`` 后 ``sleep 3`` 等进程退出）属于正常同步手段，不拦。
2. **循环内 sleep**——命令同时出现循环关键字与 ``sleep``，无论秒数多小，
   都是轮询模式。

事故依据：2026-09-02 一个 ``sleep 150`` 的 shell 监视着早已结束的进程，
白占一个后台槽位；同日主代理亦用 ``sleep 200`` 空等守护重起。
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

# 超过该秒数的单次休眠视为空等。短休眠仍允许，用于进程退出、文件落盘等真实同步。
MAX_SLEEP_SECONDS = 30.0

# 循环关键字：出现循环且含 sleep 即为轮询，与秒数无关。
LOOP_PATTERN = re.compile(r"\b(?:while|until|for)\b")

_SUFFIX_FACTORS = {"s": 1.0, "m": 60.0, "h": 3600.0, "d": 86400.0}


def _sleep_seconds(token: str) -> float | None:
    """把 ``sleep`` 的时长参数换算成秒；无法解析时返回 ``None``。"""
    match = re.fullmatch(r"(\d+(?:\.\d+)?)([smhd]?)", token)
    if match is None:
        return None
    value = float(match.group(1))
    return value * _SUFFIX_FACTORS[match.group(2) or "s"]


def _long_sleep(argv: list[str]) -> float | None:
    """命令是长休眠时返回其秒数，否则返回 ``None``。"""
    if not argv or _basename(argv[0]) != "sleep":
        return None
    total = 0.0
    seen = False
    for token in argv[1:]:
        seconds = _sleep_seconds(token)
        if seconds is None:
            # 形如 `sleep $VAR` 的动态时长无法静态判定，按保守策略放行。
            return None
        total += seconds
        seen = True
    if not seen:
        return None
    return total if total > MAX_SLEEP_SECONDS else None


def _mentions_sleep(argv: list[str]) -> bool:
    """段内是否出现 ``sleep``。

    不能只看首 token：``for i in 1 2 3; do sleep 5; done`` 里 ``do`` 与
    ``sleep`` 同段，首 token 是 ``do``；``while`` 形式因分号断句才恰好首位。
    循环体的写法不该决定拦不拦，故整段扫描。
    """
    return any(_basename(token) == "sleep" for token in argv)


def _polling_loop(text: str) -> bool:
    """命令是否为「循环 + sleep」的轮询模式。"""
    if not LOOP_PATTERN.search(text):
        return False
    return any(_mentions_sleep(argv) for argv in _command_segments(text))


def inspect_command(text: str) -> str | None:
    """返回拦截理由；命令可放行时返回 ``None``。"""
    if _polling_loop(text):
        return (
            "命令在循环中使用 sleep 轮询。改用后台任务"
            "（Bash 工具的 run_in_background）让运行时在完成时通知，"
            "或改为一次立即返回的只读检查。"
        )
    for argv in _command_segments(text):
        seconds = _long_sleep(argv)
        if seconds is not None:
            return (
                f"命令休眠 {seconds:g} 秒，超过 {MAX_SLEEP_SECONDS:g} 秒上限。"
                "本仓库禁止占住回合空等：改用后台任务"
                "（Bash 工具的 run_in_background），"
                "或立即做一次只读检查后结束本回合。"
                f"确需短暂同步（等进程退出、等文件落盘）时，"
                f"用不超过 {MAX_SLEEP_SECONDS:g} 秒的休眠。"
            )
    return None


def _text_values(value: object, keys: Iterable[str]) -> list[str]:
    if isinstance(value, str):
        return [value]
    if not isinstance(value, Mapping):
        return []
    return [
        candidate for key in keys if isinstance((candidate := value.get(key)), str)
    ]


def _runs_in_background(tool_input: object) -> bool:
    """命令是否跑在后台。

    禁令针对的是「占住回合空等」；后台任务不占回合，运行时会在它结束时回调，
    所以后台里的等待与轮询是正当手段，不拦。
    """
    if not isinstance(tool_input, Mapping):
        return False
    return tool_input.get("run_in_background") is True


def extract_command_texts(payload: Mapping[str, object]) -> list[str]:
    if payload.get("tool_name") not in TARGET_TOOL_NAMES:
        return []
    tool_input = payload.get("tool_input")
    if _runs_in_background(tool_input):
        return []
    return _text_values(tool_input, COMMAND_KEYS)


def deny_output(reason: str) -> dict[str, object]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"[P0-NO-SLEEP-POLLING] {reason}",
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
