# LAMDA PCT 预筛图件目录

## 图 1：开发期指标对比

- 文件：`figures/figure-01-development-metrics.png`、`figures/figure-01-development-metrics.svg`
- 目的：同时展示 AP、F1、FPR、FNR，避免单指标选择。
- 数据源：`development-summary.json`。
- 关键观察：PCT 单臂的 FPR/FNR 均高于 ER；缺口修复相关臂虽降低 FNR，但 FPR 明显升高。
- 决策影响：四臂不具备进入封印年的开发期资格。
- 解释边界：单种子、CPU、`screening_only`，无误差条。

## 图 2：历史良性 gate

- 文件：`figures/figure-02-historical-benign-gate.png`、`figures/figure-02-historical-benign-gate.svg`
- 目的：展示训练至 2016/2017 后历史良性 FPR 的旧值与新值。
- 数据源：四臂 `metrics/year-2016.json` 与 `year-2017.json` 的 `historical_benign_gate`。
- 关键观察：2016 年三种候选均高于 ER；2017 年虽有下降，仍不能抵消 pooled 开发期 FPR 增量。
- 决策影响：不能以单个年份的 gate 改写整体门槛。
- 解释边界：描述性诊断，不是独立重复实验或最终测试。
