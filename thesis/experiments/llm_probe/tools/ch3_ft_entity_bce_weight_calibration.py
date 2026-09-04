#!/usr/bin/env python3
"""实体级 BCE 权重 w_e 的零训练诊断标定。

依据：`thesis/methods/三目标梯度合成设计.md` §5.2／§7.4 方案 B。
仓库根 AGENTS.md 的魔法数字门禁要求六项依据，`w_e = 8192` 唯独缺
「真实数据诊断」一项——本脚本补的就是这一项。

做法：在**一个真实 LSPR23 训练批**上做一次前向，然后分别对
`L_flow`（逐流 BCE 的批均值）与 `L_ent`（实体级 BCE 的逐实体均值）
各反传一次，记录两者对**全部模型参数**的梯度范数，取
`w_e = ‖g_flow‖ / ‖g_ent‖`，使两项在梯度尺度上等权。

**零训练**：不调用 `optimizer.step()`、不写检查点、不创建运行身份、
不产生任何 `runs/` 制品，梯度只读后即弃。`target_reads = 0`（只碰 LSPR23）。

**必须在与正式四臂相同的数值路径上运行**（同设备、同精度 profile），
否则比值不可用——fp32 与 bf16 的范数比不保证一致。

用法（从 llm_probe 目录）：

    python tools/ch3_ft_entity_bce_weight_calibration.py --config <四格任一 C00 配置> [--batches 5]

输出为 JSON，不落盘；调用方自行记录进依据台账。
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import tempfile
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import ch3_ft_c00_dual_selection as dual  # noqa: E402
import ch3_ft_transformer_field_token_protocol_a as base  # noqa: E402


def grad_norm(model, torch_module) -> float:
    """全部可训练参数梯度的 L2 范数（与控制器口径一致：拼接后取全局范数）。"""
    total = None
    for p in model.parameters():
        if p.grad is None:
            continue
        v = p.grad.detach().reshape(-1).to(torch_module.float32)
        s = (v * v).sum()
        total = s if total is None else total + s
    return float(total.sqrt().detach().cpu()) if total is not None else 0.0


def main() -> int:
    ap = argparse.ArgumentParser(description="实体级 BCE 权重的零训练诊断标定")
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--batches", type=int, default=5, help="独立采样的批数，取中位数")
    ap.add_argument(
        "--reuse-transform-from",
        type=Path,
        default=None,
        help="已有运行目录，其 artifacts/sealed-input-transform.pkl 会被复制进本次临时目录，"
             "使 prepare_data 走加载分支而非重新拟合（拟合约需十分钟量级）。"
             "该变换与 d_token 无关（state_hash 逐位相同已实测），故跨档复用合法。",
    )
    args = ap.parse_args()

    config = json.loads(args.config.read_text())
    # 与运行入口第 3369 行同一调用形态：只传 config，函数内部自行按
    # config["base"]["config_path"] 解析并叠加覆写（含 width_profile）。
    base_config = dual.effective_base_config(config)

    torch_module, device, profile, precision = dual.resolve_runtime(config)

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        (out / "receipts").mkdir(parents=True, exist_ok=True)
        (out / "artifacts").mkdir(parents=True, exist_ok=True)
        if args.reuse_transform_from is not None:
            import shutil

            donor = args.reuse_transform_from / "artifacts" / "sealed-input-transform.pkl"
            if not donor.is_file():
                print(json.dumps({"error": f"复用源不存在：{donor}"}, ensure_ascii=False))
                return 1
            shutil.copyfile(donor, out / "artifacts" / "sealed-input-transform.pkl")
        arrays, train_rows, _validation_rows, view = dual.prepare_data(config, base_config, out)

        model, optimizer, _rec = dual.build_model_optimizer(
            config, base_config, view, torch_module, device
        )

        # 正类权重按运行入口同一表达式算，保证 L_flow 与正式训练同口径。
        import numpy as np

        flow_mask = dual.build_training_flow_mask(
            arrays, train_rows, config["training"]["sequence_length"]
        )
        rate = float(np.asarray(arrays["y23"])[flow_mask].mean())
        positive_weight = torch_module.tensor(
            [(1.0 - rate) / max(rate, 1e-12)], dtype=torch_module.float32, device=device
        )

        # 以权重 1.0 构造实体级 BCE 上下文，使 _add_entity_bce_microbatch_loss
        # 返回的增量恰为未加权的 L_ent 本身（0 + 1.0 * value）。
        probe_cfg = json.loads(json.dumps(config))
        probe_cfg.setdefault("mechanism", {})["entity_bce"] = {
            "enabled": True, "weight": 1.0, "aggregation": "maximum",
        }
        ent_ctx = dual._entity_bce_mechanism_config(probe_cfg, arrays["E23"])
        if not ent_ctx["enabled"]:
            print(json.dumps({"error": "实体级 BCE 上下文未启用，检查配置契约"}, ensure_ascii=False))
            return 1

        loss_fn = torch_module.nn.BCEWithLogitsLoss(reduction="none", pos_weight=positive_weight)
        effective = config["training"]["effective_batch_size"]
        micro = config["training"]["micro_batch_sequences"]
        seed = config["training"]["seed"]
        generator = torch_module.Generator().manual_seed(seed)

        samples = []
        model.train()
        for b in range(args.batches):
            positions = base.sample_distinct_positions(len(train_rows), effective, generator)
            rows = train_rows[positions.numpy()]
            indices, valid, labels = view.gather_sequences(
                rows, config["training"]["sequence_length"]
            )
            total_valid = int(valid.sum())

            # 只用第一个微批：本诊断测的是两项梯度的**相对尺度**，
            # 逐微批累积不改变比值，却会把显存和耗时放大 micro 倍。
            stop = min(micro, effective)
            numeric, categorical = view.features(indices[:stop])
            logits, valid_t = dual.forward_bare(
                model, numeric, categorical, valid[:stop], device, profile,
                precision, torch_module, entity_state=None,
            )
            labels_t = torch_module.from_numpy(labels[:stop]).to(device)
            mask32 = valid_t.to(torch_module.float32)

            with precision.fp32_island(
                logits, device_type=device.type, torch_module=torch_module
            ) as (logits32,):
                flow_sum = (loss_fn(logits32, labels_t.to(torch_module.float32)) * mask32).sum()
                # 与累加器同口径：逐流均值。
                flow_mean = flow_sum / max(int(valid[:stop].sum()), 1)
                zero = torch_module.zeros((), dtype=torch_module.float32, device=logits32.device)
                ent_mean = dual._add_entity_bce_microbatch_loss(
                    zero, ent_ctx, logits32, valid_t,
                    rows[:stop], valid[:stop], labels[:stop], torch_module, device,
                )

            optimizer.zero_grad(set_to_none=True)
            flow_mean.backward(retain_graph=True)
            gf = grad_norm(model, torch_module)

            optimizer.zero_grad(set_to_none=True)
            ent_mean.backward()
            ge = grad_norm(model, torch_module)

            optimizer.zero_grad(set_to_none=True)
            samples.append(
                {
                    "batch": b,
                    "grad_norm_flow": gf,
                    "grad_norm_entity": ge,
                    "ratio_w_e": (gf / ge) if ge > 0 else None,
                    "valid_flows_microbatch": int(valid[:stop].sum()),
                    "total_valid_units_effective_batch": total_valid,
                    "loss_flow_mean": float(flow_mean.detach().cpu()),
                    "loss_entity_mean": float(ent_mean.detach().cpu()),
                }
            )

    ratios = [s["ratio_w_e"] for s in samples if s["ratio_w_e"]]
    print(
        json.dumps(
            {
                "schema_version": "ch3-ft-entity-bce-weight-calibration-v1",
                "config": str(args.config),
                "device": str(device),
                "precision_profile_id": config["runtime"].get("precision_profile_id"),
                "width_profile": config.get("model", {}).get("width_profile", "full"),
                "target_reads": 0,
                "training_updates": 0,
                "batches": samples,
                "w_e_median": statistics.median(ratios) if ratios else None,
                "w_e_min": min(ratios) if ratios else None,
                "w_e_max": max(ratios) if ratios else None,
                "note": "w_e = ‖g_flow‖/‖g_entity‖，使两项梯度尺度等权；"
                        "口径为单微批、逐流均值 vs 逐实体均值，不含累加器的 M/N_flow 因子",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
