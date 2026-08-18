# Notes: 第四章候选与文献方向

## 已核验事实（含精确路径）

### F1 约束三的代码事实（2026-08-18 本机核验）

`thesis/experiments/llm_probe/tools/ch3_cnn_backbone_2x2.py` 约第 1011 行 `val_scores`
文档串自述「LSPR23 实体不相交验证集上的**逐流预测与标签**」，返回 `(P, Y)` 为逐流 sigmoid
分数与逐流标签。故 0.9998–0.9999 的饱和是**逐流 AP** 的饱和。实体级折外 AP 从未测量。

### F2 约束二的代码事实

`tools/ch3_xgb_cpa_elp_entity_oof.py` 第 33-36 行：树骨干 p 不可学，改为
「在源年 LSPR23 上按实体分组做折外预测，再在折外分数上网格搜索 p」，选择准则是
折外实体平均精确率（pooled OOF）；第 279-280 行冻结协议要求三折实体折外。
即**源年实体分组折外选择已是本课题既有模式**，但只用于 XGBoost 线，未用于神经模型。

### F3 本地制品盘点

- `runs/diagnostics/dijk-repro/cache/`（本机）：仅 `d24.npy`(495MB)、`s24.npy`(494MB)、
  `y24.npy`(80MB)、`ent24_local.npy`(80MB)。**LSPR23 侧缓存不在本机**，17 个 npy 全量在 B76。
- `runs/diagnostics/ch3-2x2-fairsel/`（本机）：`scores_C11.npy`、`seen_C11.npy`、
  `ch3_2x2_fairsel_results.json`、`selection_frozen.json`、`xgb_matched_p.json`。
- `runs/diagnostics/ch4-drift-v2/`（本机）：`ch4_drift_v2.json`（阈值漂移 9.60×、DR 0.5505/0.6157）。
- `runs/diagnostics/ch4-entity-length-bucket-diagnostic-seed42-v1/`：分桶增量
  `+0.123948/+0.239138/+0.137851/-0.322915/-0.302212`，无逐样本分数。
- 冻结权重 `runs/diagnostics/ch3-final-weights/`（C00/C01/C10/C11 + inference.py）。
- HF 私仓 `Heehobino/lspr23-24-causal-prefix-lp-pooling-ch3`（20 个检查点）。

### F4 关键规模事实（取自路线总控）

LSPR23：16,353,511 流 / 150,680 实体 / **239 恶意实体**。
LSPR24：20,227,356 流 / 47,115 实体 / 752 正实体 / 实体先验 1.60%。
10% 实体留出的期望正例 ≈ 24，实测 20（P1 死因）；GroupKFold 折外可让 239 全部被打分。

### F5 第三章正文口径（影响裁决措辞）

第三章正文**不含**「源年信号饱和所以选不出基座」论证；3.6.1 只写「检查点由源年度自身的
留出部分选出」。三条约束的重估**不触及第三章正文任何一字**。

## 本机诊断（Phase 3，2026-08-18，全部零 GPU、只读闸门内已产出分数，screening_only）

脚本：scratchpad `ch4_bucket_p_headroom.py` + 一段内联结构统计；输入
`runs/diagnostics/dijk-repro/cache/{ent24_local,y24}.npy` 与
`runs/diagnostics/ch3-2x2-fairsel/{scores_C11,seen_C11}.npy`；聚合公式逐字对齐
`tools/ch3_backbone_protocolA_v2.py` ent_ap。

### D1 复现精确

`e_lp=0.518350415398`、`e_max=0.291738609767`，与冻结 JSON 差均 0.00e+00；
自检 47,115 实体 / 752 正实体 / 逐流正例率 0.0257073138。

### D2 C11 五桶剖面（全局 p=1.0562171936035156）

| 桶 | 实体数 | 正实体 | 桶内 AP(全局p) | 桶内 AP(max) |
| --- | ---: | ---: | ---: | ---: |
| 1-2 | 26,770 | 103 | 0.461514 | 0.457309 |
| 3-10 | 10,894 | 206 | 0.506753 | 0.494090 |
| 11-100 | 4,993 | 319 | 0.763781 | 0.703186 |
| 101-1000 | 3,316 | 84 | 0.268140 | 0.199972 |
| 1001+ | 1,142 | 40 | 0.204067 | 0.057794 |

与判读文档（0.7638 / 0.2681 / 0.2041）逐位一致。

### D3 逐桶 oracle p 扫描（14 档网格含 max，用 LSPR24 标签作弊式选桶内最优）

余量：1-2 桶 +0.10（p=2）、3-10 桶 +4.93（p=0.25）、11-100 桶 +2.94（p=0.25）、
**101-1000 桶 +0.44（p=1.5）、1001+ 桶 +2.63（p=0.25）**。
桶最优 p 无单调结构（2 / 0.25 / 0.25 / 1.5 / 0.25）。
桶最优 p 拼装的总体实体 AP = 0.507065，**比全局 p 基线低 1.13 点**（跨桶分数可比性被破坏）。

**裁读**：长桶 C11−C00 损失为 −32.3 / −30.2 点，而决策层指数即使 oracle 也只能拿回
+0.44 / +2.63 点 → **长实体受损的主体不在聚合指数，在逐流分数本身**。
「规模条件化 p(n)」单独作为第四章主机制的余量上限被本实验压死。

### D4 长桶证据结构（正/负实体的桶内分数）

| 桶 | 正实体 k/n 中位 | 正实体最大分中位 | 负实体最大分中位 | 负实体最大分 90 分位 |
| --- | ---: | ---: | ---: | ---: |
| 1-2 | 1.0000 | 0.065907 | 0.000000 | 0.000020 |
| 3-10 | 1.0000 | 0.033262 | 0.000000 | 0.000167 |
| 11-100 | 1.0000 | 0.217991 | 0.000000 | 0.000287 |
| 101-1000 | 1.0000 | 0.037968 | 0.000021 | 0.013674 |
| 1001+ | 1.0000 | 0.132143 | 0.000821 | **0.999917** |

两个事实：（a）各桶正实体的恶意流占比中位都是 1.0——「良性流摊薄恶意证据」不是中位情形；
（b）**大型良性实体在 C11 下出现近 1.0 的逐流假阳尖峰**（1001+ 桶负实体最大分 90 分位 0.9999），
而长桶正实体的最大分中位只有 0.038 / 0.132。C00 在长桶的 AP 反推为 0.591 / 0.506，
即无机制骨干对大实体的逐流区分本来更好——机制在大实体上主动制造了假阳。
候选乙的机制假设由此聚焦：前缀均值上下文把「重复、同质的历史」当成恶意线索
（C2 心跳的特征恰是重复性），大型良性实体正是重复同质流量。**该归因是待验证假设**，
证实需 C00/C10/C01 逐流分数（新增 LSPR24 评价，须授权并登记评价次数台账）。

### D5 ch4-drift-v2 制品复核（既有数字，非本轮新实验）

阈值比 9.60×；DR 冻结迁移 0.5505 / 目标年 oracle 0.6157 / 源留出 0.9787；
BBSE 最佳工作点（源 FPR=0.05）π̂=0.0467、对前缀真值相对误差 4.54%，但 9 个工作点 6 个 π̂<0；
无标签分位数校准 path3_usable=false（FPR 0.0614 超预算）；幸存者仅 BBSE。
该运行自训模型 p=0.7800（与第三章冻结 1.0562 无关，勿混用）。

## 文献线索（Phase 5，literature-reviewer 代理盘点，只读本地，未联网）

五主题覆盖度：T1 标签移位**部分**（BBSE/JCPOT/温度缩放/保形风险控制有原件有笔记；
RLLS `methodology/2019-Azizzadenesheli-RLLS.pdf`、MLLS `2020-Alexandari-MLLS-Calibration.pdf`、
Garg 统一视角两版**有原件无笔记**；Saerens EM **原件缺**；保序回归独立校准论文缺）；
T2 TTA/漂移 NIDS **充分**（OWAD/RTTAD/CANDI/SoTTA/NetGuard/TESSERACT/XeNIDS 等原件笔记齐备；
空白：「零目标标签＋加密流量＋实体级决策层适应」无精确先例，NetGuard 用了 0.1%–1% 目标标签）；
T3 MIL 聚合**充分**（Ilse 注意力 MIL、Gulcehre 可学 Lp、**MIDAM 大包随机池化直接讨论袋规模偏差**、
**Li 2024 Size-Invariance ICML**、AP-GeM/SmoothAP 耦合优化，均有笔记）；
T4 实体聚合**部分**（DISCLOSURE/Beehive/Gehri/BAYWATCH/Zhang 2023 聚合信标/告警预算 Hopper、
Alahmadi 99% FP 齐备；「实体规模重尾分布」作为统计现象缺专门文献——可自行实测刻画替代）；
T5 早期判定**部分**（ECHO 多出口早停、FIRMBOUND 最优停止、SelectiveNet、NP 分类有笔记；
缺 Wald SPRT 与 ECTS/EARLIEST/CALIMERA 类早期时间序列分类，且现有先例均非实体级粒度）。

锚点原件路径已核验存在：
`raw/papers/datasets/locked-shields-related/2023-Gehri-Towards-Generalizing-ML-C2-Detection-CyCon.pdf`、
`raw/papers/methodology/ranking/2023-Yao-GeM-SmoothAP-IET.pdf`、
`wiki/papers/methodology/multiple-instance/2000-Lee-Stolfo-入侵检测特征构造框架.md`、
`wiki/papers/datasets/LSPR24/Dijk-2026-LSPR23到LSPR25序列构造跨年评估.md`。

## 技能调用台账

- expression-skill：已加载（2026-08-18），用于全程沟通结构。
- planning-with-files：已加载，本目录即其产物。
- research-ideation / brainstorming：待调用（Phase 4）。
- literature-reviewer 代理：待派发（Phase 5）。
- citation-verification：待调用（Phase 5）。
