#!/usr/bin/env python3
"""分段记录 DRIFT 官方双分支模型在本机 MPS 的启动耗时与资源状态。"""

from __future__ import annotations

import argparse
import gc
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


SCHEMA_VERSION = "ch3-drift-mps-startup-diagnostic-v1"
RUN_IDENTITY = "ch3-drift-mps-startup-diagnostic-v1"
BATCH_SIZE = 128
CLASS_SIZE = BATCH_SIZE // 2
STAGES = (
    "construct_model",
    "load_state_dict_file",
    "apply_state_dict",
    "move_model_to_mps",
    "load_real_batch",
    "first_forward",
    "first_backward",
)
MPS_STAGES = frozenset(STAGES[3:])


def sha256_file(path: Path) -> str:
    """计算文件摘要，不保存文件副本。"""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    """原子发布小型 JSON 状态文件。"""
    partial = path.with_name(path.name + ".partial")
    partial.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    partial.replace(path)


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    """追加资源收据；收据不含域名或成员明文。"""
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def rss_max_bytes() -> int:
    """读取本进程的最大 RSS；macOS 与 Linux 的单位不同。"""
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def resource_snapshot(run_dir: Path, torch: Any, stage: str, point: str) -> dict[str, Any]:
    """采集可解释的进程与磁盘资源状态。"""
    usage = shutil.disk_usage(run_dir)
    return {
        "stage": stage,
        "point": point,
        "monotonic_ns": time.monotonic_ns(),
        "rss_max_bytes": rss_max_bytes(),
        "disk_free_bytes": usage.free,
        "device": "mps",
        "torch_version": str(torch.__version__),
    }


def sync_mps(torch: Any) -> None:
    """等待 MPS 阶段实际完成；PyTorch 2.12 官方签名为无参数调用。"""
    torch.mps.synchronize()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir",
        required=True,
        help="位于 thesis/experiments/llm_probe/runs 下的仓库相对运行目录",
    )
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.batch_size <= 0:
        raise ValueError("batch-size 必须为正数")
    if args.batch_size != BATCH_SIZE:
        raise ValueError(f"batch-size 必须固定为 {BATCH_SIZE}")

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
    data_root = llm_probe_root / "runs/data-raw/drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521/DRIFT_input_eSLD"
    reference_root = llm_probe_root / "runs/source-snapshots/2026-DSN-DRIFT-e20d1fdf56c623993966c6786f61c01f91dec6d2"
    checkpoint = llm_probe_root / "runs/models/drift-official-dsn2026/finetuning.pt"
    tokenizer_path = reference_root / "artifacts/tokenizer/tokenizer-0-30522-both.json"
    benign_path = data_root / "T17_benign_train.parquet"
    dga_path = data_root / "T17_dga_train.parquet"
    model_path = reference_root / "model.py"
    official_tool_path = Path(__file__).with_name("ch3_drift_official_checkpoint_t17_eval.py")
    required_paths = [model_path, checkpoint, tokenizer_path, benign_path, dga_path, official_tool_path]
    for path in required_paths:
        if not path.is_file():
            raise FileNotFoundError(f"必需文件不存在：{path}")

    def stable_path(path: Path) -> str:
        return path.relative_to(repo_root).as_posix()

    official = importlib.import_module("ch3_drift_official_checkpoint_t17_eval")
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "status": "running",
        "run_identity": RUN_IDENTITY,
        "batch_size": BATCH_SIZE,
        "class_counts": {"benign": CLASS_SIZE, "dga": CLASS_SIZE},
        "data_role": "T17 训练开发批资源诊断；不产生训练或方法效果证据",
        "device": str(device),
        "torch_version": str(torch.__version__),
        "mps_synchronize_signature": "()",
        "artifacts": {
            "diagnostic_tool": {"path": stable_path(Path(__file__).resolve()), "sha256": sha256_file(Path(__file__))},
            "official_eval_tool": {"path": stable_path(official_tool_path), "sha256": sha256_file(official_tool_path)},
            "reference_model_py": {"path": stable_path(model_path), "sha256": sha256_file(model_path)},
            "checkpoint": {"path": stable_path(checkpoint), "sha256": sha256_file(checkpoint)},
            "tokenizer": {"path": stable_path(tokenizer_path), "sha256": sha256_file(tokenizer_path)},
            "benign_input": {"path": stable_path(benign_path), "sha256": sha256_file(benign_path)},
            "dga_input": {"path": stable_path(dga_path), "sha256": sha256_file(dga_path)},
        },
        "outputs": {
            "phase_status": stable_path(run_dir / "phase-status.json"),
            "timing": stable_path(run_dir / "timing.json"),
            "resource": stable_path(run_dir / "resource.jsonl"),
        },
    }
    atomic_json(run_dir / "metadata.json", metadata)

    timings: dict[str, dict[str, Any]] = {}
    completed: list[str] = []
    phase_status = {
        "schema_version": SCHEMA_VERSION,
        "status": "running",
        "current_stage": None,
        "current_stage_status": None,
        "completed_stages": completed,
        "last_completed_stage": None,
        "error_class": None,
    }
    atomic_json(run_dir / "phase-status.json", phase_status)
    atomic_json(run_dir / "timing.json", {"schema_version": SCHEMA_VERSION, "status": "running", "stages": timings})

    model: Any = None
    checkpoint_state: Any = None
    tokenizer: Any = None
    token_ids: Any = None
    char_ids: Any = None
    labels: Any = None
    logits: Any = None

    def execute_stage(stage: str, action: Callable[[], Any]) -> Any:
        if stage not in STAGES:
            raise ValueError(f"未知诊断阶段：{stage}")
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
        }
        atomic_json(run_dir / "timing.json", {"schema_version": SCHEMA_VERSION, "status": "running", "stages": timings})
        append_jsonl(run_dir / "resource.jsonl", resource_snapshot(run_dir, torch, stage, "before"))
        print(json.dumps({"stage": stage, "status": "running"}, ensure_ascii=False), flush=True)
        try:
            result = action()
            if stage in MPS_STAGES:
                sync_mps(torch)
            finished_ns = time.monotonic_ns()
            timings[stage].update(
                {
                    "status": "completed",
                    "finished_monotonic_ns": finished_ns,
                    "elapsed_seconds": (finished_ns - started_ns) / 1_000_000_000,
                }
            )
            append_jsonl(run_dir / "resource.jsonl", resource_snapshot(run_dir, torch, stage, "after"))
            completed.append(stage)
            phase_status.update(
                {
                    "current_stage_status": "completed",
                    "completed_stages": completed,
                    "last_completed_stage": stage,
                }
            )
            atomic_json(run_dir / "phase-status.json", phase_status)
            atomic_json(run_dir / "timing.json", {"schema_version": SCHEMA_VERSION, "status": "running", "stages": timings})
            print(
                json.dumps(
                    {"stage": stage, "status": "completed", "elapsed_seconds": timings[stage]["elapsed_seconds"]},
                    ensure_ascii=False,
                ),
                flush=True,
            )
            return result
        except BaseException as exc:
            finished_ns = time.monotonic_ns()
            timings[stage].update(
                {
                    "status": "failed",
                    "finished_monotonic_ns": finished_ns,
                    "elapsed_seconds": (finished_ns - started_ns) / 1_000_000_000,
                    "error_class": type(exc).__name__,
                }
            )
            append_jsonl(run_dir / "resource.jsonl", resource_snapshot(run_dir, torch, stage, "failed"))
            phase_status.update(
                {
                    "status": "failed",
                    "current_stage_status": "failed",
                    "error_class": type(exc).__name__,
                }
            )
            atomic_json(run_dir / "phase-status.json", phase_status)
            atomic_json(run_dir / "timing.json", {"schema_version": SCHEMA_VERSION, "status": "failed", "stages": timings})
            print(
                json.dumps({"stage": stage, "status": "failed", "error_class": type(exc).__name__}, ensure_ascii=False),
                file=sys.stderr,
                flush=True,
            )
            raise

    def construct_model() -> Any:
        nonlocal model
        sys.path.insert(0, str(reference_root))
        model_module = importlib.import_module("model")
        token_backbone = model_module.PretrainedModel(30522, 256, 8, 768, 12, 30)
        char_backbone = model_module.PretrainedModel(43, 256, 8, 768, 12, 77)
        model = model_module.FineTuningModel(token_backbone, char_backbone, clf_norm="pool")
        return {"parameters": sum(parameter.numel() for parameter in model.parameters())}

    def load_state_dict_file() -> Any:
        nonlocal checkpoint_state
        checkpoint_state = torch.load(checkpoint, map_location="cpu", weights_only=True)
        return {"state_keys": len(checkpoint_state)}

    def apply_state_dict() -> Any:
        assert model is not None
        assert checkpoint_state is not None
        model.load_state_dict(checkpoint_state, strict=True)
        return {"strict": True}

    def move_model_to_mps() -> Any:
        assert model is not None
        model.eval().to(device)
        return {"model_device": str(next(model.parameters()).device)}

    def load_real_batch() -> Any:
        nonlocal tokenizer, token_ids, char_ids, labels, checkpoint_state
        benign_batches = official.iter_domains(benign_path, CLASS_SIZE, CLASS_SIZE)
        dga_batches = official.iter_domains(dga_path, CLASS_SIZE, CLASS_SIZE)
        benign = next(benign_batches, [])
        dga = next(dga_batches, [])
        if len(benign) != CLASS_SIZE or len(dga) != CLASS_SIZE:
            raise ValueError("T17 两类训练文件无法提供各 64 条真实样本")
        domains = benign + dga
        tokenizer = official.PreTrainedTokenizerFast(tokenizer_file=str(tokenizer_path))
        token_ids = official.encode_subword(domains, tokenizer).to(device)
        char_ids = official.encode_char(domains).to(device)
        labels = torch.tensor([0] * CLASS_SIZE + [1] * CLASS_SIZE, dtype=torch.long, device=device)
        checkpoint_state = None
        gc.collect()
        return {"rows": len(domains), "benign": CLASS_SIZE, "dga": CLASS_SIZE}

    def first_forward() -> Any:
        nonlocal logits
        assert model is not None and token_ids is not None and char_ids is not None
        logits = model(token_ids, char_ids)
        return {"logits_shape": list(logits.shape), "logits_device": str(logits.device)}

    def first_backward() -> Any:
        assert logits is not None and labels is not None
        loss = torch.nn.functional.cross_entropy(logits, labels)
        loss.backward()
        return {"loss_finite": bool(torch.isfinite(loss).item()), "loss_device": str(loss.device)}

    actions: dict[str, Callable[[], Any]] = {
        "construct_model": construct_model,
        "load_state_dict_file": load_state_dict_file,
        "apply_state_dict": apply_state_dict,
        "move_model_to_mps": move_model_to_mps,
        "load_real_batch": load_real_batch,
        "first_forward": first_forward,
        "first_backward": first_backward,
    }
    stage_results: dict[str, Any] = {}
    try:
        for stage in STAGES:
            stage_results[stage] = execute_stage(stage, actions[stage])
    except BaseException:
        metadata["status"] = "failed"
        metadata["stage_results"] = stage_results
        atomic_json(run_dir / "metadata.json", metadata)
        raise

    phase_status.update(
        {
            "status": "completed",
            "current_stage": None,
            "current_stage_status": None,
            "completed_stages": completed,
            "last_completed_stage": completed[-1],
        }
    )
    atomic_json(run_dir / "phase-status.json", phase_status)
    atomic_json(run_dir / "timing.json", {"schema_version": SCHEMA_VERSION, "status": "completed", "stages": timings})
    metadata["status"] = "completed"
    metadata["stage_results"] = stage_results
    atomic_json(run_dir / "metadata.json", metadata)
    print(json.dumps({"status": "completed", "run_dir": str(run_dir)}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
