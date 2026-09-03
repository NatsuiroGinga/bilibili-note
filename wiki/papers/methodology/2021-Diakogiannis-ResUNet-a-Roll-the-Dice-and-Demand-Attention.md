---
title: "Looking for change? Roll the Dice and demand Attention"
authors: [Foivos I. Diakogiannis, François Waldner, Peter Caccetta]
year: 2021
date: 2026-09-03
journal: "Remote Sensing (MDPI)，2021，13(18):3707，DOI: 10.3390/rs13183707（Crossref 核验：published-online 2021-09-16）；预印本 arXiv:2009.02062v2 [cs.CV]，2021-03-23 修订（v1 提交于 2020-09-04）"
source_pdf: "[[raw/papers/methodology/2021-Diakogiannis-ResUNet-a-Roll-the-Dice-and-Demand-Attention.pdf]]"
sha256: "42a20f850e4b841098b19f6e8bb84c1d459392b092f8c0ae1fadf221a409b81c"
arxiv_id: "2009.02062v2"
tags:
  - 模型选择
  - 帕累托前沿
  - 检查点集成
  - 遥感变化检测
  - 语义分割
  - 类型/论文
key_finding: "第 7.5.2 节（物理第 12–13 页）：训练进入最后一次学习率下降后的稳定区间时，验证集 MCC 与分形 Tanimoto 相似度 ⟨FT⟩^d 两个指标经常对「哪个 epoch 最好」意见不一致；作者不挑单一 epoch，而是取二者的帕累托非支配前沿，把前沿上全部 checkpoint 的推理输出取平均（test-time 集成），从而回避了「前沿多点时如何打破平局」这一问题——不是给出平局规则，而是不需要平局规则。"
method: "mantis 系列骨干（CEECNet V1/V2、FracTAL ResNet，深度 6、初始滤波器数 32，记为 D6nf32）+ 新分形 Tanimoto 相似度损失（可调深度 d 逐步加深）+ 新注意力层 FracTAL；在 LEVIRCD 与 WHU 两个建筑物变化检测数据集上训练，验证阶段同时监控 MCC 与 ⟨FT⟩^d，末段学习率下降后按二者求非支配前沿，取前沿全部 checkpoint 的推理输出均值。"
baseline: "对比对象是自身的 CBAM 注意力变体、标准 ResNet V2 模块与 FracTAL 模块的消融（第 8 节），以及与 LEVIRCD、WHU 数据集官方或同期基线在 F1/IoU 指标上的比较（摘要报告 LEVIRCD F1=0.918/IoU=0.848，WHU F1=0.938/IoU=0.882）；7.5.2 节的选轮方法本身没有消融对照组。"
aliases:
  - Diakogiannis2021-RollTheDice
  - ResUNet-a-Roll-the-Dice-and-demand-Attention
  - mantis-CEECNet
related:
  - "[[2026-Apicella-重思模型参数选择的验证准则]]"
  - "[[2025-Rubachev-TabReD工业级时间切分表格基准]]"
  - "[[../attack-detection/2026-Berruz-漂移检测触发自适应重训|Berruz2026-漂移检测触发自适应重训]]"
---

# Looking for change? Roll the Dice and demand Attention

> Diakogiannis, Waldner, Caccetta，Remote Sensing (MDPI) 2021, 13(18):3707 · arXiv:2009.02062v2 · 28 页（正文 20 页 + 参考文献）

## 入库缘由

本课题 `thesis/methods/多指标选轮与帕累托核查.md`（2026-09-03）在核查"训练轮次上按多指标做帕累托选轮"是否有文献先例时，找到本文第 7.5.2 节是唯一直接先例，但当时只完成在线全文核验（ar5iv HTML），未入库，按仓库规则不得进入正文。本笔记完成 `raw/` 原件下载与本地全文核验，把该引用的证据等级从"在线全文核验"升级为"本地全文"。

## 一句话

作者在做遥感建筑物变化检测时观察到验证集 MCC 与分形 Tanimoto 相似度这两个指标在训练末段经常对"哪个 epoch 最好"意见不一致，于是不挑单一 epoch，而是取两指标的帕累托非支配前沿（图 9 示例中恰好两个点），把前沿上全部 checkpoint 的推理输出取平均作为最终预测——用"全部前沿点做集成"替代了"从前沿中挑一个点"，从而不需要任何打破平局的规则。

## 题录

- 题名（逐字抄自 PDF 第 1 页）：Looking for change? Roll the Dice and demand Attention
- 作者：Foivos I. Diakogiannis（ICRAR/UWA、CSIRO Data61）、François Waldner（CSIRO Agriculture & Food）、Peter Caccetta（CSIRO Data61）
- 正式出版：*Remote Sensing* (MDPI) 2021, 13(18), 3707；DOI `10.3390/rs13183707`（Crossref API 核验：`container-title=Remote Sensing`、`volume=13`、`issue=18`、`page=3707`、`published-online=2021-09-16`）
- 预印本：arXiv:2009.02062，v1 提交 2020-09-04，v2 修订 2021-03-23（本笔记核验的原件即 v2，PDF 元数据 `CreationDate: 2021-03-24`）
- 原件：`raw/papers/methodology/2021-Diakogiannis-ResUNet-a-Roll-the-Dice-and-Demand-Attention.pdf`（`sha256:42a20f85…`，28 页）
- 全文转换：`wiki/papers/methodology/2021-Diakogiannis-ResUNet-a-Roll-the-Dice-and-Demand-Attention-全文.md`（`tools/pdf_to_fulltext.sh` / MinerU `extract`，机械转换，非本笔记）

**核查记录（供交叉核对文献年份）**：本课题 `thesis/methods/多指标选轮与帕累托核查.md` 第 260、595 行把本文引用年份写作"2020"、期刊写作"ISPRS P&RS"，与 Crossref 核验结果（正式发表 2021 年、期刊为 *Remote Sensing*（MDPI），非 ISPRS 期刊）不一致。按本次入库任务的授权范围（"只改证据等级与路径，不改任何结论"），该处笔误未在本笔记范围内修正，仅在此如实记录供后续更正参考。

## 核心方法（论文整体）

- 任务：双时相高分辨率航拍影像的语义变化检测（建筑物变化），非本课题的加密流量二分类检测。
- 骨干（第 6 节，物理第 8–10 页）：mantis 系列——CEECNet V1/V2（同时"总览"与"细节"两条支路 + 相对注意力融合）、FracTAL ResNet；深度编码器为 6 层、初始滤波器数 32，记为 D6nf32。
- 损失函数：新的分形 Tanimoto 相似度（Fractal Tanimoto，⟨FT⟩^d），深度 d 可调，训练中随学习率下降逐步加深（第 4 节，物理第 4–6 页式 8 附近）。
- 数据集（第 7.1–7.2 节，物理第 10–11 页）：LEVIRCD（637 对 0.5 m 分辨率航拍图，31,333 处建筑变化）；WHU（2011/2016 两期 0.3 m 分辨率航拍图，约 20 km²，12,796 栋建筑，训练/验证/测试按空间分离的 33:37:30 切分，见图 8）。
- 评价指标（第 7.4 节，物理第 12 页）：像素级 precision、recall、F1、MCC（Matthews Correlation Coefficient）、IoU；除 IoU 外均用 `pycm` 库计算。
- 主结果（摘要）：LEVIRCD F1=0.918、IoU=0.848；WHU F1=0.938、IoU=0.882。

## 7.5.2 节：帕累托选轮方法的完整核验

**位置**：第 7.5 节"Inference"的第二个子节，标题"7.5.2. Model selection using Pareto efficiency"，**物理页码第 12 页起始，正文延伸到第 13 页**（图 9 的图注与紧随的一段说明文字落在第 13 页顶部；PDF 页脚数字与 MinerU 转换稿逐字核对一致）。全文转换稿对应行号：`wiki/papers/methodology/2021-Diakogiannis-ResUNet-a-Roll-the-Dice-and-Demand-Attention-全文.md` 第 365–369 行。

### 用哪两个指标

验证集 **MCC**（Matthews 相关系数）与**分形 Tanimoto 相似度 ⟨FT⟩^d**（本文自定义的损失/相似度指标，取 d=30 时的取值，即训练末段使用的损失深度）。原文（逐字，物理第 12 页）：

> "For monitoring the performance of our modelling approach, we usually rely on the MCC metric on the validation dataset. We observed, however, that when we perform simultaneously learning rate reduction and ⟨FT⟩^d depth increase, initially the MCC decreases (indicating performance drop), while the ⟨FT⟩^d similarity is (initially) strictly increasing. After training starts to stabilize around some optimality region (with the standard noise oscillations), there are various cases where the MCC metric and ⟨FT⟩^d similarity coefficient do not agree on which is the best model."

### 前沿求在什么范围上（不是全程训练轨迹）

**关键细节，本课题现有笔记（`多指标选轮与帕累托核查.md`）未记录**：帕累托前沿不是在整个训练轨迹的所有 epoch 上求，而是**限定在"最后一次学习率下降之后"的稳定区间**。图 9 标题逐字：

> "Figure 9: Pareto front selection **after the last reduction of learning rate**."

这与本课题 C01-half 的实测做法（在完整 10 轮训练轨迹上求非支配集）不同——本文的前沿候选池本身经过了"只看末段稳定区间"的预筛选，而非对全部训练历史求非支配集。

### 非支配前沿有几个点

原文没有给出前沿点数的一般性规律或理论上界；**具体展示的实例（图 9，WHU 数据集）恰好只有两个非支配点**。原文逐字（图 9 图注，物理第 12–13 页）：

> "The bottom panel designates with **open cyan circles the two points** that are equivalent in terms of quality prediction when both MCC and ⟨FT⟩ are taken into account... The two circles show the corresponding nondominated Pareto solutions (i.e. best candidates)."

正文另有一句泛化表述"a **set** of best candidate models"（不限定为二），但全文只展示了 WHU 这一个具体前沿实例，**未披露 LEVIRCD 数据集前沿的点数**，也未讨论前沿点数一般会是多少、是否有上界。

### 多点时怎么打破平局——本次核查的核心问题

**原文的答案是：不打破平局，因为它不需要从前沿中选出唯一点。** 逐字原文（物理第 12 页，紧接上一段）：

> "To account for this effect and avoid losing good candidate solutions, **we evaluate the average of the inference output of a set of best candidate models**. These best candidate models are selected according to the models that belong to the Pareto front of the most evolved solutions. **We use all the Pareto front (Emmerich and Deutz, 2018) model weights as acceptable solutions for inference.**"

即：作者把"前沿给出多个候选、无法从中选出单一最优"这一困难**重新定义掉**了——前沿上的每一个 checkpoint 都被判定为"可接受解"（acceptable solution），全部拿去做推理，再对**推理输出**（每个像素的 softmax 概率）取平均，等价于一次**测试时（test-time）checkpoint 集成**，而不是模型权重层面的平均。全文没有出现任何形式的"从前沿中选一个代表点"的规则（如取中位点、取某个指标最优的前沿点等），因为该规则本身在本文的设计里是不必要的。

**同时原文披露了一处方法论的沿用关系**：这个"前沿 checkpoint 集成"的做法此前已被作者自己用于超参数选择，原文引用了另一篇作者自己的工作："A similar approach was followed for the selection of hyper parameters for optimal solutions in Waldner and Diakogiannis (2020)."（该文献本次入库未追加核验，只记录引用关系，不作为本课题的独立证据来源。）

### 原文未披露的部分（如实标注，不推测补全）

- **前沿点数超过 2 时是否有额外规则**：未披露。原文正文用"a set of best candidate models"这一不限定基数的表述，图示实例恰好是 2 点，无法判断作者是否遇到过前沿点数更多（如本课题实测的情形）的情况、以及若遇到是否会改变处理方式。
- **计算复杂度/推理成本随前沿点数增长的处理**：未披露。取全部前沿点做推理均值意味着推理成本与前沿规模成正比，原文未讨论前沿点数较多时的取舍或截断策略。
- **前沿求解的具体算法实现**：仅引用 Emmerich and Deutz (2018) 作为"Pareto front"概念的定义来源，未给出本文实际使用的非支配排序算法细节（如是否用现成库、复杂度）。
- **LEVIRCD 数据集上前沿的具体点数与集成规模**：未披露，只有 WHU 数据集给出图示（2 点）。

## 与本课题的差异

| 维度 | 本文（Diakogiannis 2021） | 本课题（`多指标选轮与帕累托核查.md`） |
| --- | --- | --- |
| 任务 | 遥感双时相语义分割（变化检测），像素级多类输出 | 加密流量二分类检测，逐流 + 实体级聚合 |
| 前沿求解范围 | 仅末段（最后一次学习率下降之后）的稳定区间 | 整个训练轨迹（C01-half 全部 10 轮） |
| 用哪两个指标 | 验证集 MCC × 分形 Tanimoto 相似度 ⟨FT⟩^d（同一任务的两种"质量"打分，均连续） | 实体 AP × 逐流 AP（不同聚合粒度的排序型指标） |
| 前沿点数（已知实例） | WHU 数据集图示恰好 **2 点**；LEVIRCD 未披露 | C01-half 十轮筛选运行实测为 **{8, 10} 共 2 点**（`(实体 AP, 逐流 AP)` 与三维、双实体维度下均一致） |
| 前沿多点时的处置 | **不选点，全部前沿 checkpoint 做推理输出均值（测试时集成）** | 尚未采纳集成路线；核查报告推荐方案 A（维持单一主指标选轮），否决方案 B（帕累托前沿+集成，即本文这条路线） |
| 是否给出可部署的单一模型 | **否**——最终交付物是"若干 checkpoint 推理输出的均值"这一集成系统，仍是"一个系统、一组数字"，但不对应单个权重文件 | 是——冻结合同要求"一个格 = 一个模型"，正文每行数字须能对应唯一可复现的权重文件 |

**两点核对，与本课题 `多指标选轮与帕累托核查.md` 第 2.2 节、第 260 行的既有记录一致**（本次全文核验未推翻该记录，只是补齐了页码、逐字原文与"末段窗口"这一此前遗漏的细节）：

1. 本文确实是"训练轮次上用多指标求帕累托前沿"的先例，但其处置方式是**折叠成集成**，不产出"多个指标各自对应一个汇报模型"的结果，因此不能作为本课题"三口径三检查点"做法的先例。
2. 本文没有解决"前沿不给出唯一点"这一问题，而是绕开了它——集成路线在本课题被否决的理由（四格须重训、`+36.25%` 判据结果作废、实测前沿仅 2 点收益不可辨识）与本文的方法本身是否有效无关，纯粹是本课题的工程代价核算。

## 疑问·待验证

- 若前沿点数显著多于 2（例如本课题若在更长训练轨迹或更细粒度指标下可能出现的情形），"全部前沿 checkpoint 做推理均值"的推理成本与集成收益是否仍然合算？原文未讨论，本课题也未实测（C01-half 前沿恰好也只有 2 点，无法用现有制品验证多点场景）。
- "仅末段稳定区间求前沿"与本课题"全轨迹求前沿"这两种范围选择对前沿点数、点的分散程度有何影响？原文未与"全轨迹前沿"做对照实验，本课题也未做这一维度的消融。

## 证据记录

- 来源类型：完整论文全文（28 页，含参考文献；7.5.2 节及其前后文逐段核对；已用 `rg -a` 对全文核对 "Pareto"/"front"/"non-dominated"/"average" 相关表述，无遗漏关键段落）。
- 支持：本文确系"训练轮次层面按多指标做帕累托选轮"的可考先例；其处置方式是折叠为测试时集成而非选出单点；前沿求解范围限定在末段学习率下降之后。
- 限制：领域为遥感语义分割，非本课题的加密流量检测；前沿点数唯一披露实例仅 2 点；未讨论前沿点数更多时的处理与推理成本权衡。
- 论断强度：有支持（7.5.2 节方法本身，原文逐字核验）／推论（该方法迁移到本课题场景下的可行性与代价，未经本课题实验验证）。

## 可引用的逐字原文（每条 ≤15 词）

- "we evaluate the average of the inference output of a set of best candidate models"（物理第 12 页）
- "We use all the Pareto front... model weights as acceptable solutions for inference"（物理第 12 页）
- "Pareto front selection after the last reduction of learning rate"（图 9 图注，物理第 12 页）
