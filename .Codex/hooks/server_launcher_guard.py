#!/usr/bin/env python3
"""拒绝服务器启动器在加载 ~/.bashrc 前启用 nounset。"""

from __future__ import annotations

import argparse
import ast
import json
import re
import shlex
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, TextIO

TARGET_TOOL_NAMES = frozenset({"Bash", "exec_command", "functions.exec"})
COMMAND_KEYS = ("command", "cmd")
SOURCE_KEYS = ("source", "code", "script", "input")
SUPPORTED_SCRIPT_SUFFIXES = frozenset({".sh", ".bash", ".zsh", ".exp"})
MAX_SCRIPT_BYTES = 1024 * 1024

NOUNSET_PATTERN = re.compile(
    r"(?<![\w-])set[ \t]+(?:-[A-Za-z]*u[A-Za-z]*(?:\s|;|&&|\|\||$)|"
    r"-o[ \t]+nounset\b)"
)
BASHRC_PATTERN = re.compile(
    r"(?<![\w-])(?:source|\.)[ \t]+(?:['\"])?"
    r"(?:~|\$\{?HOME\}?|/root)/\.bashrc(?:['\"])?"
)
SERVER_MARKER_PATTERN = re.compile(
    r"(?:"
    r"(?:^|[;&|\s])ssh(?:[;&|\s]|$)|"
    r"spawn[ \t]+ssh\b|"
    r"\bGPU_(?:SSH|PWD)\b|"
    r"connect\.westd\.seetacloud\.com|"
    r"/root/autodl-tmp(?:/|\b)|"
    r"(?:gpu|server)[_-]?(?:exec|rsync|launch)|"
    r"screen[ \t]+-(?:[^\n;]*[dDmMS])"
    r")",
    re.IGNORECASE | re.MULTILINE,
)
SCRIPT_PATH_PATTERN = re.compile(
    r"(?P<path>(?:~|/|\.{1,2}/)?[^\s'\"`;|&<>]+\.(?:sh|bash|zsh|exp))\b",
    re.IGNORECASE,
)
JS_CMD_PATTERN = re.compile(
    r"\bcmd\s*:\s*(?P<quote>['\"`])(?P<body>(?:\\.|(?!\1).)*)(?P=quote)",
    re.DOTALL,
)


@dataclass(frozen=True)
class GuardDecision:
    """一次顺序检查的确定性结果。"""

    status: str
    reason: str
    origin: str | None = None

    @property
    def denied(self) -> bool:
        return self.status == "deny"


def _project_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def _without_comment_lines(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )


def _server_related(text: str, origin: str | None = None) -> bool:
    if SERVER_MARKER_PATTERN.search(text):
        return True
    if origin is None:
        return False
    name = Path(origin).name.lower()
    return any(token in name for token in ("server", "gpu", "remote", "launch"))


def _script_fragments(text: str) -> list[str]:
    """提取远程命令或 ``bash -lc`` 中被引号包裹的内联脚本。"""
    fragments: list[str] = []
    try:
        tokens = shlex.split(text, posix=True)
    except ValueError:
        tokens = []
    for token in tokens:
        if len(token) > 4 and (
            NOUNSET_PATTERN.search(token) or BASHRC_PATTERN.search(token)
        ):
            fragments.append(token)
    for match in re.finditer(
        r"(?P<quote>['\"])(?P<body>.*?)(?P=quote)", text, re.DOTALL
    ):
        body = match.group("body")
        if NOUNSET_PATTERN.search(body) or BASHRC_PATTERN.search(body):
            fragments.append(body)
    return fragments


def _check_order(text: str, origin: str) -> GuardDecision:
    cleaned = _without_comment_lines(text)
    nounset_positions = [match.start() for match in NOUNSET_PATTERN.finditer(cleaned)]
    if not nounset_positions:
        return GuardDecision("pass", "未启用 nounset。", origin)
    bashrc_positions = [match.start() for match in BASHRC_PATTERN.finditer(cleaned)]
    first_nounset = min(nounset_positions)
    if not bashrc_positions:
        return GuardDecision(
            "deny",
            "服务器启动命令启用了 nounset，但此前没有执行 source ~/.bashrc。"
            "请先加载 ~/.bashrc，再执行 set -u 或 set -o nounset。",
            origin,
        )
    if min(bashrc_positions) > first_nounset:
        return GuardDecision(
            "deny",
            "服务器启动命令在 source ~/.bashrc 之前启用了 nounset。"
            "该顺序会使非交互 ~/.bashrc 中未定义的 PS1 触发启动失败；"
            "请把 source ~/.bashrc 移到 set -u 或 set -o nounset 之前。",
            origin,
        )
    return GuardDecision("pass", "已先加载 ~/.bashrc，再启用 nounset。", origin)


def inspect_text(text: str, origin: str = "命令输入") -> GuardDecision:
    """检查一段确定属于服务器启动上下文的命令及其内联脚本。"""
    if not isinstance(text, str) or not text.strip():
        return GuardDecision("neutral", "没有可检查的命令文本。", origin)
    if not _server_related(text, origin):
        return GuardDecision("neutral", "命令与服务器启动无关。", origin)

    primary = _check_order(text, origin)
    if primary.denied:
        return primary
    for index, fragment in enumerate(_script_fragments(text), start=1):
        fragment_result = _check_order(fragment, f"{origin}的内联脚本#{index}")
        if fragment_result.denied:
            return fragment_result
    return primary


def _decode_js_literal(quote: str, body: str) -> str:
    if quote == "`":
        return bytes(body, "utf-8").decode("unicode_escape") if "\\" in body else body
    try:
        value = ast.literal_eval(f"{quote}{body}{quote}")
    except (SyntaxError, ValueError):
        return body
    return value if isinstance(value, str) else body


def _functions_exec_commands(source: str) -> list[str]:
    if "exec_command" not in source:
        return []
    commands = [
        _decode_js_literal(match.group("quote"), match.group("body"))
        for match in JS_CMD_PATTERN.finditer(source)
    ]
    return commands or [source]


def _text_values(value: object, keys: Iterable[str]) -> list[str]:
    if isinstance(value, str):
        return [value]
    if not isinstance(value, Mapping):
        return []
    texts: list[str] = []
    for key in keys:
        candidate = value.get(key)
        if isinstance(candidate, str):
            texts.append(candidate)
    return texts


def extract_command_texts(payload: Mapping[str, object]) -> list[str]:
    """从三类可能的工具输入中提取实际命令，而不是任意说明文字。"""
    tool_name = payload.get("tool_name")
    if tool_name not in TARGET_TOOL_NAMES:
        return []
    tool_input = payload.get("tool_input")
    if tool_name in {"Bash", "exec_command"}:
        return _text_values(tool_input, COMMAND_KEYS)

    source_texts = _text_values(tool_input, SOURCE_KEYS)
    commands: list[str] = []
    for source in source_texts:
        commands.extend(_functions_exec_commands(source))
    return commands


def _allowed_script_roots(project_root: Path, cwd: Path) -> tuple[Path, ...]:
    roots = {
        project_root.resolve(),
        cwd.resolve(),
        Path(tempfile.gettempdir()).resolve(),
    }
    roots.add(Path("/tmp").resolve())
    return tuple(sorted(roots, key=str))


def _inside_any(path: Path, roots: Iterable[Path]) -> bool:
    for root in roots:
        try:
            path.relative_to(root)
        except ValueError:
            continue
        return True
    return False


def _resolve_script_path(raw_path: str, cwd: Path) -> Path | None:
    cleaned = raw_path.strip("'\"")
    candidate = Path(cleaned).expanduser()
    if not candidate.is_absolute():
        candidate = cwd / candidate
    try:
        resolved = candidate.resolve()
    except OSError:
        return None
    if resolved.suffix.lower() not in SUPPORTED_SCRIPT_SUFFIXES:
        return None
    return resolved


def referenced_script_paths(
    texts: Iterable[str], project_root: Path, cwd: Path
) -> list[Path]:
    """返回命令引用且位于项目或临时目录内的可读脚本。"""
    roots = _allowed_script_roots(project_root, cwd)
    paths: list[Path] = []
    seen: set[Path] = set()
    for text in texts:
        for match in SCRIPT_PATH_PATTERN.finditer(text):
            path = _resolve_script_path(match.group("path"), cwd)
            if path is None or path in seen or not _inside_any(path, roots):
                continue
            if not path.is_file() or path.stat().st_size > MAX_SCRIPT_BYTES:
                continue
            seen.add(path)
            paths.append(path)
    return paths


def _read_script(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None


def inspect_payload(
    payload: Mapping[str, object], project_root: Path | None = None
) -> GuardDecision:
    """检查一个 PreToolUse 输入；无法确定时返回中性结果。"""
    root = (project_root or _project_root_from_script()).resolve()
    cwd_value = payload.get("cwd")
    cwd = Path(cwd_value).expanduser().resolve() if isinstance(cwd_value, str) else root
    texts = extract_command_texts(payload)
    if not texts:
        return GuardDecision("neutral", "没有提取到受管工具的命令文本。")

    parent_server_context = any(_server_related(text) for text in texts)
    for index, text in enumerate(texts, start=1):
        decision = inspect_text(text, f"工具命令#{index}")
        if decision.denied:
            return decision

    for path in referenced_script_paths(texts, root, cwd):
        content = _read_script(path)
        if content is None:
            continue
        if not parent_server_context and not _server_related(content, str(path)):
            continue
        decision = inspect_text(content, str(path))
        if decision.denied:
            return decision
    return GuardDecision("pass", "未发现服务器启动器 nounset 顺序错误。")


def neutral_hook_output() -> None:
    """中性放行；命令入口以退出码零且无输出表示成功。"""
    return None


def deny_hook_output(decision: GuardDecision) -> dict[str, object]:
    reason = decision.reason
    if decision.origin:
        reason = f"{reason} 检查位置：{decision.origin}。"
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def handle_hook_input(
    stream: TextIO, project_root: Path | None = None
) -> dict[str, object] | None:
    try:
        payload = json.load(stream)
    except (json.JSONDecodeError, OSError):
        return neutral_hook_output()
    if not isinstance(payload, dict) or payload.get("hook_event_name") not in {
        None,
        "PreToolUse",
    }:
        return neutral_hook_output()
    decision = inspect_payload(payload, project_root)
    return deny_hook_output(decision) if decision.denied else neutral_hook_output()


def inspect_file(path: Path, project_root: Path | None = None) -> GuardDecision:
    root = (project_root or _project_root_from_script()).resolve()
    try:
        resolved = path.expanduser().resolve()
    except OSError:
        return GuardDecision("neutral", "无法解析预检文件路径。", str(path))
    if resolved.suffix.lower() not in SUPPORTED_SCRIPT_SUFFIXES:
        return GuardDecision(
            "neutral", "文件类型不属于 Shell 或 Expect 脚本。", str(resolved)
        )
    if not resolved.is_file() or resolved.stat().st_size > MAX_SCRIPT_BYTES:
        return GuardDecision(
            "neutral", "文件不存在、不可读或超过大小上限。", str(resolved)
        )
    allowed_roots = _allowed_script_roots(root, Path.cwd())
    if not _inside_any(resolved, allowed_roots):
        return GuardDecision("neutral", "文件不在项目或临时目录内。", str(resolved))
    content = _read_script(resolved)
    if content is None:
        return GuardDecision("neutral", "文件不是可读取的 UTF-8 文本。", str(resolved))
    return inspect_text(content, str(resolved))


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--file", type=Path, help="显式预检本地 Shell 或 Expect 启动脚本"
    )
    parser.add_argument(
        "--project-root", type=Path, default=None, help=argparse.SUPPRESS
    )
    return parser.parse_args()


def main() -> int:
    arguments = _arguments()
    project_root = arguments.project_root.resolve() if arguments.project_root else None
    if arguments.file is not None:
        decision = inspect_file(arguments.file, project_root)
        json.dump(
            {
                "status": decision.status,
                "reason": decision.reason,
                "origin": decision.origin,
            },
            sys.stdout,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        sys.stdout.write("\n")
        return 2 if decision.denied else 0

    output = handle_hook_input(sys.stdin, project_root)
    if output is not None:
        json.dump(output, sys.stdout, ensure_ascii=False, separators=(",", ":"))
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
