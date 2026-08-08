# 任务 2：ns-3 字段角色与防泄漏契约修复后独立复审

## 审查结论

- **计划符合性：通过。** 任务 2 的字段角色、防泄漏切分和修复后边界要求均已满足。首次实现只有收集期失败仍如实保留为历史流程偏差；根据用户本轮明确裁决，该偏差不再阻塞验收，也没有被改写或伪造成行为级红测。
- **代码质量：批准。** 原审查问题 1 和问题 2 均已修复，新增测试覆盖相应边界，未发现修复引入新的严重、重要或次要缺陷。
- **问题数量：严重 0，重要 0，次要 0。**

## 原问题复核

### 1. `str`、`bytes` 与非字符串成员处理

- 修复位置：`thesis/experiments/llm_probe/src/flow_probe/ns3_field_roles.py:127`。
- 测试位置：`thesis/experiments/llm_probe/tests/test_ns3_field_roles.py:247`。
- `validate_group_disjoint_splits` 在遍历前拒绝 `str` 和 `bytes`，不再把完整组号拆成字符或字节整数。
- 集合成员在登记所有者前逐项校验，非字符串成员统一抛出 `NS3FieldRolesError`，错误包含切分名、`group_id` 和字符串契约上下文。
- 原有跨切分重叠判断保持不变，错误继续列出冲突组号和两个切分名。
- 独立只读探针分别传入 `"group-a"`、`b"group-a"` 和 `["group-a", 42]`，三类输入均按预期抛出 `NS3FieldRolesError`；合法的不相交集合、空映射和空切分仍保持原行为。

### 2. JSON、UTF-8 与读取异常包装

- 修复位置：`thesis/experiments/llm_probe/src/flow_probe/ns3_field_roles.py:41`。
- 测试位置：`thesis/experiments/llm_probe/tests/test_ns3_field_roles.py:118`。
- JSON 语法错误被转换为 `NS3FieldRolesError`，消息包含源路径、`JSON` 和中文失败上下文，`__cause__` 为原始 `JSONDecodeError`。
- UTF-8 解码错误被转换为 `NS3FieldRolesError`，消息包含源路径、`UTF-8` 和中文失败上下文，`__cause__` 为原始 `UnicodeDecodeError`。
- 文件读取错误被转换为 `NS3FieldRolesError`，消息包含源路径和中文读取失败上下文，`__cause__` 保留原始 `OSError` 子类。
- 独立只读探针使用损坏 JSON、模拟 UTF-8 解码失败和模拟 `PermissionError` 验证上述三条异常路径，异常类型、消息上下文与异常链均符合要求。

## 回归核对

- 当前三个任务文件的 Git 对象哈希分别为 `18b1e2f`、`f5a7c8c` 和 `f5bcb44`，与修复审查包记录完全一致。
- 字段角色配置未改动，五个角色计数仍为 5、12、6、15、8，合计 46。
- `CSV_FIELDS` 当前包含 46 个互异字段；配置字段同样为 46 个互异字段，二者集合完全一致。
- 生产代码继续直接导入并使用 `flow_probe.ns3_truth.CSV_FIELDS`，没有复制 46 字段全集。
- `model_input_observable` 仍精确等于五个允许字段，角色内重复、跨角色重复、遗漏、未知字段和禁止输入检查均未受修复影响。
- 新增六项边界测试分别覆盖损坏 JSON、无效 UTF-8、文件读取失败、`str`、`bytes` 和非字符串集合成员，并检查关键消息上下文与异常链。

## 历史流程边界

- 原首次实现的红测在收集期因 `ModuleNotFoundError` 失败，不构成需求行为红测。
- 实现报告没有改写该历史事实，并明确说明修复轮只为两个真实接口缺陷保存了行为级红绿证据。
- 用户已经接受上述历史流程偏差并将本次复审改为非阻塞，因此本复审不重复调用测试驱动技能、不删除已有正确实现，也不将该偏差计入当前问题数量。

## 验证记录

- 已读取任务简报、实现报告、首次审查报告、修复审查包和当前三个任务文件。
- 未重跑实现代理已有的 `pytest`；修复报告记录新增边界用例 `6 passed`、目标测试 `20 passed`、完整回归 `206 passed`。
- 已执行独立只读 Python 探针，覆盖固定字段契约、三类切分边界、跨切分重叠、空映射、空切分和三类加载异常，命令退出码为 0。
- 已执行 `.venv/bin/black --check src/flow_probe/ns3_field_roles.py tests/test_ns3_field_roles.py`，两个文件无需改写。
- 已执行 `.venv/bin/ruff check src/flow_probe/ns3_field_roles.py tests/test_ns3_field_roles.py`，检查通过。

## 修改范围

- 新增本复审报告：`.Codex/docs/sdd/task-3-ns3-field-roles-rereview.md`。
- 未修改字段角色源码、配置、测试、服务器文件或 Git 状态。
