# TQH-C2 B 受限门禁修复后独立复审报告

## 裁决

- **复审日期**：2026-07-28。
- **严重问题**：0。
- **重要问题**：0。
- **建议问题**：2。
- **结论**：三项重要问题的最小修复满足批准设计，可以进入统一开机后的服务器精确测试；服务器测试、文件哈希回读和真实 12-cell 物化前门禁全部通过前，仍不得物化 B，也不得构造 A/B/C 统一候选。

本轮只读审查了批准设计、实施计划、首轮审查报告、修复报告、`tqh_c2.py` 的修复调用链及 `test_tqh_c2.py` 的对应测试。未连接服务器、未运行本机 `pytest`、未物化 B、未修改生产代码、测试或原始数据。

## 审查输入与一致性

当前源码和测试在仓库中处于未跟踪状态，因此无法依赖 Git 基线生成逐行补丁。本轮改为核对完整修复范围、相邻调用链和报告登记哈希：

- `src/flow_probe/tqh_c2.py`：`c681639af7de97bf4902341e0e51066455492df968769be8d1e6cfaefb4fcdc0`；与修复报告一致。
- `tests/test_tqh_c2.py`：`64344da5104211bcf0fb90add628b9715d67311f051c5e6cf39d93b16b4c63a6`；与修复报告一致。
- 未修改的 `src/flow_probe/tqh_c2_candidate.py`：`62b1c38e0539a7c824b1c4c57e027fdb192f020e6c54151deb1415c820aea4df`；与修复前后报告一致。

## 三项修复复核

### 1. 数据集版本必须显式声明

- `materialize_profile()` 的 `dataset_version` 已改为无默认值的必填关键字参数。
- 命令行 `--dataset-version` 已设置为 `required=True`。
- `audit_label_cell()` 与 `audit_profile()` 仍允许省略版本，但 B 的失败 gate 会把 `None` 传入同一例外函数并严格拒绝；A/C 的正常 `PASS` 审计不受影响。
- 测试同时覆盖函数调用省略版本和命令行省略版本。旧实现会继续注入默认 `1.0.1`，因此这两项测试能真实识别原绕过。

### 2. gate、manifest、标签和 cell 的采集身份绑定

- B 例外在解析硬检查前，使用严格非空字符串读取 gate 与 manifest 的 `capture_id`，二者不一致即失败。
- `_validate_cell_metadata()` 已先把 manifest 的 profile、interval、jitter 绑定到 cell 名称，并要求每条标签的 profile、interval、jitter 和 `capture_id` 与 manifest 一致。
- 因此 gate 不能只靠相同的允许失败集合冒充另一采集单元。
- 参数化测试覆盖 gate `capture_id` 缺失和错配；旧实现完全不读取该字段，两项测试会在旧实现上失败。

### 3. UID 与五元组严格拒绝异常输入

- UID、地址和协议只接受严格非空字符串，不再对数字、布尔值或空值执行字符串强转。
- 地址必须通过 IP 合法性校验。
- 协议规范为小写后只接受 `tcp`、`udp` 或 `icmp`。
- 端口要求 `type(value) is int` 且范围为 `0` 至 `65535`，因此布尔、浮点和数字字符串均被拒绝。
- 标签和 conn 的 UID 集合完全相等后，才逐 UID 比较已经通过上述校验的五元组。

## 负向测试覆盖核验

三项修复新增的测试覆盖 **12 个失败刺激**：

| 风险 | 失败刺激数 | 覆盖内容 |
| --- | ---: | --- |
| 隐式版本 | 2 | 函数省略版本、命令行省略版本 |
| 采集身份 | 2 | gate 缺失 `capture_id`、gate 与 manifest 错配 |
| UID 与五元组强转 | 8 | 双方缺地址、双方缺协议、非法 IP、非法协议、布尔端口、浮点端口、字符串端口、数值 UID |

从 `pytest` 收集节点计数看是 11 个节点，因为函数与命令行的两个版本刺激写在同一个测试函数中；从独立行为断言计数看是 12 项。组合不会造成覆盖缺口：函数契约回归会首先使该节点失败，命令行契约单独回归时会在第二个断言失败。

原门禁合同的其他负向测试仍覆盖版本/profile 不符、未知或缺失硬检查、H4/H5/H6 失败、修订计数异常、非法标签、五元组不一致、元数据不一致、C2 数量不足和 C profile 失败 gate。

## 回归边界

### A/C 严格门禁

- 只有 cell、manifest 和调用参数均为 B，且源 gate 为 `FAIL` 时才进入受限例外。
- A/C 的 `FAIL` 仍在进入例外前直接抛错；现有 C 回归测试覆盖该分支，A 使用相同分支条件。
- `PASS` 分支未引入 B 例外状态，不改变 A/C 的既有严格通过语义。

### unknown 排除

- `unknown` 仍被映射为 `binary_label=None`、`label_status=unresolved`。
- B 暂定主记录保留 unknown 仅用于来源审计；现有候选构造器只选择 `label_status=mapped` 的记录，因此 unknown 不进入二分类候选。
- 12-cell 传播测试确认 12 条 unknown 均保持 unresolved 且二分类标签为空。

## 建议问题

### 1. B 正向夹具的硬检查详情与布尔结果不自洽

夹具把 H2 标为通过，但详情仍写着 `benign=0 need>=0.8*c2=12`；H7 的详情写明比例低于阈值，却把它标为失败。这不会绕过生产门禁，因为实现按官方 `pass` 布尔值裁决并原样保存详情，但会降低测试夹具对真实 B gate 的解释力。后续整理测试时可让 benign/unknown 分布、详情和布尔值一致，不阻塞服务器验收。

### 2. 12-cell 传播测试尚未逐 cell 核对全部审计字段

当前测试已经核对 12 个 cell 的 `quality_acceptance`、`source_gate_status` 和 unknown 排除语义，但没有逐 cell 断言失败集合、修订计数一致性及 stale/revised 差异。单 cell 正向测试已覆盖这些字段，因此不存在当前正确性缺口；真实 B 物化验收仍应逐 cell 核对全部字段。

## 本地静态验证

执行：

```bash
thesis/experiments/llm_probe/.venv/bin/black --check \
  thesis/experiments/llm_probe/src/flow_probe/tqh_c2.py \
  thesis/experiments/llm_probe/tests/test_tqh_c2.py

thesis/experiments/llm_probe/.venv/bin/ruff check \
  thesis/experiments/llm_probe/src/flow_probe/tqh_c2.py \
  thesis/experiments/llm_probe/tests/test_tqh_c2.py

PYTHONPYCACHEPREFIX=/tmp/tqh-b-fix-rereview-pycache python3 -m py_compile \
  thesis/experiments/llm_probe/src/flow_probe/tqh_c2.py \
  thesis/experiments/llm_probe/tests/test_tqh_c2.py
```

结果：Black 无需修改，Ruff 无问题，Python 编译退出码为 0。遵守实验局部规则，本机未运行 `pytest`。

## 统一开机服务器门禁

服务器启动后按以下顺序执行；任一步失败都停止，不得物化 B：

1. 使用白名单 `rsync` 同步 `tqh_c2.py` 与 `test_tqh_c2.py`，禁止 `--delete`。
2. 回读服务器 SHA-256，必须与本报告登记值一致。
3. 执行 `uv pip install --no-deps -e .`，不得运行裸 `uv sync`。
4. 先运行修复与门禁精确集合：

```bash
uv run --no-sync pytest -q \
  tests/test_tqh_c2.py::test_materialize_profile_and_cli_require_explicit_dataset_version \
  tests/test_tqh_c2.py::test_b_gate_exception_binds_gate_capture_id_to_cell \
  tests/test_tqh_c2.py::test_b_gate_exception_rejects_incomplete_or_coerced_five_tuple \
  tests/test_tqh_c2.py::test_audit_label_cell_accepts_only_b_v101_revised_gate_after_full_audit \
  tests/test_tqh_c2.py::test_b_gate_exception_requires_explicit_v101_and_b_profile \
  tests/test_tqh_c2.py::test_b_gate_exception_rejects_unapproved_or_invalid_hard_checks \
  tests/test_tqh_c2.py::test_b_gate_exception_rejects_invalid_revised_counts \
  tests/test_tqh_c2.py::test_b_gate_exception_rejects_failed_row_integrity_audit \
  tests/test_tqh_c2.py::test_b_gate_exception_propagates_to_profile_and_materialization \
  tests/test_tqh_c2.py::test_audit_label_cell_rejects_failed_gate
```

5. 精确集合通过后，运行完整文件回归：

```bash
uv run --no-sync pytest -q tests/test_tqh_c2.py
uv run --no-sync black --check src/flow_probe/tqh_c2.py tests/test_tqh_c2.py
uv run --no-sync ruff check src/flow_probe/tqh_c2.py tests/test_tqh_c2.py
```

6. 只读预审真实 B 的 12 个 cell，确认每个 cell 的失败集合非空且仅含 H1/H3/H7，H4/H5/H6 明确通过，UID、五元组、元数据、标签、修订计数和不变量审计全部通过，并保留 `source_gate_status=FAIL`。
7. 上述结果和日志写入唯一运行目录并回收本机后，才允许按批准路径开始 B 暂定物化；物化过程继续使用 `_INCOMPLETE` 和原子发布门禁。

