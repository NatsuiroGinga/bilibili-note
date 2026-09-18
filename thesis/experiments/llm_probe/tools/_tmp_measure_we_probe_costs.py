#!/usr/bin/env python3
"""一次性本机 CPU 测量脚本（用完即删，不进入生产代码）。

测量两件事，供 `thesis/methods/三项损失权重与埋点成本实测.md` 登记：
1. 固定权重下 ``‖g_flow‖`` 与 ``‖g_entity‖`` 在多个真实批次上的分布（w_e 标定）。
2. 方案 A（合并反传）与方案 B（分开反传后相加）的单步相对开销与峰值内存
   （方案 C 的成本由 A/B 的增量摊到 steps_per_epoch 解析导出，不单独起进程测）。

只读取既有实现（``ch3_ft_c00_dual_selection.py``、``ch3_ft_entity_bce.py``、
``neural_precision_runtime.py``），不修改任何生产文件；设备固定 CPU
（``tail_aggregate`` 用 scatter_reduce/index_add，MPS 后端有已知支持缺口，见
``ch3_ft_entity_ranking_loss.py`` 第 397 行附近注释）。数据复用本机已物化的
LSPR23 缓存与已封印输入变换（``ch3-ft-c00-dual-selection-mps-screening-v1`` 运行的
``sealed-input-transform.pkl``），不重新拟合。
"""

from __future__ import annotations

import argparse
import json
import resource
import sys
import time
from pathlib import Path
from typing import Any

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

import ch3_ft_c00_dual_selection as ds  # noqa: E402
import ch3_ft_entity_bce as entity_bce_module  # noqa: E402

PROJECT_ROOT = ds.PROJECT_ROOT
DONOR_RUN_ID = "ch3-ft-c00-dual-selection-mps-screening-v1"
EFFECTIVE_BATCH_SIZE = 64
SEQUENCE_LENGTH = 128
SEED = 42


def build_config(run_id: str) -> dict[str, Any]:
    return {
        "schema_version": "ch3-ft-c00-dual-selection-config-v1",
        "identity": {
            "run_id": run_id,
            "run_tier": "screening_only",
            "candidate_key": "bare-ft-c00-dual-selection",
            "science_contract_version": "ch3-ft-c00-dual-selection-science-v1",
        },
        "base": {
            "config_path": "configs/ch3-ft-transformer-field-token-protocol-a-seed42-v1.json",
            "config_sha256": "a9e11e90792a3106c2e8a3bc9cd3843b3cd4fe405a15656501bf715f05c3929a",
            "tool_path": "tools/ch3_ft_transformer_field_token_protocol_a.py",
            "tool_sha256": "1c8c0cd1ac162149363d13bbda6ca8ec9588424ec494a4c7861d7ce6c347e91b",
        },
        "runtime": {
            "device_type": "cpu",
            "precision_profile_id": "cpu-fp32-v1",
            "allow_device_fallback": False,
            "allow_cpu_op_fallback": False,
        },
        "paths": {
            "cache_root": str(PROJECT_ROOT / "runs/diagnostics/dijk-repro/cache"),
            "cardinality_receipt": str(
                PROJECT_ROOT / "runs/diagnostics/ch3-lspr23-field-cardinality-receipt-v1/field-cardinality-receipt.json"
            ),
            "output_root": str(PROJECT_ROOT / "runs/diagnostics" / run_id),
            "precision_contract": "configs/neural-precision-profiles-v1.json",
        },
        "data": {
            "source_arrays": ["X23", "y23", "I23", "M23", "E23", "T23"],
            "target_reads": 0,
            "input_candidate": "ft-transformer-input-protocol-vocabulary-token",
            "reuse_input_transform_from": DONOR_RUN_ID,
        },
        "model": {
            "role": "bare_ft_transformer",
            "expected_parameter_count": 924283,
            "old_cpa_enabled": False,
            "old_elp_enabled": False,
            "old_mechanism_scaffold_present": False,
        },
        "optimizer": {"candidate_key": "ft-transformer-official-default"},
        "training": {
            "seed": SEED,
            "effective_batch_size": EFFECTIVE_BATCH_SIZE,
            "micro_batch_sequences": EFFECTIVE_BATCH_SIZE,
            "gradient_accumulation_steps": 1,
            "validation_batch_sequences": 1,
            "sequence_length": SEQUENCE_LENGTH,
            "normalization_unit": "valid_flow",
            "selection_metrics": ["validation_flow_ap", "validation_entity_ap"],
            "tie_rule": "strict_argmax_earliest",
        },
        "budget": {
            "state": "unmeasured",
            "epochs": 0,
            "steps_per_epoch": 0,
            "validation_every_epochs": 1,
            "probe_optimizer_steps": 1,
            "basis": "本机 CPU 一次性只读测量脚本，不训练、不产生正式检查点",
        },
    }


def setup(run_id: str):
    import torch

    config = build_config(run_id)
    output_root = Path(config["paths"]["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)

    torch.set_float32_matmul_precision("highest")
    precision = ds.base._precision_module()
    contract = precision.load_and_validate_contract(ds.resolve_project_path(config["paths"]["precision_contract"]))
    profile = precision.validate_runtime_profile(contract, "cpu-fp32-v1", "cpu", torch)
    device = torch.device("cpu")

    base_config = ds.effective_base_config(config)
    arrays, train_rows, validation_rows, view = ds.prepare_data(config, base_config, output_root)
    model, optimizer, _optimizer_receipt = ds.build_model_optimizer(config, base_config, view, torch, device)

    import numpy as np

    training_flow_mask = ds.build_training_flow_mask(arrays, train_rows, SEQUENCE_LENGTH)
    train_positive_rate = float(np.asarray(arrays["y23"])[training_flow_mask].mean())
    positive_weight = torch.tensor(
        [(1.0 - train_positive_rate) / max(train_positive_rate, 1e-12)], dtype=torch.float32, device=device
    )

    import random

    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    generator = torch.Generator().manual_seed(SEED)

    return {
        "torch": torch,
        "np": np,
        "config": config,
        "device": device,
        "profile": profile,
        "precision": precision,
        "arrays": arrays,
        "train_rows": train_rows,
        "view": view,
        "model": model,
        "optimizer": optimizer,
        "positive_weight": positive_weight,
        "generator": generator,
    }


def sample_batch_rows(ctx: dict[str, Any]):
    positions = ds.base.sample_distinct_positions(len(ctx["train_rows"]), EFFECTIVE_BATCH_SIZE, ctx["generator"])
    return ctx["train_rows"][positions.numpy()]


def forward_and_losses(ctx: dict[str, Any], rows, aggregation: str):
    """单次前向，返回 (loss_flow_normalized, loss_entity_normalized, logits32, extra)。

    两者归一化口径均为“均值”：loss_flow 是本批全部有效流的 BCE 均值；loss_entity 是
    entity_bce_loss 已经返回的“本批全部计分实体”的 BCE 均值（4.5 节修正后的口径——
    单微批==全批时，entity_bce_loss 内部的 per_entity_bce[scored_mask].mean() 天然就是
    正确口径，不含 M/N_flow 因子，因为这里没有多微批的累加器参与）。
    """
    torch = ctx["torch"]
    np = ctx["np"]
    view = ctx["view"]
    device = ctx["device"]
    profile = ctx["profile"]
    precision = ctx["precision"]
    positive_weight = ctx["positive_weight"]
    arrays = ctx["arrays"]

    indices, valid, labels = view.gather_sequences(rows, SEQUENCE_LENGTH)
    numeric, categorical = view.features(indices)
    logits, valid_t = ds.forward_bare(
        ctx["model"], numeric, categorical, valid, device, profile, precision, torch,
        site="measure_we_probe_forward",
    )
    labels_t = torch.from_numpy(labels).to(device)
    mask32 = valid_t.to(torch.float32)
    n_flow = int(valid.sum())

    with precision.fp32_island(logits, device_type=device.type, torch_module=torch) as (logits32,):
        loss_fn = torch.nn.BCEWithLogitsLoss(reduction="none", pos_weight=positive_weight)
        loss_flow_sum = (loss_fn(logits32, labels_t.to(torch.float32)) * mask32).sum()
        loss_flow = loss_flow_sum / n_flow

        entity_ids_array = np.asarray(arrays["E23"])
        entity_ids_broadcast = np.broadcast_to(entity_ids_array[rows][:, None], valid.shape)
        flat_valid_np = valid.reshape(-1)
        flat_entity_global = entity_ids_broadcast.reshape(-1)
        flat_labels_np = labels.reshape(-1).astype(np.float32)
        local_entity_ids, local_entity_of_row = np.unique(flat_entity_global, return_inverse=True)
        local_entity_labels = np.zeros(local_entity_ids.shape[0], dtype=np.float32)
        np.maximum.at(local_entity_labels, local_entity_of_row[flat_valid_np], flat_labels_np[flat_valid_np])

        loss_entity, diag = entity_bce_module.entity_bce_loss(
            logits32.reshape(-1),
            valid_t.reshape(-1),
            torch.from_numpy(local_entity_of_row.astype(np.int64)).to(device),
            torch.from_numpy(local_entity_labels).to(device),
            aggregation,
            0.5,
            torch,
        )

    extra = {
        "n_flow": n_flow,
        "n_entity_total": int(local_entity_ids.shape[0]),
        "n_entity_scored": diag["scored_entity_count"],
        "loss_flow": float(loss_flow.detach().item()),
        "loss_entity": float(loss_entity.detach().item()),
    }
    return loss_flow, loss_entity, extra


def measure_we(ctx: dict[str, Any], aggregation: str, num_batches: int) -> dict[str, Any]:
    torch = ctx["torch"]
    model = ctx["model"]
    shared_params = ds._shared_parameters(model)

    records = []
    for batch_index in range(num_batches):
        rows = sample_batch_rows(ctx)
        loss_flow, loss_entity, extra = forward_and_losses(ctx, rows, aggregation)

        model.zero_grad(set_to_none=True)
        loss_flow.backward(retain_graph=True)
        g_flow = ds._flat_grad_from_params(shared_params, torch)

        model.zero_grad(set_to_none=True)
        loss_entity.backward()
        g_entity = ds._flat_grad_from_params(shared_params, torch)

        norm_flow = float(g_flow.norm().item())
        norm_entity = float(g_entity.norm().item())
        record = {
            "batch_index": batch_index,
            "norm_flow": norm_flow,
            "norm_entity": norm_entity,
            "ratio_flow_over_entity": norm_flow / norm_entity if norm_entity > 0 else None,
            **extra,
        }
        records.append(record)
        print(json.dumps({"mode": "we", "aggregation": aggregation, **record}, ensure_ascii=False), flush=True)

    model.zero_grad(set_to_none=True)
    return {"aggregation": aggregation, "num_batches": num_batches, "records": records}


def run_scheme_step(ctx: dict[str, Any], rows, scheme: str, aggregation: str, w_dummy: float) -> float:
    """跑一个完整优化步（zero_grad→前向→反传→optimizer.step()），返回墙钟秒数。

    不做梯度裁剪——本仓库对裸 FT 明令不裁剪梯度（官方 FT-Transformer 配方），
    与 ``no_clip_accumulator_class`` 的既有实现一致。
    """
    torch = ctx["torch"]
    model = ctx["model"]
    optimizer = ctx["optimizer"]

    started = time.perf_counter()
    optimizer.zero_grad(set_to_none=True)
    loss_flow, loss_entity, _extra = forward_and_losses(ctx, rows, aggregation)
    if scheme == "a":
        loss_total = loss_flow + w_dummy * loss_entity
        loss_total.backward()
    elif scheme == "b":
        loss_flow.backward(retain_graph=True)
        loss_entity.backward()
    else:
        raise ValueError(f"未知方案：{scheme}")
    optimizer.step()
    elapsed = time.perf_counter() - started
    return elapsed


def measure_cost(ctx: dict[str, Any], scheme: str, aggregation: str, steps: int, warmup: int) -> dict[str, Any]:
    timings = []
    for step_index in range(warmup + steps):
        rows = sample_batch_rows(ctx)
        elapsed = run_scheme_step(ctx, rows, scheme, aggregation, w_dummy=1.0)
        if step_index >= warmup:
            timings.append(elapsed)
            print(
                json.dumps({"mode": "cost", "scheme": scheme, "step": step_index - warmup, "seconds": elapsed}, ensure_ascii=False),
                flush=True,
            )
    peak_rss_bytes = ds.process_peak_rss_bytes()
    return {"scheme": scheme, "aggregation": aggregation, "steps": steps, "warmup": warmup, "timings_seconds": timings, "peak_rss_bytes": peak_rss_bytes}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["pilot", "we", "cost"])
    parser.add_argument("--aggregation", default="maximum", choices=["maximum", "tail_mean"])
    parser.add_argument("--scheme", default="a", choices=["a", "b"])
    parser.add_argument("--batches", type=int, default=10)
    parser.add_argument("--steps", type=int, default=8)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    run_id = args.run_id or f"ch3-ft-measure-we-probe-cpu-{args.mode}-{args.aggregation}-{args.scheme}"
    ctx = setup(run_id)

    if args.mode == "pilot":
        rows = sample_batch_rows(ctx)
        elapsed = run_scheme_step(ctx, rows, "a", args.aggregation, w_dummy=1.0)
        print(json.dumps({"mode": "pilot", "seconds": elapsed}, ensure_ascii=False))
        return

    if args.mode == "we":
        result = measure_we(ctx, args.aggregation, args.batches)
    else:
        result = measure_cost(ctx, args.scheme, args.aggregation, args.steps, args.warmup)

    if args.out:
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"written: {args.out}", flush=True)


if __name__ == "__main__":
    main()
