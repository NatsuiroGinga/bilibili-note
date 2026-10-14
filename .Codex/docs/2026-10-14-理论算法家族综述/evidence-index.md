# 证据索引：理论／算法家族综述

> 生成 2026-10-14。所有在线查询只作**候选发现**；未取全文者标`外部候选`，不得支撑正文论断。
> 「本地全文」＝`wiki/papers/**` 有 MinerU 结构化笔记；「题录核验」＝OpenAlex/Zotero 存在性＋题录核验。

## 一、本地混合索引查询（ch3-drift-20260908 工作树，1,934 条笔记，stale=false）

原始 JSON：`raw-queries/chunk1..4-*.json`（16 个查询，hybrid 模式）。
查询式与关键命中见 `notes.md`「查询日志」节。证据等级全部`本地全文`。

## 二、OpenAlex 查询（raw-queries/openalex/）

### 第一批（家族 × 先例矩阵，48 个文件）

| 文件名 | 查询式 | 总量 | 关键结论 |
| --- | --- | --- | --- |
| dro_malware.json | distributionally robust optimization malware detection | 24,007（模糊） | 顶部无直接 DRO 恶意软件 |
| dro_android.json | "distributionally robust" android | 103 | 顶部为 OOD 评测与规避鲁棒，无 DRO 方法 |
| groupdro_malware.json | "group distributionally robust" malware | **4** | **无相关命中 ⇒ 恶意软件 GroupDRO 空白** |
| irm_malware.json | "invariant risk minimization" malware | 31 | TIF 2026（TSE）为首 |
| invariant_android.json | "invariant learning" android malware | 12 | TIF 2026 |
| conformal_malware.json | "conformal prediction" malware | 132 | DroidScribe 2016、Transcending TRANSCEND 2022 |
| conformal_android.json | "conformal prediction" android | 98 | 2017 Neurocomputing 无偏置信 |
| ttA_malware.json | "test-time adaptation" malware | 41 | MADCAT 2025 |
| cl_android.json | "continual learning" android malware | 251 | Regression-Aware 2026、ProtoMal 2026 |
| cl_malware_replay.json | continual learning replay malware concept drift | 250 | SEED 2026、MADAR 2025 |
| sam_malware.json | "sharpness-aware minimization" malware | 24 | 2024 家族分类、MalFormer 2025（待核） |
| curriculum_malware.json | "curriculum learning" malware detection | 176 | MalTutor 2025 |
| curriculum_android.json | "curriculum learning" android | 907（模糊） | MalTutor 2025 |
| longtail_malware.json | "long-tailed"/"long tail" malware family | 16,714（模糊） | MalImgDA 2025 |
| logitadj_malware | "logit adjustment" malware | 18 | 无直接命中 |
| openset_malware.json | "open set recognition" malware | 209 | OSR 2025、MDENet 2023 |
| openset_android.json | "open set" android malware family | 82 | 家族开集 2025 |
| densratio_drift.json | "density ratio" concept drift malware | 20 | 无直接命中 |
| iw_drift_malware.json | "importance weighting" concept drift malware | 19 | JVLA 2017 |
| meta_malware.json | "meta-learning" malware family | 579 | 2023/2024 多篇（领域较满） |
| fewshot_android.json | "few-shot" android malware family | 405 | FAMCF/Famd/Androfim/FARM（领域较满） |
| game_malware.json | "game theory" malware evasion adversarial | 538 | GameNP 2024 TIFS |
| ssm_malware.json | "state space model" malware detection | 290 | 无直接 SSM 方法命中 |
| mamba_malware.json | Mamba malware detection | 212 | **Mamba+PE opcode 2026** |
| rwkv_traffic.json | RWKV traffic detection | 100 | 无 Android 恶意软件命中 |
| labelshift_malware.json | "label shift" malware | 58 | IoT 2025 |
| np_malware.json | "Neyman-Pearson" classification malware | 78 | GameNP 2024 |
| ood_malware.json | "out-of-distribution detection" malware | 243 | 常规 OOD 线 |
| ssl_drift_malware.json | self-supervised contrastive malware concept drift | 1,645（模糊） | TRANSCEND 线 |
| coreset_malware.json | "coreset selection"/"data pruning" malware | 144,526（模糊） | 无效宽查询 |
| curriculum_drift.json | "curriculum learning" "concept drift" | 171 | 无 LAMDA 形态命中 |
| curriculum_imbalance.json | "curriculum learning" "long-tail" | 608（模糊） | CCL 2022 |

### 第二批（定向＋摘要）

| 文件名 | 内容 | 结论 |
| --- | --- | `---` |
| abs_TIF.json | TIF: Learning Temporal Invariance in Android Malware Detectors, IEEE TSE 2026 | **不变性学习用于 Android 时间漂移的直接先例** |
| abs_PAD.json | PAD, IEEE TDSC 2023 | **恶意软件对抗训练收敛保证先例** |
| abs_UnderstandingModelWeaknesses.json | MalTutor, PACMSE 2025 | **Android 家族不平衡课程先例** |
| abs_RegressionAware.json | Regression-Aware CL, IEEE TIFS 2026 | Android CL 安全回归先例 |
| abs_GameNP.json | Game-Theoretic NP Detection, IEEE TIFS 2024 | NP＋博弈对抗检测先例（非 Android） |
| abs_UnbiasedConf.json | Android malware detection with unbiased confidence guarantees, Neurocomputing 2017 | Android 置信保证先例 |
| ewc_malware.json | "elastic weight consolidation" malware | 90 条模糊，无直接 EWC 恶意软件 |
| regularization_cl_malware.json | EWC/LwF CL malware | On the Limitations of CL 2022 |
| genreplay_malware.json | generative replay GAN malware drift | 无直接先例 |
| costsens_malware.json | cost-sensitive malware FNR | 模糊命中为主 |
| reject_drift_malware.json | reject option/selective prediction malware drift | TRANSCEND 线 |
| evl_labeldelay.json | "extreme verification latency" malware | **JVLA 2017、COMPOSE 2015（标签延迟线）** |
| prototype_cl_malware.json | prototype CL malware | ProtoMal 2026 |
| curriculum_drift.json | curriculum + concept drift | 无 LAMDA 形态 |
| ttt_malware.json | "test-time training" malware | MADCAT 2025 |
| lossreweight_malware.json | loss reweighting Android imbalance | 2026 标签噪声×不平衡 |
| focal_malware.json | focal loss Android imbalance | Chen 2023 内含 focal |
| tabssm.json | SSM tabular | 无相关 |

### 第三批（canonical 存在性核验，raw-queries/openalex/verify/）

全部核验通过（题目/年份/引用数）：SAM/Foret、logit adjustment/Menon 2020、LDAM/Cao 2019（c=218）、
Class-Balanced/Cui 2019（c=2,868）、EWC/Kirkpatrick 2017（c=7,650）、LwF/Li 2016（c=4,009）、
DER/Buzzega 2020（c=90）、OpenMax/Bendale 2016（c=1,653）、EVM/Rudd 2018（c=327）、
GroupDRO/Sagawa 2020（c=331）、IRM/Arjovsky 2019（c=272）、Curriculum/Bengio 2009（c=4,993）、
Hacohen&Weinshall 2019（c=112）、Mamba/Gu 2023（c=1,059）、GEM/Chaudhry 2017（c=485）、
A-GEM/Chaudhry 2018（c=605）、对抗训练收敛/2019（c=52）、JVLA 2017、AUPRC 收敛/Qi 2021、
Sorscher 2022（c=118）、Shimodaira 2000（c=1,670）、SelectiveNet/Geifman 2019（c=55）、
Focal/Lin 2017（c=27,010）、NP 分类/Tong 2018（c=79）。
三个精确题名查询零命中（转录变体）：`tconformal_papadopoulos`（保形半监督）、`paucDRO`、
`ewc_sur_malware`、`transcend_jordaney`——**零命中不判不存在**（TRANSCEND 经 2022 续作引用链核验）。

## 三、Zotero 语义检索

| 查询 | 关键命中 | 等级 |
| --- | --- | --- |
| distributionally robust optimization group DRO worst-group | DORO 8Q5IWSVH、Duchi-Namkoong GE5XP59G、V-REx 8QBD4NUV | 题录 |
| test-time adaptation android malware concept drift | MADCAT 59GWHNT2、Berruz 2026 VQKRUFJV、TESSERACT F6KINRCT、Transcending 2022 X8EXBQ66 | 题录 |
| conformal prediction intrusion detection risk control | CRC 2CNV4CKE、CALIBURN VS3N78LQ、非交换 CRC ZUHQEIA7、Vovk | 题录 |
| logit adjustment long-tail | BBSE V7UEB83M、Garg UIBQVTXN、Saerens ×3、NP 分类 FRB25FEZ | 题录 |
| SAM PAC-Bayes | **AUPRC 可证收敛（Qi 2021）MHNH9QBM**、Duchi-Namkoong | 题录 |

## 四、本地已占区域证据

- `LAMDA路线总控.md`、`LAMDA第三章恢复卡.md`：阶段 A/B/C、缺口修复、双风险投影、双玩家 v1/v2、
  PCT/FPR gate、尾锚 E1、阈值诊断——九个实现的运行身份与否决理由全记录。
- `thesis/methods/第三章定案.md`：ETA-BER 冻结；BER＝CVaR-pAUC 排序损失 ⇒ pAUC-DRO 格位已被占。
- `thesis/methods/第三章-LAMDA任务与方案筛选矩阵.md`（2026-10-14）：任务轴优先级与判据修正。

## 五、证据缺口（诚实披露）

1. **sam_malware 两个命中（2024 家族分类、MalFormer 2025）是否真用 SAM**——只看了标题，
   未取全文，标`外部候选`。families.md #16 已如实标注。
2. **JVLA 2017 的机制**（是否密度比重要性加权）——只有题录，未读全文。
3. **Agarwal 2021 策略梯度收敛**——未核验存在性，families.md #25 标`待核`。
4. **CITADEL 是否 Android**——本地笔记有，但未重读确认宿主；先例表述以本地笔记标题为准。
5. OpenAlex `search=` 为相关度检索，总量数字不可解释为"该组合文献量"，
   只用于**排序观察**；"未发现"结论的稳健版是「**未发现直接先例**」，
   不排除 IEEE/DIMVA 等未被 OpenAlex 覆盖的出版源有先例。
6. LAMDA 原文 PDF 未重读（宿主事实由派发简报与本地笔记提供，未重查）。
