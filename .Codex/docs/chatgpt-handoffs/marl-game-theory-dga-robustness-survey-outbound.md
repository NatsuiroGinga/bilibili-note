# ChatGPT 只读交接包

**状态：外部候选，待本地全文和实验复核。**

## 快照与执行配置

- repository：`NatsuiroGinga/bilibili-note`
- branch：`exp/ch3-lamda-20260908`
- commit：`947551cb5a6ac9858c26495f927237b7e70bb060`
- requested_model：`auto`
- requested_effort：`high`
- fallback_model：``
- selection_rationale：`由发起方按任务复杂度、额度与可用模型选择`
- requested_mode：`deep-research`
- requested_apps：`github`
- task_type：`literature-review`
- source_scope：`本消息自包含，无外部文件依赖`
- sanitized_summary_included：`true`
- fulltext_required：`false`
- zotero_ingest_required：`false`
- allowed_paths：
  - `.Codex/docs/2026-09-09-LAMDA-双玩家约束/task_plan.md`
  - `.Codex/docs/2026-09-09-LAMDA-双玩家约束/notes.md`
  - `.Codex/docs/2026-09-09-LAMDA双玩家v2复筛/analysis/analysis-report.md`
  - `.Codex/docs/2026-09-09-LAMDA双玩家v2复筛/analysis/v2-independent-analysis.json`
  - `.Codex/docs/2026-09-09-LAMDA缺口修复/analysis/analysis-report.md`

## 任务

基于上述背景与已提供线索，完成博弈×强化学习×MARL×对抗鲁棒的交叉文献调研（每条附原始出处：作者/会议或期刊/年份/节号，标注核验状态）。子题一：攻击者-防守者双侧学习的对抗博弈在网络安全检测（恶意软件/入侵/DGA/垃圾邮件）的先例——哪些工作让攻击者与检测器同时学习？各自如何处理双侧学习的非平稳性（循环追逐、模式坍缩、对手建模过拟合）？学习型攻击者相对固定攻击器（CharBot/MaskDGA 式固定算子）的收益是否有实证？子题二：MARL 综述文献（含已提供的 Hernandez-Leal、李艺春、杜威、罗彪等）中处理非平稳性与对手建模的稳定化技术清单——哪些可以借到'检测器+攻击者'双人博弈的单步（非序列）设定（我们的动作是一次域名扰动，不是多步轨迹）？子题三：GRPO 家族与 MARL 的交叉——有没有把组相对优势/无评论家结构用于多智能体或多玩家对抗的先例（如 MAPGRPO、多智能体 GRPO）？我们的'攻击者组采样+组相对优势'与 MADDPG 式集中式批评家的本质区别如何论证？子题四：单步对抗生成（one-shot perturbation，非多步轨迹）的 RL 形式化先例——把'生成一个扰动域名叫检测器误判'作为单步决策的 RL 问题，奖励=是否绕过，有没有先例与陷阱（reward hacking：生成无意义字符串绕过但脱离恶意语义——如何约束扰动保持恶意语义有效性，如同家族可解析性/与原域名编辑距离上界）？子题五：综合评估——P4（MARL 形态）相对 P3（固定攻击者组相对）的预期增量与风险对比，给出'是否值得在 P3 过门后投入 MARL'的文献依据；若有第三条中间形态（如对手模型预训练+冻结、对手池/league 机制——AlphaStar/OpenAI Five 的对手池思想），给出可借鉴的具体机制与出处。全部输出为外部候选建议，每条标注文献核验状态；本地保留裁决权。

## 脱敏实验摘要

研究背景（自包含）：DGA 域名检测的对抗规避鲁棒方向（DRIFT 基准，字符+子词双分支 Transformer 24.2M 参数）。已实测病灶：MaskDGA 式半替换扰动使本课题官方模型检出率相对下降 69.1%（FPR=1% 工作点）、CharBot 式 2 位替换下降 33.6%（本地 3 万域实测，单种子 screening）。已规划的三层实验结构：P2 朴素对抗增广训练（CharBot 算子）→ P3 组相对加权对抗训练（GRPO 组相对优势结构任务化：同一域名的 K 个扰动变体为一组，能骗过检测器的变体主导梯度，权重每半 epoch 刷新）→ P4 多智能体强化学习形态（攻击者智能体用 GRPO 组采样学习扰动策略，检测器智能体同步更新——双侧学习博弈）。已知约束：对抗训练 DGA 已有 Drichel 2404.06236（ASIA CCS 24，32 种白盒攻击、联合对抗训练优于仅嵌入空间 AT 10.15%）——P4 的差量必须落在训练动力学与对手建模深度上，不能落在对抗训练本身。已提供 MARL 综述线索（无需重复检索这些论文本身）：李艺春等 多智能体强化学习的博弈综述 自动化学报 2025；杜威丁世飞 多智能体强化学习综述 计算机科学 2019 46(8)；罗彪等 多智能体强化学习控制与决策研究综述 自动化学报 2025；Hernandez-Leal 等 A survey and critique of multiagent deep reinforcement learning AAMAS 2019 33(6)；Tampuu 等 Multiagent cooperation and competition with deep RL PloS One 2017；Tan M. MARL independent vs cooperative agents ICML 1993；Lowe 等 MADDPG NeurIPS 2017。

## 返回合同

返回 Markdown，注明 actual_model、actual_effort、actual_mode、used_apps、
结论、逐项证据、来源与精确位置、不确定性和未回答问题。
结果一律是外部候选，待本地全文和实验复核，必须由发起方独立复核。

## 禁止操作

不得修改 Git、运行代码、访问白名单外路径，也不得输出或索取原始数据、
数据集、权重、检查点、日志、凭据、服务器连接、个人绝对路径、原始 PDF、
未获授权目标期信息或其他敏感内容。不得验证实验有效性、裁决候选存废或改写冻结合同。
