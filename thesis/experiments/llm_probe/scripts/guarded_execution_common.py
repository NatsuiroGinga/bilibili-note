#!/usr/bin/env python3
"""受管远程包装器共享的路径、哈希和收据工具。"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from typing import Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REMOTE_PROJECT_ROOT = PurePosixPath("/root/autodl-tmp/thesis/experiments/llm_probe")
ALLOWED_FILE_ROOTS = frozenset({"configs", "scripts", "src", "tests"})
ALLOWED_ROOT_FILES = frozenset(
    {
        "README.md",
        "pyproject.toml",
        "uv.lock",
    }
)
DENIED_PARTS = frozenset(
    {
        ".env",
        ".git",
        ".venv",
        "__pycache__",
        "datasets",
        "models",
        "runs",
        "swanlog",
    }
)


class GuardViolation(ValueError):
    """输入违反机械执行合同。"""


def normalize_project_file(value: str) -> PurePosixPath:
    """返回允许同步的仓库相对文件路径。"""
    candidate = PurePosixPath(value)
    if not value or candidate.is_absolute() or value != candidate.as_posix():
        raise GuardViolation("路径必须是规范化的 POSIX 仓库相对路径。")
    if any(part in {"", ".", ".."} for part in candidate.parts):
        raise GuardViolation("路径不得包含空段、当前目录或父目录跳转。")
    if any(part.startswith(".") or part in DENIED_PARTS for part in candidate.parts):
        raise GuardViolation("路径命中隐藏、缓存、数据、模型、运行或凭据禁区。")
    if len(candidate.parts) == 1:
        if candidate.as_posix() not in ALLOWED_ROOT_FILES:
            raise GuardViolation("仓库根文件不在同步白名单。")
    elif candidate.parts[0] not in ALLOWED_FILE_ROOTS:
        raise GuardViolation("路径首段不在代码、配置、脚本或测试白名单。")
    return candidate


def resolve_regular_file(project_root: Path, relative: PurePosixPath) -> Path:
    """解析白名单文件并拒绝符号链接和目录逃逸。"""
    lexical = project_root.joinpath(*relative.parts)
    if lexical.is_symlink():
        raise GuardViolation("同步源不得是符号链接。")
    resolved_root = project_root.resolve()
    resolved = lexical.resolve(strict=True)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as error:
        raise GuardViolation("同步源逃逸项目根目录。") from error
    if not resolved.is_file():
        raise GuardViolation("同步源必须是普通文件。")
    return resolved


def normalize_run_artifact(value: str, suffix: str) -> PurePosixPath:
    """验证远端运行日志或状态制品路径。"""
    candidate = PurePosixPath(value)
    if (
        not value
        or candidate.is_absolute()
        or value != candidate.as_posix()
        or len(candidate.parts) < 2
        or candidate.parts[0] != "runs"
        or any(part in {"", ".", ".."} or part.startswith(".") for part in candidate.parts)
        or candidate.suffix != suffix
    ):
        raise GuardViolation(f"运行制品必须是 runs/ 下的规范化 {suffix} 相对路径。")
    return candidate


def sha256_file(path: Path) -> str:
    """流式计算普通文件的 SHA-256。"""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_write_json(path: Path, payload: Mapping[str, object]) -> None:
    """在同一目录内原子写入 JSON 收据。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def local_receipt_path(value: str | None, stem: str) -> Path:
    """把收据固定在项目的可再生运行目录内。"""
    relative = PurePosixPath(value or f"runs/hook-receipts/{stem}.json")
    if (
        relative.is_absolute()
        or len(relative.parts) < 2
        or relative.parts[0] != "runs"
        or any(part in {"", ".", ".."} or part.startswith(".") for part in relative.parts)
        or relative.suffix != ".json"
    ):
        raise GuardViolation("本地收据必须是 runs/ 下的规范化 JSON 相对路径。")
    return PROJECT_ROOT.joinpath(*relative.parts)
