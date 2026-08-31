# CEM-BER 制品与代码索引

<!-- RESEARCH_ROUTE=RWKV -->

- 日期：2026-08-31
- 用途：第三章 FT／CEM-BER 线的**单一导航入口**。本文件只做索引，不复制事实数字；
  数值以 [四格进度与错误记录](2026-08-31-第三章FT四格进度与错误记录.md) 和原始收据为准。
- 组织方式：**只建链接，不移动文件**。既有文档与其他会话都在引用现有路径，
  移动会批量破坏链接；杂乱问题用本页收敛，而不是重排目录。

## 一、恢复入口（新会话按此顺序读）

| 顺序 | 文档 | 说明 |
| ---: | --- | --- |
| 1 | [路线规则](AGENTS.md) | RWKV 路线的恢复链与写回规则 |
| 2 | [路线总控](RWKV路线总控.md) | 跨章公共合同、服务器与凭据来源 |
| 3 | [第三章恢复卡](RWKV第三章恢复卡.md) | 当前 Goal、已核实结果、活动任务、阻断 |
| 4 | [四格进度与错误记录](2026-08-31-第三章FT四格进度与错误记录.md) | 最新实测读数、口径边界、错误清单、开机动作 |

[第四章恢复卡](RWKV第四章恢复卡.md) 只在跨章任务时读；
[历史交接入口](RWKV历史交接入口.md) 与 [当前恢复卡](RWKV当前恢复卡.md)（旧链接兼容页）
只在事实冲突或制品追溯时读。

## 二、代码清单

### 2.1 本轮新增或修改（2026-08-29 至 08-31）

| 文件 | 提交 | 规模 | 用途 | 验证 |
| --- | --- | ---: | --- | --- |
| `thesis/experiments/llm_probe/tools/ch3_ft_emit_four_cell_summary.py` | `199c6dd` | 185 行（新建） | 从运行收据自动提取四格读数、逐轮历史与判据，写入固定路径 JSON | 真跑两场景：四格全缺不崩、构造真值交互算得 `0.04` 与手算一致 |
| `thesis/experiments/llm_probe/scripts/remote_launchers/pull_ch3_ft_four_cell_artifacts.sh` | `199c6dd` `be4b17d` `ca80b60` | 97 行新建，后两次共改 78 行 | 从服务器回传四格制品到本机，`--light` 只拉收据日志 | 真跑，轻量轮实测 6 秒 |
| `thesis/experiments/llm_probe/scripts/remote_launchers/watch_and_pull_ch3_ft.sh` | `ca80b60` | 79 行（新建） | 本机周期回传守护，每 5 分钟拉轻量制品，臂完成自动拉全量并打标记 | 真跑，已回传 C00／C10／C01 |
| `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_ft_four_cell_serial.sh` | `199c6dd` | +18 行 | 四格串行守护接入自动汇总，启动时与每臂结束时各汇总一次 | 服务器真跑，正确跳过已完成臂 |
| `thesis/experiments/llm_probe/tools/ch3_ft_c00_dual_selection.py` | `3344e0f` | +37 −2 行 | 排序阶段两条前向路径改用梯度检查点，修复 CUDA 显存溢出 | C01 真跑通过，峰值 `30,970` → `15,175` MiB；**C11 记忆路径的改动尚未推送服务器** |
| `thesis/experiments/llm_probe/tools/ch3_ft_lspr24_descriptive_eval.py` | `68e2197` | +1147 −38 行 | LSPR24 目标年描述性评价的前向实现（子代理交付） | 14 项实现验证通过；四格未齐，预检正确拒绝执行 |

### 2.2 更早的同线代码（本会话之前）

| 文件 | 提交 | 用途 |
| --- | --- | --- |
| `tools/ch3_ft_causal_entity_memory.py` | `44a54c0` 等 | 机制一因果实体记忆交叉注意力 |
| `tools/ch3_ft_entity_memory_interface.py` | — | 严格过去接口与实体链调度 |
| `tools/ch3_ft_entity_ranking_loss.py` | — | 机制二 CVaR-pAUC 排序损失与袋策略 |
| `tools/ch3_ft_transformer_field_token_protocol_a.py` | — | FT 主干与协议 A 输入 |
| `tools/ch3_build_metrics_table.py` | `726a59f` | 统一总表生成，已加 FT 四格适配器 |
| `tools/ch3_common_first_alert_fp_budget_envelope.py` | `4e91dcd` | 误报预算曲线与首次告警，已登记四格 |
| `tools/ch3_lspr23_entity_history_availability.py` | — | 实体历史可用性诊断 |
| `tools/ch3_gradient_controller_conflict_probe.py` | — | 机制二梯度信号实测 |
| `tools/ch3_ft_compile_equivalence_probe.py` | — | `torch.compile` 等价性与提速探针 |
| `tools/ch3_ft_data_path_benchmark.py` | — | 数据路径耗时占比探针 |

工具全量索引另见 [tools 脚本索引](tools脚本索引.md)。

### 2.3 配置

四格冻结配置在 `thesis/experiments/llm_probe/configs/`：

- `ch3-ft-c00-dual-selection-cuda-formal-v1.json`
- `ch3-ft-c10-entity-memory-cuda-formal-v1.json`
- `ch3-ft-c01-entity-ranking-cuda-formal-v1.json`
- `ch3-ft-c11-cem-ber-cuda-formal-v1.json`

## 三、制品清单（本机副本，`runs/diagnostics/` 下）

| 格 | 体积 | 文件数 | 关键制品 | 状态 |
| --- | ---: | ---: | --- | --- |
| `ch3-ft-c00-dual-selection-cuda-formal-v1` | 26 MB | 14 | 两份选轮检查点、`inflight.pt`、`receipts/selection.json` | 完整，已打 `.pulled-full` |
| `ch3-ft-c10-entity-memory-cuda-formal-v1` | 824 MB | 35 | 同上，`inflight.pt` 810 MB（99.5% 是每实体记忆状态） | 完整，已打 `.pulled-full` |
| `ch3-ft-c01-entity-ranking-cuda-formal-v1` | 26 MB | 34 | 同上，另有 20 份 `entity-ranking-diagnostics-N.json` 逐轮诊断 | 完整，已打 `.pulled-full` |
| `ch3-ft-c11-cem-ber-cuda-formal-v1` | 676 KB | 10 | 只有 `config.json`、身份收据、`entity-memory-interface.json`、`launch.log` | **无 `selection.json`、无检查点**，须整臂重跑 |

机器可读汇总：`runs/diagnostics/ch3-ft-four-cell-summary.json`，
由 [`ch3_ft_emit_four_cell_summary.py`](../../../thesis/experiments/llm_probe/tools/ch3_ft_emit_four_cell_summary.py) 生成。

**外部备份**：C00 全部制品已上传私有 HuggingFace 仓库
`Heehobino/cember-ft-lspr23-ch3` 的 `c00-bare-ft/` 路径（13 个文件）。
私有仓库，不得按公开制品引用。

## 四、文档导航（按主题）

### 4.1 当前状态

- [四格进度与错误记录](2026-08-31-第三章FT四格进度与错误记录.md)：最新读数、口径、错误、开机动作
- [CEM-BER 四格实验进度](2026-08-28-CEM-BER四格实验进度.md)：完整时间线，含两次关机与断点续训修复
- [全局进度快照](2026-08-28-全局进度快照.md)：跨骨干的横向状态
- [FT 新机制本机筛选进度快照](2026-08-28-FT新机制本机筛选进度快照.md)：重锚期的筛选记录

### 4.2 方法设计与实现

- [FT 新机制五篇文献审计](2026-08-28-FT新机制五篇文献审计/审计结论.md)：两机制的文献来源与研究空白裁决
- [因果实体记忆交叉注意力与低误报实体排序](2026-08-28-因果实体记忆交叉注意力与低误报实体排序/)：机制设计规约
- [机制一实施计划](2026-08-28-机制一因果实体记忆实施计划.md) ／ [机制一实现报告](2026-08-28-机制一实现报告.md)
- [机制二实施计划](2026-08-28-机制二低误报实体排序实施计划.md) ／ [机制二实现报告](2026-08-28-机制二实现报告.md)
- [BER 宿主集成实施计划](2026-08-28-BER宿主集成与四格补齐实施计划.md) ／ [集成报告](2026-08-28-BER宿主集成报告.md)
- [断点续训修复实施计划](2026-08-28-断点续训修复实施计划.md)
- [FT-Transformer 逐字段 Token 协议 A 实施计划](2026-08-21-FT-Transformer逐字段Token协议A实施计划.md)
- [FT 候选本机 MPS 与服务器 CUDA 单代码合同](2026-08-28-FT候选本机MPS与服务器CUDA单代码合同/)

### 4.3 诊断与裁决

- [LSPR23 实体历史可用性诊断](2026-08-28-LSPR23实体历史可用性诊断.md)：CEM 的数据前提
- [机制二梯度信号实测裁决](2026-08-28-机制二梯度信号实测裁决.md)：推翻了控制器冲突的推演
- [FT 训练吞吐优化实施计划](2026-08-28-FT训练吞吐优化实施计划.md)：X23 常驻与 compile 的实测裁决
- [CEM-BER 缺陷分析与第四章候选](2026-08-28-CEM-BER缺陷分析与第四章候选.md)

### 4.4 基线与比较

- [FT 第三章基线与消融编排](2026-08-28-FT第三章基线与消融编排/基线对比设计.md)：已发表方法池与内部比较的边界
- [XGBoost 同数据集论文配方来源审计](2026-08-26-XGBoost同数据集论文配方来源审计/审计报告.md)：**XGBoost 无源年读数的依据在第 35 行**
- [第三章 FT-TabM 底座新机制研究契约](2026-08-28-第三章FT-TabM底座新机制研究契约/)

### 4.5 正文准备

- [正文骨架与论断台账](2026-08-29-第三章CEM-BER正文骨架与论断台账.md)：22 子节骨架、论断登记、禁止表述
- 正文文件在 `thesis/chapters/第三章-CPA-ELP/`（重锚后大部分需重写，四格判据未出前不改动）

### 4.6 历史线（MLP／CPA-ELP，2026-08-27 重锚前）

结果真实但不再是主线，只作追溯：[第三章候选方案登记册](2026-08-08-第三章候选方案登记册.md)、
[D0 验收与 D1D2 病灶诊断](2026-08-27-D0验收与D1D2病灶诊断报告.md)、
[强骨干分数层回填报告](2026-08-27-强骨干分数层回填报告.md)、
[校准函数修复独立复核](2026-08-28-校准函数修复独立复核与D1D2门翻转确认报告.md)。
更早的材料在 `archive/` 与 `archive-pinn-ch3/` 下，经
[历史交接入口](RWKV历史交接入口.md) 检索。

## 五、目录现状说明

`.Codex/docs/RWKV/` 顶层有 29 个 Markdown 文件与 16 个子目录。
按 [`.Codex/docs/AGENTS.md`](../AGENTS.md) 的归档规则，成组的任务文档已进子目录
（如 `2026-08-28-FT新机制五篇文献审计/`），单文件报告留在顶层。

**未做物理重排的理由**：恢复卡、总控、正文台账与多个子目录文档之间已有 30 余条内部链接，
且其他会话可能正在引用；移动文件会批量断链，收益低于风险。
杂乱问题由本页收敛——新会话从第一节的四份文档进入，不必逐个辨认顶层文件名。

若将来确需重排，前置条件是先跑一次全仓链接扫描并准备批量改写，不宜临时移动。
