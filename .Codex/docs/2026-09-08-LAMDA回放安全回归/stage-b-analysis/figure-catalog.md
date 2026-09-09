# 阶段 B 图件目录

## 图 1：逐年当前年度指标

- 文件：[figure-01-current-year-metrics.svg](figures/figure-01-current-year-metrics.svg)
- 用途：同时显示两臂在 2020--2025 的 AP、F1、FPR、FNR，避免只看一个汇总指标。
- 数据源：阶段 B 两臂 12 个年度指标 JSON 与逐样本预测；复算 JSON 的 `per_year_current_year`。
- 读者应注意：2024 联合臂的 F1/FNR 改善没有延续到 2025；FPR 在 2020、2023--2025 方向不利。
- 解释检查：该图只能支持年度取舍描述，不能支持多种子显著性或最终测试结论。

## 图 2：回溯旧恶意负向翻转

- 文件：[figure-02-backward-negative-flips.svg](figures/figure-02-backward-negative-flips.svg)
- 用途：显示安全回归信号随训练终点的变化，并检验下降是否跨年度一致。
- 数据源：每臂 `metrics/year-*.json` 的 `evaluation.backward.old_malicious_negative_flip`。
- 读者应注意：联合臂总体下降，但 2020 和 2023 端点高于对照，说明不是单调保护。
- 解释检查：翻转率必须与当前年度 FNR/FPR 一起阅读，不能单独当作安全性胜出。
