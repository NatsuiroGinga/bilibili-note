# CPA 保留与独立实体头机制重构：证据登记笔记

- **日期**：2026-08-21
- **代理**：`cpa_entity_head_design_fable_high`（模型 `claude-fable-5`，effort `high`）
- **上游计划**：同目录 [task_plan.md](task_plan.md)（只读，不修改）
- **产出去向**：同目录 [机制设计与实验方案.md](机制设计与实验方案.md)
- **本笔记职责**：登记阶段二的五篇全文证据（证据等级、关键页码、唯一支持部件、禁止外推边界）与本课题已证病灶数值；不做机制裁决，裁决在正式方案文档。

## 一、检索工具状态披露

按仓库规则先运行状态查询，再执行离线混合检索。所有命令在工作树根执行；命令输出中首行 `ERROR: GVM_ROOT not set` 为本机 shell `chpwd` 钩子噪声（`cd` 触发，Go 版本管理器未初始化），与检索工具无关，但它会使 `cd X && cmd` 的 `&&` 链短路，本次全部改用 `;` 串联。

```bash
uv run --project scripts/literature_search --locked python -m scripts.literature_search status --json
```

- 索引存在：`.cache/literature-search/index.sqlite3`，`built_at=2026-08-21T08:35:43Z`，1768 篇笔记、36088 块。
- **`stale=true`**，原因 `source_added/source_changed`。逐项核对过期清单：新增 30 项、变更 11 项全部是 `.Codex/docs/` 过程文档与 `runs/` 收据；**`papers` 集合 500 篇零增改**（`added=0, changed=0, deleted=0`）。因此论文作用域（`--scope paper`）检索结果不受过期影响。
- **未重建索引**：本任务边界禁止修改既有文件与运行目录，重建会改写 `.cache/` 下索引；且过期源不影响 `paper` 作用域，重建非必需。此决定在此披露，主代理可在核验后自行重建。
- 向量通道**已运行**（`vector_device=mps:0`，模型 `intfloat/multilingual-e5-small`），本次为真实 `hybrid` 模式，无 `lexical` 降级。

检索命令（每篇一条，输出取 `local_results` 前 4）：

```bash
uv run --project scripts/literature_search --locked python -m scripts.literature_search query "ForkMerge auxiliary task negative transfer" --scope paper --mode hybrid --offline --json
uv run --project scripts/literature_search --locked python -m scripts.literature_search query "Ilse attention deep multiple instance learning" --scope paper --mode hybrid --offline --json
uv run --project scripts/literature_search --locked python -m scripts.literature_search query "Pevny multiple instance learning network security" --scope paper --mode hybrid --offline --json
uv run --project scripts/literature_search --locked python -m scripts.literature_search query "MIDAM multi-instance deep AUC maximization stochastic pooling" --scope paper --mode hybrid --offline --json
uv run --project scripts/literature_search --locked python -m scripts.literature_search query "Recon gradient conflict remove layer-wise multi-task" --scope paper --mode hybrid --offline --json
```

五条查询目标笔记均命中排名第 1。定位后用 `rg` 与 `Read` 完整读取全文笔记原文，页码与公式位置逐条抄自笔记（笔记为 `pdftotext` 逐页核对的结构化全文笔记，见各条登记）。

## 二、证据分级口径（沿用既有审计，不新造分类学）

- **E 级＝全文核验状态**：E3 正式全文已逐页核验；E2 全文可得但核验较弱；E1 仅摘要。出处：`.Codex/docs/RWKV/2026-08-20-第三章机制替换文献与实验审计/notes.md` 第 23 行。
- **D 级＝与本课题设计的结构同构度**：D3 同一全文覆盖全部关键关系（直接先例）；D2 覆盖多个关键关系但缺决定性环节；D1 单一基础部件。出处：`.Codex/docs/RWKV/2026-08-21-LSPR指标体系与N16文献审计.md` 第 47–53 行。
- 两轴独立：一篇论文可以是 E3（全文已核）同时只有 D1/D2（结构近邻）。`task_plan.md` 关键问题 2 所问「为什么证据仍为 D 级机制启发」，指的是 D 轴：五篇没有一篇同时覆盖「冻结骨干＋因果前缀摘要＋实体终端头＋共同实际 FP 预算裁决＋跨年度加密攻击流量」的完整耦合，也没有一篇在网络流量或 LSPR 数据上给出实验，故对本课题只能提供机制来源与可试性，不能提供有效性证据。

## 三、五篇全文证据登记

### 3.1 ForkMerge（Jiang 等，NeurIPS 2023）

```md
## Evidence Record
Evidence ID: ER-20260821-forkmerge-01
Source: wiki/papers/methodology/2023-Jiang-ForkMerge辅助任务负迁移.md
Source type: full paper
原件: raw/papers/methodology/auxiliary-learning/2023-Jiang-ForkMerge辅助任务负迁移.pdf（SHA-256 597e00c0…f9de，23 物理页，NeurIPS 正式 PDF，DOI 10.52202/075280-1322）
证据等级: E3 / D2（D2 出处：机制替换审计《机制替换候选与最小实验.md》第 178 行，候选 3「验证驱动辅助目标更新过滤」的最高近邻）
关键位置: 物理 pp.3–4 迁移增益与弱/强负迁移定义；p.4 Finding 1（负梯度夹角与负迁移非充要）；pp.5–6 公式(5)–(8)与算法 1（分叉—验证选择凸组合—合并）；pp.8–10 表 1–6（DomainNet 等权联合平均退化 9.62%、ForkMerge 平均提升 2.00%）
Supports: 仅支持一个设计部件——S2 的「辅助更新进入共享参数须由主任务验证表现驱动过滤」训练合同（S2-F 臂），及「梯度夹角只作诊断不作裁决」的边界
Contradicts: 以梯度余弦为选择器的方案（PCGrad/余弦门控作为裁决）
Limitation: 实验全在图像/多任务/推荐/半监督基准，无网络流量；参数凸组合需可反复读取的验证集，验证正例极少时有过拟合风险（p.4、机制边界第 4 条）；两分支训练计算约为单分支两倍
Claim strength: supported（对其原论文结论）/ speculative（对本课题有效性）
为什么仍为 D 级机制启发: 覆盖「辅助任务＋验证驱动选择＋分支合并」多个关键关系，但缺「冻结骨干实体头、实体级 FP 预算裁决、跨年度流量数据」决定性环节；不提供 LSPR 有效性证据
禁止外推: 不得声称 O11 病灶由辅助任务负迁移造成；不得声称 ForkMerge 必然修复跨年度性能；不得照搬连续凸组合搜索（本课题验证正例少，只做 epoch 端点硬选择）；不得引用其 2.00%/4.03% 数字作为本课题预期
```

### 3.2 Ilse（Ilse、Tomczak、Welling，ICML 2018）

```md
## Evidence Record
Evidence ID: ER-20260821-ilse-02
Source: wiki/papers/methodology/2018-Ilse-基于注意力的深度多示例学习.md
Source type: full paper
原件: raw/papers/methodology/multiple-instance/2018-Ilse-Attention-Deep-Multiple-Instance-Learning.pdf（SHA-256 9da16d3f…b199，16 页，ICML 2018/PMLR 80）
证据等级: E3 / D1（D1 出处：机制替换审计 notes.md 第 112 行）
关键位置: 第 2 页定理 1/2（对称函数分解，「实例变换→置换不变聚合→袋级变换」）；第 3 页公式(7)(8)注意力池化、嵌入级与实例级两条路线；第 4 页公式(9)门控变体；第 8 页表 2/表 3（BREAST CANCER：Embedding+mean AUC 0.796 对 Instance+mean 0.719；COLON CANCER：Attention AUC 0.968 对 Embedding+mean 0.940）
Supports: 仅支持一个设计部件——S1 实体头的**挂载位置**：在冻结隐藏表示（嵌入级）上聚合后分类，而不是在逐流概率（实例级）上再聚合
Contradicts: 「注意力池化必然优于均值」的预设——其增益仅 AUC +0.003（BREAST）至 +0.028（COLON），量级有限
Limitation: 全部实验为分子活性/病理图像，无流量、无漂移、无跨年度；未报告注意力的参数量代价；未定量回答「注意力是否退化为均值」
Claim strength: supported（嵌入级优于实例级，在其数据上）/ speculative（对本课题）
为什么仍为 D 级机制启发: 只提供「聚合位置」这一个基础部件的来源；其嵌入级优势数字来自组织病理图像，与 LSPR 实体长尾、极端类不平衡、跨年度漂移无一对应
禁止外推: 不得写「嵌入级聚合在本课题必然优于概率聚合」（本课题只有 N11 概率池化失败这一侧的本地证据）；不得据其表 2/3 预设注意力头收益；不得把其 batch=1 训练协议迁移为本课题合同
```

### 3.3 Pevný（Pevný、Somol，arXiv:1609.07257v3）

```md
## Evidence Record
Evidence ID: ER-20260821-pevny-03
Source: wiki/papers/methodology/2016-Pevny-神经网络形式化求解多示例问题.md
Source type: preprint（arXiv v3；原件未标注会议；同作者树结构论文引用其为 "In submission to ECML 2016"）
原件: raw/papers/methodology/multiple-instance/2016-Pevny-Neural-Network-Formalism-Multiple-Instance.pdf（SHA-256 f1943e15…f5b8，8 页）
证据等级: E3 / D1（D1 出处：机制替换审计 notes.md 第 112 行）
关键位置: 第 3 页公式(1)(2)嵌入空间形式化（φ_i(b)=g({k(x,θ_i)})）；第 3–4 页图 1 网络化（池化置于网络内部，袋标签反向传播训练实例嵌入）；第 4 页池化选择准则（袋标签取决于单实例→最大池化；取决于整体分布→均值池化）；第 5–6 页图 2 与表 1（20 基准平均排名 4.3）
Supports: 仅支持一个设计部件——S1 头部输入摘要的**池化算子选择**：均值与最大二者语义互补（整体分布偏移对稀疏关键流），支持 r_t=[均值;最大] 拼接作为首轮无参数摘要
Contradicts: 无
Limitation: 20 个小型通用 MIL 基准，无安全数据、无漂移；对比数字取自他人发表结果（作者自承「并非所有方法都被调到最佳」，第 7 页）；高维小样本上明显过拟合（Newsgroups/Web，表 1）
Claim strength: supported（形式化与选择准则，在其基准上）/ speculative（对本课题）
为什么仍为 D 级机制启发: 只提供「池化形式化与算子选择准则」单一部件；其袋级监督训练的是实例嵌入，本课题 S1 恰恰冻结嵌入只训头，结构并不同构；无流量证据
禁止外推: 不得把「单层 ReLU＋均值池化排名第一」写成「序列建模不如均值」或「本课题均值+最大必然有信号」；不得据其把 S1 扩成端到端训练（那是 S2 的事）
```

### 3.4 MIDAM（Zhu 等，ICML 2023）

```md
## Evidence Record
Evidence ID: ER-20260821-midam-04
Source: wiki/papers/methodology/multiple-instance/2023-Zhu-MIDAM随机池化.md
Source type: full paper
原件: raw/papers/methodology/multiple-instance/2023-Zhu-MIDAM-Stochastic-Pooling-ICML.pdf（SHA-256 3b0b6d17…7e87，23 物理页，PMLR 202:43205–43227）
证据等级: E3 / D2（D2 出处：机制替换审计 notes.md 第 112 行「MIDAM 最高同构 D2」）
关键位置: 第 3 页公式(1)平滑最大/均值/注意力池化；第 4 页随机小包代入非线性池化产生不可忽略偏差；第 4–5 页公式(7)(8)逐包移动状态；第 5 页算法 1；第 6 页定理 1 驻点复杂度
Supports: 仅支持一个设计部件——S1/S2 的**训练目标粒度**：完整袋（实体）目标与随机片段池化不得混同；支持「S1 只在完整 LSPR23 训练实体的终端摘要 r_{n_e} 上训练，不把长度 128 片段标签冒充完整实体目标」
Contradicts: 把旧 ELP 的片段级监督结果直接解释为完整实体目标的能力上限（MIDAM 把这类差异定性为可测的优化偏差，不是容量不足）
Limitation: 优化目标是 AUROC 极小极大，不是实体 AP；未使用实体均匀测度或 Horvitz–Thompson 权重；实验非流量数据
Claim strength: supported（随机片段偏差与状态修正，在其设定下）/ speculative（对本课题）
为什么仍为 D 级机制启发: 覆盖「大袋随机池化＋偏差跟踪」多个关系，但其目标（AUROC）、其修正机制（逐包移动状态）都不是本课题采用物；本课题只借「目标粒度不得混同」这一负面边界
禁止外推: 不得声称本课题「首次解决随机大袋反向传播」；不得写「随机抽 K 流等于完整实体训练」；因果跨流编码下先抽流再重编码是否改变有限总体值，仍是实验待证（笔记「实验待证」条）
```

### 3.5 Recon（Shi 等，ICLR 2023）

```md
## Evidence Record
Evidence ID: ER-20260821-recon-05
Source: wiki/papers/manifold/Recon从结构根源减少梯度冲突.md
Source type: full paper（PDF 为同题同作者 arXiv 原件；OpenReview 下载 403，会议元数据经 OpenReview 页面核对——见笔记「访问说明」）
原件: raw/papers/manifold/Recon-ICLR2023.pdf（20 页；笔记 YAML 未登记 SHA-256，该项在原文笔记中未找到）
证据等级: E3 / D1（D1 出处：机制替换审计 notes.md 第 123 行「E3/D1」）
关键位置: PDF 第 4–5 页层级 S-conflict 分数定义与算法 1（短期预训练测冲突→高冲突层任务专用化→从头训练）；第 6 页理论边界（仅一次梯度更新的条件性保证）；第 7 页参数增量 0.52%–57.25%；第 9 页表 6（专用化后严重冲突降 67%–79%，随机隔离不可复现）
Supports: 仅支持一个设计部件——S2 的**诊断可观测量**：分层梯度余弦/严重冲突率只作诊断记录，不作选择器；若冲突集中在小型头部，优先隔离头部而非改骨干（与 S1 头部隔离方向一致，但 S1 的隔离依据是本课题合同，不是 Recon 结论）
Contradicts: 「梯度余弦<0 即须干预」的裁决用法（其与 ForkMerge Finding 1 同向）
Limitation: 结构专用化需额外短期训练与从头重训；参数增量上界大（57.25%）；无流量数据；未报告统一墙钟
Claim strength: supported（结构根源诊断，在其基准上）/ speculative（对本课题）
为什么仍为 D 级机制启发: 只提供「分层冲突诊断」单一部件；其修复动作（复制高冲突层为任务专用）本轮不采用，本课题已冻结「梯度余弦只作诊断」（task_plan 第 38 行）
禁止外推: 不得把梯度余弦诊断值写进任何通过/否决门；不得据其在 S2 失败后追加「复制骨干层」的补救候选（那属于新机制，须重开分级合同流程）
```

## 四、本课题已证病灶与实测数值登记（阶段三/四引用源）

以下数值全部来自本仓库既有制品与冻结文档，登记出处行号（本会话 `rg` 实测命中）：

| 数值 | 值 | 出处 | 本会话核验命令 |
| --- | --- | --- | --- |
| LSPR23 前 0.1% 实体占流/占正例 | `76.40%` / `94.43%` | `RWKV路线总控.md` 第 35 行 | `rg -n "76\.40\|94\.43" .Codex/docs/RWKV/RWKV路线总控.md` |
| LSPR23 规模 | `16,353,511` 流、`150,680` 实体、`239` 恶意实体 | 同上第 35 行 | 同上 |
| LSPR24 规模 | `20,227,356` 流、`47,115` 实体、`752` 正实体、`46,363` 负实体 | 总控第 35 行；N-16 计划 §2.1 | `rg -n "46,363" .Codex/docs/RWKV/2026-08-21-共同实际首次告警FP预算包络实施计划.md` |
| N11（B10 逐流概率完整幂平均）源年实体 AP 变化 | `−0.1152223438` | 候选与快速实验.md 第 173 行 | `rg -n "0\.1152223438" …/候选与快速实验.md` |
| O11 相对 B10 源年：逐流 AP / 设计算子实体 AP / 最大实体 AP | `−0.0002445091` / `−0.0106985012` / `+0.0534795842` | 同上第 32 行 | `rg -n "0\.0534795842" …` |
| O11 相对 B10 目标年：逐流 AP / 实体 AP / 0–8% 阶梯面积 | `−0.0072559665` / `+0.1379661595` / `+0.0908758979` | 同上第 33 行 | 已在 Read 全文中逐字核对 |
| O11 名义 4% 终端最优可达 DR 与实际 FPR | `0.7898936170` @ `0.0372063930`，下一可达点跳至 FPR=1 | 同上第 38–39 行 | 同上 |
| O11 名义 4% 首次告警实际 FPR | `0.7905010461` | 同上第 40 行；恢复卡 §八.5 | `rg -n "0\.7905010461" …` |
| S1 头部参数量 | `2d+1`（`d` 须实施时从冻结 B10 配置机械读取，本轮不发明数值） | 候选与快速实验.md §5.1 | Read 全文核对 |
| S2 epoch 边界 | 每轮最多 `1000` 步、共 `20` 轮（既有全容量 MLP 训练合同） | 候选与快速实验.md §6.3 | Read 全文核对 |
| 六档预算与 LSPR24 公共整数 FP | `0.1/0.5/1/2/4/8%` → `k=46/231/463/927/1854/3709` | N-16 计划 §2.4 | Read 全文核对 |

## 五、纪律自查

- 五篇均有 `raw/` 原件与 `wiki/` 结构化全文笔记，无摘要冒充全文；Recon 的 SHA-256 在其笔记中未登记，如实标注「该项在原文笔记中未找到」，不补造。
- 五篇证据等级全部沿用既有审计的 E/D 判定并给出出处行号，未新造分级。
- 文献只登记「支持哪个部件＋禁止外推」，未写任何「本课题有效」结论；有效性一律待 S1/S2 实验。
- 本笔记未修改任何既有文件；检索索引未重建（理由见 §一）。
