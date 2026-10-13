# 跨年方法挖掘笔记（2026-10-13）

## 一、DRIFT 原件病灶核验（PDF 逐页已读，物理页 = 1..14）

以下全部出自原件 `raw/papers/datasets/2026-Lee-DRIFT-DGA-Temporal-Drift.pdf`，物理页号即下方标注（正式印刷页 = 物理页 + 785）。

### A. 良性侧漂移驱动 FPR 上界（作者自认）
- 物理页 12（正式 p.797）：表 VII，DRIFT 逐年 FPR 0.032849(2020)→0.096520(2025)，约为 2.94 倍；2025 年 MIT 0.071038、NYU 0.073718、HMT 0.072185 均低于 DRIFT。
- 物理页 12 正文（原文引）：`benign concept drift remains a significant challenge. Like all evaluated methods, DRIFT experiences a non-negligible increase in FPR during 2024–2025. Reducing this benign FPR drift while preserving the low FNR remains an important direction for future work — for instance, via calibrated uncertainty, adaptive thresholding, or lightweight online adaptation that limits labeling cost.`
- 物理页 11 §IV.3（原文引）：`DRIFT is not immune—FPR rises from ∼3% (2020) to ~9.6% (2025)—though still below most baselines. Temporal drift on benign traffic remains an open challenge.`
- 物理页 4 图 1：良性-DGA 潜空间质心距离 d1=86.5 > d2=79.2 > d3=76.8，两分布收敛，同时推高 FN 与 FP。
- 物理页 2 §II.1.3：良性榜每年约 33.13% 条目被替换；`a static model trained on a single snapshot of benign data may fail to generalize as the underlying distribution of popular domains evolves over time.`

### B. 未见家族 FNR 仍 14.39%
- 物理页 11 §IV.3（原文引）：`the DGA training set contains 65 DGA families, while 83 families appear only in the test set.`（注意：本句实际在物理页 8 §IV.1 与物理页 11 两处出现，正文核验以物理页 8 §IV.1「1) Dataset」段与物理页 11 §IV.3「Performance Against Future Unseen DGAs」段为准）
- 物理页 12 表 VIII：未见家族微平均 FNR = DRIFT 0.143913（MIT 0.279048 / NYU 0.255106 / HMT 0.259630）。

### C. 跨年实体（有效二级域）互斥未做
- 物理页 8 §IV.1「1) Dataset」：仅说明每年留 300,000 样本作验证（150k 良性+150k DGA），`we test on data from later years (2020–2025), i.e., on domains that are strictly newer than the training period`——以「年份严格更晚」定义，无同域实体排除条款；表 I（物理页 3）统计为 2017 起累计。
- 全文未出现任何「相同有效二级域在训练年与测试年间互斥」的表述（物理页 1–12 逐页核）。

### D. 融合为简单拼接，长尾家族负迁移（作者自认）
- 物理页 8 §IV.1「2) Feature Fusion and Classification」式 (7) v_fusion=[v_subword; v_char]，原文引：`Although more expressive fusion mechanisms (e.g., gating or cross-attention) may further improve performance, we adopt simple concatenation in this work and leave the exploration of richer fusion strategies as future work (see also per-family analysis in §IV.2.3).`
- 物理页 10 图 5：双分支宏平均 TPR 0.6713 vs 微平均 0.9397；69/147 家族上不是最佳变体。
- 物理页 10 表 V：15/147 家族上双分支同时差于两个单分支，给出真实域名例：bumblebee（cmidis1zeuu）、prometei（xinchaogedjdf/xinchashichep2/rwwm35snq1o2qe）、urzone（rvjerjato9h.ji）；另一组 69/147 中 darkwatchman（de13n67l、51e8ece1、766bbz8.com）、ifly（7o5m.ifly、d6eeht49）、nyaim2（runime-incorect、remictes-nude）。
- 物理页 10 §IV.3 文字：`natively combining them causes the hybrid to regress, suggesting that more sophisticated fusion is needed to avoid catastrophic forgetting across branches`（prometei 涉及中文语言家族训练欠代表）。

### E. 三任务等权求和，组合是 FNR 偏置选择而非 F1/FPR 最优
- 物理页 6 式 (1)：L_total = L_MTP + L_TPP + L_TOV，原文 `The total loss is defined as the sum of the three task-specific losses`，无任务权重。
- 物理页 9 §IV.2.2（原文引）：`Case 5 (MTP+TOV) achieves the lowest FPR across all years, while Case 7 (Base) retains the lowest FNR... we adopt the full joint objective because it yields the highest Accuracy (0.9528) and Recall (0.9481)`；表 III：Case 5 F1=0.9660 > Base 0.9646；表 IV：Case 5 各年 FPR 全面更低（2025：0.0855 vs 0.0965）。

### F. 统计不确定性缺失
- 物理页 1–12 全文无随机种子、重复训练、方差或置信区间；表 VI（物理页 10）DRIFT 对最强外部基线 M-ResNet+B-cos 的 F1 差 0.002907。

### G. 在线适应协议需标签、只调分类头
- 物理页 11 §IV.4：CL 协议 `the model from the previous step (N−1) is updated for a single epoch using only data from Y_train = N`（用该年标签）；原文承认成本：`the continuous acquisition of up-to-date labels`。
- 原文解释：`the invariant features learned through the pre-training already encode most of the cues needed to track emerging DGAs, so adaptation can be concentrated at the decision boundary`——适应只在决策边界，表示不动。

### H. 「不变」无不变性约束机制
- 物理页 6–7 §III.2：三项自监督均为结构/位置任务（MTP 式 3、TPP 式 4、TOV 式 5），没有任何按年份/域对齐的显式不变性损失（无对抗、无 IRM、无跨域对比对）；R2（物理页 5）只以「学到不变特征」为目标，不提供保证。原文自认（物理页 12 之前、摘要层面）：`invariant` 是设计意图非定理保证（wiki 笔记 L182 同）。

### I. 阈值与校准完全缺席
- 物理页 12 未来工作句（同 A）点名 calibrated uncertainty / adaptive thresholding 为未做方向；表 VI–VIII 全部为默认阈值下的单点指标，无 ROC/PR、无 FPR@阈值标定。

## 二、检索记录

（后台混合检索运行中，结果落 `/tmp/kuaonian-search/hybrid-results.txt`）

- 本地索引状态：built_at 2026-10-13T10:32Z，note_count 1921，chunk_count 154263，stale 未报异常。
