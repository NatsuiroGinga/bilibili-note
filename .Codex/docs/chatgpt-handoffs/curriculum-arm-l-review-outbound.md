# ChatGPT 只读交接包

**状态：外部候选，待本地全文和实验复核。**

## 快照与执行配置

- repository：`NatsuiroGinga/bilibili-note`
- branch：`exp/ch3-drift-20260908`
- commit：`eb4fd3e311f63440eeb8f52f0e5e0bfe464b1af0`
- requested_model：`auto`
- requested_effort：`high`
- fallback_model：``
- selection_rationale：`新增机制臂的 HARD-GATE 外部审核：判据漏洞与失败模式审查需深推理；现状自包含`
- requested_mode：`deep-research`
- requested_apps：`github`
- task_type：`mechanism-counterexample`
- source_scope：`白名单路径`
- sanitized_summary_included：`false`
- fulltext_required：`false`
- zotero_ingest_required：`false`
- allowed_paths：
  - `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/task_plan.md`
  - `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/h-arm-research-question-card.md`

## 任务

审核 L 臂（攻击难度课程×组相对过滤）的机制设计与冻结判据，找出失败模式与判据漏洞。现状自包含：DRIFT DGA 二分类官方 24M 双分支；病灶 CharBot 2 位替换检出缺口 36%/MaskDGA 半替换 68%；已筛选十一臂：组件 1=组相对过滤（每干净恶意域名 K=4 变体、二值 fooled 减组均值、无正优势门、跨组全局配额 top-64、确定性并列破法）对朴素增广检出大幅改善（DRIFT 骨干 22 倍/B-ResNet 11 倍）且 B-ResNet 上朴素增广两轮失效反证其增量；组件 2=良性误报加权（误报真良性 CE×3.0）；F=组件1+2 对 B 帕累托支配（仅 DRIFT 骨干）；已否决：KL 锚定/对称组相对/batch-CVaR/τ-对偶 CVaR/stateless bandit 攻击者（L1 不过门：随机替换已近最优+奖励非平稳）。三定理数值验证已完成：V1 三算子捕获率谱系（真实重放 cross-group 1.0/per-group 0.728/uniform 0.435——跨组配额竞争把预算 100% 填满被骗变体）；V2 双侧梯度部分正交（平均余弦 0.373、单样本 400 对中位 0.135、98%<0.3）；V3 预算-缺口（Uniform 闭式通过、真实 K=4 缺口 0.2978、τ_eff≈2.14）。

【L 臂设计】机制=攻击难度课程×组相对过滤：epoch 1=1 位替换(弱)→epoch 2=2 位(中)→epoch 3=半替换(强)，每档 1 epoch；每档内部组相对过滤与组件 1 完全一致（二值 fooled−组均值、无门、跨组 top-64、确定性破法）；变体缓存键含 epoch。家族锚点：课程对抗训练（Cai 2018 起源）+Shi&Liu 2024 课程 AT 在线视角（本地全文）——其理论=每轮对抗样本来自不同分布，Wasserstein 距离界相邻迭代分布误差差（Prop 4.1/4.2）+序贯 Rademacher 复杂度，『逐步加难使相邻迭代分布漂移最小化→泛化提升』；我们的算子阶梯相邻分布漂移最小（1 位与 2 位替换的分布距离远小于 2 位与半替换）。差量：Shi&Liu 无组内选择/跨组配额；BiB 等无课程——课程×组相对为正交组合。

【冻结判据】L vs D（同 screening 规格：T17 抽 6 万、3 epochs、batch 128 梯度累积、种子 42、T18 三面板）：主判据=maskdga 面板检出（FNR）改善，或检出持平（±0.003）条件下干净 FPR 更低；理论预期（Shi&Liu 界背书）=L 的逐 epoch 干净 FPR 曲线更平稳、最终检出 ≥D。失败形态预登记：①强档（半替换）变体骗过率低→组均值低→被骗者优势高→行为正常；但若强档变体全未骗过（M=0）则整组优势 0（并列簇垫底）→强档贡献塌缩为 0；②课程后期强档变体与 D 的 2 位变体分布差异是否足以产生增量未知；③每档仅 1 epoch，档内学习可能不充分。

【请输出】1) 判据漏洞审查（主判据/容差/失败形态是否完备）；2) 调度设计的改进建议（档位设置/每档时长/算子阶梯的其他选择——如连续预算插值 vs 离散档位）；3) 与 Shi&Liu 理论的对齐审查（我们的实例化是否成立、Wasserstein 漂移论证在字符离散分布上如何操作化）；4) 与已否决臂（H 对称化/I/J CVaR/K bandit）的失败模式交叉——L 是否有重叠风险；5) 机制差量的诚实边界（课程×组相对组合在课程 AT 文献中的新颖度）。

## 返回合同

返回 Markdown，注明 actual_model、actual_effort、actual_mode、used_apps、
结论、逐项证据、来源与精确位置、不确定性和未回答问题。
结果一律是外部候选，待本地全文和实验复核，必须由发起方独立复核。

## 禁止操作

不得修改 Git、运行代码、访问白名单外路径，也不得输出或索取原始数据、
数据集、权重、检查点、日志、凭据、服务器连接、个人绝对路径、原始 PDF、
未获授权目标期信息或其他敏感内容。不得验证实验有效性、裁决候选存废或改写冻结合同。
