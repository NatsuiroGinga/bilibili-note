# LSPR24 已访问目标年描述性评价表

本表由原始运行制品机械生成；粗体表示同一评价池、同一指标的全精度最强值。

| 模型 | 配置类型 | 可微 | 运行身份 | 评价池 | 逐流AP | 实体AP | 最大实体AP | DR@0.1%FPR | DR@0.5%FPR | DR@1%FPR | DR@2%FPR | DR@4%FPR | DR@8%FPR | 完整曲线摘要 | 完整曲线制品 | 证据等级 | 原始路径 | 待补原因 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 随机森林 | 论文约束独立复现 | 否 | ch3-baselines-full | LSPR24已访问目标年描述性评价池 | 0.13426844073 | 0.260525981151 | 0.260525981151 | — | — | — | — | 0.425531914894 | — | 仅持久化4% FPR单点；无完整告警预算曲线 | — | 单次运行直接可比 | /Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/diagnostics/ch3-baselines-full/trees_results.json | — |
| XGBoost | 已发表配置重跑 | 否 | ch3-baselines-full | LSPR24已访问目标年描述性评价池 | 0.2223914546 | 0.51289884799 | **0.51289884799** | — | — | — | — | 0.692819148936 | — | 仅持久化4% FPR单点；无完整告警预算曲线 | — | 单次运行直接可比 | /Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/diagnostics/ch3-baselines-full/trees_results.json | — |
| 一维卷积网络（主干重建） | 论文约束独立复现 | 是 | ch3-baselines-full | LSPR24已访问目标年描述性评价池 | 0.127082755846 | 0.409638921562 | 0.409638921562 | — | — | — | — | 0.648936170213 | — | 仅持久化4% FPR单点；无完整告警预算曲线 | — | 单次运行直接可比 | /Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/diagnostics/ch3-baselines-full/neural_results.json | — |
| 门控循环网络 | 已发表配置重跑 | 是 | ch3-baselines-full | LSPR24已访问目标年描述性评价池 | 0.287728740908 | 0.159955930349 | 0.159955930349 | — | — | — | — | 0.308510638298 | — | 仅持久化4% FPR单点；无完整告警预算曲线 | — | 单次运行直接可比 | /Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/diagnostics/ch3-baselines-full/neural_results.json | — |
| 全注意力网络 | 已发表配置重跑 | 是 | ch3-baselines-full | LSPR24已访问目标年描述性评价池 | **0.325725660495** | 0.353619988596 | 0.353619988596 | — | — | — | — | 0.740691489362 | — | 仅持久化4% FPR单点；无完整告警预算曲线 | — | 单次运行直接可比 | /Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/diagnostics/ch3-baselines-full/neural_results.json | — |
| 多层感知机＋CPA-ELP | 本章方法 | 是 | ch3-2x2-fairsel | LSPR24已访问目标年描述性评价池 | 0.29184262512 | 0.518350415398 | 0.291738609767 | — | — | — | — | 0.703457446809 | — | 仅持久化4% FPR单点；无完整告警预算曲线 | — | 单次运行直接可比 | /Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/diagnostics/ch3-2x2-fairsel/ch3_2x2_fairsel_results.json | — |
| XGBoost＋CPA-ELP | 本章机制外挂树集成 | 否 | ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1-eval-continuation2 | LSPR24已访问目标年描述性评价池 | 0.283257718059 | **0.565078418714** | — | **0.240691489362** | **0.398936170213** | **0.531914893617** | **0.75** | **0.889627659574** | **0.954787234043** | 持久化六个预设FPR工作点；无全可达预算曲线制品 | — | 单次运行直接可比 | /Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/diagnostics/ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1-eval-continuation2/xgb_cpa_elp_results.json | — |
| ResMLP2＋CPA-ELP | 骨干升级候选 | 是 | ch3-resmlp2-cpa-elp-protocol-a-2x2-seed42-v1 | LSPR24已访问目标年描述性评价池 | 0.11092047122 | 0.298882189119 | 0.263302580953 | 0.093085106383 | 0.253989361702 | 0.340425531915 | 0.49335106383 | 0.63164893617 | 0.742021276596 | 完整可达负实体预算曲线，共46363个预算点；字段：n_false_positive_entity、nominal_fpr、realized_fpr、detection_rate | /Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819/thesis/experiments/llm_probe/runs/diagnostics/ch3-resmlp2-cpa-elp-protocol-a-2x2-seed42-v1/complete-alert-budget-curves.npz#C11 | 单次运行直接可比 | /Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819/thesis/experiments/llm_probe/runs/diagnostics/ch3-resmlp2-cpa-elp-protocol-a-2x2-seed42-v1/aggregate-results.json | — |
| TabM4＋CPA-ELP | 骨干升级候选 | 是 | ch3-tabm4-cpa-elp-protocol-a-2x2-seed42-v1 | — | — | — | — | — | — | — | — | — | — | — | — | 单次运行直接可比 | /Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/diagnostics/ch3-tabm4-cpa-elp-protocol-a-2x2-seed42-v1/aggregate-results.json | 运行已完成 exit_code=0，但制品仅存服务器，两个本地 runs 根均无；拉回后重跑本工具即自动填入 |
| RWKV-7＋CPA-ELP | 骨干升级候选 | 是 | — | — | — | — | — | — | — | — | — | — | — | — | — | 未运行 | — | 实现已就绪但尚未运行，无结果制品 |
| GRANDE | 骨干升级候选 | 是 | — | — | — | — | — | — | — | — | — | — | — | — | — | 未运行 | — | 计划已冻结，尚无运行制品 |
| 骨干专属论文配方模型 | 论文配方 | 是 | — | — | — | — | — | — | — | — | — | — | — | — | — | 未运行 | — | N-05 设计已冻结、效果待实验 |

## 缺失值说明

- 随机森林：完整曲线制品：原始来源未持久化完整告警预算曲线制品；DR@0.1%FPR：原始来源未持久化该FPR工作点；DR@0.5%FPR：原始来源未持久化该FPR工作点；DR@1%FPR：原始来源未持久化该FPR工作点；DR@2%FPR：原始来源未持久化该FPR工作点；DR@8%FPR：原始来源未持久化该FPR工作点。
- XGBoost：完整曲线制品：原始来源未持久化完整告警预算曲线制品；DR@0.1%FPR：原始来源未持久化该FPR工作点；DR@0.5%FPR：原始来源未持久化该FPR工作点；DR@1%FPR：原始来源未持久化该FPR工作点；DR@2%FPR：原始来源未持久化该FPR工作点；DR@8%FPR：原始来源未持久化该FPR工作点。
- 一维卷积网络（主干重建）：完整曲线制品：原始来源未持久化完整告警预算曲线制品；DR@0.1%FPR：原始来源未持久化该FPR工作点；DR@0.5%FPR：原始来源未持久化该FPR工作点；DR@1%FPR：原始来源未持久化该FPR工作点；DR@2%FPR：原始来源未持久化该FPR工作点；DR@8%FPR：原始来源未持久化该FPR工作点。
- 门控循环网络：完整曲线制品：原始来源未持久化完整告警预算曲线制品；DR@0.1%FPR：原始来源未持久化该FPR工作点；DR@0.5%FPR：原始来源未持久化该FPR工作点；DR@1%FPR：原始来源未持久化该FPR工作点；DR@2%FPR：原始来源未持久化该FPR工作点；DR@8%FPR：原始来源未持久化该FPR工作点。
- 全注意力网络：完整曲线制品：原始来源未持久化完整告警预算曲线制品；DR@0.1%FPR：原始来源未持久化该FPR工作点；DR@0.5%FPR：原始来源未持久化该FPR工作点；DR@1%FPR：原始来源未持久化该FPR工作点；DR@2%FPR：原始来源未持久化该FPR工作点；DR@8%FPR：原始来源未持久化该FPR工作点。
- 多层感知机＋CPA-ELP：完整曲线制品：原始来源未持久化完整告警预算曲线制品；DR@0.1%FPR：原始来源未持久化该FPR工作点；DR@0.5%FPR：原始来源未持久化该FPR工作点；DR@1%FPR：原始来源未持久化该FPR工作点；DR@2%FPR：原始来源未持久化该FPR工作点；DR@8%FPR：原始来源未持久化该FPR工作点。
- XGBoost＋CPA-ELP：完整曲线制品：原始来源未持久化完整告警预算曲线制品；最大实体AP：原始来源未单独持久化最大池化实体AP。
- TabM4＋CPA-ELP：完整曲线制品：运行已完成 exit_code=0，但制品仅存服务器，两个本地 runs 根均无；拉回后重跑本工具即自动填入；完整曲线摘要：运行已完成 exit_code=0，但制品仅存服务器，两个本地 runs 根均无；拉回后重跑本工具即自动填入；DR@0.1%FPR：运行已完成 exit_code=0，但制品仅存服务器，两个本地 runs 根均无；拉回后重跑本工具即自动填入；DR@0.5%FPR：运行已完成 exit_code=0，但制品仅存服务器，两个本地 runs 根均无；拉回后重跑本工具即自动填入；DR@1%FPR：运行已完成 exit_code=0，但制品仅存服务器，两个本地 runs 根均无；拉回后重跑本工具即自动填入；DR@2%FPR：运行已完成 exit_code=0，但制品仅存服务器，两个本地 runs 根均无；拉回后重跑本工具即自动填入；DR@4%FPR：运行已完成 exit_code=0，但制品仅存服务器，两个本地 runs 根均无；拉回后重跑本工具即自动填入；DR@8%FPR：运行已完成 exit_code=0，但制品仅存服务器，两个本地 runs 根均无；拉回后重跑本工具即自动填入；实体AP：运行已完成 exit_code=0，但制品仅存服务器，两个本地 runs 根均无；拉回后重跑本工具即自动填入；逐流AP：运行已完成 exit_code=0，但制品仅存服务器，两个本地 runs 根均无；拉回后重跑本工具即自动填入；最大实体AP：运行已完成 exit_code=0，但制品仅存服务器，两个本地 runs 根均无；拉回后重跑本工具即自动填入。
- RWKV-7＋CPA-ELP：完整曲线制品：实现已就绪但尚未运行，无结果制品；完整曲线摘要：实现已就绪但尚未运行，无结果制品；DR@0.1%FPR：实现已就绪但尚未运行，无结果制品；DR@0.5%FPR：实现已就绪但尚未运行，无结果制品；DR@1%FPR：实现已就绪但尚未运行，无结果制品；DR@2%FPR：实现已就绪但尚未运行，无结果制品；DR@4%FPR：实现已就绪但尚未运行，无结果制品；DR@8%FPR：实现已就绪但尚未运行，无结果制品；实体AP：实现已就绪但尚未运行，无结果制品；逐流AP：实现已就绪但尚未运行，无结果制品；最大实体AP：实现已就绪但尚未运行，无结果制品。
- GRANDE：完整曲线制品：计划已冻结，尚无运行制品；完整曲线摘要：计划已冻结，尚无运行制品；DR@0.1%FPR：计划已冻结，尚无运行制品；DR@0.5%FPR：计划已冻结，尚无运行制品；DR@1%FPR：计划已冻结，尚无运行制品；DR@2%FPR：计划已冻结，尚无运行制品；DR@4%FPR：计划已冻结，尚无运行制品；DR@8%FPR：计划已冻结，尚无运行制品；实体AP：计划已冻结，尚无运行制品；逐流AP：计划已冻结，尚无运行制品；最大实体AP：计划已冻结，尚无运行制品。
- 骨干专属论文配方模型：完整曲线制品：N-05 设计已冻结、效果待实验；完整曲线摘要：N-05 设计已冻结、效果待实验；DR@0.1%FPR：N-05 设计已冻结、效果待实验；DR@0.5%FPR：N-05 设计已冻结、效果待实验；DR@1%FPR：N-05 设计已冻结、效果待实验；DR@2%FPR：N-05 设计已冻结、效果待实验；DR@4%FPR：N-05 设计已冻结、效果待实验；DR@8%FPR：N-05 设计已冻结、效果待实验；实体AP：N-05 设计已冻结、效果待实验；逐流AP：N-05 设计已冻结、效果待实验；最大实体AP：N-05 设计已冻结、效果待实验。

## 评价口径

- LSPR23 表只记录源年选择证据；LSPR24 表只记录已访问目标年的描述性评价，二者不混排。
- 实体 AP 为各运行预先注册的主聚合口径；最大实体 AP 单列，缺失时不反推。
- 评价时间含预测与指标计算时会在时间口径列明示，不能替代纯模型推理时间。
- 资源表不判最强；树集成使用树数、节点数或深度描述规模，不机械折算神经网络参数量。
