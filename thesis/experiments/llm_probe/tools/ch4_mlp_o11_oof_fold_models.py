# -*- coding: utf-8 -*-
"""第四章 D0：全容量 MLP O11 配置的源年三折折外评分模型物化。

目的：O11 最终模型在源年训练区上是样本内的，第四章一切源年诊断、校准与
证书必须使用折外分数。本工具按 E1 冻结的实体三折（标签分层、种子置换轮转）
训练 3 份 O11 配置模型，每个实体的分数此后只来自未见过它的模型。

复用边界：模型结构、训练循环、精度合同与检查点格式全部注入复用
``ch3_full_mlp_complete_entity_lp_protocol_a_q0_bf16``（下称 bf16），训练配方
（含逐折 epoch argmax 选择，LSPR23-only）与正式 O11 完全一致；本工具只改变
训练行子集（剔除留出折实体）。数据缓存沿用 bf16 同一 ``cache_root``，
保持与 O11 谱系同源。LSPR24 零读取。

证据等级：materialization_support（支撑物化），非论文正式证据；
不创建 SwanLab 身份（与 E1 快速门禁家族一致）。
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
import traceback
from pathlib import Path
from typing import Any

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

import ch3_full_mlp_complete_entity_lp_protocol_a_q0 as legacy
import ch3_full_mlp_complete_entity_lp_protocol_a_q0_bf16 as bf16
import neural_precision_runtime as precision

SCHEMA_VERSION = "ch4-mlp-o11-oof-fold-models-config-v1"
RUN_ID = "ch4-mlp-o11-oof-fold-models-seed42-v1"
CELL = "O11"
FOLD_COUNT = 3
T0 = time.time()


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="第四章 D0 全容量 MLP O11 三折折外评分模型物化")
    parser.add_argument("--config", required=True, help="冻结 JSON 配置")
    parser.add_argument("--validate-config", action="store_true", help="只核验配置")
    parser.add_argument("--fold", type=int, choices=(0, 1, 2), help="只训练指定折")
    parser.add_argument("--resume", action="store_true", help="恢复同身份断点")
    return parser.parse_args()


def validate_config(config: dict[str, Any]) -> None:
    if config.get("schema_version") != SCHEMA_VERSION or config.get("run_id") != RUN_ID:
        raise ValueError("配置模式或运行身份不符")
    if config.get("cells") != legacy.CELLS:
        raise ValueError("四格定义必须与正式 O11 谱系一致")
    if config.get("training") != bf16._expected_training():
        raise ValueError("训练配方必须与正式 bf16 O11 完全一致（含逐折 epoch argmax 选择）")
    if config.get("candidate", {}).get("parameter_count") != 2_144_258:
        raise ValueError("候选结构必须是父封印的 8x512 胜出配置")
    fold = config.get("fold_contract")
    if fold != {
        "count": FOLD_COUNT,
        "seed": 42,
        "assignment": "seeded-stratified-entity-round-robin",
        "entity_count": 150_680,
        "positive_entity_count": 239,
        "map_rows_via": "E23",
        "require_each_entity_once_oof": True,
        "e1_run_root": (
            "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/"
            "ch4-e1-source-entity-oof-gate-seed42-v1"
        ),
    }:
        raise ValueError("实体三折合同必须与 E1 冻结合同一致")
    if config.get("target_year_arrays_read") != 0 or config.get("formal_paper_evidence"):
        raise ValueError("目标年隔离或证据身份不符")
    if not config.get("materialization_support"):
        raise ValueError("必须声明 materialization_support 证据等级")
    if Path(config.get("paths", {}).get("output_root", "")).name != RUN_ID:
        raise ValueError("输出根与运行身份不符")
    parent = Path(config["paths"]["parent_selection_receipt"])
    if parent.name != "parent-selection-receipt.json":
        raise ValueError("父选择收据路径不符")


def sha256_array(values: Any) -> str:
    """与 E1 的 sha256_array 逐字节同构：dtype 字符串＋JSON 形状＋连续字节。"""
    import json as _json

    array = legacy.np.ascontiguousarray(values)
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(_json.dumps(array.shape).encode("ascii"))
    digest.update(memoryview(array).cast("B"))
    return digest.hexdigest()


def make_entity_folds(labels: Any, seed: int, count: int) -> Any:
    """与 E1 的 make_entity_folds 完全同构：标签分层、种子置换、轮转分配。"""
    random_state = legacy.np.random.RandomState(seed)
    fold_of_entity = legacy.np.empty(len(labels), dtype=legacy.np.int8)
    for label in (0.0, 1.0):
        entity_ids = legacy.np.flatnonzero(labels == label)
        entity_ids = entity_ids[random_state.permutation(len(entity_ids))]
        fold_of_entity[entity_ids] = legacy.np.arange(len(entity_ids)) % count
    coverage = legacy.np.bincount(fold_of_entity, minlength=count)
    if int(coverage.sum()) != len(labels) or legacy.np.any(coverage == 0):
        raise RuntimeError("实体折覆盖失败")
    return fold_of_entity


def entity_labels_from_source(source: dict[str, Any]) -> Any:
    np = legacy.np
    row_entity = source["E23"]
    seq_flow_labels = source["y23"][source["I23"]] * (source["M23"] > 0)
    row_label = (seq_flow_labels.max(1) > 0).astype(np.float32)
    entity_labels = np.zeros(int(row_entity.max()) + 1, dtype=np.float32)
    np.maximum.at(entity_labels, row_entity, row_label)
    return entity_labels


def crosscheck_e1_fold_sha(config: dict[str, Any], fold_sha: str) -> dict[str, Any]:
    """与 E1 既有收据对账；E1 收据缺失只披露，摘要冲突才阻断（数据合法性硬门）。"""
    e1_root = Path(config["fold_contract"]["e1_run_root"])
    receipts = sorted((e1_root / "receipts").glob("unit-*.json")) if e1_root.is_dir() else []
    for path in receipts:
        try:
            recorded = legacy.load_json(path).get("identity", {}).get("fold_assignment_sha256")
        except Exception:
            continue
        if recorded:
            if recorded != fold_sha:
                raise RuntimeError(
                    f"实体折分配与 E1 冻结不一致：本地 {fold_sha[:16]} vs E1 {recorded[:16]}（{path.name}）"
                )
            return {"e1_receipt": str(path), "matched": True, "sha256": fold_sha}
    log("披露：未找到可对账的 E1 折收据，折分配按同构规则自算（确定性可复算）")
    return {"e1_receipt": None, "matched": None, "sha256": fold_sha}


def install_runtime(config: dict[str, Any]) -> None:
    contract = precision.load_and_validate_contract(bf16.resolve_precision_contract(config))
    profile = precision.get_profile(contract, bf16.PROFILE_ID)
    bf16._CONTRACT = contract
    bf16._PROFILE = profile
    bf16._ACTIVE_CONFIG = config
    bf16.RUN_ID = RUN_ID
    parent_path = Path(config["paths"]["parent_selection_receipt"])
    if not parent_path.is_file():
        raise FileNotFoundError(f"父选择收据不存在：{parent_path}")
    bf16._PARENT_RECEIPT = legacy.load_json(parent_path)


def run(config: dict[str, Any], args: argparse.Namespace, config_path: Path) -> None:
    np = legacy.np
    if legacy.torch is None or not legacy.torch.cuda.is_available():
        raise RuntimeError("D0 物化要求可用 CUDA")
    output_root = Path(config["paths"]["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    frozen_config_path = output_root / "config.json"
    if frozen_config_path.is_file():
        if not args.resume or legacy.load_json(frozen_config_path) != config:
            raise RuntimeError("输出根已有不兼容冻结配置")
    else:
        legacy.atomic_json(frozen_config_path, config)
    legacy.write_status(output_root, "running", "load-source", None, "只加载 LSPR23 冻结缓存")

    cache_root = Path(config["paths"]["cache_root"])
    source = legacy.load_arrays(cache_root, legacy.SOURCE_ARRAYS)
    if source["X23"].shape != (16_353_511, 83) or source["I23"].shape != (271_815, 128):
        raise RuntimeError("LSPR23 冻结缓存形状不符")
    # E23 是逐行（逐序列）实体码；行内实体纯度由冻结缓存合同与 E1 既有核验保证，
    # 此处不重复设门（门禁密度规则：不新增覆盖同一事实的检查）。
    train_rows, validation_rows, split_stats = legacy.source_split(source, config)
    entity_labels = entity_labels_from_source(source)
    fold_contract = config["fold_contract"]
    if len(entity_labels) != fold_contract["entity_count"] or int(entity_labels.sum()) != fold_contract["positive_entity_count"]:
        raise RuntimeError(
            f"实体规模或正实体数不符：{len(entity_labels)}/{int(entity_labels.sum())}"
        )
    fold_of_entity = make_entity_folds(entity_labels, fold_contract["seed"], FOLD_COUNT)
    # E1 的 fold_assignment_sha256 是两层构造：canonical_sha256 包裹 sha256_array，
    # 逐字节复刻其 json.dumps(ensure_ascii=False, sort_keys=True, separators=(",",":"))。
    import json as _json

    inner_payload = _json.dumps(
        {
            "dtype": str(fold_of_entity.dtype),
            "shape": list(fold_of_entity.shape),
            "sha256": sha256_array(fold_of_entity),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    fold_sha = hashlib.sha256(inner_payload.encode("utf-8")).hexdigest()
    crosscheck = crosscheck_e1_fold_sha(config, fold_sha)

    run_identity = {
        "config_sha256": legacy.sha256_file(config_path),
        "code_sha256": legacy.sha256_file(Path(__file__).resolve()),
        "bf16_code_sha256": legacy.sha256_file(Path(bf16.__file__).resolve()),
        "fold_assignment_sha256": fold_sha,
    }
    fold_receipt = {
        "schema_version": "ch4-mlp-o11-oof-fold-assignment-v1",
        "run_id": RUN_ID,
        "fold_assignment_sha256": fold_sha,
        "e1_crosscheck": crosscheck,
        "source_split": split_stats,
        "per_fold": {},
        "persist_fold_membership": False,
        "target_year_arrays_read": 0,
    }
    device = legacy.torch.device("cuda")
    folds = (args.fold,) if args.fold is not None else tuple(range(FOLD_COUNT))
    for k in folds:
        oof_entities = int((fold_of_entity == k).sum())
        oof_positive = int(entity_labels[fold_of_entity == k].sum())
        keep = fold_of_entity[source["E23"][train_rows]] != k
        train_rows_k = train_rows[keep]
        held_out = int(len(train_rows) - len(train_rows_k))
        fold_receipt["per_fold"][str(k)] = {
            "oof_entities": oof_entities,
            "oof_positive_entities": oof_positive,
            "train_sequences": int(len(train_rows_k)),
            "held_out_train_sequences": held_out,
            "train_rows_sha256": sha256_array(train_rows_k),
        }
        legacy.atomic_json(output_root / "fold-assignment-receipt.json", fold_receipt)
        fold_root = output_root / f"fold-{k}"
        for name in ("checkpoints", "receipts", "inflight"):
            (fold_root / name).mkdir(parents=True, exist_ok=True)
        legacy.write_status(
            output_root, "running", f"train-fold-{k}", None,
            f"折外实体 {oof_entities}（正 {oof_positive}），训练序列 {len(train_rows_k)}",
        )
        log(f"fold-{k} 开始：留出实体 {oof_entities}（正 {oof_positive}），训练行 {len(train_rows_k)}/{len(train_rows)}")
        selection = bf16.train_cell(
            config,
            CELL,
            fold_root,
            {**run_identity, "fold": k},
            source,
            train_rows_k,
            validation_rows,
            device,
            args.resume,
        )
        fold_receipt["per_fold"][str(k)]["selection"] = {
            "selected_epoch": selection["selected_epoch"],
            "validation_flow_ap": selection["validation_flow_ap"],
            "p_at_selection": selection["p_at_selection"],
            "training_seconds": selection["training_seconds"],
            "checkpoint": selection["checkpoint"],
        }
        legacy.atomic_json(output_root / "fold-assignment-receipt.json", fold_receipt)
        log(
            f"fold-{k} 完成：epoch={selection['selected_epoch']} "
            f"验证逐流AP={selection['validation_flow_ap']:.8f} p={selection['p_at_selection']:.6f}"
        )
    completed = [str(k) for k in range(FOLD_COUNT) if "selection" in fold_receipt["per_fold"].get(str(k), {})]
    if args.fold is None and len(completed) == FOLD_COUNT:
        legacy.write_status(output_root, "finished", "complete", 0, "三折折外模型物化完成")
    else:
        legacy.write_status(
            output_root, "running", "partial", None, f"已完成折：{completed}"
        )


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()
    config = legacy.load_json(config_path)
    validate_config(config)
    install_runtime(config)
    if args.validate_config:
        print("D0 配置、折合同与精度合同核验通过")
        return 0
    try:
        run(config, args, config_path)
    except Exception as error:
        output_root = Path(config["paths"]["output_root"])
        output_root.mkdir(parents=True, exist_ok=True)
        legacy.write_status(output_root, "failed", "runtime", 1, f"{type(error).__name__}: {error}"[:1000])
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
