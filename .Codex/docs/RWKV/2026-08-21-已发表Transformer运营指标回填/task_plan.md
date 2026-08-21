# 已发表 Transformer 运营指标回填实施计划

## 目标

复用已持久化的 LSPR24 逐流分数，在不训练、不推理、不修改模型和不重新选择超参数的前提下，为发表配置全注意力 Transformer 补齐完整实际可达告警预算曲线、六档 DR 与 1 基实体内曝光序号首次告警指标，并生成可接入第三章统一帕累托表的聚合制品。

当前状态：计划已冻结，等待独立实现代理执行。

## 证据边界

- 该模型是已发表神经性能包络中的逐流 AP 和 DR@4% 锚，不代表整个已发表神经包络。
- 本轮只补 LSPR24 描述性运营指标。没有 LSPR23 逐流分数或检查点，禁止伪造源年曲线。
- 逐流分数来自历史已完成运行，本轮不读取模型、不训练、不重推理。
- CNN 与 GRU 的分数和检查点本地缺失，不纳入本工具；其恢复或重训另立任务。
- LSPR24 已被历史访问，本轮结果不得用于修改模型、阈值规则、输入、机制或候选排序规则。

## 冻结输入

输入项目根由启动器显式传入，以下路径相对于输入项目根：

1. `runs/diagnostics/ch3-baselines-full/scores_transformer_dijk2026.npy`
   - 形状：`20,227,356`
   - 类型：`float32`
   - SHA-256：`4bb845444a03cea0579c28120f2afe2d48559c8644c6a8fc80ddd37b5e63922d`
2. `runs/diagnostics/dijk-repro/cache/ent24_local.npy`
   - 形状：`20,227,356`
   - 类型：`int32`
   - SHA-256：`75f4dc8af12946de0f027320d793dd49f5e5e5060071e3ededb2a6654e60c9c6`
3. `runs/diagnostics/dijk-repro/cache/y24.npy`
   - 形状：`20,227,356`
   - 类型：`float32`
   - SHA-256：`455a4932e0483af59ebccc64b462d3c620f671c6969f15312d8358cf7f410b46`

输入必须机械复现：流数 `20,227,356`、实体数 `47,115`、正实体数 `752`、逐流 AP `0.325725660495`、最大池化实体 AP `0.353619988596`。任一不符即停止，不输出成功状态。

## 数据集－模型适配表

| 项目 | 冻结处置 |
| --- | --- |
| 合法字段 | 分数已经由冻结发表配置在合法 83 字段视图上生成；本轮不重新读取特征 |
| 实体键 | 使用冻结 `ent24_local.npy`，不读取原始 IP |
| 标签 | `y24.npy` 仅用于历史目标年描述性评价；实体标签取同实体逐流标签最大值 |
| 顺序 | 同实体内按冻结逐流数组索引升序，曝光序号从 1 开始 |
| 聚合 | 每实体取逐流分数最大值，与发表配置既有口径一致 |
| 因果边界 | 首次告警只使用当前及此前曝光；终端实体分数只用于阈值和终端曲线 |
| 输入输出 | 输入三个只读数组；只输出聚合 JSON/NPZ、收据、资源、状态和清单 |
| 梯度与状态 | 无模型、无梯度、无训练状态 |
| 持久化限制 | 禁止复制或重新持久化逐流分数、逐实体分数和逐实体首次位置 |

## 朱焱雷论文对位表

| 项目 | 本任务处置 |
| --- | --- |
| 研究问题 | 补齐同一模型在运营告警预算和首次告警维度的评价，不提出新模型 |
| 模型专属输入 | 复用发表配置既有分数，不改变其输入模态 |
| 模块挂载 | 无新增模块 |
| 强基线 | 与 XGBoost＋CPA-ELP、CNN、GRU 和正式可微候选进入同一目标年性能池 |
| 消融 | 本任务无机制消融；只做指标回填 |
| 指标 | 实际六档 DR、完整阶梯曲线、首次告警未告警率与按时检出曲线、资源后处理开销 |
| 不可迁移边界 | 朱论文不提供本任务的 4% 并列组算法；实际可达 FPR 合同以本项目制品为准 |

## 实际可达 FPR 算法

1. 将实体终端最大分数按分数相等的完整并列组降序聚合。
2. 阈值语义固定为 `score >= threshold`，同分组不得拆分、插值或按实体键任意截断。
3. 每个阶梯点记录阈值、组内正负实体数、累计 TP/FP、实际 FPR 与 DR。
4. 六档名义预算固定为 `0.1%/0.5%/1%/2%/4%/8%`；每档取所有 `actual_fpr <= nominal_fpr` 中 DR 最高的真实可达点，并记录下一可达点。
5. 每档同时记录 `nominal_target_fpr`、`actual_reachable_fpr`、负实体分母、FP 数与阈值并列组规模。
6. 4% 只是同源经验参照，不是可部署阈值或理论上限。

## 首次告警算法

- 每个六档阈值独立沿实体内升序逐流索引扫描，第一次 `flow_score >= threshold` 的位置记为 1 基 `exposure_index`。
- 分别报告正实体未告警率、告警正实体数、恶意实体首次告警曝光分位数 `q25/q50/q75/q90/q95`、固定正实体分母的按时检出累计曲线。
- 同时对全部负实体扫描并报告 `realized_first_alert_fpr`；不得沿用终端曲线的名义 4% 标签。
- `time_delay_available=false`，不得由 `t24` 或其他不完整时间字段伪造秒级延迟。

## 文件所有权

实现代理只可新增：

1. `thesis/experiments/llm_probe/tools/ch3_published_transformer_operational_backfill.py`
2. `thesis/experiments/llm_probe/configs/ch3-published-transformer-operational-backfill-v1.json`
3. `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_published_transformer_operational_backfill_v1.sh`
4. `.Codex/docs/RWKV/2026-08-21-已发表Transformer运营指标回填/实施报告.md`

本目录的 `task_plan.md` 和 `notes.md` 由主进程维护。不得修改冻结训练脚本、统一总表、恢复卡或其他运行目录。

## 运行身份与制品

- 运行 ID：`ch3-published-transformer-operational-backfill-v1`
- 运行根：`runs/diagnostics/ch3-published-transformer-operational-backfill-v1`
- 设备：CPU；GPU 数组读取和显存占用必须为 0。
- 输出：
  - `aggregate-results.json`
  - `complete-alert-budget-curves.npz`
  - `complete-alert-budget-curves-receipt.json`
  - `first-alert-timing-curves.npz`
  - `first-alert-timing-receipt.json`
  - `resource-receipt.json`
  - `input-receipt.json`
  - `status.json`
  - `manifest.json`
  - `run.log`

全部 JSON 与 NPZ 先写同目录临时文件再原子替换。成功重启按清单和哈希幂等跳过；失败保留状态与日志。

## 资源与执行边界

- 扫描超过 2,000 万条流，正式运行只能在 B76 进行。
- 预估 CPU 单进程小于 1 分钟、峰值主存不超过 2 GiB、输出 1 至 3 MiB；首次运行以资源收据为准。
- 不占 GPU，可与 GRANDE 并行的前提是控制组内存、磁盘和 I/O 门通过；资源不足时停止，不算科学失败。
- 不设置墙钟或 GPU 小时停止门。

## 最小入口验证

实现完成后只执行一次：

1. Python 语法检查。
2. 模块导入。
3. `--help`。
4. `--validate-config`。
5. 启动器 `bash -n`。
6. `git diff --check`。

不创建或运行人工夹具、单元测试、集成测试、冒烟实验，不运行 `black`。入口通过后尽快执行冻结真实数据回填。

## 阶段

- [x] 冻结证据、输入、算法、资源与文件边界。
- [ ] 独立实现代理完成四个目标文件并提交。
- [ ] 主进程在 B76 执行真实回填并回收最小聚合制品。
- [ ] 严格分析结果并接入统一帕累托表。

