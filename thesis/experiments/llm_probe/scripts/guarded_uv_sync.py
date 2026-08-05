#!/usr/bin/env python3
"""先审计 GPU 可选组干运行，再选择性执行 uv 同步。"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Sequence

from guarded_execution_common import (
    PROJECT_ROOT,
    GuardViolation,
    atomic_write_json,
    local_receipt_path,
)


CRITICAL_PACKAGES = frozenset(
    {
        "accelerate",
        "bitsandbytes",
        "flash-attn",
        "peft",
        "swanlab",
        "torch",
        "transformers",
        "triton",
        "trl",
    }
)
REMOVAL_MARKER = re.compile(r"\b(?:remove|removed|removing|uninstall|uninstalled)\b", re.IGNORECASE)
PACKAGE_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
Runner = Callable[..., subprocess.CompletedProcess[str]]


def uv_commands() -> tuple[list[str], list[str]]:
    base = ["uv", "sync", "--locked", "--extra", "gpu"]
    return [*base, "--dry-run"], base


def critical_removals(output: str) -> list[str]:
    """从 uv 干运行文本提取拟移除的关键训练依赖。"""
    hits: set[str] = set()
    for line in output.splitlines():
        lowered = line.lower()
        if not REMOVAL_MARKER.search(lowered) and not lowered.lstrip().startswith("-"):
            continue
        tokens = {token.lower().replace("_", "-") for token in PACKAGE_TOKEN.findall(line)}
        for package in CRITICAL_PACKAGES:
            if package in tokens or package in lowered:
                hits.add(package)
        if any(token.startswith(("nvidia-", "cuda-")) for token in tokens):
            hits.add("cuda-library")
    return sorted(hits)


def _run(
    runner: Runner,
    argv: Sequence[str],
    project_root: Path,
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.setdefault("UV_CACHE_DIR", "/tmp/uv-cache")
    return runner(
        list(argv),
        cwd=project_root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def execute_uv_sync(
    *,
    apply: bool,
    hardware_tier: str,
    runner: Runner = subprocess.run,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    dry_command, apply_command = uv_commands()
    dry_run = _run(runner, dry_command, project_root)
    combined = f"{dry_run.stdout}\n{dry_run.stderr}"
    removals = critical_removals(combined)
    result: dict[str, object] = {
        "dry_run_exit_code": dry_run.returncode,
        "critical_removals": removals,
        "apply_exit_code": None,
        "import_check_exit_code": None,
    }
    if dry_run.returncode != 0:
        raise GuardViolation("uv GPU 可选组干运行失败。")
    if removals:
        raise GuardViolation(f"uv 干运行拟移除关键训练依赖：{', '.join(removals)}")
    if not apply:
        return result

    applied = _run(runner, apply_command, project_root)
    result["apply_exit_code"] = applied.returncode
    if applied.returncode != 0:
        raise GuardViolation("uv GPU 可选组正式同步失败。")

    import_code = (
        "import accelerate,bitsandbytes,peft,swanlab,torch,transformers,trl;"
        "assert "
        + ("torch.cuda.is_available()" if hardware_tier == "gpu" else "True")
    )
    checked = _run(runner, ["uv", "run", "python", "-c", import_code], project_root)
    result["import_check_exit_code"] = checked.returncode
    if checked.returncode != 0:
        raise GuardViolation("关键训练依赖导入或硬件档位验证失败。")
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hardware-tier", choices=("cpu", "gpu"), default="gpu")
    parser.add_argument("--receipt", help="runs/ 下的本地 JSON 收据")
    parser.add_argument("--apply", action="store_true", help="干运行安全后执行正式同步")
    return parser


def main() -> int:
    args = _parser().parse_args()
    receipt = local_receipt_path(args.receipt, "guarded-uv-sync")
    payload: dict[str, object] = {
        "schema_version": 1,
        "operation": "guarded_uv_sync",
        "status": "running" if args.apply else "planned",
        "applied": args.apply,
        "hardware_tier": args.hardware_tier,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        payload["execution"] = execute_uv_sync(
            apply=args.apply,
            hardware_tier=args.hardware_tier,
        )
        payload["status"] = "finished" if args.apply else "planned"
        atomic_write_json(receipt, payload)
        print(json.dumps({"status": payload["status"], "receipt": str(receipt)}))
        return 0
    except (GuardViolation, OSError) as error:
        payload["status"] = "failed"
        payload["error"] = str(error)
        atomic_write_json(receipt, payload)
        print(f"guarded_uv_sync: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
