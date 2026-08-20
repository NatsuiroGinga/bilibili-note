# 证据笔记：机制二路径风险长度桶诊断

## 唯一输入

- 运行目录：`thesis/experiments/llm_probe/runs/diagnostics/ch4-xgb-path-risk-length-bucket-lspr23-diagnostic-seed42-v1`。
- 运行状态：`finished/complete/success/exit=0`；`python-exit-code.txt=0`，`tee-exit-code.txt=0`。
- 清单哈希复核：`aggregate-results.json`、`input-receipt.json`、`resource-summary.json` 的本地 SHA-256 均与 `manifest.json` 一致。
- 父 M1 摘要：本地 `summary.json` SHA-256 为 `2e4bbfe044b9ce9407090af765220fc7bc5829188cadcdfb33284002f633d462`，与输入收据一致；父运行状态为 `finished/complete/exit=0`。

## 机械完整性

- 诊断声明 B0、B1、M1 的轮次指标与聚合指标均精确匹配父运行。
- `flow_coverage_count=scored_flow_count=16,353,511`，重复覆盖、段内时间逆序和跨段时间逆序均为 0。
- `target_year_arrays_read=0`、`models_trained=0`、加载折外模型数为 3；没有持久化逐流分数、逐实体分数或实体键。

## 描述性读数

- M1 池化：FPR=`0.03711089397172313`，DR=`0.9832635983263598`，FP=`5583`，TP=`235`。
- M1 五桶 FPR：`1-2=0.0271465974`、`3-10=0.0450469427`、`11-100=0.0904020451`、`101-1000=0.1333557272`、`1001+=0.0720164609`。
- M1 五桶 DR：`0.972972973`、`0.977777778`、`1.0`、`0.974683544`、`1.0`。
- M1 漏检正实体数为 4。其 `path_maximum/threshold` 的最小值、中位数、最大值依次为 `0.0019703415`、`0.0234194283`、`0.9777939760`；全体仍低于阈值，但只有一个接近阈值的聚合极值，不能把它表述为持续次高分模式。

## 解释边界

- 仅支持“源年单种子中，池化 FPR 掩盖长度条件风险病灶”。
- 不支持 M1 有效性的统计或论文结论，不支持漏检实体存在持续次高分，也不支持反射累积已经有效。
- 可将反射累积推进到最小 Q0，前提是作为待证对照并维持冻结输入、模型与 Tong 参数。
