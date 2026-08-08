# 任务 1：ns-3 v4 契约修复后独立复审

## 裁决

- **计划符合性：通过。** 原审查提出的 3 个重要问题均已实质修复，需求简报中的 v4 验证器门禁、测试、完整回归、编译和真实冒烟证据齐全。
- **代码质量：批准。** 当前发现严重问题 0 项、重要问题 0 项、次要问题 0 项。
- C++ 生成器自动化集成仍由任务 3 的正式运行器承担，作为已知后续风险，不阻止本轮批准。

## 审查范围

- 需求简报：`.superpowers/sdd/task-1-brief.md`。
- 更新后的实现报告：`.Codex/docs/sdd/task-2-ns3-v4-contract-report.md`。
- 原独立审查：`.Codex/docs/sdd/task-2-ns3-v4-contract-review.md`。
- 最新差异包：`.superpowers/sdd/review-task-1-fix-working-tree.diff`。
- 当前生产代码：`thesis/experiments/llm_probe/src/flow_probe/ns3_truth.py`。
- 当前测试：`thesis/experiments/llm_probe/tests/test_ns3_truth.py`。
- 服务端修复日志与 `review2` 冒烟制品，只读核对，未重跑或改写。

## 原问题逐项复验

| 原重要问题                              | 当前实现                                                                                | 测试覆盖                                                                 | 独立反例结果                                       | 裁决   |
| --------------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | -------------------------------------------------- | ------ |
| 固定 46 字段顺序未验证                  | `ns3_truth.py:179-197` 在字段集合合法后要求 `tuple(fieldnames) == CSV_FIELDS`           | `test_ns3_truth.py:575-582` 交换前两列表头及对应值                       | 当前验证器以“字段顺序”拒绝                         | 已关闭 |
| 丢弃字节与包数可跨窗拼接                | `ns3_truth.py:646-668` 对每个窗口分别检查队列丢弃和误码丢失的字节/包零值一致性          | `test_ns3_truth.py:386-428` 参数化覆盖队列丢弃与随机误码两种拼接         | 当前验证器分别以“队列丢弃计量”和“误码丢弃计量”拒绝 | 已关闭 |
| 非零初始队列和超过 `50p` 的包状态可通过 | `ns3_truth.py:448-471` 要求首窗 L3 字节与包状态均为零，并检查每窗起止包数不超过该窗上限 | `test_ns3_truth.py:515-564` 覆盖首窗字节非零、首窗包非零和起止包状态越界 | 当前验证器分别以“初始队列”和“队列包状态上限”拒绝   | 已关闭 |

复验同时确认：实现没有从 `50p` 推导 L3 字节上限。L3 字节状态只要求首窗为零、数值非负、守恒成立并跨窗连续；包状态另受队列包数上限约束，量纲处理正确。

## 测试驱动证据

服务端日志目录：

`/root/autodl-tmp/thesis/experiments/llm_probe/runs/ns3-data/validator-fix-tests-20260720`

| 行为              | 红测日志与结果                                                | 绿测日志与结果                                      |
| ----------------- | ------------------------------------------------------------- | --------------------------------------------------- |
| 固定字段顺序      | `red-reordered-fields.log`：1 项因未抛异常而失败              | `green-reordered-fields.log`：1 项通过              |
| 逐窗字节/包一致性 | `red-cross-window-loss-measurement.log`：2 项因未抛异常而失败 | `green-cross-window-loss-measurement.log`：2 项通过 |
| 首窗双零与包上限  | `red-queue-state-bounds.log`：4 项因未抛异常而失败            | `green-queue-state-bounds.log`：4 项通过            |

红测失败原因与原审查反例一致，绿测没有通过更换夹具或削弱断言绕过问题。

## 最终行为门禁

- `uv run --no-sync pytest tests/test_ns3_truth.py`：**45/45 通过**，日志为 `green-validator-module-final.log`。
- `uv run --no-sync pytest`：**200/200 通过**，日志为 `full-pytest-final.log`。
- `env USER=ns3builder ./ns3 build scratch/flow-probe-queue-truth`：构建成功，日志为 `ns3-build.log`。
- 本地 `.venv/bin/black --check src/flow_probe/ns3_truth.py tests/test_ns3_truth.py`：通过。
- 本地 `.venv/bin/ruff check --no-cache src/flow_probe/ns3_truth.py tests/test_ns3_truth.py`：通过。
- 按仓库规则未在本机运行 pytest；上述 pytest 结果来自本次只读回读的服务器原始日志。

## `review2` 真实冒烟

服务端目录：

`/root/autodl-tmp/thesis/experiments/llm_probe/runs/ns3-data/v4-fix-smoke-20260720-task1-review2`

- `dos-udp-high-seed42.csv`：121 行含表头、46 列、120 个窗口，验证状态为 `passed`，qdisc 丢弃 L3 字节为 36,138,304，双残差非零窗口均为 0。
- `benign-random-loss-seed42.csv`：121 行含表头、46 列、120 个窗口，验证状态为 `passed`，下游误码 PPP 帧字节为 46,376，双残差非零窗口均为 0。
- `smoke-audit.log` 与两份验证摘要内容一致。
- `review1` 因服务端未安装控制台脚本而保留失败日志；`review2` 使用同一验证器的 Python 模块入口，在新目录重新生成并成功验证，没有覆盖失败制品。

## 服务器状态

- GPU 当前没有计算进程。
- `screen -ls` 返回无会话。
- `/root/autodl-tmp` 数据盘使用率 54%，可用空间 24 GiB，未达到告警阈值。

## 残余风险

- 当前 Python 自动化测试仍不直接执行 C++ 生成器。现有编译和两组真实冒烟足以满足任务 1 门禁；任务 3 必须由正式运行器锁定生成器、验证器、逐组日志和制品清单的共同契约。
- 本轮复审只批准任务 1，不代表七场景三随机种子正式矩阵、字段角色契约或后续 PINN 训练已经完成。
