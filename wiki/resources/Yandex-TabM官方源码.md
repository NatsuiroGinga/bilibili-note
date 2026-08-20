---
title: "Yandex Research TabM 官方源码"
date: 2026-08-20
tags:
  - TabM
  - 表格数据
  - 官方源码
  - 类型/参考
url: "https://github.com/yandex-research/tabm"
commit: "28e47ae301c92ec37787dde1ce923a0793f405b4"
license: "Apache-2.0"
related:
  - "[[2025-Gorishniy-TabM参数高效集成]]"
---

# Yandex Research TabM 官方源码

## 固定身份

- 官方仓库：<https://github.com/yandex-research/tabm>。
- 核验提交：`28e47ae301c92ec37787dde1ce923a0793f405b4`，2026-08-20 通过 `git ls-remote` 核验为主分支提交。
- 固定提交入口：<https://github.com/yandex-research/tabm/tree/28e47ae301c92ec37787dde1ce923a0793f405b4>。
- 许可证：Apache-2.0。
- 临时源码快照 SHA-256：`7305f74cf101735e4342822c49d6496247729cbb8f2701ed9ef36b97c06bf92b`；快照只用于本轮逐行核验，未写入仓库。
- 包版本：固定提交的 `tabm.py` 声明 `0.0.3`。

## 实测事实

- `tabm.py` 第 1677 至 1710 行：`TabM.make` 在无数值嵌入时默认 `n_blocks=3`、`d_block=512`、`dropout=0.1`、ReLU、`k=32`、`arch_type=tabm` 和随机符号首适配初始化；使用数值嵌入时默认层数为 2，首适配初始化为正态分布。
- `README.md` 第 225 至 235 行：训练必须分别计算 `k` 个预测的损失后取均值，不能先平均预测再计算损失；分类推理通常平均概率而不是对数几率。
- `README.md` 第 608 至 628 行：默认模型参数依赖输入；官方当前默认优化器为 `AdamW(lr=0.002, weight_decay=0.0003)`。
- `README.md` 第 649 至 657 行：`k` 不应与其他超参数随意混调；`k=16` 或 `24` 可作探索，增加 `k` 时通常需要同时增加宽度或深度。
- `README.md` 第 714 至 720 行：无数值嵌入的公开调参空间为 `k=32`、层数 `1..5`、宽度 `64..1024`、学习率 `[1e-4,5e-3]`、权重衰减 `0` 或 `[1e-4,1e-1]`。
- `paper/exp/tabm/churn/0-tuning.toml`：论文复现入口使用 `patience=16`、无固定轮数上限、梯度裁剪 `1.0`、`k=32` 和不同成员训练批次。

## 与本课题的关系

- 可直接复用成员参数化、初始化顺序、成员损失均值和分类概率平均的语义。
- 当前 TabM4 的 `k=4`、宽度 186、总样本曝光 64 和共享 ELP 属任务适配，不是官方默认。
- 证据线 B 若采用官方默认宽度与成员数，必须单独记录有效批量、梯度累积、峰值显存和训练时间；这些工程量不能由源码默认推断。
