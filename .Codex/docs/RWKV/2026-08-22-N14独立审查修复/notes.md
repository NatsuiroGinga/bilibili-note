# N14 独立审查修复证据笔记

## 已核事实

- `812e67f` 已在当前 `HEAD` 祖先中，四个授权目标文件当前工作树干净。
- 旧实现直接声明并加载 `X23/X24`，读取字段基数收据，并在目标阶段自行从源/目标数组重建实体；这些路径违反 `345c7b4` 的 Raw83 数据门。
- `ebea0f4` 提供 `open_protocol_a_dataset`：源年以 `purpose=train/validate` 和显式 `arm=A/B` 读取；目标年只接受 `purpose=target-evaluate` 且必须先通过外部源资格封印。
- `180c405` 后的源清单封印 A/B 视图、切分、训练权重聚合、变换状态和全部制品哈希；训练权重接口为 `training_weight_aggregate()`。
- Raw83 资格封印要求 `source_input_arm_sha256`、配方、容量、检查点、机制、评价代码六个 SHA-256，且 `target_feature_rows_read=0`、`target_label_rows_read=0`。
- 当前目标年度配置状态为 `blocked-until-source-arm-seal`，`winning_arm` 与资格绑定字段均为空；N14 当前不得执行目标评价。

## 技能与仓库规则裁决

- 已读取 `writing-plans`、`subagent-driven-development`、`daily-coding`、`pytorch-patterns` 和 `expression-skill`。
- 仓库禁止实验工程测试和 `black`，覆盖 `writing-plans` 的通用测试驱动建议；本任务只执行冻结静态验收。
- 主代理已把当前代理分派为唯一实现者，因此不再派生实现代理；这保留了 `subagent-driven-development` 的单实现者所有权，避免同范围并发修改。

## 待核接口

- SwanLab 继续复用仓库中经 `89ddecf`、`d6313ca`、`70a8a2b` 验证的同构调用，不新增第三方接口。
- PyTorch 继续复用现有 `neural_precision_runtime.py`、AdamW、`torch.save/load` 和 RNG 状态接口；不新增未核验 API。

## 静态验收结果

- `py_compile`：通过。
- 模块导入：通过，模式版本、参数量和四格顺序正确。
- `--help`、`--validate-config`、JSON 解析、`bash -n`：通过。
- 禁用旧路径、旧混合身份和三折路径：四个授权文件零命中。
- 依赖闭包：项目清单声明 `scikit-learn`、`torch`、`swanlab`，`numpy` 由科学计算依赖闭包提供；本地锁定环境未安装 `numpy`，故真实第三方导入未完成，启动器仍在服务器运行前机械执行完整导入门。
- 未运行测试、训练、服务器或 `black`。
