# 任务 1：ns-3 队列真值验证器独立评审

## 裁决

- **规范符合：不符合。** 验证器没有强制 `jitter_stream_base=100` 和 `jitter_max_ms=40`，会接受规范明确禁止的随机配置。
- **代码质量：不批准。** 该缺口直接影响数据可复现性，而且现有测试把违规值当作合法基线，无法阻止回归。
- **阻断修复：** 增加固定抖动参数校验，修正合法测试夹具，并添加“组内恒定但固定值错误”的拒绝测试。

## 审查范围

- 唯一需求基线：`.Codex/docs/sdd/task-1-ns3-validator-brief.md`。
- 实施证据：`.Codex/docs/sdd/task-1-ns3-validator-report.md`。
- 完整差异包：`/tmp/task-1-ns3-validator-review.patch`。
- 补充运行证据：服务器目标测试 16 项、完整套件 157 项、真实数据 21 个文件与 2520 个窗口均通过。
- 本评审执行静态逐条核对，没有重复运行实施者已经完成的格式检查，也没有在本机运行 `pytest`。

## 发现

### P1：固定抖动参数未强制，违规数据会被判定为合法

**位置：**

- `thesis/experiments/llm_probe/src/flow_probe/ns3_truth.py:303`
- `thesis/experiments/llm_probe/src/flow_probe/ns3_truth.py:315`
- `thesis/experiments/llm_probe/tests/test_ns3_truth.py:104`
- `thesis/experiments/llm_probe/tests/test_ns3_truth.py:152`

**规范要求：** `jitter_stream_base` 与 `jitter_max_ms` 在组内必须恒定，当前固定值还必须分别为 `100` 和 `40`。

**实际实现：** `_validate_group_constants` 只把两个字段与组内首行比较。因此，只要 120 行都使用相同值，任意非负有限值都会通过。文件中没有对应 `100` 和 `40` 的常量或等值判定。

**直接证据：** 测试合法夹具使用 `jitter_stream_base=1000`、`jitter_max_ms=5`，随后七个场景的通过测试均调用该夹具并断言验证成功。这不是单纯缺少测试，而是现有测试明确证明验证器会放行违规配置。

**影响：** 随机流编号和启动相位范围发生漂移时，数据仍可进入 PINN 训练。服务器上 16 项目标测试、157 项完整测试以及 21 个真实文件通过，只能证明当前样本内部一致，不能证明错误固定值会被拒绝。

**修复建议：**

1. 在 `ns3_truth.py` 定义固定值，例如 `JITTER_STREAM_BASE = Decimal("100")` 和 `JITTER_MAX_MS = Decimal("40")`。
2. 对每组首行或每一行执行固定值比较，并保留现有组内恒定检查；错误规则应明确写为“抖动配置”，并报告文件、组、字段、期望值和实际值。
3. 将合法夹具改为 `100` 和 `40`。
4. 分别增加两项拒绝测试：全组 `jitter_stream_base` 恒定为错误值；全组 `jitter_max_ms` 恒定为错误值。现有“第 80 行发生变化”测试应保留，用于覆盖组内漂移。

### P2：高风险契约缺少直接回归测试

**位置：**

- `thesis/experiments/llm_probe/tests/test_ns3_truth.py:152`
- `thesis/experiments/llm_probe/tests/test_ns3_truth.py:184`
- `thesis/experiments/llm_probe/tests/test_ns3_truth.py:268`

**具体缺口：**

- 没有测试 v3 模式错误，以及 42 字段缺失、多出、重复和乱序后仍按字段名解析。
- 没有测试 119 个窗口、重复或乱序 `window_index`、窗口长度错误、时间不连续和队列首尾不连续。
- 没有测试 `topology_id`、`queue_model`、`seed` 或 `run` 的组内漂移，也没有测试跨文件复用 `group_id`。
- 没有对必需队列丢弃缺失、随机丢包场景无下游误码丢弃、非随机场景出现下游误码丢弃建立负向测试。
- 命令测试直接调用 `main()`，没有验证安装后的 `flow-probe-validate-ns3-truth` 控制台入口；一个或多个输入中的多文件聚合也没有测试。

**影响：** 当前实现中这些判定路径静态核对基本正确，但没有测试保护。服务器通过数量不会覆盖未构造的失败输入，后续重构可能在完整 group、字段契约或丢弃来源上静默退化。

**修复建议：** 使用参数化变异测试从一份修正后的合法 120 窗口夹具生成单一违规点，并逐项断言错误信息同时包含文件名、`group_id` 和规则名。至少补齐字段契约、完整 group、连续性、组内常量、丢弃规则和多文件聚合六类测试；控制台入口可用安装环境中的命令烟雾测试覆盖。

## 逐项核对

| 核对项                   | 结论                     | 差异证据                                                                           |
| ------------------------ | ------------------------ | ---------------------------------------------------------------------------------- |
| v3 与精确 42 字段        | 实现符合，测试不足       | `_validate_header` 位于 `ns3_truth.py:166`；模式与场景判定在 `_parse_window` 中    |
| 完整 group 与唯一标识    | 实现符合，测试不足       | `_complete_windows` 位于 `ns3_truth.py:327`；跨文件标识检查位于 `ns3_truth.py:591` |
| 固定拓扑与组内配置       | 部分符合                 | 拓扑、队列、种子和运行号恒定检查存在；抖动参数只检查恒定，未检查固定值             |
| 窗口长度、时间和队列连续 | 实现符合，测试不足       | `_validate_timeline` 位于 `ns3_truth.py:348`                                       |
| 标签、暴露比例与阶段     | 实现符合                 | `_validate_labels` 位于 `ns3_truth.py:375`，窗口 50 被识别为部分暴露的过渡状态     |
| 容量与服务预算           | 实现符合                 | `_validate_capacity` 位于 `ns3_truth.py:441`，窗口 59 与窗口 60 以后分支符合需求   |
| 流量分解、守恒与保存残差 | 实现符合                 | `_validate_row` 位于 `ns3_truth.py:261`                                            |
| 隐藏设备丢弃             | 实现符合                 | `_validate_row` 同时拒绝设备丢弃字节或包非零                                       |
| 队列规则与下游误码丢弃   | 实现符合，测试不足       | `_validate_drop_rules` 位于 `ns3_truth.py:491`                                     |
| `error_stream` 与误码率  | 实现符合                 | `_validate_error_model` 位于 `ns3_truth.py:459`                                    |
| JSON 摘要                | 实现符合                 | 摘要构造位于 `ns3_truth.py:607` 至 `ns3_truth.py:646`                              |
| 命令入口                 | 静态符合，入口未执行覆盖 | `pyproject.toml:50` 映射到 `flow_probe.ns3_truth:main`                             |

## 批准条件

1. 修复 P1，并证明全组恒定但不等于 `100` 或 `40` 时验证失败。
2. 合法夹具改用规范固定值，服务器重新运行目标测试和完整测试套件。
3. 至少补齐 P2 中字段契约与完整 group 的关键负向测试；其余测试可在同一变异测试表中完成。

在上述条件满足前，本任务维持 **规范不符合、代码质量不批准**。
