# RWKV 第四章恢复卡

<!-- RESEARCH_ROUTE=RWKV -->

- **状态日期**：2026-08-19
- **用途**：第四章唯一当前恢复卡。只承载 DTEP、PBC、E1、长实体诊断、第四章 Q0 载荷、实验状态和下一动作。
- **总证据等级**：DTEP 与 PBC 均为**设计可行、实验待证**。E1、分桶诊断和历史 Q0 均为筛选或诊断证据，不得写成第四章候选已支持。

## 一、当前候选边界

工作题目为「基于双时域证据保持与先导段预算标定的跨年度实体检测方法」，算法暂名 `DTEP-PBC`。

- **DTEP**：把第三章已有因果前缀聚合作为长历史通道，新增固定二进近期证据通道及融合。当前只允许固定尺度族 `{1,2,4,8,16,32,64,128}`；`1` 由当前流原始输入表示，`128` 由现有块内因果前缀表示，中间 `{2,4,8,16,32,64}` 固定等权混合。禁止用源标签精细选窗、用目标标签选尺度或改权重。
- **PBC**：只使用无标签目标先导段冻结实体级预算规则；以源混淆收据和先导段无标签告警比例做 BBSE 准入，失败时按预注册规则回退源阈值。阈值封印落盘后才允许读取目标标签。
- **联合边界**：DTEP 定义实体因果前缀分数过程，PBC 只消费该过程在先导段内可用的状态。共同目标是先保护实体排序与长实体证据，再在误报预算下提高检出并降低告警时延。
- 基础部件已有不等于候选无创新，但不得把二进尺度、BBSE、分位阈值或预算约束宣称为首创。联合算法是否达到章级贡献，仍需共同预算基线、独立消融、联合消融、失败分面和理论边界支撑。

## 二、E1 源年实体折外信号门禁

### 2.1 冻结合同

E1 只使用 LSPR23、`seed=42`、协议 A 多层感知机、C00/C11 和 150,680 个源实体确定性三折，共 6 个训练单元。每个实体恰好作为一次留出实体，训练与留出实体交集为空；任何 LSPR24 读取均应立即失败。实施合同见[E1 实施计划](2026-08-18-第四章E1源年实体折外信号门禁实施计划.md)。

### 2.2 原始机械状态

- 运行身份：`ch4-e1-source-entity-oof-gate-seed42-v1`。
- 远端原始聚合制品：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch4-e1-source-entity-oof-gate-seed42-v1/aggregate-results.json`。
- 原始状态字段：`status=complete`、启动器 `finished`、`exit_code=0`，即 `complete/finished/exit=0`。
- `target_year_arrays_read=0`，零 LSPR24 读取。
- C00 pooled OOF 实体 AP：`0.5109066464488172`。
- C11 pooled OOF 实体 AP：`0.5447784766847485`。
- pooled 增量：`+0.03387183023593132`。
- 三折差值极差：`0.211731480949845`，约为 pooled 增量的 `6.25` 倍。
- 机械裁决：`weak_allow_coarse_rejection_only`。

旧恢复文档中的 E1 前置阶段状态已被上述原始完成收据覆盖。E1 说明源侧并非完全没有信号，但只能粗粒度淘汰方向不一致的完整候选，不能精细选择单一近期窗长、尺度子集、融合权重或时间基准；候选效果仍为实验待证。

## 三、长实体诊断

### 3.1 感知机分桶

运行 `ch4-entity-length-bucket-diagnostic-seed42-v1` 已以 `finished/complete/exit=0` 完成。四格相对冻结值逐项零差，覆盖 `47,115` 实体、`752` 正实体和 20 个检查点，`seen_all=true`，无逐样本分数。证据仅为 `screening_only=true`、`formal_paper_evidence=false`、`independent_test=false`。

C11-C00 在五个实体流数桶 `1-2/3-10/11-100/101-1000/1001+` 的实体 AP 增量为：

`+0.123948 / +0.239138 / +0.137851 / -0.322915 / -0.302212`。

现有机制在短中实体有利、在长实体显著有害，禁止写成全局提升。`1001+` 桶良性实体在 C11 下出现 `0.9999` 的逐流假阳尖峰，说明感知机上的长实体受损出现在逐流分数和表示层，不在聚合指数。

### 3.2 XGBoost 分桶

XGBoost 冻结 `raw83 + max` 与 `semantic168 + p=1.0` 的五桶实体 AP 增量为：

`+0.028998 / +0.121857 / +0.082025 / -0.073974 / -0.018679`。

两个长桶分别有 `84`、`40` 个正实体，均超过预注册最低支持数 `10`；方向翻转跨越感知机与 XGBoost，但 XGBoost 的 `1001+` 桶没有感知机的良性高分尖峰，不得假设两骨干根因相同。总体实体 AP 仍由 `0.513185` 提高到 `0.565078`，总体均值掩盖长实体退化。

## 四、DTEP Q0

### 4.1 冻结构造

- 规格：[DTEP 固定多尺度重构方案](2026-08-18-DTEP固定多尺度重构方案.md)。
- 实施计划：[DTEP 固定二进多尺度 Q0](2026-08-18-DTEP固定二进多尺度-Q0实施计划.md)。
- 运行身份：`ch4-xgb-dtep-fixed-dyadic-q0-seed42-v1`。
- 对照为 `semantic168 + p=1.0`，候选为 `fixed_dyadic251 + p=1.0`。251 维由原 `semantic168` 加 83 维固定二进近期混合组成；禁止 252、666 或 672 维视图。
- 源实体三折中，Q10 相对 Q00 的三折增量和 pooled 增量必须全部严格大于 0；失败即 `Q0_REJECTED_SOURCE_DIRECTION`，且 LSPR24 零读取。源门通过后才允许一次密封目标评价。
- 目标评价固定五桶与总体、DR@1/2/4%FPR 和效率门；目标结果不得触发 `v2` 尺度表、换尺度或改权重。

### 4.2 本地载荷与当前状态

本地三份生产载荷已存在：

- `thesis/experiments/llm_probe/tools/ch4_xgb_dtep_fixed_dyadic_q0.py`
- `thesis/experiments/llm_probe/configs/ch4-xgb-dtep-fixed-dyadic-q0-seed42-v1.json`
- `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch4_xgb_dtep_fixed_dyadic_q0_seed42_v1.sh`

2026-08-19 只读核验时，远端没有同名运行根或活动进程，三份载荷未同步；共同父制品 `runs/diagnostics/ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1/manifest.json` 缺失。DTEP Q0 **未启动、无实验结果、实验待证**。

资源估算：主机峰值约 `58.2 GiB`，启动门要求可用不少于 `60 GiB`、硬上界 `<65 GiB`；GPU 峰值保守估算 `18 GiB`，启动门要求空闲不少于 `20 GiB`、硬上界 `<24 GiB`；磁盘预留 `10 GiB`。这些是设计估算，不是实测效率结果。

## 五、PBC Q0

### 5.1 冻结构造

- 实施计划：[PBC 先导段预算标定 Q0](2026-08-18-PBC先导段预算标定-Q0实施计划.md)。
- 运行身份：`ch4-xgb-pbc-q0-seed42-v1`。
- 零训练复用父运行 `ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1` 的 `semantic168` 三折折外模型、最终模型和 `p=1.0`。
- 时间先导比例固定为 `0.1/0.2/0.3/0.5`，预算固定为实体 FPR `1%/2%/4%`。4% 只作 Gehri 同源经验工作点，1% 与 2% 是预注册保守敏感性，不表述为安全标准。
- 每个前缀与预算同时冻结源阈值、普通无标签实体分位阈值、BBSE 先验校正阈值和完整 PBC 阈值。任一门失败时精确回退源冻结阈值，并记录原因。
- `selection-seal.json` 原子落盘后才加载 `y24.npy`；后段不重新取分位数、不做 top-k、不用后段全体分数选阈值。

### 5.2 本地载荷与当前状态

本地三份生产载荷已存在：

- `thesis/experiments/llm_probe/tools/ch4_xgb_pbc_q0.py`
- `thesis/experiments/llm_probe/configs/ch4-xgb-pbc-q0-seed42-v1.json`
- `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch4_xgb_pbc_q0_seed42_v1.sh`

2026-08-19 只读核验时，远端没有同名运行根或活动进程，三份载荷未同步；共同父 `manifest.json` 缺失。PBC Q0 **未启动、无实验结果、实验待证**。峰值按 `58 GiB` 估算并要求 cgroup 内存准入；该值不是实测资源结果。

## 六、历史第四章实体 AP 候选 Q0

「实体均匀训练与直接实体 AP 优化」只用于提高 C11 实体 AP，不替换 PBC。其方案册、Q0 计划和原创性审计已完成；可学习 Lp/GeM 加直接 AP 已被占用，不能作为原创。随机袋 p 阶矩及导数的条件无偏性不推出 SOAP/SOX 非线性 AP 复合梯度无偏。

最终有效运行身份为 `ch4-entity-uniform-direct-ap-q0-seed42-v1-rerun2`，运行根 `runs/candidates/ch4-entity-uniform-direct-ap-q0-seed42-v1-rerun2`，机械状态 `COMPLETED_Q0_REJECTED/COMPLETE/exit=0`，启动器 `finished/complete/exit=0`。`strict_2x2_complete=true`、`candidate_advanced=false`、`target_labels_read_after_selection_seal=true`、`failed_run_artifacts_reused=false`、`random_lp_gate=PASSED`。

- 四格实体 AP：`0.4563850872 / 0.2892240420 / 0.3158986812 / 0.4234940164`。
- DR@4%FPR：`0.6502659574 / 0.4747340426 / 0.4853723404 / 0.6954787234`。
- 逐流 AP：`0.3013773042 / 0.2240005305 / 0.3201337105 / 0.1592074936`。
- 交互：`0.2747563804`；尾部实体 AP 增量：`-0.1070404121 / -0.0718340368`；历史 M0R0 差：`0.0066029128`。
- `entity_uniform_measure_supported=false`、`direct_entity_ap_supported=false`。
- 峰值 RSS `12658.45 MiB`、GPU `1893.14 MiB`；不持久化逐流或逐实体分数与源索引。

该结果仅为 `screening_only=true`、`formal=false`、`formal_paper_evidence=false`、`independent_test=false`，不进入论文正式表。首次 v1 的 M0R0 完成 20,000 步、累计编码 50,627,995 条流后，第二次 `swanlab.init` 返回 `401 Unauthorized`；准确状态是 `TRAINING_TRACKING_FAILED`，不是旧代码的 `EVALUATION_FAILED`。失败根 `runs/candidates/ch4-entity-uniform-direct-ap-q0-seed42-v1` 必须保留，`target_labels_read=false`，无科学结果。

原三份生产文件 SHA-256：工具 `564d6bc18e2442f25c532e624886aababbcf75e3ec022c60e0d58f4f13f1f7d3`、配置 `d9cb3a6d1ef886b44797b0c0138f61a877044f49cc8735de0f9060486a7f97f3`、启动器 `33ae46f502d53261c357a55f61840df26057dc529b2f912e2e656f5f3846cdb9`。

## 七、共享筛选视图陷阱

视图根 `runs/data-prepared/lspr24-screen-wide-v1`，合同 `lspr24-screen-6-2-2-v1`。

1. `label=-1` 占 `60.4075%`，即 `4,800,524` 窗口；`label=0` 占 `37.9779%`，`label=1` 占 `1.6145%`。可评价窗口只有 `3,146,375 / 7,946,899 = 39.59%`，消费前必须过滤到 `{0,1}`。
2. 训练区与验证区正类率为 `0.048423` 与 `0.022486`，相差 `2.15` 倍；同年任务也存在先验漂移。
3. 历史视图的 `final_split=final-not-materialized`；该事实只适用于该视图的旧合同，不得覆盖当前跨年度全量评价裁决。
4. 同年 XGBoost 验证 AP 为 `0.9690348794483452`、ROC-AUC 为 `0.9956477692756596`，余量 `0.03096512055165479`。这只是同年筛选背景，不是 DTEP 或 PBC 的效果证据。

## 八、服务器只读核验与当前阻塞

- 2026-08-19 核验时远端身份与项目根正确，RTX 5090 空闲，cgroup 可用内存约 `89.62 GiB`，磁盘可用 `40 GiB`。这些是当时快照，启动前须重核。
- 未发现 PBC、DTEP 同名运行根或活动进程。
- 当前阻塞不是当时资源，而是远端缺少两组各三份实验载荷，以及共同父 `runs/diagnostics/ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1/manifest.json`。
- 不得把缺父清单解释为父模型或父结果不存在。应先找回原始清单；无法找回时，只能基于既有父制品与哈希受控重建清单，并留下来源收据。

## 九、下一动作

1. 先完成恢复路由重构并核验链接。
2. 找回或受控重建父 `manifest.json`，核对两组本地载荷及其哈希。
3. 资源门通过后先同步并运行零重训 PBC Q0。
4. PBC 未达预注册门槛即否决 PBC，不依据目标结果改阈值、预算或评价子集。
5. 根据 PBC 裁决再决定是否运行成本更高的 DTEP Q0；DTEP 未达门槛即停止，不产生 `v2` 尺度表。
6. 只有 DTEP、PBC 独立门禁和联合消融形成有效证据后，才能冻结统一算法或写入第四章正文。

## 十、证据索引

- [第四章候选与文献方向分析](2026-08-18-第四章候选与文献方向分析.md)
- [DTEP 固定多尺度重构方案](2026-08-18-DTEP固定多尺度重构方案.md)
- [DTEP 固定二进多尺度 Q0 实施计划](2026-08-18-DTEP固定二进多尺度-Q0实施计划.md)
- [PBC 先导段预算标定 Q0 实施计划](2026-08-18-PBC先导段预算标定-Q0实施计划.md)
- [E1 源年实体折外信号门禁实施计划](2026-08-18-第四章E1源年实体折外信号门禁实施计划.md)
- [第四章实体流数分桶诊断实施与运行报告](2026-08-13-第四章实体流数分桶诊断实施与运行报告.md)
- [XGBoost 长实体分桶诊断结果分析](2026-08-18-XGBoost长实体分桶诊断结果分析.md)
- [第四章实体平均精确率原创性与数学边界](2026-08-13-第四章实体矩AP原创性与数学边界.md)
