#!/usr/bin/env python3
"""生成不含文件内容的普通 ChatGPT 只读交接包。"""
from __future__ import annotations

import argparse
from pathlib import PurePosixPath, Path


FORBIDDEN_PARTS = frozenset({"runs", ".env", ".ssh", "raw"})
FORBIDDEN_SUFFIXES = (".pdf", ".pem", ".key")


def safe_path(value: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"路径不允许越界：{value}")
    lowered = value.lower()
    if any(part.lower() in FORBIDDEN_PARTS for part in path.parts) or lowered.endswith(FORBIDDEN_SUFFIXES):
        raise ValueError(f"路径属于禁止交接范围：{value}")
    if any(token in lowered for token in ("secret", "token", "password", "credential", "id_rsa")):
        raise ValueError(f"路径疑似敏感：{value}")
    return value


def create(args: argparse.Namespace) -> None:
    paths = [safe_path(line.strip()) for line in args.paths.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not paths:
        raise ValueError("路径清单不能为空")
    output = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# ChatGPT 只读交接包", "", "**状态：外部候选，未核验。**", "",
        "## 仓库定位", "", f"- 私有仓库：`{args.repository}`", f"- 远端分支：`{args.branch}`", f"- 冻结提交：`{args.commit}`", "- 允许读取路径：",
        *[f"  - `{path}`" for path in paths], "", "## 任务", "", args.task, "", "## 期望输出", "", "返回 Markdown：结论、逐项证据（路径和行号）、不确定性、未回答问题。不得写代码、修改 GitHub、运行命令或访问未列路径。", "", "## 禁止操作", "", "不得输出秘密、凭据、SSH、数据、权重、检查点、日志、原始 PDF 或大文件内容。结果会进入受管 inbox，仍须由 Codex 独立复核。", "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    command = parser.add_subparsers(dest="command", required=True)
    create_parser = command.add_parser("create", help="生成只读交接包")
    create_parser.add_argument("--repository", required=True)
    create_parser.add_argument("--branch", required=True)
    create_parser.add_argument("--commit", required=True)
    create_parser.add_argument("--paths", required=True, type=Path)
    create_parser.add_argument("--task", required=True)
    create_parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        create(args)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
