# ChatGPT 只读交接包

**状态：外部候选，待本地全文和实验复核。**

## 快照与执行配置

- repository：`NatsuiroGinga/bilibili-note`
- branch：`exp/ch3-drift-20260908`
- commit：`1e2201f5576f9d78feabc3e042e9c65423b4ef4d`
- requested_model：`GPT-6 Pro`
- requested_effort：`high`
- fallback_model：`GPT-5.5`
- selection_rationale：`多篇全文、指标取舍、组合机制近邻与数学边界需要高能力模型高强度深度研究；输出限定为待本地复核的外部候选。`
- requested_mode：`deep-research`
- requested_apps：`github`
- task_type：`experiment-analysis`
- source_scope：`固定提交中的16份公开Markdown、DRIFT官方arXiv与按证据缺口检索的公开原始文献`
- sanitized_summary_included：`true`
- fulltext_required：`true`
- zotero_ingest_required：`false`
- allowed_paths：
  - `wiki/papers/attack-detection/朱焱雷-全文.md`
  - `.Codex/docs/2026-09-07-DGA检测系统综述/文献综述.md`
  - `.Codex/docs/2026-09-07-DRIFT引用与方法前沿/文献综述.md`
  - `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/task_plan.md`
  - `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/zhuh-ch3-benchmark.md`
  - `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/V4真实T17嵌套编辑耦合核查实施报告.md`
  - `thesis/methods/第三章-朱焱雷第三章机制构思与创新声明分析.md`
  - `thesis/methods/第三章-F指标空间与朱焱雷实验对照核查.md`
  - `thesis/methods/第三章-DRIFT数据角色与评价协议.md`
  - `thesis/methods/第三章-正式攻击与目标抽样合同裁决.md`
  - `thesis/methods/第三章-正式评价与F指标空间科研裁决.md`
  - `thesis/methods/第三章-理论命题包.md`
  - `thesis/methods/第三章-方法来源台账.md`
  - `thesis/methods/第三章-命题级原创性排重报告.md`
  - `thesis/methods/第三章-命题级原创性科研裁决.md`
  - `wiki/papers/methodology/2024-Losch-ESAT选择性对抗训练.md`

## 任务

仅做公开文献与理论候选分析，不运行代码、不修改任何内容、不裁决候选存废。先通过GitHub只读实际打开固定提交1e2201f5576f9d78feabc3e042e9c65423b4ef4d上的全部16条白名单路径，并另读DRIFT官方原文入口https://arxiv.org/abs/2605.10436及其官方HTML版本https://arxiv.org/html/2605.10436v2。逐项回报读取成功的相对路径与固定提交。优先使用已给全文和题录，只有证据缺口才检索公开原始文献。必须按原文复核指标取舍：表II用整体微平均F1作架构消融；表III用准确率、精确率、召回率、F1作预训练任务消融；表IV/VII与图6用逐年FPR/FNR；图5/表V用逐家族TPR及宏微平均；表VI用总体四指标；表VIII未见家族FNR；图7适应实验用逐年F1。全开F1 0.9646低于MTP加TOV的0.9660，作者按较高召回率取舍。因此不得强制所有指标逐项最优，也不得把F1一概作为任务外指标。本课题的低误报源阈值是已批准的任务化评价，DRIFT原文没有该协议；FPR是否为硬约束仍服从已批准合同，不得擅改。研究如何组合低漏检与低误报优势，只考虑训练机制组合、分数融合、条件决策三类假设。必须区分边际错误率与逐样本联合错误；部署方案不得以真标签选择模型。以尚无完整结果的MP混合曝光加F误报保护缺失格为优先参照，最多给出三条有全文依据且可由最小实验反证的外部候选，不作存废裁决。每条候选必须给出数学目标、假设、可观测量、近邻覆盖与差量、反例、条件代理更新、理想误差与实现误差、验证对照；不要为凑公式重复推导报告14。尊重后续审计和V4；F5双侧母问题、F20至F23课程路径均非当前生产组件。新增要求：对核心指标、必要护栏、辅助记录三类指标分别定位，并独立标注正文、附录、内部记录三种适用呈现位置；结合朱焱雷表3-5至3-7、DRIFT表II至VIII与DGA公开全文，为每项给出文献证据、用途及适用位置的矩阵和候选分类建议。不得据此直接更改任何已批准评价合同。说明哪些主指标必须满足，哪些仅为辅助诊断；不得擅自新增阈值或容差，也不得改动任何冻结数值合同：源验证良性共同成员、每臂0.1%主和1%辅阈值、T20至T25每年每类最多200000固定哈希唯一实体且无member_seed、共享编辑流k=1/k=2/random_half。每条文献或公式附官方来源URL、章节或页码、证据等级；只有摘要时明确标摘要。输出只能是外部候选，等待本地全文、数学与代码复核后才可能进入真实实验。

## 脱敏实验摘要

源期筛选中，F尚非所有任务指标最优；部分候选攻击漏检更低但良性误报更高。MP组合尚无完整结果。边际汇总不足以证明互补性。

## 返回合同

返回 Markdown，注明 actual_model、actual_effort、actual_mode、used_apps、
结论、逐项证据、来源与精确位置、不确定性和未回答问题。
结果一律是外部候选，待本地全文和实验复核，必须由发起方独立复核。

## 禁止操作

不得修改 Git、运行代码、访问白名单外路径，也不得输出或索取原始数据、
数据集、权重、检查点、日志、凭据、服务器连接、个人绝对路径、原始 PDF、
未获授权目标期信息或其他敏感内容。不得验证实验有效性、裁决候选存废或改写冻结合同。
