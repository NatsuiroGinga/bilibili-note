---
schema: paper-note-search/v1
title: "LAMDA: A Longitudinal Android Malware Benchmark for Concept Drift Analysis"
title_zh: "LAMDA：Android恶意软件长期概念漂移基准"
authors: [Md Ahsanul Haque, Ismail Hossain, Md Mahmuduzzaman Kamol, Md Jahangir Alam, Suresh Kumar Amalapuram, Sajedul Talukder, Mohammad Saidur Rahman]
year: 2026
date: 2026-09-08
journal: "The Fourteenth International Conference on Learning Representations（ICLR 2026）"
doi: null
arxiv_id: "2505.18551"
fulltext_verified: true
source_pdf: "[[raw/papers/datasets/2026-Haque-LAMDA-Android-Malware-Concept-Drift.pdf]]"
tags:
  - Android恶意软件
  - 概念漂移
  - 时间泛化
  - 数据集
  - 持续学习
  - 类型/论文
tasks: [Android恶意软件二分类, 家族分类, 时间泛化, 持续学习]
datasets: [LAMDA, API Graph]
methods: [Drebin式静态特征, AnoShift时间切分, VarianceThreshold, SHAP, CADE]
metrics: [F1, ROC-AUC, PR-AUC, FPR, FNR]
key_finding:
  - "LAMDA 发布 2013–2025（缺 2015）共 1,008,381 个 Android APK 的静态 Drebin 式特征；原论文表 7 中 LightGBM 的 F1 从 IID 97.49% 降到 FAR 47.24%。"
  - "固定代码在全部年份训练子集上共同构建词表并拟合方差筛选，严格前向复现实验必须先重建仅源期预处理。"
supports: [LAMDA原发布协议存在显著时间退化, 静态特征和标签均随年份变化, LAMDA可用于持续学习基准]
cannot_support: [本课题新算法有效, 原表7是无未来协变量泄漏的强基线, RWKV对静态词袋具有结构必要性]
method: "AndroZoo 采样、VirusTotal 弱标签、AVClass2 家族标签、Drebin 式静态二值特征、AnoShift 时间切分、特征稳定性与持续学习评估"
baseline: "Linear SVM、LightGBM、MLP、XGBoost、CADE；持续学习的 Naive、Joint、Experience Replay"
aliases:
  - LAMDA
  - Haque2026-LAMDA
related:
  - "[[2023-Chen-Android恶意软件持续学习]]"
  - "[[2025-Haque-CITADEL半监督主动漂移适应]]"
  - "[[2026-Kamol-McNdroid多模态长期漂移基准]]"
  - "[[2019-Pendlebury-TESSERACT时空实验偏置与AUT]]"
  - "[[2026-Haque-LAMDA-ICLR2026官方演示版]]"
---

# LAMDA：Android 恶意软件长期概念漂移基准

> 页码锚点：论文标题位于 PDF 物理第 1 页；MinerU 未成功生成逐页文本，数字按原论文表 7、表 14、表 15–16 和附录节号核验。

## 证据与版本

- 原件：arXiv `2505.18551v1`，提交于 2025-05-24；本地 PDF SHA-256 为 `26df883d075156abfe69d4def70e2b27614f63a53ba08dc82d0a284f3f3ed129`。
- 发表：OpenReview 论坛 `1FnCrZtBNQ` 标为 ICLR 2026 会议论文；作者仓库引用信息一致。
- 版本差异：arXiv v1 把 Suresh Kumar Amalapuram 的单位写为 University of Edinburgh，OpenReview 会议版抬头写为 Indian Institute of Technology Hyderabad；项目页/HF 卡片还使用过 “Dataset for Analyzing/Drift Analysis” 的标题变体。正式引用以 OpenReview 的 “Benchmark for Concept Drift Analysis” 为准。
- 数据：Hugging Face `IQSeC-Lab/LAMDA`，DOI `10.57967/hf/5563`，2026-09-08 核验修订 `ad9614bdd5556767f97ced2fce797c2f06408ebf`，数据卡标注 MIT。
- 代码：`IQSeC-Lab/LAMDA`，2026-09-08 核验 HEAD `7728bfafcd5539a286b5f8c47b6f1e3b2d1f4249`。根目录没有 `LICENSE`，所以数据的 MIT 标注不能自动当作代码许可。
- Zotero：条目键 `6THQM632`；本地连接器已导入题录，未自动附加 PDF。
- 全文获取：arXiv v1 PDF 已入库；OpenReview 会议版 PDF/API 直连均返回 403，尚未保存本地终稿。MinerU 标准提取两次提前退出且未产出，本文数字由 arXiv 官方 HTML 全文与原论文表号复核。会议版差异和页码仍是待核项，不伪报终稿已本地入库。
- ICLR 2026 官方演示版：`raw/papers/10011850_e9IemFB.pdf`，SHA-256 `37c1a03cc1ab3d01459695eb6855d109e10fbebe01c6824735fb0405a71f61dd`；17 页演示文稿，已建立 [[2026-Haque-LAMDA-ICLR2026官方演示版]] 笔记。该制品补充会议展示证据，不替代论文全文。

## 数据构建

- 时间范围：2013–2025，缺 2015，共 12 个年份。
- 总量：1,008,381；恶意 369,906，良性 638,475；1,380 个恶意家族、150,604 个单例、2,985 个未知家族（摘要、附录 A 表 3–4）。
- 标签：`vt_detection=0` 为良性，`vt_detection>=4` 为恶意，1–3 丢弃；家族由 AVClass2 规范化（第 3 节、附录 L.2）。
- 表示：从清单和 smali 提取权限、组件、硬件、意图过滤器、受限/可疑 API、URL/IP，编码为二值词袋（附录 B 表 5）。
- 三种变体：方差阈值 `0.001/0.0001/0.01` 分别保留 `4,561/25,460/925` 个二值特征；论文表 6 同时把严格阈值一项正文写作 915、表中写作 925，存在内部不一致。
- 年内划分：每年按标签分层随机分成 80% 训练和 20% 测试。该划分不是跨年训练合同，只是发布文件的年内分片。
- 公开格式：Parquet 与稀疏 NPZ，元数据为 `hash`、`label`、`family`、`vt_count`、`year_month` 加二值特征。
- 指标实现：监督脚本用 `average_precision_score` 生成论文的 “PR-AUC” 列；严格表述应注明它实际是平均精度（AP），不是梯形积分 PR-AUC。

## 官方时间协议

- TRAIN+IID：2013–2014；除两年最后一个月外用于训练，最后一个月用于 IID 测试。固定脚本把具体 IID 月写为 `2013-12` 与 `2014-08`。
- NEAR：2016–2017，仅测试。
- FAR：2018–2025，仅测试。
- 原论文称 5 个随机种子，每个大区间的均值和标准差同时跨种子与年份汇总。因此表中很大的标准差主要混合了年份异质性与训练随机性，不能当作纯种子方差。

## 主要实验

### 表 7：Baseline，VarianceThreshold=0.001

| 划分 | 模型 | F1 | ROC-AUC | PR-AUC | FPR | FNR |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| IID | LightGBM | 97.49±0.17 | 99.55±0.03 | 99.50±0.11 | 2.69±0.48 | 1.74±0.34 |
| FAR | LightGBM | 47.24±27.33 | 78.04±20.83 | 63.45±35.80 | 1.30±0.95 | 64.10±22.97 |
| FAR | MLP | 47.59±25.30 | 84.04±11.23 | 66.16±34.34 | 1.14±0.71 | 64.40±20.63 |
| FAR | SVM | 41.86±22.55 | 79.07±15.06 | 62.27±34.09 | 1.27±0.76 | 69.93±16.85 |
| FAR | XGBoost | 42.75±25.86 | 76.85±16.49 | 60.33±35.88 | 1.69±0.57 | 68.11±20.43 |

这些数字证明原发布表示下存在显著时间退化和充足非饱和空间，但不能直接证明某个新训练机制有效。

### 其他关键结果

- CADE：在 API Graph 上 F1/FNR/FPR 为 `0.8904/0.1191/0.0101`，在 LAMDA 上为 `0.4407/0.4734/0.1729`（附录 H 表 14）。
- 特征阈值：更严格的 `0.01` 有时降低漏报，却明显抬高误报并降低精度；不是单调改进（附录 C.3）。
- 标签漂移：附录 F 表 13 显示旧恶意标签的当前判定确有变化，2017 年有 5.19% 原恶意样本当前被标为良性；这说明弱标签具有时间版本，而不是永久真值。
- 持续学习：Domain-IL 和 Class-IL 中 Joint 通常在后期优于 Naive/Replay；例如 2025 Domain-IL 的平均 F1 为 `88.52±0.46`，而 Naive 为 `72.71±0.83`（附录 J 表 15）。这说明原论文的 200 样本/经历回放并非强上界。

## 关键有效性风险

### 未来协变量预处理泄漏

固定提交的 `vectorization_npz_creation.py` 先把 2013–2025 **所有年份训练分片**合并为 `all_X_tr`，再从中构建全局词表并拟合 `VarianceThreshold`；随后 `anoshift_experiment_models_separate.py` 才只用 2013–2014 月份训练分类器。因而 NEAR/FAR 的训练分片虽未把标签送进分类器，却参与了特征可见性和保留决策。这是严格前向评估中的未来协变量泄漏。

可复现的修复合同是：只用源期训练月份构建词表、拟合方差筛选与任何标准化器，然后冻结并转换 IID/NEAR/FAR。发布表 7 只能作为原协议读数，不能作为修复后强基线。

### 阈值与路径不一致

- 论文把 baseline 定义为 `0.001`、4,561 维。
- 固定代码 `vectorization_npz_creation.py` 的目录名含 `0.001`，实际 `VarianceThreshold(threshold=0.0001)`。
- 主 AnoShift 脚本把 `VT=0.0001`，读取对应目录。

因此论文表 7、公开 `Baseline` 文件和固定脚本之间缺少可机械验证的同一运行身份。复现前必须以特征数、选择器对象哈希、目录和脚本提交共同冻结版本。

### 其他边界

- 论文没有明确给出跨发布分片的 SHA-256 去重审计；有 `hash` 字段不等于已经证明训练/测试无重复。
- 附录 G 声称发布阈值前原始矩阵和序列化 `VarianceThreshold` 对象，但固定 HF 修订的公开清单未定位原始逐样本矩阵或 `selector.joblib`。只凭已经全时期筛选的 4,561/25,460 维文件不能完整重建严格源期特征空间。
- Class-IL 先按“测试集中家族样本数大于 10”选择 154 个家族（附录 J.2），让测试标签和支持度参与任务定义；表 16 不能作为完全隔离的最终测试结果。
- 持续学习启动器循环三次，却没有向 Python 脚本传递 run seed；脚本只固定回放 NumPy RNG 为 42，也没有记录 PyTorch 初始化种子。三次运行不能称为可复现的预注册三种子实验。
- 标签噪声附录混用两种干预：表 11 是累计阈值 `vt_count>=k` 的样本数，表 12 正文却构造 `vt_count=k` 的精确检出数子集；“阈值变化影响小”的结论不能把两表当成同一实验。
- 第 4.1 节正文把 LightGBM IID FNR 写成 1.47%，表 1/表 7 为 1.74%；引用应以表格为准并保留差异。
- 2024 仅 794 个恶意样本，2025 仅 23 个；FAR 的巨大年际差异部分来自恶意样本枯竭和类先验变化。
- 数据使用静态词袋，不含运行时行为和自然顺序；作者也把缺少动态行为列为限制。
- 论文生成与实验使用 1 TB 内存和 4×H100，但这混合了 APK 处理与下游训练成本。4,561 维稀疏基线本身可望在单卡上实验，固定代码却把稀疏矩阵 `.toarray()` 且硬编码 `cuda:2`，所以“单卡可实验”目前是工程可行性判断，不是原仓库开箱即用事实。

## 对本课题的可迁移结论

- **最优先任务化方向**：来源年份专属预处理 + 严格前向强基线；其次比较静态域泛化、标签噪声/类先验稳健、主动/持续学习。
- **RWKV 仅作软适配且当前较低**：发布输入是一 APK 一行的静态二值词袋；按年份排序样本不会产生合法的样本内因果序列。只有取得部署实体或应用版本链、原始动态调用序列，且顺序打乱显著伤害基线时，才有状态递归资格。
- 任何新算法均为“实验待证”。原论文只证明数据病灶与基准余量，不证明本课题方法有效。

## 论文可以支持

- LAMDA 原发布协议下存在显著且未饱和的长期时间退化。
- 静态特征、家族组成、类先验和 VirusTotal 标签均会随时间变化。

## 论文不能支持

- 不能支持 RWKV、mHC、课程、强化学习或博弈方法在 LAMDA 上有效。
- 不能把原表 7 当作已消除未来协变量预处理的强基线。

## 实验结果与负证据

- FAR F1 降至 41.86%–47.59%，FNR 升至 64.10%–69.93；同时后期恶意样本极少，代码存在全时期预处理与阈值路径冲突，Class-IL 还按测试家族支持度筛选类别。

## 与本课题的关系

- 先完成源期专属预处理和哈希审计，再用共同预算静态基线裁决方法空间；RWKV 目前只保留软资格。

## Evidence Record

Evidence ID: `LAMDA-E1`
Source: ICLR 2026 原论文、arXiv `2505.18551v1`、HF 修订 `ad9614b`、GitHub 提交 `7728bfa`
Source type: full paper | dataset | official repository
Supports: 数据规模、时间协议、原始基线退化、公开表示和持续学习结果
Contradicts: “公开表 7 是严格源期预处理后的无泄漏强基线”
Method / dataset / metric: Android APK 静态二值特征；IID/NEAR/FAR；F1、ROC-AUC、PR-AUC、FPR、FNR
Limitation: 官方固定代码存在未来协变量预处理和阈值/目录不一致；MinerU 未成功产出
Project relevance: 下一主候选的数据与协议审计
Claim strength: supported

## 文献信息

- OpenReview：https://openreview.net/forum?id=1FnCrZtBNQ
- arXiv：https://arxiv.org/abs/2505.18551
- 数据 DOI：https://doi.org/10.57967/hf/5563
- 数据：https://huggingface.co/datasets/IQSeC-Lab/LAMDA
- 代码：https://github.com/iqsec-lab/lamda
- 项目页：https://iqsec-lab.github.io/LAMDA/
