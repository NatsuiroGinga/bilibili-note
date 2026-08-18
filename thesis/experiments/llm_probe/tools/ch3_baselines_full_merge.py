# -*- coding: utf-8 -*-
"""第三章基线重跑的合并与主比较表生成。

读取 tools/ch3_baselines_full_trees.py 与 tools/ch3_baselines_full_neural.py 的结果，
核对两个进程的 LSPR24 评价次数合计恰为 5（每个基线一次），再与本章方法并排输出主表。

本章方法的数字**从磁盘读取**，不硬编码：
  runs/diagnostics/ch3-hparam-fairsel-v2/ch3_hparam_fairsel_v2_results.json
    group1_final       超参搜索最终配置（与基线同为 top-5 预测平均协议，协议对齐的比较对象）
    group2_cells_2x2.C11  2x2 四格的 C11（同协议）
  runs/diagnostics/ch3-2x2-fairsel/ch3_2x2_fairsel_results.json
    cells.C11          旧的单 epoch argmax 协议数字，只作历史参照，协议与基线不一致

主表一律用 max 聚合（基线没有可学习的 Lp 指数）。Lp 列借用本章 p，只作敏感性参照。
"""

import json
import os

BASE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics"
OUT = f"{BASE}/ch3-baselines-full"
V2 = f"{BASE}/ch3-hparam-fairsel-v2/ch3_hparam_fairsel_v2_results.json"
ARGMAX = f"{BASE}/ch3-2x2-fairsel/ch3_2x2_fairsel_results.json"

trees = json.load(open(f"{OUT}/trees_results.json"))
neural = json.load(open(f"{OUT}/neural_results.json"))

n_eval = trees["isolation"]["lspr24_evals"] + neural["isolation"]["lspr24_evals"]
assert n_eval == 5, f"两个进程的 LSPR24 评价次数合计应为 5，实为 {n_eval}"
assert trees["isolation"]["lspr24_disk_loads"] == 1
assert neural["isolation"]["lspr24_disk_loads"] == 1
print(f"隔离核对通过：LSPR24 合法评价次数 {n_eval} = 树模型 "
      f"{trees['isolation']['lspr24_evals']} + 神经模型 {neural['isolation']['lspr24_evals']}")
for e in trees["isolation"]["ledger"] + neural["isolation"]["ledger"]:
    print(f"  [{e['group']}] {e['model']}")

for k in ("n_entity", "n_pos_entity"):
    assert trees["lspr24"][k] == neural["lspr24"][k], f"两个进程的 LSPR24 {k} 不一致"
print(f"评价单元一致：实体 {trees['lspr24']['n_entity']:,} / "
      f"正例实体 {trees['lspr24']['n_pos_entity']} / "
      f"逐流正例率 {trees['lspr24']['flow_pos_rate']:.10f}")

ORDER = ["random_forest_dijk2024", "xgboost_dijk2026", "gru_dijk2026",
         "transformer_dijk2026", "cnn_leoste2025"]
ALL = {**trees["models"], **neural["models"]}
assert set(ORDER) == set(ALL), f"基线集合不符：{sorted(ALL)}"

# ---- 本章方法：优先用协议对齐（top-5 预测平均）的 v2 数字 ----
CH = {}
if os.path.exists(V2):
    v2 = json.load(open(V2))
    g1 = v2["group1_final"]
    CH["本章 CPA-ELP（超参搜索最终配置，top-5 预测平均）"] = {
        "flow_ap": g1["fap"], "ent_ap_max": g1["e_max"], "dr_at_fpr_max": g1["dr_max"],
        "ent_ap_lp": g1["e_lp"], "dr_at_fpr_lp": g1["dr_main"], "npar": g1["npar"],
        "note": f"配置 {g1['config']}，学到的 p={g1['p']:.6f}"}
    c11 = v2["group2_cells_2x2"]["C11"]
    CH["本章 CPA-ELP（2x2 的 C11，top-5 预测平均）"] = {
        "flow_ap": c11["fap"], "ent_ap_max": c11["e_max"], "dr_at_fpr_max": c11["dr_max"],
        "ent_ap_lp": c11["e_lp"], "dr_at_fpr_lp": c11["dr_main"], "npar": c11.get("npar"),
        "note": f"L=128/AUX_W=1.0/HID=192，学到的 p={c11['p']:.6f}"}
if os.path.exists(ARGMAX):
    a = json.load(open(ARGMAX))["cells"]["C11"]
    CH["本章 CPA-ELP（2x2 的 C11，旧单 epoch argmax 协议）"] = {
        "flow_ap": a["fap"], "ent_ap_max": a["e_max"], "dr_at_fpr_max": a["dr_max"],
        "ent_ap_lp": a["e_lp"], "dr_at_fpr_lp": a["dr_main"], "npar": a.get("npar"),
        "note": "协议与本轮基线不一致（单 epoch argmax，非 top-5 预测平均），只作历史参照"}

W = 132
print("\n" + "=" * W)
print("第三章主比较表：五个已发表基线 vs 本章方法（LSPR23 全量训练 → LSPR24 全量评价，83 字段，种子 42）")
print("主口径 = max 聚合；Lp 列借用本章 p="
      f"{trees['p_borrowed_for_lp_sensitivity']:.10f}，只作敏感性参照，不进主表")
print("-" * W)
print(f"{'基线':<38}{'架构族':<8}{'逐流AP':>10}{'实体AP(max)':>13}{'DR@4%FPR(max)':>15}"
      f"{'实体AP(Lp)':>12}{'训练用时':>10}{'规模':>22}")
print("-" * W)
for k in ORDER:
    r = ALL[k]
    print(f"{r['display_name']:<38}{r['family']:<8}{r['flow_ap']:>10.4f}"
          f"{r['ent_ap_max']:>13.4f}{r['dr_at_fpr_max']:>15.4f}"
          f"{r['ent_ap_lp_borrowed']:>12.4f}{r['train_seconds']/60:>9.1f}分"
          f"{r['scale']:>22}")
print("-" * W)
for name, r in CH.items():
    print(f"{name:<38}{'—':<8}{r['flow_ap']:>10.4f}{r['ent_ap_max']:>13.4f}"
          f"{r['dr_at_fpr_max']:>15.4f}{r['ent_ap_lp']:>12.4f}{'—':>10}"
          f"{(str(r['npar']) + ' 参数') if r.get('npar') else '—':>22}")
print("=" * W)

# ---- 与本章方法的差（主口径 max），以协议对齐的 v2 最终配置为基准 ----
ref_key = "本章 CPA-ELP（超参搜索最终配置，top-5 预测平均）"
DELTA = {}
if ref_key in CH:
    ref = CH[ref_key]
    print(f"\n各基线 − 本章方法（{ref_key}），主口径 max，正数表示基线更好")
    for k in ORDER:
        r = ALL[k]
        d = {"flow_ap": r["flow_ap"] - ref["flow_ap"],
             "ent_ap_max": r["ent_ap_max"] - ref["ent_ap_max"],
             "dr_at_fpr_max": r["dr_at_fpr_max"] - ref["dr_at_fpr_max"]}
        DELTA[k] = d
        print(f"  {r['display_name']:<38} 逐流AP {d['flow_ap']:+.4f} | "
              f"实体AP(max) {d['ent_ap_max']:+.4f} | DR@4%FPR(max) {d['dr_at_fpr_max']:+.4f}")
    best = max(ORDER, key=lambda k: ALL[k]["ent_ap_max"])
    print(f"\n★ 实体 AP(max) 最强基线：{ALL[best]['display_name']} = "
          f"{ALL[best]['ent_ap_max']:.4f}，本章方法 = {ref['ent_ap_max']:.4f}，"
          f"差 {ALL[best]['ent_ap_max'] - ref['ent_ap_max']:+.4f}")

print("\nXGBoost 锚点复现（对照 runs/diagnostics/ch3-xgb-entity/xgb_entity.json）")
for k, v in trees["xgb_anchor_delta"].items():
    print(f"  {k:<22} Δ = {v:+.10f}")

json.dump({"main_table": {k: ALL[k] for k in ORDER},
           "chapter_method_reference": CH,
           "delta_vs_chapter_method": DELTA,
           "reference_used_for_delta": ref_key,
           "xgb_anchor": trees["xgb_anchor"], "xgb_anchor_delta": trees["xgb_anchor_delta"],
           "protocol": {"train": "LSPR23 全量 16,353,511 条流",
                        "test": "LSPR24 全量 20,227,356 条流",
                        "field_budget": trees["field_budget"], "seed": trees["seed"],
                        "entity_key": "2-IP 无向对，47,115 实体 / 752 恶意实体",
                        "aggregation": "主表 max；Lp 列借用本章 p，仅敏感性参照",
                        "neural_budget": neural["budget"],
                        "lr_selection": neural["lr_selection"]},
           "isolation": {"total_lspr24_evals": n_eval,
                         "trees": trees["isolation"], "neural": neural["isolation"]}},
          open(f"{OUT}/main_comparison.json", "w"), ensure_ascii=False, indent=2, default=str)
print(f"\n主比较表已存 {OUT}/main_comparison.json")
