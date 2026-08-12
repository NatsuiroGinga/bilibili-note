---
title: "Torea-L/JCCMTM 官方源码"
date: 2026-08-11
verified_on: 2026-08-11
tags:
  - 外部资源
  - 官方源码
  - 多变量时间序列
  - 掩码预训练
  - 类型/参考
---

# Torea-L/JCCMTM 官方源码

## 核验结论

- 仓库：https://github.com/Torea-L/JCCMTM
- 2026-08-11 只读核验的 `HEAD`：`ccf61cdbbacb417130f4d43353893889ff240656`。
- README 明确称其为 Neural Networks 2025 论文 JCCMTM 的官方实现，并链接 DOI `10.1016/j.neunet.2025.107922`。
- README 和 `run_pretrain.py` 公开 `CI`、`CD`、`CICD` 三种策略；`models/JCC_backbone.py` 分别实现逐通道 `Uni` 模块、跨通道 `Multi` 模块及 `Uni-to-Mul` 变换，支持掩码时间序列预训练。
- 仓库还公开长期预测与异常检测下游入口，但不包含论文 PDF 或作者稿；因此源码不能升级成论文全文证据。
- 根目录 `LICENSE` 为 Apache-2.0。

## 与候选 A 的边界

官方源码足以确认“掩码时间序列预训练中联合通道独立与通道依赖建模”已有公开实现，候选 A 不能把该抽象组合写成原创。由于期刊全文未取得，TSaS、Uni-Mul 变换、消融数值和复杂度论证只能按期刊摘要／落地页与源码证据引用，不能伪造页码或公式级结论。

## 证据边界

该资源证明公开实现范围和许可证，不替代论文方法、实验或限制。候选 A 的源语义组约束、状态条件可信边和 LSPR23→LSPR24 冻结协议是否有效仍需真实消融。
