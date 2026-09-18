# DGA 检测专项系统综述笔记

## 已冻结问题

- 领域是否已有跨年份、未见家族、低 FPR 和重复隔离同时成立的强基线？
- DRIFT 的十个外部基线分别代表哪条技术谱系，其公开对比是否公平可复现？
- 条件记忆、在线后缀检索和跨家族稳健风险各自已有何种全文近邻？
- 哪些高分只来自同分布随机划分，不能进入第三章的正式泛化对比？

## 查询日志

### 2026-09-07：初始化

- 已读取根、`raw/`、`wiki/`、`.Codex/docs/` 与 `thesis/` 规则，以及 `citation-verification`、`google-scholar`、`pdf-converter`、`huggingface-papers`、`hf-cli` 技能。
- 沿用已核 DRIFT 原件：arXiv `2605.10436v2`，正式 DOI `10.1109/DSN69566.2026.00077`，48 条参考文献。
- 引文雪球顺序已冻结为：DRIFT 全参考分类 → 核心全文 → 前向追踪 → 独立关键词查漏。

### 2026-09-07：本地索引与 DRIFT 引用表

- 初始索引因并行文档新增为 `stale=true`，首个 `paper/hybrid/offline` 查询触发增量构建。
- 查询：`DGA detection FANCI Woodbridge Endgame EXPLAIN HMT HDDN temporal drift unseen family low false positive`；本地只有 DRIFT 和通用漂移/低 FPR 近邻，DGA 历史核心全文基本缺失。
- 已从 DRIFT v2 逐条抽取参考文献 `[1]`–`[48]`。核心分类：数据/协议 `[1,8,11–14,17,40–42]`；传统/上下文 `[2,4,20–24,37–39]`；字符深度 `[19,25–33,45–47]`；子词/Transformer `[7,9,10,16,34,35,43,48]`；分布外基准 `[36]`；低误报 `[18]`。该分类只决定精读顺序。

### 2026-09-07：首批核心全文

- 新增合法原件并由 MinerU `extract` 取得全文：Woodbridge LSTM、FANCI、Yu 等字符模型比较、Drichel 2020 真实适用性、Drichel 2023 偏差/XAI 审计、Dom2Vec、MaskDGA、CharBot、LLMs for DGA。
- Woodbridge：静态公开数据上报告二分类 AUC `0.9993`、多类微 F1 `0.9906`，以及 `TPR=90%` 时 `FPR=1e-4`；但没有时间、家族和实体隔离。
- Drichel 2020：在真实 NXD 良性数据、20 次数据集重复下比较 FANCI、Endgame、NYU 和新 B/M-ResNet；另做跨网络、1/17 个月、未知 DGA 和 3.7 亿 NXD 真实月测试。它是 DRIFT 之前最关键的低误报与外推强基线。
- Drichel 2023：说明 contextless 分类器的 99.9% 级高分会依赖 TLD、长度和数据构造偏差；必须把偏差清理与真实流量重测纳入 C00 门。
- MaskDGA/CharBot：纯字符串模型可被少量字符修改或代理梯度攻击规避；对抗重训不自动解决，身份/重复与合法性检查不可省略。
- HMT、HDDN 的 Zotero 父项已导入，但自动附件失败；在取得全文前不使用其方法数字作为结论。

### 2026-09-07：formal-v3 对候选优先级的影响

- 制品：`thesis/experiments/llm_probe/runs/diagnostics/ch3-drift-t17-t25-rosa-deepembed-coverage-probe-v1/formal-v3.json`；固定数据 revision `3b31077020cd1c013d0a75cad51042a2327c4521`，状态 `completed`。
- ROSA 总覆盖 `0.2472242380`，与 1-gram 覆盖完全相同；后继命中率 `0.0614990268`，1-gram 为 `0.0605920716`，绝对只增加 `0.0009069553`。
- 4,289,076 个可预测位置中，匹配长度 1 为 4,008,210，占 `93.45%`；长度至少 2 只有 280,866。输入覆盖不能当作分类增益，ROSA 应下调，不进入当前首个短训。
- DeepEmbed：T25 字符 OOV 为 0；2-gram 域级 OOV 良性为 0、DGA 为 `2.084e-7`；3-gram 良性为 `0.0009148`、DGA 为 `0.0031227`。因此“未来 OOV 很高”不成立；条件记忆只有在基线错误与表内低频模式相关、且超过等容量/随机哈希对照时才有短训资格。
- 精度边界：T17 良性实际样本 365,121，最坏半宽 `0.00162181`，略高于预注册 `0.00161942`。该次运行只能称描述性正式运行，不能声称全部精度门严格通过。
- raw 家族审计仍禁用；跨家族稳健风险的直接数据资格尚需家族支持度、重复域名和基线错误分面。

### 2026-09-07：Zotero、全文笔记与前向查漏

- 新导入并附PDF：Woodbridge `QLAZ28M5/YFVM27S3`、Drichel 2020 `EXIL3ZC5/6GJGYT27`、EXPLAIN `3ZSMKA6G/THAUE8Q7`、Drichel 2023 `HPHZ9DGG/4BKEN678`、MaskDGA `K3VYSJSY/6A67NG7A`、CharBot `CPILDEPS/H3PWHIIV`、LLM-DGA `876KBMY9/VVANKUZY`、中文低FPR `GS4W36SX/FFX4C3AS`。
- 只有题录或附件修复失败：Yu `ZT3V5DFU`、Dom2Vec `MFVE9BEC`、HMT `FKWTVH9J`、HDDN `JDCQ9ZB8`、Down-to-earth `IBFW33PR`。FANCI本地Connector键`KCNJNWWX`与Web附件修复库不一致。
- 一次错误的多条RIS调用产生空白本地项`YT67L9MB`；因删除是破坏性操作，本轮不擅自清理。
- 新增`wiki/papers/attack-detection/dga/`下12篇严格结构化全文笔记，并更新`wiki/papers/attack-detection/INDEX.md`。全目录严格lint：12文件，0错误，0警告。
- 2024–2026查漏已全文纳入：中文域低FPR、Down-to-earth、LLM-DGA、DRIFT；HDDN只有题录，HMT为2023直接Transformer前身且全文阻塞。Google Scholar广义关键词结果噪声很高，不把无关召回计入覆盖。
- C00阶段裁决：默认监督双分支DRIFT，完整DRIFT作发表上界，偏差约简B-ResNet强制并列；最终由共同协议真实运行决定是否替换。
- 短训阶段更新：当前首个可执行候选优先良性高分尾部风险，因为家族映射仍阻断；跨家族稳健风险在raw家族/生成器/重复审计后运行。条件记忆只在表内低频错误相关门通过后作为替代，ROSA、mHC不进入首轮。
- 并行数据角色合同已冻结为T17–19正式源训练/验证、T17→T18→T19仅筛选止损、T20–T24整批封印确认、T25 `target_informed`完整压力测试；综述已按该合同修正，不采用T20标签开发方案。

## 候选分类

| 类别 | 必核对象 | 全文状态 | 下一步 |
|---|---|---|---|
| 数据与协议 | DGArchive、Alexa、Tranco、公开 DGA 数据与去重协议 | 审计中 | 从 DRIFT 引用与数据卡反查原始来源 |
| 传统词法/统计 | FANCI、EXPLAIN 及随机森林/人工特征方法 | 审计中 | 本地/Zotero 去重后补全文 |
| 字符深度模型 | Woodbridge LSTM、Endgame、MIT/NYU、B-ResNet、M-ResNet | 审计中 | 还原谱系、数据与划分 |
| Transformer/自监督 | HMT、HDDN、BERT、Llama3、DRIFT | 审计中 | 核机制差量与共同预算 |
| 时间漂移/持续学习 | DRIFT、MADCAT、漂移重训近邻 | 部分已有全文 | 区分冻结、无标签适应和带标签更新 |
| 未见家族/开放集 | 家族留出、拒识、开放世界 DGA | 审计中 | 查全文与家族隔离 |
| 低 FPR/校准 | 固定 FPR、阈值迁移、校准 | 审计中 | 独立关键词查漏 |
| 对抗规避/泄漏 | MaskDGA、CharBot、重复/身份泄漏 | 审计中 | 核攻击权限和防御协议 |

## 阻塞与边界

- 不根据模型名称推断结构或效果。
- 不把 DRIFT 原论文对基线的二手数字替代基线原论文全文。
- 不把 DGA 家族分类高分、随机切分高分或作者自测 checkpoint 视为未来年份泛化证据。
