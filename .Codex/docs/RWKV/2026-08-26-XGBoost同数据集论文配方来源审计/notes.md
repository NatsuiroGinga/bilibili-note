# XGBoost 同数据集论文配方来源审计笔记

## 审计口径

- **同数据集**：使用同一公开数据集名称与年度；这不自动证明行成员、清洗、字段变换或评价子集逐位相同。
- **同切分**：训练、验证、测试的成员、分组键、比例与种子相同。
- **同配置**：输入、预处理、目标函数及全部已报告 XGBoost 超参数逐项相同。
- **同训练预算**：拟合次数、每次训练成员、树数、候选网格、验证选择与早停预算相同。

## 规则与路线恢复

- 已读：`AGENTS.md`、`.Codex/docs/AGENTS.md`、`.Codex/docs/RWKV/AGENTS.md`、`thesis/AGENTS.md`、`thesis/experiments/llm_probe/AGENTS.md`、`raw/AGENTS.md`、`wiki/AGENTS.md`。
- 已读：`.Codex/docs/RWKV/RWKV路线总控.md`、`.Codex/docs/RWKV/RWKV第三章恢复卡.md`。
- 已读技能：`planning-with-files`、`citation-verification`、`expression-skill`、PDF 读取技能、Zotero 技能。
- 路线边界：本任务只审计第三章来源，不触碰独立 CUDA RWKV 活动训练路径。

## 本地文献检索收据

- 首次状态检查因 `uv` 用户缓存不可写失败，后改用 `UV_CACHE_DIR=/tmp/codex-uv-cache-xgb-audit`。
- 初次向量重建因无法解析 `huggingface.co` 失败；离线模式又等待既有索引锁。按规则降级为词法索引。
- 词法索引构建时间：`2026-08-26T06:43:36.162741+00:00`。
- 词法索引 SHA-256：`70c5846168487a078d63aabd366766692bf2c6fc27b3a5a8893f1bbadd020249`。
- 词法索引当次构建：`504` 篇论文笔记，论文分块 `7,496`，向量数 `0`。
- 查询式：`LSPR23 LSPR24 XGBoost 800 learning rate 0.05 max depth 8`。
- 作用域与模式：`paper`、`lexical`。
- 关键命中：`wiki/papers/datasets/LSPR24/Dijk-2026-LSPR23到LSPR25序列构造跨年评估.md`，本地结果第 `5` 位；Leoste 2025 第 `9` 位，但其模型是随机森林与一维卷积网络，不是 XGBoost 配方来源。
- 局限：向量通道未运行；最终裁决不依赖检索排序，而依赖本地 PDF、项目配置和运行制品。

## 论文题录与全文核验

### Dijk 等 2026

- 题名：*Sequence Construction as a Primary Design Factor in Flow-Based Intrusion Detection: A Cross-Year Evaluation on the Locked Shields Datasets*。
- 作者：Allard Dijk、Risto Vaarandi、Roland Meier、Mauno Pihelgas。
- 年份：2026。
- DOI：`10.2139/ssrn.6597680`。
- Zotero：条目键 `U4ZMBMEK`，引用键 `dijk_sequence_2026`；本地 API 已返回题名、作者与年份，BibTeX 返回同一 DOI 和 SSRN URL。
- 原件：`raw/papers/datasets/LSPR24/ssrn-6597680.pdf`。
- 原件 SHA-256：`eccb238307cc46a5f500033d1edefea63d53edc2c7adc79b3695d1eeddf78c95`。
- 全文笔记：`wiki/papers/datasets/LSPR24/Dijk-2026-LSPR23到LSPR25序列构造跨年评估.md`。
- PDF：`49` 个物理页；页内编号比物理页少 `1`。

### 逐页证据

| 论断 | 原 PDF 位置 | 核验结果 |
| --- | --- | --- |
| XGBoost 核心配方 | PDF 物理第 `24` 页、印刷第 `23` 页，第 `5.6` 节 `XGBoost Tabular Baseline` | GPU 直方图；学习率 `0.05`、深度 `8`、估计器 `800`、行采样 `0.8`、列采样 `0.8`、`lambda=1`、`min_child_weight=1`、`max_bin=256`；训练与验证行数上限均为 `0`。本段不是表格。 |
| 训练／验证切分与种子 | PDF 物理第 `24-25` 页、印刷第 `23-24` 页，第 `5.8` 节 | 按唯一 `conn_key` 在序列级拆分；受控分层抽样；固定种子 `42`。论文未报比例。 |
| 83 输入字段 | PDF 物理第 `25` 页、印刷第 `24` 页；附录 A 物理第 `49` 页、印刷第 `48` 页 | 输入经过规范化；附录逐项列出 83 字段。IP 与主机名不进入 XGBoost 逐流输入。规范化器与拟合域未报告。 |
| 同年结果 | PDF 物理第 `28` 页、印刷第 `27` 页，表 `3` | XGBoost 独立逐流、无序列上下文；LSPR23/LSPR24/LSPR25 AP 为 `1.0000/0.9923/0.8513`。 |
| 跨年结果 | PDF 物理第 `31` 页、印刷第 `30` 页，表 `5` | LSPR23→LSPR24：`1.0000→0.2416`；LSPR24→LSPR25：`0.9923→0.7666`。表题明确 XGBoost 不使用序列构造。 |
| 表 `2` 边界 | PDF 物理第 `21` 页、印刷第 `20` 页 | 表 `2` 只列共享神经模型参数，不是 XGBoost 超参数表。现有登记册把 Dijk XGBoost 来源写成“表 2、5”不精确；正确模型配置出处是第 `5.6` 节印刷第 `23` 页。 |

### 同数据集论文查全边界

本地 A 类直接使用研究共四项，来源为 `.Codex/docs/RWKV/2026-08-11-LSPR直接使用论文查全审计.md`：

| 论文 | LSPR 用途 | 模型 | 是否提供 XGBoost 配方 |
| --- | --- | --- | --- |
| Dijk 等 2024 | LSPR23 同年 | Suricata、随机森林 | 否 |
| Dijk 等 2025 | LSPR24 发布统计 | 无训练模型 | 否 |
| Leoste 2025 | LSPR23→LSPR24 | 随机森林、一维卷积网络 | 否 |
| Dijk 等 2026 | LSPR23/24/25 同年与跨年 | XGBoost、GRU、Transformer | **是，唯一同数据集 XGBoost 配方来源** |

## 当前第三章 plain XGBoost

### 身份

- 总表展示名：`XGBoost`。
- 运行身份：`ch3-baselines-full`。
- 总表将 `config_type` 写为“已发表配置重跑”；来源审计认为更准确的写法是“Dijk 2026 披露树配方的本项目协议迁移”。
- 本地运行制品：`/Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/diagnostics/ch3-baselines-full/trees_results.json`。
- 选择收据：同目录 `selection_frozen_trees.json`。
- 实现：`thesis/experiments/llm_probe/tools/ch3_baselines_full_trees.py`。

### 显式配置

| 参数 | 当前值 | 来源裁决 |
| --- | --- | --- |
| `n_estimators` | `800` | Dijk 2026 明示 |
| `learning_rate` | `0.05` | Dijk 2026 明示 |
| `max_depth` | `8` | Dijk 2026 明示 |
| `subsample` | `0.8` | Dijk 2026 明示 |
| `colsample_bytree` | `0.8` | Dijk 2026 明示 |
| `reg_lambda` | `1.0` | Dijk 2026 明示 |
| `tree_method` | `hist` | Dijk 2026 明示直方图训练 |
| `device` | `cpu` | **本项目改动**；论文为 GPU |
| `eval_metric` | `aucpr` | 本项目显式设置；论文以 AP 为主指标，但未把该参数列为 XGBoost 配置项 |
| `n_jobs` | `128` | 本项目工程设置 |
| `random_state` | `42` | 本项目设置；论文的 `42` 明确用于受控分层切分，未逐字声明为 booster 随机种子 |
| `scale_pos_weight` | 未设置 | 本项目决定；论文配置段未列该项，不能仅凭缺席证明作者运行时有效值 |
| `min_child_weight` | 配置与结果 JSON **未显式设置** | Dijk 明示 `1.0`；项目代码注释称依赖 XGBoost 默认值，但本地 plain 制品没有 `save_config()` 有效值收据，故不能从运行制品逐项确证 |
| `max_bin` | 配置与结果 JSON **未显式设置** | Dijk 明示 `256`；项目代码注释称依赖默认值，同样缺运行时有效值收据 |
| 早停 | 无 | 固定 `800` 棵训到底；论文也报告 800 棵，但未提供可核早停细节 |

### 输入与选择

- 输入：`dijk-repro/cache/X23.npy` 的 `83` 列视图；不是未处理原值，而是非有限值置 `0`、按 LSPR23 全年逐列均值与标准差标准化、裁剪到 `[-10,10]` 的矩阵。
- 字段名称与顺序来自 Dijk 附录 A 的 83 字段清单。
- 训练成员：全部 LSPR23 `16,353,511` 条流；没有源年训练／验证切分。
- 目标成员：全部本项目缓存中的 LSPR24 `20,227,356` 条流。
- 选择：不搜索超参数、不选 epoch、不早停；固定配置直接训到底，训练全部结束后读取 LSPR24 一次。
- 评价：逐流 AP；以无向 2-IP 为实体，对逐流概率取最大后计算实体 AP 与 `DR@4%FPR`。Dijk 论文的 XGBoost 是逐流评价，不提供这一实体最大池化与 DR 口径。
- 结果：逐流 AP `0.2223914545997109`、最大池化实体 AP `0.512898847990404`、`DR@4%FPR=0.6928191489361702`。
- `trees_results.json` 另含从神经 C11 借来的 `p=1.056217...` 敏感性列；它不是 plain XGBoost 自选参数，也不是当前总表 plain 行的实体 AP 口径。

## 当前第三章 XGBoost+CPA-ELP

### 身份

- 总表展示名：`XGBoost＋CPA-ELP`。
- 运行身份：`ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1-eval-continuation2`。
- 它是本项目双机制组合，不是任何发表论文中的基线。
- 本地回收结果：`/Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/diagnostics/ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1-eval-continuation2/xgb_cpa_elp_results.json`。
- 配置：`thesis/experiments/llm_probe/configs/ch3-xgb-cpa-elp-gpu-oof-seed42-v1.json`。
- 实现：`thesis/experiments/llm_probe/tools/ch3_xgb_cpa_elp_entity_oof.py` 与仅评价续跑工具。

### 显式 XGBoost 配置

`num_boost_round=800`；`tree_method=hist`；`device=cuda`；`max_depth=8`；`eta=0.05`；`subsample=0.8`；`colsample_bytree=0.8`；`lambda=1.0`；`max_bin=256`；`objective=binary:logistic`；`eval_metric=aucpr`；`seed=42`；`nthread=32`。无早停，无 `scale_pos_weight`。

`min_child_weight` 仍未出现在实际 JSON 参数映射中。方案表冻结为 `1.0`，但当前代码的运行时有效配置断言没有检查该字段；本地只回收了父有效配置收据的 SHA-256，没有收据正文。因此本次审计只能登记“意图值 1.0、运行时逐项确证缺口”，不能把它写成已由本地制品机械核实。

### 输入

- 基础 83 列与 plain 行同源于 `dijk-repro/cache/X23.npy`，同样是标准化／裁剪后的视图；代码键 `raw83` 只表示“前 83 列”，不表示原始未变换数值。
- CPA 候选一 `mean166`：83 当前列＋83 个段内含当前位置的前缀均值。
- CPA 候选二 `semantic168`：83 当前列＋76 数值残差＋5 离散同值频率＋2 布尔真值率＋`log1p(prefix_count)`＋`is_segment_start`。
- 分段：无向 2-IP 实体内按冻结时间顺序形成最长 128 流的段；所有 CPA 量只看同段 `i≤t`，段界重置。
- 运行实际选择 `semantic168`，源年最大池化实体 OOF AP 为 `0.9123669237605773`；`mean166` 为 `0.892264605242949`。
- C11 的 ELP 对 `semantic168` 最终模型的实体内全部逐流概率做幂平均，`p=1.0`，即算术平均。

### 选择与训练预算

1. 以种子 `42` 按无向 2-IP 实体标签分层为三折，同一实体全部流只在一折；三折正实体数为 `80/80/79`。
2. `raw83`、`mean166`、`semantic168` 各做三次折外拟合，每次 `800` 棵，共 `9` 次选择拟合。
3. CPA 适配器在 `mean166` 与 `semantic168` 间按汇总 OOF 最大池化实体 AP 选择；完全并列时先低维，再按名称。
4. 三路各自在 `{0.5,1,2,4,8}` 上按汇总 OOF 实体 AP 选择幂指数；完全并列时先取 `|log2(p)|` 最小者，再取较小值。实际 `raw83→2.0`、`mean166→2.0`、`semantic168→1.0`。
5. 冻结 `semantic168` 和两路最终所需的 `p` 后，在全部 LSPR23 上各训一个 `raw83` 与 `semantic168` 最终模型，共 `2` 次最终拟合。
6. 全流程共 `11` 次 XGBoost 拟合；目标年只由两路最终模型各打分一次，LSPR24 不参与适配器、超参数或 `p` 选择。
7. 当前续跑 `source_year_retrained=false`，从父运行读取两份 `800` 棵模型；父模型 SHA-256 分别为 `fcff042b...e218` 与 `1805e15d...42e9`。

### 结果身份

- C00：同次 GPU 运行内 `raw83+max`，实体 AP `0.5131848219204354`。
- C11：`semantic168+p=1`，逐流 AP `0.28325771805921907`、实体 AP `0.5650784187138617`、最大池化实体 AP `0.5303760126246202`、名义 4% 点实际 FPR `0.03998878415978258`、DR `0.8896276595744681`。
- 机制增益应以同次 GPU 的 C11 对 C00 判定，而不是拿 C11 与另一次 CPU plain 行相减后称为纯机制增益。

## 核心差异与待披露问题

1. 当前统一总表同时列出 CPU plain 行和 GPU XGBoost+CPA-ELP 行；二者不是同次训练、不同设备，选择预算也不同。
2. XGBoost+CPA-ELP 内部另有 GPU C00，才是与 C11 同设备、同核心模型预算的机制控制。
3. Dijk 2026 的 XGBoost 只用 OP 逐流输入。论文虽研究 2-IP、最长 128 的序列构造，但这些只服务 GRU/Transformer，不存在 `XGBoost+2-IP前缀+实体幂平均` 的发表配置。
4. Dijk 论文的归一化器、拟合域、缺失规则、训练／验证比例和跨年评价成员未报告；因此当前两条运行都不是同切分或严格论文复现。
5. 当前 `raw83` 名称不等于原始 83 数值；正式报告应写“标准化后的 83 字段视图”。
6. 当前全源年标准化统计覆盖三折留出成员，现有仓库文档已把它识别为源年验证统计泄漏风险。对树的严格单调仿射变换通常不改排序分裂，但非有限值置零和裁剪会破坏完全等价；本审计只登记风险，不用概念推演替代重跑裁决。
