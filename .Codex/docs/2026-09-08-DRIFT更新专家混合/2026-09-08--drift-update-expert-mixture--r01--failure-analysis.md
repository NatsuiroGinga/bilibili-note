---
type: results-report
date: 2026-09-08
experiment_line: drift-update-expert-mixture
round: 1
purpose: failure-analysis
status: completed
source_artifacts:
  - analysis-report.md
  - stats-appendix.md
linked_experiments:
  - thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-update-expert-mixture-fold0-short-step-v1/result.json
linked_results:
  - thesis/methods/第三章-DRIFT双侧风险约束更新专家混合研究卡.md
---

# DRIFT 更新专家混合 / 第1轮 / 失败分析 / 2026-09-08

## 一、执行摘要

折0固定全局更新专家混合在32批有限步后全面优于联合等权的三项 BCE，但良性 BCE 相对零更新增加 `6.483869477e-6`，未通过预注册硬门。运行裁决为 `rejected_after_finite_step`，当前固定权重形式停止，不进入折1、目标年份或调参。

## 二、实验身份与决策背景

实验复用 N12 G2 折0两支端点、优化器状态、风险梯度与同一32768样本固定块。它检验原始梯度线性规划的三风险可行方向是否能转化为真实 Adam 32批更新，而不是重新训练 N12 或评价跨年效果。

## 三、设置与评价协议

- 三臂：`no_update`、`joint_all_equal`、`risk_feasible_update_mixture`。
- 唯一主要比较：混合臂相对零更新和联合等权的良性、DGA micro、family-macro BCE。
- 附加披露：AP、AUROC、固定源阈值及默认阈值的 FPR/FNR。
- 身份：单折、单种子、单固定块，`screening_only`。

## 四、主要发现

混合臂相对零更新使 DGA micro 和 family-macro BCE 分别下降 `0.606524428064` 与 `0.887813644278`，但良性 BCE 增加 `0.000006483869477`。源阈值 FPR 从 `0.009913333333` 升至 `0.027633333333`，AP 从 `0.920325958117` 降至 `0.898708778722`，AUROC 从 `0.951885067970` 降至 `0.938016178150`。

混合臂相对联合等权的三项 BCE 均改善，因此固定权重减少了等权更新伤害；但该次要观察不能覆盖零更新主门失败。

## 五、统计验证

没有可用的推断统计。独立运行单位数为1，32批属于同一连续优化轨迹。分析仅依据精确聚合值、配对差值和预注册机械门，不报告显著性、置信区间或效应量。

## 六、图件解释

本轮不生成图件。精确数值表已足以完成裁决，且没有独立重复可提供误差条；批次轨迹图会夸大证据量。

## 七、失败情况与边界

- 原始梯度线性可行性没有在有限步后维持良性风险非增。
- 子词分支在两个更新臂中均 `32/32` 批触发裁剪；该事实与 Adam、逐批非线性共同构成可能解释，但实验没有机制消融，不能作因果归因。
- 结果只否决当前固定全局权重形式，不否决所有风险约束、所有可学习门控或所有更新混合。
- 未访问目标年份，不能作跨年结论。

## 八、认知变化

此前“全局单纯形存在原始梯度可行解”只证明线性局部方向存在。当前结果将其降为不足以支撑有限步安全的代数观察，并关闭当前固定权重执行形式。

## 九、下一动作

等待标准可学习门控正锚点的资格核查完成后，由主代理依据近邻、接口和最小证伪成本裁决是否值得立新研究卡。本报告不选择新机制，也不把该门控写成已有效。

上层会话现有 `/goal` 仍描述此前待执行状态，未吸收本次 `rejected_after_finite_step`，已经过时；本任务按边界不修改 `/goal`。

## 十、制品与复现索引

- [严格分析](analysis-report.md)
- [统计附录](stats-appendix.md)
- [图件目录](figure-catalog.md)
- [研究卡](../../../thesis/methods/第三章-DRIFT双侧风险约束更新专家混合研究卡.md)
- 原始结果：`thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-update-expert-mixture-fold0-short-step-v1/result.json`

本仓库未对该内部报告执行额外 Obsidian 写回；专题目录是用户指定的唯一落点。
