# 任务十七公共观测与 ns-3 域随机化记录

## 已核验事实

- 任务十七接口审计：`../task-17-interface-audit.md`。
- 任务十七数据审计：`../task-17-data-audit.md`。
- 现有 v4 正式矩阵只有 21 个运行、7 个环境配置，拓扑、FIFO、队列上限、时延、协议和包长基本固定。
- 验证集训练均值常数状态均方误差为 `0.369276`，优于 B0 的 `0.397640` 和 B1 的 `0.375989`。
- GeNIS 可在保守约束下构造部分同流四段历史；当前 HIKARI 汇总表不能构造有可靠时间语义的四窗口。
- 论文原始 PDF 正由独立子代理研读，字段契约在页码证据返回前不扩大。

## v5 设计原则

1. 保存物理真值用于监督和验证，但通过类型与键空间将其和公共观测隔离。
2. 仿真输出逐窗口的到达包数、字节数、包长统计和到达间隔统计，以便后续按论文定义选择公共字段。
3. 环境参数由显式配置清单生成，不从场景名称反推。
4. 测量噪声只作用于公共观测副本，不污染守恒真值。
5. 统计单位是独立完整运行，不把重叠滑窗视为独立重复。

## 待记录

- v5 参数范围与切分生成算法。
- 编译与冒烟命令、输出目录和校验结果。
- 210 运行的 SwanLab 运行号、日志和制品位置。
- 常数、单窗口、四窗口及不确定性指标。

## v5 实现与服务器运行

### 生产文件

- 独立场景：`thesis/experiments/llm_probe/ns3/domain_randomized_queue_scenario.cc`。
- 冻结矩阵生成器：`thesis/experiments/llm_probe/src/flow_probe/ns3_domain_randomization.py`。
- 正式矩阵执行器：`thesis/experiments/llm_probe/src/flow_probe/ns3_domain_experiment.py`。
- 服务器包装器：`thesis/experiments/llm_probe/scripts/run_ns3_domain_randomization.sh`。
- 控制台入口：`flow-probe-plan-ns3-domain-randomization` 与 `flow-probe-run-ns3-domain-randomization`。
- 任务十六的 v4 场景、状态适配、序列、训练和耦合文件均未修改。

### 参数与字段契约

- 210 个环境参数元组按 `120/30/30/30` 划分为训练、校准、未见配置和范围外测试，切分间不重复。
- 训练、校准和未见配置使用 FIFO/CoDel；范围外测试独占 RED，并同时留出容量、时延、队列上限、丢包率、包长和抖动范围。
- 变化因素包括容量与变容时刻、接入和瓶颈时延、队列策略与上限、独立丢包、UDP/TCP、发送端数量、包长、恒定/突发到达、起始抖动和测量噪声。
- CSV 以 `public_` 和 `supervision_` 前缀隔离公共观测与仿真真值。冒烟审计发现噪声标准差配置最初误列为公共字段，已在正式运行前改为 `supervision_measurement_noise_std_ratio`。
- 修复后公共字段共 8 个，监督字段共 45 个；公共字段名中不存在容量、队列、标签、种子、运行编号或噪声配置。

### 编译、静态检查与冒烟

- 服务器 Black 成功；Shell `bash -n` 成功。
- Ruff 首次只报告 `I001` 导入排序，不属于语法或结构问题，按仓库规则未修改且未重跑。
- 本机与服务器均没有 `clang-format`，ns-3 包装器也没有格式化子命令；C++ 以编译器作为结构门禁。
- 首次 C++ 编译因辅助函数 `SocketFactory` 与 ns-3 同名类歧义退出 `2`。仅将辅助函数改名为 `SocketFactoryName` 后，重新编译退出 `0`。
- 编译日志：`runs/ns3-data/task17-v5-compile-20260722/compile-fix2.log`。
- 六组代表性冒烟覆盖 FIFO/CoDel/RED、UDP/TCP、恒定/突发与容量变化，全部退出 `0`；每组 30 个窗口，字节和包守恒残差违规数均为 `0`。
- 字段隔离修复后的 RED/TCP/突发/变容量复跑仍为 30 个窗口、双残差违规 `0`，实际观测到 `12 Mbit/s -> 6 Mbit/s` 的跨窗口容量变化。
- 冒烟路径：`runs/ns3-data/task17-v5-smoke-20260722-v1/` 和 `runs/ns3-data/task17-v5-smoke-20260722-v2/`。

### 正式矩阵

- 冻结清单：`runs/ns3-data/ns3-domain-randomization-config-v1-20260722/config_manifest.jsonl`。
- 清单 SHA-256：`a9002d666720843eba9e55fef2f6ebdda4a8ef69c6e9255797dcad5480ef0880`。
- 服务端输出：`runs/ns3-data/ns3-domain-randomization-formal-20260722-v1/`。
- `screen`：`task17-v5-210`。
- SwanLab 项目：`mortiswang/malicious-traffic-llm`；运行号：`j4xqs5er`。
- 执行器只有在单组 120 个窗口、模式版本、参数标识、公共值有限非负以及双守恒残差全部通过后，才把该配置标记为完成。

正式矩阵于 2026-07-22 17:17:59 完成：

- `210/210` 个配置完成，失败数为 `0`，`screen` 正常退出。
- 210 份 CSV 共 25,200 个数据窗口，四类切分为 `120/30/30/30`。
- 210 个组均为 120 窗口，字节和包守恒残差违规均为 `0`。
- CSV SHA-256 记录 210 项，SwanLab 指标步 210 个，全部 CSV 表头唯一一致。
- SwanLab 运行状态为 `finished`，运行号 `j4xqs5er`。
- 正式输出总大小约 15 MiB；完成时数据盘使用率 `75%`，剩余 `13 GiB`。

## 四窗口公共观测制品

- 构造器：`src/flow_probe/ns3_observability_sequences.py`。
- 服务端输出：`runs/ns3-data/ns3-observability-sequences-h4-20260722-v1/`。
- 210 个组均生成 117 条四窗口序列，共 24,570 条。
- 四类切分为训练 14,040、校准 3,510、未见配置 3,510、范围外 3,510。
- `model_inputs` 只含 `total_packets`、`total_bytes`、`packet_length_mean`、`packet_rate` 和 `byte_rate`，每项长度为 4；容量、队列真值、标签、种子、运行编号和噪声配置均未进入输入。
- 五个队列边界锚点、四窗口环境真值和守恒通量位于独立监督键空间。
- 源 CSV SHA-256 记录 210 项，输出制品 SHA-256 记录 9 项；序列输出约 94 MiB。

## 固定可辨识性诊断

- 配置：`configs/observability_diagnostic_seed42.yaml`。
- 入口：`src/flow_probe/observability_diagnostic.py`。
- 服务端输出：`runs/observability/task17-observability-seed42-20260722-v1/`。
- SwanLab：`mortiswang/malicious-traffic-llm`，运行号 `lydyn38z`，状态 `finished`。
- 两个神经估计器参数量均为 15,630，使用相同初始化、切分、特征变换、批次顺序、损失和早停规则；差别只有输入为最后一个窗口或完整四窗口。

未见配置测试结果：

| 方法         | 状态均方误差 |
| ------------ | -----------: |
| 训练均值常数 |    0.0172143 |
| 单窗口       |    0.0171397 |
| 四窗口       |    0.0166949 |

预注册裁决：

1. 四窗口相对常数改善 `3.017%`，未达到 `10%`，失败。
2. 四窗口减单窗口的组级均方误差差为 `-0.000444865`，95% 区组自助置信区间为 `[-0.000626147,-0.000262251]`，上界小于零，通过。
3. 四窗口范围外不确定性接收者工作特征曲线下面积为 `0.08111`，95% 置信区间为 `[0.02442,0.16000]`，不仅没有高于随机水平，方向还明显反转，失败。

总体为三项门槛通过一项，`overall_pass=false`。这说明四窗口历史携带少量新增信息，但不足以证明公开公共观测能够稳定恢复队列状态，也不能用当前异方差不确定性识别范围外环境。按既定停止规则，永久否决“历史环境辨识 + 物理软令牌 + 不确定性门控”，不运行 C1/C2，不再新增仿真配置、输入字段或估计器变体。

## 本地回收与完整性核对

- 正式矩阵已回收至本地 `thesis/experiments/llm_probe/runs/ns3-data/ns3-domain-randomization-formal-20260722-v1/`，210 份 CSV 的 SHA-256 全部通过。
- 四窗口制品已回收至本地 `thesis/experiments/llm_probe/runs/ns3-data/ns3-observability-sequences-h4-20260722-v1/`，9 项制品的 SHA-256 全部通过。
- 固定诊断已回收至本地 `thesis/experiments/llm_probe/runs/observability/task17-observability-seed42-20260722-v1/`。模型、指标、预测、配置等 11 项 SHA-256 通过；仅 `console.log` 未通过原清单。
- 日志不一致的根因已定位：程序在控制台捕获上下文尚未结束时先计算 `console.log` 哈希，随后又把完整指标打印到同一日志，使文件从清单记录的 1,740 字节增长到 6,347 字节。该问题不影响模型、指标、预测或研究裁决，但原清单不得表述为 12/12 全部一致；任务十七不重跑。
