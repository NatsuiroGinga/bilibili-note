# 共享 B0 HGB/XGBoost 独立代码审查

## 审查结论

**结论为“正式验收前需要修改”。**未发现会使分类标签、宏平均 F1、误报率或预测文件失真的严重问题；数据哈希、样本顺序、训练与验证隔离、标签排除和模型随机种子路径均成立。因此，当前实现可以继续运行标记为 `review_pending` 的性能探索。

发现 3 项重要问题。它们不会改变本轮预测指标，但会使逐模型内存成本和正式运行制品不满足论文证据要求。修复并完成最小回归前，不得把相关成本字段或运行完整性写成正式结论。

## 重要问题

### 1. 逐模型内存峰值实际是同一进程的累计峰值

- 位置：`thesis/experiments/llm_probe/src/flow_probe/tabular_baselines.py:606`
- 位置：`thesis/experiments/llm_probe/src/flow_probe/tabular_baselines.py:679`
- 位置：`thesis/experiments/llm_probe/src/flow_probe/tabular_baselines.py:683`
- 位置：`thesis/experiments/llm_probe/src/flow_probe/tabular_baselines.py:496`

统一执行器先运行 HGB，再在同一 Python 进程中运行 XGBoost。`resource.getrusage(...).ru_maxrss` 是进程生命周期内不可重置的高水位，第二个模型记录的数值至少包含第一个模型和共享数据装载产生的历史峰值。即使删除前一个模型并执行垃圾回收，Python 分配器和原生库也可能保留内存，因此该字段不能解释为 XGBoost 的独立峰值，也不能用于两个模型的内存效率排序。

**影响：**宏平均 F1、误报率、拟合时间和推理时间仍可使用；`peak_process_rss_bytes_after_model` 不能作为逐模型内存证据。

**最小修复建议：**保留统一父入口负责冻结数据哈希、种子、模型清单和结果汇总，但每个模型必须由全新的独立子进程运行。每个子进程只装载同一份冻结输入、训练一个模型并报告自身 `ru_maxrss`；父入口核对两份结果中的输入哈希、样本顺序哈希、种子和评价协议完全一致后再合并摘要。这样得到的是包含公共数据装载成本的单模型端到端峰值，适合公平比较。不要改用同一进程内的垃圾回收、`tracemalloc` 或简单的前后常驻内存差值：这些方法不能覆盖 NumPy、scikit-learn 和 XGBoost 的全部原生内存，也不能重置历史高水位。

### 2. 启动证据位于运行目录之外，且未登记到制品清单

- 位置：`thesis/experiments/llm_probe/scripts/run_shared_b0_tabular_baselines.sh:12`
- 位置：`thesis/experiments/llm_probe/scripts/run_shared_b0_tabular_baselines.sh:15`
- 位置：`thesis/experiments/llm_probe/scripts/run_shared_b0_tabular_baselines.sh:76`
- 位置：`thesis/experiments/llm_probe/src/flow_probe/shared_b0_tabular_baselines.py:619`

启动日志、启动状态、退出码、代码与输入绑定、服务器能力清单均写为运行目录的同级文件，例如 `${output_dir}.launcher.log`。Python 入口传给 `artifact_manifest.json` 的 `data_files` 不包含这些同级文件。归档或同步唯一运行目录后，将无法仅凭该目录证明实际启动代码、输入清单、服务器能力和包装器退出状态。

**影响：**模型预测本身不受影响，但本轮结果不能声明为制品完整的正式运行。

**最小修复建议：**在同一文件系统建立唯一启动暂存目录，先写入启动日志、代码绑定、能力清单和原子状态；Python 成功创建正式输出目录后，将这些文件移动到正式输出目录内，并在最终 `artifact_manifest.json` 中登记路径、大小和 SHA-256。若不增加暂存层，则由 Python 正式入口直接记录代码哈希、能力和启动状态，包装器只保留一个外部引导日志，并在结束时把它移入运行目录。两种方案都必须保证归档一个目录即可获得完整证据。

### 3. 可失败的预检发生在首个状态与退出码之前

- 位置：`thesis/experiments/llm_probe/scripts/run_shared_b0_tabular_baselines.sh:67`
- 位置：`thesis/experiments/llm_probe/scripts/run_shared_b0_tabular_baselines.sh:76`
- 位置：`thesis/experiments/llm_probe/scripts/run_shared_b0_tabular_baselines.sh:100`
- 位置：`thesis/experiments/llm_probe/scripts/run_shared_b0_tabular_baselines.sh:102`

脚本在 `write_state running` 之前执行代码哈希、工具版本、系统信息和磁盘探测。启用 `set -e` 后，任一步骤失败都会直接退出；此时既没有 `failed` 状态，也没有退出码文件，启动日志还可能为空。服务器重启或工具异常后，无法区分“从未启动”“预检失败”和“状态文件丢失”。

**影响：**正常计算路径的 `PIPESTATUS` 处理正确，但预检失败路径不具备可恢复、可审计状态。

**最小修复建议：**创建暂存目录后立即原子写入 `prepared` 状态，并安装统一的 `EXIT` 陷阱。陷阱在退出码非零且尚未完成时写入原始退出码和 `failed` 状态；正式计算前再切换为 `running`，成功后切换为 `finished`。增加最小 Shell 行为测试，至少覆盖预检失败、Python 失败、`tee` 失败、双方成功和已有路径拒绝五种情况。

## 已确认正确的路径

- `freeze_manifest.json` 的哈希绑定指向 `checksums.json`，后者逐一绑定训练与两套验证所用的六个 Parquet、`input_binding.json` 和 `statistics.json`。
- 公共特征列严格等于 `sample_id`、`stable_order`、8 个公共数值字段和 8 个缺失掩码；任何额外标签列都会在模型装载前被拒绝。
- 标签视图只读取 `sample_id`、`stable_order` 和 `label`，`text`、`input_text` 与标签均不会进入特征矩阵。
- 每个视图检查样本标识唯一、稳定顺序从 0 连续，并逐行核对特征和标签视图；训练、GeNIS 验证和 TQH-C2 验证还检查样本标识集合互斥。
- HGB 与 XGBoost 使用相同的冻结训练矩阵、平衡样本权重、随机种子和评价函数。XGBoost 固定使用 CPU 直方图算法、单线程、全量行采样和全量列采样。
- 分类指标、混淆矩阵、逐类指标、良性误报率、预测概率和逐样本预测均按冻结样本顺序输出。
- Shell 对 `Python | tee` 的两个退出状态分别取值，正常计算路径不会被 `tee` 的成功状态掩盖。

## 真实制品核对

2026-07-30 只读核对服务器上的共享 B0 发布清单，结果如下：

- `schema_version=flow_probe_shared_b0_view_v1`
- `stage=theory_selection`
- `status=review_pending`
- 训练候选样本数为 10,000
- GeNIS 验证样本数为 10,399
- TQH-C2 验证样本数为 4,000
- 两套验证的 `sample_overlap_count` 和 `group_overlap_count` 均为 0
- 发布清单声明 `atomic_publication=true`

这些事实与新装载入口的固定合同一致。主代理提供的服务器目标测试结果为 `7 passed`；本审查未重复运行正式实验。

## 非阻塞加固建议

- 当前装载器已经直接重算样本集合交集，但只检查 `statistics.json` 的数量。建议同时要求其中的 `sample_overlap_count=0`、`group_overlap_count=0`，并核对其稳定顺序哈希，使上游分组隔离声明在训练入口再次失败关闭。
- `swanlab_run` 的既有实现会在调用 `swanlab.finish()` 前先把状态设为 `finished`。若云端结束调用抛出异常，本地制品清单可能写成 `finished`，而包装器状态是 `failed`。本轮必须以包装器退出状态和云端 `run info`、`run summary` 的组合验收；后续应在跟踪模块的独立任务中修复该既有风险。

## 最终裁决

- 严重问题：0 项。
- 重要问题：3 项。
- 当前允许：运行 `review_pending` 的 HGB/XGBoost 性能探索，使用分类指标和预测文件。
- 当前禁止：把逐模型峰值内存、制品完整性或本轮运行状态写成正式论文结论。
- 正式验收条件：完成上述三项最小修复，运行直接受影响的服务器最小测试和 Shell 行为测试，并重新进行独立审查。
