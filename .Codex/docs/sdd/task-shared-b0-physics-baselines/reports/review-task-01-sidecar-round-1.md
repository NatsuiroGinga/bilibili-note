# 共享 B0 物理旁路任务 01 修复轮次 1 独立复审报告

## 结论

- 复审结论：**允许进入服务器目标测试**。
- 放行范围仅限任务 01 的服务器目标测试和真实配置双物化验证；本报告不放行正式训练，也不代表整个共享 B0 物理基线实施计划已经完成。
- 发现统计：严重 0 项，重要 0 项，保留建议 3 项，新增非阻塞建议 1 项。
- 原审查的 5 项重要问题均已在生产逻辑中修复，并有直接覆盖对应失败模式的测试节点。
- 服务器行为测试尚未执行，因此当前状态仍是 `review_pending`，不能把静态复审结果写成行为测试通过。

## 严重

未发现严重问题。

## 重要

未发现新的重要问题。原审查的 5 项重要问题逐项复核如下。

### 1. 来源语义重建：已解决

**生产证据：**

- [`_load_source_records`](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py#L462) 重新读取三个来源 JSONL，核对实际 SHA-256、逐源 807 条、来源划分、唯一标识及与分类标识集合相等。
- [`_physics_record`](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py#L577) 从来源记录重新计算时间锚点、归一化状态和五组累计量。
- [`validate_shared_b0_physics_sidecar`](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py#L1031) 重新加载真实配置和来源，并在 [`_validate_record_semantics`](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py#L1021) 中逐条比较全部必需语义字段，不再只信任清单自报值和数组形状。

**测试证据：**

- [`test_materializes_exact_sidecar_by_sample_id_and_preserves_classification`](/Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_shared_b0_physics_sidecar.py#L370) 手算并固定一条完整输出记录。
- [`test_validator_rebuilds_source_semantics_after_outer_hashes_are_refreshed`](/Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_shared_b0_physics_sidecar.py#L542) 覆盖累计量、来源划分和掩码三类篡改，并同步刷新外层哈希，确保语义门禁独立生效。

### 2. 掩码场景代理变量：已解决

**生产证据：**

- [`_build_state_masks`](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py#L561) 仅对 `42:<sample_id>` 计算 SHA-256 并选择第二锚点；`group_id`、标签、提示词、场景名、来源划分和来源顺序均不参与掩码计算。
- 每条掩码固定为锚点 0 加锚点 1 至 4 中的一个。

**测试证据：**

- [`test_mask_depends_only_on_sample_id_and_seed`](/Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_shared_b0_physics_sidecar.py#L310) 在保持 `sample_id` 不变时改变场景相关字段、来源信息和输入顺序，仍要求掩码逐条相同。

### 3. 三个冻结来源硬绑定：已解决

**生产证据：**

- [`load_shared_b0_physics_sidecar_config`](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py#L309) 要求来源严格按 `train`、`validation`、`test` 登记，且每个来源恰为 807 条。
- [`validate_shared_b0_physics_sidecar`](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py#L1081) 将配置绑定、分类绑定和来源清单与重新加载的真实配置及实际来源结果逐字段比较。

**测试证据：**

- [`test_production_config_freezes_paths_counts_usage_and_source_hashes`](/Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_shared_b0_physics_sidecar.py#L247) 固定生产配置的三个来源四元组、用途、掩码、阶段和状态。
- [`test_config_requires_exactly_807_records_per_source`](/Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_shared_b0_physics_sidecar.py#L294) 拒绝仍保持总数 2,421、但逐源不是 807 条的配置。
- [`test_validator_compares_source_manifest_with_real_config`](/Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_shared_b0_physics_sidecar.py#L576) 拒绝来源清单与真实配置不一致。

### 4. 发布失败破坏预建空目录：已解决

**生产证据：**

- [`materialize_shared_b0_physics_sidecar`](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py#L690) 不再预先删除调用方空目录；独立校验完成后使用一次 `Path.replace` 发布，失败时只清理同级 `.partial`。
- 发布前再次检查目标仍为空或不存在，非空目标继续拒绝覆盖。

**测试证据：**

- [`test_publish_failure_preserves_precreated_empty_directory_and_files`](/Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_shared_b0_physics_sidecar.py#L597) 注入最终重命名失败，断言原空目录保留、`.partial` 清理，并用哨兵文件验证既有内容不被覆盖。
- [`test_two_independent_materializations_are_byte_identical`](/Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_shared_b0_physics_sidecar.py#L699) 同时覆盖预建空目录上的成功发布。

### 5. 精确制品集合和符号链接：已解决

**生产证据：**

- [`_validate_output_tree`](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py#L899) 使用 `lstat` 和不跟随链接的目录项状态，拒绝根及后代符号链接、非普通文件、额外文件和额外目录。
- 实际普通文件集合必须严格等于 `REQUIRED_OUTPUT_FILES`，目录集合也必须严格等于必要父目录集合。
- [`validate_shared_b0_physics_sidecar`](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py#L1204) 还要求 `materialization_audit.required_files` 与规定列表完全相等，并拒绝同级遗留 `.partial`。

**测试证据：**

- [`test_validator_rejects_non_exact_or_linked_output_tree`](/Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_shared_b0_physics_sidecar.py#L631) 覆盖输出根链接、额外文件、分类副本、必要文件链接、异常目录和遗留 `.partial`。
- [`test_validator_requires_exact_materialization_file_set`](/Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_shared_b0_physics_sidecar.py#L679) 固定物化审计的必要文件列表。
- 双物化测试把两个目录的实际文件集合分别与规定集合比较，再逐文件比较字节。

## 建议

### 1. 物理量取值域门禁仍未处理

原审查建议按字段语义拒绝负的队列、接收、出队和丢弃量，并要求包数为非负整数。当前 [`_finite_number`](/Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py#L522) 仍只要求数值有限；容量和归一化尺度已有正值门禁，但其余物理量没有完整取值域检查。

该项按修复简报明确不属于本轮必须修复范围，不阻塞服务器目标测试。真实配置双物化后仍应统计这些字段的最小值和包数整数性；若出现非法值，不得进入训练。

### 2. 阶段、状态和记录模式仍只得到部分固定

生产配置测试已经固定 `theory_selection/review_pending`，但配置加载器仍只要求 `stage/status` 非空。输出记录的 `schema_version` 不在 `REQUIRED_RECORD_FIELDS` 中，校验器也没有拒绝记录额外字段。因此，原建议中的加载器硬门禁、记录模式精确匹配和额外字段拒绝尚未解决。

该项不影响本轮五项重要修复的正确性，但在旁路状态从候选升级为冻结前应处理。

### 3. 解析内容与哈希仍不是同一字节快照

配置、分类 JSONL 和三个来源 JSONL 仍分别执行解析与哈希读取。并发替换发生在两次读取之间时，解析内容与记录哈希理论上可能来自不同快照。原建议尚未处理。

当前来源是冻结只读制品，实际风险有限；服务器物化期间仍应保证来源目录不被其他任务写入，并在物化前后复核来源及分类哈希。

### 4. 建议完整重算连接审计中的自报字段

校验器目前核对 `join_key` 和 `sample_id_sha256`，但没有逐项重算 `classification_record_count`、`source_record_count`、`sidecar_record_count`、四个错误计数、`classification_sha256` 和 `prohibited_join_keys`。修改这些自报字段并刷新外层清单哈希不会改变训练数据，但会削弱审计文件的可信度。

这属于制品元数据加固，不影响旁路记录、来源绑定或数据泄漏结论，不阻塞服务器目标测试。

## 计划符合性

- 文件边界符合修复简报：生产模块和测试模块发生变化，生产配置哈希保持不变；三者当前均为既有未跟踪文件，没有证据表明本轮修改了白名单外生产文件。
- 修复后生产模块、测试模块和配置文件的 SHA-256 与修复报告登记值完全一致，说明复审期间未发生漂移。
- 分类输入继续只读，旁路只按 `sample_id` 连接；掩码不再依赖场景语义字段。未发现物理字段进入提示词、标签或分类输入的代码路径。
- 配置中的生产制品路径固定为 `runs/data-frozen/dataset-v1-shared-b0-physics-v1`，最终文件集合与计划一致。
- 任务 01 的公开 Python 接口已经存在。`pyproject.toml` 中尚未注册物化命令入口，但实施计划将三个命令入口统一安排在任务 05，因此这不是任务 01 缺陷；在任务 05 完成前不能把当前模块当作完整可执行流水线。
- 未发现凭据、令牌或本机、服务器绝对路径写入本轮三个工程文件。

## 本轮验证

已执行且通过：

```text
AST_PARSE_OK 2
YAML_PARSE_OK
```

- 抽象语法树检查覆盖生产模块和测试模块，使用 `python3 -B`，未写入字节码缓存。
- YAML 安全解析覆盖生产配置，并核对配置模式版本。
- 精确 SHA-256 复核确认三个工程文件与修复报告一致。
- 仅以 `rg` 检查命令入口、字段门禁和凭据模式；未发现凭据或绝对路径字面量。

按任务边界未执行：

- 本机 `pytest`。
- 格式化、仅格式类静态检查或 `git diff --check`。
- 服务器、网络、同步和真实数据物化。

## 服务器放行门禁

下一步允许执行：

```bash
cd /root/autodl-tmp/thesis/experiments/llm_probe
uv run --no-sync pytest -q tests/test_shared_b0_physics_sidecar.py
```

服务器目标测试通过后还必须：

1. 使用生产配置从两个独立空目录完成真实数据双物化，并逐文件比较字节与 SHA-256。
2. 核对三个真实来源各 807 条、实际 SHA-256 与生产配置一致。
3. 核对冻结分类文件物化前后 SHA-256 不变。
4. 统计物理量最小值、包数整数性和非有限数；若违反取值域，不得进入训练。
5. 在任务 05 注册并验证命令入口前，不启动正式训练流水线。

