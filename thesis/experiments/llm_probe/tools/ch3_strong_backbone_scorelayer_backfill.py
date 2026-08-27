#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把分数层 CPA-ELP 四格移植到 FT-Transformer 与 TabM32 的冻结 C00 逐流分数上。

背景与设计取舍（写在这里而不是只写在报告里，供任何重新阅读本文件的人核对）：

- 先例 ``tools/ch3_xgb_cpa_elp_operational_backfill.py`` 与
  ``tools/ch3_xgb_cpa_elp_entity_oof.py`` 的 CPA 机制对 XGBoost 是**特征层**实现
  （semantic168/mean166：把因果前缀均值等派生列拼进原始 83 维，再喂给一个专门在
  这套增广特征上训练过的树模型）。这条路径要求存在一个在增广特征上训练好的模型，
  对 FT-Transformer / TabM32 不成立——本工具能拿到的只有 C00（无机制）单一冻结
  检查点，机制必须在**不重训练**的前提下移植。
- 因此本工具把 CPA 压缩成分数通道上的唯一自然、零参数类比：对同一实体、已发生
  （含当前，即因果）的流，取 C00 原始分数的前缀算术平均，替换原始分数参与后续
  实体聚合。这是"prefix mean"这一支（对应 XGB 的 mean166 视图）在单标量通道上的
  直接类比，不是"residual"那一支（semantic168 的数值残差），因为残差会破坏概率
  值域，与幂平均池化（C11 用到 ``x**p``）不兼容。
- ELP（实体聚合的第二机制）复刻 ``ch3_xgb_cpa_elp_operational_backfill.py`` 224 行
  附近固定的 ``power_mean_p=1.0``（即算术平均），不做超参数搜索；基线聚合固定为
  实体内取最大值，与 ``ch3_neural_backbone_source_oof_gate.py``、
  ``ch3_ft_transformer_field_token_protocol_a.py`` 等同族工具的 C00 定义一致。
- 因此四格是：C00=实体取最大(原始分数)；C01=实体算术平均(原始分数)；
  C10=实体取最大(前缀均值分数)；C11=实体算术平均(前缀均值分数)。全程零训练、
  零超参数搜索、零对目标年的重新拟合。

- LSPR23（源年）与 LSPR24（目标年）各前向一次：目标年四格是决定性数字；源年四格
  只作对称诊断（如同仓库对全容量 MLP 的"源年 bf16 四格"旁证）。

- 2026-08-27 只读核验发现：本工具原计划要回填的 C01/C10/C11 训练缺口，
  两个骨干各自的原生（表示层）协议 A 运行已经在服务器上完整跑完全部四格并完成
  目标年评价（``aggregate-results.json`` 均为 ``state: complete, exit_code: 0``）。
  这意味着"表示层"四格已经是更强证据；本工具产出的"分数层"数字是**独立于该表示层
  训练与选轮噪声的第二条证据链**（详见报告），不是用来补齐缺失格。

模型构建、检查点加载、目标年前向与实体聚合逐字复用两个骨干各自的工具模块
（``build_cell_model``/``build_model``、``score_target``、``entity_scores``、
``load_target_arrays``/``load_source_arrays``、``load_input_transform``、
``resolve_precision_profile``、``_resolve_device``），一律 import，不复制其代码。
源年（LSPR23）全量前向没有现成函数（两个骨干的 ``score_target`` 只覆盖 LSPR24），
本工具按各自 ``score_target`` 的原样结构改写数据源为 LSPR23。
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

TOOL_DIR = Path(__file__).resolve().parent
ROOT = TOOL_DIR.parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

RUN_ID_TEMPLATE = "ch3-{backbone}-scorelayer-cpa-elp-backfill-v1"

BACKBONES: dict[str, dict[str, Any]] = {
    "ft": {
        "module": "ch3_ft_transformer_field_token_protocol_a",
        "config": ROOT / "configs" / "ch3-ft-transformer-field-token-protocol-a-seed42-v1.json",
        "display_name": "FT-Transformer（逐字段Token协议A，C00冻结检查点）",
    },
    "tabm32": {
        "module": "ch3_tabm32_paper_recipe_protocol_a",
        "config": ROOT / "configs" / "ch3-tabm32-paper-recipe-protocol-a-seed42-v1.json",
        "display_name": "TabM32（论文配方协议A，C00冻结检查点）",
    },
}

RESULT_DIR = ROOT / ".Codex" / "docs" / "RWKV" / "artifacts" / "scorelayer-cpa-elp-backfill"

T0 = time.time()


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temporary, path)


# ---------------------------------------------------------------------------
# 分数层 CPA：实体内因果（含自身）前缀算术平均，零参数
# ---------------------------------------------------------------------------


def build_causal_prefix_scores(flow_scores: Any, seen: Any, flow_entity: Any, n_flow: int) -> Any:
    """对每条被计分的流，取同实体、按升序流索引（曝光顺序）、含自身的前缀均值。

    只在 ``seen`` 的子集上构造次序，未被计分的位置保持 0（后续聚合会被 ``seen``
    掩码剔除，不参与统计）。实现与
    ``tools/ch3_xgb_cpa_elp_operational_backfill.py`` 的 ``first_alert_aggregate``
    同一套「实体分段起点+累计和相减」技巧，避免重新发明容易出错的边界处理。
    """
    import numpy as np

    seen_idx = np.flatnonzero(seen)
    # seen_idx 本身按升序流索引排列；对 entity 做稳定排序即可在同实体内保持
    # 升序流索引（曝光顺序），不需要额外的 lexsort。
    order = seen_idx[np.argsort(flow_entity[seen_idx], kind="stable")]
    ordered_entity = flow_entity[order]
    ordered_scores = flow_scores[order].astype(np.float64)
    starts = np.flatnonzero(np.r_[True, ordered_entity[1:] != ordered_entity[:-1]])
    lengths = np.diff(np.r_[starts, len(ordered_entity)]).astype(np.int64)
    position = np.arange(len(ordered_entity), dtype=np.int64) - np.repeat(starts, lengths) + 1
    cumulative = np.cumsum(ordered_scores, dtype=np.float64)
    previous = np.zeros(len(starts), dtype=np.float64)
    previous[1:] = cumulative[starts[1:] - 1]
    running_mean = (cumulative - np.repeat(previous, lengths)) / position
    if not np.isfinite(running_mean).all():
        raise RuntimeError("分数层CPA前缀均值出现非有限值")
    cpa = np.zeros(n_flow, dtype=np.float32)
    cpa[order] = running_mean.astype(np.float32)
    return cpa


# ---------------------------------------------------------------------------
# 实体身份：目标年从 s24/d24 无向对派生，源年从 E23 经 I23/M23 散射到逐流
# ---------------------------------------------------------------------------


def target_entity_identity(target: dict[str, Any]) -> tuple[Any, int, Any]:
    import numpy as np

    key = np.array(
        [
            (left + "|" + right) if left <= right else (right + "|" + left)
            for left, right in zip(target["s24"], target["d24"])
        ],
        dtype=object,
    )
    _, flow_entity = np.unique(key, return_inverse=True)
    flow_entity = flow_entity.astype(np.int64)
    entity_count = int(flow_entity.max()) + 1
    entity_labels = np.zeros(entity_count, dtype=np.float32)
    np.maximum.at(entity_labels, flow_entity, target["y24"])
    return flow_entity, entity_count, entity_labels


def source_entity_identity(source: dict[str, Any]) -> tuple[Any, int, Any, Any]:
    """LSPR23 每个序列位置 E23[row] 是该行全部有效流共享的实体号，散射到逐流。"""
    import numpy as np

    length = source["I23"].shape[1]
    dense_ids, entity_of_seq = np.unique(source["E23"], return_inverse=True)
    entity_count = int(len(dense_ids))
    n_flow = len(source["y23"])
    flow_entity = np.zeros(n_flow, dtype=np.int64)
    seq_seen = np.zeros(n_flow, dtype=bool)
    valid = source["M23"][:, :length] > 0.5
    idx = source["I23"][:, :length]
    entity_broadcast = np.broadcast_to(entity_of_seq[:, None].astype(np.int64), idx.shape)
    flat_valid = valid.reshape(-1)
    flat_idx = idx.reshape(-1)[flat_valid]
    flat_entity = entity_broadcast.reshape(-1)[flat_valid]
    flow_entity[flat_idx] = flat_entity
    seq_seen[flat_idx] = True
    entity_labels = np.zeros(entity_count, dtype=np.float32)
    np.maximum.at(entity_labels, flow_entity[seq_seen], source["y23"][seq_seen])
    return flow_entity, entity_count, entity_labels, seq_seen


# ---------------------------------------------------------------------------
# 源年（LSPR23）全量前向：两个骨干各自 score_target 的结构，换成源年数组
# ---------------------------------------------------------------------------


def score_source_ft(mod: Any, config: dict[str, Any], model: Any, transform: Any, source: dict[str, Any], device: Any, profile: dict[str, Any]) -> tuple[Any, Any]:
    import numpy as np
    import torch

    precision = mod._precision_module()
    length = config["training"]["sequence_length"]
    batch_sequences = config["training"]["micro_batch_sequences"]
    indices_all = source["I23"]
    mask_all = source["M23"]
    labels = source["y23"]
    matrix = source["X23"]
    scores = np.zeros(len(labels), dtype=np.float32)
    seen = np.zeros(len(labels), dtype=bool)
    model.eval()
    with torch.no_grad():
        for start in range(0, len(indices_all), batch_sequences):
            stop = min(start + batch_sequences, len(indices_all))
            indices = np.ascontiguousarray(indices_all[start:stop, :length])
            valid = np.ascontiguousarray(mask_all[start:stop, :length] > 0.5)
            raw = np.asarray(matrix[indices.reshape(-1)], dtype=np.float32)
            numeric, categorical = transform.apply(raw)
            numeric = np.ascontiguousarray(
                numeric.reshape(indices.shape[0], indices.shape[1], transform.numeric_field_count)
            )
            numeric_t = torch.from_numpy(numeric).to(device)
            categorical_t = None
            if categorical is not None:
                categorical = np.ascontiguousarray(
                    categorical.reshape(indices.shape[0], indices.shape[1], transform.vocabulary_field_count)
                )
                categorical_t = torch.from_numpy(categorical).to(device)
            valid_t = torch.from_numpy(valid).to(device)
            with precision.autocast_context(profile, device.type, torch):
                logits = model(numeric_t, categorical_t, valid_t)
            probabilities = model.flow_probability(logits)
            flat_indices = indices.reshape(-1)
            flat_valid = valid.reshape(-1)
            flat_probabilities = probabilities.reshape(-1).float().cpu().numpy()
            selected = flat_indices[flat_valid]
            scores[selected] = flat_probabilities[flat_valid]
            seen[selected] = True
            if (start // batch_sequences) % 2000 == 0:
                log(f"  FT/LSPR23 前向 {stop:,}/{len(indices_all):,}")
    return scores, seen


def score_source_tabm32(mod: Any, config: dict[str, Any], model: Any, transform: Any, source: dict[str, Any], device: Any, profile: dict[str, Any]) -> tuple[Any, Any]:
    import numpy as np
    import torch

    precision = mod._precision_module()
    length = config["training"]["sequence_length"]
    matrix = source["X23"]
    indices_all = source["I23"]
    mask_all = source["M23"]
    labels = source["y23"]
    scores = np.zeros(len(labels), dtype=np.float32)
    seen = np.zeros(len(labels), dtype=bool)
    # 与 score_target 同一批量常量（2026-08-27 OOM 修复后的 effective_batch_size），
    # 不新立未经依据的批量。
    batch_sequences = config["training"]["effective_batch_size"]
    model.eval()
    with torch.no_grad():
        for start in range(0, len(indices_all), batch_sequences):
            stop = min(start + batch_sequences, len(indices_all))
            indices = np.ascontiguousarray(indices_all[start:stop, :length])
            valid = np.ascontiguousarray(mask_all[start:stop, :length] > 0.5)
            raw = np.asarray(matrix[indices.reshape(-1)], dtype=np.float32)
            values = transform.apply(raw).reshape(indices.shape[0], indices.shape[1], transform.output_dimension)
            values_t = torch.from_numpy(values).to(device)
            valid_t = torch.from_numpy(valid).to(device)
            with precision.autocast_context(profile, device.type, torch):
                probabilities = model.shared_batch_flow_probability(values_t, valid_t)
            flat_indices = indices.reshape(-1)
            flat_valid = valid.reshape(-1)
            flat_probabilities = probabilities.reshape(-1).float().cpu().numpy()
            selected = flat_indices[flat_valid]
            scores[selected] = flat_probabilities[flat_valid]
            seen[selected] = True
            if (start // batch_sequences) % 500 == 0:
                log(f"  TabM32/LSPR23 前向 {stop:,}/{len(indices_all):,}")
    return scores, seen


# ---------------------------------------------------------------------------
# 四格构造与判据
# ---------------------------------------------------------------------------


def four_cells(mod: Any, flow_scores: Any, seen: Any, flow_entity: Any, entity_count: int, entity_labels: Any, n_flow: int) -> dict[str, Any]:
    from sklearn.metrics import average_precision_score
    import numpy as np

    cpa_scores = build_causal_prefix_scores(flow_scores, seen, flow_entity, n_flow)
    cells: dict[str, Any] = {}
    for cell_id, source_scores, p_value, score_source in (
        ("C00", flow_scores, None, "raw_c00"),
        ("C01", flow_scores, 1.0, "raw_c00"),
        ("C10", cpa_scores, None, "causal_prefix_mean"),
        ("C11", cpa_scores, 1.0, "causal_prefix_mean"),
    ):
        entity_score = mod.entity_scores(source_scores, seen, flow_entity, entity_count, p_value)
        valid = np.isfinite(entity_score)
        ap = float(average_precision_score(entity_labels[valid], entity_score[valid]))
        cells[cell_id] = {
            "entity_average_precision": ap,
            "entities_scored": int(valid.sum()),
            "pooling": "arithmetic_mean_p1" if p_value is not None else "entity_max",
            "score_source": score_source,
        }
    return cells


def judge(cells: dict[str, Any]) -> dict[str, Any]:
    c00 = cells["C00"]["entity_average_precision"]
    c01 = cells["C01"]["entity_average_precision"]
    c10 = cells["C10"]["entity_average_precision"]
    c11 = cells["C11"]["entity_average_precision"]
    return {
        "elp_positive": c01 > c00,
        "cpa_positive": c10 > c00,
        "joint_best": c11 >= max(c00, c01, c10),
        "elp_effect": c01 - c00,
        "cpa_effect": c10 - c00,
        "combined_effect": c11 - c00,
        "interaction": c11 - c10 - c01 + c00,
    }


# ---------------------------------------------------------------------------
# 单骨干主流程
# ---------------------------------------------------------------------------


def resolve_seal(output_root: Path) -> dict[str, Any]:
    seal_path = output_root / "selection_frozen.json"
    if not seal_path.is_file():
        raise SystemExit(f"缺少 selection_frozen.json：{seal_path}")
    return load_json(seal_path)


def _patch_main_for_unpickle(mod: Any) -> None:
    """两个骨干各自把输入变换用 ``pickle`` 落盘时是作为 ``__main__`` 脚本运行的，

    pickle 因此把 ``FieldTokenTransform``/``InputTransform`` 记成
    ``__main__.<类名>``。本工具把两个骨干模块作为普通子模块 import，
    ``__main__`` 是本文件而非它们，直接 ``pickle.load`` 会因为在当前
    ``__main__`` 命名空间找不到该类而失败。这里只是把已导入模块里的同名类
    对象挂到 ``__main__`` 命名空间，不改变类定义本身，解出来的仍是同一个类。
    """
    main_module = sys.modules["__main__"]
    for class_name in ("FieldTokenTransform", "InputTransform"):
        candidate = getattr(mod, class_name, None)
        if candidate is not None and not hasattr(main_module, class_name):
            setattr(main_module, class_name, candidate)


def build_and_load_c00(mod: Any, module_name: str, config: dict[str, Any], seal: dict[str, Any], output_root: Path, device: Any, profile: dict[str, Any]) -> tuple[Any, Any, Path]:
    import torch

    _patch_main_for_unpickle(mod)
    transform = mod.load_input_transform(output_root / "artifacts" / "sealed-input-transform.pkl")
    checkpoint_path = output_root / "checkpoints" / "selected-C00.pt"
    if not checkpoint_path.is_file():
        raise SystemExit(f"缺少C00冻结检查点：{checkpoint_path}")
    if module_name == "ch3_ft_transformer_field_token_protocol_a":
        model = mod.build_cell_model(config, "C00", transform, input_key=seal["sealed_input_candidate"])
    else:
        model = mod.build_model(config, "C00", seal["sealed_input_candidate"], seal["input_dimension"], profile)
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["model"])
    model = model.to(device)
    model.eval()
    return model, transform, checkpoint_path


def run_backbone(key: str, resume: bool) -> dict[str, Any]:
    import torch

    spec = BACKBONES[key]
    result_path = RESULT_DIR / f"{key}-result.json"
    if resume and result_path.is_file():
        log(f"{key}：已存在结果且传了 --resume，直接复用：{result_path}")
        return load_json(result_path)

    mod = importlib.import_module(spec["module"])
    config = load_json(spec["config"])
    output_root = Path(config["paths"]["output_root"])
    cache_root = Path(config["paths"]["cache_root"])
    seal = resolve_seal(output_root)

    device = mod._resolve_device()
    _, profile, _ = mod.resolve_precision_profile(device.type, torch)

    model, transform, checkpoint_path = build_and_load_c00(
        mod, spec["module"], config, seal, output_root, device, profile
    )
    checkpoint_sha256 = sha256_file(checkpoint_path)

    started = time.time()
    log(f"{key}：开始 LSPR24（目标年）全量前向打分")
    target = mod.load_target_arrays(str(cache_root))
    scores24, seen24 = mod.score_target(config, model, transform, target, device, profile)
    flow_entity24, entity_count24, entity_labels24 = target_entity_identity(target)
    n_flow24 = len(target["y24"])
    cells24 = four_cells(mod, scores24, seen24, flow_entity24, entity_count24, entity_labels24, n_flow24)
    log(
        f"{key}：LSPR24 完成，用时 {time.time() - started:.1f}s，"
        f"C00={cells24['C00']['entity_average_precision']:.6f} "
        f"C01={cells24['C01']['entity_average_precision']:.6f} "
        f"C10={cells24['C10']['entity_average_precision']:.6f} "
        f"C11={cells24['C11']['entity_average_precision']:.6f}"
    )
    del target, scores24, seen24, flow_entity24
    if device.type == "cuda":
        torch.cuda.empty_cache()

    started23 = time.time()
    log(f"{key}：开始 LSPR23（源年，诊断用）全量前向打分")
    source = mod.load_source_arrays(str(cache_root))
    if key == "ft":
        scores23, seen23 = score_source_ft(mod, config, model, transform, source, device, profile)
    else:
        scores23, seen23 = score_source_tabm32(mod, config, model, transform, source, device, profile)
    flow_entity23, entity_count23, entity_labels23, seq_seen23 = source_entity_identity(source)
    seen23_final = seen23 & seq_seen23
    n_flow23 = len(source["y23"])
    cells23 = four_cells(mod, scores23, seen23_final, flow_entity23, entity_count23, entity_labels23, n_flow23)
    log(
        f"{key}：LSPR23 完成，用时 {time.time() - started23:.1f}s，"
        f"C00={cells23['C00']['entity_average_precision']:.6f} "
        f"C11={cells23['C11']['entity_average_precision']:.6f}"
    )
    del source, scores23, seen23, flow_entity23
    if device.type == "cuda":
        torch.cuda.empty_cache()

    result = {
        "schema_version": "ch3-scorelayer-cpa-elp-backfill-v1",
        "run_id": RUN_ID_TEMPLATE.format(backbone=key),
        "backbone": key,
        "display_name": spec["display_name"],
        "checkpoint": {"path": str(checkpoint_path), "sha256": checkpoint_sha256},
        "isolation": {
            "target_retrained": False,
            "source_retrained": False,
            "zero_training": True,
            "hyperparameter_search": False,
            "target_previously_accessed": True,
            "target_informed": True,
            "resource_contention": True,
            "cpa_definition": "分数层：实体内按升序流索引、含自身的因果前缀算术平均（对XGB特征层CPA的mean166支在单标量通道上的类比，非residual支）",
            "elp_definition": "power_mean_p=1.0冻结（算术平均），基线聚合为实体取最大值；无超参数搜索，复刻ch3_xgb_cpa_elp_operational_backfill.py的固定选择",
        },
        "target_lspr24": {
            "cells": cells24,
            "judgement": judge(cells24),
            "entity_count": entity_count24,
            "positive_entity_count": int(entity_labels24.sum()),
        },
        "source_lspr23_diagnostic": {
            "cells": cells23,
            "judgement": judge(cells23),
            "entity_count": entity_count23,
            "positive_entity_count": int(entity_labels23.sum()),
        },
        "wall_seconds": time.time() - started,
        "computed_at_unix": time.time(),
    }
    atomic_json(result_path, result)
    log(f"{key}：结果已原子写入 {result_path}")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FT-Transformer/TabM32 分数层CPA-ELP四格零训练回填")
    parser.add_argument("--backbone", choices=["ft", "tabm32", "all"], default="all")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    keys = list(BACKBONES) if args.backbone == "all" else [args.backbone]
    outcomes: dict[str, Any] = {}
    for key in keys:
        try:
            outcomes[key] = run_backbone(key, args.resume)
        except Exception:  # noqa: BLE001 —— 单骨干失败不得阻塞另一骨干
            logger.exception("%s 失败", key)
            outcomes[key] = {"error": True}
    summary = {
        key: (value.get("target_lspr24", {}).get("judgement") if "error" not in value else "FAILED")
        for key, value in outcomes.items()
    }
    print("BACKFILL_SUMMARY " + json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
