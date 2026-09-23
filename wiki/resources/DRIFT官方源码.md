---
title: "snsec-net/2026-DSN-DRIFT：DRIFT 官方源码"
date: 2026-09-23
resource_type: 代码仓库
url: "https://github.com/snsec-net/2026-DSN-DRIFT"
verified_on: 2026-09-23
tags:
  - 外部资源
  - 代码仓库
  - DRIFT
  - DGA检测
  - 类型/参考
related:
  - "[[2026-Lee-DRIFT-DGA-Temporal-Drift]]"
key_finding: "固定提交 e20d1fdf 的加载器对整行调用无 subset 的 Polars unique；它不按 domain 或 exact eSLD 做身份去重。"
---

# snsec-net/2026-DSN-DRIFT

## 本地原件

- 官方地址：<https://github.com/snsec-net/2026-DSN-DRIFT>
- 本地路径：`raw/resources/2026-DSN-DRIFT`
- 已检出提交：`e20d1fdf56c623993966c6786f61c01f91dec6d2`
- 核验日期：2026-09-23
- 本地克隆仅含源码，约1.3MiB；未下载数据集、模型权重或运行制品。

## 已核源码事实

`utility/dataset.py` 的 `get_train_set()` 合并12个源角色文件后调用 `pl.read_parquet(files).unique()`；源验证和每个目标年份入口也同样调用无 `subset` 的 `unique()`。

因此该调用按整行而不是按 `domain`／exact eSLD 判重；相同域名但标签不同的记录不会因这一步被删除。该事实只能说明官方加载器行为，不能推断论文作者是否知晓或解释了跨角色异标签实体。

官方微调入口在完整源表读入后创建 `FineTuningDataset` 和 `DataLoader(..., shuffle=True, num_workers=4)`。它不能直接作为本机全源训练实现；第三章若复用官方角色，仍须遵守本项目的按需 Parquet 直读与成员合同。

## 关联

- 数据论文与数据集语义见 [[2026-Lee-DRIFT-DGA-Temporal-Drift]]。
- 当前论文数据角色与边界见 [[第三章-DRIFT数据角色与评价协议]]。
