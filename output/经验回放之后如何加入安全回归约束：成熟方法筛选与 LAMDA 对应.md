```text
actual_model: GPT-6 Astra Pro
actual_effort: 本对话未提供可独立核验的 effort 档位；不将研究深度等同于已确认的模型设置。
actual_mode: 本对话内的有界增量文献研究与公开源码只读核验。
used_apps: Sider Scholar、GitHub；另使用 web 核对原论文全文、会议记录和作者公开材料。
核验截止日期: 2026-09-08
状态: 外部候选，待发起方依据原文、公开实现及本地实验独立复核。
```

# 经验回放之后如何加入安全回归约束：成熟方法筛选与 LAMDA 对应

## 一、结论：直接先例已经存在，但“降低回归”不等于“降低漏报”

**【论文事实】最直接的来源是 *Regression-aware Continual Learning for Android Malware Detection*：它明确把 Positive-Congruent Training（PCT）加入 Replay，并在 Android 恶意软件数据上评价。因此，“经验回放＋旧正确样本回归保护”并不是需要从零拼接、尚无直接先例的组合。**论文中的保护是加权蒸馏软惩罚，不是逐样本不翻转的硬保证。定位：§IV，式（8）—（10）。([arXiv][1])

**【基于论文的推论】在既有 ER 正锚点通过之后，最适合优先核验的是 ER＋PCT/FD-LM；最必要的机制对照是 ER＋普通蒸馏。**前者检验“强调旧正确样本”是否有增量，后者排除收益仅来自额外的输出一致性正则。DER++ 是进一步需要强持续学习对照时的成熟选项；GEM/A-GEM 更适合作为约束优化来源，不能直接称为已经实现了旧恶意样本的逐样本安全保护。

**【论文事实】必须保留一个反例。**上述 Android 论文的 arXiv v2，表 I、PDF 第 7 页，在 TESSERACT 的 backward 汇总中报告：

| 方法         | 恶意样本负向翻转率 NFR\(_{\mathrm{mw}}\) ↓ |      Recall ↑ |
| ---------- | --------------------------------: | ------------: |
| Replay     |                      2.28 ± 1.31% | 85.67 ± 3.84% |
| PCT＋Replay |                      1.33 ± 0.89% | 81.40 ± 2.85% |

这说明其报告结果中出现了**负向翻转减少、召回率同时下降**的情形。这里不是 LAMDA 结果，也不是对本地候选的实验裁决。([arXiv][2])

**【基于论文的推论】真正需要证伪的命题应是：在相同信息、回放容量与训练资源条件下，减少旧恶意样本的负向翻转，同时不突破既定的 FNR、FPR 和新时段检测性能容忍界限。**仅报告更低 NFR，可能奖励一个“更少改变、也更少学会新威胁”的模型。

---

## 二、方法证据卡：原生组合、可复用约束与不适配部分

本轮重点核对既有 Android 直接近邻，并补充六篇方法来源。以下“公开实现”只表示已定位代码，不表示本轮执行或复现成功。

### 2.1 Android 回归感知持续学习：确实包含 Replay＋PCT

**题名：** *Regression-aware Continual Learning for Android Malware Detection*
**作者：** Daniele Ghiani；Daniele Angioni；Giorgio Piras；Angelo Sotgiu；Luca Minnei；Srishti Gupta；Maura Pintor；Fabio Roli；Battista Biggio。
**年份、场所：** 2026，IEEE Transactions on Information Forensics and Security。机构题录确认期刊归属；本轮读取的是 **arXiv:2507.18313v2，2026-07-10**，不是 IEEE 出版平台全文。
**稳定入口：** [arXiv v2](https://arxiv.org/abs/2507.18313v2)、[期刊 DOI](https://doi.org/10.1109/TIFS.2026.3714132)。 ([Iris][3])

**【论文事实】组合关系：原生存在。**§IV 明确说明将 PCT 项加入 Replay 目标；§V-A 的 Domain-IL 使用容量 200 的 Replay，参考任务是 Android 二分类。不是我们首次提出这种组合。其具体惩罚见下一张 PCT 证据卡。([arXiv][1])

**【基于论文的推论】适配程度最高，但仍有两个差量需要明确。**

第一，原式保护的是**旧模型正确的样本，包括良性和恶意**，而不是专门优化“旧恶意样本漏检回归”。第二，若在 LAMDA 中只对回放池内的旧恶意真阳性施加约束，就已经改变了原式的参考集合，必须标为任务化变体。

**【不确定性】**本轮未核准该 Android 论文独立、可固定的官方实验仓库。因此，损失项可以依据原文及 PCT 官方实现重建，但不能声称已逐行复现作者的 batch 组成、缓冲区管理、损失归一化及全部超参数。

---

### 2.2 PCT／FD-LM：最小可复用的旧正确样本保护损失

**题名：** *Positive-Congruent Training: Towards Regression-Free Model Updates*
**作者：** Sijie Yan；Yuanjun Xiong；Kaustav Kundu；Shuo Yang；Siqi Deng；Meng Wang；Wei Xia；Stefano Soatto。
**年份、场所：** CVPR 2021，14299–14308。
**读取版本：** arXiv:2011.09161v3，2021-05-17。
**入口：** [会议记录](https://openaccess.thecvf.com/content/CVPR2021/html/Yan_Positive-Congruent_Training_Towards_Regression-Free_Model_Updates_CVPR_2021_paper.html)、[arXiv v3](https://arxiv.org/abs/2011.09161v3)、[官方代码](https://github.com/amazon-science/regression-constraint-model-upgrade)。 ([开放获取计算机视觉研究会][4])

**【论文事实】数学形式。**用 \(z_\theta(x)\) 表示新模型 logits，\(z_-(x)\) 表示旧模型 logits。其 focal distillation 可写为：

$$
L_{\mathrm{FD}}
=
\frac{1}{|S|}
\sum_{(x_i,y_i)\in S}
\left[\alpha+\beta\,\mathbf 1\{h_-(x_i)=y_i\}\right]
D\!\left(z_\theta(x_i),z_-(x_i)\right).
$$

FD-LM 取：

$$
D(z,z_-)=\frac12\|z-z_-\|_2^2.
$$

它作为附加项与分类损失共同优化。原文位置：§4.2，式（7）—（9）。原论文是模型更新方法，**不是容量受限的经验回放算法**；与 Replay 的直接结合由上一张证据卡提供。([arXiv][5])

**【官方代码事实】**固定提交 `fb2268c67706834632ec1427945fcf30a7218227` 的 `ConstrainedUpgrade/losses.py`，`FocalDistillationLoss.forward()`，明确通过 `old_model_prediction.argmax(...) == gt` 生成正确性权重；`fd_beta=0` 对应普通蒸馏。

**【基于论文的推论】LAMDA 对应。**它只需要更新时已经取得的标签和冻结旧模型，不需要未来测试标签。但“旧模型预测正确”不能由无标签置信度替代。原实现的 argmax 与低误报部署阈值也可能不同；改用部署阈值构造保护集合，需要明确记录。

**边界：**当 \(\alpha>0\) 时，旧错误样本仍参与蒸馏；FD-LM 还会惩罚某些有益的 logits 改变。它不是“只阻止有害变化”的精确约束。

---

### 2.3 DER++：原生包含回放＋输出保持，但不是负向回归专用方法

**题名：** *Dark Experience for General Continual Learning: a Strong, Simple Baseline*
**作者：** Pietro Buzzega；Matteo Boschini；Angelo Porrello；Davide Abati；Simone Calderara。
**年份、场所：** NeurIPS 2020。
**读取版本：** arXiv:2004.07211v2，2020-10-22。
**入口：** [会议记录](https://proceedings.neurips.cc/paper/2020/hash/b704ea2c39778f07c617f6b7ce480e9e-Abstract.html)、[arXiv v2](https://arxiv.org/abs/2004.07211v2)、[官方 Mammoth 实现](https://github.com/aimagelab/mammoth/blob/master/models/derpp.py)。 ([NeurIPS 会议记录][6])

**【论文事实】组合关系：回放＋一般输出一致性存在；回归专用约束不存在。**

$$
L_{\mathrm{DER++}}
=
L_{\mathrm{current}}
+
\alpha\,
\mathbb E_{(x,z^{\mathrm{stored}})\sim M}
\|z_\theta(x)-z^{\mathrm{stored}}\|_2^2
+
\beta\,
\mathbb E_{(x,y)\sim M}
\ell_{\mathrm{CE}}(z_\theta(x),y).
$$

参考 logits 在样本进入记忆时沿训练轨迹保存，不是每年重新计算的上一版教师输出。原文位置：§3，式（5）—（6）、算法 2。

**【官方代码事实】**`models/derpp.py → Derpp.observe()` 分别从 buffer 取样计算 MSE 与标签交叉熵，随后保存当前样本、标签和 logits；本轮读取 blob 为 `048fa4d501957dc499068a9567f3bcd704ead60a`。

**【基于论文的推论】LAMDA 对应。**DER++ 是判断“是否仅靠一般输出保持就足够”的强对照，但没有旧正确性筛选、恶意类非对称权重或 FPR 约束。把 DER++ 直接称为“安全回归约束算法”会扩大原文含义。

---

### 2.4 GEM 与 A-GEM：成熟的记忆约束优化，不是逐样本不回归保证

#### GEM

**题名：** *Gradient Episodic Memory for Continual Learning*
**作者：** David Lopez-Paz；Marc’Aurelio Ranzato。
**年份、场所：** NIPS 2017。本轮按会议版核对。
**入口：** [会议记录](https://papers.nips.cc/paper_files/paper/2017/hash/f87522788a2be2d171666752f97ddebb-Abstract.html)、[arXiv](https://arxiv.org/abs/1706.08840)、[官方代码](https://github.com/facebookresearch/GradientEpisodicMemory)。 ([NIPS 会议论文][7])

**【论文事实】**GEM 使用旧任务记忆计算损失梯度，将当前梯度投影到满足历史任务约束的区域：

$$
\tilde g
=
\arg\min_v \frac12\|v-g\|_2^2,
\qquad
g_k^\top v\ge 0,\quad k<t.
$$

定位：§3，式（5）—（8）、算法 1。参考对象是**旧任务记忆的平均损失**，不是旧正确恶意样本的翻转事件。([NIPS 会议论文][8])

**【官方代码事实】**`model/gem.py → Net.observe()` 逐旧任务计算记忆梯度，`project2cone2()` 求解二次规划。该实现为每个任务分配记忆空间，不能把“每任务 200”误当成“总容量 200”。

#### A-GEM

**题名：** *Efficient Lifelong Learning with A-GEM*
**作者：** Arslan Chaudhry；Marc’Aurelio Ranzato；Marcus Rohrbach；Mohamed Elhoseiny。
**年份、场所：** ICLR 2019。
**读取版本：** arXiv:1812.00420v2。
**入口：** [arXiv v2](https://arxiv.org/abs/1812.00420v2)、[官方代码](https://github.com/facebookresearch/agem)。 ([arXiv][9])

**【论文事实】**A-GEM 用合并记忆中的随机参考批次构造 \(g_{\rm ref}\)。若 \(g^\top g_{\rm ref}<0\)，则：

$$
\tilde g
=
g-\frac{g^\top g_{\rm ref}}{\|g_{\rm ref}\|_2^2}g_{\rm ref}.
$$

定位：§4，式（10）—（11）；附录算法 2。它放松为单个平均约束，允许不同历史任务之间相互补偿。

**【基于论文的推论】两者与本任务的真实关系。**它们原生具有“记忆＋损失约束”，但不等于“标准 ER 目标＋安全回归约束”。把 \(g\) 换成 ER 目标梯度、把参考风险换成旧恶意样本条件风险，属于我们的任务化组合。

平均损失下降也不保证零翻转。一个二分类反例是：两个旧正确样本的交叉熵从 \((0.10,0.65)\) 变成 \((0.70,0.01)\)，平均值从 \(0.375\) 降到 \(0.355\)，但第一个样本越过 \(\log 2\) 对应的决策界限而变错。**这是数学反例，不是实验结果。**

---

### 2.5 RCAT：有非回归约束理论，但保护的是对抗鲁棒性

**题名：** *Robustness-Congruent Adversarial Training for Secure Machine Learning Model Updates*
**作者：** Daniele Angioni；Luca Demetrio；Maura Pintor；Luca Oneto；Davide Anguita；Battista Biggio；Fabio Roli。
**年份、场所：** IEEE TPAMI，2025。
**读取版本：** arXiv:2402.17390v2，2025-05-29。
**入口：** [arXiv v2](https://arxiv.org/abs/2402.17390v2)、[DOI](https://doi.org/10.1109/TPAMI.2025.3573237)、[官方代码](https://github.com/pralab/robustness-congruent-advtrain)。 ([arXiv][10])

**【论文事实】组合关系：对抗训练＋回归惩罚存在；容量受限 ER 不在该原生组合中。**§III-A 式（8）同时使用分类损失、改进来源模型蒸馏，以及旧模型仍正确时的额外蒸馏，并在扰动集合内做内层最大化。保护目标包括 robustness negative flips，而不只是干净样本的预测翻转。([arXiv][11])

与本问题更直接相关的是 §III-B、式（14）—（19）：

$$
\min_f \widehat L(f;D)
\quad
\text{s.t.}\quad
\widehat L(f;D_0)\le \widehat\epsilon,
$$

其中 \(D_0\) 是旧模型正确的参考子集。其一致性分析有 IID、可学习性及旧模型独立性等假设；有限的、自适应重用的漂移回放池不能自动继承该结论。([arXiv][11])

**【基于论文的推论】LAMDA 对应。**可借鉴的是“在旧正确条件子集上约束风险”的形式，不是直接搬入图像扰动球和对抗训练。没有有效 APK 变换定义时，对 Drebin 向量任意扰动不能证明真实恶意软件安全性。

---

### 2.6 MPT：2026 年已发表的 margin 保护来源，但不直接对应固定二分类

**题名：** *Mitigating Negative Flips via Margin Preserving Training*
**作者：** Simone Ricci；Niccolò Biondi；Federico Pernici；Alberto Del Bimbo。
**年份、场所：** AAAI 2026，40(11):8721–8730。
**读取版本：** arXiv:2511.08322v2，2025-11-15。
**入口：** [正式记录与 DOI](https://doi.org/10.1609/aaai.v40i11.37825)、[arXiv v2](https://arxiv.org/abs/2511.08322v2)、[官方代码](https://github.com/miccunifi/negative_flip_MPT)。 ([AAAI Publications][12])

**【论文事实】**其 §“Margin Preserving Training”，式（1）—（4），对新类别 logits 加训练期偏置：

$$
\Delta_c=
\begin{cases}
0,&c\in\mathcal Y_{\rm old},\\
k,&c\in\mathcal Y_{\rm new},
\end{cases}
\qquad
L_\Delta=-\log
\frac{e^{z_y+\Delta_y}}{\sum_c e^{z_c+\Delta_c}},
$$

再加入来自旧模型与另一个新参考模型的双来源 focal distillation。新参考模型在全部当前类别上训练；原文不是固定容量 ER 协议。([arXiv][13])

**【基于论文的推论】**LAMDA Domain-IL 中“新年份”不等于“新增输出类别”。因此，MPT 是 margin-based 非回归的相关来源，不是已经验证了 LAMDA 年度恶意／良性检测的现成方法。它也意味着“首次用 margin 保护旧正确预测”不是稳妥的创新表述。

---

## 三、哪些组合已被证明“存在”，哪些仍属于我们设计

| 方案                                 | 原方法是否有真实样本记忆／回放 | 是否直接针对旧正确样本回归  | 本问题中的身份      |
| ---------------------------------- | --------------- | -------------- | ------------ |
| Android Regression-aware CL＋Replay | 有               | 有，PCT 软惩罚      | **最直接的方法来源** |
| PCT 原论文                            | 不以有限 ER 为设定     | 有              | 可复用损失来源      |
| DER++                              | 有               | 没有正确性门控        | 一般保持能力的强对照   |
| GEM／A-GEM                          | 有记忆，用于梯度约束      | 约束平均损失，不直接约束翻转 | 约束优化来源       |
| RCAT                               | 非有限 ER 设定       | 有，包含对抗鲁棒性回归    | 理论／目标形式来源    |
| MPT                                | 非有限 ER 设定       | 有，重点是类别扩张      | margin 相关近邻  |

上述区分依据对应原文目标和算法，而不是依据方法名字。([arXiv][1])

**【基于论文的推论】推荐顺序是“先最接近的已知组合，再验证任务化差量”，不是先构建复杂新算法。**目前没有证据支持为满足工作量而同时加入生成器、主动查询器、课程调度器或第二种记忆机制。

---

## 四、如何映射为 LAMDA 的“旧恶意样本安全回归”问题

以下是**任务化形式化建议，不是上述论文已经验证的 LAMDA 算法**。

### 4.1 先把参考样本定义清楚

设更新前模型为 \(f_{t-1}\)，既有回放记忆为 \(M_{t-1}\)，样本标签实际可用时刻为 \(a_i\)。在更新时刻 \(t\)，定义：

$$
A_t^+
=
\left\{
(x_i,y_i)\in M_{t-1}:
a_i\le t,\ y_i=1,\
h_{t-1,\tau}(x_i)=1
\right\}.
$$

它是**已获得恶意标签、旧模型在阈值 \(\tau\) 下能够检出的旧样本**。

**【基于论文的推论】**该集合可以直接从现有 ER 记忆中筛出，不必另建一个额外容量的“安全 buffer”。但必须报告 \(|A_t^+|\)：总容量 200，不代表有 200 个合格恶意保护样本。

保护集合在一次更新过程中应由冻结旧模型确定。不能随着学生模型变错而将样本移出保护集合，否则目标会自行消失。

### 4.2 第一种实现：保留成熟 PCT，只改变保护优先级

固定原 ER 目标：

$$
L_{\rm ER}
=
\mathbb E_{(x,y)\sim B_t}\ell_{\rm CE}
+
\rho\,\mathbb E_{(x,y)\sim R_t}\ell_{\rm CE}.
$$

最小任务化变体是：

$$
L
=
L_{\rm ER}
+
\lambda\,
\mathbb E_{(x_i,y_i)\sim S_t}
w_i\,
D\!\left(z_\theta(x_i),z_{t-1}(x_i)\right),
$$

$$
w_i
=
\alpha
+
\beta_+\mathbf1\{i\in A_t^+\}
+
\beta_-\mathbf1\{y_i=0,\ h_{t-1,\tau}(x_i)=0\}.
$$

**【基于论文的推论】**这把“所有旧正确预测同等重要”改成显式的类条件优先级，但本质仍是 PCT 的非对称任务化版本，不是全新的蒸馏原理。是否令 \(\beta_+>\beta_-\)，以及是否只在历史记忆上计算，必须由历史验证确定，并接受 FPR 代价检验。

**实现边界：**教师输出应冻结；FD-LM 使用 logits，而不是未经说明地替换成 sigmoid 概率。\(S_t\) 究竟是当前批次、回放批次还是两者，应明确写出。不同选择不能都称为原作者完全一致的实现。

### 4.3 第二种实现：直接约束条件翻转风险，而非锁住完整 logits

这是一个**更直接、但尚待验证的替代方向**，不是要求与 PCT 同时叠加。

令二分类阈值 margin 为：

$$
s_\theta(x)
=
z_{\theta,1}(x)-z_{\theta,0}(x)
-\log\frac{\tau}{1-\tau}.
$$

对 \(A_t^+\) 使用单侧替代损失：

$$
\phi_\gamma(s)=\left[1-\frac{s}{\gamma}\right]_+,
\qquad \gamma>0.
$$

因为 \(\mathbf1\{s<0\}\le\phi_\gamma(s)\)，有：

$$
\widehat{\mathrm{cNFR}}_{\rm mw}(\theta;A_t^+)
\le
\frac1{|A_t^+|}
\sum_{i\in A_t^+}\phi_\gamma(s_\theta(x_i)).
$$

于是可考虑：

$$
\min_\theta L_{\rm ER}(\theta)
\quad\text{s.t.}\quad
\widehat R_{\rm old\text{-}mw}^{\phi}(\theta)\le\epsilon_t.
$$

**【基于论文的推论】**这条经验上界说明约束对象比对称 logit matching 更直接，但**不构成未来分布安全保证**。达到正 margin 后不再惩罚继续提高置信度，也不意味着它优于 FD-LM；过强 margin 要求可能损害良性边界或新时段适应。

若采用 GEM/A-GEM 风格求解，还须区分“一阶损失不增”与“实际更新不增”。对光滑风险 \(R\)：

$$
R(\theta-\eta v)
\le
R(\theta)-\eta\nabla R(\theta)^\top v
+\frac{L\eta^2}{2}\|v\|^2.
$$

仅令 \(\nabla R^\top v\ge0\)，并不能消除二阶增加项。带动量或 Adam 时，原始梯度也未必等于实际参数更新方向。**因此不应把一次梯度投影写成硬安全证书。**

### 4.4 创新主语应该放在哪里

**【基于论文的推论】**值得检验的差量是：

> 在有限且因果可用的历史记忆上，控制旧恶意真阳性的条件回归风险，并显式处理误报预算、标签延迟以及适应新时段的代价。

不宜作为创新主语的说法包括“首次 ER＋PCT”“首次保护旧正确样本”“首次利用历史梯度防止遗忘”或“首次 margin 保持”。上述来源已经分别覆盖这些组成部分。

只将 PCT 的恶意类权重调大，通常更接近任务化基线；理论深度需要来自**风险对象、可行性条件、有限记忆误差、优化近似及失效条件**，而不是模块数量。

---

## 五、最小实验臂与标签到达时序

### 5.1 实验臂：分阶段，不要求机械式 2×2

以下均为**【待实验验证：建议方案】**。

| 阶段       | 实验臂                    | 唯一需要回答的问题            |
| -------- | ---------------------- | -------------------- |
| 原正锚点阶段   | 已有 Naive vs 标准 ER      | 在现有公平预算下，ER 是否有正增益？  |
| 正锚点通过后   | ER vs **ER＋PCT/FD-LM** | 成熟回归保护是否降低旧恶意样本翻转？   |
| 解释上述差量时  | **ER＋普通 FD-LM 蒸馏**     | 收益来自一般输出保持，还是旧正确性门控？ |
| 有明确剩余病灶后 | ER＋任务化条件约束，比较 ER＋PCT   | 非对称／单侧风险设计是否有必要？     |

普通蒸馏对照应尽量匹配整体正则强度，不能让 PCT 仅因为平均权重更大而占便宜。它对应 PCT 官方实现中的 `fd_beta=0`，而不是临时发明的弱对照。

**【基于论文的推论】**DER++ 只在需要证明优于成熟 replay-distillation 基线时加入；A-GEM 只在声称约束投影带来增量时加入。没有必要同时运行本报告全部方法，更没有必要为了矩阵完整性添加无机制意义的实验臂。

最低公平条件是同一起点、相同年度顺序、相同当前数据和回放采样、相同训练步数、相同已取得标签集合；教师计算及额外记忆前后向另行计费。正锚点的既有合同不应因新增方法而被悄然改变。

### 5.2 标签到达需要两个时钟

**【待实验验证：协议建议】**区分样本出现时刻 \(s_i\) 与标签可用时刻 \(a_i\)：

$$
D_t^{\rm eligible}
=
\{(x_i,y_i):s_i\le t,\ a_i\le t\}.
$$

更新、buffer 入库和“旧正确”门控都只能使用该集合。样本已经出现但标签尚未到达时，不能利用最终标签把它提前放入恶意保护集合。

若公开字段不能给出逐样本真实 \(a_i\)，则 \(a_i=s_i+\Delta\) 只能是**预先声明的延迟模拟**，不能称为真实标注流程复原。已有年度正锚点可保持不变；延迟条件作为独立压力协议，不能与即时全标签成绩混报。

**【待实验验证：时间顺序】**在 prequential 评价中，应先用当前已部署模型作预测，再在标签到达后允许更新。当年标签已经用于训练后的同年测试，与更新前对下一批样本的预测是不同问题，应分别列明。

### 5.3 三类样本集合不得混用

| 集合             | 允许用途           | 禁止用途                       |
| -------------- | -------------- | -------------------------- |
| 训练与回放记忆 \(M\)  | 梯度、蒸馏、约束构建     | 充当独立安全证明                   |
| 历史验证／校准集 \(V\) | 选择权重、阈值、历史接受门  | 隐性变成不断调参的目标期测试集            |
| 封存评价集 \(E\)    | 比较新旧模型的翻转及逐年风险 | 反向选择 \(\lambda\)、保护样本或未来家族 |

这是**【待实验验证：隔离设计】**。使用测试标签事后计算翻转是合法评价；用这些标签决定哪些训练样本值得保护则改变了信息条件。

---

## 六、必须报告的指标，以及明确的失败门

### 6.1 “旧恶意样本负向翻转率”必须写清分母

对固定历史评价集合 \(E_j\)，令：

$$
n_{10}^{(j,t)}
=
\sum_{i\in E_j}
\mathbf1\{y_i=1,\ h_{t-1}(x_i)=1,\ h_t(x_i)=0\}.
$$

建议同时报告：

$$
\mathrm{NFR}_{\rm mw}^{(j,t)}
=
\frac{n_{10}^{(j,t)}}{N_+^{(j)}},
$$

$$
\mathrm{cNFR}_{\rm mw}^{(j,t)}
=
\frac{n_{10}^{(j,t)}}{
\sum_{i\in E_j}\mathbf1\{y_i=1,h_{t-1}(x_i)=1\}
}.
$$

**【论文事实】**Android 回归论文的 NFR 定义以相应评价集合样本数为分母；PCT/MPT 的 Rel-NFR 又采用另一种归一化。因此，本报告的 cNFR 不能不加说明地与这些指标同名互换。([arXiv][2])

**【基于论文的推论】**还必须报告分子、恶意样本总数及旧真阳性数。分母为零时应记为“不适用”，不能记成安全的 0%。

先前对不同年份的聚合 AP、AUC、FNR，不能反推出该指标；负向翻转需要**同一批样本在更新前后的配对预测**。

### 6.2 负向翻转必须与“修复了多少旧漏报”一起看

对同一批恶意样本，令 \(n_{01}\) 为旧漏报被新模型修复的数量，则：

$$
\mathrm{FNR}_{t}-\mathrm{FNR}_{t-1}
=
\frac{n_{10}-n_{01}}{N_+}.
$$

**【基于论文的推论】**降低 \(n_{10}\) 的同时，也可能大幅减少 \(n_{01}\)，导致 FNR 反而更高。这就是不能用回归指标代替检测指标的原因。

| 评价层面  | 最小报告内容                                       |
| ----- | -------------------------------------------- |
| 旧威胁保持 | NFR\(_{\rm mw}\)、cNFR\(_{\rm mw}\)、负向与正向翻转计数 |
| 检测风险  | 历史阈值下 FNR、FPR；旧数据与新到达数据分别计算                  |
| 排序能力  | AP；同时报告恶意比例，避免跨年基率变化被忽略                      |
| 时间表现  | 每年结果、最差年份及清楚定义的聚合；不只报最终均值                    |
| 泛化范围  | 已见家族／在训练历史中未见家族分组，字段不足时明确缺失                  |
| 资源    | 新标签数、回放容量、教师缓存、前后向次数、运行时与峰值显存                |

以上为**【待实验验证：指标方案】**。测试集扫描阈值得到的 `TPR@FPR` 可以作为离线排序评价，但不能代替历史校准阈值下的实际部署风险。

另外，不同方法长期轨迹中的旧模型质量可能不同。只比较各自相邻模型的 NFR，会混入保护集合差异。必要时增加一个**从共同旧模型分叉的单次更新比较**；它不需要重新构造完整 2×2。

### 6.3 失败门应事先定义，而不是看完结果后解释

以下是**【待实验验证：停止条件模板】**，不替代已有合同中的具体容忍值。

| 失败门       | 什么情况下不能支持相应主张                           |
| --------- | --------------------------------------- |
| **正锚点门**  | ER 未通过原有相对 Naive 的正增益检查；不得用后续保护项掩盖该问题   |
| **回归增量门** | ER＋PCT 没有降低配对旧恶意翻转，或相对普通蒸馏没有增量          |
| **漏报代价门** | 翻转下降，但旧／新时段 FNR 恶化超过预先容忍值               |
| **误报门**   | 只能通过降低阈值、提高 FPR 获得所谓安全收益                |
| **适应停滞门** | 保护项使模型接近冻结；新时段 AP、召回或旧漏报修复明显受损          |
| **记忆泛化门** | 保护效果仅出现在训练 buffer，独立历史评价集没有改善           |
| **证据不足门** | 合格旧真阳性过少，无法支持稳定的风险比较；应记“未能判定”，而非“零回归有效” |
| **资源门**   | 优势依赖额外训练模型、更多标签、更多样本访问或未计费的计算           |
| **时序门**   | 参考集合、阈值或参数使用了尚未到达的标签／目标测试结果             |

在线是否接受更新只能依据当时可用的历史材料；封存测试上的失败门用于事后检验研究假设，不能被循环用于挑选最终模型。

---

## 七、理论深度、实现成本与不能扩大的证据边界

### 7.1 理论上最有价值的不是再增加一个损失名词

**【基于论文的推论】**这一方向的理论问题可以明确为：训练中的代理风险是否控制目标翻转风险、有限记忆是否代表历史安全集合、约束是否可行，以及控制历史回归需要付出多少新时段风险。

其中 RCAT 已经给出条件集合上的非回归约束及一致性分析；GEM/A-GEM 已给出梯度约束框架。把这些内容重新命名不构成新的理论贡献。真正的差量必须说明它们在**有限记忆、时间相关样本、旧模型与记忆不独立、非对称风险**条件下哪里失效，以及新的设计究竟补了哪一处。([arXiv][11])

一个可用的证据尺度提醒是：对独立、未用于优化的保护评价样本，即使观察到零次翻转，单侧置信上界也不为零。若有 \(n\) 个符合独立伯努利模型的样本，95% 单侧上界为：

$$
1-0.05^{1/n}.
$$

**【基于统计模型的推论】**即使 \(n=200\)，该上界仍约为 1.5%；而真实恶意保护子集可能远小于总记忆容量。对反复用于优化的 buffer，不能直接套用这个独立审计解释。

### 7.2 实现与计算成本

| 方法        | 根据算法结构可预期的额外工作                  | 本轮不能确认的内容            |
| --------- | ------------------------------- | -------------------- |
| ER＋PCT    | 冻结教师、正确性 mask、蒸馏项；教师输出可在条件固定时缓存 | LAMDA 实测时长、显存和收益     |
| DER++     | 保存历史 logits；官方实现包含额外的记忆损失计算     | 当前 LAMDA 预算下是否优于 PCT |
| A-GEM 类约束 | 参考风险反向传播、梯度投影、优化器方向处理           | 有限步长下实际风险是否守住        |
| GEM       | 多历史任务梯度、QP、明确总容量分配              | 是否值得其额外计算            |
| RCAT      | 扰动生成与内层优化，还需有效威胁模型              | 对真实 APK 时间漂移的适用性     |
| MPT       | 额外参考模型训练、类别扩张与 margin 处理        | 固定二分类下有无必要           |

这里的成本判断是**【基于原文／代码结构的推论】**，不是单卡性能实测。DER++ 与 GEM 的具体实现路径已核对；其余方法不能凭“公开代码”就推定能无修改运行 LAMDA。  ([arXiv][11])

### 7.3 仅概念相关，不能宣称为已验证来源的情况

**【证据边界】**

* **RCAT → LAMDA 时间安全：**原文的对抗鲁棒性回归不等于年度概念漂移回归；其理论假设也不是漂移流自动满足的。
* **MPT → 新年份／新恶意家族：**新年份不是新输出类别；二分类中新出现的家族也未必对应新增分类头。
* **DER++／GEM → 零负向翻转：**输出保持或平均损失约束都不等于逐样本检测保证。
* **主动学习、生成式或多样性回放 → 安全约束：**获得标签、生成旧分布或提高覆盖，与约束旧正确样本回归是不同环节。本轮没有据此认定已经存在适配 LAMDA 标签延迟协议的完整组合。

**【不确定性】**本轮未核准 Android Regression-aware CL 的独立官方实验实现，也未完成其 IEEE 出版版与 arXiv v2 的逐项对照；上述结果严格绑定所读版本。没有运行 LAMDA 实验，也没有建立这些方法在同一 LAMDA 协议下的优劣排名。既有全时期预处理问题仍限制严格时间外推措辞，新增回归损失不会消除这一资格问题。

---

## 最终建议

**【基于论文的推论】保持原计划：先验证标准 ER；通过后，以 ER＋PCT/FD-LM 作为最直接的成熟安全回归来源，用 ER＋普通蒸馏解释增量。**只有当配对诊断证明“对称保持牺牲适应”或“总体保护仍遗漏旧恶意风险”等具体病灶时，再引入一种条件风险改造，并与 ER＋PCT 比较。

第三章能够提出的有意义问题，不是“回放后再加一个模块是否有效”，而是：

> **在标签只能按时到达、历史记忆有限且误报预算不放宽的条件下，能否减少旧恶意真阳性的负向回归，同时保留对新时段威胁的学习能力？**

成熟文献已经提供了可复用的损失、优化与反例；**这个问题在你的 LAMDA 协议下是否成立，仍完全属于待实验证据。**

[1]: https://arxiv.org/html/2507.18313v2 "Regression-aware Continual Learning for Android Malware Detection"
[2]: https://arxiv.org/pdf/2507.18313v2 "https://arxiv.org/pdf/2507.18313v2"
[3]: https://iris.unica.it/cris/rp/rp03282?utm_source=chatgpt.com "ROLI, FABIO"
[4]: https://openaccess.thecvf.com/content/CVPR2021/html/Yan_Positive-Congruent_Training_Towards_Regression-Free_Model_Updates_CVPR_2021_paper.html "https://openaccess.thecvf.com/content/CVPR2021/html/Yan_Positive-Congruent_Training_Towards_Regression-Free_Model_Updates_CVPR_2021_paper.html"
[5]: https://arxiv.org/pdf/2011.09161v3 "https://arxiv.org/pdf/2011.09161v3"
[6]: https://proceedings.neurips.cc/paper/2020/hash/b704ea2c39778f07c617f6b7ce480e9e-Abstract.html "https://proceedings.neurips.cc/paper/2020/hash/b704ea2c39778f07c617f6b7ce480e9e-Abstract.html"
[7]: https://papers.nips.cc/paper_files/paper/2017/hash/f87522788a2be2d171666752f97ddebb-Abstract.html "https://papers.nips.cc/paper_files/paper/2017/hash/f87522788a2be2d171666752f97ddebb-Abstract.html"
[8]: https://papers.nips.cc/paper_files/paper/2017/file/f87522788a2be2d171666752f97ddebb-Paper.pdf "https://papers.nips.cc/paper_files/paper/2017/file/f87522788a2be2d171666752f97ddebb-Paper.pdf"
[9]: https://arxiv.org/abs/1812.00420 "[1812.00420] Efficient Lifelong Learning with A-GEM"
[10]: https://arxiv.org/abs/2402.17390 "[2402.17390] Robustness-Congruent Adversarial Training for Secure Machine Learning Model Updates"
[11]: https://arxiv.org/html/2402.17390v2 "Robustness-Congruent Adversarial Training for Secure Machine Learning Model Updates"
[12]: https://ojs.aaai.org/index.php/AAAI/article/view/37825?utm_source=chatgpt.com "Mitigating Negative Flips via Margin Preserving Training | Proceedings of the AAAI Conference on Artificial Intelligence"
[13]: https://arxiv.org/html/2511.08322v2 "Mitigating Negative Flips via Margin Preserving Training"
