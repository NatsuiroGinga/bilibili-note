# ResMLP2 与 TabM 协议 A 四格重跑实施计划

## 一、目标与边界

- 目标：把最初的 ResMLP2 与 TabM4 放回第三章原多层感知机的协议 A，使用同一训练预算和四格消融直接比较。
- 取消：宽瓶颈 ResMLP2、源年三折资格门和只跑 C00/C11 的合同不再用于本次重跑。
- 证据等级：单次直接可比实验。LSPR24 已被历史实验访问，本次不得写成新的不可见最终测试或独立泛化证明。
- 不修改原多层感知机、既有 ResMLP2/TabM 三折运行和失败目录；使用全新工具、配置、启动器与运行身份。

## 二、统一实验合同

两种骨干都执行四格：

| 单元 | 因果前缀跨流聚合 | 实体级可学幂平均池化 |
| --- | --- | --- |
| C00 | 关闭 | 关闭 |
| C01 | 关闭 | 开启 |
| C10 | 开启 | 关闭 |
| C11 | 开启 | 开启 |

共同协议逐项复用 `tools/ch3_2x2_fairsel.py`：

1. 数据为同一组 LSPR23/LSPR24 的 83 字段缓存、序列索引、掩码与实体键。
2. `seed=42`，序列长 128，批量 64，20 轮，每轮 1000 步，不早停。
3. 学习率 0.002，权重衰减 0.01，丢弃率 0.1，辅助损失权重 1.0。
4. LSPR23 使用原协议 A 的实体不相交训练/验证划分；每格跑满 20 轮，以验证逐流 AP 的最早最大轮次冻结检查点。
5. 四格选择结果全部冻结写盘后，才允许首次加载 LSPR24；每格只评价一次，禁止用 LSPR24 指标改结构、轮次、聚合指数或超参数。
6. ResMLP2 固定为最初结构：隐藏宽度 139、两个预归一化全宽残差块、参数量 89,796。
7. TabM 固定为四成员、隐藏宽度 186、成员概率算术平均、共享 ELP 指数、参数量 90,175。
8. 两个运行串行执行，避免 GPU 争用污染资源比较；先完成 ResMLP2，再完成 TabM。

## 三、必须输出的统一指标

每格均输出并进入同一结构的聚合结果：

- LSPR23：所选轮次、选择时验证逐流 AP、训练时长与检查点身份。
- LSPR24：逐流 AP、实体 AP、最大池化实体 AP、`0.1%/0.5%/1%/2%/4%/8%` 六档实体检测率、完整可达告警预算曲线的压缩聚合。
- 资源：参数量、训练墙钟、评价墙钟、峰值 GPU 显存、峰值进程内存和总 GPU 小时。
- 隔离：LSPR24 首次加载发生在选择封印之后；四格目标评价调用数必须恰为 4。

源年选择指标、LSPR24 跨年度指标和资源指标必须分表，不得用源年三折实体 AP 替代本次目标年四格结果，也不得只用实体 AP 宣布胜负。

## 四、文件与运行身份

实现代理只新增以下文件：

1. `thesis/experiments/llm_probe/tools/ch3_resmlp2_tabm_protocol_a_2x2.py`
2. `thesis/experiments/llm_probe/configs/ch3-resmlp2-protocol-a-2x2-seed42-v1.json`
3. `thesis/experiments/llm_probe/configs/ch3-tabm4-protocol-a-2x2-seed42-v1.json`
4. `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_resmlp2_protocol_a_2x2_seed42_v1.sh`
5. `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_tabm4_protocol_a_2x2_seed42_v1.sh`
6. `.Codex/docs/RWKV/2026-08-20-ResMLP2与TabM协议A四格重跑实施报告.md`

运行身份：

- `ch3-resmlp2-cpa-elp-protocol-a-2x2-seed42-v1`
- `ch3-tabm4-cpa-elp-protocol-a-2x2-seed42-v1`

## 五、执行顺序

1. 复用原协议 A 的加载、选择封印、目标一次评价和指标函数；只新增两种骨干适配与完整预算曲线/资源汇总。
2. 只执行 Python 语法、模块导入、命令帮助、配置验证和 Shell 语法检查；不运行格式化器、人工夹具、单元测试或独立冒烟实验。
3. 最小入口检查通过后立即同步生产文件并启动 ResMLP2 真实四格实验。
4. ResMLP2 结束后启动 TabM 真实四格实验，不以 ResMLP2 结果决定是否运行 TabM。
5. 分别回收原始状态、日志、选择封印、聚合结果和资源收据，再更新恢复卡；工程失败与科学结果必须分开记录。

