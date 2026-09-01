# 尾部聚合参数取值裁决 task_plan

<!-- RESEARCH_ROUTE=RWKV -->

- 日期：2026-09-01
- 代理：`tail_agg_alpha_decision_fable`（模型 `claude-fable-5`；Claude Code 的 `Agent` 工具无 `effort` 入参，强度继承会话设置）
- 目标：裁决实体内尾部聚合参数 α 的取值路径——A（固定 α，独立依据）／B（复用 BER 预算 β）／C（可微软聚合，绕开定值）

## 待办

- [x] 建检查点目录与本文件
- [x] 读 `2026-09-01-BER同框架机制一可行性/调研报告.md`
- [x] 读 `2026-08-31-BER机制形式化与复杂度规约.md`
- [x] 读 `ch3_ft_entity_ranking_loss.py` 的 `prefix_scores`
- [x] 路径 B 核算（实验 1，`bag_dist_path_b.py`）：六档 β 下 91.7%–99.3% 实体恒为 max，否决
- [x] 路径 C 核验（实验 2，`lse_path_c_probe.py`）：数值良态、fullgraph 零断裂，但 C10 τ0 定值回归＋尺度混淆，降为退路
- [x] 路径 A 评估（实验 1、3）：防饱和 ⟺ α≤1/2 ＋ 支撑最大化 ⇒ α=0.5 唯一解
- [x] 本地文献索引查询（status 在线；四篇全文笔记在库；ATk 原文仍摘要级、k 无推荐定值）
- [x] 写裁决报告并提交（`裁决报告.md`）

## 结果

**采纳路径 A：α = 0.5（冻结）；C 为预注册退路；B 实测否决。** 详见 `裁决报告.md`。

## 硬约束（复述）

- 不得用先导 α→AP 读数选值；不读 LSPR24；不连服务器不占 GPU
- 数值验证用 `/opt/miniconda3/envs/rwkv/bin/python`（torch 2.12.0）
- 报告落 `裁决报告.md`，git 只 add 精确路径
