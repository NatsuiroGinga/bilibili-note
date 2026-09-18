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
- task_type：`mechanism-counterexample`
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

基于上述实测与裁决，完成两项设计任务（外部候选，本地保留裁决权，未来年份 T20-T25 不进入任何设计）：任务一【对抗自查】：审查 route 族否决裁决的证据链是否存在漏洞——特别检查：(a) 单 cell 效用贴 0 导致的符号脆弱性，是否可能通过更好的 cell 设计（更细/更粗分箱、连续效用代替 lookup）获得稳定信号；(b) 支路 10.7:1 不对称是否意味着正确的问题不是'选哪支'而是'何时整体弃用 subword 支'（单侧弃用比对称路由更容易学？）；(c) 有没有你的 CARS 设计中被正锚点设计遗漏的可行变体。若你认为否决过严，给出具体的、可零训练或低保真验证的翻案实验；若不反对，明确说'否决成立'。任务二【TTA 任务化设计】（主任务）：为 DRIFT 设计测试时适应（TENT/CoTTA/SAR 家族）的任务化最小臂。要求：(1) 家族机制对照——TENT（熵最小化只更新归一化层参数）、CoTTA（持续适应+随机恢复）、SAR（尖锐度感知可靠适应）三者机制差异与在 DRIFT 年度面板上的适配性逐条分析，附原始出处（作者/会议/年份/节号）；(2) 最小臂设计——第一个证伪实验的完整规格：适应什么参数（只 BN 统计/BN 参数/更多？）、什么损失（熵/多样性权重？）、什么数据（当年 test 无标签流的全部还是分块？）、评价协议（适应后逐年指标 vs 静态 C00，分表不混）、预算与停止条件；(3) 协议四项建议——到达顺序、无标签接口合法性边界（TTA 用当年 test 无标签分布是否须披露为目标知情/单列适应协议）、更新对象、静态与适应分表；(4) 与本课题已否决机制的边界——TTA 是否会重蹈 M1-v2 的约束梯度冲突或 N12 的双侧取舍，给出预判与可证伪检验；(5) 通过/失败门——相对静态 C00：未来年 FPR 不增、FNR 或未见家族 FNR 改善、源年不塌；失败形态预注册（如适应后 FPR 恶化的'熵陷阱'）。(6) 若 TTA 最小臂通过，第二组件从哪个家族取（与你上一轮报告的八臂消融衔接）。全部输出附文献出处，成熟方法不得改名；输出为外部候选，本地复核后进台账。

## 脱敏实验摘要

接续你上一轮 DRIFT 第三章机制构思深度研究（主推 CARS 反事实优势路由与保护，含两问式正锚点核查设计）。现在回报核查实测结果，请求下一阶段设计。实测（全量 30 万域/年，DRIFT 官方模型三冻结动作 C00 静态融合/char 反事实支/subword 反事实支，T17 拟合 T18 验证）：一、CARS 两问式正锚点判定【未通过】。问二 override 零梯度 lookup：主探针前向流 net=-207（coverage 2885/rescued 1339/induced 1546），同数据经特征缓存重算的对照实现 net=+713（coverage 4089/rescued 2401/induced 1688）——对齐诊断证明两实现代码逐位等价，符号翻转全部来自 MPS 前向位级非确定性；根因是 lookup 正效用集中在 10 个候选 cell 的 1 个且效用贴 0，前向噪声即可翻转裁决。二、问一 which-branch：lookup 表跨年 balanced accuracy 0.9598，但置信度启发式负锚对照 0.9555——仅高 0.43pp，伪成功形态被负锚识别。三、K4 联合表示键（cos/逐元素/L2 差异分箱）与低阶键读数逐位相同，无增量信息。四、支路实力 10.7:1 完全不对称（char 独对 97546 vs subword 独对 9135；挽回 6310 vs 37）——which-branch 退化为单侧问题。裁决：route/selection 族正锚点不通过（信号脆弱无结构），CARS 不立项，N14 撤销。本课题已否决机制全景：M1-v1 静态错误再优化、M1-v2 原始-对偶约束（梯度余弦-1）、M2/J06、硬最大近邻、R02 DeepEmbed/R07 Engram 条件记忆、固定更新专家混合、N12 家族课程（G2 折0充分性早停）、CARS 路由族（本次）。用户已明确裁决：不接受'病灶刻画型'章节形态，第三章必须是赢基线的机制章；已确立方法论纠偏——机制否决后下一候选必须优先从成熟方法家族取件做最小证伪实验，只有家族清单耗尽才自研；排序以'离已验证有效干预的距离'为第一键。

## 返回合同

返回 Markdown，注明 actual_model、actual_effort、actual_mode、used_apps、
结论、逐项证据、来源与精确位置、不确定性和未回答问题。
结果一律是外部候选，待本地全文和实验复核，必须由发起方独立复核。

## 禁止操作

不得修改 Git、运行代码、访问白名单外路径，也不得输出或索取原始数据、
数据集、权重、检查点、日志、凭据、服务器连接、个人绝对路径、原始 PDF、
未获授权目标期信息或其他敏感内容。不得验证实验有效性、裁决候选存废或改写冻结合同。
