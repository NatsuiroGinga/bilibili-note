# TQH-C2 B 受限门禁独立审查修复报告

## 结论

独立审查报告中的 3 项重要问题已完成最小代码修复和负向测试补充。本轮未连接服务器、未运行 `pytest`、未物化 B、未修改原始数据、候选物化器或既有候选制品。修复仍需服务器精确测试和新的独立审查通过后，才能解除 B 物化阻塞。

## 修复范围

仅修改：

- `thesis/experiments/llm_probe/src/flow_probe/tqh_c2.py`
- `thesis/experiments/llm_probe/tests/test_tqh_c2.py`

新增本报告：

- `.Codex/docs/sdd/task-tqh-dataset-download-manager/b-gate-review-fix-report.md`

未修改：

- `thesis/experiments/llm_probe/src/flow_probe/tqh_c2_candidate.py`
- 原始 TQH-C2 数据、派生数据、运行目录、依赖文件和命令入口配置

## 三项重要问题的处置

### 1. 删除数据集版本隐式默认

- `materialize_profile()` 的 `dataset_version` 改为必填关键字参数。
- 命令行 `--dataset-version` 改为 `required=True`，不再默认注入 `1.0.1`。
- 既有 C 物化测试全部显式传入版本，避免测试继续依赖隐式默认。
- 新增函数调用与命令行均省略版本的负向测试。

### 2. 绑定 gate 的采集身份

- B 受限例外在解析硬检查前，严格读取 manifest 和 gate 的 `capture_id`。
- gate 缺失 `capture_id` 时立即失败。
- gate 与 manifest 的 `capture_id` 不一致时立即失败。
- 标签行与 manifest 的绑定继续由既有 `_validate_cell_metadata()` 校验，因此 gate、manifest 和标签三者共同绑定当前 cell。
- 新增 gate `capture_id` 缺失与错配的两个负向测试。

### 3. 五元组和 UID 改为 fail-close

- `_required_text()` 不再把数字、布尔值或其他对象强转为字符串，只接受严格非空字符串。
- 地址字段必须是严格非空字符串，并通过 `ipaddress.ip_address()` 合法性验证。
- 协议字段必须是严格非空字符串，规范为小写后只能属于 `tcp`、`udp` 或 `icmp`。
- 端口必须满足 `type(value) is int` 且位于 `0～65535`；布尔值、浮点数和数字字符串均拒绝。
- 新增双方同时缺地址、同时缺协议、非法 IP、异常协议、布尔端口、小数端口、字符串端口和数值 UID 的负向测试。

## 测试先行记录

负向测试先于生产代码修改落盘。根据修复前调用链：

- 函数与命令行省略版本会继续取得默认 `1.0.1`；
- gate 的 `capture_id` 完全未读取；
- 地址和协议会被 `str()` 折叠，端口会被 `int()` 强转；

因此新增用例在旧实现上会分别出现“未按合同拒绝”的失败。本轮受任务边界限制不得连接服务器，同时实验局部规则禁止本机运行 `pytest`，故没有伪造实际红灯或绿灯记录；服务器验证仍是交付门禁。

## 本机静态验证

```text
thesis/experiments/llm_probe/.venv/bin/black \
  thesis/experiments/llm_probe/src/flow_probe/tqh_c2.py \
  thesis/experiments/llm_probe/tests/test_tqh_c2.py
```

结果：退出码 `0`；测试文件完成格式化，生产文件无需变化。

```text
thesis/experiments/llm_probe/.venv/bin/ruff check \
  thesis/experiments/llm_probe/src/flow_probe/tqh_c2.py \
  thesis/experiments/llm_probe/tests/test_tqh_c2.py
```

结果：`All checks passed`，退出码 `0`。

```text
PYTHONPYCACHEPREFIX=/tmp/tqh-b-review-fix-pycache python3 -m py_compile \
  thesis/experiments/llm_probe/src/flow_probe/tqh_c2.py \
  thesis/experiments/llm_probe/tests/test_tqh_c2.py
```

结果：退出码 `0`。

```text
git diff --check
```

结果：退出码 `0`。

最终 SHA-256：

- `src/flow_probe/tqh_c2.py`：`c681639af7de97bf4902341e0e51066455492df968769be8d1e6cfaefb4fcdc0`
- `tests/test_tqh_c2.py`：`64344da5104211bcf0fb90add628b9715d67311f051c5e6cf39d93b16b4c63a6`
- 未修改的 `src/flow_probe/tqh_c2_candidate.py`：`62b1c38e0539a7c824b1c4c57e027fdb192f020e6c54151deb1415c820aea4df`

## 服务器精确测试命令

服务器启动后，先以白名单 `rsync` 同步最终两份文件并核对上述 SHA-256，再执行：

```bash
source ~/.bashrc >/dev/null 2>&1
cd /root/autodl-tmp/thesis/experiments/llm_probe
uv pip install --no-deps -e .
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

精确集合通过后，再执行完整文件回归：

```bash
uv run --no-sync pytest -q tests/test_tqh_c2.py
```

预计精确集合与完整文件回归各低于 `5` 秒；服务器启动、连接和环境初始化时间另计。测试失败时不得物化 B，应保留完整错误输出并只修复实际失败根因。

## 剩余门禁

1. 服务器精确集合和完整文件回归退出码均为 `0`。
2. 新的独立审查代理确认严重问题 `0`、重要问题 `0`。
3. 修复后的生产代码与测试哈希同步到实现记录和服务器验收记录。
4. 上述门禁全部完成前，B 物化、统一 A/B/C 候选构造和相关训练继续阻塞。
