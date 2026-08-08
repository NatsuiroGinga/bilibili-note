# TQH-C2 A/B/C 统一候选物化器实施报告

## 任务边界

- 执行计划：`2026-07-28-tqh-b-exception-and-abc-implementation-plan.md` 任务 4。
- 首次分派曾错误要求修改既有 C-only 文件，与落盘计划冲突；主代理已明确该分派无效。
- 本次只新增独立 A/B/C 入口和隔离测试，不修改、覆盖或迁移既有 C-only 实现与历史制品。
- 未连接服务器，未读取或物化真实数据，未运行本机 `pytest`。

## 修改文件

- 新增：`thesis/experiments/llm_probe/src/flow_probe/tqh_c2_candidate_abc.py`
- 新增：`thesis/experiments/llm_probe/tests/test_tqh_c2_candidate_abc.py`
- 新增：`.Codex/docs/sdd/task-tqh-dataset-download-manager/abc-candidate-implementation-report.md`

## 实现内容

1. 要求调用方显式提供 A、B、C 三个暂定 profile 目录和独立的批准输入配置；配置按 profile 固定输入标识、上游制品清单 SHA-256、提取器 SHA-256、主记录数和包记录数。
2. 回读 `artifact_checksums.provisional.json` 登记的 8 个上游制品，逐项核对路径、大小和 SHA-256；同时核验运行清单、必要审计和主记录中的数据集标识、版本 `1.0.1`、profile、暂定状态、记录数和提取器合同。
3. 验证 A/B/C 全局 `sample_id` 和 `allocation_group_id` 唯一，并执行固定标签契约检查。
4. 主记录允许载入内存；大包表只通过 `pyarrow.parquet.ParquetFile.read_row_group` 逐行组读取。
5. 每个 Parquet 行组必须只能映射到一个完整 cell；同一 cell 的行组必须相邻，出现 `cell_order_fallback` 立即失败；样本可跨相邻行组，但不得关闭后再次出现。
6. 逐样本验证包序号连续性和 `packet_count_kept`，复用既有 37 字段聚合语义并生成相同语义的观测序列哈希。
7. 未知和辅助标签保留在来源审计中，但不进入二分类候选样本表。
8. 验证每个 profile 恰好包含 `30/300/1800/3600 × 0/30/70` 的 4×3 唯一 cell 网格。
9. 从满足 profile、interval、cell 数量、标签和组互斥硬约束的组合中确定性选择划分；先最小化样本比例偏差，再扩大 jitter 覆盖并使用稳定哈希处理平局：
   - `tqhc2_cell_indomain`：28/4/4 cell；
   - `tqhc2_leave_one_profile_out_A`：20/4/12 cell；
   - `tqhc2_leave_one_profile_out_B`：20/4/12 cell；
   - `tqhc2_leave_one_profile_out_C`：20/4/12 cell。
10. 域内验证和测试分别覆盖 A/B/C 与四个 interval；各留一套件验证覆盖两个源 profile 与四个 interval，测试固定为完整留出 profile。
11. 为四个套件分别输出训练、验证和测试清单，共 12 份；每行绑定同一个 `samples.parquet` SHA-256。
12. 套件审计显式记录每个 split 的 profile、interval、jitter、cell 数、样本数、样本比例、目标比例和偏差；任一硬约束不满足即失败。
13. 输出目录预先写入 `_INCOMPLETE`；成功后才删除，且已存在目录一律拒绝覆盖。

## 隔离测试覆盖

- 四套划分的 cell 数量、覆盖与套件内互斥。
- 测试使用独立字面量断言批准的四个 suite 键、12 个文件名、profile 与 interval 覆盖，不从生产常量导入期望合同。
- 12 份清单的主表哈希绑定和冻结协议可加载性。
- 37 个模型字段可加载且每个划分同时包含良性与恶意标签。
- 未知标签排除和 A/B/C 全局主键唯一。
- 两次新目录物化逐字节复现和拒绝覆盖。
- 混合多个 cell 的 Parquet 行组拒绝。
- 跨 profile `sample_id` 冲突拒绝。
- 固定标签契约错误拒绝。
- 主记录与包观测计数不一致拒绝。
- 非 `1.0.1` 数据版本拒绝。
- 上游登记制品被修改、运行清单计数未绑定批准配置和提取器不一致拒绝。
- 4×3 cell 网格缺失或重复拒绝。
- `cell_order_fallback` 拒绝并保留 `_INCOMPLETE`。
- 样本跨相邻行组成功、样本关闭后非连续重现失败并保留 `_INCOMPLETE`。

## 本机静态检查

```text
UV_CACHE_DIR=/tmp/uv-cache uv run --no-sync black src/flow_probe/tqh_c2_candidate_abc.py tests/test_tqh_c2_candidate_abc.py
结果：通过，两份文件已格式化。

UV_CACHE_DIR=/tmp/uv-cache uv run --no-sync ruff check src/flow_probe/tqh_c2_candidate_abc.py tests/test_tqh_c2_candidate_abc.py
结果：唯一修复轮发现 1 处中文字符串超过 100 字符；已拆分字面量。按局部规则未重复运行 Ruff，服务器门禁将复核。

UV_CACHE_DIR=/tmp/uv-cache uv run --no-sync python -m py_compile src/flow_probe/tqh_c2_candidate_abc.py tests/test_tqh_c2_candidate_abc.py
结果：通过。

git diff --check -- src/flow_probe/tqh_c2_candidate_abc.py tests/test_tqh_c2_candidate_abc.py
结果：通过。
```

## 服务器最小验收命令

在服务端项目根目录执行：

```bash
uv pip install --no-deps -e .
uv run --no-sync pytest -q \
  tests/test_tqh_c2_candidate.py \
  tests/test_tqh_c2_candidate_abc.py \
  tests/test_frozen_protocol.py
uv run --no-sync black --check \
  src/flow_probe/tqh_c2_candidate.py \
  src/flow_probe/tqh_c2_candidate_abc.py \
  tests/test_tqh_c2_candidate.py \
  tests/test_tqh_c2_candidate_abc.py
uv run --no-sync ruff check \
  src/flow_probe/tqh_c2_candidate.py \
  src/flow_probe/tqh_c2_candidate_abc.py \
  tests/test_tqh_c2_candidate.py \
  tests/test_tqh_c2_candidate_abc.py
```

审查修复的精确行为节点：

```bash
uv run --no-sync pytest -q \
  tests/test_tqh_c2_candidate_abc.py::test_materialize_abc_builds_approved_hard_coverage_suites \
  tests/test_tqh_c2_candidate_abc.py::test_materialize_abc_rejects_unregistered_upstream_change \
  tests/test_tqh_c2_candidate_abc.py::test_materialize_abc_rejects_manifest_count_not_bound_to_approval \
  tests/test_tqh_c2_candidate_abc.py::test_materialize_abc_rejects_extractor_mismatch \
  tests/test_tqh_c2_candidate_abc.py::test_materialize_abc_rejects_incomplete_four_by_three_grid \
  tests/test_tqh_c2_candidate_abc.py::test_materialize_abc_rejects_row_group_with_multiple_cells \
  tests/test_tqh_c2_candidate_abc.py::test_materialize_abc_rejects_cell_order_fallback \
  tests/test_tqh_c2_candidate_abc.py::test_materialize_abc_accepts_sample_across_adjacent_row_groups \
  tests/test_tqh_c2_candidate_abc.py::test_materialize_abc_rejects_noncontiguous_sample_reappearance
```

## 遗留风险

- 尚未在服务器执行行为测试，当前只能确认静态语法与格式门禁。
- 正式 A/B/C 包表是否始终满足“单行组单 cell”需要任务 6 的双份真实物化验证；不满足时必须停止，不能退化为一次载入全部包表。
- 本实现保持候选状态 `review_pending`，在独立审查和双份物化前不得形成论文结论。
