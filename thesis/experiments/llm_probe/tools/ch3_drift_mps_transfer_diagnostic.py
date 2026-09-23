#!/usr/bin/env python3
"""诊断 DRIFT 官方检查点从 CPU 加载并迁移到 MPS 的四个阶段。"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import resource
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Callable


SCHEMA_VERSION = "ch3-drift-mps-transfer-diagnostic-v1"
RUN_IDENTITY = "ch3-drift-mps-transfer-diagnostic-v1"
STAGES = (
    "construct_model",
    "load_state_dict_file",
    "apply_state_dict",
    "move_model_to_mps",
)
MPS_STAGE = "move_model_to_mps"


def sha256_file(path: Path) -> str:
    """计算既有输入文件摘要，不复制文件。"""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    """原子发布小型 JSON 收据。"""
    partial = path.with_name(path.name + ".partial")
    partial.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    partial.replace(path)


def rss_max_bytes() -> int:
    """读取本进程最大 RSS，兼容 macOS 与 Linux 单位差异。"""
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def resource_snapshot(
    run_dir: Path,
    stage: str,
    point: str,
    *,
    device: str,
    code_sha256: str,
    checkpoint_sha256: str,
    torch_version: str,
) -> dict[str, Any]:
    """记录每阶段所需的资源与输入身份字段。"""
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": stage,
        "point": point,
        "monotonic_ns": time.monotonic_ns(),
        "rss_max_bytes": rss_max_bytes(),
        "disk_free_bytes": shutil.disk_usage(run_dir).free,
        "device": device,
        "torch_version": torch_version,
        "code_sha256": code_sha256,
        "checkpoint_sha256": checkpoint_sha256,
    }


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    """追加资源记录并立即刷盘。"""
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir",
        required=True,
        help="位于 thesis/experiments/llm_probe/runs 下的仓库相对运行目录",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    contract = importlib.import_module("ch3_drift_formal_contract")
    run_dir = contract.resolve_run_dir(args.run_dir)
    if run_dir.exists():
        if not run_dir.is_dir():
            raise FileExistsError(f"运行路径不是目录，拒绝覆盖：{run_dir}")
        existing_entries = list(run_dir.iterdir())
        if any(
            entry.name != "console.log" or entry.is_symlink() or not entry.is_file()
            for entry in existing_entries
        ):
            raise FileExistsError(
                f"运行目录含非 console.log 既有制品，拒绝覆盖：{run_dir}"
            )
    run_dir.mkdir(parents=True, exist_ok=True)

    torch = importlib.import_module("torch")
    if not hasattr(torch.backends, "mps") or not torch.backends.mps.is_available():
        raise RuntimeError("当前环境没有可用的 MPS，诊断只允许在 MPS 环境运行")
    device = torch.device("mps")

    repo_root = Path(__file__).resolve().parents[4]
    llm_probe_root = repo_root / "thesis/experiments/llm_probe"
    reference_root = llm_probe_root / "runs/source-snapshots/2026-DSN-DRIFT-e20d1fdf56c623993966c6786f61c01f91dec6d2"
    checkpoint = llm_probe_root / "runs/models/drift-official-dsn2026/finetuning.pt"
    model_path = reference_root / "model.py"
    script_path = Path(__file__).resolve()
    for path in (model_path, checkpoint):
        if not path.is_file():
            raise FileNotFoundError(f"必需文件不存在：{path}")

    code_sha256 = sha256_file(script_path)
    checkpoint_sha256 = sha256_file(checkpoint)
    torch_version = str(torch.__version__)

    def stable_path(path: Path) -> str:
        return path.relative_to(repo_root).as_posix()

    metadata: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "running",
        "run_identity": RUN_IDENTITY,
        "device": str(device),
        "torch_version": torch_version,
        "mps_synchronize_signature": "()",
        "scope": "仅模型构造、检查点文件加载、状态应用和迁移到 MPS；不执行前向、反向、训练或优化",
        "artifacts": {
            "diagnostic_tool": {"path": stable_path(script_path), "sha256": code_sha256},
            "reference_model_py": {"path": stable_path(model_path), "sha256": sha256_file(model_path)},
            "checkpoint": {"path": stable_path(checkpoint), "sha256": checkpoint_sha256},
        },
        "outputs": {
            "phase_status": stable_path(run_dir / "phase-status.json"),
            "timing": stable_path(run_dir / "timing.json"),
            "resource": stable_path(run_dir / "resource.jsonl"),
        },
    }
    atomic_json(run_dir / "metadata.json", metadata)

    completed: list[str] = []
    phase_status: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "running",
        "current_stage": None,
        "current_stage_status": None,
        "completed_stages": completed,
        "last_completed_stage": None,
        "error_class": None,
    }
    timings: dict[str, dict[str, Any]] = {}
    atomic_json(run_dir / "phase-status.json", phase_status)
    atomic_json(run_dir / "timing.json", {"schema_version": SCHEMA_VERSION, "status": "running", "stages": timings})

    model: Any = None
    checkpoint_state: Any = None

    def execute_stage(stage: str, action: Callable[[], Any]) -> Any:
        """先发布 running，再执行阶段；中止时不覆盖该 running 状态。"""
        started_ns = time.monotonic_ns()
        phase_status.update(
            {
                "status": "running",
                "current_stage": stage,
                "current_stage_status": "running",
                "error_class": None,
            }
        )
        atomic_json(run_dir / "phase-status.json", phase_status)
        timings[stage] = {
            "status": "running",
            "started_monotonic_ns": started_ns,
            "finished_monotonic_ns": None,
            "elapsed_seconds": None,
            "device": str(device),
            "code_sha256": code_sha256,
            "checkpoint_sha256": checkpoint_sha256,
        }
        atomic_json(run_dir / "timing.json", {"schema_version": SCHEMA_VERSION, "status": "running", "stages": timings})
        append_jsonl(run_dir / "resource.jsonl", resource_snapshot(run_dir, stage, "before", device=str(device), code_sha256=code_sha256, checkpoint_sha256=checkpoint_sha256, torch_version=torch_version))
        print(json.dumps({"stage": stage, "status": "running"}, ensure_ascii=False), flush=True)
        try:
            result = action()
            if stage == MPS_STAGE:
                torch.mps.synchronize()
            finished_ns = time.monotonic_ns()
            timings[stage].update(
                {
                    "status": "completed",
                    "finished_monotonic_ns": finished_ns,
                    "elapsed_seconds": (finished_ns - started_ns) / 1_000_000_000,
                }
            )
            append_jsonl(run_dir / "resource.jsonl", resource_snapshot(run_dir, stage, "after", device=str(device), code_sha256=code_sha256, checkpoint_sha256=checkpoint_sha256, torch_version=torch_version))
            completed.append(stage)
            phase_status.update({"current_stage_status": "completed", "completed_stages": completed, "last_completed_stage": stage})
            atomic_json(run_dir / "phase-status.json", phase_status)
            atomic_json(run_dir / "timing.json", {"schema_version": SCHEMA_VERSION, "status": "running", "stages": timings})
            print(json.dumps({"stage": stage, "status": "completed", "elapsed_seconds": timings[stage]["elapsed_seconds"]}, ensure_ascii=False), flush=True)
            return result
        except Exception as exc:
            finished_ns = time.monotonic_ns()
            timings[stage].update({"status": "failed", "finished_monotonic_ns": finished_ns, "elapsed_seconds": (finished_ns - started_ns) / 1_000_000_000, "error_class": type(exc).__name__})
            append_jsonl(run_dir / "resource.jsonl", resource_snapshot(run_dir, stage, "failed", device=str(device), code_sha256=code_sha256, checkpoint_sha256=checkpoint_sha256, torch_version=torch_version))
            phase_status.update({"status": "failed", "current_stage_status": "failed", "error_class": type(exc).__name__})
            atomic_json(run_dir / "phase-status.json", phase_status)
            atomic_json(run_dir / "timing.json", {"schema_version": SCHEMA_VERSION, "status": "failed", "stages": timings})
            raise

    def construct_model() -> dict[str, int]:
        nonlocal model
        sys.path.insert(0, str(reference_root))
        model_module = importlib.import_module("model")
        token_backbone = model_module.PretrainedModel(30522, 256, 8, 768, 12, 30)
        char_backbone = model_module.PretrainedModel(43, 256, 8, 768, 12, 77)
        model = model_module.FineTuningModel(token_backbone, char_backbone, clf_norm="pool")
        return {"parameters": sum(parameter.numel() for parameter in model.parameters())}

    def load_state_dict_file() -> dict[str, int]:
        nonlocal checkpoint_state
        checkpoint_state = torch.load(checkpoint, map_location="cpu", weights_only=True)
        return {"state_keys": len(checkpoint_state)}

    def apply_state_dict() -> dict[str, bool]:
        if model is None or checkpoint_state is None:
            raise RuntimeError("模型或检查点状态尚未准备")
        model.load_state_dict(checkpoint_state, strict=True)
        return {"strict": True}

    def move_model_to_mps() -> dict[str, str]:
        if model is None:
            raise RuntimeError("模型尚未构造")
        model.eval().to(device)
        return {"model_device": str(next(model.parameters()).device)}

    actions: dict[str, Callable[[], Any]] = {
        "construct_model": construct_model,
        "load_state_dict_file": load_state_dict_file,
        "apply_state_dict": apply_state_dict,
        "move_model_to_mps": move_model_to_mps,
    }
    stage_results: dict[str, Any] = {}
    try:
        for stage in STAGES:
            stage_results[stage] = execute_stage(stage, actions[stage])
    except Exception:
        metadata.update({"status": "failed", "stage_results": stage_results})
        atomic_json(run_dir / "metadata.json", metadata)
        raise

    phase_status.update({"status": "completed", "current_stage": None, "current_stage_status": None, "completed_stages": completed, "last_completed_stage": completed[-1]})
    atomic_json(run_dir / "phase-status.json", phase_status)
    atomic_json(run_dir / "timing.json", {"schema_version": SCHEMA_VERSION, "status": "completed", "stages": timings})
    metadata.update({"status": "completed", "stage_results": stage_results})
    atomic_json(run_dir / "metadata.json", metadata)
    print(json.dumps({"status": "completed", "run_dir": str(run_dir)}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
