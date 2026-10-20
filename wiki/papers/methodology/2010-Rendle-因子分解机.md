---
title: "Factorization Machines"
authors: [Steffen Rendle]
year: 2010
date: 2026-10-20
journal: "IEEE International Conference on Data Mining（ICDM 2010），DOI 10.1109/ICDM.2010.127"
source_pdf: "[[raw/papers/methodology/2010-Rendle-FactorizationMachines.pdf]]"
sha256: "cfd4d560d04fff87c4f9c8cb8fd02a33310412c1d065b9a37aed26958c7d33e7"
arxiv_id: ""
zotero_item_key: "XT7UI4TS"
bibtex_key: "rendle_factorization_2010"
tags:
  - 因子分解机
  - 特征交互
  - 稀疏数据
  - 推荐系统
  - 类型/论文
key_finding: "FM 以因子化参数替代 SVM 多项式核的稠密参数化，在巨大稀疏下仍可估计二阶交互：交互权重 ⟨v_i,v_j⟩ 由 k 维因子向量内积给出（Eq. 3），模型方程可重排为 O(kn) 线性复杂度（Lemma 3.1），稀疏下为 O(k·m(x))；即使两个特征从未共现，因子化也借相关交互估计其组合（§III 例）。"
method: "二阶 FM：w_0 + Σw_i x_i + ΣΣ⟨v_i,v_j⟩x_i x_j（Eq. 1），SGD 直接优化（Eq. 4 逐参数 O(1) 梯度）；对回归/分类/排序统一，仅由输入特征向量定义任务"
baseline: "SVM（多项式核）、PARAFAC、biased MF、SVD++、PITF、FPMC（后四者可由 FM 按输入特征定义模仿，§V）"
aliases:
  - RendleFM
  - FM2010
related:
  - "[[2018-Li-安卓恶意软件因子分解机]]"
  - "[[2016-Qu-乘积神经网络PNN]]"
---

# Factorization Machines（FM 正源）

> Steffen Rendle，ICDM 2010，DOI `10.1109/ICDM.2010.127`，物理 6 页。原件由用户 2026-10-20 手动下载（IEEE 付费墙，代理通道不可达）。

## 一句话

FM 把「全部二阶特征交互」写成 k 维因子向量内积的因子化参数，用线性参数量与线性计算量在巨大稀疏数据上估计交互——这正是长稀疏二值特征（如 Android 静态特征）上显式交互建模的正源。

## 题录与原件

- 题名/作者/单位（Osaka University）见物理第 1 页；IEEE 排版 6 页。
- 原件：`raw/papers/methodology/2010-Rendle-FactorizationMachines.pdf`。
- SHA-256：`cfd4d560d04fff87c4f9c8cb8fd02a33310412c1d065b9a37aed26958c7d33e7`。
- Zotero 条目键：`XT7UI4TS`（历史重复 `6RQSW2FV`/`H7MK7SZM` 均无 PDF，留待清理）。

## 论文原方法

- **模型方程**（§III-A，Eq. 1）：$\hat y(\mathbf x) := w_0 + \sum_{i=1}^n w_i x_i + \sum_{i=1}^n\sum_{j=i+1}^n \langle\mathbf v_i,\mathbf v_j\rangle x_i x_j$，阶数 d=2；交互参数 $\langle\mathbf v_i,\mathbf v_j\rangle := \sum_{f=1}^k v_{i,f} v_{j,f}$（Eq. 3）。
- **稀疏下的参数估计**（§III-3）：直接估计交互需要两特征共现样本；因子化打破独立性——从未共现的（Alice, Star Trek）也能借相关交互（经 Star Wars 等中转）得到非零估计。这是 FM 相对 SVM 多项式核（稠密 $w_{ij}$）在 $\bar m_D \ll n$ 时的本质优势。
- **线性复杂度**（Lemma 3.1）：Eq. 1 的交互项可重排为 $\frac12\sum_{f=1}^k\left(\left(\sum_i v_{i,f}x_i\right)^2-\sum_i v_{i,f}^2 x_i^2\right)$，计算 $O(kn)$；稀疏下 $O(k\,m(\mathbf x))$。
- **优化**（§III-4 学习，Eq. 4）：SGD 直接优化原始形式；$\partial\hat y/\partial v_{i,f} = x_i\sum_j v_{j,f}x_j - v_{i,f}x_i^2$，其中 $\sum_j v_{j,f}x_j$ 与 i 无关可预计算，每参数梯度 O(1)、每样本更新 $O(kn)$（稀疏 $O(k\,m(\mathbf x))$）；支持 square/logit/hinge 损失。
- **统一预测器**（§V）：仅改输入特征向量定义即可模仿 biased MF、SVD++、PITF、FPMC。

## 与本课题的关系（只登记可迁移机制）

- 机制：长稀疏二值向量上的**低秩二阶交互**，参数 $O(nk)$——与本课题 4561 维稀疏二值特征同构（激活率 0.27–1.58%，高稀疏）。
- 域内对照已入库：Li et al. 2018（[[2018-Li-安卓恶意软件因子分解机]]）在 DREBIN 式特征上实测 FM 与单隐层 MLP 精度/F1 打平；PNN（[[2016-Qu-乘积神经网络PNN]]）给出内积/外积乘积层的复杂度谱系，并注明「无隐层等权求和时内积 PNN 等同 FM」。
- 可用接口：partial FM「只在指定特征组间建交互」（Li 2018 物理第 5 页）——若做交互探针，可按特征组（如权限/组件/API）分组。

## 不能支持的论断

- 不能由本文断言「FM 优于 MLP」——Li 2018 的域内实测是打平；
- 本文无年度协议、无概念漂移、无恶意软件任务，不支持任何漂移相关结论；
- 本文的交互是全局静态的，不提供按年份/按稀缺度调制的任何机制。

## 证据等级

- 原件级别：ICDM 2010 正式论文，6 页全文；Eq. 1/3、Lemma 3.1、Eq. 4 已对照 MinerU 转换文本核验（转换件 `/tmp/fm-extract/`，不入库）。
- 可支撑：FM 的模型方程、复杂度、稀疏估计原理、与 SVM/矩阵分解的关系。
- 实验待证：任何 FM 探针在本课题协议下的表现（探针 #3 现为备选）。
