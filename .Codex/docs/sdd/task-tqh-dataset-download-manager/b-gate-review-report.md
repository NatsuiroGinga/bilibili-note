# TQH-C2 B v1.0.1 受限门禁独立审查报告

## 裁决

- **审查时间**：2026-07-28 14:09 CST
- **严重问题**：0
- **重要问题**：3
- **建议问题**：2
- **结论**：阻塞 B 物化；修复并由新的审查代理复核前，不得进入统一开机验收或 A/B/C 候选构造。

本轮只读检查了批准设计、实施计划、实现报告、`tqh_c2.py` 的 B 门禁调用链、`test_tqh_c2.py` 的新增合同测试及实验 `AGENTS.md` 写回。未修改代码、未运行服务器、未物化 B。

## 重要问题

### 1. 隐式默认版本绕过“显式声明”

- 位置：`thesis/experiments/llm_probe/src/flow_probe/tqh_c2.py:1291`、`:1464`。
- 现象：`materialize_profile()` 与命令行均默认注入 `1.0.1`。调用方不声明版本时，B 的 `FAIL` gate 仍会收到允许版本并签发例外。
- 影响：违反批准合同“调用方必须显式声明 B v1.0.1”，形成顶层 fail-open。
- 修复要求：移除物化函数的隐式版本默认值，并把 `--dataset-version` 设为必填；增加函数与命令行省略版本的负向测试。

### 2. `gate.capture_id` 未绑定当前 cell

- 位置：`tqh_c2.py:267-375`、`:483-504`。
- 现象：manifest 与标签的 `capture_id` 会互相核对，但 B 例外只读取 gate 的 checks，不检查实际存在的 `gate.json.capture_id`。
- 影响：把另一个 B cell 的允许失败 gate 替换进当前目录后仍可能通过，输出的“原始失败项与详情”不再属于当前采集单元。
- 修复要求：要求 gate、manifest、标签的 `capture_id` 严格相同，并明确拒绝 gate 缺失或错配 capture_id；增加负向测试。

### 3. 五元组完整性比较允许缺字段与类型强转

- 位置：`tqh_c2.py:181-188`、`:507-524`、`:578-610`。
- 现象：地址与协议缺失时被转为空字符串；端口通过 `int()` 强转。label 与 conn 同时缺字段，或使用布尔、小数、数字字符串等可强转值时，可能被折叠为相等。
- 影响：无效五元组可在 B 例外审计中被记录为 `five_tuple=pass`。
- 修复要求：UID、地址和协议必须是严格非空字符串；地址必须是有效 IP，协议必须是合法非空传输协议；端口必须满足 `type(value) is int` 且范围有效，然后才允许比较。增加缺字段、布尔、小数和字符串端口的负向测试。

## 建议问题

1. B 正向夹具没有 benign，却让 H2 以 `benign=0 need>=12` 标记通过；H7 的 1/51 低于阈值却标记失败。应让标签分布与 H2/H7 详情语义自洽并接近真实 B。
2. 12-cell 传播测试只核对 `source_gate_status`。应同时断言每个 cell 的 `quality_acceptance`、失败集合、修订计数一致、stale/revised 差异与完整性字段。

## 已确认边界

- B 例外判定已位于 UID 集合、五元组、元数据、合法标签与逐行计数之后。
- H1-H7 完整性、非空允许失败子集、允许集合外失败、布尔类型、H4/H5/H6、严格修订计数、`invariant_violations=0` 与 `flows_malicious_c2>=50` 已有实现和测试。
- A/C 的失败 gate 继续严格拒绝。
- 当前源码与测试 SHA-256 与实现报告一致；C-only candidate 源码 SHA-256 未变化。
- 最终 Ruff 修复后的文件尚未在服务器复跑，这是独立于代码发现的运行门禁。

## 修复后统一验收

新的修复代理完成最小修复、服务器精确测试和新的独立审查后，统一开机至少执行：

```bash
source ~/.bashrc
cd /root/autodl-tmp/thesis/experiments/llm_probe
uv pip install --no-deps -e .
uv run pytest tests/test_tqh_c2.py -q
uv run black --check src/flow_probe/tqh_c2.py tests/test_tqh_c2.py
uv run ruff check src/flow_probe/tqh_c2.py tests/test_tqh_c2.py
```

零重要问题复核前不得运行真实 B 物化。
