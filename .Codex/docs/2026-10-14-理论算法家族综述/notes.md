# 过程笔记：理论／算法家族综述

> 派发 2026-10-14；模型 opus、effort high。本文件边做边写，不等任务结束补写。

## 判据（经主代理两次修正后的最终版）

- **主判据（决定能否成章）**：① 机制故事 ② 可写的形式化（收敛/结构/界/复杂度都算）
  ③ 本机快速可实测。
- **风险指标（不排序、不筛除）**：定理是否落在指标上。
- **主表最重要的两列**：「分析套路怎么写」（该族理论小节的常见形态 + 2–3 个已写并被接受的
  论文例证，只核存在不核对错）＋「机制词汇表」（该族提供的现成机制说法）。
- **排序主键**：分析套路好不好套 > 机制词汇能否套到 LAMDA 任务 > 恶意软件先例（有先例好写）
  > 成本 > 本地占据。指标定理降为风险指标。
- **空白分两类**：机制空白（没人提出过该机制）vs 应用空白（机制有、未用到 Android 恶意软件/
  该任务）。分别标注，主代理按两类分别排序。

## 网络通路（主代理实测）

- HuggingFace 等被重置站点：`curl -x http://127.0.0.1:7890`；arXiv 直连。
- `WebFetch` 对部分站点不可用，报错即换 curl 重试，不得判「来源不可得」。

## 本地已占区域（依据，2026-10-14 读）

来源：`.Codex/docs/LAMDA/LAMDA路线总控.md`、`LAMDA第三章恢复卡.md`（2026-09-09 状态）、
`thesis/methods/第三章-LAMDA任务与方案筛选矩阵.md`（2026-10-14 筛选计划）。

**已在 LAMDA 上实验并被否决/封顶的（不得再作为第三章主机制）**：

| 家族/实现 | 运行身份 | 结果 |
| --- | --- | --- |
| 标准经验回放 ER | `ch3-lamda-domain-il-naive-replay-screening-seed42-v1`（阶段 A） | 资格通过：FPR 与旧恶意负向翻转率降，AP/FNR 略差。**只作基线**，不承担创新 |
| 安全记忆（PCT 式保护集合） | 阶段 B `ch3-lamda-security-regression-ablation-seed42-v1` | 未全面占优；实现偏差（用了当前模型分数非上一冻结模型）已作废该复现资格 |
| 角色记忆 M＋双侧修复 O（ER+M/ER+O/ER+M+O） | 阶段 C `ch3-lamda-mo-source-dev-screening-seed42-v1` | 三臂均 `reject_screening` |
| 缺口感知条件风险门控 | `ch3-lamda-gap-repair-screening-seed42-v1` | `reject_implementation`：修复 FNR 降但 FPR 升至 0.139 |
| 双风险梯度投影（A-GEM 类） | `ch3-lamda-dual-risk-projection-screening-seed42-v1` | 安全保持有信号、恶意修复不足 |
| 双玩家速率约束（Lagrangian 乘子）v1/v2 | `ch3-lamda-dual-player-screening-mps-seed42-v1/v2` | v1 乘子发散全塌缩；v2 乘子几乎不介入、无独立信号 → `reject_implementation` |
| 尾锚约束（尾部高分良性推回） | E1 oracle 检验 `oracle-tail-clip.json` | 受损良性不在冻结高分尾，损伤是全局表征漂移 → `oracle_e1_rejected` |
| 无重训阈值诊断 | 开发期诊断 | F1 仅 +0.00008，不作为机制 |
| PCT+FPR gate 四臂（Cotter/Kumar） | `ch3-lamda-pct-fpr-screening-mps-seed42-v1` | `reject_implementation` |

**本地已有全文、已评估、未运行**（候选池内近邻对照，不是空白）：

- TERM（指数倾斜经验风险）、IWMS（延迟标签持续学习）、DGR（深度生成回放）
- DRO 四篇：GroupDRO／DORO／pAUC-DRO／类别条件 Wasserstein-DRO（L1–L4 本地全文齐）
- TTA 四篇：TENT／EATA／CoTTA／SoTTA＋OWAD（本地全文齐，`wiki/papers/attack-detection/`）
- Chen Android 持续学习、Cebere 九项假设审计（Web 记录）
- V-REx（第四章挖掘代理已核）

**DRIFT 旧线（非本工作树主线，但共享机制史）**：组相对选择与课程调度被自身消融否掉；
累积编辑深度与全局交叉熵选择有效但非设计产物。博弈在 DRIFT 上的具体形式（双侧对手）
被数学否决（目标精确分解为两个独立单侧最坏值）——**新博弈形式必须避开同型塌缩**。

## 查询日志

### 本地混合索引（ch3-drift-20260908 工作树，1,934 条笔记，stale=false）

原始 JSON 落 `raw-queries/`。分块后台执行：

已执行 16 个查询（4 块 × 4），原始 JSON 在 `raw-queries/chunk1..4-*.json`。
关键命中（本地已有全文的结构化笔记，证据等级=本地全文）：

| 方向 | 本地命中的全文笔记 |
| --- | --- |
| IRM/不变性 | `methodology/2021-Ahuja-不变性与信息瓶颈.md`、`2021-Krueger-REx风险外推.md`、`2024-Liu-FOIL时间序列OOD不变学习.md` |
| 保形/风险控制 | `2024-Angelopoulos-保形风险控制.md`(CRC)、`2021-Bates-分布无关风险控制预测集.md`(RCPS)、`2019-Tibshirani-协变量移位加权保形.md`、`2012-Vovk-条件归纳保形预测.md`、`soc-alert-operations/2026-CALIBURN-区间依赖保形风险控制的告警预算.md`（流式 IDS+区间依赖 CRC！）、`2025-Almeida-协变量移位高概率风险控制.md` |
| TTA | TENT/EATA/SAR/CoTTA 全齐＋`2026-Kim-CANDI精选测试时适应.md`、`2025-Roh-MADCAT自监督测试时适应.md`（恶意软件 TTA 先例） |
| 持续学习 | `2023-Chen-Android恶意软件持续学习.md`、`2017-Shin-深度生成回放.md`、`2024-Botos-IWMS延迟标签持续学习.md` |
| 课程 | `auxiliary-learning/2018-Cai-课程对抗训练.md`、`课程式对抗训练-在线视角.md`(2024)、`2026-Shin-课程学习与Wasserstein测地线.md` |
| 博弈 | 朱焱雷全文、`game/stackelberg-vs-nash_2011_kiekintveld.md`、`game/Complexity of Computing Optimal Stackelberg Strategies in Security Resource Allocation Games.md`(2010)、`game/SCORER-表征与强化学习斯塔克尔伯格耦合.md`(2026)、`datasets/locked-shields-related/2021-SchroederdeWitt-AI-NIDS博弈不动点与规避攻击.md` |
| 长尾/CVaR | `ranking/2019-Prashanth-CVaR估计的集中不等式.md`、`2025-Chen-BUOT双层非平衡传输.md` |
| 重要性加权 | `2024-Joo-IW-GAE重要性加权组准确率.md`、Tibshirani、Almeida 2025 |
| 开集/拒识 | `2022-Luxemburk-TLS细粒度服务分类与拒识.md`、`datasets/data-protocol/开放集入侵识别-未知攻击协议.md`(2017)、`Geifman2019-SelectiveNet选择性预测.md` |
| 标签噪声 | `2022-Arp-安全机器学习十大陷阱.md` |
| 主动学习 | `2025-Haque-CITADEL半监督主动漂移适应.md`（恶意软件 AL+漂移先例）、`2019-Pendlebury-TESSERACT时空实验偏置与AUT.md`、`2025-Gupta-NetGuard漂移与不均衡NIDS主动适应.md` |
| 梯度手术 | `2020-Yu-PCGrad梯度手术.md`、`manifold/Recon从结构根源减少梯度冲突.md`、`2018-Chen-GradNorm梯度归一化.md`、`game/AuxiNash-辅助学习非对称议价训练.md`、`2025-Patapati-SON-GOKU图着色多任务调度.md` |
| RL | `2018-Anderson-RL-Malware-Evasion.md`、`2020-Song-MAB-Malware学习型黑盒规避.md`（攻击侧）、`2026-Sabbah-自监督强化学习漂移维护.md`（Android+SSRL+RL+漂移！）、`PINN引文链与恶意流量检测理论映射.md` |
| coreset | 朱焱雷 2.4.2 引 Toneva 遗忘样本、`2026-Park-COMET代码本在线适应异常检测.md`、SelectiveNet、`training-efficiency/2019-Jiang-选择性反传聚焦高损失样本.md`、`2020-Mialon-ERM椭球区域数据点筛除.md` |
| RWKV/SSM | `rwkv/` 目录 5 篇：RWKV、RWKV-X、FRWKV、GoldFinch、RADLADS |
| 排序/聚合 | `ranking/2019-Kawaguchi-OrderedSGD批内top-q选择.md`、`2021-Hu-SoRR-Sum-of-Ranked-Range.md` |

未在本地命中的方向（需在线补）：类别条件 W-DRO 在恶意软件、保形在 Android 恶意软件、
SAM 在恶意软件、长尾/平衡误差在 Android 家族分类、密度比重要性加权在 Android 漂移、
课程在 Android 漂移、元学习/少样本在家族分类。

### Zotero 语义检索（5 个方向，题录级）

命中：CRC/CALIBURN/非交换 CRC/Vovk；BBSE/Garg/Saerens；NP 分类（Tong 2018 Sci Adv）；
DORO/Duchi-Namkoong/V-REx；MADCAT/Berruz/TESSERACT/Transcending 2022；AUPRC 可证收敛（Qi 2021）。
关键发现：**NP 分类定理直接落在指标上**（`P(FNR(λ̂)≤α)≥1−δ`）——全表最罕见。

### OpenAlex 三批（raw-queries/openalex/）

- 第一批 32 个家族×先例查询 + 第二批 15 个定向查询 + 6 篇摘要抽取 + 第三批 28 个 canonical 存在性核验。
- 重大发现：TIF 2026（TSE）＝不变性学习×Android 时间漂移直接先例；PAD 2023（TDSC）＝恶意软件
  收敛保证先例；MalTutor 2025＝Android 家族不平衡课程先例；GameNP 2024（TIFS）＝NP×博弈先例；
  Mamba+PE opcode 2026＝恶意软件 SSM 先例（Windows）；GroupDRO×恶意软件＝空白（总量 4 无相关）。
- 网络通路实测：OpenAlex/Semantic Scholar/arXiv 直连；Semantic Scholar 限流 429 后弃用；
  WebSearch 工具返回空结果弃用；WebFetch 按主代理指示换 curl。

### 任务完成状态

- [x] families.md：28 条家族（17 个超族），含分析套路、机制词汇、先例、成本、占据、空白类型
- [x] ranked-shortlist.md：前 5 条（BBSE 标签转移修正、课程年序重排、SAM、NP 校准、GroupDRO）
- [x] evidence-index.md：三批查询收据、canonical 核验、六条证据缺口披露
