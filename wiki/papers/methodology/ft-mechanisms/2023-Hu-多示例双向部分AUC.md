---
title: "Non-Smooth Weakly-Convex Finite-sum Coupled Compositional Optimization"
authors: [Quanqi Hu, Dixian Zhu, Tianbao Yang]
year: 2023
date: 2026-08-28
journal: "NeurIPS 2023，Advances in Neural Information Processing Systems 36"
source_pdf: "[[raw/papers/methodology/ft-mechanisms/2023-Hu-Multi-Instance-TPAUC-NeurIPS.pdf]]"
sha256: "3854226246c4a9364f4b88096a4e221d74c915086f494cff87c03d08c72bcb3c"
arxiv_id: "2310.03234"
tags: [多示例学习, 双向部分AUC, 随机池化, 低误报, 类型/论文]
key_finding: "论文已把多示例袋级预测与双向部分 AUC 直接结合，并支持均值、平滑最大和注意力池化；“实体袋+pAUC”这一组合已经被明确占用。"
zotero_status: "未操作：本轮 Zotero 本地 API 未运行"
---

# 多示例双向部分 AUC

## 全文证据

- 物理第 8 页公式（8）–（9）定义双向部分 AUC：只比较最低分正样本与最高分负样本。
- 同页明确把 `X_i` 扩展为多实例袋，先以实例编码均值得到袋分数；全文说明也可扩展到平滑最大和注意力池化。
- 物理第 9 页表 2 在 MUSK2、Fox、Colon、Lung 上比较 AUC-M、MIDAM、SOTAs 与 SONT；SONT(att)直接优化多示例 TPAUC。
- 训练固定 100 个周期，袋批量 16/8，每袋抽 4/128 个实例，五折以最佳验证表现选择（物理第 9–10 页）。
- 本轮未找到作者公开的正式实现仓库；不得把 LibAUC 的 MIDAM 实现误写成本文 SONT 的实现。

## 新颖性边界

- 已占用：多示例袋、注意力/均值池化、顶部负袋与底部正袋排序、低误报/低漏报联合区域。
- 未覆盖：网络实体的严格时间前缀、源年/目标年隔离、当前流与历史记忆的同构部署、实体暴露诊断。
- 因此 D2 的“实体低误报排序”新颖性风险高；只有因果前缀生成、实体均匀测度、冻结预算和 FT 联合算法的差量消融产生信号，才可作为本课题机制。
