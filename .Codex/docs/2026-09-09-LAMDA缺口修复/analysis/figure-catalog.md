# LAMDA 缺口修复筛选图件目录

## 图 1：开发期 pooled 指标

- 文件：`figures/figure-01-development-metrics.png`、`figures/figure-01-development-metrics.svg`
- 目的：并列展示 ER、缺口修复、条件门控和联合臂的 AP、F1、FPR、FNR，避免只看一个指标。
- 数据源：四臂 `development-summary.json`，独立复算值。
- 图例含义：柱高为单种子 pooled 点估计；没有误差条，因为没有多种子重复。
- 关键观察：缺口修复降低 FNR 但 FPR 大幅上升；条件门控 FPR 略降但 FNR 上升；联合臂仍高于 ER 的 FPR。
- 决策影响：三种具体实现均不能进入封印年；下一候选必须显式加入独立 FPR gate 或更保守的安全回归保护。
- 解释边界：该图是筛选诊断，不是统计显著性图，也不是无泄漏泛化结果。

## 图 2：开发期翻转诊断

- 文件：`figures/figure-02-transition-rates.png`、`figures/figure-02-transition-rates.svg`
- 目的：同时显示恶意正向修复率、恶意负向翻转率和良性新增误报率，拆解保持—修复取舍。
- 数据源：相邻年度 `next_year.jsonl` 与 `current_year.jsonl` 的逐样本配对复算。
- 图例含义：每条线为固定运行下的配对比例；分母分别为旧模型漏判恶意、旧模型正确恶意和全部良性样本。
- 关键观察：缺口修复的恶意修复率最高，但良性新增误报率也最高；条件门控把良性新增误报压回 ER 附近，却没有恢复恶意修复。
- 决策影响：不能只用 FNR 或旧恶意翻转率筛选；后续必须把 FPR、恶意修复和回归同时作为门槛。
- 解释边界：配对计数是描述性证据，单种子下不进行独立性显著性检验。
