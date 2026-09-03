#!/usr/bin/env python3
"""PreToolUse 钩子：命中特定命令或文件路径时注入提示，不拦截任何工具调用。

存在原因：根 AGENTS.md 与各级子规则要求全文常驻，但最长加载路径的组合字节已逼近
32,768 上限，无法把「做 X 时必须注意 Y」这类局部注意事项继续塞进规则正文。同时
2026-09-03 单日内反复踩中同一批坑（PDF 全文提取错用 flash-extract 丢公式、
pkill -f 整行自匹配导致 SSH 255、torch.equal 未重置 RNG 假阳性失败、
GPU 相关对象直接写入 atomic_json 导致空转 15 小时……），写进恢复卡也没能防止
复发——卡越长越容易漏读。本钩子把这些「用到时才需要知道」的注意事项，
从常驻规则文本改成命令/路径命中时才注入的一次性提醒。

只注入，不拦截：本钩子的 handle_hook_input 只会返回
``{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": ...}}``
或 ``None``，从不设置 ``permissionDecision``。命中即附加提醒，不命中或发生任何
异常即静默放行（返回 None，退出码 0，无输出）。

依据（2026-09-03 查证 https://code.claude.com/docs/en/hooks，已存 .Codex/docs/
同日的注入实现报告）：
1. JSON 输出总述："hookSpecificOutput 是需要更丰富控制的事件用的嵌套对象，
   只要求一个 hookEventName 字段"——permissionDecision、additionalContext 等
   均为该对象下彼此独立的可选字段，不存在"必须先给 permissionDecision 才能带
   additionalContext"的约束。
2. "Add context for Claude" 一节的标准示例本身就只含 hookEventName +
   additionalContext，未设置 permissionDecision：
   ``{"hookSpecificOutput": {"hookEventName": "PostToolUse",
   "additionalContext": "..."}}``；文档同段给出的 PreToolUse 字段表把
   additionalContext 单独列为一项，仅注明"permissionDecision 为 defer 时
   additionalContext 被忽略"，反证其余情况（含未设置 permissionDecision）下生效。
3. PreToolUse 一节明确："Exit code 0 with no output means the hook has no
   decision to report, so the tool call continues through the normal
   permission flow. The hook can deny the call, but staying silent doesn't
   approve it."——本钩子从不输出 permissionDecision，因此既不会拦截，也不会
   越权自动放行（不会绕过用户原本就需要确认的权限提示）。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Callable, Mapping, TextIO

# 复用 prettier_guard 已有的命令抽取与解析：TARGET_TOOL_NAMES 覆盖
# Bash/Shell/exec_command/functions.exec 四种工具形态，extract_command_texts
# 已处理 functions.exec 的 JS 字符串反转义，_command_segments/_basename 已处理
# bash -c、eval、env、sudo、command 等包装展开。运行方式与仓库其余钩子一致：
# Claude Code 以 `python3 <本文件绝对路径>` 启动子进程，Python 会自动把脚本所在
# 目录（.Codex/hooks/）加入 sys.path，故无需手工修改 sys.path 即可裸 import。
from prettier_guard import (  # noqa: E402
    TARGET_TOOL_NAMES as COMMAND_TOOL_NAMES,
    _basename,
    _command_segments,
    extract_command_texts,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FILE_TOOL_NAMES = frozenset({"Edit", "Write", "MultiEdit", "NotebookEdit"})
FILE_PATH_KEYS = ("file_path", "path", "notebook_path")
RULE_FILE_NAMES = frozenset({"AGENTS.md", "CLAUDE.md"})
# 根 AGENTS.md「规则发现与子域路由」节登记的组合上限。
RULE_BYTE_BUDGET = 32768


# --- 六条注入规则中，五条作用于命令文本 -----------------------------------


def _pdf_extraction(texts: list[str]) -> bool:
    return any(re.search(r"pdftotext|flash-extract", text) for text in texts)


def _pkill_pgrep_self_match(texts: list[str]) -> bool:
    """命令里存在 ``pkill -f`` / ``pgrep -f`` 的真实调用（而非仅提及该字符串）。"""
    for text in texts:
        for argv in _command_segments(text):
            if not argv:
                continue
            if _basename(argv[0]) in {"pkill", "pgrep"} and "-f" in argv[1:]:
                return True
    return False


def _git_commit(texts: list[str]) -> bool:
    for text in texts:
        for argv in _command_segments(text):
            if len(argv) >= 2 and _basename(argv[0]) == "git" and argv[1] == "commit":
                return True
    return False


def _rng_equality_check(texts: list[str]) -> bool:
    return any(re.search(r"torch\.equal|逐位", text) for text in texts)


def _json_receipt_write(texts: list[str]) -> bool:
    return any(re.search(r"atomic_json|receipts/", text) for text in texts)


# (标签, 命中判定, 提醒文案)；文案按要求控制在三行以内，只说怎么做对。
COMMAND_RULES: list[tuple[str, Callable[[list[str]], bool], str]] = [
    (
        "PDF 提取",
        _pdf_extraction,
        "PDF 全文提取优先用 tools/pdf_to_fulltext.sh（token 已配置，走 extract）。\n"
        "  flash-extract 限 10MB/20 页且丢失公式符号，不得据此推导公式。",
    ),
    (
        "进程匹配",
        _pkill_pgrep_self_match,
        "pkill -f / pgrep -f 整行不得出现被匹配的完整字符串，否则会匹配到自身，\n"
        "  导致命令挂起或 SSH 返回 255 但目标进程未杀；需要同时写文件时拆成两次独立调用。",
    ),
    (
        "git 提交",
        _git_commit,
        'git commit 用 -m "..." -- <精确路径>，禁止 git add .。\n'
        "  提交信息末尾不得出现 Co-Authored-By。",
    ),
    (
        "RNG 与逐位比较",
        _rng_equality_check,
        "torch.equal / 逐位相等检查前先重置全局 RNG（如 torch.manual_seed）。\n"
        "  骨干含 attention_dropout=0.2、ffn_dropout=0.1，不重置必然假阳性失败。",
    ),
    (
        "JSON 落盘",
        _json_receipt_write,
        "写入 atomic_json 或 receipts/ 前，张量/GPU 相关数值先 .item() / float()。\n"
        "  torch.cuda.Event 等对象不可 JSON 序列化，此前因此致 GPU 空转 15 小时。",
    ),
]


# --- 第六条作用于 Edit/Write 的目标路径 -------------------------------------


def _rule_chain_bytes(target: Path) -> tuple[int, int]:
    """按仓库「规则发现与子域路由」的加载算法，实测从项目根到目标目录的累计字节数。

    每层只计入 AGENTS.override.md 优先、否则 AGENTS.md 的文件大小（与该层实际
    加载规则一致）；返回 ``(已用字节, 层数)``。目标文件自身当前内容（编辑前）
    随其所在目录一并计入。
    """
    resolved = target.expanduser().resolve()
    rel_dir = resolved.parent.relative_to(PROJECT_ROOT)

    total = 0
    for depth in range(len(rel_dir.parts) + 1):
        level_dir = PROJECT_ROOT.joinpath(*rel_dir.parts[:depth])
        for name in ("AGENTS.override.md", "AGENTS.md"):
            candidate = level_dir / name
            if candidate.is_file():
                try:
                    total += candidate.stat().st_size
                except OSError:
                    pass
                break
    return total, len(rel_dir.parts) + 1


def _rule_budget_reminder(payload: Mapping[str, object]) -> str | None:
    tool_name = payload.get("tool_name")
    if tool_name not in FILE_TOOL_NAMES:
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, Mapping):
        return None

    path_value = None
    for key in FILE_PATH_KEYS:
        candidate = tool_input.get(key)
        if isinstance(candidate, str) and candidate:
            path_value = candidate
            break
    if path_value is None or Path(path_value).name not in RULE_FILE_NAMES:
        return None

    try:
        total, levels = _rule_chain_bytes(Path(path_value))
    except (ValueError, OSError):
        return None

    pct = total / RULE_BYTE_BUDGET
    return (
        f"[规则字节预算] 本次编辑前，根到本目录（{levels} 层）的规则加载链已实测"
        f"用去 {total} / {RULE_BYTE_BUDGET} 字节（{pct:.1%}）。\n"
        "  超限会静默截断、最深层规则失效且无报错；新增前先看能否并入既有小节。"
    )


# --- 汇总与输出 -------------------------------------------------------------


def build_additional_context(payload: Mapping[str, object]) -> str | None:
    reminders: list[str] = []

    tool_name = payload.get("tool_name")
    if tool_name in COMMAND_TOOL_NAMES:
        texts = extract_command_texts(payload)
        if texts:
            for label, matches, message in COMMAND_RULES:
                if matches(texts):
                    reminders.append(f"[{label}] {message}")

    budget_reminder = _rule_budget_reminder(payload)
    if budget_reminder:
        reminders.append(budget_reminder)

    if not reminders:
        return None

    # 单条命令命中多条规则时合并为一段输出，不逐条单独注入。
    lines = ["=== 按需规则提醒（命中即提示，不拦截，2026-09-03 起）==="]
    lines.extend(reminders)
    return "\n".join(lines)


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

    context = build_additional_context(payload)
    if not context:
        return None
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": context,
        }
    }


def main() -> int:
    try:
        output = handle_hook_input(sys.stdin)
        if output is not None:
            json.dump(output, sys.stdout, ensure_ascii=False)
            sys.stdout.write("\n")
    except Exception:
        # 硬性要求：钩子自身出错必须静默放行，不得因钩子崩溃挡住工具调用。
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
