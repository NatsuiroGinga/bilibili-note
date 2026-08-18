# -*- coding: utf-8 -*-
"""只读：打印 ch3-hparam-fairsel-v2（top-5 预测平均协议）的 2x2 四格 LSPR24 指标。

用于跨基座对照表的骨干 A（MLP）参照列。不训练、不评价、不写盘。
"""

import json

V2 = ("/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/"
      "ch3-hparam-fairsel-v2/ch3_hparam_fairsel_v2_results.json")

r = json.load(open(V2))
sel = r["selection"]
print("checkpoint_rule =", sel["checkpoint_rule"])
print("selection_field =", sel["selection_field"], " topk =", sel["topk"], " seed =", sel["seed"])
print("isolation:", r["isolation"]["lspr24_disk_loads"], "loads /",
      r["isolation"]["lspr24_evals"], "evals")
print("lspr24:", r["lspr24"])
print("-" * 100)
g2 = r["group2_cells_2x2"]
for c in ["C00", "C01", "C10", "C11"]:
    m = g2[c]
    print("{} agg={} lp={} npar={} top5={} val_ap_pred_avg={:.6f}".format(
        c, m["agg"], m["lp"], m["npar"], m["topk_epochs"], m["val_ap_pred_avg"]))
    print("    fap={:.6f} e_max={:.6f} e_lp={:.6f} dr_main={:.6f} dr_max={:.6f} "
          "p={:.6f} train_s={:.1f}".format(
              m["fap"], m["e_max"], m["e_lp"], m["dr_main"], m["dr_max"],
              m["p"], m["train_seconds"]))
print("-" * 100)
d = g2["C11"]["e_lp"] - g2["C00"]["e_lp"]
print("MLP 骨干 C11-C00 实体AP(主口径) 增益 = {:.6f} - {:.6f} = {:+.6f}（{:+.2f} 个百分点）".format(
    g2["C11"]["e_lp"], g2["C00"]["e_lp"], d, d * 100))
print("winner(第一组) =", r["group1_final"]["config"])
