# TQH-C2 B 受限例外与 A/B/C 统一候选实施计划

> 执行方式：`writing-plans` → `subagent-driven-development` → 最小验证 → 独立审查。实现代理每项任务至多使用一次测试驱动开发工作流；审查代理不得修改代码。

## 目标

在不修改原始数据、不上传原始 PCAP、不覆盖历史 C-only 候选的前提下，安全物化 TQH-C2 B/QUIC 暂定制品，并从 A/B/C 36 个完整 cell 生成可重复的统一候选与四套 cell 级划分。

## 任务 1：实现 B v1.0.1 受限门禁例外

**文件**

- 修改：`thesis/experiments/llm_probe/src/flow_probe/tqh_c2.py`
- 修改：`thesis/experiments/llm_probe/tests/test_tqh_c2.py`
- 写报告：`.Codex/docs/sdd/task-tqh-dataset-download-manager/b-gate-implementation-report.md`

**步骤**

1. 增加显式的 B v1.0.1 允许失败集合与质量接受状态，不使用路径字符串推断版本或 profile。
2. 让 `audit_label_cell`、`audit_profile`、`extract_cell` 和 `materialize_profile` 把声明版本传入同一门禁函数；默认行为继续严格拒绝失败 gate。
3. 在完成 UID、五元组、元数据、合法标签和逐行计数审计后才签发 B 例外接受状态。
4. 强制修订计数逐字段等于逐行重计、`invariant_violations=0`、修订 C2 不低于 50。
5. 把源 gate 状态、失败项、详情、接受原因、修订计数依据和 stale 计数差写入 cell 审计。
6. 添加正向测试以及版本不符、profile 不符、未知失败项、H4/H5/H6 失败、修订计数不符、非法标签、五元组不符、元数据不符和 C2 不足的负向测试。
7. 保留 A/C `PASS` 行为与现有失败 gate 回归测试。

**服务器验收**

```bash
uv run pytest tests/test_tqh_c2.py -q
uv run black --check src/flow_probe/tqh_c2.py tests/test_tqh_c2.py
uv run ruff check src/flow_probe/tqh_c2.py tests/test_tqh_c2.py
```

## 任务 2：独立审查 B 门禁实现

**范围**

- 只读审查任务 1 的差异、测试与报告。
- 重点检查 fail-open、版本/profile 伪造、缺失检查被默认为通过、计数类型绕过、审计字段遗漏和 A/C 回归。
- 严重或重要问题由新的修复代理最小修复并重新执行任务 1 精确测试，再由新的审查代理复核。

**输出**

- `.Codex/docs/sdd/task-tqh-dataset-download-manager/b-gate-review-report.md`

## 任务 3：物化并验收 B/QUIC

**输入**

- 标签根：`raw/datasets/TQH-C2-2026/extracted/`
- PCAP 根：`raw/datasets/TQH-C2-2026/extracted/`
- profile：`B`
- 数据集版本：`1.0.1`

**输出**

- `thesis/experiments/llm_probe/runs/data-frozen/dataset-v1-provisional/tqh-c2-B-20260728-v1/`
- 运行日志：`thesis/experiments/llm_probe/runs/data-downloads/tqh-c2-pcap-20260724/B/process-20260728.log`

**门禁**

1. 输出不存在且本机空间高于停止门槛。
2. 12 个 cell 全部满足 B 受限例外，`_INCOMPLETE` 最终不存在。
3. 主记录 `sample_id` 全局唯一，三个 Parquet/JSON 层级均可读。
4. 审计中保留 12 个 `source_gate_status=FAIL`、允许失败项、修订依据和逐行一致性。
5. 标签分布、包连接率、未匹配/歧义、负时间差和无包会话如实记录。
6. 模型字段敏感命中为 0，所有登记 SHA-256 回读通过。
7. 立即更新状态报告、笔记、计划、实验总控和实验 `AGENTS.md` 防复发规则。

## 任务 4：实现 A/B/C 统一候选物化器

**文件**

- 新增：`thesis/experiments/llm_probe/src/flow_probe/tqh_c2_candidate_abc.py`
- 新增：`thesis/experiments/llm_probe/tests/test_tqh_c2_candidate_abc.py`
- 仅在确需共享且不改变 C-only 输出时修改：`thesis/experiments/llm_probe/src/flow_probe/tqh_c2_candidate.py`
- 写报告：`.Codex/docs/sdd/task-tqh-dataset-download-manager/abc-candidate-implementation-report.md`

**步骤**

1. 读取三个暂定 profile 的主表，验证同一数据版本、profile 集合 A/B/C、每个 profile 12 个 cell、全局 `sample_id` 唯一和固定标签契约。
2. 按 Parquet row group 流式聚合包观测；验证 row group 到 cell 的单值映射、样本/包计数和单 cell 内包序号连续。
3. 复用既有 37 字段聚合和观测序列哈希语义，生成全局唯一候选样本表。
4. 确定性生成 `tqhc2_cell_indomain` 与三个留一 profile suite 的 12 份划分清单。
5. 强制每个 suite 内 cell 互斥、覆盖条件、标签覆盖、manifest 绑定和测试隔离。
6. 分 suite 输出重复签名与 P0 子集审计；残余重复只能被记录，不能静默删除或移动完整 cell。
7. 输出协议、字段角色、组表、来源清单、制品哈希与 `_INCOMPLETE` 失败标记。
8. 添加小型固定夹具，覆盖四套划分、未知标签排除、流式 row group、多 cell 混入拒绝、跨 profile 主键冲突、固定标签错误、包计数错误、可加载性、拒绝覆盖和逐字节复现。

**服务器验收**

```bash
uv run pytest tests/test_tqh_c2_candidate.py tests/test_tqh_c2_candidate_abc.py tests/test_frozen_protocol.py -q
uv run black --check src/flow_probe/tqh_c2_candidate.py src/flow_probe/tqh_c2_candidate_abc.py tests/test_tqh_c2_candidate.py tests/test_tqh_c2_candidate_abc.py
uv run ruff check src/flow_probe/tqh_c2_candidate.py src/flow_probe/tqh_c2_candidate_abc.py tests/test_tqh_c2_candidate.py tests/test_tqh_c2_candidate_abc.py
```

## 任务 5：独立审查统一候选实现

- 新审查代理只读检查任务 4 差异、测试和制品合同。
- 重点检查跨 suite 与 suite 内的样本身份、测试泄漏、row group 边界、标签排除、复现性、内存上界、C-only 回归和来源哈希。
- 输出：`.Codex/docs/sdd/task-tqh-dataset-download-manager/abc-candidate-review-report.md`。
- 严重或重要问题按任务 2 相同机制最小修复并复核。

## 任务 6：双份物化与正式发布

**临时输出**

- `/tmp/tqh-candidate-abc-v0-a-20260728/protocol/`
- `/tmp/tqh-candidate-abc-v0-b-20260728/protocol/`

**正式输出**

- `thesis/experiments/llm_probe/runs/data-frozen/dataset-candidate-tqhc2-abc-v0/protocol/`

**验收**

1. 两份临时输出的全部非自引用制品逐字节一致。
2. `FrozenProtocol` 成功加载 12 份清单，所有清单绑定同一个 samples 哈希。
3. `samples.parquet` 的 `sample_id` 全局唯一且模型字段均为有限数值。
4. in-domain 为 28/4/4 cell，三个留一套件分别为 20/4/12 cell，覆盖合同全部通过。
5. 全部制品哈希回读通过后原子发布，不覆盖已有正式目录。
6. 更新详细报告、实验总控、计划和 `AGENTS.md`；候选仍标记 `review_pending`，原始 PCAP 不上传。

## 任务 7：派生制品服务器同步

只在本地全部验收与独立审查通过后执行：

1. 查询服务器空间与现有目标。
2. 使用明确白名单 `rsync` 同步 B 暂定派生和 A/B/C 候选；禁止 `--delete`，禁止包含原始 PCAP。
3. 回读服务器制品哈希并加载 12 份划分清单。
4. 同步事实写入详细报告与实验总控；不启动 GPU 训练。

## 停止条件

- 原始或派生输入哈希不一致。
- B 出现允许集合外的失败门禁，或任一完整性审计失败。
- 本机空间低于既定停止门槛，或服务器空间低于局部规则门槛。
- row group 无法证明单 cell 归属且实现没有有界内存的安全替代路径。
- 独立审查发现严重或重要问题且尚未修复复核。
- 正式目标目录已存在，无法证明是同字节产物。
