# ChatGPT 只读交接包

**状态：外部候选，待本地全文和实验复核。**

## 快照与执行配置

- repository：`NatsuiroGinga/bilibili-note`
- branch：`exp/ch3-drift-20260908`
- commit：`05e76858c35c902826984e3f630d2ecd42da3bde`
- requested_model：`auto`
- requested_effort：`high`
- fallback_model：``
- selection_rationale：`机制近邻排重与威胁模型调研需联网全库检索，deep-research 高强度；本地文献代理已并行本地库检索，此为双线之二`
- requested_mode：`deep-research`
- requested_apps：`github`
- task_type：`neighbor-deduplication`
- source_scope：`白名单路径`
- sanitized_summary_included：`false`
- fulltext_required：`false`
- zotero_ingest_required：`false`
- allowed_paths：
  - `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/task_plan.md`
  - `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/h-arm-research-question-card.md`

## 任务

两个检索主题，输出题录+出处锚点+每条标证据等级（全文/摘要/仅题录），检索未获也如实声明并列出已用检索式：主题一：误报注入攻击（false positive injection / alert flooding / 告警预算消耗 / 攻击者故意制造误报以掩护真实入侵）作为正式威胁模型在 NIDS/IDS/恶意软件检测文献中的先例，2000-2026 年，含对抗机器学习侧（poisoning 攻击抬高误报率）与安全运营侧（alert fatigue）两个角度。主题二：判别式分类任务的对抗训练中，是否存在先例使用「同一干净训练样本的多个扰动变体组内的相对信号（如组内均值基线、留一基线、组内排序）」来做样本选择或梯度加权——排除 RL 策略优化场景（GRPO/GFPO/RLOO/PPO 组内优势已知），找图像/文本/网络流量/恶意软件检测等判别任务上的先例。背景（可引用）：我们的方法对同一干净域名生成 K=4 字符扰动变体为组，组内 fooled 相对信号 top-k 过滤入批（恶意侧），良性侧拟对称构造 CharBot 近邻组，组内误报信号加权；已对照 Drichel 2024 均匀切分（无组内选择）、CharBot 静态增广、MaskDGA 白盒迭代，均无组内相对机制。

## 返回合同

返回 Markdown，注明 actual_model、actual_effort、actual_mode、used_apps、
结论、逐项证据、来源与精确位置、不确定性和未回答问题。
结果一律是外部候选，待本地全文和实验复核，必须由发起方独立复核。

## 禁止操作

不得修改 Git、运行代码、访问白名单外路径，也不得输出或索取原始数据、
数据集、权重、检查点、日志、凭据、服务器连接、个人绝对路径、原始 PDF、
未获授权目标期信息或其他敏感内容。不得验证实验有效性、裁决候选存废或改写冻结合同。
