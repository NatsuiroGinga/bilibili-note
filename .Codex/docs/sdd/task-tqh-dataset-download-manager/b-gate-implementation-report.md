# TQH-C2 B v1.0.1 受限门禁实现报告

## 结论

已按批准设计实现 TQH-C2 B v1.0.1 受限门禁。源 `gate.json` 仍保留 `FAIL`；只有显式声明 B/1.0.1、硬检查与全部逐行完整性审计通过时才签发 `accepted_b_v1_0_1_revised_counts`。A/C、未声明版本或 profile、未知失败项、缺失硬检查及任一完整性失败继续终止。

本任务未修改原始数据，未物化 B，未创建 A/B/C 候选，未修改 `tqh_c2_candidate.py`，未提交或推送。

## 修改文件

- `thesis/experiments/llm_probe/src/flow_probe/tqh_c2.py`
  - 增加 B v1.0.1 允许失败集合、完整 H1-H7 检查集合、质量接受状态与例外理由。
  - 在 UID、五元组、元数据、合法标签和逐行重计完成后统一判定源 gate。
  - 严格要求修订计数字段集合与类型、逐字段等于逐行重计、`invariant_violations=0`、`flows_malicious_c2>=50`。
  - 将声明版本/profile 贯穿 `audit_label_cell`、`audit_profile`、`extract_cell` 与 `materialize_profile`。
  - 审计保留源 gate 状态、原失败项与详情、例外理由、修订计数来源、stale/revised 差异及完整性结果。
- `thesis/experiments/llm_probe/tests/test_tqh_c2.py`
  - 增加 B 正向门禁夹具和版本/profile、失败集合、缺失 H2/H4、H4-H6 失败、布尔类型绕过、修订计数、非法标签、五元组、元数据与 C2 下限负向测试。
  - 增加 12-cell `audit_profile`/`materialize_profile` 传播测试，并确认 `unknown` 保持 `unresolved`、`binary_label=None`。
  - 保留 C 失败 gate 严格拒绝回归。
- `thesis/experiments/llm_probe/AGENTS.md`
  - 增加 B 受限例外启动前预检、允许边界和最小验证规则。
- `.Codex/docs/sdd/task-tqh-dataset-download-manager/b-gate-implementation-report.md`
  - 本报告。

## 测试驱动记录

### 初始红灯

```bash
uv run pytest tests/test_tqh_c2.py::test_audit_label_cell_accepts_only_b_v101_revised_gate_after_full_audit -q
```

结果：`1 failed in 0.29s`。失败原因为 `audit_label_cell()` 尚不接受 `dataset_version`，符合缺失功能预期。

### 首轮绿灯与 C 回归

```bash
uv run pytest tests/test_tqh_c2.py::test_audit_label_cell_accepts_only_b_v101_revised_gate_after_full_audit tests/test_tqh_c2.py::test_audit_label_cell_rejects_failed_gate -q
```

结果：`2 passed in 0.16s`。

### 新增合同集合

```bash
uv run pytest tests/test_tqh_c2.py::test_b_gate_exception_requires_explicit_v101_and_b_profile tests/test_tqh_c2.py::test_b_gate_exception_rejects_unapproved_or_invalid_hard_checks tests/test_tqh_c2.py::test_b_gate_exception_rejects_invalid_revised_counts tests/test_tqh_c2.py::test_b_gate_exception_rejects_failed_row_integrity_audit tests/test_tqh_c2.py::test_b_gate_exception_propagates_to_profile_and_materialization -q
```

结果：`19 passed in 0.61s`。

### 缺失 H2 防 fail-open 回归

修复前精确节点结果：`1 failed in 0.21s`，原因为未抛出异常。加入 H1-H7 完整性要求后，同一节点结果为 `1 passed in 0.16s`。

```bash
uv run pytest 'tests/test_tqh_c2.py::test_b_gate_exception_rejects_unapproved_or_invalid_hard_checks[missing_h2]' -q
```

## 格式化与静态检查

- `uv run --locked black src/flow_probe/tqh_c2.py tests/test_tqh_c2.py`：通过，两个文件已格式化。
- `uv run --locked ruff check src/flow_probe/tqh_c2.py tests/test_tqh_c2.py`：首次发现一个未使用导入和一个导入排序问题。
- `uv run --locked ruff check --fix src/flow_probe/tqh_c2.py tests/test_tqh_c2.py`：`2 fixed, 0 remaining`；按局部规则未重复运行 Ruff。
- `PYTHONPYCACHEPREFIX=/tmp/tqh-b-pycache .venv/bin/python -m py_compile src/flow_probe/tqh_c2.py tests/test_tqh_c2.py`：退出码 `0`。

最终 SHA-256：

- `src/flow_probe/tqh_c2.py`：`b65f01008d311da2c67ea2e0889cf595136e102e1dd2075a9eae1865e1b2d85e`
- `tests/test_tqh_c2.py`：`df0715f743884f483ab0069a15505b9bf825cd6688fc48ac0cf72cb931eb9dbd`
- 未修改的 `src/flow_probe/tqh_c2_candidate.py`：`62b1c38e0539a7c824b1c4c57e027fdb192f020e6c54151deb1415c820aea4df`

## 待集中执行的服务器门禁

服务器切换为按量计费后不再保持常开。最终 Black/Ruff 机械修复后尚未重复服务器测试；下次统一开机时先同步上述最终 SHA-256 文件，再运行以下最小集合：

```bash
uv run pytest tests/test_tqh_c2.py::test_audit_label_cell_accepts_only_b_v101_revised_gate_after_full_audit tests/test_tqh_c2.py::test_b_gate_exception_requires_explicit_v101_and_b_profile tests/test_tqh_c2.py::test_b_gate_exception_rejects_unapproved_or_invalid_hard_checks tests/test_tqh_c2.py::test_b_gate_exception_rejects_invalid_revised_counts tests/test_tqh_c2.py::test_b_gate_exception_rejects_failed_row_integrity_audit tests/test_tqh_c2.py::test_b_gate_exception_propagates_to_profile_and_materialization tests/test_tqh_c2.py::test_audit_label_cell_rejects_failed_gate -q
```

预计测试计算时间低于 2 秒；服务器启动、SSH 与 `uv` 初始化另计约 10 秒。独立审查若要求完整文件回归，再运行：

```bash
uv run pytest tests/test_tqh_c2.py -q
```

## 边界与遗留风险

- 本报告只证明实现与小型夹具合同；尚未物化或验收真实 B 的 12 个 cell。
- 生产源码实质修改仍须由新的审查代理检查 fail-open、类型绕过、审计字段与 A/C 回归。
- 原始 `raw/datasets/TQH-C2-2026/`、既有派生目录、候选协议、实验总控和恢复文档均未修改。
- 本任务没有运行制品路径；唯一新增制品是本实现报告。
