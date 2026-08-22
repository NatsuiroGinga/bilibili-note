# N14 独立审查修复计划

## 任务边界

- 基线实现：`812e67f`。
- 冻结规范：`345c7b4`。
- 共享 Raw83 最终接口：`ebea0f4`、`180c405`。
- 唯一实现代理：`n14_tabular_resnet_fix_impl_sol_high`，模型 `gpt-5.6-sol`，`effort=high`。
- 只修改 N14 工具、配置、远程启动器、既有实施报告和本目录文档。
- 不修改 Raw83、精度、SwanLab、其他模型或活动运行根；不访问服务器，不训练，不创建或运行测试。

## 实施步骤

| 优先级 | 动作 | 验收条件 | 状态 |
| --- | --- | --- | --- |
| P0 | 将输入发现统一迁移到 Raw83 `dataset-manifest.json` 与 `open_protocol_a_dataset` 的 `train`、`validate`、`target-evaluate` 用途接口 | 工具、配置、启动器对旧缓存和旧字段基数收据零命中；源阶段不打开目标清单 | 已完成 |
| P0 | 固定 A/B C00 输入选择、封印输入后的两个 AdamW 候选、再完成 C00/C01/C10/C11 | 无旧混合身份和三折路径；所有阶段身份绑定清单、输入臂、优化器、代码与配置哈希 | 已完成 |
| P0 | 修正训练权重和原子恢复 | 逐流与块正类权重仅来自 Raw83 `training_weight_aggregate`；每 20 个完整 `optimizer.step()` 保存模型、AdamW、epoch、step、最佳、采样器、全部随机状态、精度、微批和恢复计数 | 已完成 |
| P0 | 完成源年指标与资格封印 | 四格全部封印后才写外部源资格封印；源年输出逐流 AP、实体 AP、最大实体 AP、完整整数 FP 终端曲线、1 基首次告警曲线、六档实际 FPR 和资源；不持久化分数、标签或成员 | 已完成 |
| P0 | 阻断当前目标评价 | 当前配置保持目标阻塞；只有外部主进程注入胜出 Raw 臂的目标清单、标签阶段令牌与资格封印后才允许评价 | 已完成 |
| P1 | 对齐 BF16、SwanLab、参数与清单合同 | 使用统一精度运行时；显式登记 LayerNorm 偏离；`387074` 三方核对；SwanLab 两次上限状态机；末写清单并复核全部内容 SHA-256；无墙钟上限 | 已完成 |
| P1 | 更新实施报告并完成静态验收 | 一次完成 `py_compile`、导入、`--help`、`--validate-config`、JSON、`bash -n`、依赖闭包、旧路径零命中和差异检查 | 已完成；本机缺第三方包，仅静态核对依赖声明 |

## 验收命令

验证统一在 `thesis/experiments/llm_probe` 下加载 `tools/env/activate.sh`，并设置 `UV_CACHE_DIR=/tmp/uv-cache` 与 `PYTHONPYCACHEPREFIX=/tmp/codex-pycache`。禁止 `black`、测试、服务器和训练。

## 阻塞条件

- 目标文件出现他人并发修改。
- 共享 Raw83 接口不足以表达冻结合同且必须修改共享文件。
- 目标评价缺少外部源资格封印或后续注入的胜出臂年度清单。
