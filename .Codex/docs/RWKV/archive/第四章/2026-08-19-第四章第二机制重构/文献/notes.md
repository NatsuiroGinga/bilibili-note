# 第四章第二机制文献调研笔记

## 结论先行

- **最强机制近邻**：Huang 与 Veeravalli 的有限时域最快变化检测。其物理第 3 页公式（2）—（3）同时规定“迟检概率不超过给定水平”和“有限路径内假警概率不超过给定水平”；第 4—6 页公式（6）—（18）给出反射 CuSum、时变阈值及有限时域保证。这是当前最直接的“首达＋时延＋路径风险”全文。
- **最强领域近邻**：Daum 等的 ECHO。其物理第 6 页用多出口分类器和置信度门提前退出，物理第 10—12 页观察到部分流“早期判对、后来判错”。它只证明其六项评测任务中存在早期证据变弱现象，不能证明本课题冻结 XGBoost 路径存在同一现象。
- **路径难负样本训练**：没有直接全文证据。Pevný、Ilse、Zhu 等只覆盖实体/袋级池化、稀疏证据保持或随机小袋估计偏差；没有论文把实体假阳路径作为难负样本重新训练冻结分类器，同时给出实体假阳风险和时延保证。
- **执行顺序**：先做零训练、源年、固定五桶的 M1 残余病灶诊断。第三章的 `semantic168+p=1` 相对 `raw83+max` 在 `101-1000`、`1001+` 桶的实体 AP 增量为 `-0.073974/-0.018679`，但机制一 Q0 已改变路径统计量，故旧诊断不能直接归因给 M1。

## 证据与分类口径

- **D0**：主题相似，未覆盖关键机制。
- **D1**：覆盖一个组件，但任务、风险单位或数据合同不同。
- **D2**：覆盖至少两个关键组件，足以构成强近邻或可证伪候选，但与本课题仍有清楚差异。
- **D3**：直接覆盖冻结逐流分数、实体路径状态、有限样本实体风险及源年到跨年评价的整套组合。本轮为零。
- “全文核验”只指可读取原件并定位物理页码/公式；摘要、题录或搜索摘要不进入技术结论。

## 检索台账

### 本地索引与通道状态

- 索引：507 篇结构化全文笔记、6799 个块，索引文件约 20 MB。
- 向量状态：`vector_count=0`、`vector_dimension=0`。首次用 `hybrid` 启动 Q01 时，嵌入模型未缓存且模型源不可达，故同一查询改为 `lexical`；后续全部本地结果均明确为词法结果。
- 完成 16 组脚本查询。Q15 与 Q16 是停止查询，均无新增 D2/D3。

| 编号 | 查询式 | 范围/结果摘要 | 与候选关系 |
| --- | --- | --- | --- |
| Q01 | `early classification time series earliness accuracy detection delay minimum prediction length` | 本地；召回 ECHO、早期 QUIC 等 | 建立早分类方向；混合通道失败后词法重跑 |
| Q02 | `quickest change detection optimal stopping false alarm delay CUSUM Shiryaev sequential` | 本地；本库直接命中稀少 | 促使转官方 QCD 全文 |
| Q03 | `sequential probability ratio test early warning frozen classifier score false alarm` | 本地；无直接冻结分数实体路径方法 | 未新增 D2 |
| Q04 | `entity heterogeneity conditional threshold group-specific false positive entity length` | 本地；主要命中公平/条件阈值和实体上下文 | 纯条件阈值按排除条件剔除 |
| Q05 | `early malware detection prefix packet detection time earliness network` | 本地；召回早期流量分类与恶意检测 | ECHO/早期 QUIC 为领域基线 |
| Q06 | `time-to-detection alarm delay first detection false positive network intrusion` | 本地；无同时给实体风险与首达时延者 | 未新增 D2 |
| Q07 | `multiple instance learning bag size bias mean pooling max pooling` | 本地；召回 Pevný、Ilse、MIDAM | 支持池化边界，不支持路径难负训练 |
| Q08 | `hard positive evidence dilution top-k pooling long sequence anomaly` | 本地；主要为 MIL/注意力/池化 | 与 ELP 高度重叠，排除主候选 |
| Q09 | `early time series classification optimal stopping earliness accuracy TEASER Economy` | `scope=all`；本地结果有效，外部提供方当次失败 | 锁定 TEASER 与非近视决策 |
| Q10 | `quickest change detection classifier score CUSUM false alarm detection delay` | `scope=all`；本地结果有效，外部提供方当次失败 | 锁定有限时域 QCD 与 SCUSUM |
| Q11 | `multiple instance learning bag size bias evidence dilution top-k pooling positive instance` | `scope=all`；本地结果有效，外部提供方当次失败 | 无超出既有 ELP/MIL 的 D2 |
| Q12 | `conditional Neyman Pearson classification group specific threshold heterogeneous false positive` | `scope=all`；本地结果有效，外部提供方当次失败 | 只得到阈值/公平性方向，按排除条件剔除 |
| Q13 | `hard negative mining difficult negative entity path false positive long sequence XGBoost` | 本地；无直接路径级难负训练全文 | exact claim 记为未支持 |
| Q14 | `early time series classification optimal stopping detection delay false alarm entity sequential` | 在线；OpenAlex 5、Crossref 5、Semantic Scholar 429 | 新增 Huang—Veeravalli 全文候选 |
| Q15 | `finite horizon CUSUM frozen classifier probability entity path detection delay` | 本地；ECHO 排第 4，其余无关 | 停止查询 1，无新增 D2/D3 |
| Q16 | `non-myopic early classification frozen XGBoost score stop continue false positive constraint` | 本地；召回 C2 信标、ECHO/早期 QUIC 邻近材料 | 停止查询 2，无新增 D2/D3 |

### 官方入口核验

另用 8 个精确题名/主题查询核验官方入口：Huang—Veeravalli 有限时域 QCD、Wu 等 SCUSUM、TEASER、Dachraoui 等非近视早分类、ECHO、Pevný 树结构 MIL、Ilse 注意力 MIL、Zhu 等 MIDAM。采用的入口分别为 arXiv、PMLR、作者公开全文或出版方；未把聚合搜索页当作技术证据。

## 全文证据

### F1：Huang 与 Veeravalli，有限时域最快变化检测，D2

- 题录：Yu-Han Huang、Venugopal V. Veeravalli，*Finite-Horizon Quickest Change Detection Balancing Latency with False Alarm Probability*，arXiv:2511.12803v1，后续出版信息 DOI `10.1080/07474946.2026.2636106`。
- 官方入口：<https://arxiv.org/abs/2511.12803>。
- 临时全文：`/private/tmp/ch4-second-mechanism-pdfs/huang-veeravalli-finite-horizon-qcd.pdf`，27 页，SHA-256 `96ac067fe28cc47eacbca34b59de4b1b34db682489db8c7e05c544e9c892134d`。
- 物理第 3 页公式（1）假设有限时域 `T` 内观测相互独立，变点前后分别来自 `f0/f1`；公式（2）把时延定义为迟检概率不超过 `δ_D` 的最小长度；公式（3）在 `P∞(τ≤T)≤δ_F` 下最小时延。
- 物理第 4—5 页公式（6）—（15）给出 CuSum/SR 以及随时间增长阈值的有限时域变体；固定阈值在时域增大时无法保持路径假警概率。
- 物理第 6 页定理 2、公式（17）—（18）同时给出有限时域假警概率控制和 `O(log T)` 时延阶。
- 物理第 6—8 页公式（19）—（32）把已知分布推广到均值不同的次高斯未知分布，GLR/GSR 仍需要独立观测、可辨识均值变化及已知次高斯参数。
- **可支持**：有限路径内的“首次越界”可以同时研究假警概率与迟检概率；反射累积统计量能把变点前累积证据归零。
- **不能支持**：冻结 XGBoost 概率天然满足独立、次高斯均值变点；论文阈值可直接替换 Tong 阈值；源年结论自动迁移 LSPR25。

### F2：Wu 等，基于评分的最快变化检测，D1/D2 边界

- 题录：Suya Wu 等，*Score-based Quickest Change Detection for Unnormalized Models*，AISTATS 2023，PMLR 206。
- 官方全文：<https://proceedings.mlr.press/v206/wu23b/wu23b.pdf>。
- 临时全文：`/private/tmp/ch4-second-mechanism-pdfs/wu-score-based-qcd.pdf`，20 页，SHA-256 `f37dda2ebe4750a81ee75529b5fa55e0474af42ae948641f04f1f85d16a7931b`。
- 物理第 4—5 页公式（6）—（9）给出 CUSUM 与 SCUSUM 首达规则，公式（9）的状态可递归为反射累积，单步更新为 `O(1)`。
- 物理第 6 页引理 1证明适当缩放下变点前增量负漂移、变点后正漂移；定理 3 公式（12）给 `E∞[T]≥e^τ` 的平均假警运行长度下界，定理 4 公式（13）给渐近检测时延。
- **关键消歧**：题名中的 “score” 是 Hyvärinen 真评分，用于未归一化生成分布，不是分类器输出概率或风险分数。论文物理第 1—3 页已明确该定义。
- 物理第 8 页结论把放宽数据独立性和未知变后分布列为未来工作。因此本篇不能直接为冻结 XGBoost 分数赋予理论保证，只能支持反射递推、首达和负/正漂移诊断的结构。

### F3：Dachraoui、Bondu 与 Cornuéjols，非近视早分类，D2 近邻

- 题录：*Early Classification of Time Series as a Non-Myopic Sequential Decision Making Problem*，ECML PKDD 2015。
- 作者公开全文：<https://antoinecornuejols.github.io/publications/PUBLIES/ECML-15-early-classification.pdf>。
- 临时全文：`/private/tmp/ch4-second-mechanism-pdfs/dachraoui-bondu-cornuejols-nonmyopic-early-classification.pdf`，15 页，SHA-256 `7c3147b0a4ddbf3950c11bbc9848b62bed49db10a2f152cc2317ec9196459f40`。
- 物理第 5 页公式（1）—（3）把误分类成本与非减等待成本相加；物理第 6—8 页公式（4）—（5）按当前不完整序列估计所有未来时刻的期望成本，算法 2 在最优剩余时域为 0 时停止。
- 物理第 6—8 页还要求：按完整训练序列聚类、为每一时刻训练分类器、在独立样本上估计逐簇混淆矩阵。物理第 13 页明确真实数据的等待成本是人为设为 `0.01/0.05/0.1×t`。
- **可支持**：继续/停止应按实体当前状态自适应，而不是用全体统一的固定退出时刻。
- **不能直接采用**：原法不是冻结单一 XGBoost 分数后处理，且人为等待成本会引入新的自由参数；把其压成源年分数状态表属于本课题新适配，需单独证伪。

### F4：Schäfer 与 Leser，TEASER，D2 基线

- 题录：Patrick Schäfer、Ulf Leser，*TEASER: Early and Accurate Time Series Classification*，arXiv:1908.03405v2；期刊版本 DOI `10.1007/s10618-020-00690-z`。
- 官方入口：<https://arxiv.org/abs/1908.03405>。
- 临时全文：`/private/tmp/ch4-second-mechanism-pdfs/schaefer-leser-teaser.pdf`，11 页，SHA-256 `98b2ac847f164e87017d68f064e7c0e157c0f1a495f81d8f20338b53a76ece15`。
- 物理第 3 页把每个快照的分类器概率、预测类和前两类概率差交给二级可靠性分类器，并要求 `v` 次连续同类可靠预测才退出。
- 物理第 4—5 页说明每个快照单独训练一级分类器，二级为只用正确预测训练的一类支持向量机；`v∈{1,…,5}` 用训练集调和均值择优。
- **可支持**：每条序列应有不同退出时刻；连续确认是防止单点早退的强基线。
- **不能直接采用**：需要多套前缀分类器和新可靠性模型，没有实体假阳有限样本证书，也不能直接复用冻结单一 XGBoost 的现成分数路径。

### F5：Daum 等，ECHO，D2 领域基线

- 题录：Shilo Daum、Tal Shapira、Anat Bremler-Barr、David Hay，*Non-uniformity is All You Need: Efficient and Timely Encrypted Traffic Classification With ECHO*，arXiv:2406.01852v3。
- 官方入口：<https://arxiv.org/abs/2406.01852>。
- 本地原件：`raw/papers/attack-detection/early-detection/2024-Horowicz-ECHO-Timely-Encrypted-Traffic-Classification-arXiv2406.01852v3.pdf`；结构化全文笔记：`wiki/papers/attack-detection/2024-Daum-ECHO非均匀分箱与早期分类.md`。
- 物理第 6 页在对数分布的多个出口分别训练分类器，以最大 softmax 置信度超过 `β-α` 提前退出；物理第 10—12 页报告一些流早期预测正确而后续预测错误，并在部分任务降低平均退出时长。
- **可支持**：加密流量确实可能存在“困难证据随更多流量被淹没”的现象，早退是必要基线。
- **不能支持**：本课题的长实体退化就是证据淹没；ECHO 的多分类器与 `α` 置信松弛等价于冻结单模型后处理；其平衡多类 accuracy 结果可转成 4% 实体 FPR 结论。

### F6：Pevný 与 Somol，树结构 MIL，D1

- 官方入口：<https://arxiv.org/abs/1703.02868>。
- 本地原件：`raw/papers/methodology/multiple-instance/2016-Pevny-Discriminative-Models-Tree-Structure-MIL-AISec.pdf`；结构化全文笔记：`wiki/papers/methodology/2016-Pevny-树结构多示例判别模型.md`。
- 物理第 3—5 页比较均值与最大池化：少量高度特异连接可能被均值淹没，最大池化能保留；实体流数差异大时最大池化较稳定。
- 物理第 6 页在约 1:1000 实体比例下用 PR 曲线，且最大池化简单网络出现训练—测试过拟合。
- **边界**：它支持“稀疏强证据可能需要保留”，不支持“选择假阳路径作难负样本重训”或冻结 XGBoost 分数上的首达风险控制。

### F7：Ilse、Tomczak 与 Welling，注意力 MIL，D1

- 官方入口：<https://proceedings.mlr.press/v80/ilse18a.html>。
- 本地原件：`raw/papers/methodology/multiple-instance/2018-Ilse-Attention-Deep-Multiple-Instance-Learning.pdf`；结构化全文笔记：`wiki/papers/methodology/2018-Ilse-基于注意力的深度多示例学习.md`。
- 物理第 3 页公式（7）—（8）把袋表示写成注意力加权平均，权重和为 1；物理第 4 页公式（9）给门控变体。
- 物理第 7—8 页显示注意力相对嵌入均值池化的收益因数据集而异，且作者在经典 MIL 基准只声称与最好方法相当。
- **边界**：注意力/可学池化与第三章 ELP 高度重叠，不能作为第四章第二机制；也没有难负路径训练或时延约束。

### F8：Zhu 等，MIDAM 随机池化，D1

- 官方入口：<https://proceedings.mlr.press/v202/zhu23l.html>。
- 本地原件：`raw/papers/methodology/multiple-instance/2023-Zhu-MIDAM-Stochastic-Pooling-ICML.pdf`；结构化全文笔记：`wiki/papers/methodology/multiple-instance/2023-Zhu-MIDAM随机池化.md`。
- 物理第 3 页公式（1）定义平滑最大池化；第 4 页说明直接以随机小袋替代完整袋会得到有偏估计；第 4—6 页公式（7）—（8）、算法 1 和定理 1用移动状态降低该偏差并给优化收敛结论。
- **边界**：它回答“大实体随机抽流训练是否有偏”，不回答“哪些实体路径应作为难负样本”，也会重新进入可学池化/训练路线，故不晋级。

## 筛选与排除

| 方向 | 最近全文 | 裁定 | 原因 |
| --- | --- | --- | --- |
| 反射累积证据首达 | Huang—Veeravalli；Wu 等 | 有条件 D2 | 能接收冻结分数经预注册变换后的增量，且与运行均值不同；但变点/独立假设和增量构造必须实测。单独替换 M1 只是替代臂；联合告警须整体重新 Tong 校准并证明检出集合互补 |
| 非近视继续/停止 | Dachraoui 等 | D2 近邻，储备 | 理论结构直接，但原实现依赖逐时刻分类器、完整序列簇和人为等待成本；冻结分数适配是新推论 |
| 可靠性连续确认早退 | TEASER、ECHO | D2 强基线，不晋级主机制 | 直接覆盖早退，但多分类器/新可靠性模型、无实体风险证书；与机制一“首次越界”重叠较大 |
| 路径难负样本训练 | Pevný、Ilse、MIDAM 仅为邻近 | D0（精确主张） | 没有全文把实体假阳路径挖掘、冻结分类器适配、实体风险和时延放在同一方法中；重训还突破冻结分数边界 |
| 注意力、top-k、可学池化 | Ilse、MIDAM、Pevný | 排除 | 重复第三章 ELP/MIL，占用已有机制而不解决序贯时延 |
| 分桶/条件阈值 | 条件 NP 与公平阈值检索结果 | 排除 | 属纯阈值再校准；若使用完整实体最终长度在线选阈值还会引入未来信息 |
| 目标标签漂移适配 | 测试时适应类结果 | 排除 | 源年资格不允许使用 LSPR25 标签 |

## 零训练病灶诊断建议

此诊断是**启动第二机制前的 G0 门禁，不是第二机制，也不证明任何方法有效**。

1. 固定源年现有交叉拟合 XGBoost 分数、M1 校准划分、`q=0.04`、实体键和时间排序；不得重训模型或重选阈值。
2. 沿用预注册五桶 `1-2 / 3-10 / 11-100 / 101-1000 / 1001+`。完整实体长度只能作离线分面，不得作为在线决策输入。
3. 对 B0、B1、M1 分别报告每桶良/恶实体数、FP、TP、FPR、DR、首次告警曝光序号、实际时延、归一化首次告警位置和未告警比例；同时给每桶对总 FP/FN 的贡献。
4. 对 M1 新增误报实体、M1 漏检但 B0/B1 检出的实体做配对路径摘要：首曝分数、路径最大运行均值、最终均值、最大单流分数、达到最大值的曝光位置。不得只看桶级 AP。
5. 只有当 M1 后仍在长桶出现可重复的 FPR/DR 或时延异常，且路径显示“旧前缀稀释后段持续证据”或可审计的负/正漂移时，才进入反射累积证据试验。试验必须同时报告 C1 独有、M1 独有的配对 TP/FP 集合，以及共同检出实体的首次告警时延差；只有新增检出或稳定提前告警，才满足“互补”而非“替代”。
6. 若 M1 已消除长桶异常，或异常来自单点尖峰而不是持续证据，则否决当前 CUSUM 路线；单点尖峰更适合用 TEASER 式连续确认作压力基线，但仍需重新校准实体路径风险。

## 未关闭疑点

- 实体内部是否存在可审计的攻击变点或逐流标签尚未确认。没有它，QCD 的“变点后检测时延”只能改写为本课题经验时延指标，不能套用原定理。
- 冻结 XGBoost 分数沿同一实体高度相关；Huang—Veeravalli 与 Wu 等的独立性条件尚未满足。
- 反射累积增量 `g(p)-κ` 中的 `g`、`κ` 必须由源年内层交叉拟合冻结；当前没有文献证明任何固定变换适用于本数据。
- 机制一 Q0 只有汇总 FP/TP，正式方案明确指出当前制品没有实体集合。完成配对长度桶诊断需要可追溯实体路径制品，不能从汇总数反推。
- M1 与 C1 的并集风险不能由两条分支各自的证书推出。正式联合方案必须先固定联合统计量或联合告警事件，再在独立良性实体上重新执行 Tong 校准；本轮未冻结该联合构造。
- 4 篇联网全文尚未正式进入 `raw/`、`wiki/` 或 Zotero；若主代理决定继续该路线，需要另开有写入权限的文献入库任务。

## Zotero 状态

- 本轮按任务边界未读写 Zotero。
- 新联网全文均为“已核全文、未入库”；不得把临时文件路径当作长期原件路径。
