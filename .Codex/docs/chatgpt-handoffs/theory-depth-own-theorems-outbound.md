# ChatGPT 只读交接包

**状态：外部候选，待本地全文和实验复核。**

## 快照与执行配置

- repository：`NatsuiroGinga/bilibili-note`
- branch：`exp/ch3-drift-20260908`
- commit：`eb4fd3e311f63440eeb8f52f0e5e0bfe464b1af0`
- requested_model：`auto`
- requested_effort：`high`
- fallback_model：``
- selection_rationale：`三定理完整推导需要深数学推理；朱式范式与现状自包含；白名单文件供核对`
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

为毕业论文第三章直接推导自有定理（完整陈述+证明）。GitHub 白名单可能 404，现状自包含。

【参照范式：朱式方法改造】朱第三章（加密流量对抗鲁棒，双骨干）构思链：①第二章把 Min-Max 对抗训练病灶拆三项（非凸内层收敛难/鲁棒-自然失衡/多步开销）；②攻击时序假设把扰动形式化为参数响应函数 δ*(θ)，传统 AT 把 δ* 当常数的缺陷被形式化为『外层更新遗漏参数对攻击策略的诱导』；③组件 DS 从课程学习家族任务化为三调度公式 ε(t)/K(t)/α(t)；④组件 RGO 从 Stackelberg/双层优化/展开优化任务化为『分类器领导者、伪装跟随者，内层 PGD 轨迹纳入外层求导』（更新=直接项+反应项）；⑤联合=过程耦合 DS→轨迹→RGO；⑥消融四臂×2骨干组合增益 12.3>两单臂之和 9.0；⑦3 定理引理但 0 个有编号假设/误差界/收敛率，且 ET-BERT 实现 requires_grad=False+δ* 常数化→dδ*/dθ=0 反应梯度实现级断裂；⑧弱结果表达『干净准确率损失控制在 2.1% 内』。

【我们的现状】DRIFT DGA 二分类官方 24M 双分支。病灶：CharBot 2 位替换检出缺口 36%/MaskDGA 半替换 68%。十一臂筛选+第二骨干两轮已完成：组件 1=恶意侧组相对过滤（每干净域名 K=4 变体、违规量 u=|s−y| 减组均值、跨组全局配额 top-64）；组件 2=良性误报加权（误报真良性 CE×3.0）；F=组件1+2 对朴素增广帕累托支配（仅 DRIFT 骨干）；B-ResNet 第二骨干上组件方向复现且朴素增广两轮 lr 均失效（反证选择机制增量）。已确认约束：①组内排序与原始违规量代数等价（A_i=K/(K−1)(u_i−ū)）②三近邻 Tramèr 组内 max/MaxUp worst-copy/BiB 同源误分类选择均无跨组配额竞争 ③无持久攻击者参数，内层=Monte Carlo hard-mining operator ④P1-P4 全部为 RLOO/REINFORCE/CVaR 已知结果重述，无一新定理 ⑤已否决：KL 锚定/对称组相对/batch-CVaR/τ-对偶 CVaR/stateless bandit 攻击者（随机替换在该动作空间已近最优）⑥独有实验现象：B-ResNet 上朴素增广两轮失效而组相对过滤强效；F 的组合在两骨干上均为『检出大增+FPR 可控代价』的帕累托移动模式。

【任务：直接推导以下三个自有定理的完整陈述与证明（不是审查计划，是产出数学）】
定理 1（选择算子谱系）：对抗训练样本选择三算子——uniform（朴素增广，每干净样本均匀选变体）/per-group top-k（每组选组内最难）/cross-group budgeted（我们，全局 top-q 跨组竞争）——在组骗过率异质条件下的『已骗过样本捕获数』期望的闭式比较。建议路径：两类型混合模型（π 比例高骗过组 p_h、1−π 低骗过组 p_l，变体分数独立），推导 E[C_uniform]/E[C_per-group]/E[C_budgeted] 闭式与三者严格排序的充要条件（π、p_h、p_l、q 的显式阈值）；非平凡性要求：给出 cross-group 严格优的参数区域与退化为等价的边界，并讨论覆盖-强度权衡（per-group 覆盖全部组，budgeted 集中高违规组）。
定理 2（双侧梯度近正交）：恶意侧 hard-risk 梯度与良性侧尾部梯度在分数-参数线性化下的内积结构。建议路径：一阶泰勒 s_θ(x)≈s_0(x)+⟨∇s(x),θ−θ_0⟩，梯度内积=误报良性样本对×骗过恶意变体对的特征梯度 Gram 块和；证明当两组样本的特征梯度相关（NTK 风格 Gram 块间范数）小于块内范数时（条件：字符扰动邻域的恶意变体与真实良性分布的特征梯度低相关），联合目标的帕累托改进性质成立（联合一步更新在两轴上都不劣于单独更新）；给出正交性退化的反例条件。
定理 3（预算-缺口收缩界）：K 个 i.i.d. 违规量的 order-statistic 对 sup 的逼近误差：Uniform 情形闭式 E[max_k u_k]=K/(K+1)、缺口=1/(K+1)；一般尾部的收缩率分档（指数尾 O(1/K)/重尾 O(K^{-1/τ})）；把 K 解释为攻击者搜索预算的定量语义，并给出 K=4 在 Uniform 下的缺口 0.2 作为可验证实例。
每定理要求：编号假设（显式列出）/定理陈述/完整证明/理想化假设与真实网络差距的诚实边界声明/可数值验证的推论（如定理 1 的闭式可用 Monte Carlo 验证、定理 2 的 Gram 块间范数可用真实模型 NTK 采样实测）。

【输出】三定理的完整数学（陈述+证明+边界+数值验证推论）；若某定理被证明不可行（如条件过强），给出替代命题；最后给出三定理作为一组对参照论文『3 定理引理但 0 个可核验』的理论对标评估。

## 返回合同

返回 Markdown，注明 actual_model、actual_effort、actual_mode、used_apps、
结论、逐项证据、来源与精确位置、不确定性和未回答问题。
结果一律是外部候选，待本地全文和实验复核，必须由发起方独立复核。

## 禁止操作

不得修改 Git、运行代码、访问白名单外路径，也不得输出或索取原始数据、
数据集、权重、检查点、日志、凭据、服务器连接、个人绝对路径、原始 PDF、
未获授权目标期信息或其他敏感内容。不得验证实验有效性、裁决候选存废或改写冻结合同。
