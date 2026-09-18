# ChatGPT 只读交接包

**状态：外部候选，待本地全文和实验复核。**

## 快照与执行配置

- repository：`NatsuiroGinga/bilibili-note`
- branch：`exp/ch3-drift-20260908`
- commit：`9fc297b98265905c95d52eaf83c820858421be2d`
- requested_model：`auto`
- requested_effort：`high`
- fallback_model：``
- selection_rationale：`方向 a 需离散 RL 对抗生成的大范围文献调研与设计空间分析；现状自包含`
- requested_mode：`deep-research`
- requested_apps：`github`
- task_type：`literature-review`
- source_scope：`白名单路径`
- sanitized_summary_included：`false`
- fulltext_required：`false`
- zotero_ingest_required：`false`
- allowed_paths：
  - `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/task_plan.md`
  - `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/h-arm-research-question-card.md`

## 任务

为毕业论文第三章（DGA 域名检测的对抗鲁棒训练）评估方法深化方向。注意：GitHub 白名单文件可能无法读取（前两轮均 404），以下现状自包含。

【现状】DRIFT 基准 DGA 二分类，官方 24M 字符+子词双分支 Transformer。病灶：CharBot 2 位替换检出缺口 36%、MaskDGA 半替换 68%。九臂源期筛选（T17 抽 6 万、T18 面板）：A 基线；B 朴素增广；D 组相对过滤（K=4 变体组、fooled 减组均值、全局跨组配额 top-64）对 B 检出大幅改善但 FPR +0.9pp；F=D+良性误报加权（误报真良性 CE×3.0）对 B 帕累托支配（FPR 0.0184<0.0197 且三面板检出全面更优）；E KL 锚定/H 对称组相对/I CVaR batch top-k 三者否决（I 因尾部梯度劫持）。理论定位（对抗审查后）：双侧尾风险 surrogate；组相对信号组内排序与原始违规量代数等价（A_i=K/(K−1)(u_i−ū)），增量仅剩跨组配额竞争+双侧构造；留一基线无偏命题仅服务可学习攻击者 policy gradient。排重（全文级）：Drichel 2024 联合 AT/CharBot/MaskDGA 直接近邻；Tramèr 2019/MaxUp 2020/MMEL 2021/BiB 2025 机制近邻均无跨组配额与双侧构造。威胁模型：Nelson 2008 FP-availability。

【问题】参照同门论文第三章（课程调度 DS+反应梯度 RGO，表面技术密度高但二阶理论实现断裂）被质疑『一个加权没有技术含量』。

【三候选方向】a（1-2 周）：可学习字符攻击策略 π_φ 替代固定扰动算子，与检测器交替训练，组相对优势升级为真 policy gradient，min-max 博弈成立；需调研离散字符序列 RL 先例（MAB-Malware RAID 2020 stateless bandit、对抗样本 RL 生成）、交替训练稳定性（两时间尺度/PPO 裁剪/熵正则）、失败模式（熵塌缩/奖励稀疏）。b（半天）：良性侧 J(θ,τ)=τ+(1/α)E[(ℓ−τ)₊] 的 τ 对偶联合更新（Rockafellar-Uryasev population CVaR 一致形式）替换已过门的 hard 加权——τ 收敛性质、与 batch top-k 差异、替换是否值得。c（1-2 天写作）：四命题包 P1 留一无偏+P2 (1−1/k) 缩放+P3 top-q 截断偏差界（Cauchy-Schwarz 已有）+P4 batch-CVaR 偏差（influence function 已有）。

【输出】1) 三方向优先级与组合建议（对标参照论文技术密度的充分性）；2) 方向 a 完整设计空间（算法选型/先例/稳定性/失败模式/最小可行实验）；3) 第 4+ 方向（能实质提升技术密度且有文献依据）；4) 每条建议标文献支撑与证据等级。

## 返回合同

返回 Markdown，注明 actual_model、actual_effort、actual_mode、used_apps、
结论、逐项证据、来源与精确位置、不确定性和未回答问题。
结果一律是外部候选，待本地全文和实验复核，必须由发起方独立复核。

## 禁止操作

不得修改 Git、运行代码、访问白名单外路径，也不得输出或索取原始数据、
数据集、权重、检查点、日志、凭据、服务器连接、个人绝对路径、原始 PDF、
未获授权目标期信息或其他敏感内容。不得验证实验有效性、裁决候选存废或改写冻结合同。
