---
title: "LSPR24 Zenodo 官方数据发布页"
date: 2026-08-08
verified_on: 2026-08-08
tags:
  - LSPR24
  - 网络入侵检测
  - 数据集
  - Zenodo
  - 类型/参考
related:
  - "[[papers/datasets/LSPR24-Locked-Shields实兵演习数据集|LSPR24 数据集论文]]"
  - "[[papers/datasets/LSPR24/Leoste-2025-LSPR23到LSPR24跨年泛化|LSPR24 跨年基线]]"
---

# LSPR24 Zenodo 官方数据发布页

## 来源

- 正式名称：Locked Shields Partners Run 24 (LSPR24): A Next-Generation Cybersecurity Dataset for Blue Team Automation
- 稳定链接：<https://doi.org/10.5281/zenodo.14900873>
- 发布者：Allard Dijk、Roland Meier、Cosimo Melella、Mauno Pihelgas
- 创建日期：2025-04-10
- 许可：CC0

## 文件与校验信息

| 文件 | 页面标称大小 | 官方 MD5 | 用途 |
| --- | ---: | --- | --- |
| `lspr24_v2.parquet` | 2.8 GB | `a407011e9edbe615ce58a1e625c0a340` | 约 2022 万条网络流及标签 |
| `attack_narratives.json` | 11.3 MB | `4d9be4a2aea86b425dadcb446440752b` | 攻击叙事与提交记录 |
| `eve.log` | 145.4 MB | `7706badbf6f5759be544d7bcaabcd235` | Suricata 事件日志 |
| `ossec-archive-host-logs.json` | 5.0 GB | `46c4dd79e90ee26d40736996b52abd91` | 主机日志 |

## 已核验事实

- 页面将 LSPR24 定位为 LSPR23 的后继版本，记录超过 400 GB 捕获流量、约 2000 万条流、20 亿个包、287 GB 传输量和 31.6 小时活动。
- 页面明确鼓励跨 LSPR23／LSPR24 的比较与迁移学习。
- 页面把 LSPR25 记录列为后继数据集；LSPR25 用于三年度同年与跨年序列构造评价。

## 使用边界

- Zenodo 页面给出文件、许可和摘要性规模，不给出模型实验协议；模型指标必须回到具体使用论文。
- `attack_narratives.json` 的提交时间不能自动视为攻击开始时间。
- 本课题当前最终测试封存规则不因公开数据页可访问而改变。
