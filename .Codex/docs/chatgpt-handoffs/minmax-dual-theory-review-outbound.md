# ChatGPT 只读交接包

**状态：外部候选，待本地全文和实验复核。**

## 快照与执行配置

- repository：`NatsuiroGinga/bilibili-note`
- branch：`exp/ch3-drift-20260908`
- commit：`e335c20ccf957e4a86b500a3982ea8ff68cbc1d0`
- requested_model：`auto`
- requested_effort：`high`
- fallback_model：``
- selection_rationale：`纯数学对抗审查，chat+high 即可；GitHub app 供其读取白名单内方案文档核对实现细节`
- requested_mode：`chat`
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

对我们提出的双侧组相对对抗训练统一框架做理论对抗审查（机制反例推演），找出数学上的坑与审稿人必问题。框架表述：min_θ [ max_{变体组G_i^mal} E ℓ(f_θ(x̃),y) + λ·CVaR_α(良性尾部) ℓ ]，其中恶意侧内层 max 用组相对优势蒙特卡洛实现（对同一干净域名的 K=4 字符扰动变体计算违规量 u=|s(x̃)−y|，减组内留一均值基线得优势，正优势变体 top-q 配额入批）；良性侧用 batch 内真良性样本 CE 的 CVaR_α（最坏 5% 分位均值，硬 top-k 形式）。三个具体问题：Q1 双内层 max 联合优化的收敛风险——交替更新两个内层 max 是否存在振荡/不收敛构造，何时需要共享内层解；Q2 组相对 top-q 硬选择作为内层 max 估计的偏差——无偏基线命题（留一均值基线下梯度估计期望等于 REINFORCE 梯度）是否被 top-q 截断破坏，截断偏差有无界定或缓解表述；Q3 batch 内 CVaR_α 经验估计与总体 CVaR 的偏差随批大小的行为（batch 1024 中良性约 512 个、α=0.05 即最坏 25 个样本的均值——估计方差量级），以及与全数据 CVaR 的关系。输出：每问给出反例构造或收敛条件、审稿人可能的攻击线、规避表述建议。只做数学推演，不需要联网检索文献。

## 返回合同

返回 Markdown，注明 actual_model、actual_effort、actual_mode、used_apps、
结论、逐项证据、来源与精确位置、不确定性和未回答问题。
结果一律是外部候选，待本地全文和实验复核，必须由发起方独立复核。

## 禁止操作

不得修改 Git、运行代码、访问白名单外路径，也不得输出或索取原始数据、
数据集、权重、检查点、日志、凭据、服务器连接、个人绝对路径、原始 PDF、
未获授权目标期信息或其他敏感内容。不得验证实验有效性、裁决候选存废或改写冻结合同。
