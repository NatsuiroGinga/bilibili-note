---
title: "广告点击预估：来自一线的经验（FTRL-Proximal 与逐坐标学习率）"
authors: [H. Brendan McMahan, Gary Holt, David Sculley, Michael Young, Dietmar Ebner, Julian Grady, Lan Nie, Todd Phillips, Eugene Davydov, Daniel Golovin, Sharat Chikkerur, Dan Liu, Martin Wattenberg, Arnar Mar Hrafnkelsson, Tom Boulos, Jeremy Kubica]
year: 2013
date: 2026-10-15
journal: "KDD 2013（Google）"
source_pdf: "[[raw/papers/methodology/2013-McMahan-广告点击预估FTRL与逐坐标学习率.pdf]]"
tags: [优化器, FTRL, 逐坐标学习率, 稀疏二值特征, 在线学习, 类型/论文]
key_finding: "在工业级大规模 CTR 预估（特征极稀疏、每样本非零特征极少）中，逐坐标学习率相比单一全局学习率把 AucLoss 降低 11.2%；并报告在稀疏特征 + 噪声标签下 dropout 反而有害、输入归一化 x/‖x‖ 也偏有害。"
---

# 广告点击预估：FTRL-Proximal 与逐坐标学习率

## 全文核验结论

- 设定（第 1 页）：CTR 预估是**极稀疏**问题——「数据极稀疏，每样本通常只有极小比例的非零特征值」。
- 方法：FTRL-Proximal（兼具稀疏性与收敛性）+ **逐坐标学习率**。
- **逐坐标学习率的论证（§3.1，第 2–3 页）**：用「10 枚硬币、每轮只翻一枚」的思想实验说明——把整体当单一问题用全局 `η_t = 1/√t` 会在该特征**未被观测时也衰减其学习率**，明显次优；正解是按特征出现次数给 `η_{t,i} = α/(β+√n_{t,i})`。并引 Streeter & McMahan 证明存在**标准算法渐进远差于独立副本**的一族问题。
- **实测（§3.1 末，第 3 页）**：「逐坐标学习率相比全局学习率把 AucLoss 降低 **11.2%**」；并说明在其实设定中「AucLoss 降 1% 已算大」。
- **两条负面工程结论**：`dropout` 在稀疏、噪声标签设定下无益甚至有害（§5，第 6 页）；输入归一化 `x/‖x‖` 也「看起来有害」（第 6 页）——归因于与逐坐标学习率/正则的相互作用。

## 对本课题的合法映射

- 这是把「**逐坐标学习率**」用在**稀疏（近二值）特征 + 极不平衡标签 + 在线学习**工业系统上的**最大规模实测**，形态与 LAMDA（4561 维稀疏二值、类别不平衡、年度在线到达）高度同构。
- 「每样本非零特征数差异大」「特征频次极不均匀」正是 LAMDA 的情形，故「单一全局学习率一刀切」的失效论证可直接引用。

## 原创边界与不能直接声称

- 模型是**线性 logistic + FTRL**（非 MLP），无隐藏层、无 ReLU；**不能**据此声称逐坐标学习率在四层 MLP 上有同等 11.2% 的收益。
- 无年度漂移/持续学习；dropout/归一化的负面结论只在其自身稀疏噪声设定内成立。

## 证据记录

- 全文状态：已下载并核验（§1、§3.1、§5）。
- 稳定标识：KDD 2013；DOI `10.1145/2487575.2488200`。
- 课题角色：Q1/Q4 的**工业级稀疏二值特征 + 逐坐标学习率**证据；解释 2013 的更新路径。
