# 三源统一数据索引与预算清单实施计划

> **执行要求：** 使用 `subagent-driven-development` 按任务实施；实现代理只针对自己的任务使用一次 `test-driven-development`，测试仅在服务器执行。

## 目标

在不重新处理 GeNIS、TQH-C2 和 ns-3 底层数据的前提下，生成可审计、可复现、逐字节稳定的三源统一主索引与训练、候选筛选、开放集评测预算清单，使同协议基线和 R1-R3 技术路线筛选能够立即启动。

## 架构

统一层只保存样本身份、来源、原始制品定位、划分角色、标签可用性和视图可用性，不改写三个来源的特征或标签。预算层以统一样本身份为唯一引用，使用固定配置、固定种子和 SHA-256 排序生成清单；两次独立物化逐文件比对后再原子发布。源数据继续由各自冻结协议负责，避免复制大体量特征和包数据。

## 技术栈

Python 3.10、Pandas、PyArrow、PyYAML、pytest、uv、rsync。

## 全局约束

- 服务器项目根目录固定为 `/root/autodl-tmp/thesis/experiments/llm_probe`。
- Python 测试只在服务器用 `uv run --no-sync pytest` 执行，不在本机运行。
- 本地与服务器代码同步只使用 `rsync`，不得使用 `--delete`。
- 不运行裸 `uv sync`，不修改现有训练依赖。
- GeNIS 正式训练恰好 `30,000` 条；TQH-C2 直接复用已冻结的域内训练 `27,235` 条；ns-3 使用全部 `2,421` 条且每条只出现一次；统一正式训练总数固定为 `59,656` 条。
- 候选筛选清单固定约 `10,000` 条，组成必须在任何候选结果产生前冻结。
- GeNIS 神经模型开放集主表固定 `30,000` 条；开放集全量清单保留 `1,179,168` 条及其哈希。
- 清单不得读取模型预测、指标或最终测试结果，不得通过复制样本补足预算。
- 每个预算记录必须唯一映射至统一主索引；跨来源样本身份冲突必须显式失败，不得静默覆盖。
- 第一次真实物化保持 `provisional` 与 `review_pending`，独立复审和双物化一致性通过后才允许发布。
- 长任务写入唯一输出目录、完整日志、状态和哈希；服务器重启后能够从已落盘阶段恢复。

## 任务

### Task 1：审计三源输入契约并冻结预算配置

**文件：**

- 创建：`.Codex/docs/sdd/task-unified-dataset-budget/notes.md`
- 创建：`thesis/experiments/llm_probe/configs/unified_budget_v1.yaml`

**验收：**

- [x] 核验三源实际路径、协议哈希、样本数、划分名、样本身份和可用分层字段。
- [x] 明确 GeNIS 会话与时间字段能否从现有冻结制品直接取得；字段缺失时只记录真实限制，不构造伪字段。
- [x] 固定候选筛选清单三源数量与选择规则，并证明总数约为 `10,000`。
- [x] 配置写明算法命名空间、种子、源哈希、目标数量、输出文件名和禁止使用的划分。

### Task 2：实现统一索引与确定性预算生成器

**文件：**

- 创建：`thesis/experiments/llm_probe/src/flow_probe/unified_budget.py`
- 创建：`thesis/experiments/llm_probe/tests/test_unified_budget.py`
- 修改：`thesis/experiments/llm_probe/pyproject.toml`

**接口：**

- 输入：任务 1 的固定配置、两个冻结协议目录和三份 ns-3 JSONL。
- 输出：统一主索引、预算清单、统计、校验和与冻结清单。
- 公开入口：`materialize_unified_budget(*, project_root: Path, config_path: Path, output_dir: Path) -> dict[str, object]`。
- 命令入口：`flow-probe-build-unified-budget --project-root <路径> --config <配置> --output <新目录>`。
- 候选协议必须使用配置中的 `expected_protocol_version`、`expected_status` 和 `expected_phase` 调用现有 `load_frozen_protocol`；不得把候选制品伪装成最终冻结协议。

**固定选择算法：**

1. GeNIS 会话时间只从配置绑定的 `session_assignments.jsonl` 获取，以 `group_id=session_id` 连接；时间块为 `start_time` 转换得到的 UTC 自然日。训练和开放集分别按“UTC 日、家族、子类”形成联合分层单元，以 Hamilton 最大余数法分配精确目标，并在目标允许时保证每个非空分层单元至少一条。
2. GeNIS 层内按会话轮转：会话以 `SHA-256(算法命名空间|种子|分层键|group_id)` 排序，会话内样本以对应 `sample_id` 哈希排序，每轮每个会话至多取一条，直到满足配额，避免大流会话垄断。
3. TQH-C2 正式清单逐条复用 `tqhc2_cell_indomain-train.jsonl` 的固定 `27,235` 条及其顺序，不重新组合搜索。候选子集按 `allocation_group_id`、`profile`、`interval_s`、`jitter_pct` 和 `binary_label` 分层，以相同 Hamilton 与 SHA-256 规则抽取固定数量。
4. ns-3 按 `train`、`validation`、`test` 固定顺序读入三份各 `807` 条清单，正式与候选都使用全部 `2,421` 条且不重复。其历史测试划分在新合同中只作来源元数据，最终物理外测改用冻结模型后的哑铃与停车场拓扑。
5. 候选 GeNIS 与 TQH-C2 都必须是相应正式清单的子集；统一正式与候选清单分别使用独立算法命名空间对全部已选样本做 SHA-256 稳定混排。
6. 三源原始 `sample_id` 当前零冲突，因此统一索引保持原标识；实现仍须每次验证全局唯一，发现冲突立即失败，不自动改名。

**输出模式：**

- `master_records.parquet` 只保存 `sample_id`、来源、源制品相对路径、源记录序号、源划分、分组身份、任务角色和视图可用掩码；检测标签只保留源值用于分层审计，不构造跨源统一类别。
- 每份 JSONL 预算行至少包含模式版本、预算标识、顺序号、`sample_id`、来源、任务角色和 `master_records.parquet` 哈希，并采用固定键顺序与结尾换行。
- `budget_checksums.json` 登记除自身和冻结清单外的全部制品；`budget_freeze_manifest.json` 再绑定校验和文件哈希，不建立自引用哈希。
- 持久化输出不得包含绝对路径、输出路径、运行时钟或随机标识，以保证两个不同目录逐字节一致。

**验收：**

- [x] 测试覆盖非法源哈希、跨来源身份冲突、禁止划分泄漏、重复样本、目标不足、非确定顺序和输出覆盖拒绝。
- [x] 测试覆盖候选协议显式状态加载，防止误用 `load_frozen_protocol` 的最终协议默认参数。
- [x] 测试覆盖 Hamilton 精确配额、UTC 日分层、会话轮转、候选为正式子集和 ns-3 不重复。
- [x] 生成 `master_records.parquet`，仅保存引用与角色元数据，不复制原始高维特征。
- [x] 生成 `train_genis_30000.jsonl`、`train_tqhc2_cell_cap1000.jsonl`、`train_ns3_all2421.jsonl`、`train_unified_formal.jsonl`、`train_candidate_approx10000.jsonl`、`eval_genis_open_neural_30000.jsonl` 与 `eval_genis_open_full_1179168.jsonl`。
- [x] 生成 `budget_statistics.json`、`budget_checksums.json` 和 `budget_freeze_manifest.json`，记录输入哈希、实现哈希、顺序哈希、计数、分层前后统计和运行状态。
- [x] 输出先写临时目录，全部检查通过后原子改名；已存在目标目录时拒绝覆盖。
- [x] 在服务器运行直接覆盖本模块的最小测试，不运行无关完整回归；有效通过 `13/13` 项（目标套件 `12` 项加精确复核 `1` 项）。

### Task 3：独立复审与双物化验收

**文件：**

- 创建：`.Codex/docs/sdd/task-unified-dataset-budget/code-review.md`
- 创建：`.Codex/docs/sdd/task-unified-dataset-budget/materialization-verification.md`

**验收：**

- [x] 独立审查数据泄漏、样本身份、分层抽样、哈希绑定、原子发布和重启恢复；严重问题为 `0`，仍有早期异常内部状态标记的重要恢复缺口。
- [x] 在服务器两个全新目录独立运行真实物化，保存配置、命令、日志、状态和资源统计。
- [x] 比较两次输出的相对路径、文件数、行数和 SHA-256；两次各 `11` 个文件，差异为 `0`。
- [x] 验证正式训练总数 `59,656`、候选数量 `10,000`、开放集主表 `30,000` 和全量开放集 `1,179,168`。
- [x] 运行与发布继续标记为 `review_pending`；剩余恢复缺口不改变本次成功构建内容，但在最终冻结前必须关闭。

详细验收见[双物化与发布验证](materialization-verification.md)。

### Task 4：原子发布并解锁同协议基线

**文件：**

- 发布：`thesis/experiments/llm_probe/runs/data-frozen/dataset-v1/`
- 更新：`output/第一创新点实验总控.md`
- 仅在长期边界改变时更新：`output/开题改进交接文档.md`

**验收：**

- [x] 将通过验收的一次构建发布到服务器固定路径 `runs/data-frozen/dataset-v1/`，与验收构建逐文件 SHA-256 差异为 `0`。
- [ ] 以 `rsync` 回收配置、清单、哈希、日志和摘要到本机。
- [ ] 基线与候选配置只引用发布后的版本、清单路径和 SHA-256。
- [x] 在总控文档记录服务端路径、准确计数、哈希、运行日志和下一步 B0 顺序；本地回收路径待完成后补记。
- [ ] 发布完成后立即启动共享预算基线，不等待文档格式化或无关审查。

## 关键问题

1. GeNIS 当前冻结样本中，时间与会话信息的实际字段是什么？
2. 三源原始 `sample_id` 是否全局唯一，还是必须增加不改变原身份的统一命名空间键？
3. 候选 `10,000` 条的三源固定组成如何兼顾检测任务与全部 `2,421` 条物理序列？
4. 统一索引如何引用 ns-3 JSONL 而不复制序列正文？

## 已作决策

- 不重做 TQH-C2 预算：直接复用已双物化验收的 `27,235` 条域内训练清单。
- 不裁剪三个来源的冻结制品：统一层只新增引用索引与预算选择层。
- 正式训练精确总量固定为 `59,656`，不再沿用“约 60,000”作为执行值。
- 统一预算生成完成前不启动新的 PINN 候选训练；但字段审计、实现、复审和双物化并行推进。

## 错误记录

- 首次 `apply_patch` 因目标目录不存在而失败；随后发现受限环境禁止直接创建 `.Codex/docs/sdd` 子目录，已通过获批的目录创建操作解决，未产生半成品文件。

## 状态

**Task 2、Task 3 已完成，Task 4 进行中。** 统一预算已在服务器双物化并暂定发布，数据内容与确定性门禁通过；状态继续保持 `theory_selection/review_pending`。下一步回收关键制品、固定基线配置引用并启动共享预算 B0，不得把当前发布写成论文最终冻结数据。
