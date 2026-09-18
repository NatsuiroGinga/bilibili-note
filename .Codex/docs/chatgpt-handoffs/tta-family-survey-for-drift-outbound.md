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

完成 TTA 家族的系统性文献综述（全部给原始出处：作者/会议/年份/节号/公式号，标注核验状态）。子题一：TENT 原文（Wang et al., ICLR 2021, arXiv:2006.10726）方法节精确细节——熵损失的精确数学形式（softmax 熵还是 marginal entropy？单样本还是批平均？）、online 适应协议的精确时序（每批先预测记录再更新，还是更新后重预测本批？）、更新对象（BN affine 的确切范围——是否含统计量）、优化器与学习率、train/eval 模式处理（BN 统计更新需要 train 模式，affine 梯度是否依赖模式）、className。

子题二：LayerNorm/Transformer 上的 TTA 变体——TENT 的 BN 限制在 Transformer（LN 无 running statistics）场景的已知解法与先例（更新 LN affine、prompt/adapter 式适应、EATA/SAR 的改进），哪些论文明确做过'只更新 LN 参数的测试时适应'，各自损失与协议。

子题三：安全/恶意软件/入侵检测领域的 TTA 应用查重——有没有已发表工作把 TTA（TENT/CoTTA/SAR/EATA/ROTTA 等）用于恶意软件检测、入侵检测、DGA 检测或概念漂移安全场景？逐一给出处与结果；若无，给'最接近的'工作（如 drift 检测中的在线适应、半监督安全检测）。这决定任务化空间是否为空。

子题四：CoTTA（CVPR 2022）与 SAR（ICLR 2023）方法节精确机制——CoTTA 的随机恢复与增广平均置信、SAR 的尖锐度感知筛选与样本可靠性权重——哪些组件适合小模型（24M 参数）年度面板、哪些是 ImageNet 特化。

子题五：TTA 的已知失败模式与批评文献——熵最小化的退化/坍缩案例、熵陷阱（错误预测越推越自信）、batch 顺序敏感性、以及 EATA/RAIN/DELTA 等修正机制——给出可预注册的失败判据先例。

输出按子题组织，每条附出处；最后给'对本课题最小臂设计的修正建议清单'（哪些规格必须改、哪些是安全变体、哪些保留）。全部为外部候选，本地全文复核后才进台账。

## 脱敏实验摘要

研究背景（自包含）：DGA 域名二分类跨年漂移检测（DRIFT 基准 DSN 2026，2017-2019 训练、2020-2025 逐年评价）。官方模型：字符+子词双分支 Transformer 24.2M 参数，全部 LayerNorm 无 BatchNorm，静态融合分类头。实测病灶：源年三支路判定不一致率 35.5%/34.4%/35.0%；官方 2025 年 FPR 0.0965（较 2020 的 0.0328 恶化约 3 倍）、未见家族 FNR 0.1439、家族宏平均 TPR 0.6713（微平均 0.9397）。本课题已否决九个机制族（含基于反事实优势路由的方案——正锚点未通过，信号脆弱），现转向测试时适应（TTA）家族：计划最小臂为熵最小化只更新 LayerNorm affine 参数（注意：TENT 原文只做了 BatchNorm，LayerNorm affine 是本课题的平移变体），在线单 pass，Adam lr 1e-4。判据已冻结：适应后相对静态基线 ΔFPR 不增且（ΔFNR 改善或 ΔAP 改善）；FPR 恶化预注册为熵陷阱。已否决机制清单与用户约束（必须赢基线的机制章、成熟家族取件、GRPO 家族结构思想只作增强不作改名）同前述报告。

## 返回合同

返回 Markdown，注明 actual_model、actual_effort、actual_mode、used_apps、
结论、逐项证据、来源与精确位置、不确定性和未回答问题。
结果一律是外部候选，待本地全文和实验复核，必须由发起方独立复核。

## 禁止操作

不得修改 Git、运行代码、访问白名单外路径，也不得输出或索取原始数据、
数据集、权重、检查点、日志、凭据、服务器连接、个人绝对路径、原始 PDF、
未获授权目标期信息或其他敏感内容。不得验证实验有效性、裁决候选存废或改写冻结合同。
