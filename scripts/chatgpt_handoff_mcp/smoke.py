#!/usr/bin/env python3
"""在独立 Git 项目中验证通用交接 CLI 与 MCP 往返。"""
from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SCRIPT_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_ROOT.parents[1]
CLI = REPOSITORY_ROOT / "tools/chatgpt_handoff.py"
SERVER = SCRIPT_ROOT / "server.py"
SMOKE_ROOT = SCRIPT_ROOT / ".smoke-project"


def run(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(arguments),
        check=check,
        capture_output=True,
        text=True,
    )


def tool_json(result: object, expect_list: bool = False) -> object:
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict) and "result" in structured:
        return structured["result"]
    content = getattr(result, "content")
    values = [json.loads(item.text) for item in content if hasattr(item, "text")]
    if expect_list:
        return values
    value = values[0]
    if isinstance(value, dict) and set(value) == {"result"}:
        return value["result"]
    return value


def prepare_project() -> Path:
    if SMOKE_ROOT.exists():
        shutil.rmtree(SMOKE_ROOT)
    SMOKE_ROOT.mkdir()
    run("git", "init", "-b", "main", str(SMOKE_ROOT))
    run("git", "-C", str(SMOKE_ROOT), "config", "user.name", "Smoke")
    run("git", "-C", str(SMOKE_ROOT), "config", "user.email", "smoke@example.invalid")
    run(
        "git",
        "-C",
        str(SMOKE_ROOT),
        "remote",
        "add",
        "origin",
        "git@github.com:example/handoff-smoke.git",
    )
    (SMOKE_ROOT / "docs").mkdir()
    (SMOKE_ROOT / "docs/context.md").write_text(
        "# 证据\n\n保守纠错需要来源证据。\n",
        encoding="utf-8",
    )
    (SMOKE_ROOT / "paths.txt").write_text("docs/context.md\n", encoding="utf-8")
    run("git", "-C", str(SMOKE_ROOT), "add", "docs/context.md", "paths.txt")
    run("git", "-C", str(SMOKE_ROOT), "commit", "-m", "docs: add smoke context")
    return SMOKE_ROOT


def initialize_and_create(project: Path) -> None:
    init = [sys.executable, str(CLI), "init", "--project-root", str(project)]
    run(*init)
    run(*init)
    run(
        sys.executable,
        str(CLI),
        "create",
        "--project-root",
        str(project),
        "--name",
        "portable-review",
        "--paths",
        str(project / "paths.txt"),
        "--task",
        "只读审查证据边界。",
        "--model",
        "research-model",
        "--effort",
        "high",
        "--fallback-model",
        "fallback-model",
        "--mode",
        "deep-research",
        "--apps",
        "github,zotero",
        "--source-scope",
        "白名单与公开全文",
        "--fulltext-required",
        "--zotero-ingest-required",
    )
    invalid = project / "invalid-paths.txt"
    invalid.write_text("../outside.md\n", encoding="utf-8")
    rejected = run(
        sys.executable,
        str(CLI),
        "create",
        "--project-root",
        str(project),
        "--name",
        "invalid",
        "--paths",
        str(invalid),
        "--task",
        "应被拒绝。",
        check=False,
    )
    if rejected.returncode == 0:
        raise AssertionError("跨项目路径未被拒绝")


async def verify_mcp(project: Path) -> None:
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[
            str(SERVER),
            "--transport",
            "stdio",
            "--project-root",
            str(project),
        ],
    )
    async with stdio_client(parameters) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            expected = {
                "list_handoffs",
                "get_handoff",
                "get_snapshot_manifest",
                "get_execution_profile",
                "search_handoff_context",
            }
            if not expected <= names:
                raise AssertionError(f"MCP 工具缺失：{sorted(expected - names)}")
            listed = await session.call_tool("list_handoffs", {})
            records = tool_json(listed, expect_list=True)
            handoff_id = records[0]["id"]
            manifest_result = await session.call_tool(
                "get_snapshot_manifest", {"handoff_id": handoff_id}
            )
            manifest = tool_json(manifest_result)
            if manifest["requested_model"] != "research-model":
                raise AssertionError("模型字段未往返")
            if manifest["requested_effort"] != "high":
                raise AssertionError("思考强度字段未往返")
            if manifest["requested_mode"] != "deep-research":
                raise AssertionError("模式字段未往返")
            if manifest["requested_apps"] != ["github", "zotero"]:
                raise AssertionError("应用字段未往返")
            profile = await session.call_tool(
                "get_execution_profile", {"handoff_id": handoff_id}
            )
            if profile.isError:
                raise AssertionError("执行配置读取失败")
            searched = await session.call_tool(
                "search_handoff_context",
                {"handoff_id": handoff_id, "query": "保守纠错"},
            )
            matches = tool_json(searched, expect_list=True)
            if not matches or matches[0]["path"] != "docs/context.md":
                raise AssertionError("白名单检索未命中")
            rejected = await session.call_tool(
                "get_handoff", {"handoff_id": "../../etc/passwd"}
            )
            if not rejected.isError:
                raise AssertionError("路径穿越 ID 未被拒绝")


async def main() -> None:
    project = prepare_project()
    try:
        initialize_and_create(project)
        await verify_mcp(project)
        print("跨项目初始化、执行配置、MCP 往返与越界拒绝通过")
    finally:
        shutil.rmtree(project, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())
