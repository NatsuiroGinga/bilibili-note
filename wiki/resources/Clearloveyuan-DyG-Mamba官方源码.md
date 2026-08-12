---
title: "Clearloveyuan/DyG-Mamba 官方源码"
date: 2026-08-11
verified_on: 2026-08-11
tags:
  - 外部资源
  - 官方源码
  - 动态图
  - 连续时间状态空间模型
  - 类型/参考
related:
  - "[[2025-Li-DyG-Mamba连续状态空间动态图]]"
---

# Clearloveyuan/DyG-Mamba 官方源码

## 核验结论

- 仓库：https://github.com/Clearloveyuan/DyG-Mamba
- 2026-08-11 只读核验的 `HEAD`：`ce54319e97560593c8ee704c8df65f5c6f95fd8c`。
- README 明确称其为 DyG-Mamba 官方实现，链接 arXiv:2408.06966 与 OpenReview 论文，并给出动态链接预测、节点分类和 12 套动态图数据的入口。
- `models/DyGMamba.py:346` 起的 `get_dt_features` 从相邻时间戳构造归一化跨度并编码；`models/mamba_simple.py:358` 起的 `MambaTimeDelta` 把跨度特征送入选择性扫描。
- 仓库根目录未发现 `LICENSE`／`COPYING`，直接请求根 `LICENSE` 也返回 404，故许可证状态为**未声明**。
- 静态检索未找到 `spectral_norm` 或等价名称；论文式（13）的谱范数约束是否完整落实到当前提交，不能仅凭 README 确认。该差异只作为复现风险，不否定论文公式证据。

## 证据边界

该仓库证明作者公开了真实时间跨度进入 Mamba 扫描的实现与动态图任务入口。它不能证明候选 B 的 RWKV-7 改写、频谱支路或 LSPR 跨年度检测有效，也不能在许可证未声明时直接用于衍生分发。
