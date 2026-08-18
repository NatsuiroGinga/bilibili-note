---
title: "LHXXHB/EnsV 官方源码"
date: 2026-08-12
verified_on: 2026-08-12
tags: [外部资源, 官方源码, 无标签选模, 域适应, 类型/参考]
related: ["[[2024-Hu-EnsV无标签域适应选模]]"]
---

# LHXXHB/EnsV 官方源码

## 核验事实

- 仓库：https://github.com/LHXXHB/EnsV
- 只读核验 `HEAD`：`b0bb1d1181d6796516335fa4d88391e81eb49a95`。
- README 对应 NeurIPS 2024 EnsV，公开 `ensv.py`、候选检查点和 Office-Home 演示。
- 许可证：MIT。
- 原环境为 Python 3.7.13、CUDA 10.1、PyTorch 1.7.1；RTX 5090 需要现代栈重建，但核心预测矩阵计算可轻量重写。

## 本课题边界

EnsV 只作负迁移门禁的一项信号。多数类共识风险使其不能单独决定回滚。

