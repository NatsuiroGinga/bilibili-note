# LSPR23 字段基数收据实施计划

**目标：** 为 TabM32 的输入适配裁决产出仅使用 LSPR23 Protocol A 训练区的七个字段汇总基数收据。

**范围：** 新增独立诊断工具、配置、远程启动器及实施报告；不读取 `y23`、任何 LSPR24 数组或逐流/逐实体明细。

## 文件边界

- 新增：`thesis/experiments/llm_probe/tools/ch3_lspr23_field_cardinality_receipt.py`
- 新增：`thesis/experiments/llm_probe/configs/ch3-lspr23-field-cardinality-receipt-v1.json`
- 新增：`thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_lspr23_field_cardinality_receipt_v1.sh`
- 新增：本目录的计划、笔记和实施报告。

## 执行步骤

- [x] 读取 Protocol A 既有实现，锁定 `seed=42`、实体验证比例 `0.1` 与时间尾部比例 `0.15` 的逐字切分语义。
- [x] 冻结仅可读取的五个数组 `X23/I23/M23/E23/T23` 与七个 Dijk 字段的固定顺序。
- [x] 实现内存映射、训练有效流去重掩码、逐字段分块精确频数统计、原子状态和最终收据。
- [x] 编写 CPU/GPU0 固定、资源采样、心跳日志、幂等跳过和原子状态的远程启动器。
- [x] 执行 `py_compile` 与 `bash -n`；导入、`--help`、配置核验已尝试，但工作树 `llm_probe/.venv` 缺少 `numpy`，按规则不在实现阶段自行同步依赖。

## 内存与隐私边界

- `X23` 以 `mmap_mode="r"` 打开；每次只取一个字段且默认块大小为 `131072` 行，不复制完整多字段矩阵。
- 训练有效流仅保留长度为 `X23.shape[0]` 的布尔掩码；字段频数按块内 `np.unique` 合并，最终只保留值到计数的聚合字典。
- 输出不包含流、实体、索引、标签或 LSPR24 数据；仅输出指定七个字段前二十值及计数、汇总覆盖率和哈希。
