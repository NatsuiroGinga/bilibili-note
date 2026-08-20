# LSPR23 源年选择表

本表由原始运行制品机械生成；粗体表示同一评价池、同一指标的全精度最强值。

| 模型 | 配置类型 | 可微 | 运行身份 | 选择池 | 选择指标 | 选择分数 | 选定轮次 | 验证逐流AP | 选定幂指数 | 选择口径 | 证据等级 | 原始路径 | 待补原因 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 随机森林 | 论文约束独立复现 | 否 | ch3-baselines-full | LSPR23固定配置训练集 | — | — | — | — | — | 树模型无 epoch 概念与检查点选择，直接按各自论文配置训到底；LSPR24 只在训练全部结束后评价一次 | 单次运行直接可比 | /Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/diagnostics/ch3-baselines-full/trees_results.json | — |
| XGBoost | 已发表配置重跑 | 否 | ch3-baselines-full | LSPR23固定配置训练集 | — | — | — | — | — | 树模型无 epoch 概念与检查点选择，直接按各自论文配置训到底；LSPR24 只在训练全部结束后评价一次 | 单次运行直接可比 | /Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/diagnostics/ch3-baselines-full/trees_results.json | — |
| 一维卷积网络（主干重建） | 论文约束独立复现 | 是 | ch3-baselines-full | LSPR23实体不相交验证集 | 前5名轮次预测平均的逐流AP | 0.999741846994 | 15、17、18、19、20 | 0.999741846994 | — | 逐 epoch 在 LSPR23 实体不相交验证集上算逐流 AP，取前 5 名 epoch 的预测平均；学习率在 {各自 Q0/论文值, 本章 2e-3} 两档中按同一验证信号择优；LSPR24 不参与选择 | 单次运行直接可比 | /Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/diagnostics/ch3-baselines-full/neural_results.json | — |
| 门控循环网络 | 已发表配置重跑 | 是 | ch3-baselines-full | LSPR23实体不相交验证集 | 前5名轮次预测平均的逐流AP | **0.999843019888** | 12、14、15、19、20 | 0.999843019888 | — | 逐 epoch 在 LSPR23 实体不相交验证集上算逐流 AP，取前 5 名 epoch 的预测平均；学习率在 {各自 Q0/论文值, 本章 2e-3} 两档中按同一验证信号择优；LSPR24 不参与选择 | 单次运行直接可比 | /Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/diagnostics/ch3-baselines-full/neural_results.json | — |
| 全注意力网络 | 已发表配置重跑 | 是 | ch3-baselines-full | LSPR23实体不相交验证集 | 前5名轮次预测平均的逐流AP | 0.999517272258 | 4、8、11、18、19 | 0.999517272258 | — | 逐 epoch 在 LSPR23 实体不相交验证集上算逐流 AP，取前 5 名 epoch 的预测平均；学习率在 {各自 Q0/论文值, 本章 2e-3} 两档中按同一验证信号择优；LSPR24 不参与选择 | 单次运行直接可比 | /Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/diagnostics/ch3-baselines-full/neural_results.json | — |
| 多层感知机＋CPA-ELP | 本章方法 | 是 | ch3-2x2-fairsel | LSPR23实体不相交验证集 | 单轮逐流AP | **0.999742290479** | 10 | 0.999742290479 | 1.0562171936 | 逐epoch在LSPR23实体不相交验证集上取逐流AP最大的epoch，无末5平均，不早停 | 单次运行直接可比 | /Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/diagnostics/ch3-2x2-fairsel/ch3_2x2_fairsel_results.json | — |
| XGBoost＋CPA-ELP | 本章机制外挂树集成 | 否 | ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1-eval-continuation2 | LSPR23三折实体OOF | 实体OOF AP | 0.922235112994 | — | — | 1 | LSPR23 三折实体折外 CPA 单机制实体 AP（最大聚合） | 单次运行直接可比 | /Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/diagnostics/ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1-eval-continuation2/xgb_cpa_elp_results.json | — |
| ResMLP2＋CPA-ELP | 骨干升级候选 | 是 | ch3-resmlp2-cpa-elp-protocol-a-2x2-seed42-v1 | LSPR23实体不相交验证集 | 单轮逐流AP | 0.999649147724 | 12 | 0.999649147724 | 0.998496055603 | 协议A：源年验证集单轮逐流AP择优 | 单次运行直接可比 | /Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819/thesis/experiments/llm_probe/runs/diagnostics/ch3-resmlp2-cpa-elp-protocol-a-2x2-seed42-v1/aggregate-results.json | — |
| TabM4＋CPA-ELP | 骨干升级候选 | 是 | ch3-tabm4-cpa-elp-protocol-a-2x2-seed42-v1 | — | — | — | — | — | — | — | 单次运行直接可比 | /Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/diagnostics/ch3-tabm4-cpa-elp-protocol-a-2x2-seed42-v1/aggregate-results.json | 运行已完成 exit_code=0，但制品仅存服务器，两个本地 runs 根均无；拉回后重跑本工具即自动填入 |
| RWKV-7＋CPA-ELP | 骨干升级候选 | 是 | — | — | — | — | — | — | — | — | 未运行 | — | 实现已就绪但尚未运行，无结果制品 |
| GRANDE | 骨干升级候选 | 是 | — | — | — | — | — | — | — | — | 未运行 | — | 计划已冻结，尚无运行制品 |
| 骨干专属论文配方模型 | 论文配方 | 是 | — | — | — | — | — | — | — | — | 未运行 | — | N-05 设计已冻结、效果待实验 |

## 缺失值说明

- 随机森林：选定轮次：该来源没有单轮检查点选择，或未持久化选定轮次；选定幂指数：该模型或选择规则不使用幂平均指数；选择指标：固定配置直接训练，不执行开发集择优；选择分数：固定配置直接训练，或原始制品未持久化选择分数；验证逐流AP：该来源未持久化可比较的源年验证逐流AP。
- XGBoost：选定轮次：该来源没有单轮检查点选择，或未持久化选定轮次；选定幂指数：该模型或选择规则不使用幂平均指数；选择指标：固定配置直接训练，不执行开发集择优；选择分数：固定配置直接训练，或原始制品未持久化选择分数；验证逐流AP：该来源未持久化可比较的源年验证逐流AP。
- 一维卷积网络（主干重建）：选定幂指数：该模型或选择规则不使用幂平均指数。
- 门控循环网络：选定幂指数：该模型或选择规则不使用幂平均指数。
- 全注意力网络：选定幂指数：该模型或选择规则不使用幂平均指数。
- XGBoost＋CPA-ELP：选定轮次：该来源没有单轮检查点选择，或未持久化选定轮次；验证逐流AP：该来源未持久化可比较的源年验证逐流AP。
- TabM4＋CPA-ELP：选定轮次：运行已完成 exit_code=0，但制品仅存服务器，两个本地 runs 根均无；拉回后重跑本工具即自动填入；选定幂指数：运行已完成 exit_code=0，但制品仅存服务器，两个本地 runs 根均无；拉回后重跑本工具即自动填入；选择指标：运行已完成 exit_code=0，但制品仅存服务器，两个本地 runs 根均无；拉回后重跑本工具即自动填入；选择口径：运行已完成 exit_code=0，但制品仅存服务器，两个本地 runs 根均无；拉回后重跑本工具即自动填入；选择分数：运行已完成 exit_code=0，但制品仅存服务器，两个本地 runs 根均无；拉回后重跑本工具即自动填入；验证逐流AP：运行已完成 exit_code=0，但制品仅存服务器，两个本地 runs 根均无；拉回后重跑本工具即自动填入。
- RWKV-7＋CPA-ELP：选定轮次：实现已就绪但尚未运行，无结果制品；选定幂指数：实现已就绪但尚未运行，无结果制品；选择指标：实现已就绪但尚未运行，无结果制品；选择口径：实现已就绪但尚未运行，无结果制品；选择分数：实现已就绪但尚未运行，无结果制品；验证逐流AP：实现已就绪但尚未运行，无结果制品。
- GRANDE：选定轮次：计划已冻结，尚无运行制品；选定幂指数：计划已冻结，尚无运行制品；选择指标：计划已冻结，尚无运行制品；选择口径：计划已冻结，尚无运行制品；选择分数：计划已冻结，尚无运行制品；验证逐流AP：计划已冻结，尚无运行制品。
- 骨干专属论文配方模型：选定轮次：N-05 设计已冻结、效果待实验；选定幂指数：N-05 设计已冻结、效果待实验；选择指标：N-05 设计已冻结、效果待实验；选择口径：N-05 设计已冻结、效果待实验；选择分数：N-05 设计已冻结、效果待实验；验证逐流AP：N-05 设计已冻结、效果待实验。

## 评价口径

- LSPR23 表只记录源年选择证据；LSPR24 表只记录已访问目标年的描述性评价，二者不混排。
- 实体 AP 为各运行预先注册的主聚合口径；最大实体 AP 单列，缺失时不反推。
- 评价时间含预测与指标计算时会在时间口径列明示，不能替代纯模型推理时间。
- 资源表不判最强；树集成使用树数、节点数或深度描述规模，不机械折算神经网络参数量。
