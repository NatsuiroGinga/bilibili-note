#!/usr/bin/env python3
"""在显式派发前校验子代理名称、模型和工作树绑定。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from typing import Mapping, TextIO

AGENT_TOOL_NAMES = frozenset({"Agent", "spawn_agent", "collaboration.spawn_agent"})
MODEL_BY_TASK_SUFFIX = {
    "sol": "gpt-5.6-sol",
    "terra": "gpt-5.6-terra",
    "luna": "gpt-5.6-luna",
    "astra": "gpt-6-astra",
}
TASK_NAME_PATTERN = re.compile(
    r"^(?P<domain>[a-z0-9]+)_"
    r"(?P<duty>[a-z0-9_]+)_"
    r"(?P<model>sol|terra|luna|astra)_"
    r"(?P<effort>[a-z0-9]+)$"
)
PATH_PATTERN = re.compile(
    r"(?:/[-A-Za-z0-9._]+(?:/[-A-Za-z0-9._]+)*|"
    r"\.[-A-Za-z0-9_]+(?:/[-A-Za-z0-9._]+)+|"
    r"[-A-Za-z0-9_]+(?:/[-A-Za-z0-9._]+)+|"
    r"[-A-Za-z0-9_]+\.(?:py|md|json|toml|yaml|yml|sh))"
)
WORKTREE_PATTERN = re.compile(
    r"(?:唯一(?:允许)?(?:的)?工作树|工作树(?:路径)?|worktree)\s*"
    r"(?:为|是|:|：)?\s*[`'\"]?(?P<path>/[-A-Za-z0-9._/]+)"
)
BRANCH_PATTERN = re.compile(
    r"(?:预期分支|expected branch)\s*(?:为|是|:|：)?\s*"
    r"[`'\"]?(?P<branch>[-A-Za-z0-9._/]+)"
)
FIRST_ACTION_PATTERN = re.compile(
    r"(?:首个动作|第一步|first action).{0,160}?\bpwd\b.{0,160}?"
    r"git\s+branch\s+--show-current",
    re.DOTALL,
)
WRITING_TASK_PATTERN = re.compile(
    r"(?:写入|修改|实现|编辑|创建).{0,60}?(?:文件|代码|脚本|配置|文档)",
    re.DOTALL,
)


@dataclass(frozen=True)
class Violation:
    """单条可向派发者反馈的确定性拒绝理由。"""

    rule_id: str
    reason: str


def _has_declared_path(message: str) -> bool:
    return bool(PATH_PATTERN.search(message))


def _validate_task_name(tool_input: Mapping[str, object]) -> list[Violation]:
    task_name = tool_input.get("task_name")
    if not isinstance(task_name, str):
        return [Violation("ADG-NAME", "必须提供字符串 task_name。")]

    match = TASK_NAME_PATTERN.fullmatch(task_name)
    if match is None:
        return [
            Violation(
                "ADG-NAME",
                "task_name 必须为 <domain>_<specific_duty>_<model>_<effort>，"
                "模型后缀只能是 sol、terra、luna 或 astra。",
            )
        ]

    violations: list[Violation] = []
    expected_model = MODEL_BY_TASK_SUFFIX[match.group("model")]
    if tool_input.get("model") != expected_model:
        violations.append(
            Violation(
                "ADG-MODEL",
                "task_name 的模型后缀要求 model=" + expected_model + "。",
            )
        )
    if tool_input.get("reasoning_effort") != match.group("effort"):
        violations.append(
            Violation(
                "ADG-EFFORT",
                "task_name 的推理强度后缀必须与 reasoning_effort 一致。",
            )
        )
    return violations


def _validate_worktree_briefing(message: str) -> list[Violation]:
    violations: list[Violation] = []
    worktree_paths = [match.group("path") for match in WORKTREE_PATTERN.finditer(message)]
    if "唯一" not in message or len(worktree_paths) != 1:
        violations.append(
            Violation("ADG-WORKTREE", "简报必须声明唯一绝对工作树路径。")
        )
    if not BRANCH_PATTERN.search(message):
        violations.append(Violation("ADG-BRANCH", "简报必须声明预期分支。"))
    if not FIRST_ACTION_PATTERN.search(message):
        violations.append(
            Violation(
                "ADG-FIRST-ACTION",
                "简报必须要求首个动作核对 pwd 与 git branch --show-current。",
            )
        )
    return violations


def _is_writing_task(tool_input: Mapping[str, object], message: str) -> bool:
    return tool_input.get("agent_type") == "worker" or bool(
        WRITING_TASK_PATTERN.search(message)
    )


def _validate_writing_briefing(message: str) -> list[Violation]:
    violations: list[Violation] = []
    if not ("文件所有权" in message and "责任所有权" in message and _has_declared_path(message)):
        violations.append(
            Violation(
                "ADG-BRIEF-OWNERSHIP",
                "写入任务必须声明带路径的文件所有权和责任所有权。",
            )
        )
    if not re.search(r"(?:不是唯一代理|非独占工作树|不独占工作树)", message):
        violations.append(
            Violation("ADG-BRIEF-SHARED", "写入任务必须声明工作树非独占。")
        )
    if not re.search(r"(?:不得|禁止|不要)回滚.{0,40}(?:他人|其他代理|用户)", message):
        violations.append(
            Violation("ADG-BRIEF-REVERT", "写入任务必须禁止回滚他人改动。")
        )
    return violations


def inspect_payload(payload: Mapping[str, object]) -> list[Violation] | None:
    """只检查子代理创建请求；其他工具调用不产生输出。"""
    if payload.get("tool_name") not in AGENT_TOOL_NAMES:
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, Mapping):
        return [Violation("ADG-INPUT", "子代理创建输入必须为 JSON 对象。")]

    violations = _validate_task_name(tool_input)
    message = tool_input.get("message")
    if not isinstance(message, str) or not message.strip():
        return violations + [Violation("ADG-BRIEF", "必须提供非空 message 简报。")]
    violations.extend(_validate_worktree_briefing(message))
    if _is_writing_task(tool_input, message):
        violations.extend(_validate_writing_briefing(message))
    return violations


def _deny_output(violations: list[Violation]) -> dict[str, object]:
    reason = "；".join(
        "[" + violation.rule_id + "] " + violation.reason
        for violation in violations
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def _load_payload(stream: TextIO) -> tuple[Mapping[str, object] | None, list[Violation]]:
    try:
        payload = json.load(stream)
    except (json.JSONDecodeError, OSError):
        return None, [Violation("ADG-INPUT", "输入不是有效 JSON。")]
    if not isinstance(payload, dict):
        return None, [Violation("ADG-INPUT", "输入必须是 JSON 对象。")]
    return payload, []


def handle_hook_input(stream: TextIO) -> dict[str, object] | None:
    """兼容未来原生 Hook 调用；当前项目不将其注册为自动拦截。"""
    payload, parse_violations = _load_payload(stream)
    if parse_violations:
        return _deny_output(parse_violations)
    assert payload is not None
    if payload.get("hook_event_name") not in {None, "PreToolUse"}:
        return None
    violations = inspect_payload(payload)
    return _deny_output(violations) if violations else None


def _preflight(stream: TextIO) -> tuple[dict[str, object], int]:
    payload, parse_violations = _load_payload(stream)
    violations = parse_violations
    if payload is not None:
        inspected = inspect_payload(payload)
        if inspected is None:
            violations = [Violation("ADG-INPUT", "预检仅接受子代理创建输入。")]
        else:
            violations = inspected
    return (
        {
            "valid": not violations,
            "violations": [
                {"rule_id": violation.rule_id, "reason": violation.reason}
                for violation in violations
            ],
        },
        0 if not violations else 2,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="从标准输入校验 Agent JSON；通过为 0，拒绝为 2。",
    )
    arguments = parser.parse_args()
    if arguments.preflight:
        output, exit_code = _preflight(sys.stdin)
        json.dump(output, sys.stdout, ensure_ascii=False, separators=(",", ":"))
        sys.stdout.write("\n")
        return exit_code

    output = handle_hook_input(sys.stdin)
    if output is not None:
        json.dump(output, sys.stdout, ensure_ascii=False, separators=(",", ":"))
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
