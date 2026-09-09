# 双风险梯度投影图件目录

## 图 1：开发期指标

- 文件：[figure-01-development-metrics.svg](figures/figure-01-development-metrics.svg)
- 用途：比较 ER 与双风险投影在 AP、F1、FPR、FNR 上的逐年变化。
- 关键观察：投影臂 FPR 略低，但 FNR 和 AP 更差。
- 解释边界：单种子、screening_only，不支持正式泛化结论。

## 图 2：回溯负向翻转

- 文件：[figure-02-backward-flips.svg](figures/figure-02-backward-flips.svg)
- 用途：展示投影对旧恶意负向翻转的安全保持效果。
- 关键观察：2017 端点翻转率由约 `0.0778` 降至约 `0.0403`，但该安全收益伴随当前恶意 FNR 上升。
- 解释边界：必须与 AP/FNR/FPR 和正向修复共同解读。
