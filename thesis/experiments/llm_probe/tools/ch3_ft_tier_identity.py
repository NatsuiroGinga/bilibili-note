#!/usr/bin/env python3
"""起跑前的档位身份并排核对：防止把本机档、缩容档、满血档跑混。

背景（2026-09-03 用户要求）：同一套四格代码支持三个骨干档位与两种设备，
配置文件名相近、身份哈希只在细节上不同，人眼比对极易看错，
而跑错档要到几小时后看结果才发现。故把「起跑前该核对的每一项」
固化成一条命令，一次并排打出全部待跑配置。

用法（从 llm_probe 目录）：

    python tools/ch3_ft_tier_identity.py configs/a.json configs/b.json ...
    python tools/ch3_ft_tier_identity.py --all-sixth        # 全部本机档配置

不修改任何文件、不加载 PyTorch、不接触数据，纯读配置。
输出末尾给出一致性判断：四格应当**只在机制开关上不同**，
档位／设备／精度／轮数／验证批若不一致即打印警告（提示，不退出非零）。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import ch3_ft_c00_dual_selection as dual  # noqa: E402
import ch3_ft_transformer_field_token_protocol_a as base  # noqa: E402

# 三档的展示名与骨干规格。参数量一律现算，不写死数字——
# 2026-09-03 曾把测速复刻件的 23,041 当成宿主闭式结果写进文档。
TIER_DISPLAY = {
    dual.WIDTH_PROFILE_FULL: ("满血档", base.D_TOKEN, base.N_LAYERS),
    dual.WIDTH_PROFILE_HALF: ("缩容档 half（历史）", dual.HALF_WIDTH_D_TOKEN, base.N_LAYERS),
    dual.WIDTH_PROFILE_SCREENING_WIDTH56: (
        "筛选档 width56（当前主用）",
        dual.SCREENING_WIDTH56_D_TOKEN,
        base.N_LAYERS,
    ),
}


def describe(path: Path) -> dict[str, object]:
    cfg = json.loads(path.read_text())
    model = cfg.get("model", {})
    profile = model.get("width_profile", dual.WIDTH_PROFILE_FULL)
    display, d_token, n_layers = TIER_DISPLAY.get(profile, ("未登记档位", None, None))
    mech = cfg.get("mechanism", {})

    def on(key: str) -> str:
        block = mech.get(key)
        return "开" if isinstance(block, dict) and block.get("enabled") else "关"

    runtime = cfg.get("runtime", {})
    training = cfg.get("training", {})
    budget = cfg.get("budget", {})
    identity = cfg.get("identity", {})
    return {
        "文件": path.name,
        "运行身份": identity.get("run_id", "—"),
        "级别": identity.get("run_tier", "—"),
        "档位": display,
        "d_token": d_token,
        "层数": n_layers,
        "裸FT参数量": dual.bare_ft_expected_parameter_count(profile),
        "登记参数量": model.get("expected_parameter_count"),
        "设备": runtime.get("device_type", "—"),
        "精度": runtime.get("precision_profile_id", "—"),
        "轮数": budget.get("epochs"),
        "每轮步数": budget.get("steps_per_epoch"),
        "微批序列": training.get("micro_batch_sequences"),
        "验证批序列": training.get("validation_batch_sequences"),
        "抽样": "有" if cfg.get("data", {}).get("entity_subsample") else "无",
        "实体级BCE": on("entity_bce"),
        "尾部聚合ETA": on("entity_tail_aggregation"),
        "实体排序BER": on("entity_ranking"),
        "因果记忆CEM": on("entity_memory"),
    }


# 四格之间**允许**不同的只有这三项；其余不一致即为疑似跑错档。
MECHANISM_KEYS = ("实体级BCE", "尾部聚合ETA", "实体排序BER", "因果记忆CEM")
MUST_MATCH = (
    "档位", "d_token", "层数", "裸FT参数量", "设备", "精度",
    "轮数", "每轮步数", "微批序列", "验证批序列", "抽样",
)


def main() -> int:
    ap = argparse.ArgumentParser(description="并排核对四格配置的档位身份")
    ap.add_argument("configs", nargs="+", type=Path)
    args = ap.parse_args()

    paths = list(args.configs)

    rows = [describe(p) for p in paths]
    keys = list(rows[0])
    width = max(len(k) for k in keys) + 2
    col = max(28, max(len(str(r[k])) for r in rows for k in keys) + 2)

    print("=" * (width + col * len(rows)))
    for k in keys:
        line = f"{k:<{width}}" + "".join(f"{str(r[k]):<{col}}" for r in rows)
        print(line)
    print("=" * (width + col * len(rows)))

    problems: list[str] = []
    for k in MUST_MATCH:
        values = {str(r[k]) for r in rows}
        if len(values) > 1:
            problems.append(f"  ⚠️ 「{k}」在各配置间不一致：{sorted(values)}")
    for r in rows:
        if r["登记参数量"] != r["裸FT参数量"] and r["因果记忆CEM"] == "关":
            problems.append(
                f"  ⚠️ {r['文件']} 的 model.expected_parameter_count="
                f"{r['登记参数量']} 与该档闭式 {r['裸FT参数量']} 不符"
            )

    mech_sets = {tuple(r[k] for k in MECHANISM_KEYS) for r in rows}
    if len(mech_sets) != len(rows):
        problems.append("  ⚠️ 存在机制开关完全相同的配置——四格应两两不同")

    if problems:
        print("疑似问题（提示，不阻断；起跑前请逐条确认）：")
        for p in problems:
            print(p)
    else:
        print("一致性检查通过：各配置仅在机制开关上不同，骨干／设备／预算全部一致。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
