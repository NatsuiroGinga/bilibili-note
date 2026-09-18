#!/usr/bin/env python3
"""阻止实验持久制品落入系统临时目录的 Codex PreToolUse 守卫。"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, TextIO

SHELL_TOOL_NAMES = frozenset(
    {"Bash", "Shell", "exec_command", "functions.exec"}
)
PATCH_TOOL_NAMES = frozenset({"apply_patch", "Edit", "Write"})

PERSISTENT_KEYS = (
    "cache_root",
    "checkpoint",
    "checkpoint_dir",
    "checkpoint_path",
    "data_dir",
    "data_path",
    "data_root",
    "dataset",
    "dataset_dir",
    "dataset_path",
    "dataset_root",
    "download_local_dir",
    "input_root",
    "local_dir",
    "model",
    "model_dir",
    "model_path",
    "output",
    "output_dir",
    "output_path",
    "output_root",
    "run_dir",
    "run_root",
    "runs_dir",
    "weights",
    "weights_dir",
    "weights_path",
)
PERSISTENT_OPTIONS = (
    "--cache-root",
    "--checkpoint",
    "--checkpoint-dir",
    "--checkpoint-path",
    "--data-dir",
    "--data-path",
    "--data-root",
    "--dataset",
    "--dataset-dir",
    "--dataset-path",
    "--dataset-root",
    "--download-local-dir",
    "--input-root",
    "--local-dir",
    "--model",
    "--model-dir",
    "--model-path",
    "--output",
    "--output-dir",
    "--output-path",
    "--output-root",
    "--run-dir",
    "--run-root",
    "--runs-dir",
    "--weights",
    "--weights-dir",
    "--weights-path",
)
TEMPORARY_VALUE_PATTERN = re.compile(
    r"(?:"
    r"(?:^|[\"'])/(?:private/)?tmp(?:/|$)|"
    r"(?:^|[\"'])/private/var/folders/[^\"'\s]+/T(?:/|$)|"
    r"(?:^|[\"'])/var/folders/[^\"'\s]+/T(?:/|$)|"
    r"\$(?:TMPDIR|TMP|TEMP)(?:\b|[/{])|"
    r"\$\{(?:TMPDIR|TMP|TEMP)\}(?:\b|[/{])|"
    r"(?:tempfile\.)?(?:gettempdir|mk(?:d)?temp)\s*\(|"
    r"os\.tmpdir\s*\(|"
    r"os\.environ(?:\.get)?\s*\(\s*[\"'](?:TMPDIR|TMP|TEMP)[\"']|"
    r"os\.environ\[\s*[\"'](?:TMPDIR|TMP|TEMP)[\"']\s*\]"
    r")",
    re.IGNORECASE,
)
VALUE_PATTERN = r"(?P<value>\"[^\"]*\"|'[^']*'|[^\s,;|)\]}]+)"
KEY_PATTERN = "|".join(re.escape(key) for key in PERSISTENT_KEYS)
OPTION_PATTERN = "|".join(re.escape(option) for option in PERSISTENT_OPTIONS)
ASSIGNMENT_PATTERN = re.compile(
    rf"(?<![A-Za-z0-9_])(?:[\"']?(?P<key>{KEY_PATTERN})[\"']?)"
    rf"\s*(?::|=)\s*{VALUE_PATTERN}",
    re.IGNORECASE,
)
OPTION_VALUE_PATTERN = re.compile(
    rf"(?P<option>{OPTION_PATTERN})(?:=|\s+){VALUE_PATTERN}",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Decision:
    """守卫对单次钩子输入的确定性结论。"""

    rule_id: str
    reason: str


def _is_temporary_value(value: str, workdir: Path | None) -> bool:
    normalized = value.strip().strip("\"'")
    if TEMPORARY_VALUE_PATTERN.search(normalized):
        return True
    if workdir is None or not normalized or normalized.startswith("$"):
        return False
    try:
        resolved = (workdir / Path(normalized)).resolve()
    except OSError:
        return False
    return bool(TEMPORARY_VALUE_PATTERN.search(resolved.as_posix()))


def _inspect_text(text: str, workdir: Path | None) -> Decision | None:
    for match in ASSIGNMENT_PATTERN.finditer(text):
        value = match.group("value")
        if _is_temporary_value(value, workdir):
            return Decision(
                "P2-EXPERIMENT-TMP-PATH",
                "实验持久路径字段 "
                + match.group("key")
                + " 不能指向系统临时目录："
                + value,
            )

    for match in OPTION_VALUE_PATTERN.finditer(text):
        value = match.group("value")
        if _is_temporary_value(value, workdir):
            return Decision(
                "P2-EXPERIMENT-TMP-PATH",
                "实验持久路径参数 "
                + match.group("option")
                + " 不能指向系统临时目录："
                + value,
            )
    return None


def _text_inputs(payload: Mapping[str, object]) -> list[str]:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, Mapping):
        return []
    return [
        value
        for key in ("command", "cmd", "patch", "source", "script")
        if isinstance((value := tool_input.get(key)), str)
    ]


def _tool_workdir(payload: Mapping[str, object]) -> Path | None:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, Mapping):
        return None
    workdir = tool_input.get("workdir")
    if not isinstance(workdir, str) or not workdir.strip():
        return None
    try:
        return Path(workdir).expanduser().resolve()
    except OSError:
        return None


def _belongs_to_project(payload: Mapping[str, object]) -> bool:
    cwd_value = payload.get("cwd")
    if not isinstance(cwd_value, str):
        return False
    try:
        cwd = Path(cwd_value).expanduser().resolve()
    except OSError:
        return False
    for candidate in (cwd, *cwd.parents):
        if (candidate / "AGENTS.md").is_file() and (
            candidate / "thesis/experiments/llm_probe/AGENTS.md"
        ).is_file():
            return True
    return False


def inspect_payload(payload: Mapping[str, object]) -> Decision | None:
    tool_name = payload.get("tool_name")
    if tool_name not in SHELL_TOOL_NAMES | PATCH_TOOL_NAMES:
        return None
    if not _belongs_to_project(payload):
        return None
    workdir = _tool_workdir(payload)
    for text in _text_inputs(payload):
        if decision := _inspect_text(text, workdir):
            return decision
    return None


def _deny_output(decision: Decision) -> dict[str, object]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "["
            + decision.rule_id
            + "] "
            + decision.reason
            + "。请改用当前工作树的 "
            + "thesis/experiments/llm_probe/runs/data-raw 或 runs/diagnostics。",
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
    return _deny_output(decision) if decision else None


def main() -> int:
    output = handle_hook_input(sys.stdin)
    if output is not None:
        json.dump(output, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
