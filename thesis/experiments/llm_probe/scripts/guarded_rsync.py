#!/usr/bin/env python3
"""只同步白名单单文件并核对远端 SHA-256。"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Callable, Sequence

from guarded_execution_common import (
    PROJECT_ROOT,
    REMOTE_PROJECT_ROOT,
    GuardViolation,
    atomic_write_json,
    local_receipt_path,
    normalize_project_file,
    resolve_regular_file,
    sha256_file,
)

GPU_EXEC = Path("/tmp/gpu-exec.exp")
GPU_RSYNC = Path("/tmp/gpu-rsync-push.exp")
HASH_PATTERN = re.compile(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", re.IGNORECASE)
ANSI_ESCAPE_PATTERN = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
CONTROL_CHARACTER_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
CREDENTIAL_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(password|passwd|token|secret)\b(\s*[:=]\s*)(?:\S+)"
)
REMOTE_ADDRESS_PATTERN = re.compile(r"\b[^\s@]+@[^\s:]+")
SSH_PORT_PATTERN = re.compile(r"(?<=-p\s)\d{2,5}\b")
SSH_HOST_PORT_PATTERN = re.compile(r"(?i)(\bhost\s+)([^\s]+)(\s+port\s+)(\d{1,5})")
MAX_DIAGNOSTIC_CHARACTERS = 2_000
Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class SyncPlan:
    """一次白名单同步的不可变计划。"""

    source_relative: str
    destination_relative: str
    source_absolute: str
    remote_absolute: str
    sha256: str


class ManagedCommandFailure(GuardViolation):
    """携带已脱敏子进程诊断的受管命令失败。"""

    def __init__(
        self,
        message: str,
        *,
        step: str,
        result: subprocess.CompletedProcess[str],
    ) -> None:
        super().__init__(message)
        self.diagnostic: dict[str, object] = {
            "step": step,
            "exit_code": result.returncode,
            "stdout": _sanitize_diagnostic_text(result.stdout),
            "stderr": _sanitize_diagnostic_text(result.stderr),
        }


def build_sync_plan(
    source: str,
    destination: str | None = None,
    project_root: Path = PROJECT_ROOT,
) -> SyncPlan:
    source_relative = normalize_project_file(source)
    destination_relative = normalize_project_file(destination or source)
    source_absolute = resolve_regular_file(project_root, source_relative)
    remote_absolute = REMOTE_PROJECT_ROOT.joinpath(*destination_relative.parts)
    return SyncPlan(
        source_relative=source_relative.as_posix(),
        destination_relative=destination_relative.as_posix(),
        source_absolute=str(source_absolute),
        remote_absolute=remote_absolute.as_posix(),
        sha256=sha256_file(source_absolute),
    )


def _run(runner: Runner, argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return runner(
        list(argv),
        text=True,
        capture_output=True,
        check=False,
    )


def _sensitive_environment_values() -> tuple[str, ...]:
    values: list[str] = []
    for name, value in os.environ.items():
        upper_name = name.upper()
        if not value:
            continue
        if (
            upper_name in {"GPU_PWD", "GPU_SSH"}
            or upper_name.endswith("_PWD")
            or any(marker in upper_name for marker in ("PASSWORD", "TOKEN", "SECRET"))
        ):
            values.append(value)
    return tuple(sorted(set(values), key=len, reverse=True))


def _sanitize_diagnostic_text(value: str | None) -> str:
    """保留诊断语义，同时移除凭据、远端地址和控制字符。"""
    text = value or ""
    for secret in _sensitive_environment_values():
        text = text.replace(secret, "<凭据已脱敏>")
    text = ANSI_ESCAPE_PATTERN.sub("", text)
    text = CREDENTIAL_ASSIGNMENT_PATTERN.sub(r"\1\2<凭据已脱敏>", text)
    text = REMOTE_ADDRESS_PATTERN.sub("<远端地址已脱敏>", text)
    text = SSH_PORT_PATTERN.sub("<端口已脱敏>", text)
    text = SSH_HOST_PORT_PATTERN.sub(
        r"\1<远端地址已脱敏>\3<端口已脱敏>",
        text,
    )
    text = CONTROL_CHARACTER_PATTERN.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if len(text) > MAX_DIAGNOSTIC_CHARACTERS:
        text = f"{text[:MAX_DIAGNOSTIC_CHARACTERS]}\n<诊断已截断>"
    return text


def _raise_command_failure(
    message: str,
    *,
    step: str,
    result: subprocess.CompletedProcess[str],
) -> None:
    raise ManagedCommandFailure(message, step=step, result=result)


def prepare_remote_parent(
    plan: SyncPlan,
    runner: Runner = subprocess.run,
) -> dict[str, object]:
    """只创建并验证目标父目录，不执行文件传输。"""
    if not GPU_EXEC.is_file():
        raise GuardViolation("缺少固定的 GPU Expect 命令入口。")

    remote_path = PurePosixPath(plan.remote_absolute)
    prepare_command = (
        f"mkdir -p -- {shlex.quote(remote_path.parent.as_posix())} && "
        f"test -d {shlex.quote(remote_path.parent.as_posix())}"
    )
    prepare = _run(runner, ["expect", str(GPU_EXEC), prepare_command])
    if prepare.returncode != 0:
        _raise_command_failure(
            "远端目标父目录创建或验证失败。",
            step="prepare",
            result=prepare,
        )
    return {"prepare_exit_code": prepare.returncode}


def apply_sync_plan(
    plan: SyncPlan, runner: Runner = subprocess.run
) -> dict[str, object]:
    """创建父目录、同步并验证远端哈希。"""
    if not GPU_EXEC.is_file() or not GPU_RSYNC.is_file():
        raise GuardViolation("缺少固定的 GPU Expect 入口，拒绝退化为裸 ssh 或 rsync。")

    execution = prepare_remote_parent(plan, runner=runner)

    transfer = _run(
        runner,
        [
            "expect",
            str(GPU_RSYNC),
            plan.source_absolute,
            plan.remote_absolute,
        ],
    )
    if transfer.returncode != 0:
        _raise_command_failure(
            "受管 rsync 返回非零状态。",
            step="transfer",
            result=transfer,
        )

    hash_command = f"sha256sum -- {shlex.quote(plan.remote_absolute)}"
    verification = _run(runner, ["expect", str(GPU_EXEC), hash_command])
    if verification.returncode != 0:
        _raise_command_failure(
            "远端 SHA-256 查询失败。",
            step="verify",
            result=verification,
        )
    hashes = {value.lower() for value in HASH_PATTERN.findall(verification.stdout)}
    if plan.sha256.lower() not in hashes:
        raise GuardViolation("同步后远端 SHA-256 与本地源文件不一致。")
    return {
        **execution,
        "transfer_exit_code": transfer.returncode,
        "verify_exit_code": verification.returncode,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="仓库内白名单相对源文件")
    parser.add_argument("--destination", help="仓库内白名单相对远端目标")
    parser.add_argument("--receipt", help="runs/ 下的本地 JSON 收据")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--apply", action="store_true", help="实际执行同步；默认只生成计划"
    )
    mode.add_argument(
        "--prepare-only",
        action="store_true",
        help="仅创建并验证远端父目录，不传输文件",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    receipt: Path | None = None
    try:
        plan = build_sync_plan(args.source, args.destination)
        receipt = local_receipt_path(args.receipt, "guarded-rsync")
        payload: dict[str, object] = {
            "schema_version": 1,
            "operation": "guarded_rsync",
            "status": "planned",
            "applied": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "plan": asdict(plan),
        }
        if args.apply:
            payload["execution"] = apply_sync_plan(plan)
            payload["status"] = "finished"
            payload["applied"] = True
        elif args.prepare_only:
            payload["execution"] = prepare_remote_parent(plan)
            payload["status"] = "prepared"
        atomic_write_json(receipt, payload)
        print(json.dumps({"status": payload["status"], "receipt": str(receipt)}))
        return 0
    except (GuardViolation, OSError) as error:
        if receipt is not None:
            failed_payload: dict[str, object] = {
                "schema_version": 1,
                "operation": "guarded_rsync",
                "status": "failed",
                "error": str(error),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            if isinstance(error, ManagedCommandFailure):
                failed_payload["diagnostic"] = error.diagnostic
            atomic_write_json(
                receipt,
                failed_payload,
            )
        print(f"guarded_rsync: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
