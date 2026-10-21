#!/usr/bin/env python
"""第四章整合方法通用性补臂：k=2 与 half-width 骨干变体（单一冻结协议）。

来源：`thesis/methods/第四章-整合方法重构决定.md` §四（待补实验）：
1. `k2`：TabMMLP k=2，骨干 512/384/256/128、头 100/100/1 不变，补全 k 曲线 2/4/8；
2. `halfwidth`：TabMMLPWidth k=4，骨干 256/192/128/64、头 64/64/1，
   与 uniform（既有 `tabm4`，标准宽度）做单变量对照。

## 协议（与 `ch4_lamda_tabm_pilot.py` 逐位同源）

- 种子 42；`build_parts`（2×2 模块，quota/deficit/repeat 2、容量 200）；
- `ch3.iterate_batches_parts` 同一数据流；SGD(0.01, 0.9, 1e-6)、batch 1024、10 epoch；
- 优化器每个年度重建；阈值 0.5；12 年 backward 面板 + 逐年度 current-year F1；
- `preds_{arm}_{year}.npz` 与既有 tabm 臂同格式（y_true/y_score/threshold）。

## 成员化结构

- `k2` 直接复用 `ch4_lamda_tabm_pilot.TabMMLP`（BatchEnsembleLinear，首层 r 随机符号 ±1）；
- `halfwidth` 在本脚本内定义 `TabMMLPWidth`：各层 BatchEnsembleLinear、首层 r 随机符号 ±1、
  其余 r=1/s=1/β=0、Dropout 0.2 位置不变；不修改 tabm 原脚本。

## 判据（预登记，非存废）

- k 敏感性只登记 12y mean 随 k∈{2,4,8} 的方向，不作支持/否决判定；
- 宽度变体只登记与 uniform（tabm4）的 12y 差，不作支持/否决判定。

## 运行

    PY=/opt/miniconda3/envs/rwkv/bin/python
    $PY tools/ch4_lamda_general_pilot.py --arm k2
    $PY tools/ch4_lamda_general_pilot.py --arm halfwidth

两臂串行执行；每臂独立进程，避免 RNG 与内存状态跨臂泄漏。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))
import ch3_lamda_domain_il_e4 as ch3  # noqa: E402  （只读导入；不改原脚本）
from ch4_lamda_tabm_pilot import (  # noqa: E402
    THRESHOLD,
    BatchEnsembleLinear,
    TabMMLP,
    f1_of,
    train_epochs_tabm,
)
from ch4_lamda_training_process_2x2 import build_parts  # noqa: E402

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
SEED = ch3.SEED
RUN_DIR = TOOLS_DIR.parent / "runs/diagnostics/ch4-lamda-general-pilot"
TABM_DIR = TOOLS_DIR.parent / "runs/diagnostics/ch4-lamda-tabm-pilot"
ARMS = ("k2", "halfwidth")
ARM_K = {"k2": 2, "halfwidth": 4}

UNIFORM_RESULT = TABM_DIR / "tabm4-result.json"
TABM8_RESULT = TABM_DIR / "tabm8-result.json"


class TabMMLPWidth(nn.Module):
    """半宽骨干的逐层 BatchEnsemble 化（同深、同 Dropout 位置）。

    标准 TabMMLP：512/384/256/128 + 100/100/1；
    本变体：256/192/128/64 + 64/64/1（单变量：只改宽度）。
    """

    def __init__(self, input_dim: int, k: int) -> None:
        super().__init__()
        self.k = k
        self.enc1 = BatchEnsembleLinear(input_dim, 256, k, first=True)
        self.enc2 = BatchEnsembleLinear(256, 192, k, first=False)
        self.enc3 = BatchEnsembleLinear(192, 128, k, first=False)
        self.enc4 = BatchEnsembleLinear(128, 64, k, first=False)
        self.cls1 = BatchEnsembleLinear(64, 64, k, first=False)
        self.cls2 = BatchEnsembleLinear(64, 64, k, first=False)
        self.cls3 = BatchEnsembleLinear(64, 1, k, first=False)
        self.drop = nn.Dropout(0.2)

    def forward(self, x: torch.Tensor, return_members: bool = False) -> torch.Tensor:
        if x.dim() == 2:
            b = x.shape[0]
            h = x.unsqueeze(1).expand(b, self.k, x.shape[1]) * self.enc1.r  # (B,k,in)
        else:
            h = x
        for layer in (self.enc1, self.enc2, self.enc3, self.enc4):
            h = torch.relu(layer(h))
        h = self.drop(torch.relu(self.cls1(h)))
        h = self.drop(torch.relu(self.cls2(h)))
        out = torch.sigmoid(self.cls3(h))                  # (B, k, 1)
        if return_members:
            return out
        return out.mean(dim=1)                             # 推理：成员概率均值


def build_model(arm: str, input_dim: int) -> tuple[nn.Module, dict[str, Any]]:
    if arm == "k2":
        return TabMMLP(input_dim, ARM_K[arm]), {
            "backbone": "TabMMLP",
            "encoder_widths": [512, 384, 256, 128],
            "head_widths": [100, 100, 1],
        }
    if arm == "halfwidth":
        return TabMMLPWidth(input_dim, ARM_K[arm]), {
            "backbone": "TabMMLPWidth",
            "encoder_widths": [256, 192, 128, 64],
            "head_widths": [64, 64, 1],
        }
    raise ValueError(arm)


def _call_first(names: tuple[str, ...]) -> tuple[int | None, str | None]:
    for name in names:
        fn = getattr(torch.mps, name, None)
        if callable(fn):
            return int(fn()), name
    return None, None


def mps_mem_snapshot(label: str) -> dict[str, Any]:
    """采样 MPS 内存（字节）。

    torch 2.12 实测接口名为 `current_allocated_memory` / `driver_allocated_memory`；
    任务简报中的 `*_bytes` 名称在本版本不存在，故按别名顺序兼容读取并记录实际 API。
    """
    if DEVICE.type != "mps":
        return {"label": label, "mps": False}
    torch.mps.synchronize()
    cur, cur_api = _call_first(("current_allocated_bytes", "current_allocated_memory"))
    drv, drv_api = _call_first(("driver_allocated_bytes", "driver_allocated_memory"))
    return {
        "label": label,
        "mps": True,
        "current_allocated_bytes": cur,
        "driver_allocated_bytes": drv,
        "current_api": cur_api,
        "driver_api": drv_api,
    }


def _peak(samples: list[dict[str, Any]], key: str) -> int | None:
    vals = [int(s[key]) for s in samples if s.get(key) is not None]
    return max(vals) if vals else None


def run_arm(arm: str) -> dict[str, Any]:
    k = ARM_K[arm]
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    if DEVICE.type == "mps":
        torch.mps.empty_cache()
    years = list(ch3.DOMAIN_YEARS)
    print(f"[arm] {arm} k={k} device={DEVICE.type}", flush=True)
    print(f"[config] epochs={ch3.OFFICIAL_EPOCHS} batch={ch3.OFFICIAL_BATCH} "
          f"lr={ch3.OFFICIAL_LR} momentum={ch3.OFFICIAL_MOMENTUM} "
          f"weight_decay={ch3.OFFICIAL_WEIGHT_DECAY} memory={ch3.OFFICIAL_MEMORY} "
          f"seed={SEED} threshold={THRESHOLD}", flush=True)
    print(f"[data] root={ch3.DATA_ROOT}", flush=True)

    store = {y: ch3.load_year(y, "train") for y in years}
    input_dim = int(store[years[0]][0].shape[1])
    rng = np.random.default_rng(SEED)
    buf_rng = np.random.default_rng(SEED)

    model, arch = build_model(arm, input_dim)
    model = model.to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[model] arm={arm} k={k} params={n_params:,} arch={arch}", flush=True)

    mem_samples = [mps_mem_snapshot("before_training")]
    current_year_f1: dict[str, float] = {}
    current_year_n: dict[str, int] = {}
    current_year_pos: dict[str, int] = {}
    year_wall: dict[str, float] = {}
    preds: dict[int, dict[str, np.ndarray]] = {}
    train_logs: dict[str, dict[str, Any]] = {}
    t0 = time.time()
    for idx, year in enumerate(years):
        x_curr, y_curr = store[year]
        parts, _meta = build_parts(store, years, idx, x_curr, y_curr, buf_rng)
        n_rows = int(sum(p[0].shape[0] for p in parts))
        pos_rows = int(sum(int((p[1] == 1).sum()) for p in parts))
        print(f"[parts] {year}: rows={n_rows:,} pos={pos_rows:,} "
              f"pos_rate={pos_rows / max(n_rows, 1):.4f}", flush=True)

        t_year = time.time()
        train_logs[str(year)] = train_epochs_tabm(model, parts, ch3.OFFICIAL_EPOCHS,
                                                  DEVICE, rng, arm, year)
        xt, yt = ch3.load_year(year, "test")
        m = ch3.evaluate(model, xt, yt, ch3.OFFICIAL_BATCH, DEVICE)
        current_year_f1[str(year)] = float(m["f1"])
        current_year_n[str(year)] = int(m["n"])
        current_year_pos[str(year)] = int(m["n_pos"])
        del xt, yt
        year_wall[str(year)] = round(time.time() - t_year, 1)
        mem_samples.append(mps_mem_snapshot(f"after_year_{year}"))
        print(f"[{year}] current_f1={m['f1']:.4f} (n={m['n']}, pos={m['n_pos']}, "
              f"{year_wall[str(year)]:.0f}s)", flush=True)

        if idx == len(years) - 1:
            for ty in years:
                xt, yt = ch3.load_year(ty, "test")
                sc = ch3.score_shard(model, xt, ch3.OFFICIAL_BATCH, DEVICE).astype(np.float32)
                preds[ty] = {"y_true": yt.astype(np.int8), "y_score": sc}
                del xt, yt

    del store
    backward_f1 = {str(ty): f1_of(preds[ty]["y_true"], preds[ty]["y_score"]) for ty in years}
    mean_f1 = float(np.mean(list(backward_f1.values())))

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    for ty, d in preds.items():
        np.savez_compressed(RUN_DIR / f"preds_{arm}_{ty}.npz",
                            y_true=d["y_true"], y_score=d["y_score"],
                            threshold=np.float32(THRESHOLD))
    mem_samples.append(mps_mem_snapshot("after_training"))
    wall_seconds = round(time.time() - t0, 1)

    uniform = json.loads(UNIFORM_RESULT.read_text(encoding="utf-8"))
    delta_mean = (mean_f1 - float(uniform["mean_f1"])) * 100
    delta_2023 = (backward_f1["2023"] - float(uniform["f1_2023"])) * 100
    delta_2024 = (backward_f1["2024"] - float(uniform["f1_2024"])) * 100

    before = mem_samples[0]
    after = mem_samples[-1]
    efficiency = {
        "device": DEVICE.type,
        "n_params": n_params,
        "wall_seconds": wall_seconds,
        "year_wall_seconds": year_wall,
        "mps_memory": {
            "available": DEVICE.type == "mps",
            "sampling": "训练前、每年评价后、打分结束后各采样一次；peak 为采样最大值，非硬件峰值",
            "api_note": ("torch 2.12 的 MPS 内存接口为 current_allocated_memory / "
                         "driver_allocated_memory（字节）；*_bytes 别名不存在"),
            "samples": mem_samples,
            "sampled_peak_current_allocated_bytes": _peak(mem_samples, "current_allocated_bytes"),
            "sampled_peak_driver_allocated_bytes": _peak(mem_samples, "driver_allocated_bytes"),
            "before_training_driver_allocated_bytes": before.get("driver_allocated_bytes"),
            "after_training_driver_allocated_bytes": after.get("driver_allocated_bytes"),
            "driver_delta_bytes": (
                None if before.get("driver_allocated_bytes") is None
                or after.get("driver_allocated_bytes") is None
                else int(after["driver_allocated_bytes"]) - int(before["driver_allocated_bytes"])
            ),
        },
    }

    payload: dict[str, Any] = {
        "schema_version": "ch4-general-arm-v1",
        "arm": arm,
        "k": k,
        "architecture": arch,
        "n_params": n_params,
        "transplant_notes": {
            "first_adapter_init": "random_sign_pm1",
            "other_adapters_init": "r=1,s=1,beta=0",
            "train_loss": "mean_of_member_bce",
            "eval": "mean_of_member_sigmoid",
            "protocol_deviation": ("SGD(0.01,0.9,1e-6)/batch1024/10ep，无裁剪无早停；"
                                   "论文用 AdamW+clip+早停；属任务化适配，非复现"),
            "width_variant": ("halfwidth 只改宽度：骨干 256/192/128/64、头 64/64/1；"
                              "k2 保持标准宽度 512/384/256/128、头 100/100/1"),
        },
        "protocol": {
            "domain_years": years,
            "epochs": ch3.OFFICIAL_EPOCHS,
            "batch": ch3.OFFICIAL_BATCH,
            "lr": ch3.OFFICIAL_LR,
            "momentum": ch3.OFFICIAL_MOMENTUM,
            "weight_decay": ch3.OFFICIAL_WEIGHT_DECAY,
            "memory": ch3.OFFICIAL_MEMORY,
            "seed": SEED,
            "threshold": THRESHOLD,
            "data_root": str(ch3.DATA_ROOT),
            "device": DEVICE.type,
        },
        "registration": {
            "criterion": ("k 敏感性只登记 12y mean 随 k∈{2,4,8} 的方向；"
                          "宽度变体只登记与 uniform（tabm4）的 12y 差；"
                          "均不作支持/否决判定"),
            "uniform_reference": {
                "arm": "tabm4",
                "path": str(UNIFORM_RESULT.relative_to(TOOLS_DIR.parent)),
                "mean_f1": float(uniform["mean_f1"]),
                "f1_2023": float(uniform["f1_2023"]),
                "f1_2024": float(uniform["f1_2024"]),
                "n_params": int(uniform["n_params"]),
            },
        },
        "mean_f1": mean_f1,
        "f1_2023": backward_f1["2023"],
        "f1_2024": backward_f1["2024"],
        "backward_f1": backward_f1,
        "current_year_f1": current_year_f1,
        "current_year_n": current_year_n,
        "current_year_pos": current_year_pos,
        "descriptive_deltas_vs_uniform": {
            "delta_mean12_pp": delta_mean,
            "delta_2023_pp": delta_2023,
            "delta_2024_pp": delta_2024,
            "note": "描述性差值，非预登记判据",
        },
        "efficiency": efficiency,
        "wall_seconds": wall_seconds,
        "train_logs": train_logs,
        "ts": datetime.now(UTC).isoformat(),
    }
    (RUN_DIR / f"{arm}-result.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[efficiency] params={n_params:,} wall={wall_seconds:.1f}s "
          f"peak_current={efficiency['mps_memory']['sampled_peak_current_allocated_bytes']} "
          f"peak_driver={efficiency['mps_memory']['sampled_peak_driver_allocated_bytes']}",
          flush=True)
    print(f"=== {arm}: 12y mean={mean_f1:.10f} | 2023={backward_f1['2023']:.6f} "
          f"2024={backward_f1['2024']:.6f} | params={n_params:,} | "
          f"d_vs_uniform(12y/2023/2024)={delta_mean:+.3f}/{delta_2023:+.3f}/"
          f"{delta_2024:+.3f}pp | {wall_seconds:.0f}s ===", flush=True)
    write_comparison()
    return payload


def _arm_entry(k: int, arm: str, result: dict[str, Any], source: str) -> dict[str, Any]:
    return {
        "k": k,
        "arm": arm,
        "mean_f1": float(result["mean_f1"]),
        "f1_2023": float(result["f1_2023"]),
        "f1_2024": float(result["f1_2024"]),
        "n_params": int(result["n_params"]),
        "wall_seconds": result.get("wall_seconds"),
        "source": source,
    }


def write_comparison() -> None:
    new: dict[str, dict[str, Any]] = {}
    for arm in ARMS:
        p = RUN_DIR / f"{arm}-result.json"
        if p.is_file():
            new[arm] = json.loads(p.read_text(encoding="utf-8"))
    if not new:
        return

    curve: list[dict[str, Any]] = []
    if "k2" in new:
        curve.append(_arm_entry(2, "k2", new["k2"], "ch4-lamda-general-pilot/k2-result.json"))
    if UNIFORM_RESULT.is_file():
        u = json.loads(UNIFORM_RESULT.read_text(encoding="utf-8"))
        curve.append(_arm_entry(4, "tabm4", u, "ch4-lamda-tabm-pilot/tabm4-result.json"))
    if TABM8_RESULT.is_file():
        t8 = json.loads(TABM8_RESULT.read_text(encoding="utf-8"))
        curve.append(_arm_entry(8, "tabm8", t8, "ch4-lamda-tabm-pilot/tabm8-result.json"))
    curve.sort(key=lambda e: e["k"])

    direction: dict[str, Any] | None = None
    if [e["k"] for e in curve] == [2, 4, 8]:
        vals = [e["mean_f1"] for e in curve]
        if vals[0] < vals[1] < vals[2]:
            label = "increasing_with_k"
        elif vals[0] > vals[1] > vals[2]:
            label = "decreasing_with_k"
        else:
            label = "non_monotonic"
        direction = {
            "k_order": [2, 4, 8],
            "mean_f1": vals,
            "label": label,
            "criterion": "预登记仅登记方向，不作支持/否决判定",
        }

    width_variant: dict[str, Any] | None = None
    if "halfwidth" in new and UNIFORM_RESULT.is_file():
        hw = new["halfwidth"]
        u = json.loads(UNIFORM_RESULT.read_text(encoding="utf-8"))
        width_variant = {
            "arm": "halfwidth",
            "k": 4,
            "encoder_widths": [256, 192, 128, 64],
            "head_widths": [64, 64, 1],
            "uniform_reference": "tabm4（512/384/256/128，头 100/100/1）",
            "delta_mean12_pp": float(hw["descriptive_deltas_vs_uniform"]["delta_mean12_pp"]),
            "delta_2023_pp": float(hw["descriptive_deltas_vs_uniform"]["delta_2023_pp"]),
            "delta_2024_pp": float(hw["descriptive_deltas_vs_uniform"]["delta_2024_pp"]),
            "n_params": int(hw["n_params"]),
            "uniform_n_params": int(u["n_params"]),
            "param_ratio": float(hw["n_params"]) / float(u["n_params"]),
            "wall_seconds": hw.get("wall_seconds"),
            "uniform_wall_seconds": u.get("wall_seconds"),
            "criterion": "预登记仅登记与 uniform 的 12y 差，不作支持/否决判定",
        }

    efficiency = {}
    for arm, r in new.items():
        eff = r["efficiency"]
        efficiency[arm] = {
            "n_params": eff["n_params"],
            "wall_seconds": eff["wall_seconds"],
            "sampled_peak_current_allocated_bytes":
                eff["mps_memory"]["sampled_peak_current_allocated_bytes"],
            "sampled_peak_driver_allocated_bytes":
                eff["mps_memory"]["sampled_peak_driver_allocated_bytes"],
            "before_training_driver_allocated_bytes":
                eff["mps_memory"]["before_training_driver_allocated_bytes"],
            "after_training_driver_allocated_bytes":
                eff["mps_memory"]["after_training_driver_allocated_bytes"],
        }
    if UNIFORM_RESULT.is_file():
        u = json.loads(UNIFORM_RESULT.read_text(encoding="utf-8"))
        efficiency["tabm4(reference)"] = {
            "n_params": int(u["n_params"]),
            "wall_seconds": u.get("wall_seconds"),
            "sampled_peak_current_allocated_bytes": None,
            "sampled_peak_driver_allocated_bytes": None,
            "note": "既有制品未采显存，仅登记参数与墙钟",
        }

    comp = {
        "schema_version": "ch4-general-pilot-comparison-v1",
        "k_curve": curve,
        "k_curve_direction": direction,
        "width_variant": width_variant,
        "efficiency": efficiency,
        "registration_note": ("k 曲线三点（2/4/8）与宽度对照均为预登记通用性登记项；"
                              "只登记方向与差值，不作支持/否决判定"),
        "ts": datetime.now(UTC).isoformat(),
    }
    (RUN_DIR / "general-comparison.json").write_text(
        json.dumps(comp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[comparison] wrote {RUN_DIR / 'general-comparison.json'}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="第四章整合方法通用性补臂")
    parser.add_argument("--arm", choices=ARMS, required=True)
    args = parser.parse_args()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    run_arm(args.arm)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
