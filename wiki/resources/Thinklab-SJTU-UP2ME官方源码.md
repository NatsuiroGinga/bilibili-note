---
title: "Thinklab-SJTU/UP2ME 官方源码"
date: 2026-08-11
verified_on: 2026-08-11
tags:
  - 外部资源
  - 官方源码
  - 多变量时间序列
  - 掩码预训练
  - 类型/参考
related:
  - "[[2024-Zhang-UP2ME逐变量预训练与多变量图微调]]"
---

# Thinklab-SJTU/UP2ME 官方源码

## 核验结论

- 仓库：https://github.com/Thinklab-SJTU/UP2ME
- 2026-08-11 只读核验的 `HEAD`：`6fd70378870a0bab8627c39def660e483c4dc1d9`。
- 根目录 `LICENSE` 为 Apache-2.0；README 明确称其为 ICML 2024 UP2ME 的原始 PyTorch 实现，并链接论文。
- `models/finetune_model/UP2ME_detector.py:45-47` 冻结整个预训练模型；`:97-98` 用预训练编码结果构图；`:112-136` 逐补丁掩码，经时间—通道层和冻结解码器完成重建。
- `models/finetune_model/graph_structure.py:35-55` 对各通道编码做最大池化与余弦相似度，再求逐通道近邻图和全局前 `kC` 边的交集；这与论文式（9）一致。
- README 与脚本覆盖预测、插补和异常检测，并提供逐数据集预训练模型；它证明作者实现了候选 A 的直接近邻链条，但不证明跨数据集或跨年度冻结泛化。

## 证据边界

该仓库可作为 UP2ME 方法链与复现入口的一级代码证据。它不含 LSPR 网络字段语义、RWKV 状态可信边或 LSPR23→LSPR24 合同，也不能用其公开结果推断候选 A 有效。
