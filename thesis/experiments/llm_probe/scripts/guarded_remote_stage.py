#!/usr/bin/env python3
"""同步已核验脚本与参数，并通过固定服务器入口执行一次阶段。"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Callable

from guarded_execution_common import (
    PROJECT_ROOT,
    REMOTE_PROJECT_ROOT,
    GuardViolation,
    atomic_write_json,
    local_receipt_path,
    normalize_project_file,
    normalize_run_artifact,
    resolve_regular_file,
    sha256_file,
)
from guarded_rsync import (
    GPU_EXEC,
    ManagedCommandFailure,
    apply_sync_plan,
    build_sync_plan,
)

REMOTE_RUNNER = PurePosixPath("scripts/guarded_remote_runner.py")
REMOTE_COMMON = PurePosixPath("scripts/guarded_execution_common.py")
Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class RemoteStagePlan:
    """受管远程阶段的完整不可变计划。"""

    script: str
    params: str
    log: str
    state: str
    capabilities: str
    script_sha256: str
    params_sha256: str


def build_stage_plan(
    *,
    script: str,
    params: str,
    log: str,
    state: str,
    capabilities: str,
    project_root: Path = PROJECT_ROOT,
) -> RemoteStagePlan:
    script_relative = normalize_project_file(script)
    params_relative = normalize_project_file(params)
    if script_relative.parts[0] != "scripts" or script_relative.suffix != ".sh":
        raise GuardViolation("阶段入口必须是 scripts/ 下的 Shell 文件。")
    if params_relative.parts[0] != "configs" or params_relative.suffix not in {
        ".json",
        ".yaml",
        ".yml",
    }:
        raise GuardViolation("阶段参数必须是 configs/ 下的 JSON 或 YAML 文件。")

    script_path = resolve_regular_file(project_root, script_relative)
    params_path = resolve_regular_file(project_root, params_relative)
    if params_relative.suffix == ".json":
        try:
            payload = json.loads(params_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise GuardViolation("阶段 JSON 参数无法解析。") from error
        if not isinstance(payload, dict):
            raise GuardViolation("阶段 JSON 参数顶层必须是对象。")
    elif params_path.stat().st_size == 0:
        raise GuardViolation("阶段 YAML 参数不得为空。")

    return RemoteStagePlan(
        script=script_relative.as_posix(),
        params=params_relative.as_posix(),
        log=normalize_run_artifact(log, ".log").as_posix(),
        state=normalize_run_artifact(state, ".json").as_posix(),
        capabilities=normalize_run_artifact(capabilities, ".json").as_posix(),
        script_sha256=sha256_file(script_path),
        params_sha256=sha256_file(params_path),
    )


def build_remote_command(plan: RemoteStagePlan) -> str:
    """构造只含白名单相对路径和固定入口的单行载荷。"""
    arguments = [
        "python3",
        REMOTE_RUNNER.as_posix(),
        "--script",
        plan.script,
        "--params",
        plan.params,
        "--log",
        plan.log,
        "--state",
        plan.state,
        "--capabilities",
        plan.capabilities,
        "--script-sha256",
        plan.script_sha256,
        "--params-sha256",
        plan.params_sha256,
    ]
    quoted = " ".join(shlex.quote(value) for value in arguments)
    return (
        "source ~/.bashrc >/dev/null 2>&1; "
        "set -Eeuo pipefail; "
        f"cd {shlex.quote(REMOTE_PROJECT_ROOT.as_posix())}; "
        f"GUARDED_BASHRC_LOADED=1 {quoted}"
    )


def apply_stage_plan(
    plan: RemoteStagePlan,
    runner: Runner = subprocess.run,
) -> dict[str, object]:
    """同步四个固定输入后执行远端阶段。"""
    if not GPU_EXEC.is_file():
        raise GuardViolation("缺少固定 GPU Expect 入口。")
    sync_sources = (
        REMOTE_COMMON.as_posix(),
        REMOTE_RUNNER.as_posix(),
        plan.script,
        plan.params,
    )
    sync_receipts: list[dict[str, object]] = []
    for source in sync_sources:
        sync_plan = build_sync_plan(source)
        execution = apply_sync_plan(sync_plan, runner=runner)
        sync_receipts.append(
            {
                "path": source,
                "sha256": sync_plan.sha256,
                "execution": execution,
            }
        )

    remote = runner(
        ["expect", str(GPU_EXEC), build_remote_command(plan)],
        text=True,
        check=False,
    )
    if remote.returncode != 0:
        raise GuardViolation(f"受管远程阶段返回非零状态 {remote.returncode}。")
    return {
        "sync": sync_receipts,
        "remote_exit_code": remote.returncode,
        "remote_state": str(REMOTE_PROJECT_ROOT.joinpath(plan.state)),
        "remote_capabilities": str(REMOTE_PROJECT_ROOT.joinpath(plan.capabilities)),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", required=True)
    parser.add_argument("--params", required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--capabilities", required=True)
    parser.add_argument("--receipt", help="runs/ 下的本地 JSON 收据")
    parser.add_argument(
        "--apply", action="store_true", help="实际同步并启动；默认只生成计划"
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    receipt = local_receipt_path(args.receipt, "guarded-remote-stage")
    payload: dict[str, object] = {
        "schema_version": 1,
        "operation": "guarded_remote_stage",
        "status": "planned",
        "applied": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        plan = build_stage_plan(
            script=args.script,
            params=args.params,
            log=args.log,
            state=args.state,
            capabilities=args.capabilities,
        )
        payload["plan"] = asdict(plan)
        if args.apply:
            payload["status"] = "running"
            atomic_write_json(receipt, payload)
            payload["execution"] = apply_stage_plan(plan)
            payload["status"] = "finished"
            payload["applied"] = True
        atomic_write_json(receipt, payload)
        print(json.dumps({"status": payload["status"], "receipt": str(receipt)}))
        return 0
    except (GuardViolation, OSError) as error:
        payload["status"] = "failed"
        payload["error"] = str(error)
        if isinstance(error, ManagedCommandFailure):
            payload["diagnostic"] = error.diagnostic
        atomic_write_json(receipt, payload)
        print(f"guarded_remote_stage: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
