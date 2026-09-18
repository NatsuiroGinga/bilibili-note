#!/usr/bin/env python3
"""为冻结的 DRIFT 训练入口提供严格 NumPy 标量 JSON 发布兼容层。"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch

ORIGINAL = Path(__file__).with_name("ch3_drift_n10_conservative_fusion_pilot.py")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    partial = path.with_name(path.name + ".partial")
    partial.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(partial, path)


def argument_value(name: str) -> Path:
    try:
        return Path(sys.argv[sys.argv.index(name) + 1]).resolve()
    except (ValueError, IndexError) as error:
        raise ValueError(f"缺少参数：{name}") from error


def argument_text(name: str) -> str:
    try:
        return sys.argv[sys.argv.index(name) + 1]
    except (ValueError, IndexError) as error:
        raise ValueError(f"缺少参数：{name}") from error


def derive_stage_dir(run_root: Path, stage: str, arm: str) -> Path:
    if stage == "p0_c00" and arm == "c00":
        return run_root / "p0_c00"
    if stage == "p1_gate" and arm in {"dynamic", "qmf", "conservative_correction", "constant"}:
        return run_root / "p1_gate" / arm
    raise ValueError("stage 与 arm 组合不合法")


def strict_numpy_dumps(original_dumps: Any) -> Any:
    def dumps(value: Any, *args: Any, **kwargs: Any) -> str:
        supplied = kwargs.pop("default", None)
        def default(item: Any) -> Any:
            if isinstance(item, np.generic):
                return item.item()
            if supplied is not None:
                return supplied(item)
            raise TypeError(f"不允许发布非标量对象：{type(item).__name__}")
        return original_dumps(value, *args, default=default, **kwargs)
    return dumps


def main() -> int:
    if "--help" in sys.argv or "-h" in sys.argv:
        module = import_original()
        return int(module.main())
    if "--print-stage-dir" in sys.argv:
        run_root = argument_value("--run-dir")
        print(derive_stage_dir(run_root, argument_text("--stage"), argument_text("--arm")))
        return 0
    config_path = argument_value("--config")
    run_root = argument_value("--run-dir")
    stage = argument_text("--stage")
    arm = argument_text("--arm")
    stage_dir = derive_stage_dir(run_root, stage, arm)
    before_status = json.loads((stage_dir / "status.json").read_text(encoding="utf-8")) if (stage_dir / "status.json").is_file() else {}
    before_checkpoint = torch.load(stage_dir / "checkpoint.pt", map_location="cpu", weights_only=False) if (stage_dir / "checkpoint.pt").is_file() else None
    if stage == "p0_c00" and before_status.get("status") == "completed" and (stage_dir / "result.json").is_file():
        return 0
    module = import_original()
    code = int(module.main())
    if code != 0:
        return code
    result_path = stage_dir / "result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    current_training = result.get("runtime", {}).pop("training", None)
    recovered_dynamic = before_status.get("status") == "failed" and before_status.get("error_type") == "TypeError" and isinstance(before_checkpoint, dict) and int(before_checkpoint.get("completed_batch", -1)) == 2929 and int(before_checkpoint.get("examples_seen", -1)) == 3000000
    if recovered_dynamic:
        result["runtime"]["training_total"] = {"updates": 2930, "examples_seen": 3000000, "mean_loss": None, "boundary": "由冻结断点恢复；历史均值损失不可恢复，未编造。"}
        result["runtime"]["publication_resume"] = {"updates": 0, "examples_seen": 3000000, "validation_only": True, "wall_seconds": current_training.get("wall_seconds") if isinstance(current_training, dict) else None}
    else:
        result["runtime"]["training_total"] = current_training
    result["serialization_compatibility"] = {"wrapper": "strict_numpy_scalar_item", "original_script_sha256": sha256_file(ORIGINAL)}
    atomic_json(result_path, result)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    p0_checkpoint = run_root / "p0_c00" / "checkpoint.pt"
    receipt = {
        "status": "completed",
        "wrapper_sha256": sha256_file(Path(__file__)),
        "original_script_sha256": sha256_file(ORIGINAL),
        "config_sha256": sha256_file(config_path),
        "p0_checkpoint_sha256": sha256_file(p0_checkpoint),
        "p1_checkpoint_sha256": sha256_file(stage_dir / "checkpoint.pt") if (stage_dir / "checkpoint.pt").is_file() else None,
        "preexisting_failure": {"status": before_status.get("status"), "error_type": before_status.get("error_type")},
        "result_sha256": sha256_file(result_path),
        "run_identity": result["run_identity"],
        "serialization_compatibility": result["serialization_compatibility"],
    }
    atomic_json(stage_dir / "publication-repair.json", receipt)
    return 0


def import_original() -> Any:
    original_dumps = json.dumps
    json.dumps = strict_numpy_dumps(original_dumps)
    spec = importlib.util.spec_from_file_location("ch3_drift_n10_conservative_fusion_pilot", ORIGINAL)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载冻结训练入口")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit(main())
