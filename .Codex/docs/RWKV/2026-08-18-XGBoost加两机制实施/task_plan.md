# XGBoost 加两机制实施计划

## 目标

在 B76 上完成 XGBoost 的 CPA、ELP 及组合四格真实实验，以源年实体折外协议选择 CPA 挂载和幂次，并生成可复核的聚合制品。

## 文件边界

- 新增 `thesis/experiments/llm_probe/tools/ch3_xgb_cpa_elp_entity_oof.py`
- 新增 `thesis/experiments/llm_probe/configs/ch3-xgb-cpa-elp-gpu-oof-seed42-v1.json`
- 新增 `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_xgb_cpa_elp_gpu_oof_seed42_v1.sh`
- 更新本目录 `notes.md` 和最终运行报告
- 不修改既有 XGBoost 锚点脚本、第三章正文、共同缓存或正在运行的卷积实验

## 阶段

- [x] P0：读取规则、执行文档、文献审计、接口勘察和真实缓存
- [x] P0：核验 XGBoost 3.2.0 官方 GPU 接口与 `E23` 实体分组
- [x] P0：修订执行合同，删除实体泄漏、CPU 逐位门和逐样本持久化问题
- [x] P1：实现单入口工具、冻结配置和持久启动器
- [x] P1：执行语法、配置、命令入口和 Shell 检查
- [x] P1：同步 B76；用户依据实时资源明确允许与卷积并行，已启动持久会话
- [ ] P1：用必要真实折测量 `max_gpu_fits=1/2`，随后完成 11 次拟合
- [ ] P1：回收聚合制品，执行结果分析并更新恢复文档
- [ ] P2：按原子范围提交代码、配置、启动器、合同和报告

## 当前状态

运行身份为 `ch3-xgb-cpa-elp-gpu-oof-seed42-v1`，持久会话为
`ch3-xgb-cpa-elp-gpu-s42-v1`。当前处于源年选择阶段，已完成源年实体、折分、时间非降与
SwanLab 前置门禁。`mean166` 已完成，并通过 `16,353,511` 条流各写入一次的覆盖核验；
`semantic168` 当前为 `172,032/271,815（63.3%）`。真实拟合进度仍为 `0/11`，首折未完成，
适配器与 `p` 均未选择，模型制品为 `0`，LSPR24 尚未读取。状态文件为
`running/source_selection/detail=started/exit_code=null`，错误扫描零命中，实验待证。

## 阻塞

- 无阻塞。启动时实测 GPU 空闲 `22810 MiB`，资源门要求至少 `11264 MiB`；用户已明确允许
  在控制组内存、磁盘和显存门均通过时与卷积实验并行。
- 2026-08-18 16:34 快照：GPU 使用／总量 `9842/32607 MiB`、空闲 `22268 MiB`、利用率约
  `34%`；控制组内存使用 `52,524,875,776` 字节，上限 `96,636,764,160` 字节。

## 错误记录

- 首次远端形状核验尝试以 `mmap_mode` 打开对象数组，NumPy 拒绝对象类型内存映射；已缩小为数值缓存核验，不影响数据或实验。
