# ChatGPT 只读交接包

**状态：外部候选，待本地全文和实验复核。**

## 快照与执行配置

- repository：`NatsuiroGinga/bilibili-note`
- branch：`exp/ch3-drift-20260908`
- commit：`c94d8f1c1e8a0fbe7fb2817c04097241d12934d6`
- requested_model：`auto`
- requested_effort：`high`
- fallback_model：``
- selection_rationale：`全部候选的评估/排序/组合/挖掘需深推理与文献调研；现状自包含`
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

对本课题第三章的**全部候选方案**逐个评估、排序、组合并挖掘遗漏。**你可以在沙箱运行代码自验数学**（沙箱环境与本地隔离）。GitHub 白名单文件可能 404，以下现状自包含。

【方法与证据基线】DRIFT DGA 二分类 24M 双分支。病灶：CharBot 2 位替换检出缺口 36%/MaskDGA 半替换 68%。16 臂源期筛选（T17 抽 6 万、T18 三面板 k2/krand/maskdga）+第二骨干 B-ResNet 两轮+三组条件定理+数值验证 V1-V3。

【全部候选方案清单（按分组）】
■ 主候选 F：组件 1（恶意侧组相对过滤：K=4 变体、二值 fooled−组均值、无门、跨组配额 top-64）+组件 2（良性误报加权 CE×3）。证据：对朴素增广帕累托支配（仅 DRIFT 骨干）、组件正交闭环（D/G 单臂）、V1 捕获率谱系 1.0/0.728/0.435、B-ResNet 方向复现且朴素增广失效、正式全量 A/B 跑着。弱过门变体：L（课程 弱→中→强）增量小于波动不入正式。
■ 已否决库（各有失败模式归因）：H 对称组相对（检出回退超容差）；I batch-CVaR（尾部梯度劫持）；J τ-对偶 CVaR（τ 塌陷+1/α=20 放大器冲突）；K stateless bandit（L1 不过门：随机替换已近最优+奖励非平稳）；E KL 锚定（无效应）；C 全入批（批次失衡 5:1 教训）。
■ 进行中：P 臂（K=8 搜索预算扩展——V3 预测覆盖缺口 0.2978→~0.16，训练级检验跑着）；N 臂已出（per-group 检出优于 cross-group——覆盖-强度权衡实证）；N2 已出（per-group+加权与 F 统计等效——选择算子差异被加权掩盖）。
■ 待筛队列（设计自由度审计 10 项）：O 长度比例自适应 K；组定义变体（family/长度）；soft 加权形式；q-K 耦合（定理 3D β 制度）；阈值 t 源验证标定；覆盖下界机制；连续 λ 插值课程（F20-F23）；训练预算分配；算子族扩展（插入/交换）；良性侧其他保护形式。
■ 已确立约束：组内排序与原始违规量代数等价；跨组配额竞争是三近邻（Tramèr/MaxUp/MMEL/BiB）皆无的运算（但其训练级增量被加权掩盖——N2 vs F 等效）；benign×3 是 state-dependent excess-risk reweighting；Danskin 意义下传统 AT 梯度精确；离散黑盒域无 PGD 可用；单冻结种子。

【请输出】1) 全部候选逐个评估：每个的潜在收益上限/成本/风险/与 16 臂证据的兼容性/优先级；2) 组合方案：哪些候选应组合成最终方法的最优形态（如 F+课程+FPR 保护调优的联合），组合的正当性论证结构；3) 遗漏候选挖掘：第 11+ 个有文献依据的机制方向（从独有实验现象挖掘：B-ResNet 上朴素增广失效而组相对有效、M 曝光增益伴 FPR 代价、N2 加权掩盖算子差异——这些现象暗示什么新机制）；4) 明确不推荐的方向及理由；5) 诚实边界：全部建议标外部候选。

## 返回合同

返回 Markdown，注明 actual_model、actual_effort、actual_mode、used_apps、
结论、逐项证据、来源与精确位置、不确定性和未回答问题。
结果一律是外部候选，待本地全文和实验复核，必须由发起方独立复核。

## 禁止操作

不得修改 Git、运行代码、访问白名单外路径，也不得输出或索取原始数据、
数据集、权重、检查点、日志、凭据、服务器连接、个人绝对路径、原始 PDF、
未获授权目标期信息或其他敏感内容。不得验证实验有效性、裁决候选存废或改写冻结合同。
