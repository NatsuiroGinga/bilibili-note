#!/usr/bin/env python3
"""在服务器固定项目根内执行已核验脚本并完整记录状态。"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Callable, Sequence, TextIO

from guarded_execution_common import (
    REMOTE_PROJECT_ROOT,
    GuardViolation,
    atomic_write_json,
    normalize_project_file,
    normalize_run_artifact,
    resolve_regular_file,
    sha256_file,
)


HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
REMOTE_ROOT = Path(REMOTE_PROJECT_ROOT.as_posix())
OpenLog = Callable[[Path], TextIO]


@dataclass(frozen=True)
class LoggedResult:
    """主进程和日志写入器的独立状态。"""

    process_exit_code: int | None
    logger_exit_code: int
    log_nonempty: bool
    final_exit_code: int


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _open_log(path: Path) -> TextIO:
    return path.open("w", encoding="utf-8", buffering=1)


def run_logged_process(
    argv: Sequence[str],
    *,
    cwd: Path,
    log_path: Path,
    open_log: OpenLog = _open_log,
) -> LoggedResult:
    """无 `tee` 管道地复制输出，并分别保留主进程和日志状态。"""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        log_handle = open_log(log_path)
    except OSError:
        return LoggedResult(None, 1, False, 1)

    process: subprocess.Popen[str] | None = None
    logger_exit_code = 0
    try:
        process = subprocess.Popen(
            list(argv),
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            try:
                log_handle.write(line)
                log_handle.flush()
            except OSError:
                logger_exit_code = 1
                process.terminate()
                break
            try:
                sys.stdout.write(line)
                sys.stdout.flush()
            except (BrokenPipeError, OSError):
                pass
    finally:
        if process is not None and process.stdout is not None:
            process.stdout.close()
        try:
            log_handle.close()
        except OSError:
            logger_exit_code = 1

    process_exit_code = process.wait() if process is not None else None
    try:
        log_nonempty = log_path.is_file() and log_path.stat().st_size > 0
    except OSError:
        log_nonempty = False

    if process_exit_code not in {None, 0}:
        final_exit_code = process_exit_code
    elif logger_exit_code != 0:
        final_exit_code = logger_exit_code
    elif not log_nonempty:
        final_exit_code = 1
    else:
        final_exit_code = 0
    return LoggedResult(
        process_exit_code,
        logger_exit_code,
        log_nonempty,
        final_exit_code,
    )


def _first_line(argv: Sequence[str]) -> str | None:
    result = subprocess.run(
        list(argv),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    lines = result.stdout.strip().splitlines()
    return lines[0] if lines else None


def collect_capabilities(project_root: Path) -> dict[str, object]:
    """重新探测每个正式阶段所需的命令、硬件和磁盘。"""
    rg_path = shutil.which("rg")
    uv_path = shutil.which("uv")
    if uv_path is None and Path("/root/.local/bin/uv").is_file():
        uv_path = "/root/.local/bin/uv"
    if rg_path is None:
        raise GuardViolation("服务器缺少 rg，禁止使用传统搜索工具降级。")
    if uv_path is None:
        raise GuardViolation("服务器缺少 uv，禁止继续正式阶段。")

    fd_path = shutil.which("fd")
    gpu_path = shutil.which("nvidia-smi")
    disk = shutil.disk_usage(project_root)
    return {
        "schema_version": 1,
        "captured_at": _utc_now(),
        "hostname": socket.gethostname(),
        "project_root": str(project_root),
        "commands": {
            "rg": {"path": rg_path, "version": _first_line([rg_path, "--version"])},
            "uv": {"path": uv_path, "version": _first_line([uv_path, "--version"])},
            "fd": {
                "path": fd_path,
                "version": _first_line([fd_path, "--version"]) if fd_path else None,
                "fallback": None if fd_path else "rg --files",
            },
        },
        "hardware": {
            "nvidia_smi_path": gpu_path,
            "gpu": (
                _first_line(
                    [
                        gpu_path,
                        "--query-gpu=name,memory.total,driver_version",
                        "--format=csv,noheader",
                    ]
                )
                if gpu_path
                else None
            ),
        },
        "disk": {
            "total_bytes": disk.total,
            "used_bytes": disk.used,
            "free_bytes": disk.free,
        },
    }


def _resolve_inputs(
    project_root: Path,
    script_value: str,
    params_value: str,
) -> tuple[Path, Path]:
    script_relative = normalize_project_file(script_value)
    params_relative = normalize_project_file(params_value)
    if script_relative.parts[0] != "scripts" or script_relative.suffix != ".sh":
        raise GuardViolation("远程阶段入口必须是 scripts/ 下的 Shell 文件。")
    if params_relative.parts[0] != "configs" or params_relative.suffix not in {
        ".json",
        ".yaml",
        ".yml",
    }:
        raise GuardViolation("远程阶段参数必须是 configs/ 下的 JSON 或 YAML 文件。")
    return (
        resolve_regular_file(project_root, script_relative),
        resolve_regular_file(project_root, params_relative),
    )


def execute_stage(
    *,
    project_root: Path,
    script_value: str,
    params_value: str,
    log_value: str,
    state_value: str,
    capabilities_value: str,
    expected_script_sha256: str,
    expected_params_sha256: str,
    open_log: OpenLog = _open_log,
) -> int:
    """执行一次阶段并原子维护能力清单和运行状态。"""
    if os.environ.get("GUARDED_BASHRC_LOADED") != "1":
        raise GuardViolation("启动器未证明先加载 bashrc，拒绝执行阶段。")
    if not HASH_PATTERN.fullmatch(expected_script_sha256) or not HASH_PATTERN.fullmatch(
        expected_params_sha256
    ):
        raise GuardViolation("预期输入哈希格式无效。")

    script_path, params_path = _resolve_inputs(project_root, script_value, params_value)
    if sha256_file(script_path) != expected_script_sha256:
        raise GuardViolation("远程脚本 SHA-256 与启动计划不一致。")
    if sha256_file(params_path) != expected_params_sha256:
        raise GuardViolation("远程参数 SHA-256 与启动计划不一致。")

    log_relative = normalize_run_artifact(log_value, ".log")
    state_relative = normalize_run_artifact(state_value, ".json")
    capabilities_relative = normalize_run_artifact(capabilities_value, ".json")
    log_path = project_root.joinpath(*log_relative.parts)
    state_path = project_root.joinpath(*state_relative.parts)
    capabilities_path = project_root.joinpath(*capabilities_relative.parts)

    prepared = {
        "schema_version": 1,
        "stage": script_value,
        "params": params_value,
        "script_sha256": expected_script_sha256,
        "params_sha256": expected_params_sha256,
        "status": "prepared",
        "updated_at": _utc_now(),
    }
    atomic_write_json(state_path, prepared)
    try:
        capabilities = collect_capabilities(project_root)
        capabilities["inputs"] = {
            "script_sha256": expected_script_sha256,
            "params_sha256": expected_params_sha256,
        }
        atomic_write_json(capabilities_path, capabilities)
    except (GuardViolation, OSError) as error:
        prepared.update({"status": "failed", "exit_code": 127, "error": str(error)})
        prepared["updated_at"] = _utc_now()
        atomic_write_json(state_path, prepared)
        return 127

    prepared.update({"status": "running", "updated_at": _utc_now()})
    atomic_write_json(state_path, prepared)
    result = run_logged_process(
        ["bash", str(script_path), str(params_path)],
        cwd=project_root,
        log_path=log_path,
        open_log=open_log,
    )
    prepared.update(
        {
            "status": "finished" if result.final_exit_code == 0 else "failed",
            "exit_code": result.final_exit_code,
            "process_exit_code": result.process_exit_code,
            "logger_exit_code": result.logger_exit_code,
            "log_nonempty": result.log_nonempty,
            "log": log_value,
            "capabilities": capabilities_value,
            "updated_at": _utc_now(),
        }
    )
    atomic_write_json(state_path, prepared)
    return result.final_exit_code


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", required=True)
    parser.add_argument("--params", required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--capabilities", required=True)
    parser.add_argument("--script-sha256", required=True)
    parser.add_argument("--params-sha256", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        return execute_stage(
            project_root=REMOTE_ROOT,
            script_value=args.script,
            params_value=args.params,
            log_value=args.log,
            state_value=args.state,
            capabilities_value=args.capabilities,
            expected_script_sha256=args.script_sha256,
            expected_params_sha256=args.params_sha256,
        )
    except (GuardViolation, OSError) as error:
        print(f"guarded_remote_runner: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
