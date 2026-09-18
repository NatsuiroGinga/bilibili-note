# L29 下一批设计裁决：warm-start 受限修复（主进程冻结，2026-09-09）

**用户裁决记录**：用户已裁定"直接排进下一批"（warm-start restricted 臂），细节由主进程把握。本文件是该批次的冻结设计依据，供实现简报引用；正式并入方案文档由文档代理在 v3 终态分析后执行。

## 背景实测（v3 运行中事实，2026-09-09）

`ch3-lamda-restricted-repair-screening-mps-seed42-v1` 前三臂已回收的逐年读数：

- ER 与 gap 两臂 2013/2014 逐位一致（该两年修复候选为 0，机制臂未触发，退化 ER——预期内）；
- **restricted_repair（head-only 冷启动）结构性失败**：2013 loss 十轮 0.693→0.6928（未收敛）、2014 loss 卡死 0.6885（同期全参数臂 0.6897→0.1134）、2014 AP 0.7011、FNR=1.0 全判良性、backward FPR=0.000。冻结一个从未收敛的冷启动骨干，头无法拉出线性可分性。

## 冻结设计（warm-start 修正案）

**机制定义**：restricted 臂的骨干不再从零训练，而是**初始化自同流 ER 臂对应年末的骨干权重快照**，年度更新中骨干冻结、仅头分类器接收梯度。

- 骨干来源：`ch3-lamda-restricted-repair-screening-mps-seed42-v1/checkpoints/experience_replay/year-{Y}/year-complete.pt`（同工具同流同预算，实现上唯一新增的是加载其 `state_dict()["model"]` 的 backbone 部分）。
- 加载时点：每年年初（含 2013 首年）从对应 ER 年末快照初始化骨干；头仍从头初始化。
- 因果合法性：ER 快照只用已到达年份训练所得，无未来信息；同流身份在 run-manifest 登记 backbone_source_run 与其 SHA-256。

**臂矩阵（v3b，运行身份 `ch3-lamda-restricted-repair-warmstart-screening-mps-seed42-v1`）**：

1. `experience_replay`——同流 ER 锚（复用 v3 读数也可，但同身份重跑更干净；选**复用 v3**：同工具同配置逐位一致已证，省 2.5 分钟，裁决用 v3 的 ER 臂读数，登记引用）
2. `gap_repair`——全参数修复对照（同上，复用 v3）
3. `restricted_repair_warmstart`——warm-start head-only 修复
4. `restricted_repair_warmstart_curriculum`——warm-start head-only＋浅缺口优先暴露（CUR 定义不变：epoch e 暴露 d ≤ 当年 e/10 分位）

**单一因子链保持干净**：3 vs 2 差"参数作用范围"（共享同一骨干来源）；4 vs 3 差"暴露调度"；2 vs 1 差"修复项"。v3 冷启动事实作为边界条目入文档（head-only 的部署前提是已有可用骨干），不进判据。

**判据**（不变，对 v3 ER 同流锚）：§7 主判据——ΔFPR≤0、旧恶意负向翻转不增、FNR 改善或修复率提高、ΔAP≥−0.002。归因上限措辞按 L28 审查收窄：CUR 臂结论只写"head-only＋课程化暴露整体配置效应"。

**预算**：与 v3 完全一致（种子 42、10 轮、批 1024、SGD、阈值 0.5、容量 200、年份 2013→2018）；warm-start 加载不增加训练预算。预计墙钟 ~10 分钟（两臂×5 年）。

**验收附加项**：逐年核对 warm-start 臂 backbone 权重与 ER 快照逐位一致（加载正确性）；`exposed_repair_candidates` 曲线核对 CUR 的 e/10 分位合同。

## 风险与边界

- warm-start 后 head-only 若仍不过门，"受限参数修复"路线到此为止（连续两个合理形态失败），届时按 §7 第二停止线上呈表述层决策；
- warm-start 使 restricted 臂与 ER 臂共享骨干谱系，比较语义为"在同一表示上的更新策略"，正文表述不得写成独立架构；
- 单种子、screening_only、发布视图未来协变量披露不变。
