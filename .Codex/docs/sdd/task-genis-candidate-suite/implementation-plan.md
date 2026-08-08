# GeNIS 候选协议物化实施计划

> **执行要求**：必须使用 `subagent-driven-development` 逐任务实施并由新的审查代理检查。实现代理可按 `thesis/experiments/llm_probe/AGENTS.md` 使用一次测试驱动开发。所有复现测试仅在服务器 `uv` 环境执行。

**目标：** 从已追溯的 GeNIS v3 物化文件和其绑定会话分配生成 `data-protocol-v1.0-rc1` 候选协议，冻结家族、子类、时间前向与未知子类清单，并为统一树模型验证入口提供严格无精确观测交叉的训练/验证清单。

**架构：** 新模块只消费旧 JSONL、`materialization_summary.json`、绑定的 `session_assignments.jsonl` 与 `plan_summary.json`。它在内存中连接哈希会话元数据，改写不安全的旧 `sample_id`，展平八个公共观测字段及缺失掩码，写入统一 `samples.parquet`、字段角色、标签合同、不可变清单与审计；不修改旧输入和任何 TQH-C2 目录。

**技术栈：** Python 3.10、Pandas、PyArrow、PyYAML、现有 `flow_probe.frozen_protocol`、Pytest、Black、Ruff。

## 全局约束

- 候选常量固定为 `data-protocol-v1.0-rc1`、`provisional`、`theory_selection`、`review_pending`、`dataset-candidate-genis-v0`。
- 家族开发套件名固定为 `genis_family_development`，子类开发套件名固定为 `genis_subtype_development`，开放集套件名固定为 `genis_subtype_open_set`。
- 开放集只表示未知子类；三个留出标签固定为 `dos-icmp`、`dos-pushack`、`dos-udp`，不得写成未知家族。
- 旧 `sample_id` 只可用于内存中生成 `genis:` 加 SHA-256 的新稳定标识，不得写入任何候选制品；输入文件名和路径只允许出现在来源谱系审计，不得进入主记录、清单或模型视图。
- 树视图仅包含八个公共数值观测和对应八个缺失掩码；提示词、补全文本、文件名、路径、会话号、时间、标签和排除原因不得进入模型视图。
- 主验证清单排除观测签名已在训练出现的记录；主表保留这些记录并写明 `development_eligible=false` 与固定排除原因。
- 时间前向测试和开放集清单只冻结，不进入本轮验证基线；候选协议禁止 `final_tuning` 与最终测试结论。
- 不修改 `pyproject.toml`、`uv.lock`、`frozen_protocol.py`、`tabular_baselines.py`、`tqh_c2_candidate.py` 或任何 TQH-C2 运行目录。
- 持久化制品不得写运行时间、随机值、绝对输入路径或绝对输出路径；来源谱系只写输入根内相对路径、大小和 SHA-256，以保证双份逐字节确定性与可迁移性。
- 不切换分支、不提交、不暂存、不回滚共享工作树中的其他改动。

---

### Task 1（任务一）：实现确定性 GeNIS 候选协议物化器

**文件：**
- 新建：`thesis/experiments/llm_probe/src/flow_probe/genis_candidate.py`
- 新建：`thesis/experiments/llm_probe/tests/test_genis_candidate.py`
- 不修改其他生产文件或测试文件。

**接口：**

```python
def materialize_candidate(
    *,
    prepared_dir: Path,
    assignments_path: Path,
    plan_summary_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    """生成 GeNIS 理论筛选候选协议；输出目录必须不存在。"""
```

模块必须提供 `build_parser()` 和 `main()`，支持：

```text
python -m flow_probe.genis_candidate \
  --prepared-dir <目录> \
  --assignments <session_assignments.jsonl> \
  --plan-summary <plan_summary.json> \
  --output-dir <新目录>
```

**输入验证：**

- [ ] 要求 v3 目录含 `train.jsonl`、`validation.jsonl`、`test.jsonl`、三个 `ood_*.jsonl` 和 `materialization_summary.json`。
- [ ] 要求物化摘要模式为 `genis_materialized_split_v1`，其 `assignment_sha256` 必须等于实际分配文件 SHA-256。
- [ ] 要求计划模式为 `genis_hybrid_forward_split_v1`、比例为 `[0.8, 0.1, 0.1]`、`temporal_order_verified=true`，未知子类集合必须精确等于三个固定标签。
- [ ] 要求两个摘要中的原始来源文件名、大小和 SHA-256 逐项一致。
- [ ] 每条旧记录必须具有预期八字段 `features`、合法 `sample_id`、32 位十六进制 `group_id`、`source_dataset=genis`、合法二元标签和家族标签；数值只能为有限数或 `null`。
- [ ] 每个 `group_id` 必须存在于分配清单，记录所在文件必须与分配值一致；各会话实际行数必须等于分配清单 `row_count`。
- [ ] 按子类重新验证训练、验证、测试的严格时间顺序；验证已知子类在训练和严格验证中均有覆盖，未知子类与训练子类集合不相交。

**主记录：**

- [ ] 新 `sample_id` 使用 `genis:` 加 `sha256("dataset-candidate-genis-v0\\0" + old_sample_id)`，不包含旧标识、文件名、标签或分组值。
- [ ] 从分配清单恢复 `subtype_label`；验证 `family_label` 与子类前缀一致，`binary_label` 与 benign/攻击语义一致。
- [ ] 展平八个观测字段，并为每个字段新增 `<field>_missing` 的 `0/1` 数值掩码；保留缺失观测为 Parquet 空值。
- [ ] `observation_sha256` 只由按固定字段顺序规范化的八个观测值生成；`source_record_sha256` 由旧记录规范化 JSON 生成；`candidate_record_sha256` 由除自身外的候选记录生成。
- [ ] 对训练签名集合命中的验证记录设置 `development_eligible=false` 和 `exclusion_reason=exact_observation_seen_in_train`；其他开发记录为可用，测试与开放集标为仅评估。
- [ ] 按新 `sample_id` 稳定排序后以 Zstandard 压缩写 `samples.parquet`，全部列必须在 `field-roles.yaml` 中恰好分类。

**清单：**

- [ ] `splits/genis-family-development-train.jsonl`：套件 `genis_family_development`、划分 `train`、全部训练记录。
- [ ] `splits/genis-family-development-validation.jsonl`：同套件、划分 `validation`、只含严格验证记录。
- [ ] `splits/genis-family-time-forward-test.jsonl`：同套件、划分 `test`、原时间前向测试记录。
- [ ] `splits/genis-subtype-development-train.jsonl`、`...validation.jsonl`、`genis-subtype-time-forward-test.jsonl`：对应子类套件并复用相同样本顺序。
- [ ] `splits/genis-subtype-open-set-test.jsonl`：套件 `genis_subtype_open_set`、划分 `test`、三个未知子类的聚合清单。
- [ ] 每行写 `protocol_version`、`suite_id`、`split_id`、`sample_id` 和当前 `samples.parquet` SHA-256；不得包含标签。

**附属制品与审计：**

- [ ] 写 `schema.json`、`label-contract.json`、`field-roles.yaml`、`candidate-manifest.json`、`source-artifacts.jsonl`。
- [ ] 写 `audit/input-lineage.json`、`audit/label-coverage.json`、`audit/leakage-audit.json`、`audit/manifest-hashes.json`、`audit/p0-subset.json` 和 `audit/artifact-sha256.txt`。
- [ ] 泄漏审计至少报告旧标识未持久化、候选标识唯一、样本和会话跨开发划分交叉为 0、严格训练/验证精确观测交叉为 0、原验证被排除数量、时间顺序、未知子类隔离、模型字段敏感词命中和所有清单哈希。
- [ ] `protocol.yaml` 登记除自身外全部制品哈希，明确 `final_tuning_allowed=false`、`final_test_claim_allowed=false` 和“测试/开放集未用于当前路线选择”。创建期间写 `_INCOMPLETE`，成功后才删除。

**测试：**

- [ ] 构造不含 `attack_subtype` 的最小 v1 夹具，证明子类由绑定分配清单恢复，而不是从文件名或标签猜测。
- [ ] 证明旧标识包含攻击文件名时，主记录和清单不出现旧标识或源文件名；来源谱系可以记录输入文件名但只能是审计制品；新标识稳定且唯一。
- [ ] 构造训练/验证同观测记录，证明主表保留该验证记录但家族和子类验证清单均排除它，审计交叉计数为 0。
- [ ] 用 `load_frozen_protocol(..., expected_protocol_version="data-protocol-v1.0-rc1", expected_status="provisional", expected_phase="theory_selection")` 加载输出，并分别按 `family_label` 与 `subtype_label` 读取开发清单，验证相同 `sample_id` 顺序和字段预算。
- [ ] 证明开放集清单只含三个未知子类，且其子类集合与训练集合不交叉；标签合同明确它们仍属于已知 `dos` 家族。
- [ ] 对两个新输出目录运行物化，比较全部文件相对路径和字节，要求完全一致。
- [ ] 分别覆盖分配哈希不一致、来源摘要不一致、未知会话、会话行数不一致、文件与 assignment 不一致、时间交叉、非法非有限特征和已存在输出目录的拒绝路径。

**服务器最小验证命令：**

```bash
source ~/.bashrc >/dev/null 2>&1
cd /root/autodl-tmp/thesis/experiments/llm_probe
uv run --no-sync pytest -q tests/test_genis_candidate.py tests/test_frozen_protocol.py tests/test_tabular_baselines.py
```

预期：全部通过，退出码 `0`。

---

### Task 2（任务二）：服务器双份物化与独立审查

**输入：**

```text
runs/data-prepared/genis-hybrid-forward-v1-20260719-v3/
runs/data-splits/genis-hybrid-forward-v1-20260719-v2/session_assignments.jsonl
runs/data-splits/genis-hybrid-forward-v1-20260719-v2/plan_summary.json
```

**输出：**

```text
runs/data-candidate-builds/genis-v0/build-a/
runs/data-candidate-builds/genis-v0/build-b/
```

- [ ] 同一代码与输入分别运行两次，输出目录预先不存在。
- [ ] 比较两目录的相对文件集合和每个文件 SHA-256；必须全部相同。
- [ ] 用冻结协议加载器实际读取家族与子类训练/验证清单；核对严格验证观测交叉为 0。
- [ ] 分派新的审查代理检查任务差异、输入谱系、标签恢复、标识泄漏、字段角色、清单隔离、确定性和测试证据；严重或重要问题必须修复并重审。
- [ ] 审查通过后，把 `build-a` 原子复制到新的 `runs/data-frozen/dataset-candidate-genis-v0/protocol/`；目标存在时拒绝覆盖，不触碰 TQH-C2 目录。

---

### Task 3（任务三）：家族验证树模型基线

**固定配置：**

```text
协议：runs/data-frozen/dataset-candidate-genis-v0/protocol/
训练：splits/genis-family-development-train.jsonl
验证：splits/genis-family-development-validation.jsonl
标签：family_label
阶段：theory_selection
协议版本：data-protocol-v1.0-rc1
调参试次：0，公开默认配置
模型：hgb、xgboost
种子：42、43、44
```

- [ ] HGB 和 XGBoost 分别使用独立 `screen` 会话，每个会话顺序执行三个种子，形成六个唯一输出目录和六个 SwanLab 在线运行。
- [ ] 运行前确认 `swanlab ping` 与 `swanlab verify`，并再次检查磁盘、CPU/GPU 进程和输出路径不存在。
- [ ] 每个运行必须保存配置、环境、协议与清单哈希、预测、指标、成本、控制台日志、SwanLab 日志和 `artifact_manifest.json`。
- [ ] 仅汇总 `validation` 指标；不得加载时间前向测试或开放集清单，不得按任何测试结果选种或改参数。
- [ ] 通过 SwanLab 云端接口核对六个运行均为 `FINISHED`、有指标数据点且图表页可见；记录运行编号和地址。

---

### Task 4（任务四）：结果写回与交付门禁

- [ ] 回收候选协议、六个运行制品和启动日志到对应本地 `runs/` 路径，不覆盖其他任务制品。
- [ ] 对本任务 Python 文件运行一次 Black 与 Ruff，对本任务 Markdown 运行一次 Prettier，并执行 `git diff --check`。
- [ ] 写 `.Codex/docs/sdd/task-genis-candidate-suite/implementation-report.md`、`review.md` 和 `2026-07-24-GeNIS树模型验证基线报告.md`，记录协议/样本哈希、命令配置、三种子指标、日志、服务器与本地路径、SwanLab 运行编号/地址及失败项。
- [ ] 更新 `output/第一创新点实验总控.md` 的数据冻结与基线状态，并链接详细报告；本任务不改变理论路线、章节边界或长期结论时不修改 `output/开题改进交接文档.md`。
- [ ] 重新执行关键加载、哈希与报告路径核验后，才能将任务计划标记完成。
