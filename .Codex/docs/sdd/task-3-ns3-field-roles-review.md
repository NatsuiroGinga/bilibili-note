# 任务 2：ns-3 字段角色与防泄漏契约独立审查

## 审查结论

- **计划符合性：不通过。** 字段清单、唯一归类、禁止输入和组级互斥等功能要求已经实现，但实现报告保存的红测只是测试收集阶段的 `ModuleNotFoundError`，没有观察到字段遗漏、重复、禁止输入和跨切分重叠各自按预期失败，不满足本任务强制测试驱动要求。
- **代码质量：不批准。** 当前字段契约本身正确，但切分接口会把单个字符串按字符集合处理，格式损坏的 JSON 也不会产生带配置路径的中文加载错误。这两项接口边界缺陷需要在任务 2 范围内修复并补充回归测试。
- **问题数量：严重 0，重要 3，次要 0。**

## 重要问题

### 1. 切分值为字符串时会把字符误当作 `group_id`

- 位置：`thesis/experiments/llm_probe/src/flow_probe/ns3_field_roles.py:115`
- 位置：`thesis/experiments/llm_probe/src/flow_probe/ns3_field_roles.py:120`
- 位置：`thesis/experiments/llm_probe/tests/test_ns3_field_roles.py:196`
- 严重程度：重要。
- 事实：接口标注接受 `Collection[str]`，而 Python 的 `str` 本身满足该协议。实现直接迭代 `group_ids`，因此传入单个组号字符串时会逐字符登记所有者。
- 复现：传入 `{"train": "group-a", "validation": "group-b"}` 后，函数报告 `group_id 'g'` 在两个切分中冲突，而不是拒绝无效的集合形态或按完整组号处理。
- 影响：调用方一次漏写列表或集合括号，就会得到虚假的字符级冲突；若两个字符串没有公共字符，还可能错误通过。此行为破坏“完整 `group_id` 为最小单位”的防泄漏语义。
- 缺失测试：现有成功用例覆盖 `set`、`list` 和 `tuple`，但没有覆盖同样符合当前类型标注的字符串值。
- 任务内修复要求：明确拒绝 `str` 和 `bytes` 形式的切分值，并对集合成员进行字符串校验；新增字符串值和非字符串成员的负向测试。

### 2. JSON 解析失败没有配置路径和中文加载上下文

- 位置：`thesis/experiments/llm_probe/src/flow_probe/ns3_field_roles.py:41`
- 位置：`thesis/experiments/llm_probe/tests/test_ns3_field_roles.py:109`
- 严重程度：重要。
- 事实：`read_text` 与 `json.loads` 位于异常包装之外。格式损坏的配置会直接抛出英文 `json.decoder.JSONDecodeError`，错误文本只有行列位置，不包含传入的配置路径，也不统一为 `NS3FieldRolesError`。
- 复现：让读取结果为 `{` 后，错误为 `Expecting property name enclosed in double quotes: line 1 column 2 (char 1)`，无法从错误本身确认是哪一个角色配置加载失败。
- 影响：后续命令入口加载快照或用户指定配置时，调用方无法依赖统一异常类型，日志也缺少定位文件所需的上下文。
- 缺失测试：现有测试覆盖合法 JSON 的顶层类型和成员类型，但没有覆盖 JSON 语法损坏、编码失败或文件读取失败。
- 任务内修复要求：捕获 JSON 解析、解码和文件读取异常，转换为包含 `source_path` 与具体原因的中文 `NS3FieldRolesError`，同时保留原异常作为原因；新增相应负向测试。

### 3. 红测证据是收集错误，不是需求行为的预期失败

- 位置：`.Codex/docs/sdd/task-3-ns3-field-roles-report.md:21`
- 位置：`.Codex/docs/sdd/task-3-ns3-field-roles-report.md:31`
- 位置：`.superpowers/sdd/task-2-brief.md:15`
- 位置：`.superpowers/sdd/task-2-brief.md:19`
- 严重程度：重要。
- 事实：实现报告记录的唯一红测结果是 `ModuleNotFoundError: No module named 'flow_probe.ns3_field_roles'`，并明确说明测试在收集阶段失败。
- 影响：测试没有执行到字段遗漏、重复、禁止输入或组重叠断言，因而没有证明这些测试会在缺少相应行为时失败。该证据不满足“先观察预期失败，再做最小实现”的任务要求。
- 裁决边界：当前绿测能够证明现有实现满足这些断言，但不能替代行为级红测证据。因此该问题直接导致计划符合性不通过，不等同于当前功能必然错误。

## 逐项核对

| 核对项                                | 结果     | 证据与说明                                                                                                                                                                                                                 |
| ------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 角色名集合精确                        | 通过     | `ROLE_NAMES` 在 `ns3_field_roles.py:12` 固定为五个要求角色，`ns3_field_roles.py:45` 对集合做精确相等检查。                                                                                                                 |
| 46 字段恰好一次                       | 通过     | 当前 `CSV_FIELDS` 为 46 个互异字段；加载器在 `ns3_field_roles.py:65`、`ns3_field_roles.py:76` 和 `ns3_field_roles.py:82` 分别拒绝角色内重复、跨角色重复、遗漏与未知字段。只读探针得到角色计数 `5 + 12 + 6 + 15 + 8 = 46`。 |
| 角色内重复拒绝                        | 通过     | `ns3_field_roles.py:65` 使用计数器拒绝；`test_ns3_field_roles.py:157` 有负向测试。                                                                                                                                         |
| 跨角色重复拒绝                        | 通过     | `ns3_field_roles.py:72` 建立字段所有者并拒绝多所有者；`test_ns3_field_roles.py:167` 有负向测试。                                                                                                                           |
| 成员非字符串拒绝                      | 通过     | `ns3_field_roles.py:63` 在计数前校验成员类型；`test_ns3_field_roles.py:127` 有负向测试。                                                                                                                                   |
| `model_input_observable` 精确允许列表 | 通过     | `ns3_field_roles.py:19` 固定五个允许字段，`ns3_field_roles.py:97` 同时拒绝缺失、禁止字段和顺序变化；JSON 的五项与其一致。                                                                                                  |
| 加载错误清楚                          | 不通过   | 语义错误信息清楚，但 `ns3_field_roles.py:41` 未包装 JSON 解析、解码和读取异常。                                                                                                                                            |
| 直接复用 `ns3_truth.CSV_FIELDS`       | 通过     | `ns3_field_roles.py:10` 直接导入，`ns3_field_roles.py:82` 以其作为字段全集；生产代码没有复制 46 字段全集。                                                                                                                 |
| JSON 与代码契约一致                   | 通过     | 当前 JSON 角色计数为 5、12、6、15、8，字段和值顺序与任务简报完全一致；五个模型输入字段与 `ALLOWED_MODEL_INPUTS` 一致。                                                                                                     |
| 任意两个命名切分共享组时拒绝          | 通过     | `ns3_field_roles.py:119` 记录所有者，`ns3_field_roles.py:123` 在第二个切分遇到同组时失败，错误包含完整冲突组号和两个切分名；`test_ns3_field_roles.py:208` 验证三项信息。                                                   |
| 空映射                                | 合理     | 当前返回 `None`。在该函数只负责验证集合不相交的前提下，空映射满足空真值，不应在这里附加切分完整性职责。                                                                                                                    |
| 空切分                                | 合理     | 当前允许命名切分对应空集合，且不会影响其他切分的互斥检查；数据完整性应由调用方的独立契约处理。                                                                                                                             |
| 不同集合                              | 部分通过 | `set`、`list` 和 `tuple` 行为一致且已有成功用例；字符串也属于当前标注的 `Collection[str]`，但被错误逐字符处理，详见重要问题 1。                                                                                            |
| 遗漏测试                              | 通过     | `test_ns3_field_roles.py:137` 删除一个字段并验证错误。                                                                                                                                                                     |
| 重复测试                              | 通过     | `test_ns3_field_roles.py:157` 和 `test_ns3_field_roles.py:167` 分别覆盖角色内与跨角色重复。                                                                                                                                |
| 禁止输入测试                          | 通过     | `test_ns3_field_roles.py:177` 覆盖加入禁止字段和移除允许字段。                                                                                                                                                             |
| 组重叠测试                            | 通过     | `test_ns3_field_roles.py:208` 构造训练与验证共享同一个完整 `group_id`。                                                                                                                                                    |

## 验证记录

- 已读取需求简报、实现报告、工作区差异包、三个任务文件和 `ns3_truth.py` 的 `CSV_FIELDS`。
- 已对当前代码执行只读 Python 探针：`CSV_FIELDS` 数量为 46，互异字段数量为 46，五个角色合计为 46。
- 已确认空映射和两个空切分均返回 `None`。
- 已确认字符串切分值复现字符级错误：冲突组被报告为 `'g'`。
- 已确认损坏 JSON 直接抛出不含配置路径的英文 `JSONDecodeError`。
- 按仓库规则未在本机运行 `pytest`；服务器测试结果依据实现报告中的目标测试 `14 passed` 与完整回归 `193 passed`，本审查不把报告中的既有结果当作独立红测证据。

## 审查范围

- 本报告只审查任务 2 的字段角色配置、加载器、切分互斥函数、测试和测试驱动证据。
- 未修改代码、配置、测试、服务器文件或 Git 状态。
- 未审查或建议任务 2 以外的流水线集成。
