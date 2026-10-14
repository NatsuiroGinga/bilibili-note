# 对抗 × 漂移联合框架查证报告（四问）

> 2026-10-14。**由查证子代理撰写，主代理转存**（该代理无 Bash 工具，harness 拦截其写报告类文件）。
> 同目录另有该代理产出的 `task_plan.md`、`notes.md`、`evidence-index.md`（18 条证据台账），均已提交。

## 四问一句话结论

### Q1（联合工作是否存在）——**A 类：已有人联合，但形态不是最坏情形联合框架**

- **防御侧**：**Şandor, Portase, Coleşa, IEEE ICCP 2024**（DOI `10.1109/ICCP63557.2024.10793037`，
  OpenAlex 摘要直核：「combining feature engineering and adversarial training … generating training
  data mutations … maintaining high performance over time」，被引 1，**全文未取得**）。
- **攻击侧**：**TAH-GAN 2026 预印本**（DOI `10.21203/rs.3.rs-10821022/v1`，Crossref 摘要直核：
  time-aware GAN 做「drift-aware robustness assessment」，评估在 KronoDroid/AndroMD）。
- **两篇均未构造「输入扰动 × 时间切片」的统一最坏情形集合。**
- 分开做的证据充分：漂移侧（MADCAT / Barbero / MORPH / CITADEL 等）、对抗侧（PAD / DeepTrust / ELSA-RAMD 等）。

### Q2（PAD 2023 占了什么）——**占的是「固定数据分布上、扰动球内的对抗训练优化收敛保证」，不涉及分布漂移**

- Li et al., **TDSC 2023**, DOI `10.1109/tdsc.2023.3265665`（**OpenAlex 直核 ＋ 本地制品
  `raw-queries/openalex/abs_PAD.json` 早已存在**；arXiv `2302.11328v2` 全文已核）。
- 白盒规避威胁模型（§III-A）、box 约束特征空间混合梯度攻击 SMA（**非 norm 球**）、
  数据集 Drebin+Malscan、**Theorem 2 收敛率 `O(1/√N)`**。
- **全文 `rg`「concept drift / temporal / distribution shift / time-evolv」零命中。**
- **本地综述「已占收敛保证」成立**；但它的最坏情形对象与「扰动 × 时间切片」联合最坏情形**是不同对象**，
  差异化空间存在。

### Q3（二值静态特征上的特征空间攻击是否可实施）——**可实施、被接受、已制度化——前提是带可实现性约束**

关键页码（Cortellazzi/Pierazzi, S&P 2020, arXiv `1911.02142v3`，本地有 36 页全文笔记）：

- 四类约束定义（8–12）**p.7–8**
- 特征空间 → 问题空间投影的**置信度单调下降** **p.9**
- **Android 可行性规则「最多新增 1 个权限、不新增危险权限」＋注入真实良性字节码切片** **p.15 / p.13**
- `0→1`（新增）可实现；`1→0`（删除）**受语义依赖约束**（PAD §III-B：「side-effect features incur
  interdependent perturbations … preserve the functionality or semantics」）
- **「删除不存在的权限不可实现」是文献推论，未检索到逐字表述**（标为推论）

**接受度证据**：PAD 用 Drebin（TDSC，被引 40）；**ELSA-RAMD / SaTML 2025 把 DREBIN 二值特征的
特征空间攻击设为正式竞赛赛道**（DeepTrust, arXiv `2510.12310` 全文核）；Zainab arXiv `2609.34456`
实测可执行性约束使攻击 ASR 大降。

### Q4（LAMDA 上有无对抗评价）——**未发现（2026-10-14 可检索面）**

检索途径：本地两份 LAMDA 笔记 `rg -i adversar` **双零命中** ＋ Zotero 无该类条目 ＋
**S2 被引 14 条逐条判读** ＋ 唯一对抗向引用 **DeepTrust 全文 `rg LAMDA` 零命中**
（其对抗实验在 ELSA-RAMD，DREBIN 特征 `d=1,461,078`）。

## C4 判定（三选一）

**「可做」，但带两个前提**：最坏情形联合框架（扰动 × 时间切片）**无直接占据者**——
PAD 占的是固定分布下的优化收敛保证、Şandor 是数据变异、TAH-GAN 是生成器评价面；
**攻击面不构成不可实施障碍**（Q3：带可实现性约束的二值特征攻击是成熟且被制度化接受的做法）。

**两个前提**：
1. 攻击必须按 Cortellazzi 四约束（**p.7–8**）做可实现性限制，否则会被判不可实施；
2. 须与 Şandor ICCP 2024 / TAH-GAN 显式差异化（**形态差异清晰：它们不是最坏情形联合**）。

## 最大不确定

1. **Şandor ICCP 2024 全文未取得**（IEEE 挡、无 OA 副本）——是否真正构造联合最坏情形只有摘要级证据，
   标**待验证**；若它实际做了联合最坏情形，C4 的差异化空间会收窄。
2. TAH-GAN 是预印本且未取得全文，「time-aware」强度待核。
3. 「删除不存在的权限不可实现」无逐字文献表述，只能作**推论**引用。
4. Q4「未发现」只覆盖当日可检索面（LAMDA 为 2026 新基准，预印本渠道可能有滞后）。

## 过程留档（**防复发**）

本任务中段该代理据「Crossref 404 ＋ Scholar 零命中 ＋ IEEE 被挡」**误判 PAD「查无实据」**，
主代理核出真 DOI（`10.1109/tdsc.2023.3265665`）并指出**本地 `raw-queries/` 早已有记录**后推翻。
教训已写入其 `notes.md`：

> **404 只证明该 DOI 不存在；工具失败叠加 ≠ 来源不存在；
> 下「不存在」结论前先 `rg` 本地 `raw-queries/` 与 `wiki/`，再用 OpenAlex 直连
> （不要走代理，代理会 429）复核。**
