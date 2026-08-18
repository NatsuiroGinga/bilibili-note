# -*- coding: utf-8 -*-
"""从 E5 result.json 提取汇报所需的完整数字表。只读。"""
import json

R = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/lspr24-decision-rule-headroom-v1"
with open(f"{R}/result.json") as f:
    res = json.load(f)

print("=== 第1组：漏检事件分数形态 ===")
g1 = res["group1_missed_event_score_shape"]
for b in ("0.01", "0.1", "1.0", "10.0"):
    row = g1[b]
    print(f"\n-- 预算 {b} thr={row['threshold']:.6g} 漏检={row['n_missed_events']}")
    for tag in ("单窗事件", "多窗事件"):
        t = row[tag]
        m = t["成员窗分数分布"]
        mx = t["每事件max分数分布"]
        gp = t["距阈值差(thr-max)分布"]
        print(f"   {tag} n={t['n_events']} 成员窗n={m['n']}")
        print(f"     成员窗分数 p25={m['p25']:.4g} p50={m['p50']:.4g} p75={m['p75']:.4g} "
              f"p90={m['p90']:.4g} max={m['max']:.4g}")
        print(f"     事件max   p25={mx['p25']:.4g} p50={mx['p50']:.4g} p75={mx['p75']:.4g} "
              f"p90={mx['p90']:.4g} max={mx['max']:.4g}")
        print(f"     距阈值差  p25={gp['p25']:.4g} p50={gp['p50']:.4g} p75={gp['p75']:.4g} "
              f"p90={gp['p90']:.4g}  max>=0.5:{t['max>=0.5的事件数']} max>=0.1:{t['max>=0.1的事件数']}")
print("\n-- 单窗事件历史代理量")
print(json.dumps(g1["single_window_history_availability"], ensure_ascii=False, indent=1))

print("\n=== 第2组 oracle：全部 25 个规则在 0.01 档 ===")
ot = res["group2_evidence_accumulation"]["oracle_upper_bound"]
rows = sorted(((v["0.01"]["event_recall"], k) for k, v in ot.items()), reverse=True)
for rec, k in rows:
    v = ot[k]
    print(f"  {rec:.6f}  {k:42s} 0.1={v['0.1']['event_recall']:.4f} "
          f"1.0={v['1.0']['event_recall']:.4f} 10.0={v['10.0']['event_recall']:.4f}")

print("\n=== 第2组 oracle 摘要 / 诚实 ===")
for b in ("0.01", "0.1", "1.0", "10.0"):
    o = res["group2_evidence_accumulation"]["oracle_summary"][b]
    h = res["group2_evidence_accumulation"]["honest"][b]
    bo, bh = o["paired_endpoint_bootstrap"], h["paired_endpoint_bootstrap"]
    print(f"[{b}] oracle 最优={o['best_rule']} 召回={o['best_event_recall']:.6f} "
          f"Δ={o['oracle_gain_event_recall']:+.6f} 配对CI={[round(x,4) for x in bo['paired_ci95_delta']]}")
    print(f"      诚实 选中={h['selected_on_half_a']} 后半基线={h['half_b_baseline_max_rule']['event_recall']:.6f} "
          f"候选={h['half_b_selected_rule']['event_recall']:.6f} Δ={h['honest_gain_event_recall']:+.6f} "
          f"配对CI={[round(x,4) for x in bh['paired_ci95_delta']]} "
          f"边际半宽(基线)={bh['marginal_halfwidth_baseline']:.4f} "
          f"配对半宽={bh['paired_halfwidth_delta']:.4f} 比值={bh['marginal_over_paired_halfwidth_ratio']:.2f}")
print("误报口径诊断:", json.dumps(res["group2_evidence_accumulation"]["fp_accounting_diagnostic@0.01"],
                                 ensure_ascii=False))

print("\n=== 第3组 ===")
g3 = res["group3_endpoint_budget_allocation"]
print(f"端点数={g3['n_endpoints']} 无负窗端点={g3['n_endpoints_without_negative_window']} "
      f"零成本可达事件={g3['events_reachable_at_zero_fp_cost']} Gini={g3['marginal_slope_gini']:.4f}")
print("边际斜率分布:", json.dumps(g3["marginal_slope_distribution"], ensure_ascii=False))
zc = g3["ablation_zero_cost_per_endpoint_calibration"]
print(f"零成本逐端点标定(全验证集): fp={zc['result']['fp']} 召回={zc['result']['event_recall']:.6f} "
      f"Δ={zc['vs_baseline@0.01']['point_delta']:+.6f} "
      f"配对CI={[round(x,4) for x in zc['vs_baseline@0.01']['paired_ci95_delta']]}")
for b in ("0.01", "0.1", "1.0", "10.0"):
    o = g3["oracle_upper_bound"][b]
    h = g3["honest"][b]
    bo, bh = o["paired_endpoint_bootstrap"], h["paired_endpoint_bootstrap"]
    print(f"[{b}] oracle 分配={o['greedy_event_recall']:.6f} 均匀={o['baseline_uniform_event_recall']:.6f} "
          f"Δ={o['oracle_gain_event_recall']:+.6f} 配对CI={[round(x,4) for x in bo['paired_ci95_delta']]} "
          f"LP上界={o['lp_upper_bound_event_recall']:.6f} fp分布Gini={o['fp_distribution_gini']:.4f}")
    print(f"      诚实 后半均匀={h['half_b_baseline_uniform']['event_recall']:.6f}(fp="
          f"{h['half_b_baseline_uniform']['fp']}) 份额迁移={h['half_b_transferred_share_allocation']['event_recall']:.6f}"
          f"(fp={h['half_b_transferred_share_allocation']['fp']}) Δ={h['honest_gain_event_recall']:+.6f} "
          f"配对CI={[round(x,4) for x in bh['paired_ci95_delta']]}")
    z = h["ablation_zero_quota_pure_per_endpoint_calibration"]
    bz = h["ablation_zero_quota_vs_baseline_bootstrap"]
    print(f"      消融 零配额={z['event_recall']:.6f}(fp={z['fp']}) 配对CI="
          f"{[round(x,4) for x in bz['paired_ci95_delta']]} | 均匀配额="
          f"{h['ablation_equal_share_quota']['event_recall']:.6f}(fp={h['ablation_equal_share_quota']['fp']})")
    print(f"      严格冻结 候选={h['half_b_strict_thresholds_from_half_a']['event_recall']:.6f}"
          f"(fp={h['half_b_strict_thresholds_from_half_a']['fp']}) 全局冻结="
          f"{h['half_b_strict_global_threshold_from_half_a']['event_recall']:.6f}"
          f"(fp={h['half_b_strict_global_threshold_from_half_a']['fp']}) 同误报全局="
          f"{h['half_b_baseline_at_matched_fp']['event_recall']:.6f}"
          f"(fp={h['half_b_baseline_at_matched_fp']['fp']})")
tr = g3["transferability_of_per_endpoint_calibration"]
print("\n逐端点标定时间可迁移性:", json.dumps(tr, ensure_ascii=False, indent=1)[:1200])

print("\n=== 第4组 ===")
g4 = res["group4_orthogonality"]
print("组合规则:", g4["combined_rule"])
for b in ("0.01", "0.1", "1.0", "10.0"):
    o = g4["oracle_upper_bound"][b]
    h = g4["honest"][b]
    print(f"[{b}] oracle 组合={o['combined_event_recall']:.6f} Δ={o['combined_gain']:+.6f} "
          f"M1单独={o['m1_gain_alone']:+.6f} M2单独={o['m2_gain_alone']:+.6f} "
          f"可加预测={o['additive_prediction']:+.6f} 正交比={o['orthogonality_ratio']}")
    print(f"      诚实 组合={h['half_b_combined']['event_recall']:.6f} Δ={h['honest_gain_event_recall']:+.6f} "
          f"配对CI={[round(x,4) for x in h['paired_endpoint_bootstrap']['paired_ci95_delta']]}")

print("\n=== 切分元数据 ===")
print(json.dumps(res["split_meta"], ensure_ascii=False))
print("\n=== 裁决 ===")
print(json.dumps(res["verdict"], ensure_ascii=False, indent=1))
print("\n收据:", res["screening_only"], res["formal_paper_evidence"], res["final_accessed"],
      res["split_names_seen"], f"{res['total_wall_seconds']:.1f}s")
