---
title: "Ensemble Learning Using Decorrelated Neural Networks"
authors: [Bruce E. Rosen]
year: 1996
date: 2026-10-21
journal: "Connection Science, 8(3–4):373–384（DOI 10.1080/095400996116820；本地 PDF 为作者预印本，非出版社排版版）"
source_pdf: "[[raw/papers/methodology/1996-Rosen-去相关神经网络集成.pdf]]"
sha256: "0cb89ced75c38baf92e37c34af0d27e46f8a780292a80be1bcba69e93d4f1865"
doi: "10.1080/095400996116820"
tags:
  - 集成多样性
  - 去相关
  - 负相关学习
  - 正则化
  - 类型/论文
key_finding: "去相关惩罚的正源：对第 $j$ 个网络加 $\\lambda(t)d(i,j)P$，其中 $P=(y-f_i)(y-f_j)$ 是两个网络误差的乘积，$d$ 只选此前已训练的网络，$\\lambda(t)$ 常数或随训练衰减（实验用 $1/i$、$100/(Nt)$，脚注称通常由交叉验证确定）。它按成员逐个顺序训练，不是 NCL 的全体同时训练；惩罚未归一化，且在 0–1 分类域恒非负，只能压低正相关，不能直接制造负相关。"
method: "顺序训练集成成员：$E_j=\\sum_p[(y_p-f_j)^2+\\sum_{i=1}^{j-1}\\lambda(t)d(i,j)P]$；$P=(y-f_i)(y-f_j)$；训练后期退火 $\\lambda(t)$。"
baseline: "独立训练后线性组合的集成（No Penalty）；3 Parity、带噪正弦、非均匀分布的非线性回归三个任务"
aliases:
  - Rosen1996
  - DecorrelatedNeuralNetworks
  - Rosen-DeCorr
related:
  - "[[1999-Liu-负相关学习NCL]]"
  - "[[1995-Krogh-神经网络集成歧义分解]]"
  - "[[2005-Brown-多样性创建方法分类学]]"
---

# 去相关神经网络集成（Rosen 1996，NCL 惩罚项的正源）

> Bruce E. Rosen，*Ensemble Learning Using Decorrelated Neural Networks*，*Connection Science* 8(3–4):373–384，1996。DOI `10.1080/095400996116820`。

## 一句话

这篇论文把「成员误差要去相关」写成一个可训练的惩罚项：给第 $j$ 个网络的损失加上它与**此前已训练网络**的误差乘积 $P=(y-f_i)(y-f_j)$，并按 $\lambda(t)$ 退火。它是 Liu & Yao (1999) NCL 惩罚项的直接前身，但两者的训练时序、参考对象与梯度行为不同——这一差别恰好解释了本课题 NCL 先导的消失梯度诊断。

## 题录与原件（证据等级：题录已核实；全文为作者预印本）

- **Crossref**：`query.bibliographic` 命中首条即本篇；题名 *Ensemble Learning Using Decorrelated Neural Networks*，作者 Bruce E. Rosen，容器 *Connection Science*，卷 8、期 3–4、页 373–384，1996 年 12 月，DOI `10.1080/095400996116820`。
- **OpenAlex**：`W2015437745`，同 DOI、同卷期页；作者单位 University of Texas at San Antonio；`open_access.is_oa=false`，`oa_status=closed`。另有 CiteSeerX 记录 `10.1.1.8.9813`，其原始 URL 指向作者页 `http://www.cs.ucla.edu/~rosen/rosen/decor.ps`。
- **Semantic Scholar**：paperId `aed45c0e4603f9896ac652d8c7091c3b7dd0a250`，`externalIds.DBLP=journals/connection/Rosen96`，`openAccessPdf.status=CLOSED`。
- **独立链接证据**：Liu & Yao 1999 的 Crossref 参考文献列表第 6 条即本 DOI（`10.1080/095400996116820`），说明 NCL 论文所对比的「Rosen 的去相关网络」就是本篇。
- **修正任务假设**：题名不是 “Ensemble Diversity Using Decorrelated Neural Networks”，出处也不是 WCNN/INNS。Crossref、OpenAlex、S2/DBLP 三方一致支持 **Connection Science 8(3–4):373–384, 1996**。未发现同题会议版。
- **开放副本**：作者页原件已下线（`web.cs.ucla.edu` 返回 403）；Wayback Machine 2006-02-08 快照仍返回 `application/postscript`，文件标题 `connection_science.dvi`、`%%Pages: 14`。本地用 Ghostscript 10.08.0 转为 PDF，**14 个物理页、Letter 纸张**，SHA-256 `0cb89ced75c38baf92e37c34af0d27e46f8a780292a80be1bcba69e93d4f1865`。
- **版本边界**：出版社版为 12 页（373–384），本地 PDF 是**作者预印本**（首页写 “To appear in Connections Science”，其中 “Connections” 为原文笔误）。**下文页码全部是本地预印本物理页，不是期刊印刷页**；公式编号与期刊版是否一致未核（期刊版在付费墙后，未取得）。

## 方法：去相关惩罚的精确形式

### 1. 成员误差函数（式 7，预印本第 4 页）

第 $j$ 个网络在全部模式上的误差为

$$
E_j=\sum_{p=1}^{N}\left[(y_p-f_j(\vec x_p))^2
+\sum_{i=1}^{j-1}\lambda(t)\,d(i,j)\,P(\vec x_p,y_p,f_i,f_j)\right]\tag{7}
$$

其中 $p$ 是模式下标，$\lambda(t)$ 是（可随时间变化的）缩放函数，$d$ 是指示函数，$P$ 是相关惩罚函数。**求和上限是 $j-1$：只与此前已训练的网络去相关**，不是与全部其他成员同时去相关。

### 2. 惩罚函数（式 8，第 6 页）

$$
P(\vec x,y,f_i,f_j)=(y-f_i(\vec x))(y-f_j(\vec x))\tag{8}
$$

即两个网络误差的**乘积**。原文明确：误差同号且正相关时 $P>0$；两个网络越去相关，$P$ 越负（第 6 页）。

### 3. 指示函数（式 9–10，第 6 页）

只惩罚相邻网络：

$$
d(i,j)=\begin{cases}1 & i=j-1\\0 & \text{otherwise}\end{cases}\tag{9}
$$

或只让偶数号网络与紧邻的前一个网络去相关（可并行训练）：

$$
d(i,j)=\begin{cases}1 & i=j-1\ \text{且}\ i\ \text{为偶数}\\0 & \text{otherwise}\end{cases}\tag{10}
$$

### 4. 缩放函数 $\lambda(t)$（第 5–6 页）

- $\lambda(t)$ 可取常数或随时间变化；脚注 1（第 6 页）写明**通常由交叉验证确定**。
- 论文明确警告：惩罚过大会让成员彼此去相关但**个体误差上升**，集成性能反而变差；对策是**退火惩罚**——先迫使新网络形成不同映射，再逐步把重点移回模式误差（第 5 页）。
- 三个任务的设置：3 Parity 用 $\lambda(t)=1/i$（第 $i$ 个网络，第 7 页）；带噪正弦用 $\lambda(t)=100/(N t)$，$N=88$、$t$ 为训练轮次（第 8 页）；噪声非线性任务用常数 $\lambda$（第 9 页）。

## 实验结果（第 7–9、13–14 页）

| 任务 | 设置 | 无惩罚 | 有惩罚 | 页码 |
|---|---|---|---|---|
| 3 Parity | 2–8 个成员，50 次重复 | — | Penalty 2（式 10 + $\lambda=1/i$）最好 | 第 7 页，图 3 |
| 带噪正弦 | 2 个成员，150 次重复 | 集成 1-2：`0.0034/0.009` | 集成 1-2：`0.0030/0.002` | 第 14 页，表 1 |
| 非均匀噪声非线性 | 1–5 个成员，10 次重复 | 集成 1-5：`0.14780/0.00183` | 集成 1-5：`0.14641/0.00127` | 第 14 页，表 2 |

注意：有惩罚时**单个网络**不一定更好（带噪正弦 network 2 从 `0.0079` 升到 `0.0103`；非线性 network 3–5 也略升），收益来自集成层面的误差抵消。

## 与 NCL（Liu & Yao 1999）的精确关系

NCL 的惩罚（其式 8–11）是

$$
p_i=(F_i-g)\sum_{j\ne i}(F_j-g)
\quad\text{或（有噪声/分类）}\quad
p_i=(F_i-F)\sum_{j\ne i}(F_j-F),
$$

其中 $F$ 是集成输出。与 Rosen 的式 (8) 对比：

1. **Rosen 是单项配对，NCL 是对全部其他成员求和**。在目标参照形式下，NCL 的 $p_i=\sum_{j\ne i}P_{ij}$，即 Rosen 惩罚的「全配对求和」版本。
2. **Rosen 顺序训练**：训练网络 $j$ 时，$f_i\ (i<j)$ 已固定，只有 $f_j$ 更新；NCL 同时更新全部成员。Rosen 的指示函数还允许只与相邻网络配对，NCL 则是全连接。
3. **参考对象不同**：Rosen 的 $P$ 用目标 $y$（与 $d$ 同类），NCL 的分类形式用集成输出 $F$ 替代未知的 $g$。

### 关键推论：NCL 式 (11) 的消失梯度在本篇中没有对应物

令 $e_k=F_k-F$，则 $\sum_{k=1}^{M}e_k=0$，于是

$$
p_i=e_i\sum_{j\ne i}e_j=e_i(-e_i)=-e_i^2,
\qquad
\frac{\partial p_i}{\partial F_i}=-2\left(1-\frac1M\right)e_i.
$$

成员与集成均值重合（$e_i=0$）时惩罚梯度恒为零——这正是本课题 NCL 先导失败的诊断。**这是 NCL 用 $F$ 作参考后代数化简的结果，不是 Rosen 式 (8) 的性质**：Rosen 顺序训练时 $e_i=y-f_i$ 固定，$\partial P/\partial f_j=-(y-f_i)$，即使 $f_j=f_i$ 也不为零（除非前一个网络已完美拟合）。

但这不等于 Rosen 的形式已经解决尺度问题：

- $P$ 是误差的双线性乘积，**没有按误差方差或批内尺度归一化**；其量级随误差平方缩放，$\lambda$ 必须靠退火或交叉验证补偿。顺序训练时 $\partial P/\partial f_j=-(y-f_i)$，其幅度等于**前一个成员的误差**：前成员越准，去相关推力越弱，这同样是一个未归一化的尺度来源。
- 原文明确：在 **0–1 分类域**，网络输出被限制在目标范围内，因此式 (8) 的惩罚**恒非负**（第 8 页）。它只能压低正相关，不能像回归误差那样把 $P$ 推到负值；「越去相关 $P$ 越负」的陈述只对可取正负的回归误差成立。
- 原文没有分析成员重合处的梯度，也没有给出归一化形式。

## 对本课题第三轮的直接含义（只登记，不裁决）

- **可引为正源**：Rosen 1996 是「在训练损失中加成员误差乘积去相关项」的文献起点；NCL 1999 是其同时训练、全配对的推广。
- **可解释先导失败**：NCL 分类形式 $p_i=-e_i^2$ 的消失梯度是参考对象换成集成均值后的代数后果；Rosen 的顺序、目标参照配对形式不含这一精确抵消。第三轮若回到「配对 + 目标/固定参照」，有正源依据。
- **不能直接照搬**：Rosen 的 $P$ 在 0–1 分类域恒非负且未归一化，不能直接当作「尺度稳定、可制造负相关」的去相关项；第三轮若需要尺度稳定与可正可负，需另找归一化相关/余弦形式（见第三组检索）。
- **$\lambda$ 设定**：Rosen 用 $1/i$、$100/(Nt)$、常数 + 交叉验证，并强调退火；NCL 用 $[0,1]$ 且声明问题相关。两者都不支持把 $\lambda$ 固定为跨任务常数。

## 证据等级

- 题录：Crossref + OpenAlex + Semantic Scholar（DBLP 键）+ NCL 参考文献 DOI，**已核实**。
- 全文：作者预印本（Wayback 快照 → PostScript → Ghostscript PDF），14 页完整；**非出版社版**，期刊版未取得。
- 公式：式 (7) 第 4 页、式 (8)–(10) 与脚注 1 第 6 页、0–1 分类非负性第 8 页，均已回渲染页视觉复核；表 1–2 第 14 页已复核。
- 与 NCL 的关系：基于两篇全文公式的代数推导，**本笔记自行推导，非原文陈述**；已标为推论，不得写成 Rosen 或 NCL 的原文结论。
