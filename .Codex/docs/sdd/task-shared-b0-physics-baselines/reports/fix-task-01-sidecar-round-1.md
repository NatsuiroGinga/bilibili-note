# 共享 B0 物理旁路任务 01 修复轮次 1 报告

## 状态

- 修复状态：五项重要问题均已完成代码与回归测试修改，等待服务器目标测试。
- 修复边界：只处理修复简报列出的五项重要问题，未处理原审查报告中的三项建议。
- 未提交、未推送，未运行本机 `pytest`、格式化、服务器或网络命令。

## 白名单文件

本轮实际修改：

- `thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py`
- `thesis/experiments/llm_probe/tests/test_shared_b0_physics_sidecar.py`
- `.Codex/docs/sdd/task-shared-b0-physics-baselines/reports/fix-task-01-sidecar-round-1.md`

生产配置 `thesis/experiments/llm_probe/configs/shared_b0_physics_sidecar_v1.yaml` 已复核但未改写。其修复前后 SHA-256 均为 `cfce7175cb3692150dd368ac19dd925b345c15f5bf543931579f2b89cc7056de`。

## 五项重要修复

### 1. 独立校验重新绑定冻结来源语义

修复位置：

- `validate_shared_b0_physics_sidecar`
- `_load_source_records`
- `_physics_record`
- `_validate_record_semantics`

修复内容：

- 校验器从 `source_manifest.config.path` 重新加载并验证真实配置，不再只比较配置哈希。
- 校验器重新读取三个来源 JSONL，逐源验证实际哈希、807 条计数、来源划分和 `sample_id` 集合。
- 对每条输出记录重新计算时间锚点、归一化状态、容量累计量、接收字节累计量、接收包累计量、出队字节累计量、丢弃字节累计量和确定性掩码。
- 输出的 `group_id`、`stable_order`、`source_split`、用途、来源记录标识和来源文件哈希也逐字段与重建记录比较。

测试节点：

- `test_materializes_exact_sidecar_by_sample_id_and_preserves_classification` 使用一条完整手算记录固定全部输出字段。
- `test_validator_rebuilds_source_semantics_after_outer_hashes_are_refreshed[cumulative]`
- `test_validator_rebuilds_source_semantics_after_outer_hashes_are_refreshed[source_split]`
- `test_validator_rebuilds_source_semantics_after_outer_hashes_are_refreshed[mask]`

三类篡改测试均同步重算记录、数据清单和物化审计中的外层制品哈希，确保失败来自来源语义门禁。

### 2. 掩码只由 `sample_id` 与种子 42 派生

修复位置：

- `_build_state_masks`

修复内容：

- 第二锚点改为对 `42:<sample_id>` 的 SHA-256 整数取模派生。
- `group_id` 只保留为必需输出字段，不参与锚点选择。
- 每条掩码严格为锚点 0 加锚点 1 至 4 中的一个。

测试节点：

- `test_mask_depends_only_on_sample_id_and_seed`

该测试保持两个 `sample_id` 不变，同时改变 `group_id`、标签、提示词、场景名、来源划分、来源哈希和输入顺序，并逐条核对掩码仍等于仅按 `sample_id` 与种子计算的结果。

### 3. 三个来源各 807 条并逐字段绑定生产配置

修复位置：

- `load_shared_b0_physics_sidecar_config`
- `validate_shared_b0_physics_sidecar`

修复内容：

- 配置加载器新增逐源门禁，三个 `expected_count` 必须各为 807，不能只满足总和 2,421。
- 校验器将 `source_manifest` 中的分类绑定、配置绑定和三个来源的 `source_split/path/sha256/record_count/selected_record_count` 与真实配置及实际文件结果精确比较。
- 数据清单中的输出路径、阶段、状态、用途、记录数、锚点数、前缀和掩码配置与重新加载的真实配置逐项比较。

测试节点：

- `test_production_config_freezes_paths_counts_usage_and_source_hashes`
- `test_config_requires_exactly_807_records_per_source`
- `test_validator_compares_source_manifest_with_real_config`

生产配置测试固定三个来源的 `split/path/sha256/expected_count`，并固定掩码模式、种子 42、`theory_selection` 阶段和 `review_pending` 状态。

### 4. 发布失败保留调用方预建空目录

修复位置：

- `materialize_shared_b0_physics_sidecar`

修复内容：

- 删除“先移除预建空目录，再重命名 `.partial`”的失败窗口。
- 发布改为同级 `.partial` 到目标路径的一次 `Path.replace`；发布前只读复核目标仍为空或不存在。
- 重命名失败时异常清理仅删除 `.partial`，不会删除原空目录；非空目标继续在写入前拒绝。

测试节点：

- `test_publish_failure_preserves_precreated_empty_directory_and_files`

该测试注入最终重命名失败，断言原空目录仍存在且为空、`.partial` 被清理；随后放入哨兵文件，确认再次物化被拒绝且文件字节不变。

### 5. 精确文件集合与不跟随链接校验

修复位置：

- `_validate_output_tree`
- `validate_shared_b0_physics_sidecar`

修复内容：

- 使用 `lstat` 和 `DirEntry.stat(follow_symlinks=False)` 检查输出根及全部后代，拒绝根符号链接、后代符号链接和其他非普通文件。
- 最终普通文件集合必须严格等于 `REQUIRED_OUTPUT_FILES`，目录集合必须严格等于必要父目录集合。
- 拒绝输出根同级遗留的 `<output>.partial`。
- `materialization_audit.required_files` 必须严格等于规定文件列表。

测试节点：

- `test_validator_rejects_non_exact_or_linked_output_tree[output_root_symlink]`
- `test_validator_rejects_non_exact_or_linked_output_tree[extra_file]`
- `test_validator_rejects_non_exact_or_linked_output_tree[renamed_classification_copy]`
- `test_validator_rejects_non_exact_or_linked_output_tree[required_file_symlink]`
- `test_validator_rejects_non_exact_or_linked_output_tree[non_empty_directory]`
- `test_validator_rejects_non_exact_or_linked_output_tree[leftover_partial]`
- `test_validator_requires_exact_materialization_file_set`
- `test_two_independent_materializations_are_byte_identical`

双物化测试现在分别将两个输出目录的实际普通文件集合与 `REQUIRED_OUTPUT_FILES` 比较，再逐文件比较字节。

## 静态检查

已执行且通过：

```text
AST_PARSE_OK 2
YAML_PARSE_OK flow_probe_shared_b0_physics_sidecar_config_v1
```

抽象语法树检查使用 `python3 -B`，未写入字节码缓存；YAML 使用 Ruby 安全加载，只检查生产配置语法和模式版本。

按修复简报要求未执行：

- 本机 `pytest` 或其他行为测试。
- Black、Prettier、Ruff、`git diff --check` 或其他格式化、格式检查。
- 本机正式物化。
- 服务器、同步或网络命令。

待服务器执行：

```bash
cd /root/autodl-tmp/thesis/experiments/llm_probe
uv run --no-sync pytest -q tests/test_shared_b0_physics_sidecar.py
```

## 白名单自审

- 修复前 SHA-256：生产模块 `aa079770794d5c0bdabbced5dd6a05c898360eb51a1437f1ac229f8c7ae74ab8`，测试模块 `db7417439b87219d6ef6abf35f58eeca50b6ca5692d05e838067ab08edd5e8eb`。
- 修复后、报告写入前 SHA-256：生产模块 `7fe2aee8c64ef1b357559274a0c7f5bdf1b8914fc0081ea63ce269233b9c3a9c`，测试模块 `4d93b6a720111dae0e768c2eddf241eb1216df9b18f53e43c8a250fa59c2ace1`。
- 生产配置哈希未变化。
- 精确路径状态审计显示三个工程文件为既有未跟踪文件；修复报告位于 `.gitignore` 已登记的 `.Codex/` 过程文档目录，因此不出现在普通 `git status` 中，但已在指定路径落盘。
- 本轮没有读取后覆盖、暂存、回滚或删除白名单外的既有工作树变更。
- 未生成运行制品、缓存、分类副本或临时测试目录。

## 遗留验证

- 服务器目标测试尚未执行，因此本报告不声明行为测试已通过。
- 预建空目录替换依赖目标服务器的同文件系统目录重命名语义；服务器目标测试中的双物化和失败注入用例是最终放行门禁。
