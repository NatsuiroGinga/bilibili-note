# 正锚点核查过程笔记（2026-09-09）

- 16:xx 主代理手写探针首版有两处路径占位笔误，重写；branch_features 改为 import 原工具（`ch3_drift_official_branch_conflict_diagnostic.py`）消除属性名风险；分类概率语义以原工具 `probabilities()`（softmax[:,1]）为准。
- 小样本自检（T17 val 前 3000+3000）：融合错误率 0.0278 vs 既有制品 0.02825 ✓；但 subword 挽回=0 与制品聚合（6317）严重不符。
- 根因：中和均值取样——原工具主流程用 T17 val **全量**（config `full:true`）算合并均值，我先用前 6000 抽样均值导致反事实偏置。改为全量均值后待复验。
- MPS 限制：`aten::_nested_tensor_from_mask_left_aligned` 无 MPS 实现，`PYTORCH_ENABLE_MPS_FALLBACK=1` 下该算子落 CPU、其余 MPS（官方警告已接受，全量前向预计 20–40 分钟）。
- 用户两次纠偏已吸收：①脚本与实验由主进程推进、子代理只管文档；②长任务一律后台不阻塞会话。
- 报告 (6) 回收后正锚点设计升级为两问式（which-branch + override），lookup 优先、LR 为辅；判据冻结在 task_plan.md，探针脚本内嵌同版。
- 运行：后台 PID 10527，console 落 probe-console.log，结果落 positive-anchor-result.json。出数后按 task_plan 第三节裁决映射执行，不修改判据。
