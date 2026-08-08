# DEDALE orange_dmz 标签关联过程笔记

## 开始时间

- 2026-07-21 12:47:19 CST。

## 官方依据

- DEDALE V2 官方数据页：<https://entrepot.recherche.data.gouv.fr/dataset.xhtml?persistentId=doi:10.57745/Y5JLDG>。
- 官方下载与标注说明：<https://dedale.inria.fr/download.html>。
- 官方标签脚本提交：`f148722e`，仓库为 <https://gitlab.inria.fr/mlanvin/dedale_labeling>。

## 只读预审计

- `zeek_orange_dmz.zip` 与 `cicflowmeter_orange_dmz.zip` 均通过 CRC 检查和官方 MD5 校验。
- 两个归档各含 D1 至 D28 的 28 个已标注连接流文件。
- Zeek 共 839,054 行，标签分布为 `0: 839052`、`1: 2`、`2: 0`。
- CICFlowMeter 共 1,142,442 行，标签分布为 `0: 1142440`、`1: 2`、`2: 0`。
- Zeek 前两周 413,685 行，CICFlowMeter 前两周 566,462 行，均全部为标签 0。
- 两端全部记录的 `date` 与 `ts` 按 UTC 换算一致，允许误差 10 微秒时错配均为 0。
- 两端仅有的两条攻击流均位于 D15，五元组、时间戳、攻击步骤、MITRE 战术/技术和说明一致。

## 首轮关联发现

- Zeek 的 `uid` 是 Zeek 连接标识；CICFlowMeter 的 `uid` 是五元组与协议号的拼接值，不能直接连接。
- Zeek 使用 `tcp/udp/icmp`，CICFlowMeter 使用 `6/17/1`，必须先规范化协议。
- 协议规范化后，CICFlowMeter 中 799,831 条同向记录和 157 条反向记录能在相同五元组下于 1 秒内找到 Zeek 候选，合计 799,988 条，占 70.0244%。
- 其余 342,454 条尚未证明可唯一关联，不能传播或覆盖标签；需要继续审计更宽起点差、区间重叠和候选歧义。

## 当前检查点

全部检查点完成。只读审计工具、定向测试、完整回归、v3 正式运行、本地归档和详细报告均已完成。

## 测试驱动记录

### 任务 1：字段契约

- 失败测试：服务器运行 `uv run --no-sync pytest tests/test_dedale_audit.py -q`，收集阶段因 `ModuleNotFoundError: No module named 'flow_probe.dedale_audit'` 失败，原因符合预期。
- 最小实现：新增协议规范化、UTC 纳秒时间解析、D1 至 D28 阶段分类和三类标签校验。
- 通过测试：同一服务器命令返回 `17 passed in 0.02s`。
- 本机格式化与静态检查：Black 未改动文件，Ruff 全部通过。

### 任务 2：关联裁决

- 失败测试：服务器运行同一定向命令，收集阶段因缺少 `AssociationDecision` 等关联接口失败，原因符合预期。
- 最小实现：新增不含 `uid` 的不可变流记录、规范化五元组、同向/反向候选索引、起点容差或区间重叠裁决，以及歧义、未匹配和标签冲突结果。
- 标签纪律：裁决仅比较两侧官方标签；测试明确确认标签冲突不会改变任一记录的标签。
- 通过测试：服务器返回 `25 passed in 0.03s`。
- 本机格式化与静态检查：Black 完成格式化，Ruff 全部通过。

### 任务 3：全量审计与正式制品

- 失败测试：全量审计接口、CIC 微秒时长换算和多对一目标复用统计均先在服务器观察到预期失败，再分别实现。
- 最小实现：流式读取 28 个 Zeek CSV 和 CIC ZIP 内 28 个 CSV；输出输入清单、字段与标签审计、绝对 UTC 阶段划分、攻击包络、唯一候选关联、歧义、未匹配、标签冲突和目标复用统计。
- 单位修复：官方 CICFlowMeter 字段说明确认 `duration` 为微秒。错误按秒解释时产生 367,135 条虚假跨校准/测试边界记录；除以 `1_000_000` 后 CIC 仅有 7 条跨界，Zeek 为 8 条。
- 通过测试：服务器定向测试返回 `31 passed`，完整回归返回 `281 passed in 3.25s`。
- 正式运行：v3 共审计 CIC 1,142,442 条；唯一候选匹配 1,138,471 条，占 99.6524%；歧义 2,015 条，未匹配 1,956 条，标签冲突 0。
- 一一配对边界：匹配落到 799,914 个唯一 Zeek 目标，其中 44,368 个目标被复用；严格一对一 CIC 子集为 755,546 条。
- 服务端制品：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/data-audit/dedale-orange-dmz-v2-20260721-v3/`。
- 本机制品：`/Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/data-audit/dedale-orange-dmz-v2-20260721-v3/`。
- 最终本机验证：8 个 Markdown/JSON 文件通过 Prettier，Python 文件通过 Black 与 Ruff，Shell 脚本通过 `bash -n`，`uv lock --check` 与 `git diff --check` 通过。
- 结束时间：2026-07-21 14:44:45 CST。
