---
title: "Scarlett125/PROTOCOL 官方源码"
date: 2026-08-12
verified_on: 2026-08-12
tags: [外部资源, 官方源码, 部分最优传输, 类别不平衡, 类型/参考]
related: ["[[2025-Xue-PROTOCOL不平衡部分传输]]"]
---

# Scarlett125/PROTOCOL 官方源码

## 核验事实

- 仓库：https://github.com/Scarlett125/PROTOCOL
- 只读核验 `HEAD`：`e17f095b38c81251caccdc4456696060b126882a`。
- PMLR 正式页直接链接该软件，README 与 ICML 2025 论文一致。
- 根目录未显示许可证，许可证状态记为**未声明**。
- 复现说明要求手工修改环境中的 PyTorch `TransformerEncoderLayer` 和多头注意力实现，环境侵入性高，不宜直接纳入本课题生产环境。

## 本课题边界

该源码收紧“渐进部分质量 + 少数类再平衡”的原创边界。第一候选只复用数学先例，不直接移植多视图网络。
