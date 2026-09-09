# 第三章 LAMDA 候选方案统一筛选台账

**用途：** 统一登记 LAMDA 第三章的基线、已筛查实现、外部方法候选和条件候选，并规定逐项筛选顺序。本文档不纳入 DRIFT、RWKV 或其他路线的候选。

**当前状态：** 研究中。除标记为“实验支持”的条目外，其余均不能写成 LAMDA 方法有效性结论。**当前下一动作：L29 受限参数修复四臂待跑**（ER2018 / ER2018+修复 / ER2018+head-only修复 / ER2018+head-only修复+CUR，运行身份预定 `ch3-lamda-restricted-repair-screening-mps-seed42-v1`，见 [方案 §8](第三章-LAMDA修复保护二人博弈尾锚约束方案.md) 与 L29 行）。

## 统一数据与评价合同

- 数据：Hugging Face `IQSeC-Lab/LAMDA`，revision `ad9614bdd5556767f97ced2fce797c2f06408ebf`。
- 原论文年份角色：`TRAIN+IID=2013--2014`、`NEAR=2016--2017`、`FAR=2018--2025`；原论文将 `NEAR/FAR` 作为测试区域。
- 本项目筛选覆盖层（用户 D1 裁决 2026-09-09 后）：来源年 `2013/2014`；项目开发层 `2016/2017`＋`2018`（train 进入到达流、test 进入评价面板）；封印评价 `2019--2023`；`2024/2025` 因恶意样本枯竭（794/23）只作探索性，不作统计评价基础。开发层只是为避免在封印评价上选择方法而增加的内部筛选用途，不能写成原论文的数据角色。
- 当前公开 `4561` 维特征空间包含全时期训练分片协变量，所有现阶段候选运行均标为 `screening_only`。封印评价年（`2019--2023`）与 `2024/2025` 探索性读数均不得参与候选、阈值或超参数选择。
- 统一报告 AP、AUROC、F1、FPR、FNR、Brier、旧恶意负向翻转率、当前恶意正向修复率、良性新增误报和资源成本。不得只用 AP 或 F1 裁决。
- 通过候选的最低条件：相对 ER 不增加 FPR 和旧恶意负向翻转，并在 AP、FNR 或当前恶意正向修复率至少一项改善。若联合方案没有两个单机制的独立信号或没有可解释互补收益，不保留联合创新主张。

## 状态定义

| 状态 | 含义 |
| --- | --- |
| `baseline` | 共同预算比较锚点，不承担创新主张 |
| `running` | 已启动真实筛选，尚无结果 |
| `qualified_screening` | 仅通过来源／开发期资格门，不能当正式泛化结论 |
| `experiment_support` | 本项目已有真实制品支持指定作用面 |
| `reject_implementation` | 具体实现被源年筛查否决，不否定抽象方法家族 |
| `external_pending` | 有全文或网页方法证据，但尚无 LAMDA 本地实验 |
| `pending_experiment` | 方案与判据已冻结，待真实运行 |
| `oracle_e1_rejected` | E1 oracle 上界检验否决该形态：覆盖不足且 oracle 裁剪后 FPR 不过 ER 门 |
| `conditional_candidate` | 数据条件或因果证据尚未满足，暂不实现 |
| `excluded` | 当前数据合同无法支持，除非出现新信息 |

## 候选总表

| 编号 | 候选方案 | 方法家族／依据 | LAMDA 任务化差量 | 最小筛选 | 当前状态 | 证据与备注 |
| --- | --- | --- | --- | --- | --- | --- |
| L0 | Naive 逐年更新 | LAMDA 原论文基线 | 无回放、固定年度顺序 | 与 ER 同预算比较 | `baseline` | 阶段 A 共同基线 |
| L1 | 标准经验回放 ER | 回放基线 | 总容量 200 的单样本 reservoir | 与 Naive 比较 FPR、AP、FNR、旧恶意翻转 | `qualified_screening` | [阶段 A 报告](../../.Codex/docs/2026-09-08-LAMDA回放安全回归/stage-a-qualification-reanalysis.md)；FPR 与旧恶意翻转下降，但 AP/FNR 略差 |
| L2 | PCT／Focal Distillation | Regression-aware／PCT | 保护旧模型正确决策，恶意漏判修复另行建模 | ER、ER+PCT、等 FPR 阈值对照 | `reject_screening` | [PCT 预筛分析](../../.Codex/docs/2026-09-09-LAMDA-PCT-FPR门控/analysis/analysis-report.md)；[PCT 联合框架方案](第三章-LAMDA恶意漏判修复与PCT联合框架候选.md)；[Regression-aware 全文笔记](../../wiki/papers/attack-detection/2025-Ghiani-Regression-aware持续学习安全回归.md)；PCT 是直接基线，不是创新名称；开发期 FPR/FNR 均高于 ER |
| L3 | 缺口感知恶意修复 | 困难正例／正向修复任务化 | 只对当前真实恶意且旧模型漏判者按 margin 缺口加权 | ER vs ER+缺口修复 | `reject_implementation` | [四臂分析报告](../../.Codex/docs/2026-09-09-LAMDA缺口修复/analysis/analysis-report.md)；FNR 降低但 FPR 增加 `0.125489090` |
| L4 | 条件双侧风险门控 | A-GEM 双参考梯度任务化 | 仅当候选梯度与旧恶意或良性参考梯度冲突时投影 | ER vs ER+条件门控 | `reject_implementation` | 与既有始终双风险投影 pooled 结果相同；保留为安全基线，不形成独立新差量 |
| L5 | 缺口修复＋条件风险门控 | L3 与 L4 的联合候选 | 修复与安全约束通过同一年度更新耦合 | 四臂联合臂 | `reject_implementation` | FPR 增加 `0.065176777`，联合不满足安全门 |
| L6 | 始终双风险梯度投影 | A-GEM | 每批都保护旧恶意与良性参考梯度 | 与 ER、A-GEM 单风险对照 | `experiment_support` | [双风险报告](../../.Codex/docs/2026-09-09-LAMDA双风险梯度投影/analysis-report.md)；FPR/旧恶意翻转下降，但 FNR/AP 变差，只作安全基线 |
| L7 | 固定四角色记忆 | CBRS／MADAR 等记忆选择的任务化尝试 | 保护、修复、误报控制、覆盖四角色轮转 | ER、ER+角色记忆、同配额随机 | `reject_implementation` | [阶段 C 报告](../../.Codex/docs/2026-09-09-LAMDA决策角色记忆双侧修复/analysis/analysis-report.md)；等配额实现导致开发期风险恶化 |
| L8 | 等单位双侧风险损失 | 风险代理损失 | 对保护、修复、良性代理统一加 BCE | ER vs ER+风险损失 | `reject_implementation` | 阶段 C 具体实现 FPR 大幅升高，不能继续沿用 |
| L9 | 仅调阈值 | 操作点匹配基线 | 不改训练，只在开发层找 FPR 约束阈值 | 与 ER 相同 FPR 比较 FNR | `reject_implementation` | 在 FPR 约束下仅 F1 `+0.000079785`，不构成机制 |
| L10 | TFCO／原始—对偶 FPR 约束 | 数据依赖约束学习 | 模型玩家修复恶意漏判，安全玩家更新 FPR 拉格朗日乘子 | ER、阈值匹配、约束训练，等 FPR 比较 | `external_pending` | 网页深度研究已列出 Cotter 等 Eq. (1)/(2)；原件与现代 PyTorch 接口仍需核验 |
| L11 | 双玩家安全约束回放 | L3＋L10 的博弈化组合 | 安全玩家只控制良性 FPR 约束和旧恶意回归，非攻击者—防守者叙事 | ER、L3、双玩家层、联合 | `reject_implementation` | [博弈候选方案](第三章-LAMDA双玩家安全约束博弈候选方案.md)；v2 复筛（[分析报告](../../.Codex/docs/2026-09-09-LAMDA双玩家v2复筛/analysis/analysis-report.md)、[独立分析 JSON](../../.Codex/docs/2026-09-09-LAMDA双玩家v2复筛/analysis/v2-independent-analysis.json)，2016+2017 pooled n=41668/臂）：双玩家单臂 ΔAP +0.000334/ΔFPR −0.001304/ΔFNR +0.005489、修复候选恒 0、乘子年更新 3 次且峰值 ≤0.082——未介入、无独立信号；缺口＋双玩家联合 ΔFPR +0.100039、λ_benign 峰值 1.136、良性新增误报 2553 vs ER 174、恶意负向翻转 0.0390 不低于缺口单臂 0.0387——不通过 FPR 与旧恶意保持门；v1 乘子发散仅作根因（恢复卡 v1 条目）。**演化续接 L28（尾锚）** |
| L12 | MIR 干扰感知记忆 | Maximally Interfered Retrieval | 从旧正确样本中选虚拟更新后最易退化者，替代固定角色配额 | ER vs MIR，等容量和暴露量 | `external_pending` | [MIR 全文笔记](../../wiki/papers/attack-detection/2019-Aljundi-MIR最大干扰检索.md)；需记录额外前向成本 |
| L13 | GSS 梯度多样性记忆 | Gradient-based Sample Selection | 用梯度覆盖替代轮转配额，限制重复方向 | ER vs GSS-Greedy，等容量 | `external_pending` | [GSS 全文笔记](../../wiki/papers/attack-detection/2019-Wei-GSS梯度样本选择在线持续学习.md)；不能单独保证 FPR |
| L14 | CBRS 类别内 reservoir | 类别不平衡持续学习 | 二元恶意／良性分别受容量约束 | ER vs CBRS，同容量 | `external_pending` | [CBRS 全文笔记](../../wiki/papers/attack-detection/2020-Chrysakis-CBRS不平衡在线持续学习.md)；必须优于简单类别平衡才保留 |
| L15 | MADAR 多样性感知回放 | 恶意软件家族多样性 | 在已允许家族字段可用时维持历史家族覆盖 | ER vs MADAR，同历史池预算 | `external_pending` | [MADAR 全文笔记](../../wiki/papers/attack-detection/2025-Mohamed-MADAR多样性感知回放.md)；历史池与本项目总容量口径需先统一 |
| L16 | PBR 不确定性／原型回放 | 互信息与原型约束 | 任务化为旧恶意漏判的原型覆盖 | ER vs PBR，同容量 | `external_pending` | [PBR 全文笔记](../../wiki/papers/attack-detection/2024-Park-PBR先验无关平衡回放.md)；文献公式方向冲突未裁决，暂不实现 |
| L17 | ECBRS/PAPA 扰动近似 | NIDS 持续学习 | 仅作扰动稳健性诊断，不移植 AnoShift 主指标 | 与 ER 的扰动诊断对照 | `external_pending` | [ECBRS/PAPA 全文笔记](../../wiki/papers/attack-detection/2023-Amalapuram-ECBRS-PAPA网络入侵持续学习.md) |
| L18 | FreeMOCA 参数插值 | 无记忆参数保持 | warm-start／逐层插值作为无回放对照 | ER vs 参数插值，明确任务差异 | `external_pending` | [FreeMOCA 全文笔记](../../wiki/papers/attack-detection/2026-Asadi-FreeMOCA无记忆恶意代码持续学习.md)；不同数据合同，不与主表直接排名 |
| L19 | DGR 梯度重加权 | 类别不平衡持续学习 | 在相同 replay 下重加权恶意／良性梯度 | 普通类别平衡 vs DGR，等 FPR 比较 | `external_pending` | 网页报告与 CVPR 2024 原件候选；不得超过简单类别平衡才保留 |
| L20 | TERM 倾斜经验风险 | 风险敏感目标 | 在恶意缺口集合内放大高损失样本 | CE、类别加权、TERM，等 FPR 比较 | `external_pending` | 网页报告给出 Eq. (1)--(4)；高损失良性异常可能增加 FPR |
| L21 | IWMS 延迟标签回放 | 延迟标签持续学习 | 只从已确认标签 memory 取样，单独检查预测为良性的真实恶意队列 | 朴素延迟回放 vs IWMS | `external_pending` | [网页报告](../../.Codex/docs/chatgpt-handoffs/inbox/LAMDA-2026-定向漏判修复-FPR约束深度研究报告.md)；预测类别路由可能自强化漏判 |
| L22 | Chen-AL 伪损失主动学习 | Android 主动学习 | 在固定人工复核预算下选择高价值样本，标签到达后再训练 | 随机、softmax 不确定性、伪损失选择 | `external_pending` | [Chen 全文笔记](../../wiki/papers/attack-detection/2023-Chen-Android恶意软件持续学习.md)；外部结果不能当 LAMDA 数值 |
| L23 | CITADEL 半监督主动适应 | Android 漂移适应 | 作为持续标签预算强基线，需单列标签成本 | 同标签预算比较 | `external_pending` | [CITADEL 全文笔记](../../wiki/papers/attack-detection/2025-Haque-CITADEL半监督主动漂移适应.md)；课程证据只在 APIGraph |
| L24 | DREAM 漂移检测与适应 | Android 漂移专用 | 高预算行为／概念适应对照 | 同标签、同计算预算对照 | `external_pending` | 网页报告候选；工程侵入高，暂不优先 |
| L25 | 课程学习 | 课程调度方法族 | 只能使用源期可观测难度，不能按 FAR 损失排序 | 随机、反向、源期难度顺序，等样本和步数 | `conditional_candidate` | CITADEL 附录 E 只在 APIGraph；尚无 LAMDA 独立证据 |
| L26 | 强化学习维护策略 | 序贯决策方法族 | 需要合法的时间窗、维护动作、延迟反馈和成本 | 固定周期、上下文 bandit、RL，同动作预算 | `conditional_candidate` | LAMDA 当前数据没有已核准动作／奖励合同 |
| L27 | 攻击者—防守者博弈 | 对抗博弈叙事 | 需要攻击者动作、响应和反事实收益 | 与静态 DRO 区分的真实响应实验 | `excluded` | LAMDA 没有这些可观测量，不能凭概念使用 |
| L28 | 安全玩家尾锚约束（修复—保护二人博弈框架下的尾风险部件） | 修复—保护二人约束博弈（承接 L11 否决后的演化）：约束对象从全量良性均值改为当年已到达良性中旧模型分数最高尾集 | 尾锚 A_t=TopK 分位数尾保护，R̂_tail 风险代理与修复候选 R_t 对偶（同一 θ⁻、互补标签）；V1 固定 β 尾损失 / V2 乘子尾约束 | ER2018、ER2018+修复、+V1、+V2（同流 ER 锚，面板 2016–2018） | `oracle_e1_rejected` | [二人博弈尾锚约束方案](第三章-LAMDA修复保护二人博弈尾锚约束方案.md)；演化链：L11 v1 乘子发散（reject，根因）→ v2 单臂无介入／联合欠抑制（`reject_implementation`）→ 尾锚修正安全玩家作用面；**E1 oracle 判读（2026-09-09，[oracle-tail-clip.json](../../.Codex/docs/2026-09-09-LAMDA双玩家v2复筛/analysis/oracle-tail-clip.json)，脚本 `oracle_tail_clip.py` 同目录）**：T_keep（θ⁻ 判对良性按分数 TopK）对 n₊（ER 判对→缺口臂判错良性，2016：2009；2017：1748）覆盖 K=500 仅 8.8%/2.9%、K=2000 仅 34%/11.8%；oracle（尾集预测钉回 ER 判定）裁剪后 FPR 0.12–0.16，远超 ER 当年 FPR（0.0215/0.0066）——任何 K 不过 ER 门，受损良性不在冻结高分尾，V1/V2 不跑（方案 §7 停止条件第一行已触发）。演化续接 L29（受限参数修复） |
| L29 | 受限参数修复（head-only 冻结骨干＋CUR 课程调度） | 受限参数更新（承接 L28 否决后的演化）：E1 表明修复损伤为全局表征漂移，候选从“约束谁”转为限制修复的参数作用范围与深度 | head-only 冻结骨干仅调头；+CUR 浅缺口优先暴露（P10 s_e 分位调度） | ER2018、ER2018+修复（全参数历史对照）、ER2018+head-only修复、ER2018+head-only修复+CUR（同流 ER 锚，面板 2016–2018） | `pending_experiment` | [方案 §8](第三章-LAMDA修复保护二人博弈尾锚约束方案.md)；机制依据：E1（[oracle-tail-clip.json](../../.Codex/docs/2026-09-09-LAMDA双玩家v2复筛/analysis/oracle-tail-clip.json)，全局表征漂移）＋P10（[curriculum-buckets.json](../../.Codex/docs/2026-09-09-LAMDA双玩家v2复筛/analysis/curriculum-buckets.json)，穿越代价分位调度）；共同预算：容量 200、种子 42、10 轮、批 1024、阈值 0.5、到达流 2013→2014→2016→2017→2018；判据沿用方案 §7 主判据（同流 ER 锚）；运行身份预定 `ch3-lamda-restricted-repair-screening-mps-seed42-v1`，MPS 预计 20–25 分钟 |

## 逐项筛选顺序

1. 完成当前运行 L3/L4/L5 的来源／项目开发层筛选，先判断缺口修复和条件门控是否有独立信号。
2. 若 L3 有信号而保护不足，取得并核验 PCT／Focal Distillation 原件，运行 L2 直接基线，再测试 L3＋L2＋FPR gate。
3. 若记忆选择仍是瓶颈，按 L12→L13→L14 的顺序逐项替换记忆策略；每项先做同容量单臂，不同时叠加多个采样器。
4. L11 双玩家 v2 已按源年筛查否决（单臂未介入、联合臂不通过 FPR 与旧恶意保持门，见上表）；演化候选 L28 尾锚于 2026-09-09 经 E1 oracle 判读否决（`oracle_e1_rejected`，见上表与方案 §3）；**当前下一动作：L29 受限参数修复四臂待跑**（ER2018 锚 / ER2018+修复 / ER2018+head-only修复 / ER2018+head-only修复+CUR，运行身份预定 `ch3-lamda-restricted-repair-screening-mps-seed42-v1`）；修复层约束都不能绕过独立 FPR gate。
5. L15--L24 只在前述最小路线没有足够信号且资源预算允许时进入；强化学习和攻击者博弈保持条件状态；课程调度不再独立重开——L25 维持条件状态，其 P10 病灶由 L29 第四臂 CUR 部件吸收（方案 §8），L29 通过也不把 L25 升级为独立候选。
6. 任何候选通过来源／开发层后，才允许冻结一次 `2019--2023` 封印评价；`2024/2025` 只作探索性报告，目标期结果不得回灌台账排序。

## 统一失败门

- FPR gate 违反，直接淘汰该具体实现，即使 AP、F1 或 FNR 更好。
- 等 FPR 下不能降低 FNR 或提高恶意正向修复率，淘汰该候选的任务化差量。
- 只降低旧恶意负向翻转而不修复当前恶意，标记为安全基线，不升级主算法。
- 优势可由阈值匹配、简单类别平衡或随机同容量记忆复现，不能宣称机制独立贡献。
- 使用未来标签、封印年指标、测试反馈或未冻结的人工标注预算，运行作废。
- 联合臂不优于最好单臂或无法解释交互，保留单机制或 ER，不凑两个机制。

## 结果写回规则

- 每次真实运行完成后，在本台账更新运行身份、配置哈希、数据版本、逐年制品路径、主指标和状态；不覆盖历史行。
- `external_pending` 只有取得本地原件、结构化全文笔记和适配表后才能变为可运行候选。
- `experiment_support` 只描述已经测得的作用面；不得把筛查结果扩大为跨年份正式结论。
