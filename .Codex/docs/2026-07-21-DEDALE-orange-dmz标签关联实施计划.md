# DEDALE orange_dmz 标签关联实施计划

> **执行要求：** 当前实现代理按 `superpowers:test-driven-development` 逐项执行；主代理负责独立复核。每个行为必须先在服务器观察测试按预期失败，再做最小实现并复跑。

**目标：** 建立一个只读、可复现的 DEDALE 2.0 `orange_dmz` 审计工具，验证官方标签、UTC 时间轴以及 Zeek 与 CICFlowMeter 记录的高置信关联范围，并生成不含原始连接标识的汇总制品。

**架构：** 工具直接流式读取 Zeek 已解压的 28 个 `conn_labeled.csv` 和 CICFlowMeter ZIP 内的 28 个已标注 CSV，不修改或重新标注任何数据。关联分为官方标签契约检查、协议与端口规范化、同向或反向五元组候选检索、时间差与区间重叠裁决四层；只统计唯一高置信匹配、歧义、未匹配和标签冲突，不输出推断标签。

**技术栈：** Python 3.10 标准库、`pytest`、Black、Ruff、Bash、`uv`。

## 全局约束

- 不占用 GPU，不下载整套 DEDALE，不解压 CICFlowMeter 归档。
- 原始 ZIP、已解压 Zeek 文件和现有实验制品只读；每次运行使用唯一输出目录。
- 标签 `0/1/2` 分别保留为良性、攻击、攻击相关；不得把缺失标签补成任一类别。
- D1 至 D14 仅用于训练、验证或阈值校准；D15 至 D28 仅用于时间外推测试。
- 官方八天攻击包络固定为 `[2025-01-06 00:00:00, 2025-01-14 00:00:00)` UTC，但包络内标签 0 不得改成攻击。
- Python 仅在本机运行 Black 和 Ruff；所有 `pytest` 统一在服务器项目 `uv` 环境运行。
- 新增代码范围固定为：
  - `thesis/experiments/llm_probe/src/flow_probe/dedale_audit.py`
  - `thesis/experiments/llm_probe/tests/test_dedale_audit.py`
  - `thesis/experiments/llm_probe/scripts/run_dedale_orange_dmz_audit.sh`
  - `thesis/experiments/llm_probe/pyproject.toml` 仅增加命令入口
- 正式运行制品写入唯一目录 `thesis/experiments/llm_probe/runs/data-audit/dedale-orange-dmz-v2-20260721-v3/`，包含 `audit.json`、`input_manifest.json` 和 `console.log`。v1 保留单位错误诊断，v2 保留修正单位后的中间结果，二者均不得作为正式结果引用。

---

### 任务 1：字段、标签与 UTC 时间契约

**文件：**

- 创建：`thesis/experiments/llm_probe/tests/test_dedale_audit.py`
- 创建：`thesis/experiments/llm_probe/src/flow_probe/dedale_audit.py`

**接口：**

- `normalize_protocol(value: str) -> str`：把 `6/17/1` 规范为 `tcp/udp/icmp`，保留未知协议的小写值。
- `parse_utc_date(value: str) -> float`：把带纳秒小数的无时区字符串严格解释为 UTC Unix 时间。
- `classify_day(day_id: int) -> str`：D1 至 D14 返回 `calibration`，D15 至 D28 返回 `test`，其他日序拒绝。
- `validate_label(value: str) -> str`：只接受 `0/1/2`。

- [x] **步骤 1：先编写字段契约测试**

测试必须覆盖协议映射、纳秒 UTC 时间、D14/D15 边界、非法日序和非法标签。

- [x] **步骤 2：在服务器观察预期失败**

运行：

```bash
uv run --no-sync pytest tests/test_dedale_audit.py -q
```

预期：因 `flow_probe.dedale_audit` 尚不存在而收集失败。

- [x] **步骤 3：实现最小字段契约**

实现只包含上述四个纯函数、明确中文错误信息和常量；不读取真实数据。

- [x] **步骤 4：在服务器观察测试通过**

运行同一步骤 2，预期字段契约测试全部通过。

### 任务 2：五元组与时间关联裁决

**文件：**

- 修改：`thesis/experiments/llm_probe/tests/test_dedale_audit.py`
- 修改：`thesis/experiments/llm_probe/src/flow_probe/dedale_audit.py`

**接口：**

- `FlowIdentity`：保存规范化协议、源地址、源端口、目的地址和目的端口，可生成反向身份。
- `FlowRecord`：保存数据源、日序、UTC 起点、结束点、五元组和官方标签。
- `associate_record(record, index, start_tolerance_seconds) -> AssociationDecision`：按同向优先、反向次之检索；只有候选唯一且起点差不超过阈值，或候选唯一且区间发生重叠时返回高置信匹配；多候选必须返回歧义。

- [x] **步骤 1：先编写关联行为测试**

测试必须分别证明：数字协议能与文本协议匹配；同向唯一匹配；反向唯一匹配；时间超限不匹配；多个候选返回歧义；标签冲突只计数不覆盖；同名 `uid` 不参与关联。

- [x] **步骤 2：在服务器观察新增测试按预期失败**

运行任务 1 的测试命令，预期因关联接口尚不存在而失败。

- [x] **步骤 3：实现最小关联逻辑**

采用五元组索引和按起点排序的候选列表；输出匹配方向、匹配依据、起点差、候选数和标签是否冲突，不输出新标签。

- [x] **步骤 4：在服务器观察测试通过**

运行任务 1 的测试命令，预期全部通过。

### 任务 3：只读全量审计命令与正式制品

**文件：**

- 修改：`thesis/experiments/llm_probe/tests/test_dedale_audit.py`
- 修改：`thesis/experiments/llm_probe/src/flow_probe/dedale_audit.py`
- 创建：`thesis/experiments/llm_probe/scripts/run_dedale_orange_dmz_audit.sh`
- 修改：`thesis/experiments/llm_probe/pyproject.toml`

**接口：**

- `audit_dedale(zeek_dir: Path, cic_zip: Path, start_tolerance_seconds: float) -> dict[str, object]`：返回输入清单、字段版本、每日行数、标签分布、UTC 一致性、阶段计数、八天包络检查及关联统计。
- 命令入口 `flow-probe-audit-dedale`：接收 `--zeek-dir`、`--cic-zip`、`--output` 和 `--manifest-output`。

- [x] **步骤 1：先编写小型 ZIP/CSV 集成测试**

测试临时构造两个 Zeek 日文件和一个 CIC ZIP，验证 D14/D15 阶段、标签计数、同向/反向/歧义/未匹配统计、UTC 错配拒绝以及结果不包含原始 UID、IP 和端口。

- [x] **步骤 2：在服务器观察集成测试按预期失败**

运行任务 1 的测试命令，预期因 `audit_dedale` 尚不存在而失败。

- [x] **步骤 3：实现流式读取、命令入口和启动脚本**

启动脚本检查 28 个 Zeek CSV、两个输入归档和唯一输出目录；审计命令只创建结果目录及三个制品，不修改输入。

- [x] **步骤 4：格式化与静态检查**

本机运行：

```bash
black src/flow_probe/dedale_audit.py tests/test_dedale_audit.py
ruff check src/flow_probe/dedale_audit.py tests/test_dedale_audit.py
bash -n scripts/run_dedale_orange_dmz_audit.sh
```

- [x] **步骤 5：服务器测试与全量只读运行**

先运行定向测试，再运行完整测试；随后执行启动脚本，输出到唯一目录。验收要求：28 个日文件、两端 UTC 错配为 0、前两周非良性为 0、非良性不越出八天包络、2 条攻击语义一致、所有关联类别之和等于 CIC 总行数。

- [x] **步骤 6：归档与最终检查**

同步服务器结果摘要到本机运行目录，更新 `.Codex/docs/2026-07-21-DEDALE-orange-dmz标签关联审计.md`，并运行 Prettier 与 `git diff --check`。

## 阻塞条件

- 任一输入归档 MD5 或 CRC 变化。
- 日序不是连续 D1 至 D28，或字段版本跨日漂移。
- `date` 与 `ts` 无法统一解释为 UTC。
- 官方标签字段缺失、非法或前两周出现非良性标签。
- 需要把未匹配流强行赋予推断标签才能继续。

## 当前状态

- [x] 官方 V2 元数据、标签语义和使用协议核验。
- [x] 两个归档 CRC、字段、28 天覆盖、UTC 与标签分布只读预审计。
- [x] 首轮五元组关联预审计，识别 `uid` 与协议编码差异。
- [x] 按任务 1 至任务 3 完成测试驱动实现和正式 v3 制品。

**状态：已完成。** 服务端定向测试 31 项通过，完整回归 281 项通过；正式结果已同步到本机，详细结论见 `.Codex/docs/2026-07-21-DEDALE-orange-dmz标签关联审计.md`。
