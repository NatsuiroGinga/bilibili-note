#!/usr/bin/env python3
"""为中断的第三章 XGBoost 父运行生成独立恢复证明。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

PARENT_RUN_ID = "ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1"
PROOF_SCHEMA_VERSION = "ch3-xgb-parent-recovery-proof-v1"
PROOF_FILENAME = "parent-recovery-proof.json"
N_TREE = 800
EXPECTED_PARENT_CONFIG_SHA256 = (
    "75a38b94a28d892d728f06f046eef747a8e738ea3fe0c912c80cf85631185b00"
)
EXPECTED_SHA256 = {
    "selection_frozen_xgb2x2.json": (
        "a9075653efc6b29b6eb9d72f04409781af18e7c65cb31c1ba9bac941e1293943"
    ),
    "effective_config_receipts.json": (
        "657c9f88b3c37f15e48817b145ad8bb22b8f4edd5ba700742b945c84c413515d"
    ),
    "model_raw83.json": (
        "fcff042b8621812d8ed781e5571edae36ec8c9d43ec4840e6b27ae9a0302e218"
    ),
    "model_semantic168.json": (
        "1805e15d96ac4ebb57df910640a4c5e1af58f692659db2eb80b724851efe42e9"
    ),
}
MODEL_NAMES = (
    "model_raw83.json",
    "model_semantic168.json",
    "model_oof_semantic168_fold0.json",
    "model_oof_semantic168_fold1.json",
    "model_oof_semantic168_fold2.json",
)
REQUIRED_EFFECTIVE_TAGS = {
    "raw83/final",
    "semantic168/final",
    "semantic168/fold0",
    "semantic168/fold1",
    "semantic168/fold2",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def atomic_json(path: Path, value: Any) -> None:
    partial = path.with_name(f"{path.name}.partial")
    with partial.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    partial.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="为中断的第三章 XGBoost 父运行生成独立恢复证明"
    )
    parser.add_argument("--parent-run-root", type=Path, required=True)
    parser.add_argument("--parent-config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def validate_parent_identity(parent: Path, parent_config: Path, out: Path) -> None:
    if parent.name != PARENT_RUN_ID:
        raise SystemExit(f"父运行身份不符：{parent.name}")
    if parent == out or parent in out.parents:
        raise SystemExit("恢复证明目录必须独立于父运行目录")
    if not parent_config.is_file():
        raise SystemExit(f"父配置缺失：{parent_config}")
    actual_config_sha = sha256_file(parent_config)
    if actual_config_sha != EXPECTED_PARENT_CONFIG_SHA256:
        raise SystemExit("父配置摘要不符")
    config = load_json(parent_config)
    if config.get("run_id") != PARENT_RUN_ID:
        raise SystemExit("父配置运行身份不符")
    if config.get("seed") != 42 or config.get("num_boost_round") != N_TREE:
        raise SystemExit("父配置种子或树数不符")


def validate_incomplete_state(parent: Path) -> dict[str, Any]:
    status_path = parent / "status.json"
    if not status_path.is_file():
        raise SystemExit(f"父状态缺失：{status_path}")
    status = load_json(status_path)
    if (
        status.get("run_id") != PARENT_RUN_ID
        or status.get("state") != "running"
        or status.get("stage") != "source_selection"
        or status.get("exit_code") is not None
    ):
        raise SystemExit("父状态不符合已核验的中断状态")
    missing = []
    for name in ("xgb_cpa_elp_results.json", "manifest.json"):
        if (parent / name).exists():
            raise SystemExit(f"父运行出现原先缺失的完成制品，拒绝生成恢复证明：{name}")
        missing.append(name)
    return {
        "complete": False,
        "historical_status": {
            "filename": status_path.name,
            "sha256": sha256_file(status_path),
            "bytes": status_path.stat().st_size,
            "state": status["state"],
            "stage": status["stage"],
            "detail": status.get("detail"),
            "exit_code": status["exit_code"],
        },
        "known_interruption": {
            "stage": "LSPR24 semantic168 前缀构造",
            "observed_completion_fraction_approx": 0.816,
            "evidence": "2026-08-19 远端只读日志与制品核验",
        },
        "missing_completion_artifacts": missing,
    }


def validate_selection(parent: Path) -> dict[str, Any]:
    selection = load_json(parent / "selection_frozen_xgb2x2.json")
    if selection.get("run_name") != PARENT_RUN_ID:
        raise SystemExit("父选择收据运行身份不符")
    if selection.get("seed") != 42 or selection.get("num_boost_round") != N_TREE:
        raise SystemExit("父选择收据种子或树数不符")
    if selection.get("xgboost_version") != "3.2.0":
        raise SystemExit("父选择收据 XGBoost 版本不符")
    if selection.get("adapter_selection", {}).get("selected") != "semantic168":
        raise SystemExit("父选择收据适配器不符")
    p_selection = selection.get("p_selection", {})
    if float(p_selection.get("raw83", {}).get("p_selected", -1)) != 2.0:
        raise SystemExit("父选择收据 raw83 的 p 不符")
    if float(p_selection.get("semantic168", {}).get("p_selected", -1)) != 1.0:
        raise SystemExit("父选择收据 semantic168 的 p 不符")
    for view in ("raw83", "semantic168"):
        if int(selection.get("final_models", {}).get(view, {}).get("n_tree", -1)) != N_TREE:
            raise SystemExit(f"父选择收据最终模型树数不符：{view}")
    return {
        "selected_adapter": "semantic168",
        "p_raw83": 2.0,
        "p_semantic168": 1.0,
        "seed": 42,
        "num_boost_round": N_TREE,
    }


def validate_effective_receipts(parent: Path) -> dict[str, Any]:
    receipts = load_json(parent / "effective_config_receipts.json")
    if not isinstance(receipts, list) or len(receipts) != 11:
        raise SystemExit("父有效配置收据必须恰有 11 项")
    if any(not isinstance(item, dict) or item.get("passed") is not True for item in receipts):
        raise SystemExit("父有效配置收据存在未通过项")
    tags = [str(item.get("tag")) for item in receipts]
    if len(set(tags)) != len(tags):
        raise SystemExit("父有效配置收据标签重复")
    missing_tags = REQUIRED_EFFECTIVE_TAGS.difference(tags)
    if missing_tags:
        raise SystemExit(f"父有效配置收据缺少依赖标签：{sorted(missing_tags)}")
    return {
        "receipt_count": len(receipts),
        "all_passed": True,
        "required_dependency_tags": sorted(REQUIRED_EFFECTIVE_TAGS),
        "all_tags": sorted(tags),
    }


def artifact_receipt(path: Path, expected_sha256: str | None = None) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise SystemExit(f"父运行制品缺失或为空：{path}")
    actual_sha256 = sha256_file(path)
    if expected_sha256 is not None and actual_sha256 != expected_sha256:
        raise SystemExit(f"父运行制品摘要不符：{path.name}")
    return {"bytes": path.stat().st_size, "sha256": actual_sha256}


def main() -> None:
    args = parse_args()
    parent = args.parent_run_root.resolve()
    parent_config = args.parent_config.resolve()
    out = args.out.resolve()
    proof_path = out / PROOF_FILENAME
    validate_parent_identity(parent, parent_config, out)
    if proof_path.exists():
        raise SystemExit(f"恢复证明已存在，禁止覆盖：{proof_path}")

    parent_state = validate_incomplete_state(parent)
    selection_summary = validate_selection(parent)
    effective_summary = validate_effective_receipts(parent)

    artifacts: dict[str, dict[str, Any]] = {}
    for name, expected_sha256 in EXPECTED_SHA256.items():
        artifacts[name] = artifact_receipt(parent / name, expected_sha256)

    import xgboost as xgb

    if xgb.__version__ != "3.2.0":
        raise SystemExit(f"恢复证明生成环境的 XGBoost 版本不符：{xgb.__version__}")

    for name in MODEL_NAMES:
        path = parent / name
        if name not in artifacts:
            artifacts[name] = artifact_receipt(path)
        receipt = artifacts[name]
        booster = xgb.Booster()
        booster.load_model(path)
        tree_count = int(booster.num_boosted_rounds())
        if tree_count != N_TREE:
            raise SystemExit(f"父模型树数不是 {N_TREE}：{name}={tree_count}")
        receipt["num_boosted_rounds"] = tree_count

    proof = {
        "schema_version": PROOF_SCHEMA_VERSION,
        "proof_role": "事后恢复核验证明，不是父运行原生 manifest.json",
        "parent_run_id": PARENT_RUN_ID,
        "parent_run_root": str(parent),
        "parent_config": {
            "path": str(parent_config),
            "bytes": parent_config.stat().st_size,
            "sha256": sha256_file(parent_config),
        },
        "parent_state": parent_state,
        "selection_contract": selection_summary,
        "effective_config_receipts": effective_summary,
        "artifacts": artifacts,
        "sourced_from_existing_parent_artifacts_only": True,
        "does_not_assert_parent_completion": True,
    }
    out.mkdir(parents=True, exist_ok=False)
    atomic_json(proof_path, proof)
    print(f"PARENT_RECOVERY_PROOF_WRITTEN path={proof_path}", flush=True)


if __name__ == "__main__":
    main()
