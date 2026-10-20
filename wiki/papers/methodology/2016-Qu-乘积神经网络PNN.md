---
title: "Product-based Neural Networks for User Response Prediction"
authors: [Yanru Qu, Han Cai, Kan Ren, Weinan Zhang, Yong Yu, Ying Wen, Jun Wang]
year: 2016
date: 2026-10-20
journal: "arXiv:1611.00144v1（2016-11-01）；文档所称 ICDM 2016 正式版未取得"
source_pdf: "[[raw/papers/methodology/2016-Qu-ProductBasedNeuralNetworks-PNN.pdf]]"
sha256: "d0dc3c685ddf4ff546fc38e1a3560b5de6f62aa1751439006a6a72514ba63cb4"
arxiv_id: "1611.00144v1"
zotero_item_key: "LR3KTQNA"
bibtex_key: "qu_productbased_2016"
tags:
  - 特征交互
  - 推荐系统
  - 稀疏二值特征
  - 乘积层
  - 类型/论文
key_finding: "PNN 在逐字段 one-hot 嵌入之上加入内积或外积乘积层：内积变体通过对交互权重矩阵做 Wp=θθ^T 的低秩分解，把二阶交互的时间与空间复杂度从 O(N²(D1+M)) 降到 O(D1MN)；外积变体用 fΣfΣ^T 叠加把复杂度从 O(D1M²N²) 降到 O(D1M(M+N))（物理第 3 页，Eq. 11–14）。"
method: "逐字段嵌入 → 线性信号 z 与二阶乘积信号 p 并行 → l1=relu(lz+lp+b1) → 两层全连接 → sigmoid；对比 IPNN、OPNN 与两者拼接的 PNN*"
baseline: "LR、FM、FNN、CCPM；数据集 Criteo 与 iPinYou"
aliases:
  - PNN
  - IPNN
  - OPNN
related:
  - "[[2018-Li-安卓恶意软件因子分解机]]"
---

# PNN：乘积神经网络

> Qu、Cai、Ren、Zhang、Yu、Wen、Wang，arXiv:1611.00144v1，6 个物理页。

## 一句话

PNN 把「字段级 one-hot 嵌入」之后的二阶交互显式写成乘积层：内积变体以低秩分解把交互权重降到线性参数与线性计算量，外积变体以 $f_\Sigma f_\Sigma^\top$ 叠加降低复杂度，再交给全连接层学习高阶模式。

## 题录与原件

- 题名与作者见物理第 1 页；arXiv 标识页边为 `arXiv:1611.00144v1 [cs.LG] 1 Nov 2016`。
- arXiv：<https://arxiv.org/abs/1611.00144>。
- 当前原件：Zotero 附件 `ETX7DZGA`，路径
  `/Users/bilibili/Zotero/storage/ETX7DZGA/Qu 等 - 2016 - Product-based Neural Networks for User Response Prediction.pdf`，共 6 页。
- **迁移状态**：本代理无 shell，未能把该 PDF 复制进 `raw/`，也未能计算 SHA-256。
  计划落点 `raw/papers/methodology/2016-Qu-Product-based-Neural-Networks.pdf`；主代理补齐后应改 `source_pdf` 并回填 `sha256`。
- Zotero 条目：`LR3KTQNA`（preprint，带 PDF）；库内另有历史重复条目 `9RFSEWUE`（无 PDF），需合并。
- 版本边界：本笔记只核验 **arXiv v1 预印本**。文档所称 ICDM 2016 正式版未取得，正式版与 v1 的差异未核验。

## 论文原方法（公式与页码锚点）

- 输入是多字段类别特征的逐字段 one-hot 拼接；每个字段独立连到嵌入层（物理第 3 页，Eq. 8）：
  $f_i = W_0^i\, x[\text{start}_i:\text{end}_i]$。
- 输出与隐层（物理第 2 页，Eq. 1–2）：
  $\hat y=\sigma(W_3 l_2+b_3)$，$l_2=\mathrm{relu}(W_2 l_1+b_2)$。
- 第一隐层同时接收线性信号 $l_z$ 与二阶信号 $l_p$（物理第 2 页，Eq. 3）：
  $l_1=\mathrm{relu}(l_z+l_p+b_1)$。
- 张量内积算子（物理第 2 页，Eq. 4）：$A\odot B\triangleq\sum_{i,j}A_{i,j}B_{i,j}$。
- 线性与二阶信号（物理第 2 页，Eq. 5；第 3 页 Eq. 6–7）：
  $l_z^n=W_z^n\odot z$，$l_p^n=W_p^n\odot p$；
  $z=(z_1,\dots,z_N)\triangleq(f_1,\dots,f_N)$；$p=\{p_{i,j}\}_{i,j=1..N}$，$p_{i,j}=g(f_i,f_j)$。
- 训练目标是 log loss（物理第 3 页，Eq. 9）。
- **IPNN**：$g(f_i,f_j)=\langle f_i,f_j\rangle$。直接实现时
  $l_1$ 空间复杂度 $O(D_1N(M+N))$、时间 $O(N^2(D_1+M))$（物理第 3 页）。
  引入分解假设 $W_p^n=\theta^n\theta^{n\top}$ 后有
  $W_p^n\odot p=\sum_i\sum_j\theta_i^n\theta_j^n\langle f_i,f_j\rangle=\langle\sum_i\delta_i^n,\sum_i\delta_i^n\rangle$，
  $l_p=(\|\sum_i\delta_i^1\|,\dots,\|\sum_i\delta_i^{D_1}\|)$（物理第 3 页，Eq. 11–12），
  空间与时间均降为 $O(D_1MN)$。
- 更一般的 K 阶分解为 $W_p^n\odot p=\sum_i\sum_j\langle\theta_i^n,\theta_j^n\rangle\langle f_i,f_j\rangle$，
  $\theta_i^n\in\mathbb R^K$，表达更强但复杂度增 K 倍（物理第 3 页，Eq. 13）。
- **OPNN**：$g(f_i,f_j)=f_i f_j^\top$，直接实现空间与时间均为 $O(D_1M^2N^2)$；
  用叠加 $p=\sum_i\sum_j f_i f_j^\top=f_\Sigma(f_\Sigma)^\top$、$f_\Sigma=\sum_i f_i$ 后降为 $O(D_1M(M+N))$（物理第 3 页，Eq. 14）。
- 论文自述的结构关系（物理第 4 页 §D）：去掉 $l_p$ 后 PNN 等同 FNN；在无隐层且输出层等权求和时，内积 PNN 等同 FM。

## 直接参数与协议

- 数据集（物理第 4 页）：Criteo 取连续 7 天训练、随后 1 天评价，负采样后 79.38M 实例、1.64M 维；
  iPinYou 10 天日志、每广告主最后 3 天测试，one-hot 后 19.50M 实例、937.67K 维。
- 训练：TensorFlow 实现，SGD；LR/FM 用 L2 正则，神经网络用 dropout，隐层默认 dropout 0.5（物理第 4 页）。
- 结构：每个 PNN 为 1 个嵌入层 + 1 个乘积层 + 3 个隐层，共 5 层；嵌入阶数与 FM 一致取 10（物理第 4 页）。
- 消融结论（物理第 5–6 页）：嵌入阶数比较 2/10/50/100，取 10；隐层数比较 1/3/5/7，3 层泛化较好；
  tanh 优于 sigmoid，ReLU 亦有良好表现。
- 主结果（物理第 5 页，表 I/II，AUC）：
  - Criteo：LR 71.48%、FM 72.20%、FNN 75.66%、CCPM 76.71%、IPNN 77.79%、OPNN 77.54%、PNN* 77.00%。
  - iPinYou：LR 73.43%、FM 75.52%、FNN 76.19%、CCPM 76.38%、IPNN 79.14%、OPNN 81.74%、PNN* 76.61%。
- 不一致项：iPinYou 上 OPNN 的 AUC 高于 IPNN，但 log loss（5.211e-3）与 RIG（1.349e-1）均劣于 IPNN（5.195e-3、1.376e-1，表 II）。
  PNN*（内积+外积拼接）在 AUC 上没有优于单变体（物理第 5 页正文）。

## 与本课题的关系（只写可迁移机制）

- **稀疏二值 → 逐字段嵌入**：对 one-hot 的每个活跃坐标只取一行嵌入，等价于可学习查找表；
  非活跃坐标不产生前向贡献，参数梯度也只在活跃坐标上出现。这与本课题 4561 维稀疏二值特征的输入形态同型。
- **显式二阶交互的参数化**：以 $\langle f_i,f_j\rangle$ 代替 $W_{ij}$，把交互参数从 $O(N^2)$ 降到 $O(NK)$，
  且不需要预先枚举坐标对；这是「共现结构显式参数化」的可迁移构件。
- **低秩分解降低计算量**：IPNN 的 $W_p=\theta\theta^\top$ 使计算对字段数线性；OPNN 的 $f_\Sigma f_\Sigma^\top$ 给出共享的 $M\times M$ 交互矩阵。
  两者都可作为「同预算下二阶层如何控制参数与计算」的实现选项。
- **线性旁路**：常数信号「1」保留 $l_z$，使乘积层不替代一阶项（物理第 3 页）。这是结构约束，不涉及效果判断。
- **字段划分是外部输入**：PNN 的「字段」由数据表示给定；本课题的 permission/API/intent 等特征组可提供字段边界，
  但字段数 $N$、嵌入维 $M$ 与基座宽度 $D_1$ 的关系需要在实现前冻结。

## 不能支持的论断

- 不能声称 PNN 会提升 LAMDA 或任何年度指标；论文没有年度漂移、类别极端不平衡、实体级指标或恶意软件数据。
- 不能把 Criteo/iPinYou 的 AUC 差值外推为本课题的预期增益；两篇数据集是广告点击，正例率与特征语义不同。
- 不能把 arXiv v1 的数字与结论直接写成 ICDM 2016 正式版；正式版未取得。
- 不能声称 OPNN 一致优于 IPNN：iPinYou 上两者在不同指标上互有胜负（表 II）。
- 不能声称乘积层能缓解跨年坐标翻转或冷启动坐标；论文没有对应实验。
- 不能把 PNN 的参数量与本课题 2.69M 参数基座等预算对比；论文未给出与当前基座可比的预算口径。

## 证据等级

- 原件级别：arXiv v1 预印本，6 个物理页；Eq. 1–14、表 I–III、图 1–5 与消融结论均已回到原始 PDF 页码核验。
- 未核验：ICDM 2016 正式版；官方代码（论文第 4 页脚注给出 GitHub 链接，本次未运行、未比对）。
- 可支撑：PNN 的结构、两变体公式、复杂度推导、训练设置与论文自报数字。
- 实验待证：任何在本课题数据、预算与年度协议下的表现。
