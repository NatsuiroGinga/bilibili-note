# TQH-C2 A/B/C 统一候选唯一修复轮独立复审

## 裁决

**允许启动真实双物化，但只允许写入两个全新的临时目录；当前仍不允许向正式候选目录发布。**

本轮复审结果为：

- 严重问题：`0`；
- 重要问题：`0`；
- 建议：`2`。

首次审查提出的 1 个严重问题和 3 个重要问题均已消除。服务器目标回归和静态门禁已有通过证据，真实 A/B/C 包表的行组布局也满足当前流式读取合同。因此可以进入任务 6 的双份真实物化、逐字节比较和哈希回读阶段。

该裁决不等于正式发布许可。只有两份临时制品的全部非自引用文件逐字节一致、12 份清单可加载、全部登记哈希回读通过、覆盖审计通过且正式目标不存在时，才允许由主代理另行执行同文件系统原子发布。

## 审查范围

- 生产代码：`thesis/experiments/llm_probe/src/flow_probe/tqh_c2_candidate_abc.py`
- 测试代码：`thesis/experiments/llm_probe/tests/test_tqh_c2_candidate_abc.py`
- 必要对照：`thesis/experiments/llm_probe/src/flow_probe/tqh_c2_candidate.py`
- 批准设计：`.Codex/docs/sdd/task-tqh-dataset-download-manager/2026-07-28-tqh-b-exception-and-abc-design.md`
- 实施计划：`.Codex/docs/sdd/task-tqh-dataset-download-manager/2026-07-28-tqh-b-exception-and-abc-implementation-plan.md`
- 首次审查：`.Codex/docs/sdd/task-tqh-dataset-download-manager/abc-candidate-review.md`
- 实现报告：`.Codex/docs/sdd/task-tqh-dataset-download-manager/abc-candidate-implementation-report.md`

本次没有修改生产代码、测试或既有 C-only 实现，只新增本复审报告；按实验规则没有在本机运行 `pytest`。

## 原阻塞问题复核

### 1. 硬覆盖划分与样本比例目标：已解决

**代码证据**：

- `tqh_c2_candidate_abc.py:392-417` 从四个 interval 各选择一个完整 cell，并要求候选精确覆盖指定 profile 集合。
- `tqh_c2_candidate_abc.py:429-491` 对域内验证和测试的互斥硬覆盖组合进行确定性选择，先最小化样本比例偏差，再扩大 jitter 覆盖。
- `tqh_c2_candidate_abc.py:494-545` 对三个留一 profile 套件固定完整测试域，并在源域中选择覆盖两个 profile 和四个 interval 的验证集。
- `tqh_c2_candidate_abc.py:939-1054` 独立记录并复核每个划分的 profile、interval、jitter、cell 数、样本数、样本比例和目标偏差；任一硬条件失败会终止物化。
- `test_tqh_c2_candidate_abc.py:275-355` 使用独立字面量合同检查域内与留一套件覆盖，不再只断言 cell 数量。

**裁决**：首次审查中的严重问题已消除。当前划分器不会把缺少 profile 或 interval 覆盖的清单记为通过。

### 2. 批准输入身份、哈希、计数、提取器和 4×3 网格绑定：已解决

**代码证据**：

- `tqh_c2_candidate_abc.py:46-50` 固定 A、B、C 三份批准输入标识。
- `tqh_c2_candidate_abc.py:115-240` 要求批准配置字段完整，回读上游制品清单本身的 SHA-256，并逐项复核固定 8 个制品的相对路径、大小和 SHA-256。
- `tqh_c2_candidate_abc.py:196-218` 绑定数据集版本、profile、12 个 cell、暂定状态、提取器哈希、主记录数和包记录数。
- `tqh_c2_candidate_abc.py:261-333` 再以实际 Parquet 内容复核主记录行数、包表元数据行数、提取器哈希、标签合同和 A/B/C 全局样本身份。
- `tqh_c2_candidate_abc.py:336-389` 要求每个 profile 精确包含 `30/300/1800/3600 × 0/30/70` 的 12 个唯一 cell。
- `test_tqh_c2_candidate_abc.py:371-416` 覆盖未登记制品变化、清单计数漂移、提取器不一致和 4×3 网格缺失。

**裁决**：首次审查中的输入来源重要问题已消除。双物化启动时必须把同一份批准输入配置视为冻结运行输入，记录该配置的 SHA-256，禁止现场按当前文件重新生成批准值。

### 3. 批准 suite 键：已解决

**代码证据**：

- `tqh_c2_candidate_abc.py:52-68` 使用批准的四个 suite 键并由它们生成 12 个清单文件名。
- `test_tqh_c2_candidate_abc.py:35-51` 以独立字面量集合固定四个 suite 键和 12 个文件名，不从生产常量导入预期合同。

**裁决**：首次审查中的公开合同漂移已消除。

### 4. cell 顺序回退拒绝：已解决

**代码证据**：

- `tqh_c2_candidate_abc.py:680-779` 分 profile 维护当前 cell、已关闭 cell、当前样本和已关闭样本；离开后的 cell 再出现、样本非连续重现、行组混入多个 cell 或包序号不连续均会终止。
- `test_tqh_c2_candidate_abc.py:432-475` 分别覆盖 cell 回退拒绝、样本跨相邻行组成功和样本关闭后非连续重现失败，并检查失败目录保留 `_INCOMPLETE`。

**裁决**：首次审查中的流式顺序重要问题已消除。

## 其他正确性复核

### 数据泄漏与划分身份

- 每套 suite 对 36 个完整 cell 只分配一次，训练、验证和测试通过 cell 清单表达，样本不会在同一 suite 内跨划分。
- 测试域不参与模型拟合；划分选择只使用 cell 元数据和样本数量，不使用模型结果或包级模型字段。
- 模型视图继续只暴露既有 37 个数值字段。profile、interval、jitter、capture、suite、split 和标签均属于清单或审计元数据，不进入该模型视图。
- 重复观测签名只记录，不据此拆分、移动或删除完整 cell，符合批准设计。

### 全局样本标识符与标签

- 每个 profile 内和 A/B/C 合并后均检查 `sample_id` 非空且全局唯一；`allocation_group_id` 也要求全局唯一。
- 只有固定标签合同中 `label_status=mapped` 的良性与恶意 C2 样本进入候选；未知、侦察和横向移动标签不进入二分类候选。
- 12 份清单均绑定同一个 `samples.parquet` SHA-256。

### 流式行组与真实输入兼容性

本机只读核对了三份已验收上游包表的 Parquet 行组归属，没有运行候选物化或测试：

| profile | 行组数 | 混入多个 cell | cell 顺序回退 |
| --- | ---: | ---: | ---: |
| A | 246 | 0 | 0 |
| B | 157 | 0 | 0 |
| C | 12 | 0 | 0 |

因此真实上游当前满足“单行组单 cell、同一 cell 行组连续”的前置合同，不会因既有 Parquet 布局在入口处必然失败。

### 可重复性

- 分组排序、候选枚举、比例比较和 SHA-256 平局裁决均为确定性过程。
- 测试已覆盖两个新目录的逐字节复现与拒绝覆盖。
- 成功路径最后才移除 `_INCOMPLETE`；异常路径保留失败证据。

## 服务器验证证据

服务器验证目录：

`/root/autodl-tmp/thesis/experiments/llm_probe/runs/validation/20260728-tqh-abc-candidate-fix1/`

截至本次复审，主代理提供并核对的证据为：

- 硬件档位切换前的原回归日志已有前 13 个通过点；未以缺少最终摘要为由重复这些节点。
- 续跑分片 `rest-a` 为 `4 passed`，`rest-b` 为 `9 passed`，覆盖剩余 13 个节点。
- 格式化后的核心硬覆盖节点为 `1 passed in 77.12s`。
- Black 退出码为 `0`，Ruff 退出码为 `0`，`py_compile` 退出码为 `0`。
- 当前生产源码 SHA-256 为 `84f2709d01d38c73c00d69df2f0c76d8cdb7208bc993ce461df1f51c3c0ad74e`，与复审文件一致。

这些分片证据满足重启恢复规则下的目标回归门禁；本复审不把硬件档位切换造成的前台中断误判为测试失败。

## 建议

### 1. 记录双物化的时间和峰值常驻内存

当前域内硬覆盖选择需要穷举候选对，单个核心夹具耗时约 77 秒；真实包聚合还会为每个映射样本暂存一个单行 DataFrame。它们不构成当前正确性阻塞，但双物化必须分别记录总时长、峰值常驻内存和失败阶段，禁止并行运行两份物化放大内存峰值。

### 2. 严格执行既定终点

如果任一真实物化因通用划分器、内存上界或真实输入合同失败，不再进行第二轮通用修复，也不扫描新的划分策略。应保留带 `_INCOMPLETE` 的失败目录，停止通用划分器，切换到预注册、人工核验且固定哈希的 36-cell 分配清单。

## 双物化执行边界

允许主代理执行以下动作：

1. 冻结同一份批准输入配置及其 SHA-256。
2. 串行物化到两个全新临时目录，禁止直接指向正式候选路径。
3. 比较全部非自引用制品，加载 12 份批准命名的清单，回读全部登记哈希，并核对四套覆盖审计。
4. 任一失败时保留证据并按固定终点切换预注册 36-cell 清单。

在上述验收全部通过前，候选继续保持 `provisional/theory_selection/review_pending`，不得启动基于该候选的正式训练、形成最终测试结论或写入论文性能主表。
