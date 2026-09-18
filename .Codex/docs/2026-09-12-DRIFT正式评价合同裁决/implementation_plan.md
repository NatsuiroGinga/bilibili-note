# DRIFT 第三章正式评价接口与正式运行实施计划

> **2026-09-13 14:37 用户裁决覆盖：禁止新增物化。** 已废止预生成成员／源训练／源验证副本、攻击数据集、落盘索引和新增 Rust 物化工程；正文现已改为现有 DRIFT Parquet 只读直读方案。已验收的三份 JSON 配置与 `ch3_drift_formal_contract.py` 保留并最小适配；正在运行的 MP 不受影响。

> **状态：主代理已核验直读、编辑、评价及比较边界，按具体简报逐项实施。** 共享编辑已通过真实T17与跨进程验收；直读模块开始实现。两骨干训练中的增强缓存精确恢复仍须独立简报，不因本计划已核验而视为已解决。父代理按难度为 `gpt-5.6-luna` 选择实际 `effort`；未实现接口及未运行阶段继续按下文标识，不得提前启动或报告完成。

> **实施代理须知：** 实现阶段必须按 `subagent-driven-development` → `daily-coding` 执行本计划。同一时间只允许一个实现代理修改本任务文件；主代理负责独立验收。不得用聊天建议代替文件修改、真实数据门禁和真实运行制品。

**目标：** 在不改变 A/B/D/F/G 训练科研合同的前提下，让 DRIFT 与第二骨干通过同一只读加载器直接消费现有 Parquet，在运行时执行规范 `unique()`、固定哈希成员选择和共享编辑，输出逐臂低误报阈值、逐年干净／三档攻击预测及实体配对统计。该计划只使 F 具备被检验的条件，不预判 F 有效。

**总体设计：** 将“原始输入直读与审计”“共享编辑”“单臂训练”“统一评价”“配对统计”拆成五个有收据边界的阶段。原始 Parquet 始终原地只读；成员与攻击不预写磁盘，而由共同配置、原文件 SHA-256 和确定性算法在各运行中复算。每个骨干、训练臂和评分任务使用独立进程与运行目录；各臂预测以成员主键、输入哈希、编辑流哈希和成员根摘要机械核对配对关系。

**技术栈：** 本机只使用已验收的 `/opt/miniconda3/envs/rwkv/bin/python`（Python `3.14.5`）及其实测 PyTorch、NumPy、PyArrow、SciPy、Polars、SwanLab；服务器只使用 `source tools/env/activate.sh` 后的 `uv run --no-sync`，实际 Python 与库版本从当次服务器环境验收收据读取并写入运行身份，不在本计划猜填。优先使用当前环境的 PyArrow 原生批读取；若仓库已有 Polars 或 Rust 执行引擎能以库接口完成同一只读扫描，可复用但不得新建工具链、数据工程、落盘索引或副本。全量源数据需要常驻内存完成 exact eSLD `unique()` 与训练随机访问，必须先实测容量；禁止把内存不足偷换成临时磁盘物化。

**当前运行事实快照（2026-09-13 15:03）：** 正式评价平台已登记的 4 条历史运行均为 `CRASHED`，`0 running`；与本计划分离的本机 MP 进程 PID `77528` 活动，第 3 轮进度为 `161/469`，尚未完成。B-ResNet B 臂最小修复已通过主代理验收，但尚未以新身份重跑真实训练或产生效果结果。本计划不得把 MP 或 B 臂工程修复写成正式评价训练／科学结果，也不得因本计划修订改变 MP 成员或运行身份。实施或正式启动前须重新只读核对平台、持久会话、进程与原始日志；若状态变化，以新收据更新实施报告，不回写猜测。

**可立即实施的最小范围：** Luna 可先最小修改已验收四文件的模式与直读约束，再实现纯 CPU 的只读加载器、30 文件输入收据、规范 `unique()`、重合／冲突审计、固定哈希选择器、共享编辑算子和真实 T17 嵌套验证。新实体资格政策、family 资格、源训练—验证重合处置或配对重采样参数未冻结，只阻断对应主张／校准／区间，不拖住这些接口及不受影响的训练。当前 MP 保留既有成员和运行身份，不事后换样本。

---

## 一、冻结边界与证据来源

### 1.1 不得改动的科研合同

1. 正式攻击只有共享编辑流的三档前缀：`k=1`、`k=2`、`random_half`。不得保留新的 `krand` 正式键，不得把历史第二次 `perturb2` 调用重命名为新分布。
2. T20–T25 每年、每类最多选择 `200000` 个固定哈希唯一实体；不足上限时取全部唯一实体。成员选择不设置 `member_seed`，不得接受同名命令行参数或配置字段。
3. 每个训练臂在完全相同的 T17–T19 源验证良性成员上，依据该臂自己的恶意概率分数分别冻结 `0.001` 主阈值和 `0.01` 辅阈值。
4. `score >= threshold` 判恶意；阈值必须按整体同分数组保守选择，使实测源良性假阳性数不超过 `floor(alpha * N_b)`。不得按行序拆分同分组。
5. T17–T19 的训练、验证角色不变；T20–T25 可用于披露后的目标知情架构、辅助任务组合和方法配置比较，但不得进入静态训练、早停或源阈值冻结。凡根据 T20–T25 结果作出的选择，必须登记所见结果、候选集合与新配置身份，并明确不能声称为独立最终测试。
6. A/B/D/F/G 的训练公式、优化器、学习率、批量、轮数、训练种子、在线增强和内部 `0.5` 分支判定保持现有正式脚本语义。正式评价的新编辑流不得反向替换训练增强流。
7. 固定 `0.5` 只能以名称含 `legacy` 的诊断字段保留，不能作为正式低误报主结果。
8. 纯 DGA 攻击面板只报告 FNR、TPR、计数和区间，不生成依赖正负混合的准确率、精确率、F1、AP 或 ROC-AUC。干净混合面板同时保留原文总体检测指标及本课题追加指标，并分别报告固定等类成员的 `sampled_50_50` 与合格发布总体权重的 `release_weighted` 语义；两者均不得暗称自然部署先验。
9. 当前只有一个训练种子。实体配对区间只表示固定训练运行条件下的样本不确定性，不得解释成训练随机性区间或多种子稳定性。
10. 不得设置未获批准的非劣界、最小增益或成功阈值。区间跨零记为“未分辨”；负效应完整记录，是否构成否决只由主代理验收后的主任务指标角色合同判断，辅助或任务外指标的负效应不自动否决。不得事后改成员、阈值或指标。

### 1.2 历史文件的角色

以下文件只提供已核对的训练语义和失败经验，不作为新生产入口：

- `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/official_p2p3.py`：筛选期训练臂来源；其 `krand` 重复分布、局部数据和 `0.5` 评价不得迁移。
- `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/official_p2p3_full.py`：A/B/D/F/G 臂公式及 `p2p3_official_full_checkpoint_v2` 的断点修复来源；其源数据只串接、不执行官方合并后 `unique()` 的重复曝光，以及顺序目标抽样、T18 独占攻击、全量 Python 列表和多臂单进程 SwanLab 均不得迁移。
- `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/bresnet_p2p3.py`：BResNet 架构与编码来源；其 B 臂最小实现修复已经验收，现为每个主批恶意成员追加一个 `official_p2p3.perturb2` 变体并校验 A/B/D/F/G 臂名，证据见 `.Codex/docs/2026-09-12-DRIFT正式评价合同裁决/bresnet-b-fix-report.md`。该修复尚未重跑真实训练，T17 小样本、旧 B 运行身份、无正式合法断点和 `0.5` 评价均不得迁移；既有 `B≈A` 读数不能解释为朴素增广无效，也不能进入正式比较。
- `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/server_launch_p2p3.sh`：历史直接启动脚本，只读保留，禁止调用和修改。
- `tools/ch3_drift_official_checkpoint_t17_eval.py` 与 `tools/ch3_drift_official_branch_conflict_diagnostic.py`：可复用已核对的 DRIFT 编码、载入和分支分数语义；其输入清洗和指标实现不能直接作为正式接口。

科学依据以 `thesis/methods/第三章-正式评价与F指标空间科研裁决.md`、`thesis/methods/第三章-正式攻击与目标抽样合同裁决.md`、`thesis/methods/第三章-DRIFT数据角色与评价协议.md`、`thesis/methods/第三章-基线与消融比较清单.md` 和已经主代理核验的 `thesis/methods/第三章-主任务指标与论文呈现合同.md` 为准；运行约束以 `thesis/experiments/llm_probe/AGENTS.md`、其 `scripts/AGENTS.md` 及拆分运行合同为准。实现与正式运行清单记录指标角色合同及基线／消融清单的当时 SHA-256；该合同明确未设定的数值门不随“核心指标”名称自动生效。

---

## 二、精确文件边界与职责

实现代理只修改或新建下列生产文件；历史证据文件不改：

| 文件 | 动作 | 唯一职责 |
| --- | --- | --- |
| `thesis/experiments/llm_probe/pyproject.toml` | 条件修改 | 仅在正式代码直接导入 SciPy 且当前未声明直接依赖时加入与锁文件兼容的 SciPy 约束。 |
| `thesis/experiments/llm_probe/uv.lock` | 条件修改 | 只由 `uv add`／`uv lock` 机械更新，不手改。 |
| `thesis/experiments/llm_probe/configs/ch3-drift-formal-evaluation-v1.json` | 最小修改 | 保留已验收的 30 角色、哈希、攻击、阈值与结果合同；将输入访问冻结为原 Parquet 只读直读，删除 `materialize` 能力并拒绝派生数据路径。 |
| `thesis/experiments/llm_probe/configs/ch3-drift-official-p2p3-formal-v3.json` | 最小修改 | 保留已验收的 DRIFT 数值与单臂身份；把 `input_views` 改为直接引用评价配置中的源角色及直读合同，删除 `materialize` 能力。 |
| `thesis/experiments/llm_probe/configs/ch3-drift-bresnet-p2p3-formal-v1.json` | 最小修改 | 保留已验收的第二骨干数值、协议身份和臂集合；改为相同直读合同。正式入口迁移已验收的 B 臂最小修复，但必须使用新运行身份重跑；合法正式断点仍为拟实现，不继承旧 B 结果。 |
| `thesis/experiments/llm_probe/tools/ch3_drift_formal_contract.py` | 最小修改 | 保留现有长度前缀编码、哈希、严格配置、原子收据和状态机；移除 `materialize` 模式，新增直读路径、禁止输出类型和只读输入门禁，不重写框架。 |
| `thesis/experiments/llm_probe/tools/ch3_drift_formal_data.py` | 新建 | 统一只读扫描现有 30 个 Parquet，在内存中执行规范 `unique()`、源重合／标签冲突审计及目标固定哈希前 200000 选择；只返回批／迭代器和收据，不写数据副本或索引。 |
| `thesis/experiments/llm_probe/tools/ch3_drift_formal_edit.py` | 新建 | 对评价迭代器当前 DGA 实体按需生成 `k=1/k=2/random_half` 共享前缀，返回编辑字符串与哈希；不写攻击数据集。 |
| `thesis/experiments/llm_probe/tools/ch3_drift_formal_models.py` | 新建 | 定义统一 `ModelAdapter`，实现 DRIFT 与 BResNet 的模型载入、批量恶意概率评分和身份核验；不选择阈值。 |
| `thesis/experiments/llm_probe/tools/ch3_drift_official_p2p3_formal.py` | 新建 | 将已冻结 DRIFT A/B/D/F/G 训练语义迁入配置化、单臂、可恢复的正式入口；使用有界数据访问。 |
| `thesis/experiments/llm_probe/tools/ch3_drift_bresnet_p2p3_formal.py` | 新建 | 将 BResNet 架构升级为全量、A/B/D/F/G、单臂、可恢复正式入口；评价仍交给共享评价器。 |
| `thesis/experiments/llm_probe/tools/ch3_drift_formal_evaluate.py` | 新建 | 直读原 Parquet，对一个骨干／臂运行时选成员和编辑，冻结逐臂阈值并输出允许留存的逐实体预测、计数、区间和收据。 |
| `thesis/experiments/llm_probe/tools/ch3_drift_formal_compare.py` | 新建 | 只消费本次五臂逐实体结果，核对完全配对后计算 F−B、D−B、D−A、F−D、G−A 与 A/D/G/F 交互项；明确 D−B 是相对朴素增广的整套选择训练差异，不重新评分或伪装成纯选择器效应。 |
| `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_drift_formal_input_audit_v1.sh` | 新建 | 经统一远程入口在服务器直读 30 个原 Parquet，写小型输入／重合／容量收据；不写数据文件。 |
| `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_drift_official_p2p3_formal_v3.sh` | 新建 | 严格校验单个 `ARM` 后启动一个 DRIFT 训练进程。 |
| `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_drift_bresnet_p2p3_formal_v1.sh` | 新建 | 严格校验单个 `ARM` 后启动一个 BResNet 训练进程。 |
| `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_drift_formal_evaluation_v1.sh` | 新建 | 严格校验 `BACKBONE`、`ARM` 和阶段，分别启动单臂评分或同骨干汇总。 |
| `.Codex/docs/2026-09-12-DRIFT正式评价合同裁决/implementation-report.md` | 实现后新建 | 记录修改文件、直读与容量检查、命令入口、开发区验证、正式运行身份和遗留风险。 |
| `.Codex/docs/DRIFT/DRIFT第三章恢复卡.md` | 节点更新 | 只在下文规定的证据节点由主代理写回，不把“代码完成”写成“实验支持”。 |

禁止顺手重构现有训练工具、通用启动器或历史文档。若实现中发现上述文件范围不足，先在实施报告写明新增职责与原因，由主代理确认后再扩展。

---

## 三、共享最小接口

### 3.1 配置与状态机

所有入口统一支持：

```text
--config <仓库相对路径>
--run-dir <仓库相对运行目录>
--audit | --run | --resume | --summarize
```

每次只允许一个模式；`--materialize` 必须被合同模块和全部生产入口明确拒绝。训练入口额外要求 `--arm A|B|D|F|G`；单臂评分要求 `--backbone drift|bresnet --arm A|B|D|F|G`；同骨干汇总要求 `--backbone drift|bresnet --summarize`，不得把 `all` 当作训练臂写进结果模式。正式配置中不得出现 `member_seed`、可变目标上限、运行时攻击名称、派生数据输出路径或可由命令行覆盖的阈值预算。命令行与配置冲突立即退出。

`ch3_drift_formal_contract.py` 同时是拟实现的统一机械门禁入口：

```text
python tools/ch3_drift_formal_contract.py \
  --gate inputs|train|evaluate|compare \
  --config <仓库相对路径> \
  --run-dir <仓库相对路径> \
  [--backbone drift|bresnet] [--arm A|B|D|F|G]
```

四个薄启动器必须先调用该入口并取得 `gate-receipt.json`，再调用统一远程启动器；生产入口自身也复验同一收据，不能只依赖 shell。门禁按阶段最小依赖检查：`inputs` 登记 30 个原文件的完整状态，`train` 只要求该臂所需源角色和容量，`evaluate` 只要求共同源验证及所请求目标单元，`compare` 只要求待计算差异涉及的臂和单元；任一阶段仍须检查模式版本、相关路径／SHA-256、代码身份、检查点、资格状态和单写者身份。禁止项按**输出角色与模式**判定：配置中的数据视图、成员、攻击、缓存和索引输出字段一律拒绝，数据库或索引模式也一律拒绝；不能仅凭 `.parquet` 后缀判定。结果模式只白名单允许计划冻结模式的逐样本预测 `entity-scores.parquet`、逐实体效应 `entity-effects.parquet`、模型、合法断点、统计结果和小型 JSON／JSONL 收据，且禁止这些结果重新作为训练或成员选择输入。

每个运行目录均须原子写入：

- `config.snapshot.json`：规范化配置及 SHA-256。
- `manifest.json`：上游制品哈希、代码身份、环境身份和输出清单。
- `status.json`：`created`、`running`、`complete`、`failed` 之一；失败包含阶段、错误类和可恢复性，但不含凭据。
- `run.log`：与统一启动器日志同 inode 或明确链接。
- `resource.jsonl`：时间、cgroup `memory.current`、`memory.max`、GPU 显存和吞吐；不得用 `free` 推断容器余量。

只有 `status=complete` 且清单内全部文件哈希匹配时，下游才可消费。存在临时文件、部分状态或未知模式版本时失败关闭。

### 3.2 原 Parquet 直读与运行时成员接口

输入合同完整列出 T17–T19 的 12 个训练文件、6 个验证文件和 T20–T25 的 12 个目标文件，共 30 个角色。加载器以只读方式打开配置中的原路径；每次运行写 `input-receipt.json`，记录仓库 revision、相对路径、文件字节数、Parquet 行数、行组数、模式和文件 SHA-256。缺文件、重复／额外角色、哈希变化、空值、非字符串、空 eSLD 或未声明字段变化均阻断**依赖该角色的阶段**，不允许在完整六年裁决中静默跳年，也不复制原文件；目标年缺失或全输入审计未完成不能反向阻断已满足全部源角色与容量门的有效单臂训练。

拟实现的统一接口为：

```text
audit_inputs(config) -> InputReceipt
load_source_unique_in_memory(role_group, input_receipt) -> SourceStore
iter_target_selected(year, class, input_receipt) -> Iterator[EntityBatch]
count_target_unique_in_memory(year, class, input_receipt) -> TargetUniqueCount
```

`SourceStore` 只存在于当前训练／评价进程内，进程结束即释放；不得序列化为 Parquet、Arrow、NumPy、数据库、缓存或索引。它按冻结角色顺序直读源 Parquet，先检测跨类冲突，再执行官方合并后 exact eSLD `unique()`，向两个骨干暴露同一实体顺序、标签和来源语义。每个进程写 `source-read-receipt.json`，只含原文件哈希、原始／唯一计数、冲突／重合计数、规范顺序摘要、实现与资源身份，不含实体列表。

成员身份采用无歧义 UTF-8 长度前缀编码：

```text
member_hash = SHA-256(encode(namespace, revision, panel_id, year, class, exact_esld))
```

其中 `namespace` 是配置中的版本标识，不是随机种子。实现必须保留 exact eSLD；不得 `strip`、`lower` 或以 Python 对象散列替代 SHA-256。每个 `(panel_id, year, class)` 先按 exact eSLD 去重，再按完整 256 位摘要升序取最小 `min(200000, unique_count)` 个。摘要碰撞、同一 exact eSLD 的标签冲突或长度前缀编码复算不一致均阻断受影响面板。

`target_official_annual_v1` 在每个 `(year,class)` 单元顺序扫描一次原 Parquet，以最大 200000 项内存堆维护完整 SHA-256 最小集合；堆内以 exact eSLD 去重并检查会影响入选集合的摘要碰撞。相同输入收据和配置必须得到相同 `selected_member_root_sha256`。不写成员表；评价结果逐样本记录 `member_hash`、原文件身份和分数。这个有界堆只证明入选成员唯一且选择确定，**不能**给出超过上限单元的全文件 `N_unique`、总体重复数或全体碰撞数，也不得用原始行数替代这些量。

`count_target_unique_in_memory` 是与前 200000 选择器分离的可选精确统计：对一个 `(year,class)` 保存全文件 exact eSLD 集合，在内存中计算 `N_unique`、类内重复数及集合根摘要；其容量随该单元唯一实体数线性增长，必须使用独立的真实容量前检。计算失败时写 `blocked_no_non_materialized_exact_count`，不得从堆大小、原始行数或近似基数估计补值。该失败不改变固定哈希主成员，也不阻断不依赖总体类别权重的 `sampled_50_50` 与逐实体主指标，只使相应 `release_weighted` 结果及“全体重复／唯一计数”主张标为未具备。`target_new_entity_annual_v1` 与 family 分面仍待重合、生成器等价、良性污染和映射资格裁决；直读器可以输出聚合审计收据，但在资格收据冻结前不得过滤实体或提出相应主张。

共同源阈值成员由 T17–T19 三个 benign val 文件在内存中合并并 `unique()`，不设 200000 上限。源训练／验证重合审计与处置分离：先写聚合计数与集合摘要，不暗自过滤。若存在重合而政策未冻结，训练和不依赖独立校准的接口可继续；阈值分数与诊断阈值可留存，但正式校准资格及“实体隔离”主张标为 `blocked_pending_source_overlap_policy`。

当前只读实测仅覆盖 MP 使用的四个小样本内部清单：各文件内部无重复，字段仅有 `domain,label`；T17 train 与 T18 val 共享 18 个域名，其中良性 17 个、DGA 1 个，family 覆盖尚未测。该证据证明不能声称筛选成员完全实体隔离，但不能外推为 18 个全量源角色的交集结论，也不授权暂停 MP、改变其样本或拍脑袋冻结新实体策略。全量源角色仍须由本工具重新审计。

只允许输出小型收据：`input-receipt.json`、`source-read-receipt.json`、`target-selection-receipt.json`、`target-unique-count-receipt.json`、`overlap-conflict-audit.json`、`capacity-preflight.json` 和经主代理冻结的资格收据。每个统计字段同时记录算法、范围和 `complete|blocked` 状态：前 200000 选择收据只给入选数和入选集合根摘要；唯一数、类内重复数、全体碰撞数只有相应整集合精确统计完成后才可给值。收据不写逐实体清单。

全量规模为 262674016 行，源角色约 8693 万行。目标选择器的严格常驻上界是一个输入批加 200000 个候选；源 `unique()`、全量源训练／验证交集、逐轮随机访问和每个目标单元的精确 `N_unique` 则需要与相应唯一实体数线性增长的内存。Luna 必须在服务器先用真实批次测出所选现有执行引擎的每实体槽位、字符串区、顺序向量、批缓存和模型保留量，分别以 `U_source <= N_source`、`U_target_cell <= N_target_cell` 计算各操作的 `required_peak_bytes`，与 cgroup `memory.max`、当前占用和模型实测峰值比较并写 `capacity-preflight.json`。只有对应操作的 `required_peak_bytes` 有确定上界且容量满足才可启动；批大小与保留量不得猜测。目标总体计数容量不足只阻断依赖它的总体加权结果，不连带阻断有界主成员选择。

若现有 PyArrow／Polars／Rust 库接口无法在内存上界内完成下列任一项：全局 exact eSLD `unique()`、精确源训练／验证交集、每轮唯一实体随机访问、目标单元整集合唯一计数，则该项明确标为 `blocked_no_non_materialized_exact_algorithm`。禁止以临时排序文件、SQLite／LMDB、内存映射落盘表、Arrow IPC、缓存分区或新增 Rust 项目绕过；主代理需回用户裁决容量或范围，计划不得假装已解决。阻断按操作传播，不得让缺少 `release_weighted` 的总体计数拖住固定哈希成员的主评价。

### 3.3 评价时共享编辑接口

每个已入选 DGA 实体只建立一个确定性域内编辑流。流身份由以下长度前缀字段派生，不接受自由随机种子：

```text
attack_stream_id = SHA-256(encode(
  attack_namespace, revision, exact_esld
))
```

流身份不含面板、年份、模型或训练臂，因此同一 revision 内重复出现的 exact eSLD 在所有消费端得到同一编辑；面板、年份和类只属于成员关联。字符集固定为 `abcdefghijklmnopqrstuvwxyz0123456789-`。拟实现的 v1 算子使用 `SHA-256(encode(attack_stream_id, counter))` 扩展字节，并用拒绝采样驱动 Fisher–Yates 不放回位置排列和“排除原字符后”的等概率替换；不得用有模偏差的直接取余，也不得依赖 Python 对象散列或遍历顺序。算法版本及其规范说明哈希进入输入／编辑算法收据和评价 `manifest.json`。v1 不设置重复编号或自由种子；三档预算为：

```text
L = len(exact_esld)
q1 = min(1, L)
q2 = min(2, L)
qh = min(max(1, floor(L / 2)), L)
```

`k=1`、`k=2`、`random_half` 必须分别取同一流的前 `q1`、`q2`、`qh` 个编辑，因而满足前缀嵌套。空字符串在成员门已失败；`L=1` 或 `L=2/3` 导致预算重合时保留真实结果并记录 `degenerate_budget=true`，不得丢弃或补造差异。编辑只存在于当前评价批内；逐样本预测记录 `member_hash`、`attack_tier`、`attack_stream_id`、预算、汉明距离、`output_sha256` 和退化标记，不写 `attacked_esld` 或攻击数据文件。以下任一情况阻断当前评价：

- 替换字符等于原字符；
- 实际汉明距离不等于有效预算；
- 三档不满足同流前缀；
- 相同 `(member_hash, attack_tier)` 得到多个输出；
- 不同输入意外得到相同攻击输出而未在 `attack-collision-audit.json` 中记录；
- 相同原文件收据和成员主键复算得到不同编辑流／输出哈希。

DRIFT、BResNet 和全部训练臂调用同一个纯函数。各臂虽在各自进程重新生成编辑，但比较器必须逐行验证 `member_hash/attack_tier/attack_stream_id/output_sha256` 完全相同。真实 T17 嵌套审计只写聚合计数与根摘要。

### 3.4 模型适配器

`ModelAdapter` 只暴露以下公共接口：

```text
identity() -> {backbone, arm, checkpoint_schema, checkpoint_sha256,
               train_config_sha256, input_receipt_sha256, complete}
score(exact_esld_batch) -> float64 恶意概率数组
```

DRIFT 适配器复用已核验的编码、token 分支、字符分支和融合概率语义；BResNet 适配器复用已核验的 40 项字符表、长度 63 左填充编码和 `p_mal`。两个适配器必须返回同方向、有限的 `[0,1]` 恶意概率，不得在适配器内阈值化、改变 exact eSLD 或选择成员。数据门先断言正式 exact eSLD 已是小写且全部字符可编码；BResNet 历史 `.lower()` 对合格输入只能是字节不变的幂等步骤，未知字符不得静默映射为填充。

每个正式评分身份须在配置中固定骨干、检查点、输入收据、成员／编辑算法、评分批量、张量精度、设备与软件环境，随后只生成一份权威 `entity-scores.parquet`；其 SHA-256 只证明已保存制品未被改写，不代表跨批量或跨硬件位级可复现。本项目已有不同 MPS 批量／前向产生数值噪声的证据，因此改变评分批量、精度或环境必须创建新评分身份，不能要求分数内容哈希相同。需要复算时，优先在同一固定身份下执行；若比较不同身份，只记录逐实体绝对差和汇总差异。只有已有实测收据冻结了数值容差时才据此判定，否则报告差异而不设置默认阈值。各臂运行时成员根摘要和编辑流哈希仍必须严格一致。

### 3.5 逐臂阈值冻结

评价器先对共同源良性清单评分，再独立为每个 `(backbone, arm)` 冻结两个阈值。对 `alpha in {0.001, 0.01}`：

1. 校验全部分数有限，记录实际分数数据类型。
2. 令 `q=floor(alpha*N_b)`。
3. 按分数降序形成整体同分组，从最高分组开始累计；只要加入下一整组后累计仍不超过 `q` 就纳入。若至少纳入一组，阈值取最后纳入组的分数；若首组已超过 `q`，阈值取同数据类型 `nextafter(max_score, +∞)`，不使用无穷值。
4. 复算并断言实际 FP 不超过 `q`，不按输入行序拆同分组。

`thresholds.json` 至少记录：算法版本、`alpha`、`N_b`、`q`、阈值、分数数据类型、最大／最小分数、阈值处同分组大小、实际 FP/FPR、源成员根摘要、输入收据哈希、模型检查点哈希、训练配置哈希和阈值文件哈希。一个臂的阈值不得供另一臂使用。

### 3.6 结果模式与统计字段

每个评价运行写 `entity-scores.parquet`、`thresholds.json`、`metrics.json` 和 `manifest.json`。逐实体表至少包含：运行身份、骨干、训练臂、面板、年、类、成员哈希、攻击档位（干净为 `clean`）、输入／输出哈希、恶意概率、两个源冻结阈值下的预测。正式结果不依赖行序，汇总前按稳定主键排序。

每个面板单元至少记录：

- `n_total`、`n_benign`、`n_dga`、`tp`、`tn`、`fp`、`fn`；
- 0.1% 主工作点和 1% 辅工作点的 FPR、FNR、TPR；
- 每个二项比例的 95% Clopper–Pearson 精确区间及算法／SciPy 版本；
- 干净混合面板在两个源冻结工作点下的准确率、精确率、召回率和 F1，以及阈值无关的 AP、ROC-AUC；既有总体检测指标均保留，不能因不是自动淘汰项而省略；
- `sampled_50_50` 派生统计按两类固定哈希顺序各取 `min(n_benign, n_dga)` 个，记录正类比例 `0.5`，只在统计时选行，不另写数据视图；`release_weighted` 只能使用 `count_target_unique_in_memory` 对同一年度、同一资格规则得到的两个完整精确 `N_y,c` 计算类别权重，并保存计数收据哈希与隐含正类比例。任一总体唯一计数未完成时，`release_weighted_status=blocked_missing_exact_unique_count` 且不生成加权数值，绝不以原始行数或前 200000 入选数替代。二者都不是现实部署先验；没有外部冻结的部署基率时不得报告部署精确率／F1；
- 明确分离的 `clean_fpr_at_0p5_legacy`、`clean_fnr_at_0p5_legacy`，不进入主表；
- 纯 DGA 攻击单元不生成准确率、精确率、F1、AP 或 ROC-AUC 键，模式校验发现任一混合类别指标即失败；Recall 只以同义且唯一的 TPR 字段表示。

目标年重新标阈值只能进入独立的 `target_informed_oracle` 表，字段名、目录和图表均不得与 `source_frozen` 主结果合并。T25 无论结果方向如何都必须报告；缺少 T25 使整套正式评价不完整。

同一骨干五臂完成后，比较器必须先逐行核对相同 `panel_id/year/member_hash/attack_tier`、相同输入／攻击哈希和相同成员数，再计算本次批准五臂内的差异：

- 完整方法效应：`F - B`；
- 相对朴素增广的整套选择训练差异：`D - B`。B 对原域名只执行一次 `perturb2`，D/F 使用 `base + candidate` 两阶段复合核且候选数量、选择方式也不同，因此该差异不能命名为纯组件一、组中心化或筛选器效应；
- A/D/G/F 因子链中的组件一开关差异：`D - A`；
- A/D/G/F 因子链中的组件二条件差异：`F - D`；
- A/D/G/F 因子链中的组件二单独差异：`G - A`；
- 交互项：`I = R_F - R_D - R_G + R_A`。

纯选择器归因需要后续新增两个**同候选池、同复合候选核、同候选数、同入批配额**的控制身份：`Uniform-q` 不读取候选分数并均匀选择，`CE-top-q` 按未中心化全局交叉熵排序。统一训练和比较接口须预留可注册的有意义展示名、候选池／配额身份及逐候选选择收据字段，但这两个控制不加入本次已批准的 A/B/D/G/F 臂枚举、启动命令、完整性门或正式运行预算；须由主代理另行冻结配置与身份后才能实现和运行。后续合格比较分别为 `D - Uniform-q` 与 `D - CE-top-q`，不得用 B 替代。

后续控制的最小登记接口仅冻结字段，不属于本次实现范围：`control_id`、展示名、`proposal_kernel_id`、每个 owner 的候选数、入批配额、选择规则、并列规则、独立选择流身份、候选池根摘要和选择结果根摘要。`Uniform-q` 与 `CE-top-q` 必须共享除选择规则／所需评分计算外的全部这些字段；正式配置、训练入口和比较器只有在主代理另行批准新配置版本后才允许接受这两个 `control_id`。

`R` 对 FPR、FNR 采用“越低越好”的统一改善方向，对 TPR、准确率、精确率、召回率、F1、AP、ROC-AUC 采用“越高越好”的统一改善方向；原始差值与方向化差值同时保存，防止符号误读。指标角色由主代理已核验的主任务指标与论文呈现合同给出；该合同未设定的数值门不得由比较器补造，也不因某列存在就要求全部为正。

配对比较首版必须先输出完全配对的逐实体效应长表，并把训练随机性、攻击流和样本不确定性分开。重采样次数、累计批量和数值容差目前没有冻结依据，实施代理不得沿用草稿整数或自行新增科学阈值。拟实现的比较器须支持由 `paired-resampling-contract.json` 提供这些参数，并在该收据缺失时只生成逐实体效应与 `resampling_status=blocked_unfrozen_contract`，不得发布配对区间或据此裁决。收据应在不读取正式目标效应方向的前提下，依据真实成员规模的运行时间、峰值内存和数值精度实测由主代理冻结；确定性流从收据哈希和单元主键派生，不新增自由训练种子。正式重采样以实体为单位，同一抽样索引绑定各臂和三档编辑，并输出实际次数、流身份、累计精度轨迹与停止原因。

---

## 四、旧数据、旧断点与旧结果的兼容和失败关闭

1. **原数据：** 只允许直接读取当前 DRIFT revision 的 30 个 Parquet。每个正式运行须复算完整输入收据；只有 T20 的既有哈希不能替代全清单。revision 或任一文件哈希变化时创建新运行身份，不复制、改写或版本化原数据。
2. **旧检查点：** `p2p3_official_full_checkpoint_v1/v2` 以及 BResNet 筛选权重只允许 `--audit` 或标为 `engineering_only` 的入口冒烟；不得正式续训、迁移为新模式或作为正式比较模型。形式上能载入不等于训练身份合格。
3. **新 DRIFT 断点：** 使用 `ch3_drift_official_p2p3_formal_checkpoint_v3`；保留已修复的“下一批”语义，记录模型、优化器、Python/NumPy/PyTorch/CUDA 随机状态、内存唯一实体顺序摘要与洗牌状态、`next_epoch`、`next_batch_idx`、训练配置哈希、输入收据哈希、骨干和单臂身份。断点不得嵌入域名集合、增强域名缓存或落盘索引。对于训练实现中按原样本索引缓存增强字符串的臂，仅保存随机数生成器状态**不能**证明恢复后能重建此前所有缓存值及后续命中轨迹；本计划不新造其恢复算法。
4. **新 BResNet 断点：** 使用独立的 `ch3_drift_bresnet_p2p3_formal_checkpoint_v1`，字段与 v3 的恢复语义一致。不得只保存最终权重。
5. **断点频率与增强缓存恢复合同：** DRIFT 保留已核验的 v2 调度：每 2000 批及每轮末保存，断点指向下一批；拟实现的 BResNet 正式入口沿用相同调度。该调度只冻结保存时点，不自动解决增强缓存恢复。依赖不落盘增强域名缓存的训练臂按 [训练增强缓存无明文恢复实施简报](augmentation-cache-resume-brief.md) 重放首轮已见前缀、核对缓存摘要，再恢复检查点各随机状态；真实中断收据尚未形成前仍不得宣称恢复等价，也不授权落盘缓存。写入仍采用临时文件、同步、原子替换并复读模式与身份；若实测证明调度不合格，只能登记证据并由主代理裁决。
6. **运行目录：** 每个骨干、每个臂使用新目录和单写者锁。恢复时重新直读原 Parquet 并复算规范顺序摘要；只允许同一目录、同一配置哈希、同一输入收据、同一骨干和同一臂恢复。任何字段不符立即退出，不提供“忽略差异”开关。
7. **旧结果：** 不改写历史 JSON，不把旧 `krand`、顺序样本或 `0.5` 数值导入新主表。若需要并列展示，只能标 `legacy_duplicate_distribution`、`legacy_order_sample`、`legacy_threshold_0p5` 和原运行身份。
8. **缺失年份与部分运行：** 不允许静默跳过。单臂失败可恢复该臂；缺臂只阻断依赖该臂的差异，缺目标单元只阻断该单元及汇总，缺 T25 或五臂不全使完整六年／完整五臂裁决为 `incomplete`。这些缺口不得抹去已经合法完成的单臂训练、评分和不依赖缺项的点值。

---

## 五、分步实施任务

`implementation_progress.md` 保留的是禁止物化裁决前建立的八任务台账；下表只解释编号迁移，不改变该台账的历史状态。后续派发须同时写“旧台账任务／本计划任务”，避免把旧任务 3（共享编辑）误当成本计划任务 3（两骨干训练）。

| 旧八任务台账 | 本计划五任务 | 当前处置 |
| --- | --- | --- |
| 旧任务 1：配置与共享合同 | 新任务 1：直读合同与统一加载器 | 已验收四文件保留，按直读语义最小适配。 |
| 旧任务 2：成员与物化 | 新任务 1：直读合同与统一加载器 | 旧物化派工已取消；职责缩为运行时 `unique()`、固定哈希选择、精确计数状态和容量收据。 |
| 旧任务 3：共享编辑 | 新任务 2：共享编辑纯函数 | 按需编辑，不依赖旧任务 2 的落盘成员。 |
| 旧任务 4：DRIFT 训练；旧任务 5：B-ResNet 训练 | 新任务 3：两骨干单臂训练 | 两条实现链仍使用独立入口和运行身份；B 臂修复已验收但真实训练未重跑。 |
| 旧任务 6：统一阈值与评价 | 新任务 4：统一直读评价 | 改为运行时选择／编辑后输出允许的预测结果。 |
| 旧任务 7：配对比较与统计 | 新任务 5：配对统计、报告与恢复卡 | 统计职责不变，效应命名按本计划 §3.6 修正。 |
| 旧任务 8：恢复卡写回 | 新任务 5：配对统计、报告与恢复卡 | 仍只由主代理按已验证节点写回，不交给实现代理。 |

### 任务 1：直读合同与统一加载器

**文件：** 最小修改已验收的三份 JSON 与 `tools/ch3_drift_formal_contract.py`；新建 `tools/ch3_drift_formal_data.py`、`scripts/remote_launchers/run_ch3_drift_formal_input_audit_v1.sh`。

**动作：** 删除 `materialize` 能力，冻结 `direct_parquet_read_only`；按输出角色拒绝派生数据和索引，同时白名单允许结果模式的预测、效应、模型、断点和统计收据。实现原 Parquet 批扫描、运行时源 `unique()`、目标固定哈希前 200000、独立的目标总体精确唯一计数、输入／重合／冲突收据和容量前检。先在本机开发区跑真实短 CPU 检查，再在服务器扫描完整 30 文件；两处均不写数据副本。

**验收：** 现有三份 JSON 数值与角色不变；合同入口拒绝 `--materialize`、`member_seed` 和派生数据路径，但接受精确白名单结果路径；已存在的原文件只读，缺失角色准确登记且只阻断依赖阶段；目标选择常驻集合不超过 200000；源全量与目标总体精确计数分别有内存上界和 cgroup 容量收据。精确操作若容量不足，按依赖范围明确阻断而非落盘；固定哈希选择不因总体计数失败而改变。

### 任务 2：共享编辑纯函数

**文件：** 新建 `tools/ch3_drift_formal_edit.py`。

**动作：** 实现第三节的单实体共享流纯函数；输入 exact eSLD，返回三档当前批内字符串、预算和哈希。对真实 T17 DGA 验证实体检查异字符、位置不重复、汉明距离、前缀嵌套和短域退化，只写聚合审计 JSON。

**验收：** 同一 revision／eSLD 在不同调用顺序和进程中得到相同三档根摘要；无 `krand`、MaskDGA、自由种子、攻击 Parquet 或缓存目录。

### 任务 3：两骨干单臂训练

**文件：** 新建 `tools/ch3_drift_official_p2p3_formal.py`、`tools/ch3_drift_bresnet_p2p3_formal.py` 及各自薄启动器。

**动作：** DRIFT 精确迁移 A/B/D/F/G 臂公式与优化语义；BResNet 正式入口迁移已验收的 B 臂修复及既有 A/D/G/F。每个进程只训练一个臂，直接加载内存 `SourceStore`，不写训练／验证副本、增强域名缓存或随机顺序索引。两骨干消费相同规范顺序摘要；断点沿用每 2000 批及轮末的保存时点，但不得把保存 RNG 状态写成已解决缓存增强臂的精确恢复。

**验收：** 只有当前训练臂所需源容量前检通过才在服务器启动该臂全量。无增强缓存依赖的路径须由真实短步证明保存、退出并从下一批恢复；任何依赖内存增强缓存的路径，在独立精确恢复简报和真实中断证据通过前标为 `blocked_pending_augmentation_cache_resume_contract`，但不拖住直读接口及不依赖该缓存的训练臂。断点绑定原文件、规范唯一实体顺序、配置、骨干和臂。源重合未决不阻塞训练，但不得据此声称验证独立。

### 任务 4：统一直读评价

**文件：** 新建 `tools/ch3_drift_formal_models.py`、`tools/ch3_drift_formal_evaluate.py`、`scripts/remote_launchers/run_ch3_drift_formal_evaluation_v1.sh`。

**动作：** 每个骨干／臂固定评分批量、精度和环境；直读共同源良性并逐臂冻结 0.1%／1% 阈值；逐年、逐类重新扫描目标原文件，在内存中选固定成员，对 DGA 即时生成三档编辑并评分。只输出允许的逐样本预测、阈值、指标、收据与评价断点；预测行不保存原域名或攻击字符串。

**验收：** 每臂 `selected_member_root_sha256`、`attack_stream_id` 和 `output_sha256` 与其他臂一致，T20–T25 六年干净／三档完整；纯 DGA 指标模式合法。源重合政策未决时校准资格明确受阻，但分数与诊断结果可留存。旧检查点只作 `engineering_only` 入口检查，不进入正式汇总。

### 任务 5：配对统计、报告与恢复卡

**文件：** 新建 `tools/ch3_drift_formal_compare.py`、实施报告；恢复卡仅由主代理按证据节点更新。

**动作：** 读取五臂逐样本预测，先核对成员／编辑主键和输入收据，再计算 F−B、D−B、D−A、F−D、G−A 与 A/D/G/F 交互项；D−B 的字段和表头固定标为“相对朴素增广的整套选择训练差异”。先输出逐实体效应；只有 `paired-resampling-contract.json` 冻结后才运行区间。为后续 `Uniform-q`、`CE-top-q` 控制保留有意义展示名及候选池／配额收据的消费接口，但本任务不扩展五臂训练。实施报告列修改文件、配置哈希、直读与容量收据、短步身份、未决资格和未执行项；正式结果另经 `results-analysis` → `results-report`。

**验收：** 任一行不配对、输入哈希不同、阈值来源错臂或单元缺失时数据状态非 `complete`。重采样合同缺失只阻断区间，不补造整数或淘汰门。实现代理不得把工程通过写成实验支持。

---

## 六、最小静态、入口与真实数据验证

### 6.1 禁止项

- 不创建或运行人工夹具、单元测试、集成测试。
- 不运行 `black`，不因格式化延迟真实数据验证。
- 不用系统裸 `python3`，不新建环境，不在服务器运行 `uv sync`。
- 不用 `pdftotext`，不上传本地原文到未经授权的第三方服务。
- 不运行历史 `server_launch_p2p3.sh`，不直接启动远程 `nohup`，不让一个 Python 进程顺序创建多个 SwanLab 正式运行。
- 不创建成员、源训练／验证或攻击派生数据集，不创建磁盘索引、数据库、缓存分区或新增 Rust 工程；审计输出限小型收据。
- 不读取目标结果后改变成员、攻击、源阈值、训练预算、重采样规则或停止条件。合同允许目标知情候选／配置选择，但选择后必须创建新配置与运行身份、披露所见结果和全部被比较候选，且不得把同一目标面板重述为独立最终测试。

### 6.2 实现后最小检查命令

从 `thesis/experiments/llm_probe` 执行，Python 缓存写入临时目录：

```bash
PYTHONPYCACHEPREFIX=/tmp/ch3-drift-formal-pycache \
  /opt/miniconda3/envs/rwkv/bin/python -m py_compile \
  tools/ch3_drift_formal_contract.py \
  tools/ch3_drift_formal_data.py \
  tools/ch3_drift_formal_edit.py \
  tools/ch3_drift_formal_models.py \
  tools/ch3_drift_official_p2p3_formal.py \
  tools/ch3_drift_bresnet_p2p3_formal.py \
  tools/ch3_drift_formal_evaluate.py \
  tools/ch3_drift_formal_compare.py

/opt/miniconda3/envs/rwkv/bin/python tools/ch3_drift_formal_data.py --help
/opt/miniconda3/envs/rwkv/bin/python tools/ch3_drift_formal_edit.py --help
/opt/miniconda3/envs/rwkv/bin/python tools/ch3_drift_formal_contract.py --help
/opt/miniconda3/envs/rwkv/bin/python tools/ch3_drift_official_p2p3_formal.py --help
/opt/miniconda3/envs/rwkv/bin/python tools/ch3_drift_bresnet_p2p3_formal.py --help
/opt/miniconda3/envs/rwkv/bin/python tools/ch3_drift_formal_evaluate.py --help
/opt/miniconda3/envs/rwkv/bin/python tools/ch3_drift_formal_compare.py --help

bash -n scripts/remote_launchers/run_ch3_drift_formal_input_audit_v1.sh
bash -n scripts/remote_launchers/run_ch3_drift_official_p2p3_formal_v3.sh
bash -n scripts/remote_launchers/run_ch3_drift_bresnet_p2p3_formal_v1.sh
bash -n scripts/remote_launchers/run_ch3_drift_formal_evaluation_v1.sh
```

这一步只证明语法、导入和入口可用，不是科学验证。不得运行 `black` 或其他自动格式化器；JSON 只做解析与严格模式检查，不能因格式化延迟真实数据验证。

### 6.3 真实数据直读与开发区验证命令

所有远程命令最终必须经薄启动器调用 `scripts/remote_launchers/launch_run_with_pull.sh`，凭据只来自既有环境。实现完成后，薄启动器应支持下列确定命令：

```bash
cd /Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe

/opt/miniconda3/envs/rwkv/bin/python tools/ch3_drift_formal_data.py \
  --config configs/ch3-drift-formal-evaluation-v1.json \
  --run-dir runs/diagnostics/ch3-drift-formal-direct-read-local-v1 \
  --audit --scope development

/opt/miniconda3/envs/rwkv/bin/python tools/ch3_drift_formal_edit.py \
  --config configs/ch3-drift-formal-evaluation-v1.json \
  --run-dir runs/diagnostics/ch3-drift-formal-t17-nesting-local-v1 \
  --audit --scope t17-validation

bash scripts/remote_launchers/run_ch3_drift_formal_input_audit_v1.sh \
  ch3-drift-formal-capacity-preflight-v1 --capacity-preflight

bash scripts/remote_launchers/run_ch3_drift_formal_input_audit_v1.sh \
  ch3-drift-formal-input-audit-full-v1 --audit-full

bash scripts/remote_launchers/run_ch3_drift_official_p2p3_formal_v3.sh \
  A ch3-drift-official-a-recovery-smoke-v3 --engineering-short-step

bash scripts/remote_launchers/run_ch3_drift_formal_evaluation_v1.sh \
  drift A ch3-drift-formal-eval-drift-a-t20-smoke-v1 --engineering-t20
```

本机两条命令只读冻结开发区真实数据，验证接口和 T17 嵌套，不缩小正式成员预算或形成论文结果。服务器 `--audit-full` 对 30 个角色逐项扫描，存在缺口也写出各角色 `complete|blocked` 的输入／冲突／重合聚合收据；`--capacity-preflight` 只读真实批次并测量内存结构，不写索引。全输入收据不完整只按 §3.1 传播到依赖阶段。`--engineering-short-step` 和 `--engineering-t20` 使用真实数据／模型，分别检查无增强缓存路径的基础恢复入口和直读评价；缓存增强臂的正式恢复仍受 §4 独立实施简报约束。所有开发检查写 `engineering_only=true`，不得被正式比较器消费。

真实快速门至少确认：

- 原 Parquet 以只读方式打开，运行目录没有任何派生数据或索引文件；
- 门禁按角色拒绝数据副本并接受白名单结果模式的 `entity-scores.parquet`／`entity-effects.parquet`；
- 目标选择的成员根摘要与运行时编辑哈希可确定性复算；
- 前 200000 选择与总体唯一计数状态分离；总体计数缺失时 `release_weighted` 不产生数值；
- 源内存结构有严格 `required_peak_bytes`，cgroup 容量满足；否则正式训练明确阻断；
- 断点从下一批恢复，无重复样本曝光；
- 模型分数有限且方向正确；
- 逐臂两个阈值满足实际 FP 上限；
- T20 干净与三档攻击行数、成员主键完全配对；
- 回传守护存活且轻量状态、日志、清单已落本机。

同时分别记录原文件扫描／源 `unique()`、目标内存选择／即时编辑、DRIFT 单批与断点保存、BResNet 单批与断点保存、逐实体评分的真实墙钟时间、吞吐、cgroup 峰值、GPU 峰值和结果字节数。只有这些收据齐全后，才能计算各阶段资源预算与预计完成时间；不得预填猜测工期。不同骨干单独估算，首轮初始化与稳态吞吐分开记录。

任一项失败，回到原实现代理依据真实制品一次只修一个变量；不得另造测试夹具绕开。

---

## 七、正式启动顺序、命令和制品路径

### 7.1 固定运行目录

相对 `thesis/experiments/llm_probe`：

```text
runs/diagnostics/ch3-drift-formal-capacity-preflight-v1/
runs/diagnostics/ch3-drift-formal-input-audit-full-v1/
runs/diagnostics/ch3-drift-official-{a,b,d,g,f}-formal-v3/
runs/diagnostics/ch3-drift-bresnet-{a,b,d,g,f}-formal-v1/
runs/diagnostics/ch3-drift-formal-eval-drift-{a,b,d,g,f}-v1/
runs/diagnostics/ch3-drift-formal-eval-bresnet-{a,b,d,g,f}-v1/
runs/diagnostics/ch3-drift-formal-comparison-drift-v1/
runs/diagnostics/ch3-drift-formal-comparison-bresnet-v1/
```

前检／审计目录只保存输入、容量、计数、根摘要和资格状态 JSON／JSONL 收据，不含成员行、域名、攻击字符串、派生 Parquet 或索引。训练目录保存合法断点、模型、训练摘要、SwanLab 轻量制品和资源日志。评价目录保存允许的逐实体预测、阈值、指标、类别比例和收据。比较目录保存允许的逐实体效应、汇总与重采样状态。

精确相对产物路径如下，其中 `{backbone}`、`{arm}` 只能取配置允许值：

```text
runs/diagnostics/ch3-drift-formal-capacity-preflight-v1/capacity-preflight.json
runs/diagnostics/ch3-drift-formal-capacity-preflight-v1/resource.jsonl
runs/diagnostics/ch3-drift-formal-input-audit-full-v1/input-receipt.json
runs/diagnostics/ch3-drift-formal-input-audit-full-v1/source-read-receipt.json
runs/diagnostics/ch3-drift-formal-input-audit-full-v1/overlap-conflict-audit.json
runs/diagnostics/ch3-drift-formal-input-audit-full-v1/target-selection-receipt.json
runs/diagnostics/ch3-drift-formal-input-audit-full-v1/target-unique-count-receipt.json
runs/diagnostics/ch3-drift-formal-input-audit-full-v1/qualification-policy-receipt.json

runs/diagnostics/ch3-drift-official-{arm}-formal-v3/checkpoint/checkpoint.pt
runs/diagnostics/ch3-drift-official-{arm}-formal-v3/model.pt
runs/diagnostics/ch3-drift-official-{arm}-formal-v3/training-summary.json
runs/diagnostics/ch3-drift-official-{arm}-formal-v3/resource.jsonl
runs/diagnostics/ch3-drift-bresnet-{arm}-formal-v1/checkpoint/checkpoint.pt
runs/diagnostics/ch3-drift-bresnet-{arm}-formal-v1/model.pt
runs/diagnostics/ch3-drift-bresnet-{arm}-formal-v1/training-summary.json
runs/diagnostics/ch3-drift-bresnet-{arm}-formal-v1/resource.jsonl

runs/diagnostics/ch3-drift-formal-eval-{backbone}-{arm}-v1/entity-scores.parquet
runs/diagnostics/ch3-drift-formal-eval-{backbone}-{arm}-v1/thresholds.json
runs/diagnostics/ch3-drift-formal-eval-{backbone}-{arm}-v1/metrics.json
runs/diagnostics/ch3-drift-formal-eval-{backbone}-{arm}-v1/manifest.json

runs/diagnostics/ch3-drift-formal-comparison-{backbone}-v1/entity-effects.parquet
runs/diagnostics/ch3-drift-formal-comparison-{backbone}-v1/comparison.json
runs/diagnostics/ch3-drift-formal-comparison-{backbone}-v1/resampling-status.json
runs/diagnostics/ch3-drift-formal-comparison-{backbone}-v1/paired-resampling-contract.json
runs/diagnostics/ch3-drift-formal-comparison-{backbone}-v1/paired-intervals.json
runs/diagnostics/ch3-drift-formal-comparison-{backbone}-v1/precision-audit.json
```

`qualification-policy-receipt.json` 与 `paired-resampling-contract.json` 为条件文件：主代理尚未冻结时可缺失，但状态必须明确为相应主张／区间被阻断，不能创建空文件冒充批准。运行目录若出现成员、源副本、攻击数据、磁盘索引或缓存分区，统一门禁必须失败。

### 7.2 启动顺序

1. **只读远端身份核验：** 先查现有代理／持久会话／GPU 进程／磁盘，核对服务器根目录、激活脚本、锁文件和 cgroup；不得因看不到本机会话而重复启动。
2. **容量前检：** 在服务器只读真实批次，测定源内存唯一化、顺序向量、模型和批缓存上界；不足则停止依赖该结构的全量训练，不创建磁盘替代。MP 第 3 轮继续按原身份运行。
3. **全输入审计：** 直读 30 文件，完成角色／哈希／模式、源重复／冲突／训练—验证重合及目标选择根摘要；容量允许时另做年度总体精确唯一计数，只写收据。目标文件缺口只阻断相关评价单元和完整六年裁决，不阻断源侧条件已满足的单臂训练；总体计数不足只阻断 `release_weighted`，新实体与 family 未决只阻断对应分面，均不阻断官方固定成员的年度主评价。
4. **DRIFT 基线：** 依次启动 A、B；每臂完成即按原文件重新直读评价，不能提前改合同。
5. **DRIFT 组件臂：** 依次启动 D、G、F；单 GPU 不并发。五臂完成后比较。
6. **第二骨干：** 各运行重新直读同一原文件并核对输入／成员根摘要，依次运行 A、B、D、G、F 及评价；不拿 DRIFT 结果填补失败单元。
7. **结果分析：** 两骨干完整后执行 `results-analysis` → `results-report`，再由主代理裁决“实验支持／实验否决／未分辨”。

### 7.3 正式命令

以下薄启动器和参数均为**拟实现接口**，不是当前仓库已有事实；实现验收后才能执行。已核验的现有统一入口签名为：

```text
bash scripts/remote_launchers/launch_run_with_pull.sh <config_path> <run_id> [run_args] [python_entrypoint]
```

每个拟实现薄启动器只能按固定映射填入上述四类参数，不得绕开该入口。

输入与容量前检：

```bash
bash scripts/remote_launchers/run_ch3_drift_formal_input_audit_v1.sh \
  ch3-drift-formal-capacity-preflight-v1 --capacity-preflight

bash scripts/remote_launchers/run_ch3_drift_formal_input_audit_v1.sh \
  ch3-drift-formal-input-audit-full-v1 --audit-full
```

DRIFT 每臂分别执行，运行失败后只对同一身份使用 `--resume`：

```bash
bash scripts/remote_launchers/run_ch3_drift_official_p2p3_formal_v3.sh A ch3-drift-official-a-formal-v3 --run
bash scripts/remote_launchers/run_ch3_drift_official_p2p3_formal_v3.sh B ch3-drift-official-b-formal-v3 --run
bash scripts/remote_launchers/run_ch3_drift_official_p2p3_formal_v3.sh D ch3-drift-official-d-formal-v3 --run
bash scripts/remote_launchers/run_ch3_drift_official_p2p3_formal_v3.sh G ch3-drift-official-g-formal-v3 --run
bash scripts/remote_launchers/run_ch3_drift_official_p2p3_formal_v3.sh F ch3-drift-official-f-formal-v3 --run
```

每个训练目录 `complete` 后分别评分：

```bash
bash scripts/remote_launchers/run_ch3_drift_formal_evaluation_v1.sh drift A ch3-drift-formal-eval-drift-a-v1 --run
bash scripts/remote_launchers/run_ch3_drift_formal_evaluation_v1.sh drift B ch3-drift-formal-eval-drift-b-v1 --run
bash scripts/remote_launchers/run_ch3_drift_formal_evaluation_v1.sh drift D ch3-drift-formal-eval-drift-d-v1 --run
bash scripts/remote_launchers/run_ch3_drift_formal_evaluation_v1.sh drift G ch3-drift-formal-eval-drift-g-v1 --run
bash scripts/remote_launchers/run_ch3_drift_formal_evaluation_v1.sh drift F ch3-drift-formal-eval-drift-f-v1 --run
bash scripts/remote_launchers/run_ch3_drift_formal_evaluation_v1.sh drift all ch3-drift-formal-comparison-drift-v1 --summarize
```

BResNet 使用同样顺序：

```bash
bash scripts/remote_launchers/run_ch3_drift_bresnet_p2p3_formal_v1.sh A ch3-drift-bresnet-a-formal-v1 --run
bash scripts/remote_launchers/run_ch3_drift_bresnet_p2p3_formal_v1.sh B ch3-drift-bresnet-b-formal-v1 --run
bash scripts/remote_launchers/run_ch3_drift_bresnet_p2p3_formal_v1.sh D ch3-drift-bresnet-d-formal-v1 --run
bash scripts/remote_launchers/run_ch3_drift_bresnet_p2p3_formal_v1.sh G ch3-drift-bresnet-g-formal-v1 --run
bash scripts/remote_launchers/run_ch3_drift_bresnet_p2p3_formal_v1.sh F ch3-drift-bresnet-f-formal-v1 --run

bash scripts/remote_launchers/run_ch3_drift_formal_evaluation_v1.sh bresnet A ch3-drift-formal-eval-bresnet-a-v1 --run
bash scripts/remote_launchers/run_ch3_drift_formal_evaluation_v1.sh bresnet B ch3-drift-formal-eval-bresnet-b-v1 --run
bash scripts/remote_launchers/run_ch3_drift_formal_evaluation_v1.sh bresnet D ch3-drift-formal-eval-bresnet-d-v1 --run
bash scripts/remote_launchers/run_ch3_drift_formal_evaluation_v1.sh bresnet G ch3-drift-formal-eval-bresnet-g-v1 --run
bash scripts/remote_launchers/run_ch3_drift_formal_evaluation_v1.sh bresnet F ch3-drift-formal-eval-bresnet-f-v1 --run
bash scripts/remote_launchers/run_ch3_drift_formal_evaluation_v1.sh bresnet all ch3-drift-formal-comparison-bresnet-v1 --summarize
```

薄启动器须把上述身份映射到固定配置和固定输出目录，拒绝任意路径、额外臂和覆盖参数。远端实际入口始终为：

```text
source tools/env/activate.sh
uv run --no-sync python <固定入口> --config <固定配置> <固定模式>
```

---

## 八、恢复卡更新节点

恢复卡只在以下节点更新，且每次附原始制品路径与状态：

1. **实施验收完成：** 写“评价接口已实现、真实快速门通过”，列修改文件和快速运行目录；状态仍为“实验待证”。
2. **直读输入与容量审计完成：** 写 30 个原文件完整性、输入收据哈希、源规范唯一化／重合／冲突状态、目标入选成员根、编辑算法哈希、各精确操作容量和阻断范围。目标年度总体唯一计数只有整集合精确统计成功后才登记；失败只阻断 `release_weighted` 及相应总体计数主张。新实体候选另写资格审计及“待裁决／已冻结”状态；只影响候选资格的问题不冒充整条训练路线失败。
3. **每个正式训练臂完成：** 写骨干、臂、配置哈希、检查点哈希、SwanLab 身份、训练状态和评价目录；不摘录单个有利数字代替整套结果。
4. **每个骨干五臂比较完成：** 写全单元完整性、效应与区间制品路径、精度状态；区间跨零写“未分辨”，负效应逐项保留。只有指标角色合同已冻结且该项属于其否决范围时，才写候选证伪证据。
5. **双骨干分析裁决完成：** 经 `results-analysis` → `results-report` 后，才更新 F 的“实验支持／实验否决／未分辨”状态及下一动作。

任何中间节点不得改写 DRIFT 路线总控中的公共科研合同；只有新实验导致跨章裁决变化时，主代理才同步总控。

---

## 九、停止条件与裁决边界

### 9.1 工程停止

遇到以下任一项，停止受影响阶段并保留诊断制品：

- 30 文件角色、revision、路径、模式或哈希不完整；
- exact eSLD 无效、跨类标签冲突、成员摘要碰撞，或声明为 `complete` 的精确成员计数不守恒；
- 输出角色为成员／源／攻击副本、磁盘索引、数据库或缓存分区，或结果 Parquet 不符合白名单模式；
- 攻击预算、汉明距离、共享流前缀或复算哈希不一致；
- 训练配置、输入清单、断点、骨干、臂或单写者身份冲突；
- 恢复重复／漏过批次，断点间隔超过合同，cgroup 内存逼近上限且无法在不改科研顺序的前提下降低；
- SwanLab 预检失败、回传守护未存活、服务器唯一副本风险未消除；
- 分数非有限、概率方向错误、逐臂阈值 FP 超预算、结果模式出现非法指标；
- 配对主键、成员、攻击或阈值来源不一致；
- 缺 T25 时阻断完整六年裁决，缺正式臂时阻断依赖该臂的差异和完整五臂裁决，需要区间时配对重采样合同／精度状态不合格则只阻断相应区间；均不撤销其他已合法完成的单臂训练、评分或点值。

工程失败不算科学否决。修复必须回到同一实现代理，一次只改变一个工程变量；若修复会改变训练、成员、攻击或指标科研合同，则停止并交主代理／用户重新裁决。

### 9.2 科研停止

- 主任务指标与论文呈现合同已由主代理核验；它冻结指标角色和呈现原则，但未设定的数值门不自动生效。有效正式结果据此判断 F 的作用范围。
- 不得要求 F 在所有指标、所有年份逐项超过 B，也不得把每个目标年的 FPR 不高于源侧 `alpha` 设为自动硬门。辅助与任务外指标完整报告，但其负向变化本身不默认淘汰；若主任务提升伴随干净性能代价，须用 Standard／对抗训练基线区分并以真实对照证据解释，不能只靠措辞豁免。
- D−B 只能裁决相对朴素增广的整套选择训练差异，不能单独支持或否定组中心化／纯选择器贡献；纯选择器须等待同候选池同配额的 `Uniform-q` 与 `CE-top-q`。D−A、F−D、G−A 或 A/D/G/F 交互项在已冻结的相应机制指标上否定主张时，缩小或否决对应组件主张，不用另一个实现的旧读数辩护；辅助指标的反向变化只记录和解释，不越权改写其角色。
- 配对区间跨零或数值精度未解决：标“未分辨”，不得称等效、非劣或有效；尚无已冻结重采样合同时只报告点值和逐实体制品，不用临时区间裁决。
- 只有完成双骨干、完整 T20–T25、全部三档攻击和预注册指标后，才允许讨论迁移性；单骨干信号不能替代第二骨干。

### 9.3 明确不得实施的变更

- 不新增攻击档位、随机重复、`member_seed`、自适应攻击、MaskDGA 或家族筛选。
- 不改变每年每类 200k 上限、哈希排序、exact eSLD 去重、共同源良性成员或逐臂阈值规则。
- 正式源数据在每次运行中按规范合并后 `unique()` 并核对顺序根摘要，不再改变训练臂公式、训练种子、唯一实体曝光、预算、公平对照和内部 `0.5` 分支逻辑；旧脚本的重复曝光属于本计划明确纠正的历史偏离，不作为必须保留的合同。
- 不预生成或落盘成员、源训练／验证副本和攻击数据，不创建磁盘索引、缓存分区、数据库或新 Rust 工程；确切内存算法不可行时按受影响操作失败关闭并交用户裁决。
- 不把 T20–T25 标签或样本写入静态训练、早停或源阈值冻结。允许其参与已披露的目标知情候选／配置比较；每次修订必须生成新配置、新运行身份和选择记录，完整保留反向结果，并取消独立最终测试表述。
- 不迁移旧 v1/v2 断点为合法新断点，不改写旧结果，不跨实现沿用未复测读数。
- 不把工程短步、目标 oracle、legacy 诊断或单比例精度写成 F 的正式有效性证据。

---

## 十、交付验收清单

- [ ] 已验收三份配置与合同模块完成最小直读适配，科研数值和角色不变；配置严格、无未知键、无 `member_seed`／`materialize`，并记录规范哈希。
- [ ] 30 个真实输入角色及 SHA-256 完整，T20–T25 无缺年。
- [ ] 共同源按官方合并后规范 `unique()` 直读构建，源冲突／重合审计与处置分离；容量不满足时不创建磁盘替代。
- [ ] 官方年度目标按运行时固定哈希选择至多 200000 个唯一实体；入选根可复算。年度总体精确唯一计数另有独立状态，缺失时不生成 `release_weighted` 或编造总体重复数。
- [ ] 六年 DGA 三档攻击由同一纯函数在评价批内生成，跨骨干／跨臂以成员主键、输入哈希和编辑流哈希严格配对，短域退化如实记录，不落盘攻击数据集。
- [ ] 新实体与 family 资格未决只阻断对应分面或主张，不改变官方面板、MP 成员和既有运行身份。
- [ ] DRIFT 与 BResNet 均为 A/B/D/F/G 单臂单进程，断点、SwanLab、资源和回传身份完整。
- [ ] 旧检查点只作审计／工程冒烟，正式比较只接受新合法完整检查点。
- [ ] 每臂分别在同一源良性成员上冻结 0.1%／1% 阈值，FP 预算机械断言通过。
- [ ] 逐年干净和三档攻击逐实体结果完整，T25 必报，纯 DGA 单元不存在非法混合类别指标。
- [ ] 本次五臂的 F−B、D−B、D−A、F−D、G−A 与 A/D/G/F 交互项完全配对并保存逐实体长表；D−B 未被误称纯组件或筛选器效应。重采样收据未冻结则明确阻断区间，已冻结则精度通过或明确标记未解决。
- [ ] 语法、导入、命令入口、Shell 语法通过；未运行 `black`、人工测试或集成测试。
- [ ] 真实 T20 复算、真实短步恢复和真实单臂评价门通过后才启动正式顺序。
- [ ] 实施报告与恢复卡按证据节点更新，F 在正式统计完成前保持“实验待证”。

本计划不授权 Git 提交、推送或合并；版本控制动作由主代理另行处理。
