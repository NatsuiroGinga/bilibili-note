# TQH-C2 A/B/C 统一候选独立审查

## 裁决

**不允许启动真实双物化，也不允许向正式目录发布。**

当前发现 **1 个严重问题、3 个重要问题**。其中划分器会生成不满足已批准硬覆盖条件的清单，但套件审计仍将其记为 `pass`。即使两次物化逐字节一致，这也只会稳定复现错误划分，不能满足任务 6。

解除阻塞前必须完成最小修复、服务器目标回归和新的独立复审。当前代码只能视为静态检查通过的实现草案。

## 审查范围

- 生产代码：`thesis/experiments/llm_probe/src/flow_probe/tqh_c2_candidate_abc.py`
- 测试代码：`thesis/experiments/llm_probe/tests/test_tqh_c2_candidate_abc.py`
- 对照实现：`thesis/experiments/llm_probe/src/flow_probe/tqh_c2_candidate.py`
- 批准设计：`.Codex/docs/sdd/task-tqh-dataset-download-manager/2026-07-28-tqh-b-exception-and-abc-design.md`
- 实施计划：`.Codex/docs/sdd/task-tqh-dataset-download-manager/2026-07-28-tqh-b-exception-and-abc-implementation-plan.md` 任务 4、5、6
- 上位合同：`.Codex/docs/2026-07-24-统一数据冻结与PINN候选顺序实验合同.md`
- 实验规则：`thesis/AGENTS.md`、`thesis/experiments/llm_probe/AGENTS.md`、`.Codex/docs/AGENTS.md`

本次未修改生产代码、测试或既有 C-only 实现，只新增本审查报告。

## 严重问题

### 1. 划分器没有实施硬覆盖与样本比例目标，审计却无条件通过

**位置**：

- `tqh_c2_candidate_abc.py:203-262`
- `tqh_c2_candidate_abc.py:601-665`
- `test_tqh_c2_candidate_abc.py:168-230`

**合同**：批准设计第 75 至 78 行要求：

- 域内验证和测试各自同时覆盖 A/B/C 与 `30/300/1800/3600` 四个 interval；
- 三个留一套件的验证集各自覆盖两个源 profile 与四个 interval；
- 满足硬覆盖后，再确定性最小化样本比例相对 `80/10/10` 的偏差。

**现状**：`_build_suite_groups` 只按 SHA-256 对每个 profile 的 cell 排序，然后取前若干个 cell。它不搜索满足覆盖约束的组合，也不计算样本比例目标。`_suite_audits` 只检查样本覆盖、样本身份、二元标签和三个清单哈希数量，不检查 profile、interval、jitter 或样本比例，因此会把不合格划分写为 `pass`。

按测试夹具中实际使用的 `4 interval × 3 jitter × 3 profile` 网格复算当前算法，结果为：

| 套件 | 验证 interval 覆盖 | 测试 interval 覆盖 | 合同结果 |
| --- | --- | --- | --- |
| `tqhc2_cell_indomain` | `300/1800/3600` | `30/300` | 失败 |
| `tqhc2_leave_a_out` | `1800/3600` | 四个 interval | 失败 |
| `tqhc2_leave_b_out` | `30/1800` | 四个 interval | 失败 |
| `tqhc2_leave_c_out` | `300/3600` | 四个 interval | 失败 |

测试只断言 `28/4/4` 与 `20/4/12` 数量，没有断言硬覆盖或样本比例。因此现有测试成功不能证明划分协议有效。

**影响**：验证和测试不能按预注册加密条件覆盖执行，验证选择可能偏向少数 interval。基于这些清单得到的模型选择和测试结果无效。

**必须修复**：

1. 对域内和三个留一套件分别做确定性受约束组合选择。
2. 先满足 profile、interval、cell 数量、标签覆盖和组隔离，再以样本比例偏差及 jitter 覆盖作为确定性目标和平局裁决。
3. 审计必须记录每个 split 的 profile、interval、jitter、cell 数、样本数、样本比例和目标偏差；任一硬约束不满足时立即失败。
4. 测试必须用独立的字面量合同断言上述覆盖，不能只从生产常量导入期望值。

## 重要问题

### 2. 输入身份和来源哈希未验证，错误历史制品或已变更制品可被接纳

**位置**：

- `tqh_c2_candidate_abc.py:67-155`
- `tqh_c2_candidate_abc.py:158-200`
- `tqh_c2_candidate_abc.py:508-547`
- `test_tqh_c2_candidate_abc.py:120-150`

**现状**：

- 运行清单只检查 `dataset_id`、`dataset_version`、`profile`、`cell_count` 和 `status`。
- 未把运行清单中的 `master_record_count`、`packet_record_count`、`extractor_contract_sha256` 与实际输入交叉核对。
- 未要求并回读 `artifact_checksums.provisional.json` 中登记文件的路径、大小和 SHA-256。
- `_source_artifacts` 只在接纳输入后计算当前字节的哈希。若输入已被改动，新哈希仍会被当成合法来源，无法证明它仍是上游验收通过的字节。
- 只检查每个 profile 有 12 个 `capture_group_id`，未验证每个 profile 恰好包含 `30/300/1800/3600 × 0/30/70` 的 12 个唯一 cell。
- 固定设计指定 C 输入为 `tqh-c2-C-20260724-v8`，但本地历史 C v2 至 v7 同样声明 `1.0.1/provisional`，当前入口没有哈希绑定即可接纳这些旧制品。

测试夹具把 `artifact_checksums.provisional.json`、来源清单和上游审计写成空对象，仍期待物化成功，因此该缺口被测试固化为允许行为。

**影响**：错误版本、旧提取器输出、缺失 cell 网格或验收后被修改的主表和包表可以进入统一候选。候选自身哈希仍会自洽，但无法证明来自批准的 A/B/C 输入，破坏来源追踪与双物化有效性。

**必须修复**：

1. 要求三份上游制品的运行清单、制品校验清单和必要审计全部存在且结构有效。
2. 逐项回读上游制品路径、大小和 SHA-256，并核对主记录数、包记录数与提取器合同哈希。
3. 以任务 6 的冻结运行配置显式绑定三份已批准输入清单或主制品哈希，不依靠路径字符串猜测版本。
4. 验证每个 profile 的完整 4×3 cell 网格，并增加缺 cell、重复 cell、哈希不符、清单计数不符和提取器不一致的负向测试。

### 3. 留一套件标识不符合已批准的公开合同

**位置**：

- `tqh_c2_candidate_abc.py:43-59`
- `tqh_c2_candidate_abc.py:213-238`
- `test_tqh_c2_candidate_abc.py:18-29`

**合同**：批准设计第 76 至 78 行使用：

- `tqhc2_leave_one_profile_out_A`
- `tqhc2_leave_one_profile_out_B`
- `tqhc2_leave_one_profile_out_C`

**现状**：实现改为 `tqhc2_leave_a_out`、`tqhc2_leave_b_out`、`tqhc2_leave_c_out`，相应清单文件名也随之改变。测试直接导入生产端 `SUITE_IDS` 和 `SPLIT_FILENAMES`，因此不能发现合同漂移。

**影响**：任务 6、后续预算生成器和实验配置按批准标识查找 12 份清单时会失败，或者形成两套语义相同但键不同的协议。

**必须修复**：恢复批准标识和清单文件名，并在测试中使用独立字面量集合断言 4 个 suite 和 12 个文件名。

### 4. 未实现 cell 顺序回退拒绝，流式审计会遗漏合同规定的失败条件

**位置**：

- `tqh_c2_candidate_abc.py:336-441`
- `tqh_c2_candidate_abc.py:767-775`
- `test_tqh_c2_candidate_abc.py:246-255`

**合同**：批准设计第 84 行要求 row group 单 cell、同一 cell 的 row group 相邻，并在 cell 顺序回退时立即失败。

**现状**：实现维护 `closed_samples`，能拒绝同一 `sample_id` 在包表中非连续重现；但没有维护已关闭 cell。若顺序为 `cell-A → cell-B → cell-A`，只要第二次 A 包含新的连续样本，当前代码会接纳。`streaming-audit.json` 仍固定写入 `status=pass`。现有负向测试只覆盖单个 row group 混入多个 cell，没有覆盖 cell 回退或样本跨相邻 row group。

**影响**：不符合上游行组布局合同的输入会被静默接纳，审计无法证明按批准的相邻 cell 策略处理，也削弱对输入被重排或错误重写的检测。

**必须修复**：维护当前 cell 与已关闭 cell 集合，cell 离开后再次出现即失败；增加 cell 回退、样本跨相邻 row group 成功、样本非连续重现失败和失败后 `_INCOMPLETE` 保留测试。

## 已通过项

1. **Parquet 包表没有全量载入**：生产代码通过 `pyarrow.parquet.ParquetFile.read_row_group` 逐 row group 读取，只保留当前 row group、当前待完成样本和全体样本级 37 字段结果。它确实避免一次载入三个 profile 的全部包观测。
2. **37 字段与序列哈希语义复用**：直接复用旧 C-only 的 `_aggregate_features`、`MODEL_FEATURE_FIELDS` 与相同字段顺序的序列哈希逻辑。
3. **标签排除正确**：只有 `label_status=mapped` 进入候选，`unknown`、`malicious_recon`、`malicious_lateral` 被排除；固定标签映射逐行检查。
4. **全局样本主键检查存在**：每个 profile 内与 A/B/C 合并后均检查 `sample_id` 唯一；`allocation_group_id` 也检查全局唯一。
5. **12 份清单绑定同一主表哈希**：每行写入同一个 `samples.parquet` SHA-256，协议登记 12 份清单，固定夹具可由 `FrozenProtocol` 加载并回读制品哈希。
6. **模型字段未见泄漏**：模型视图只暴露既有 37 个数值聚合字段；profile、interval、jitter、capture 和标签均不在模型字段列表内，字段角色沿用旧 C-only 合同。
7. **临时目录失败标记基本正确**：已存在目录拒绝覆盖；新目录先写 `_INCOMPLETE`，异常不会执行末尾删除，成功后才删除标记。
8. **旧 C-only 行为未被修改**：工作树中 `tqh_c2_candidate.py` 没有本任务差异，新模块只读取其现有常量和辅助函数。

## 流式内存边界

实现没有保存全体包行，但仍有两个需要在真实运行中监控的峰值：

- 当前 row group 会整体转为 Pandas，并同时建立该 row group 的样本分段列表；峰值至少约为一个最大 row group 的多份内存表示。
- 每个映射样本的单行 DataFrame 被保存在 `feature_rows`，直到全部 profile 扫描结束后才统一 `concat`。A 已有 `181,556` 个映射样本，A/B/C 合并后会产生数十万个小 DataFrame，Python 对象开销可能显著。

这两点不等同于全包载入，因此不单独阻塞正确性修复后的临时冒烟；真实双物化必须记录峰值常驻内存和总时长。若资源异常，应把样本级结果改成分批表或行记录，而不是退化为全包读取。

## 原子失败与正式发布边界

当前入口只实现“目录内 `_INCOMPLETE` 标记”，没有实现任务 6 的双份比较、全部哈希回读和正式目录原子重命名。因此：

- 修复后首次真实运行也只能指向两个计划中的全新临时目录；
- 禁止直接把正式目标目录传给 `--output-dir`；
- 只有外部验收完成逐字节比较、12 清单加载、全部哈希回读和正式目标不存在检查后，才可在同一文件系统中原子重命名一份完整临时父目录；
- 复制后删除、覆盖已有目录或仅删除 `_INCOMPLETE` 都不算原子发布。

## 测试与静态检查

本机按实验规则未运行 `pytest`。实现报告也明确服务器行为测试尚未执行。

已执行：

```text
UV_CACHE_DIR=/tmp/uv-cache uv run --no-sync black --check src/flow_probe/tqh_c2_candidate_abc.py tests/test_tqh_c2_candidate_abc.py
结果：通过，两份文件无需修改。

UV_CACHE_DIR=/tmp/uv-cache uv run --no-sync ruff check src/flow_probe/tqh_c2_candidate_abc.py tests/test_tqh_c2_candidate_abc.py
结果：通过。

UV_CACHE_DIR=/tmp/uv-cache uv run --no-sync python -m py_compile src/flow_probe/tqh_c2_candidate_abc.py tests/test_tqh_c2_candidate_abc.py
结果：通过。

git diff --check -- src/flow_probe/tqh_c2_candidate_abc.py tests/test_tqh_c2_candidate_abc.py
结果：通过。
```

## 解除阻塞门禁

1. 修复上述严重和重要问题，并增加直接覆盖原问题的回归测试。
2. 在服务器运行计划中的三个测试文件、Black 与 Ruff，全部退出码为 0。
3. 由新的独立审查代理确认严重问题 0、重要问题 0。
4. 才允许在两个全新临时目录执行真实双物化；失败目录保留 `_INCOMPLETE`，不得复用。
5. 两份非自引用制品逐字节一致，`FrozenProtocol` 加载 12 份批准命名的清单，覆盖审计和全部 SHA-256 回读通过后，才允许原子发布。

