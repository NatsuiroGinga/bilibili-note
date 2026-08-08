# TQH-C2 A/B/C 固定清单物化实施计划

> **供实现代理使用：** 必须采用 `superpowers:subagent-driven-development` 执行；实现代理可针对本任务使用一次 `superpowers:test-driven-development`，不得把测试驱动流程重复用于同一任务。

**目标：** 在不继续修补通用 A/B/C 划分器的前提下，先冻结每个采集单元最多 1,000 条的实际使用样本，再使用预注册的 36-cell 分配和兼容真实交错包顺序的过滤聚合器，生成可双份复现的 TQH-C2 A/B/C 预算候选协议。

**架构：** 新建独立的预算物化模块。首次只在 36-cell 主记录统计上运行一次组合搜索并冻结分配清单，后续物化不再搜索；再按 cell 与二分类标签进行确定性比例抽样，冻结最多 36,000 条的样本清单。包表仍按 Parquet 行组顺序扫描，但只保留目标 `sample_id`；每个 profile 过滤后按 `sample_id, packet_index` 排序，复用既有聚合与序列哈希语义，完成后立即释放中间表，禁止全量载入 2601 万条包记录。

**技术栈：** Python 3.10、Pandas、NumPy、PyArrow、uv、pytest、Black、Ruff。

## 全局约束

- 不修改 `src/flow_probe/tqh_c2_candidate_abc.py` 的通用划分与流式聚合逻辑，不再进行第二轮通用修复。
- 组合搜索只允许在冻结 36-cell 分配清单时运行一次；固定后两次物化、基线和候选方法只能读取该清单，不得重新搜索。
- 固定分配与样本清单只能由 A/B/C 的 36 个完整 cell、输入标签计数、`sample_id` 和预注册覆盖规则生成；不得读取任何模型预测或最终测试结果。
- 每个 cell 的映射样本上限为 1,000；采用自然二分类比例的最大余数配额，配额相同时按标签字典序裁决，类内按 `sha256("tqhc2-abc-budget-v1|" + sample_id)` 与 `sample_id` 排序。少于 1,000 条的 cell 全部保留，且两类均非空。
- 当前批准输入据此得到 35,235 条流和 2,475,729 条包，分别占 303,599 条映射流和 25,541,137 条映射包的 11.61% 与 9.69%；实现必须重算并核对这些计数。
- 域内套件固定为 28/4/4 cell；三个留一 profile 套件固定为 20/4/12 cell；四个套件均要求验证集和测试集覆盖四档 interval，域内验证与测试覆盖 A/B/C 和三档 jitter，留一套件验证集覆盖两个训练 profile 和至少两档 jitter。
- 固定清单文件进入版本控制并绑定 SHA-256；物化器只读使用，发现缺失、额外、重复 cell 或硬覆盖失败时立即拒绝。
- 包聚合必须验证未知 `sample_id`、cell/profile 绑定、cell 顺序回退、包序号重复/缺口/回退、主记录计数不一致、标签字段泄漏和非有限特征。
- `observation_sequence_sha256` 复用现有候选的规范 JSON 行编码语义；同一样本跨行组交错不得改变按 `packet_index` 恢复后的摘要。
- 失败输出保留 `_INCOMPLETE`，不得覆盖或复用；真实双物化只能串行运行，并记录总时长和峰值常驻内存。
- Python 测试仅在服务器运行；本机只允许静态检查和真实数据物化。
- 真实固定路径再次出现输入完整性或结果正确性失败时停止，不增加第三种物化器，不降低门槛。

---

### 任务 1：固定 36-cell 分配、预算样本清单与验证器

**文件：**

- 新建：`thesis/experiments/llm_probe/configs/tqhc2_abc_fixed_assignment_v1.json`
- 新建：`thesis/experiments/llm_probe/src/flow_probe/tqh_c2_candidate_abc_fixed.py`
- 新建：`thesis/experiments/llm_probe/tests/test_tqh_c2_candidate_abc_fixed.py`

**接口：**

- 输入：A/B/C `master_records.parquet` 形成的 36-cell 基表与固定 JSON。
- 输出：`load_fixed_suite_groups(path: Path, base_groups: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, object]]]` 与 `select_budget_samples(master: pd.DataFrame, cap_per_cell: int = 1000) -> tuple[pd.DataFrame, dict[str, object]]`。

- [ ] 在当前已批准 A/B/C 主记录的 cell 统计上调用一次现有受约束组合搜索，生成四个套件的固定 `train/validation/test` 分配；记录生成依据与配置 SHA-256，不保存任何模型结果。
- [ ] 在测试中构造完整 4×3×3 网格，验证四套分配的 cell 数、互斥性、全集覆盖和硬覆盖条件。
- [ ] 增加缺失 cell、额外 cell、重复 cell、错误 profile 留出和覆盖不足的拒绝测试。
- [ ] 实现每 cell 最多 1,000 条的确定性比例抽样；测试自然比例最大余数、并列裁决、少量 cell 全保留、两次字节一致和样本清单哈希绑定。
- [ ] 实现只读加载器和审计输出；运行服务器精确测试并确认全部通过。

### 任务 2：目标样本的交错包过滤与聚合器

**文件：**

- 修改：`thesis/experiments/llm_probe/src/flow_probe/tqh_c2_candidate_abc_fixed.py`
- 修改：`thesis/experiments/llm_probe/tests/test_tqh_c2_candidate_abc_fixed.py`

**接口：**

- 输入：预算主记录、三个 profile 派生目录。
- 输出：`filter_and_aggregate_budget_packets(master: pd.DataFrame, profile_dirs: Mapping[str, Path]) -> tuple[pd.DataFrame, dict[str, str], list[dict[str, object]]]`。

- [ ] 添加同一 `sample_id` 在单个行组内分成多个片段仍可正确聚合的测试；预期特征必须逐字段等于旧 `_aggregate_features` 对按 `packet_index` 排序后样本的结果。
- [ ] 添加同一流跨相邻行组、包序号缺口、重复、回退、未知样本、跨 cell 回退和主记录计数不一致测试。
- [ ] 每个 profile 逐行组读取必要列，使用冻结目标 `sample_id` 集合立即过滤；只拼接该 profile 的目标包，按 `sample_id, packet_index` 稳定排序后验证序号和主记录计数。
- [ ] 复用既有 `_aggregate_features` 与 `_sequence_hashes_for_sample` 语义生成特征与摘要；完成一个 profile 后只保留聚合结果并释放包级中间表，禁止拼接三个 profile 的全量包。
- [ ] 对完整上游包表只做顺序扫描和 cell/profile 审计，不为未入选样本计算特征、分位数或序列哈希；记录扫描行数、保留行数和过滤比例。
- [ ] 在 profile 结束时生成与 `MODEL_FEATURE_FIELDS` 完全一致的有限数值表，最终保留包数必须等于 2,475,729。
- [ ] 运行服务器精确测试；记录测试数、时长和峰值内存。

### 任务 3：固定候选协议输出与命令入口

**文件：**

- 修改：`thesis/experiments/llm_probe/src/flow_probe/tqh_c2_candidate_abc_fixed.py`
- 修改：`thesis/experiments/llm_probe/tests/test_tqh_c2_candidate_abc_fixed.py`
- 修改：`thesis/experiments/llm_probe/pyproject.toml`

**接口：**

- 命令：`flow-probe-materialize-tqh-c2-abc-budget --profile-a-dir PATH --profile-b-dir PATH --profile-c-dir PATH --approved-inputs PATH --assignment PATH --cap-per-cell 1000 --output-dir PATH`。
- 输出：与 `FrozenProtocol` 兼容的 `samples.parquet`、`groups.parquet`、12 份 JSONL 清单、字段角色、来源、审计、制品哈希和 `protocol.yaml`。

- [ ] 使用固定 suite groups、预算样本清单和过滤聚合器生成候选协议；协议中记录固定分配 SHA-256、样本清单 SHA-256、抽样算法版本、源码 SHA-256、峰值内存记录要求和 `review_pending` 限制。
- [ ] 添加两个小型独立输出逐字节一致、12 份清单加载、全局 `sample_id` 唯一、模型字段有限、输出拒绝覆盖和失败保留 `_INCOMPLETE` 的测试。
- [ ] 只注册新命令入口，不更改历史 C-only 和通用 A/B/C 命令。
- [ ] 在服务器执行受影响的最小测试集合、Black、Ruff 和语法检查；不得因本任务重跑无关训练测试。

### 任务 4：独立审查与真实双物化

**文件：**

- 新建：`.Codex/docs/sdd/task-tqh-dataset-download-manager/abc-fixed-materialization-implementation-report.md`
- 新建：`.Codex/docs/sdd/task-tqh-dataset-download-manager/abc-fixed-materialization-review.md`
- 更新：`.Codex/docs/sdd/task-tqh-dataset-download-manager/task_plan.md`
- 更新：`output/第一创新点实验总控.md`

- [ ] 新的独立审查代理核对固定清单、真实排序处理、摘要编码、内存上界、泄漏、失败原子性和测试证据；严重或重要问题不为 0 时停止真实运行。
- [ ] 在两个全新临时目录串行物化，分别保存命令、输入与代码 SHA-256、日志、状态、时长、峰值内存和结果摘要。
- [ ] 比较全部非自引用制品；逐字节不一致、12 份清单加载失败、哈希回读失败或硬覆盖失败时停止，不追加第三次物化。
- [ ] 全部门禁通过后才原子发布到 `runs/data-frozen/dataset-candidate-tqhc2-abc-v0/protocol/`，并更新详细报告与实验总控；正式发布前保持 `review_pending`。

## 已知失败与裁决

- 2026-07-28 第一份真实通用物化在约 63 秒后失败，错误为 `单个行组内 sample_id 非连续：A:row_group=0`；输出保留于 `/tmp/tqh-candidate-abc-v0-a-20260728/protocol/_INCOMPLETE`。
- A 首行组含 65,536 条包记录、732 个唯一样本、1,922 个样本片段，同一流可在其他流之后继续出现，但样例流的 `packet_index` 仍严格为 0 至 32。
- 该事实证明“样本在行组内连续”是错误的工程假设，不代表数据损坏。按预注册终点停止通用物化器修复，改用本计划；本计划失败后不再新增物化架构。

## 当前状态

**任务 1 待实施。** 用户已否决全量处理；当前固定预算为 35,235 条流、2,475,729 条包。原通用路径的测试、静态检查和修复后复审已通过，但真实输入揭示了测试夹具未覆盖的交错包排序。
