#!/usr/bin/env python3
"""集中执行项目级 PreToolUse 机械门禁。"""

from __future__ import annotations

import json
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, TextIO

from server_launcher_guard import (
    extract_command_texts,
    inspect_payload as inspect_order,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LLM_PROBE_RELATIVE = Path("thesis/experiments/llm_probe")
REMOTE_PROJECT_ROOT = "/root/autodl-tmp/thesis/experiments/llm_probe"
SHELL_TOOL_NAMES = frozenset({"Bash", "exec_command", "functions.exec"})
AGENT_TOOL_NAMES = frozenset({"Agent", "spawn_agent"})
GENERIC_AGENT_NAMES = re.compile(
    r"^(?:task|agent|temp|tmp|test|worker|subagent|任务|代理|临时代理)(?:_?\d+)?$",
    re.IGNORECASE,
)
VALID_AGENT_NAME = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
GUARDED_WRAPPERS = frozenset(
    {
        "guarded_remote_stage.py",
        "guarded_rsync.py",
        "guarded_uv_sync.py",
    }
)
WRAPPER_DIRECTORY = PROJECT_ROOT / LLM_PROBE_RELATIVE / "scripts"
REMOTE_QUERY_COMMANDS = frozenset(
    {
        "cat",
        "df",
        "du",
        "fdfind",
        "jq",
        "nvidia-smi",
        "ps",
        "pwd",
        "rg",
        "screen",
        "sha256sum",
        "test",
        "wc",
    }
)
UV_RUN_OPTIONS_WITH_VALUE = frozenset(
    {
        "--directory",
        "--env-file",
        "--extra",
        "--group",
        "--index",
        "--index-strategy",
        "--link-mode",
        "--no-extra",
        "--no-group",
        "--only-group",
        "--prerelease",
        "--project",
        "--python",
        "--python-platform",
        "--resolution",
        "--with",
        "--with-editable",
        "--with-requirements",
        "-E",
        "-p",
        "-w",
    }
)
DANGEROUS_RSYNC_OPTIONS = re.compile(
    r"(?:^|\s)(?:--delete(?:-[a-z-]+)?|--remove-source-files)(?:\s|$)",
    re.IGNORECASE,
)
REMOTE_TRANSPORT_PATTERN = re.compile(
    r"(?:"
    r"(?:^|[;&|\s])ssh(?:[;&|\s]|$)|"
    r"(?:^|[;&|\s])scp(?:[;&|\s]|$)|"
    r"\bGPU_(?:SSH|PWD)\b|"
    r"gpu-(?:exec|rsync)[^\s'\"]*\.exp"
    r")",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PolicyDecision:
    """一次项目策略检查的确定性结果。"""

    status: str
    rule_id: str
    reason: str

    @property
    def denied(self) -> bool:
        return self.status == "deny"


def _pass() -> PolicyDecision:
    return PolicyDecision("pass", "P1-PASS", "未命中项目机械拒绝规则。")


def _deny(rule_id: str, reason: str) -> PolicyDecision:
    return PolicyDecision("deny", rule_id, reason)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def _basename(token: str) -> str:
    return Path(token).name.lower()


def _shell_tokens(text: str) -> list[str]:
    try:
        lexer = shlex.shlex(text, posix=True, punctuation_chars=";&|()")
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer)
    except ValueError:
        return []


def _command_segments(text: str, depth: int = 0) -> list[list[str]]:
    """提取命令位置，并递归展开常见 ``sh -c`` 与 ``eval`` 包装。"""
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
            preserves_query = (
                _basename(raw[index]) == "command"
                and index + 1 < len(raw)
                and raw[index + 1] == "-v"
            )
            if not preserves_query:
                index += 1
                while index < len(raw) and raw[index].startswith("-"):
                    index += 1
        if index >= len(raw):
            continue

        argv = raw[index:]
        segments.append(argv)
        executable = _basename(argv[0])
        if executable in {"bash", "sh", "zsh"}:
            for option_index, option in enumerate(argv[1:], start=1):
                if option in {"-c", "-lc"} and option_index + 1 < len(argv):
                    segments.extend(
                        _command_segments(argv[option_index + 1], depth + 1)
                    )
                    break
        elif executable == "eval" and len(argv) > 1:
            segments.extend(_command_segments(" ".join(argv[1:]), depth + 1))
    return segments


def _python_module(argv: list[str], module: str) -> bool:
    executable = _basename(argv[0])
    if not executable.startswith("python"):
        return False
    return any(
        argv[index] == "-m" and argv[index + 1] == module
        for index in range(1, len(argv) - 1)
    )


def _is_pytest_command(argv: list[str]) -> bool:
    executable = _basename(argv[0])
    if executable == "pytest" or executable.startswith("pytest-"):
        return True
    if _python_module(argv, "pytest"):
        return True
    if executable != "uv" or "run" not in argv[1:]:
        return False
    run_index = argv.index("run", 1)
    nested = argv[run_index + 1 :]
    index = 0
    while index < len(nested) and nested[index].startswith("-"):
        option = nested[index]
        if option == "--":
            index += 1
            break
        index += 1
        if "=" not in option and option in UV_RUN_OPTIONS_WITH_VALUE:
            index += 1
    nested = nested[index:]
    if not nested:
        return False
    return _basename(nested[0]) == "pytest" or _python_module(nested, "pytest")


def _is_uv_sync_command(argv: list[str]) -> bool:
    return _basename(argv[0]) == "uv" and len(argv) > 1 and argv[1] == "sync"


def _guarded_wrapper(argv: list[str], cwd: Path) -> str | None:
    if not argv or not _basename(argv[0]).startswith("python"):
        return None
    for token in argv[1:]:
        name = _basename(token)
        if name not in GUARDED_WRAPPERS:
            continue
        candidate = Path(token).expanduser()
        if not candidate.is_absolute():
            candidate = cwd / candidate
        if candidate.resolve() == (WRAPPER_DIRECTORY / name).resolve():
            return name
    return None


def _targets_experiment(cwd: Path, texts: Iterable[str]) -> bool:
    experiment_root = PROJECT_ROOT / LLM_PROBE_RELATIVE
    if _is_within(cwd, experiment_root):
        return True
    markers = (LLM_PROBE_RELATIVE.as_posix(), REMOTE_PROJECT_ROOT)
    return any(any(marker in text for marker in markers) for text in texts)


def _contains_unsafe_remote_encoding(text: str) -> bool:
    if "\n" in text or "\r" in text or "<<" in text or "JSON.stringify" in text:
        return True
    without_printf_formats = re.sub(r"%[a-zA-Z]\\\\[nr]", "", text)
    return "\\n" in without_printf_formats or "\\r" in without_printf_formats


def _expect_invocations(text: str) -> list[list[str]]:
    return [
        argv
        for argv in _command_segments(text)
        if argv and _basename(argv[0]) == "expect"
    ]


def _approved_short_remote_query(payload: str) -> bool:
    if len(payload) > 768 or _contains_unsafe_remote_encoding(payload):
        return False
    tokens = _shell_tokens(payload)
    if "`" in payload or any(token in {"&&", "||", "|"} for token in tokens):
        return False

    commands = _command_segments(payload)
    query_count = 0
    saw_bashrc = False
    for argv in commands:
        executable = _basename(argv[0])
        if executable in {"source", "."}:
            if len(argv) < 2 or not argv[1].endswith("/.bashrc"):
                return False
            saw_bashrc = True
            continue
        if executable == "cd":
            if len(argv) != 2 or not argv[1].startswith("/root/autodl-tmp/thesis"):
                return False
            continue
        if executable == "command" and len(argv) >= 3 and argv[1] == "-v":
            query_count += 1
            continue
        if executable not in REMOTE_QUERY_COMMANDS:
            return False
        if executable == "screen" and (len(argv) < 2 or argv[1] != "-ls"):
            return False
        query_count += 1
    return saw_bashrc and query_count == 1


def inspect_agent_payload(payload: Mapping[str, object]) -> PolicyDecision:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, Mapping):
        return _deny("P1-AGENT", "子代理创建输入不是可检查的对象。")
    task_name = tool_input.get("task_name")
    message = tool_input.get("message")
    if not isinstance(task_name, str) or not VALID_AGENT_NAME.fullmatch(task_name):
        return _deny(
            "P1-AGENT",
            "子代理 task_name 必须为 3 至 64 位小写语义化 snake_case 名称。",
        )
    if GENERIC_AGENT_NAMES.fullmatch(task_name):
        return _deny("P1-AGENT", "子代理 task_name 不能使用任务编号或通用临时名称。")
    if not isinstance(message, str) or len(message.strip()) < 12:
        return _deny("P1-AGENT", "子代理 message 必须包含不少于 12 个字符的具体职责。")
    return _pass()


def inspect_shell_payload(payload: Mapping[str, object]) -> PolicyDecision:
    texts = extract_command_texts(payload)
    if not texts:
        return _pass()

    cwd_value = payload.get("cwd")
    cwd = Path(cwd_value).expanduser() if isinstance(cwd_value, str) else PROJECT_ROOT
    targets_experiment = _targets_experiment(cwd, texts)

    for text in texts:
        commands = _command_segments(text)
        wrappers = {
            wrapper for argv in commands if (wrapper := _guarded_wrapper(argv, cwd))
        }

        if DANGEROUS_RSYNC_OPTIONS.search(text):
            return _deny(
                "P1-RSYNC",
                "禁止 rsync 删除源或目标内容；受管同步不接受 --delete 或 --remove-source-files。",
            )

        if targets_experiment and any(_is_pytest_command(argv) for argv in commands):
            return _deny(
                "P1-PYTEST",
                "实验目录禁止本机或内联远程 pytest；请通过受管远程阶段脚本在服务端 uv 环境执行。",
            )

        if targets_experiment and any(_is_uv_sync_command(argv) for argv in commands):
            return _deny(
                "P1-UV-SYNC",
                "禁止直接 uv sync；请使用 scripts/guarded_uv_sync.py 先干运行并检查关键训练依赖。",
            )

        direct_rsync = any(_basename(argv[0]) == "rsync" for argv in commands)
        direct_scp = any(_basename(argv[0]) == "scp" for argv in commands)
        direct_sync_expect = any(
            len(argv) > 1 and _basename(argv[1]).startswith("gpu-rsync")
            for argv in _expect_invocations(text)
        )
        if (
            targets_experiment
            and (direct_rsync or direct_scp or direct_sync_expect)
            and "guarded_rsync.py" not in wrappers
        ):
            return _deny(
                "P1-RSYNC",
                "实验文件同步必须使用 scripts/guarded_rsync.py；禁止直接 rsync、scp 或临时 Expect 同步器。",
            )

        has_remote_command = any(
            argv and _basename(argv[0]) in {"ssh", "scp"} for argv in commands
        )
        if has_remote_command or REMOTE_TRANSPORT_PATTERN.search(text):
            if _contains_unsafe_remote_encoding(text):
                return _deny(
                    "P1-REMOTE",
                    "远程入口禁止真实多行、here-document、JSON.stringify 多行或字面量反斜杠换行。",
                )
            if wrappers.intersection(GUARDED_WRAPPERS):
                continue
            expect_calls = _expect_invocations(text)
            if expect_calls:
                for argv in expect_calls:
                    if len(argv) < 3 or _basename(argv[1]) != "gpu-exec.exp":
                        return _deny("P1-REMOTE", "远程操作必须使用受管包装器。")
                    if not _approved_short_remote_query(argv[2]):
                        return _deny(
                            "P1-REMOTE",
                            "临时 gpu-exec 仅允许一个只读查询；正式或多语句操作必须使用受管持久脚本。",
                        )
                continue
            return _deny(
                "P1-REMOTE",
                "禁止直接 ssh、scp 或环境变量拼接远程命令；请使用项目受管包装器。",
            )

    return _pass()


def inspect_payload(payload: Mapping[str, object]) -> PolicyDecision:
    tool_name = payload.get("tool_name")
    if tool_name in AGENT_TOOL_NAMES:
        return inspect_agent_payload(payload)
    if tool_name not in SHELL_TOOL_NAMES:
        return _pass()

    order_decision = inspect_order(payload, PROJECT_ROOT)
    if order_decision.denied:
        return _deny("P0-NOUNSET", order_decision.reason)
    return inspect_shell_payload(payload)


def deny_hook_output(decision: PolicyDecision) -> dict[str, object]:
    reason = f"[{decision.rule_id}] {decision.reason}"
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
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
    decision = inspect_payload(payload)
    return deny_hook_output(decision) if decision.denied else None


def main() -> int:
    # 用户明确要求暂停本会话的项目执行门禁，以解除模型下载阻塞。
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
