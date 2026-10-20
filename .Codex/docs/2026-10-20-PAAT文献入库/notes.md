# PAAT 文献入库检查点

> 每完成一篇立即追加。字段：查询式 / 来源 URL / 原件路径 / 元数据核验 / 证据等级 / 页码锚点 / 与 M1/M2 关系 / wiki / Zotero。

## 进度总览

| 文献 | 题录核验 | PDF | 全文转换 | 全文阅读 | wiki | INDEX | Zotero |
|---|---|---|---|---|---|---|---|
| ProtoNet | 待办 | 待办 | 待办 | 待办 | 待办 | 待办 | 待办 |
| SupCon | 待办 | 待办 | 待办 | 待办 | 待办 | 待办 | 待办 |
| ClassBalanced | 待办 | 待办 | 待办 | 待办 | 待办 | 待办 | 待办 |
| LDAM | 待办 | 待办 | 待办 | 待办 | 待办 | 待办 | 待办 |
| Decoupling | 待办 | 待办 | 待办 | 待办 | 待办 | 待办 | 待办 |

## 初始检索记录

- 工具：arXiv Export API `https://export.arxiv.org/api/query?id_list=<id>`；Crossref `https://api.crossref.org/works`。
- scholar CLI 当前网络不可达，按用户指示不依赖。
- 本地查重：`rg -il "Prototypical|Supervised Contrastive|Class-Balanced|Label-Distribution-Aware|Decoupling Representation" wiki raw/papers` 未命中目标论文全文，只有主题相关的其他笔记。

## 逐篇检查点

### 1. ProtoNet

- **查询式**：arXiv `id_list=1703.05175`；WebSearch `"Prototypical Networks for Few-shot Learning" NeurIPS 2017 proceedings`。
- **来源 URL**：https://export.arxiv.org/api/query?id_list=1703.05175；https://papers.nips.cc/paper_files/paper/2017/hash/cb8da6767461f2812ae4290eac7cbc42-Abstract.html
- **题录核验**：Jake Snell, Kevin Swersky, Richard S. Zemel；2017；NIPS 2017（Advances in Neural Information Processing Systems 30）；arXiv:1703.05175v2。
- **原件路径**：`raw/papers/methodology/2017-Snell-Prototypical-Networks-Few-Shot.pdf`（13 页，PDF v1.5，571 KB）。
- **全文转换**：MinerU `extract`，`/tmp/2026-10-20-PAAT文献入库/2017-Snell-Prototypical-Networks-Few-Shot.md`；JSON 页码索引 `/tmp/2026-10-20-PAAT文献入库/json/...json`。
- **证据等级**：本地全文（已读 §1–§5 与附录 Table 1–6）。
- **页码锚点**：Eq. 1–2 第 2 页；§2.3 第 3–4 页；§2.4 Eq. 7–8 第 4 页；§2.6 第 4–5 页；Table 1 第 5 页；Table 2 第 6 页；Table 3 第 7 页；结论第 8 页。
- **与 M1/M2 关系**：M1 的直接结构来源（类均值原型 + 距离 softmax）。边界：无 EMA 原型、无跨年漂移、无投影头；二分类下与 BCE 高度重叠。
- **wiki**：`wiki/papers/methodology/2017-Snell-原型网络少样本学习.md`
- **Zotero**：`NFQVNZ4U`（新建）。

### 2. SupCon

- **查询式**：arXiv `id_list=2004.11362`；WebSearch `"Supervised Contrastive Learning" Khosla NeurIPS 2020 proceedings`。
- **来源 URL**：https://export.arxiv.org/api/query?id_list=2004.11362；https://neurips.cc/virtual/2020/poster/17228
- **题录核验**：Prannay Khosla, Piotr Teterwak, Chen Wang, Aaron Sarna, Yonglong Tian, Phillip Isola, Aaron Maschinot, Ce Liu, Dilip Krishnan；2020；NeurIPS 2020（Advances in NeurIPS 33）；arXiv:2004.11362v5。
- **原件路径**：`raw/papers/methodology/2020-Khosla-Supervised-Contrastive-Learning.pdf`（23 页，2.1 MB）。
- **全文转换**：MinerU `extract`，`/tmp/2026-10-20-PAAT文献入库/2020-Khosla-Supervised-Contrastive-Learning.md`；JSON 页码索引同目录 `json/`。
- **证据等级**：本地全文（已读 §1–§4 与补充材料目录/关键节）。
- **页码锚点**：§3.1 第 4 页；Eq. 2–3 第 5 页；Eq. 4–6 第 5–6 页；Table 1 第 5 页；Table 2–3 第 6 页；鲁棒性第 7 页；迁移 Table 4 第 8 页；训练细节第 9 页；补充材料 §6–§10 第 13–19 页。
- **与 M1/M2 关系**：M1 的类内紧凑性依据（多正例 + 温度 + 投影头）。边界：需大批量/多正例；正例有放回重复会夸大类内一致性；需要标签保持增广；类别条件稳定假设与年度漂移冲突。
- **wiki**：`wiki/papers/methodology/2020-Khosla-监督对比学习.md`
- **Zotero**：`5RD58S8H`（新建）。

### 3. ClassBalanced

- **查询式**：arXiv `id_list=1901.05555`；Crossref `query.bibliographic=Class-Balanced Loss Based on Effective Number of Samples`。
- **来源 URL**：https://export.arxiv.org/api/query?id_list=1901.05555；Crossref 返回 DOI `10.1109/cvpr.2019.00949`。
- **题录核验**：Yin Cui, Menglin Jia, Tsung-Yi Lin, Yang Song, Serge Belongie；2019；CVPR 2019；doi:10.1109/CVPR.2019.00949；arXiv:1901.05555v1（arXiv comment 给出代码链接）。
- **原件路径**：`raw/papers/methodology/2019-Cui-Class-Balanced-Loss.pdf`（11 页，858 KB）。
- **全文转换**：MinerU `extract`，`/tmp/2026-10-20-PAAT文献入库/2019-Cui-Class-Balanced-Loss.md`；JSON 页码索引同目录 `json/`。
- **证据等级**：本地全文（已读 §1–§6 与附录 A）。
- **页码锚点**：§3.1 第 3 页；Prop. 1/Eq. 1–5 第 3–4 页；Eq. 6 第 4 页；Eq. 8/11/13 第 5 页；§5.2 第 6 页；Table 2 第 6 页；§5.3 β 消融第 7 页；Table 3 第 8 页。
- **与 M1/M2 关系**：M2 的「损失重加权」替代路径；明确反对过采样（与 M2 的有放回平衡采样构成直接对照）；sigmoid CE 形式可直接映射到二分类 BCE；偏置初始化建议可迁移。
- **推算记录**：β=0.9999、n+=159、总样本约 9,700 时正负权重比约 39:1（按频率倒数约 60:1）；n+=5 时正例权重约 0.2、正负比约 1265:1。**属本文按公式推算，不是论文实验，也不是 PAAT 实测**。
- **wiki**：`wiki/papers/methodology/2019-Cui-有效样本数类平衡损失.md`
- **Zotero**：`H6V9H92E`（新建）。

### 4. LDAM

- **查询式**：arXiv `id_list=1906.07413`；arXiv comment 字段。
- **来源 URL**：https://export.arxiv.org/api/query?id_list=1906.07413
- **题录核验**：Kaidi Cao, Colin Wei, Adrien Gaidon, Nikos Arechiga, Tengyu Ma；2019；NeurIPS 2019（arXiv comment: "to appear in NeurIPS 2019"）；arXiv:1906.07413v2。
- **原件路径**：`raw/papers/methodology/2019-Cao-LDAM-Label-Distribution-Aware-Margin.pdf`（18 页，1.3 MB）。
- **全文转换**：MinerU `extract`，`/tmp/2026-10-20-PAAT文献入库/2019-Cao-LDAM-Label-Distribution-Aware-Margin.md`；JSON 页码索引同目录 `json/`。
- **证据等级**：本地全文（已读 §1–§5 与附录目录）。
- **页码锚点**：Theorem 1/Eq. 4–5 第 4 页；Eq. 8 第 5 页；Eq. 12–13 第 5 页；Algorithm 1 第 6 页；Table 1 第 7 页；Table 2 第 8 页；Table 3 第 9 页。
- **与 M1/M2 关系**：M2 启用时点的关键证据（DRW：早期 ERM、退火后平衡）；类相关间隔是重采样的替代；明确警告重采样少数类易过拟合。
- **推算记录**：n+=159 时 n^{1/4}=3.55；n+=5 时 n^{1/4}=1.50；同一 C 下 2025 年正类间隔约为 2024 年的 2.4 倍。**属本文按公式推算，不是论文实验，也不是 PAAT 实测**。
- **wiki**：`wiki/papers/methodology/2019-Cao-LDAM标签分布感知间隔.md`
- **Zotero**：`ANRD7VXK`（新建）。

### 5. Decoupling

- **查询式**：arXiv `id_list=1910.09217`；arXiv comment 字段。
- **来源 URL**：https://export.arxiv.org/api/query?id_list=1910.09217
- **题录核验**：Bingyi Kang, Saining Xie, Marcus Rohrbach, Zhicheng Yan, Albert Gordo, Jiashi Feng, Yannis Kalantidis；2020；ICLR 2020（arXiv comment: "Published as a conference paper at ICLR 2020"）；arXiv:1910.09217v2。
- **原件路径**：`raw/papers/methodology/2020-Kang-Decoupling-Representation-Classifier.pdf`（16 页，740 KB）。
- **全文转换**：MinerU `extract`，`/tmp/2026-10-20-PAAT文献入库/2020-Kang-Decoupling-Representation-Classifier.md`；JSON 页码索引同目录 `json/`。
- **证据等级**：本地全文（已读 §1–§6 与附录 A 开头）。
- **页码锚点**：Eq. 1 第 3 页；Eq. 2 第 4 页；cRT/NCM/τ/LWS 第 4 页；Eq. 3–4 第 4 页；Table 1 第 6 页；Table 2 第 7 页；Table 3–4 第 8 页；Fig. 2 第 7 页。
- **与 M1/M2 关系**：对 M2 的最强反证/替代方案（实例平衡学表示 + 分类器再平衡）；NCM 是 M1 的低成本强基线，解释「零训练原型无增益」；PAAT 正负各半回合在二分类下就是 q=0 类平衡采样。
- **wiki**：`wiki/papers/methodology/2020-Kang-长尾解耦表示与分类器.md`
- **Zotero**：`APMCBGQF`（新建）。

## 工具与阻塞记录

- **arXiv Export API**：5/5 成功，返回题名、作者、发布时间、版本与 comment/journal_ref。
- **Crossref**：Class-Balanced 命中 DOI `10.1109/cvpr.2019.00949`；其余 NeurIPS/ICLR 论文未命中正式 DOI，venue 由 arXiv comment 与会议页核验。
- **WebSearch**：ProtoNet 与 SupCon 的会议页/venue 核验；返回 NIPS 2017 proceedings 与 NeurIPS 2020 poster 页。
- **DBLP API**：返回 202 + 机器人验证页，未使用；**Semantic Scholar API**：429 限流，未使用。
- **OpenAlex**：用于交叉核对题名/年份；对 ProtoNet/SupCon/LDAM/Decoupling 返回 arXiv 源，未提供会议 venue。
- **scholar CLI**：按用户指示未使用（网络不可达）。
- **MinerU**：`auth --verify` 通过（Source: env，不打印 token）；`extract` 5/5 成功，正式模式，公式/表格保留。
- **Zotero**：查重（semantic + exact title）均未命中；`zotero_add_items_by_arxiv` 5/5 成功，未附带 PDF（本地原件已入库）。
- **未取得全文**：无。第一优先 5 篇均为本地全文。
- **第二优先**：未执行（时间用于第一优先全文阅读与笔记）。
