# ChatGPT 只读交接包

**状态：外部候选，待本地全文和实验复核。**

## 快照与执行配置

- repository：`NatsuiroGinga/bilibili-note`
- branch：`exp/ch3-drift-20260908`
- commit：`c94d8f1c1e8a0fbe7fb2817c04097241d12934d6`
- requested_model：`auto`
- requested_effort：`high`
- fallback_model：``
- selection_rationale：`10 项设计自由度的逐项评估需文献调研+机制推演；沙箱代码自验已获用户授权`
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

对 DGA 对抗鲁棒训练方法的『设计自由度审计表』逐项评估并补全。**你可以在沙箱运行代码自验数学**（沙箱环境与本地隔离）。

【背景】DRIFT DGA 二分类 24M 双分支。已完成 16 臂筛选（源期 T17 抽 6 万、T18 三面板）：F 形态（组件 1=恶意侧组相对过滤：K=4 变体、二值 fooled−组均值、无门、跨组配额 top-64；组件 2=良性误报加权 CE×3）对朴素增广帕累托支配（仅 DRIFT 骨干），五变体方向（H 对称/I·J CVaR/K bandit/L·M 课程）全未同时改善两轴。三组条件定理（分配律/共同下降/双预算分解）+数值验证 V1-V3（捕获率谱系 1.0/0.728/0.435、梯度余弦 0.373、覆盖缺口 0.2978）。外部审查已确认：组内排序与原始违规量代数等价、跨组配额竞争是三近邻（Tramèr/MaxUp/MMEL/BiB）皆无的运算、benign×3 是 state-dependent excess-risk reweighting 非 max 估计器、选择器值函数梯度为零。

【设计自由度审计表（10 项，逐项评估）】
1. 变体数 K：固定 4 → 长度比例自适应 K_i=max(2,⌈ℓ_i/4⌉)？V3 缺口 0.2978 在长短域名间不均（长域名严重欠采样）；P 臂（K=8 均匀）正在跑
2. 变体算子族：perturb2 固定 → 课程三档（L 弱过门）→ 算子族扩展（插入/交换/删除——CharBot 明确不用，MaskDGA 半替换在用）？
3. 组定义：按干净域名 → 按 family/长度/生成器分组？（组相对信号的含义随组定义改变）
4. 加权形式：hard×3 → 连续 soft（I/J 的 CVaR 形态被否决——但非 CVaR 的 soft 指示加权未筛）？
5. 配额 q=64：固定 → 与 K 耦合（定理 3D β 制度）/按 N₊ 容量动态？
6. 阈值 t=0.5：固定 → 源验证标定（判据 v2 提及未做）？
7. 良性侧保护形式：hard 加权 → 非组相对的其他形式（H 否决的是组相对对称，非全部保护形式）？
8. 覆盖保证：无（cross-group 允许部分样本零覆盖，chatgpt4 警告覆盖集中）→ 覆盖下界机制？
9. 调度路径形状：三档阶梯 → 连续 λ 插值（F20-F23 transport 课程，代码未实现）？
10. 训练预算分配：每档 1 epoch → 有效优化步预算定义（外审警告未定义）？

【请输出】1) 十项逐项：可行性/预期收益/成本/风险/与 16 臂已筛空间的正交性/优先级排序；2) 每项的最小验证实验设计（screening 级）；3) 第 11+ 项：审计表遗漏的设计自由度（从我们的方法结构与文献族挖掘）；4) 组合评估：哪几项可同时做、哪几项互斥；5) 诚实边界：哪些项你判断为低价值不值得筛。

## 返回合同

返回 Markdown，注明 actual_model、actual_effort、actual_mode、used_apps、
结论、逐项证据、来源与精确位置、不确定性和未回答问题。
结果一律是外部候选，待本地全文和实验复核，必须由发起方独立复核。

## 禁止操作

不得修改 Git、运行代码、访问白名单外路径，也不得输出或索取原始数据、
数据集、权重、检查点、日志、凭据、服务器连接、个人绝对路径、原始 PDF、
未获授权目标期信息或其他敏感内容。不得验证实验有效性、裁决候选存废或改写冻结合同。
