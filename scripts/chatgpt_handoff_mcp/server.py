#!/usr/bin/env python3
"""为任意 Git 项目提供受限、只读的 ChatGPT 交接 MCP。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

DEFAULT_HANDOFF_ROOT = ".Codex/docs/chatgpt-handoffs"
FORBIDDEN_PARTS = frozenset(
    {
        "runs",
        "raw",
        "data",
        "dataset",
        "datasets",
        "logs",
        "checkpoints",
        ".env",
        ".ssh",
        ".git",
    }
)
FORBIDDEN_SUFFIXES = frozenset(
    {
        ".csv",
        ".tsv",
        ".jsonl",
        ".npy",
        ".npz",
        ".pcap",
        ".pcapng",
        ".pdf",
        ".log",
        ".pem",
        ".key",
        ".pt",
        ".pth",
        ".ckpt",
    }
)
PROFILE_FIELDS = (
    "requested_model",
    "requested_effort",
    "fallback_model",
    "selection_rationale",
    "requested_mode",
    "requested_apps",
    "task_type",
)


def resolve_project_root(value: str | None) -> Path:
    candidate = value or os.environ.get("CHATGPT_HANDOFF_PROJECT_ROOT") or os.getcwd()
    root = Path(candidate).expanduser().resolve()
    if not root.is_dir() or not (root / ".git").exists():
        raise ValueError("project-root 必须指向 Git 工作树根目录")
    return root


def configured_handoff_root(project_root: Path, value: str | None) -> Path:
    configured = value or os.environ.get("CHATGPT_HANDOFF_ROOT")
    if configured is None:
        config_path = project_root / ".chatgpt-handoff.json"
        if config_path.is_file():
            config = json.loads(config_path.read_text(encoding="utf-8"))
            configured = str(config.get("handoff_root", DEFAULT_HANDOFF_ROOT))
        else:
            configured = DEFAULT_HANDOFF_ROOT
    candidate = Path(configured).expanduser()
    root = candidate.resolve() if candidate.is_absolute() else (project_root / candidate).resolve()
    if not root.is_relative_to(project_root):
        raise ValueError("handoff-root 必须位于 project-root 内")
    if not root.is_dir():
        raise ValueError("交接目录不存在，请先运行 chatgpt_handoff.py init")
    return root


def safe_project_file(project_root: Path, relative: str) -> Path | None:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        return None
    candidate = (project_root / path).resolve()
    if not candidate.is_relative_to(project_root) or not candidate.is_file():
        return None
    lowered_parts = {part.lower() for part in path.parts}
    if lowered_parts & FORBIDDEN_PARTS or candidate.suffix.lower() in FORBIDDEN_SUFFIXES:
        return None
    return candidate


def handoff_records(handoff_root: Path) -> dict[str, Path]:
    records: dict[str, Path] = {}
    for path in sorted(handoff_root.glob("*-outbound.md")):
        identifier = hashlib.sha256(path.name.encode("utf-8")).hexdigest()[:16]
        records[identifier] = path
    return records


def read_handoff(handoff_root: Path, identifier: str) -> str:
    path = handoff_records(handoff_root).get(identifier)
    if path is None:
        raise ValueError("未知交接包 ID")
    return path.read_text(encoding="utf-8")


def _field(text: str, key: str, legacy_label: str | None = None) -> str | None:
    labels = [key]
    if legacy_label:
        labels.append(legacy_label)
    for label in labels:
        match = re.search(rf"^- {re.escape(label)}：`([^`]*)`", text, re.MULTILINE)
        if match:
            return match.group(1)
    return None


def parse_manifest(text: str) -> dict[str, Any]:
    apps = _field(text, "requested_apps") or ""
    return {
        "repository": _field(text, "repository", "私有仓库"),
        "branch": _field(text, "branch", "远端分支"),
        "commit": _field(text, "commit", "冻结提交"),
        "requested_model": _field(text, "requested_model"),
        "requested_effort": _field(text, "requested_effort"),
        "fallback_model": _field(text, "fallback_model"),
        "selection_rationale": _field(text, "selection_rationale"),
        "requested_mode": _field(text, "requested_mode"),
        "requested_apps": [item.strip() for item in apps.split(",") if item.strip()],
        "task_type": _field(text, "task_type"),
        "source_scope": _field(text, "source_scope"),
        "sanitized_summary_included": _field(text, "sanitized_summary_included"),
        "fulltext_required": _field(text, "fulltext_required"),
        "zotero_ingest_required": _field(text, "zotero_ingest_required"),
        "allowed_paths": re.findall(r"^  - `([^`]+)`", text, re.MULTILINE),
    }


def build_server(project_root: Path, handoff_root: Path, host: str, port: int) -> FastMCP:
    server = FastMCP("chatgpt-handoff-readonly", host=host, port=port)

    @server.tool()
    def list_handoffs() -> list[dict[str, str]]:
        """列出当前项目的受管出站包及其稳定 ID。"""
        return [
            {"id": identifier, "path": path.relative_to(project_root).as_posix()}
            for identifier, path in handoff_records(handoff_root).items()
        ]

    @server.tool()
    def get_handoff(handoff_id: str) -> str:
        """按稳定 ID 读取一个受管出站包。"""
        return read_handoff(handoff_root, handoff_id)

    @server.tool()
    def get_snapshot_manifest(handoff_id: str) -> dict[str, Any]:
        """读取仓库快照、白名单、任务类别和执行配置。"""
        return parse_manifest(read_handoff(handoff_root, handoff_id))

    @server.tool()
    def get_execution_profile(handoff_id: str) -> dict[str, Any]:
        """读取请求的模型、思考强度、模式、应用和任务类别。"""
        manifest = parse_manifest(read_handoff(handoff_root, handoff_id))
        return {key: manifest[key] for key in PROFILE_FIELDS}

    @server.tool()
    def search_handoff_context(handoff_id: str, query: str) -> list[dict[str, Any]]:
        """只在交接包明确允许的 Markdown 文件中进行字面量检索。"""
        if not query or len(query) > 160 or any(ord(char) < 32 for char in query):
            raise ValueError("查询不能为空、不能含控制字符且不得超过 160 字符")
        manifest = parse_manifest(read_handoff(handoff_root, handoff_id))
        matches: list[dict[str, Any]] = []
        for relative in manifest["allowed_paths"]:
            candidate = safe_project_file(project_root, relative)
            if candidate is None or candidate.suffix.lower() != ".md":
                continue
            for line_number, line in enumerate(
                candidate.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if query.casefold() in line.casefold():
                    matches.append(
                        {"path": relative, "line": line_number, "text": line[:500]}
                    )
                    if len(matches) >= 50:
                        return matches
        return matches

    return server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root")
    parser.add_argument("--handoff-root")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default="streamable-http",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8123)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.host != "127.0.0.1":
        raise SystemExit("本地服务仅允许绑定 127.0.0.1")
    try:
        project_root = resolve_project_root(args.project_root)
        handoff_root = configured_handoff_root(project_root, args.handoff_root)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(str(error)) from error
    build_server(project_root, handoff_root, args.host, args.port).run(
        transport=args.transport
    )


if __name__ == "__main__":
    main()
