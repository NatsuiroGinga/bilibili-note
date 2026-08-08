# DEDALE 2.0 orange_dmz 标签与跨工具关联审计

## 结论

`zeek_orange_dmz.zip` 和 `cicflowmeter_orange_dmz.zip` 都已经包含官方逐流标签，**不需要执行外部标签传播**。本次工作的正确产物是可复现的关联覆盖审计，而不是生成一个新的“已标注”数据集。

最终 v3 结果表明：

- Zeek 共 839,054 条连接流，标签为 `0: 839052`、`1: 2`、`2: 0`。
- CICFlowMeter 共 1,142,442 条流程，标签为 `0: 1142440`、`1: 2`、`2: 0`。
- 两端仅有的 2 条攻击事件在 UTC 时间、规范化五元组、步骤、MITRE 战术/技术和说明上完全一致，标签冲突为 0。
- 1,138,471 条 CIC 记录得到唯一 Zeek 候选，覆盖率为 99.6524%；2,015 条为一对多歧义，1,956 条未匹配。
- 99.6524% **不是逐行一一对应率**。成功匹配只落到 799,914 个唯一 Zeek 目标；44,368 个 Zeek 目标被多个 CIC 记录复用，涉及 382,925 条 CIC，最大复用度为 899。
- 严格的一对一配对子集只有 755,546 条 CIC。任何跨工具特征级配对分析都应默认使用该子集，其余记录保留各自官方标签，不能强行合并。

## 官方语义与输入

### 官方依据

- [DEDALE V2 数据页](https://entrepot.recherche.data.gouv.fr/dataset.xhtml?persistentId=doi:10.57745/Y5JLDG)：四周数据、前两周仅良性、第三周开始 8 天 APT 场景。
- [官方标注与使用说明](https://dedale.inria.fr/download.html)：标签 `0/1/2` 的含义，以及前两周校准、后两周只测试的建议。
- [官方标签脚本](https://gitlab.inria.fr/mlanvin/dedale_labeling)：元数据固定提交 `f148722e`。
- [CICFlowMeter 官方字段说明](https://github.com/ahlashkari/CICFlowMeter/blob/master/ReadMe.txt)：`Flow duration` 的单位为微秒。

### 输入路径

- Zeek 已解压根目录：`/root/autodl-tmp/thesis/datasets/DEDALE-2.0/extracted/zeek_orange_dmz/orange_dmz/`。
- Zeek 原始归档：`/root/autodl-tmp/thesis/datasets/DEDALE-2.0/zeek_orange_dmz.zip`。
- CICFlowMeter 原始归档：`/root/autodl-tmp/thesis/datasets/DEDALE-2.0/cicflowmeter_orange_dmz.zip`。
- 两个归档均通过官方 MD5 和 CRC 检查；审计没有修改或解压 CICFlowMeter 归档。

## 字段与单位

### 共同关联字段

两端均提供：

- `date`、`ts`。
- `ip_src`、`port_src`、`ip_dst`、`port_dst`、`proto`。
- `duration`。
- `label`、`step`、`attack_step`、`tactic`、`technique`、`comments`。

### 必须处理的契约差异

1. Zeek 的 `uid` 是连接标识；CICFlowMeter 的 `uid` 是由五元组和协议号拼接的字符串。两列同名但语义不同，禁止直接连接。
2. Zeek 协议为 `tcp/udp/icmp`，CICFlowMeter 协议为 `6/17/1`。关联前统一为文本协议。
3. Zeek `duration` 单位为秒，CICFlowMeter `duration` 单位为微秒。CIC 值必须除以 `1_000_000` 后才能构造结束时间。
4. 两端的 `date` 都是不带时区标记的文本，但与 Unix `ts` 按 UTC 换算完全一致。本次对全部 1,981,496 条记录逐行核验，允许误差 10 微秒时错配为 0。

### 单位错误追溯

首轮正式运行错误地把 CIC `duration` 当作秒，产生 367,135 条虚假跨界连接。全量诊断确认：

- CIC `duration` 中位数为 5,069,857，P95 为 119,997,880，最大值为 120,000,000。
- 按官方微秒单位换算，最大时长恰为 120 秒。
- 误当秒时跨 D14/D15 边界 367,135 条；按微秒时只有 7 条。

该错误通过新增回归测试修复。首轮目录保留为失败诊断制品，不得引用其关联结果。

## 四周时间轴

### 固定边界

- D1：2024-12-23。
- D14：2025-01-05。
- D15：2025-01-06。
- D28：2025-01-19。
- 校准区间：`[2024-12-23 00:00:00, 2025-01-06 00:00:00)` UTC。
- 严格测试区间：`[2025-01-06 00:00:00, 2025-01-20 00:00:00)` UTC。
- 官方 8 天攻击包络：`[2025-01-06 00:00:00, 2025-01-14 00:00:00)` UTC。

攻击包络只是允许非良性事件出现的时间范围，不能把其中全部流标记为攻击。

### 目录日与绝对时间差异

| 项目                        |    Zeek | CICFlowMeter |
| --------------------------- | ------: | -----------: |
| 目录 D1 至 D14 行数         | 413,685 |      566,462 |
| 按绝对 UTC 起点进入校准区间 | 413,683 |      566,324 |
| 按绝对 UTC 起点进入测试区间 | 425,371 |      576,103 |
| 起点日期不同于目录日期      |      18 |       38,831 |
| 跨越校准/测试边界           |       8 |            7 |
| 起点晚于四周结束边界        |       0 |           15 |

因此正式清单必须按绝对 `ts` 划分，并保留 `day_id` 作为来源信息：

- 排除 Zeek 8 条和 CIC 7 条跨校准/测试边界记录。
- 排除 CIC 15 条四周窗外记录。
- 不得只根据 `D1` 至 `D28` 目录名决定阶段。

## 攻击事件

两端精确共享以下 2 条标签 1 事件：

| UTC 时间                      | 协议/服务 | 步骤             | 战术     | 技术    | 说明               |
| ----------------------------- | --------- | ---------------- | -------- | ------- | ------------------ |
| 2025-01-06 10:00:13.154357910 | TCP/SMTP  | `initial_access` | `TA0001` | `T1566` | 攻击者发送恶意邮件 |
| 2025-01-06 10:00:18.405628920 | TCP/SSL   | `initial_access` | `TA0001` | `T1566` | 客户端拉取感染邮件 |

两个组件均没有标签 2。`orange_dmz` 只看到初始访问的两条攻击流，不代表整个 8 天 APT 场景只产生两条攻击流；后续阶段可能位于内部网络、服务器或系统日志视角。

## 关联规则

### 裁决顺序

1. 统一协议号和端口表示，构造有向五元组。
2. 先在同向五元组中查找起点差不超过 1 秒的候选。
3. 同向无候选时尝试反向五元组。
4. 起点容差内无候选时，检查正确单位下的时间区间重叠。
5. 只有候选唯一时才记为匹配；多个候选记为歧义，零个候选记为未匹配。
6. 只比较两端官方标签；不生成、不覆盖、不传播标签。

### 全量结果

| 指标                          |      数量 |
| ----------------------------- | --------: |
| CIC 总行数                    | 1,142,442 |
| 唯一候选匹配                  | 1,138,471 |
| 匹配覆盖率                    |  99.6524% |
| 同向匹配                      | 1,137,833 |
| 反向匹配                      |       638 |
| 起点容差匹配                  |   799,958 |
| 唯一区间重叠匹配              |   338,513 |
| 一对多歧义                    |     2,015 |
| 未匹配                        |     1,956 |
| 标签冲突                      |         0 |
| 匹配到的唯一 Zeek 目标        |   799,914 |
| 被复用的 Zeek 目标            |    44,368 |
| 落到复用目标的 CIC 行         |   382,925 |
| 单个 Zeek 目标最大 CIC 复用数 |       899 |
| 严格一对一 CIC 行             |   755,546 |

## 实验使用协议

1. Zeek 实验直接读取官方 `conn_labeled.csv`；CICFlowMeter 实验直接读取归档内官方 `*_Flow_labeled.csv`。
2. 不再执行“Zeek 标签复制到 CICFlowMeter”的处理，因为 CIC 组件已经有官方标签。
3. D1 至 D14 只用于无攻击背景建模、阈值校准或良性分布适配；D15 至 D28 只用于时间外推测试。
4. 按绝对 UTC 时间划分，清除跨边界和四周窗外记录。
5. 若要做 Zeek 与 CICFlowMeter 的配对特征比较，只使用 755,546 条严格一对一记录；不得把复用目标当作独立一一配对。
6. `label=2` 在其他视角出现时必须独立保留，不能未经消融合并到 0 或 1。
7. `uid`、IP、端口和绝对时间只用于关联与审计，进入模型提示前必须排除捷径风险。
8. 当前组件适合低误报、每日告警数、每百万流误报数和两条关键攻击流召回；不适合普通平衡多分类或完整 APT 阶段覆盖结论。

## 代码与制品

### 新增代码

- `thesis/experiments/llm_probe/src/flow_probe/dedale_audit.py`。
- `thesis/experiments/llm_probe/tests/test_dedale_audit.py`。
- `thesis/experiments/llm_probe/scripts/run_dedale_orange_dmz_audit.sh`。
- `thesis/experiments/llm_probe/pyproject.toml` 新增 `flow-probe-audit-dedale` 入口。

### 正式运行

- 服务端：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/data-audit/dedale-orange-dmz-v2-20260721-v3/`。
- 本地：`/Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/data-audit/dedale-orange-dmz-v2-20260721-v3/`。
- 制品：`audit.json`、`input_manifest.json`、`console.log`。
- v1 目录包含错误单位诊断结果；v2 修正了单位但缺少多对一统计；v3 是当前唯一正式结果。

### 验证

- 测试驱动失败证据：模块缺失、关联接口缺失、全量接口缺失、微秒单位缺失和多对一统计缺失均先在服务器观察到预期失败。
- DEDALE 定向测试：`31 passed`。
- 服务器完整回归：`281 passed in 3.25s`。
- 本机 Black、Ruff 和 `bash -n` 通过。
- 输出没有原始 UID、IP、端口或推断标签。

## 下一步所需小文件

若要把时间轴从两个网络事件扩展到完整攻击动作，可在主代理确认后下载以下官方小文件，合计约 24.9 MB：

- `README.md`：4,772 字节，MD5 `1fa4df8d4ccff010d7296eb0783bdc15`。
- `userbehaviour_logs.zip`：22,196,076 字节，MD5 `25c891442f693c4f525f930d17fedb4a`。
- `system_logs_labels.zip`：2,669,407 字节，MD5 `455d0a7042531eff74285006f97822e4`。

本次没有下载这些文件。其他 Zeek 网络视角均超过 3 GiB，暂不扩大范围。
