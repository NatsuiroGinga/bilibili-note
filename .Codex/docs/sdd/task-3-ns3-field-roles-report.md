# 任务 2：ns-3 字段角色与防泄漏契约实现报告

## 结论

- 状态：完成。
- 46 个 `ns3_truth.CSV_FIELDS` 字段已唯一归入五个固定角色。
- `model_input_observable` 仅允许 5 个容量或队列入口可观测字段。
- 任意两个命名切分共享 `group_id` 时，校验器会报告冲突组号和两个切分名。

## 修改文件

- `thesis/experiments/llm_probe/configs/ns3_queue_truth_field_roles.json`
- `thesis/experiments/llm_probe/src/flow_probe/ns3_field_roles.py`
- `thesis/experiments/llm_probe/tests/test_ns3_field_roles.py`
- `.Codex/docs/sdd/task-3-ns3-field-roles-report.md`

未修改任务 1 的 C++、ns-3 真值验证器及其测试。

## 测试驱动证据

### 红测

服务器命令：

```bash
source ~/.bashrc
cd /root/autodl-tmp/thesis/experiments/llm_probe
uv run --no-sync pytest -q tests/test_ns3_field_roles.py
```

结果：测试收集按预期失败，错误为
`ModuleNotFoundError: No module named 'flow_probe.ns3_field_roles'`。失败发生时实现文件与配置文件均不存在。

红测日志：

`/root/autodl-tmp/thesis/experiments/llm_probe/runs/ns3-data/field-roles-tests-20260720/red-target.log`

### 绿测

格式化后的服务器目标测试：

```bash
source ~/.bashrc
cd /root/autodl-tmp/thesis/experiments/llm_probe
uv run --no-sync pytest -q tests/test_ns3_field_roles.py
```

结果：`14 passed in 0.03s`。

最终目标日志：

`/root/autodl-tmp/thesis/experiments/llm_probe/runs/ns3-data/field-roles-tests-20260720/green-target-final.log`

格式化后的服务器完整回归：

```bash
source ~/.bashrc
cd /root/autodl-tmp/thesis/experiments/llm_probe
uv run --no-sync pytest -q
```

结果：`193 passed in 3.09s`。

最终完整回归日志：

`/root/autodl-tmp/thesis/experiments/llm_probe/runs/ns3-data/field-roles-tests-20260720/green-full-final.log`

## 契约检查

角色计数：

| 角色                     | 字段数 |
| ------------------------ | -----: |
| `model_input_observable` |      5 |
| `state_supervision`      |     12 |
| `label_target`           |      6 |
| `split_metadata`         |     15 |
| `audit_only`             |      8 |
| 合计                     |     46 |

加载器直接复用 `flow_probe.ns3_truth.CSV_FIELDS`，未在实现模块复制 46 字段全集。测试覆盖：

- 固定配置成功加载并返回元组值。
- 角色名缺失或多出。
- 配置顶层不是对象、角色成员不是数组、成员不是字符串。
- 字段遗漏、未知字段、角色内重复和跨角色重复。
- 模型输入包含禁止字段或缺少允许字段。
- 不相交切分通过，共享 `group_id` 的切分失败。

重叠错误示例：

```text
group_id 'shared-group' 同时出现在切分 'train' 与 'validation' 中
```

## 格式与静态检查

- Black：已格式化 `src/flow_probe/ns3_field_roles.py` 和
  `tests/test_ns3_field_roles.py`；格式化后的代码已重新完成服务器目标与完整回归。
- Ruff：上述两个 Python 文件执行 `ruff check`，结果为 `All checks passed!`。
- Prettier：配置 JSON 与本报告均执行 `prettier --write`。
- `git diff --check`：执行成功，无空白错误输出。

本机首次通过 `uv run --no-sync black` 调用时，因沙箱无法写入用户级 `uv` 缓存而失败；随后直接使用项目现有 `.venv/bin/black` 完成格式化，不涉及依赖变更。

## 残余风险

- 本任务只提供角色配置加载和切分集合校验接口，尚未把接口接入后续数据物化或训练流水线；调用方仍需在生成训练、验证和测试制品前显式调用。
- `group_id` 的正确组成与 CSV 内容真实性由现有 `ns3_truth` 验证器负责，本模块只检查已经给出的组号是否跨切分重叠。

## 独立审查修复轮

### 结论

- 状态：两个真实接口缺陷已修复。
- 字段角色 JSON 和 46 字段精确映射未修改；实现继续直接复用
  `flow_probe.ns3_truth.CSV_FIELDS`。
- 原实现报告中的 `ModuleNotFoundError` 只属于收集期失败，仍不构成需求行为红测。
  根据本轮控制器下发的加速例外，不再删除并重建现有正确实现，也不把历史日志改写为
  行为红测；该流程偏差在此保留记录。

### 修复内容

1. `validate_group_disjoint_splits` 现在统一以 `NS3FieldRolesError` 拒绝
   `str`、`bytes` 形式的切分值，避免把完整 `group_id` 拆成字符或字节整数。
2. 切分集合中的成员现在必须全部为字符串，非字符串成员统一以
   `NS3FieldRolesError` 拒绝，并在信息中标明切分名和契约上下文。
3. `load_ns3_field_roles` 现在分别包装 JSON 解析失败、UTF-8 解码失败和文件读取失败；
   错误信息包含源路径与中文上下文，并通过 `raise ... from exc` 保留原异常链。

### 真实红绿证据

服务器输出目录：

`/root/autodl-tmp/thesis/experiments/llm_probe/runs/ns3-data/field-roles-fix-tests-20260720/`

本轮先只修改测试并同步服务器，执行六项新增边界测试。红测结果为
`6 failed, 14 deselected`：损坏 JSON、无效 UTF-8、文件不存在均直接抛出原始异常；
字符串、字节串和非字符串集合成员均未抛出契约错误。

红测日志：

`red-interface-boundaries.log`

完成最小实现后复跑同一组用例，结果为 `6 passed, 14 deselected`。

新增用例绿测日志：

`green-interface-boundaries.log`

### 回归验证

- Black 格式化后的最终目标测试：`20 passed in 0.03s`，日志为
  `green-target-final.log`。
- Black 格式化后的最终完整回归：`206 passed in 2.91s`，日志为
  `green-full-final.log`。
- Black：已集中格式化本轮两个 Python 文件；模块发生纯格式变化，测试文件无需改写。
- Ruff：本轮两个 Python 文件检查通过，输出为 `All checks passed!`。

### 修改边界与顾虑

- 本轮修改 `src/flow_probe/ns3_field_roles.py`、`tests/test_ns3_field_roles.py` 和本报告。
- 未修改 `configs/ns3_queue_truth_field_roles.json`，未修改任务 1 的 C++、真值验证器或测试。
- 历史收集期红测不足仍是已知流程偏差；本轮只为两个真实缺陷保存了可复现的行为级
  红绿证据，不声称补齐原始实现的全部测试驱动历史。
