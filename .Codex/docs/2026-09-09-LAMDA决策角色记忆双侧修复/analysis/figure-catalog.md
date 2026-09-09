# 阶段 C 图件目录

## 图 1：开发期指标

- 文件：[figure-01-development-metrics.svg](figures/figure-01-development-metrics.svg)
- 用途：并列展示四臂在 2016/2017 的 AP、F1、FPR、FNR。
- 关键观察：ER+M 主要以 FNR 和 AP 换取较低 FPR；ER+O 与 ER+M+O 的 FPR 明显升高。
- 解释边界：单种子、screening_only，不支持正式泛化或显著性结论。

## 图 2：旧恶意负向翻转

- 文件：[figure-02-development-flips.svg](figures/figure-02-development-flips.svg)
- 用途：检验 M/O 是否保持标准 Replay 的历史恶意安全性。
- 关键观察：三个候选臂在 2017 端点的负向翻转率都显著高于 ER。
- 解释边界：负向翻转必须与当前年度 FNR、正向修复和 FPR 一起解释，不能单独作为安全指标。
