# 过程笔记：ATk / SoRR 入库与差异核对

## 进度

| 时刻 | 事项 | 状态 |
| --- | --- | --- |
| T1 | arXiv 题录核验（两篇均 v2） | 完成 |
| T1 | 原件下载入 `raw/papers/methodology/ranking/` | 完成，提交 `8e17f76` |
| T2 | `mineru-open-api extract -f json`，按 `page_idx` 重排带物理页标记 | 完成，同一提交 |
| T5 | 五问全文核对（读毕 ATk 全 18 页要点、SoRR 第 2–6 节） | 完成 |
| T6 | 「Hu 2023」引用核实（含物理页 8 单页提取核验） | 完成，见下 |
| T3 | 两份结构化笔记＋FCCO 笔记证据记录补充 | 完成，提交 `8412b86` |
| T4 | `INDEX.md` 新增「顶-k 与排序区间聚合损失」小节 | 完成，同一提交 |
| T5 | `核对报告.md` | 完成 |

自检：三份笔记 frontmatter 必填字段齐全、均含 `类型/论文` 标签与「不可直接声称」小节；
`wiki/papers/methodology/` 下 wikilink 无断链（脚本实测）。

## 题录（联网核验，2026-09-01）

- **ATk**：Yanbo Fan, Siwei Lyu, Yiming Ying, Bao-Gang Hu，*Learning with Average Top-k Loss*，
  NeurIPS 2017。arXiv:1705.08826v2，18 物理页，SHA-256 `72312fbf…7027`。
- **SoRR**：Shu Hu, Yiming Ying, Xin Wang, Siwei Lyu，*Sum of Ranked Range Loss for
  Supervised Learning*，**JMLR 接收**（arXiv 注释原文：`Accepted by Journal of Machine
  Learning Research (JMLR)`），arXiv:2106.03300v2，44 物理页，SHA-256 `37e1dc5e…0be6`。
  arXiv 同时注明与 arXiv:2010.01741（NeurIPS 2020 会议版）文本重叠，本次入库的是期刊扩展版。

## 关键页码台账（全部来自 `extract` 输出，非 `pdftotext`）

### ATk（arXiv:1705.08826v2）

| 位置 | 内容 |
| --- | --- |
| 物理页 2 | 式(1) `L_avt-k(L_z(f)) = (1/k) Σ_{i=1}^{k} ℓ_[i](f)`；`k=n`→均值损失，`k=1`→最大损失 |
| 物理页 3 | 式(2) 变分形式 `∝ min_{λ≥0}{ (1/n)Σ[ℓ_i−λ]_+ + (k/n)λ }`；引理 1 |
| 物理页 4 | 式(3) 参数化目标；式(4) SGD；式(5)(6) ATk-SVM，`k=n`→C-SVM，`ν=k/n`→ν-SVM；**「Choosing k」段：k 为整数，验证集网格搜索** |
| 物理页 5 | 式(7) 总体形式，`k/n → ν`；**定理 1**：`ν > E*_ℓ` ⟹ 分类校准；必要条件 `ν ≥ ∫min(η,1−η)`，给出 k 的**下界** `k > n E*_ℓ` |
| 物理页 6 | **定理 2**：ATk-SVM 超额误分类误差界，取 `k = ⌈n(E_h(f_H)+μ)⌉` |
| 物理页 6–8 | 实验：k 在 `[1,n]` 上 log10 网格由验证集选出 |
| 物理页 7 | 相关工作：自步学习＝average bottom-k |
| 物理页 8 | 相关工作：排序问题的 top 加权损失 [17,24] 是**互补的 individual loss**，「can be combined」——ATk 本身未与排序损失复合 |

**全文词频（`rg -ic`）**：`bag` 0、`multi-instance` 0、`multiple instance` 0、
`CVaR` 0、`AUC` 0、`pAUC` 0、`partial area` 0；`rank`/`ranking` 各 4，仅出现在相关工作。

### SoRR（arXiv:2106.03300v2）

| 位置 | 内容 |
| --- | --- |
| 物理页 4–5 | 第 2 节相关工作；物理页 5 明确 Rawat 2020 双随机挖掘「在样本级与标签级同时用 average top-k」 |
| 物理页 5 | SoRR 定义：`ψ_{m,k}(S)=Σ_{i=m+1}^{k} s_[i]`，AoRR=`(1/(k−m))ψ_{m,k}`，**k、m 为整数**，`0 ≤ m < k ≤ n` |
| 物理页 6 | **定理 1** 式(1) DC 分解 |
| 物理页 7 | 式(2) 随机次梯度；式(3) `φ_m` 次梯度 |
| 物理页 8–9 | 3.1 与双层优化的联系（`q_i∈{0,1}`, `‖q‖_0=n−m`） |
| 物理页 10 | 第 4 节 `L_aorr(S(θ)) = (1/(k−m)) Σ_{i=m+1}^{k} s_[i](θ)`，`S(θ)={s_i(θ)}_{i=1}^n`，n＝训练样本总数；**明列 ATk 为 `m=0` 特例** |
| 物理页 11 | 式(6) 双阈值 min-max 形式；个体样本级解释（减 λ、上截 λ̂） |
| 物理页 12 | 4.1 校准；式(7) 总体极限 `k/n→ν, m/n→μ` |
| 物理页 13 | 式(8) 总体 min-max；**定理 4**：`0 ≤ λ* < λ̂*` ⟹ 校准；**`k ≤ m` 时校准不成立**。4.2：明写 average-top-k 对应 **CVaR at level `α = k/n`**；式(9) `L = ν C_ν[s] − μ C_μ[s]`（ICVaRs） |
| 物理页 14 | 式(10) 经验 ICVaRs；**定理 5** 偏差界 `(b−a)[√(5k ln(3/δ)/n²) + √(ln(1/δ)/2n)]`；明确「AoRR 超额泛化与目标分类问题的非渐近关系很难建立，留作未来工作」 |
| 物理页 14–15 | **4.3 Determine k and m**：贪心搜索；或按**训练准确率**触发的自适应比例表 `k=n → ⌊n/2⌋(≥70%) → ⌊n/4⌋(≥80%) → ⌊n/8⌋(≥90%) → ⌊n/16⌋(≥95%) → ⌊n/32⌋(≥99.5%)`（引 Kawaguchi & Lu 2020）；或用干净验证集直接学 λ、λ̂ 代替定 k、m |
| 物理页 22 | 第 5 节 TKML：`s_j(θ)=[1+θ_j^T x − min_{y∈Y}θ_y^T x]_+`，`ψ_{k,k+1}(S)=s_[k+1]`，标签级排序间隔 |
| 物理页 26 | 第 6 节：TKML（标签级）＋AoRR（样本级）复合；点名 Rawat 2020「ATk 于样本级、top-k 多类 SVM 于标签级」 |
| 物理页 27 | 式(11) `L_TKML-AoRR`；式(12) 三参数更新；`k'` 标签级、`k`/`m` 样本级 |

**全文词频（`rg -ic`）**：`bag` 0、`multi-instance` 0、`multiple instance` 0、
`AUC` 0、`pAUC` 0、`partial area` 0、`compositional` 0、`nested` 0、`coupled` 0；
`CVaR` 9、`bilevel` 9、`ranking` 12。

## 任务三：「Hu 2023」核实结论

- 可行性调研报告（**不在本 ch3 分支工作树**，位于 `codex/ch4-dtep-pbc-20260819`
  提交 `7a5cab0`）第 120–123 行原文是：「『袋级池化 ∘ 部分 AUC』的耦合复合优化（FCCO）
  由 Hu 等 2023 建立（物理页 8 式(8)–(9)……［全文核验，`2023-Hu-多示例双向部分AUC.md`］）」。
- 该笔记确实存在，但也只在 `codex/ch4-dtep-pbc-20260819`（提交 `00cc9b4`），
  本 ch3 分支工作树没有。其题名为 **Quanqi Hu, Dixian Zhu, Tianbao Yang,
  *Non-Smooth Weakly-Convex Finite-sum Coupled Compositional Optimization*,
  NeurIPS 2023, arXiv:2310.03234**。
- **结论：不是代理写错作者年份，是两篇不同的真实论文，且都属 FCCO 家族。**
  Wang 与 Yang 2022（ICML，PMLR v162）提出 FCCO 框架与 SOX；Hu 等 2023（NeurIPS）
  是同一资深作者 Tianbao Yang 的**非光滑弱凸扩展**，题名字面含
  “Finite-sum Coupled Compositional Optimization”。
- **盘点报告第 99–101 行的表述本身有误**：它把可行性报告读成「FCCO＝Hu 2023」，
  再与仓库里的 Wang 2022 对撞。可行性报告说的是「袋级池化 ∘ pAUC 这个 FCCO **实例**
  由 Hu 2023 建立」，指向的是另一篇，不是同一工作。
- 页码核验见下节。
