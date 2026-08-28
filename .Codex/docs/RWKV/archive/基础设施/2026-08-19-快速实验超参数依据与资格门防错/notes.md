# 快速实验超参数依据与资格门防错笔记

## 一、事故证据

### 1.1 已核验事实

| 事实 | 证据 | 证据边界 |
| --- | --- | --- |
| 旧 PBC 将目标前缀比例设为 `0.1/0.2/0.3/0.5` | `2026-08-18-PBC先导段预算标定-Q0实施计划.md` | 其角色是无标签分布诊断与阈值重标定，不要求实体在前缀内完整结束 |
| 超参台账把目标前缀 `10%` 分类为“既有运行／人为诊断设定”，要求正式选比例不得看目标标签并报告覆盖实体数 | `2026-08-13-超参设置证据台账.md` 第 P0.2 节 | 台账没有为 `10%` 提供直接文献或完整实体双段语义背书 |
| 新方案把 `10%` 迁移为完整结束实体选择段，把 `10%—20%` 迁移为不相交完整实体确认段 | `2026-08-19-双段先导置信预算告警-Q0方案与实施计划.md` 第三节 | 这是新的角色与资格谓词，不是旧参数的同义复用 |
| 新方案要求确认段用 Bonferroni 校正后的单侧二项上界，但未在冻结前反推最小良性实体数 | 同上第四节与第六节 | “样本不足则回退”只定义运行后行为，没有定义启动资格 |
| 本机无标签诊断对 `10/20`、`15/30`、`20/40`、`25/50` 四组截止均得到选择完整实体 `0`、确认完整实体 `0`、评价新实体 `47,112`、跨界实体 `3` | `thesis/experiments/llm_probe/runs/diagnostics/ch4-two-stage-segment-eligibility-diagnostic-v1.json` | 诊断明确记录 `target_labels_loaded=false`、`model_predictions_run=false`、`run_identity_created=false`；只证明资格，不评价效果 |
| 实体首次出现时间的 `q1%=0.777298`、`q50%=0.806445`；实体末次出现时间的最小值为 `0.777294`；全局时间跨度 `141.781060` 小时 | 同一诊断收据 | 说明按全局最小／最大时间做 `10%/20%` 截止与实际实体活动严重错位；不据此选择新的比例 |
| 失败运行身份状态为 `failed/two_stage_confidence_budget_q0/python_failed/exit=1`，约 `387.8` 秒后报“选择段没有实体”；无阈值封印、无评价结果 | 父任务回收的远端状态摘要；远端身份 `runs/candidates/ch4-xgb-two-stage-confidence-budget-q0-seed42-v1` | 本任务没有远端原始日志的本地路径，不把摘要冒充本地原始日志；本地一手证据是上述无标签诊断 JSON |

### 1.2 事故链

1. **来源降级**：`10%` 原本是旧 PBC 的人为诊断前缀，并非直接文献给出的完整实体选择比例。
2. **语义偷换**：新方案把“前缀内可见流”改成“前 `10%` 内首次出现且完整结束的实体”，又新增独立确认角色；参数值相同，但统计对象与资格谓词已变。
3. **数据分布假设未核验**：没有先用实体首末时间统计验证全局时间比例能产生完整实体。实际 `47,115` 个实体中只有 `3` 个跨越早期边界，其余 `47,112` 个首次出现在 `20%` 之后。
4. **统计分母未反推**：方案写了 Clopper–Pearson 上界与 Bonferroni 校正，却没有由预算、候选数和置信水平计算确认段最小良性实体数。
5. **断言位置过晚**：方案层只要求结果报告计数；实现层直到模型评分之后加载选择段标签时才检查“没有实体”；启动器只做配置、输入、资源和跟踪门，没有资格收据门。
6. **失败成本扩大**：一个只需地址、时间和实体聚合即可否决的配置，经过父制品核验、资源门、跟踪门、全量数据处理与预测后才退出。

事故的最小根因不是“缺少一个判空”，而是**超参来源、角色资格、统计分母和启动断言没有组成同一个冻结合同**。

## 二、直接方法证据

| 来源 | 已核验位置 | 可支持内容 | 不能支持内容 |
| --- | --- | --- | --- |
| Clopper、Pearson，1934，《The Use of Confidence or Fiducial Limits Illustrated in the Case of the Binomial》，`Biometrika 26(4):404–413`，DOI `10.1093/biomet/26.4.404` | [OUP/CiNii 题录与正式 PDF 入口](https://cir.nii.ac.jp/crid/1363670318642609408)；JSTOR DOI `10.2307/2331986` | 二项比例精确置信限的原始方法来源 | 不支持本项目的 `10%/20%` 时间边界、实体独立性或跨年度交换性 |
| Tong、Feng、Li，2018，《Neyman-Pearson classification algorithms and NP receiver operating characteristics》，DOI `10.1126/sciadv.aao1659` | 本地原件 `raw/papers/methodology/2018-Tong-Neyman-Pearson-Classification.pdf`，印刷第 4 页，公式（1）（2）附近；`pdftotext` 第 521—537 行 | 独立留出负类样本、类型一错误违约概率、次序统计阈值，以及极端次序统计下 `n ≥ log δ / log(1−α)` 的显式最低样本量 | 不支持相关实体、用同一批实体选阈值再确认、跨年度漂移下无条件保证，也不支持本项目时间比例 |
| Tong、Xia、Wang、Feng，2020，《Neyman-Pearson classification: parametrics and sample size requirement》，JMLR 21(12):1–48 | [JMLR 正式页面](https://www.jmlr.org/papers/v21/18-577.html) | 再次明确非参数伞式算法对类 0 样本有最低样本量要求，并讨论样本拆分 | 不替代本项目对确认段实体独立性与功效目标的预注册 |

直接近邻检索目录在本任务读取时仍记录“新增全文 `0`、查询 `0` 组”。因此，本笔记只能说明经典统计方法与样本量公式已有直接来源，不能宣称完整双段网络实体算法已有或没有直接同构。

## 三、样本量推导

设：

- `p`：待控制的实体假阳率预算；
- `m`：同一比较族中的候选阈值数；
- `α_F`：该比较族的族错误率；
- `δ=α_F/m`：Bonferroni 后单候选显著性；
- `n`：独立良性确认实体数；
- `k`：确认段误报实体数。

单侧 Clopper–Pearson 上界为

`U_CP(k,n,δ)=Beta^{-1}(1−δ; k+1, n−k)`，其中 `k<n`；`k=n` 时上界为 `1`。

零误报时有闭式：

`U_CP(0,n,δ)=1−δ^(1/n)`。

因此，哪怕假设确认段零误报，能够确认预算 `p` 的最低必要样本量仍为：

`n_risk(p,δ)=ceil(log(δ)/log(1−p))`。

当前配置为每个预算内 `m=7`、`α_F=0.05`，即 `δ=0.05/7`：

| 预算 `p` | 零误报最低良性确认实体数 `n_risk` | 在该整数样本量下的零误报上界 |
| ---: | ---: | ---: |
| `0.01` | `492` | `0.0099937163` |
| `0.02` | `245` | `0.0199679160` |
| `0.04` | `122` | `0.0396958922` |

这只是**最好情形的必要条件**。要由功效反推样本量，还必须预注册一个可接受方法在确认段的真实假阳率假设 `q<p` 和二类错误率 `β`：

1. `k_max(n)=max{k∈[0,n] : U_CP(k,n,δ)≤p}`；
2. `Power(n;q)=P_{K~Binomial(n,q)}[K≤k_max(n)]`；
3. `n_power=min{n≥n_risk : Power(n;q)≥1−β}`。

如果不声明 `q` 与 `β`，只能签发“风险界最好情形可计算”收据，**不能签发功效充分收据**。若三个预算也要作为一个同时覆盖的比较族，则应令 `m=7×3=21`；此时零误报最低数变为 `602/299/148`。当前配置写的是“预算内 Bonferroni”，是否升级为跨预算同时覆盖必须由用户裁决，不能静默改变。

选择段还有阈值分辨率要求。若最低候选尾率为 `r_min`，并要求该尾部至少有 `h` 个良性实体，则必要分母为 `n_selection≥ceil(h/r_min)`。当前 `r_min=0.001`；即使取最弱的 `h=1`，也需要至少 `1,000` 个良性选择实体。`h` 是工程稳定性假设，不是 Tong 或 Clopper–Pearson 给出的保证，必须单独登记来源和敏感性。

## 四、最小收据字段草案

### 4.1 超参依据收据

所有未由冻结数据、接口合同或已证明公式唯一决定的数值均视为魔法数字。每个数值必须在注册表中占一行，并同时提供四块依据：

1. `literature_evidence`：直接文献题名、DOI／原件、页码／公式、原文支持对象与本项目差异；
2. `derivation_evidence`：公式、输入量、计算器哈希、精确结果、取整规则和误差界；
3. `empirical_evidence`：冻结真实数据无标签统计或仅源侧实验的制品路径、哈希、样本单位、标签权限与结果；
4. `applicability_boundary`：适用数据版本、统计单位、角色、取值范围、独立性／交换性条件和失效触发器。

通用字段为：`parameter_id`、`config_json_pointer`、`value`、`unit`、`role_semantics`、`provenance_class`、`target_labels_seen`、`sensitivity_required`、`owner`、`frozen_at`、`supersedes`、四块依据各自的 `status`，以及总状态 `verified/unverified/rejected`、`freeze_eligible`、`missing_evidence`。

只有四块依据均为 `passed` 且总状态为 `verified` 时，`freeze_eligible` 才能为真。`not_applicable` 不能用于绕过缺失的文献、推导或真实／源侧证据；如果某类证据确实不适用，该数值就不是可冻结的科学超参数，必须移出实验配置或由无自由度的接口／数据常量替代。

### 4.2 无标签资格收据

`schema_version`、`data_manifest_sha256`、`entity_key_schema`、`time_field`、`time_unit`、`boundary_parameterization`、`candidate_boundaries`、`selection_rule`、`n_flow`、`n_entity`、`time_min`、`time_max`、`time_span`、`first_time_quantiles`、`last_time_quantiles`、每组边界的 `selection_total/confirmation_total/evaluation_total/boundary_total`、`role_total`、两两交集、`target_labels_loaded=false`、`model_loaded=false`、`model_predictions_run=false`、`run_identity_created=false`、`producer_sha256`、`receipt_sha256`、`decision`、`failure_reason`。

### 4.3 风险与功效收据

`risk_method`、`budget_p`、`family_definition`、`familywise_alpha`、`candidate_count`、`budget_count_in_family`、`delta_per_candidate`、`n_risk_zero_error`、`q_design`、`beta_design`、`n_power`、`selection_tail_rate_min`、`selection_tail_support_h`、`n_selection_resolution`、`observed_selection_negative`、`observed_confirmation_negative`、`observed_confirmation_false_positive`、`cp_upper`、`independence_unit`、`independence_justification`、`exchangeability_limit`、`calculation_implementation_sha256`、`decision`、`fallback_reason`。

## 五、未关闭问题

1. 是否放弃基于全局时间跨度的 `10%/20%`，改为预注册的实体完成秩／活跃时间秩边界；这是算法合同变更，不能由本任务代替用户决定。
2. Bonferroni 比较族只在每个预算内含 `7` 个候选，还是同时包含 `3` 个预算共 `21` 个候选。
3. 功效设计中的 `q`、`β`，以及选择段尾部最小支持数 `h` 尚未冻结。
4. 实体之间的独立性只是比逐流更可信，尚未被本课题验证；若实体仍有主机关联，应按簇或有效样本量重新定义风险单位。
5. 完整 D3 直接近邻检索仍在并行进行；它约束原创措辞，不应阻塞已通过资格与统计门的 Q0。

## 六、`10%/10%/80%` 的魔法数字反例登记

| 依据轴 | 核验结果 | 裁定 |
| --- | --- | --- |
| 直接文献 | 现有直接方法文献支持样本拆分、误差控制和独立确认的一般原则，没有给出 LSPR24 完整实体 `10%/10%/80%` 比例 | `missing` |
| 数学／统计推导 | 冻结前没有从 Clopper–Pearson 风险界、功效或选择尾部分辨率反推两个先导段规模 | `missing` |
| 真实数据／源侧实验 | 冻结前没有资格收据；事后无标签真实数据诊断显示选择、确认均为 `0` | `failed` |
| 适用边界 | 旧 PBC 的无标签流前缀与新方案的完整实体选择／确认角色不等价；全局时间比例也与实体活动集中区错位 | `failed` |

总状态为 `rejected`，`freeze_eligible=false`。该比例不能因来自旧实验、写入恢复卡或已经实现而恢复资格；只有新方案版本重新取得四块完整依据后才能形成新的冻结候选。
