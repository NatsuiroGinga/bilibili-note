---
title: "FT-Transformer-Based IoT Network Attack Detection and Cross-Dataset Generalization Analysis"
authors: [Fapeng Li, Yatong Tao, Leilei Qu]
year: 2026
date: 2026-09-03
journal: "Electronics（MDPI），2026-06-08 出版（收稿 2026-04-30，接收 2026-06-04）"
source_pdf: "[[raw/papers/attack-detection/2026-Li-FT-Transformer-IoT-Attack-Detection.pdf]]"
sha256: "57b366781bdda2e9d3443168409cc4bea8a0be0e2c351608fd7743ba00a51ea3"
tags:
  - FT-Transformer
  - 物联网入侵检测
  - 跨数据集泛化
  - 训练协议
  - 类型/论文
key_finding: "本文用 FT-Transformer 做 IoT 攻击检测（CICIoT2023 主数据集，多个外部数据集做跨数据集验证），训练策略明确使用 AdamW + 学习率衰减 + 早停三者组合，并在正文直接把该组合与训练收敛稳定性挂钩（物理页 7，§3.3）；实测训练过程报告为稳定、无明显震荡（物理页 13，§5.2）。是本次核查的六篇同类工作中唯一一篇明确采用学习率衰减且报告稳定性结论的文献，但未给出衰减的具体机制（步长/系数/触发条件均未披露），也未做加/不加衰减的消融，不能作为因果证据。"
method: "FT-Transformer 处理流级统计特征做二分类/多分类攻击检测；用特征对齐外部验证、特征并集验证、标准化 NetFlow 外部验证、CORAL 域对齐等多种跨数据集泛化协议评估同一模型；辅以 SHAP 可解释性分析"
baseline: "Random Forest、XGBoost、MLP、TabNet、TabTransformer 风格数值 Transformer基线"
aliases:
  - Li2026-FTTransformer-IoT
  - electronics-15-02516
related:
  - "[[../methodology/2021-Gorishniy-表格数据深度学习模型再审视]]"
---

# 基于 FT-Transformer 的物联网网络攻击检测与跨数据集泛化分析

> Li、Tao、Qu，Electronics（MDPI），2026-06-08，物理页 1 至 31。

## 一句话

本文是本次核查六篇同类工作中**唯一明确采用学习率衰减**的一篇：训练策略正文原话把"学习率衰减 + 早停"的组合直接与"提升收敛稳定性、降低过拟合风险"挂钩（物理页 7），随后在训练过程分析章节报告了平稳收敛、无明显震荡的实测结果（物理页 13）。但论文**未披露衰减的具体机制**（是 StepLR、ReduceLROnPlateau 还是其他形式、衰减系数与触发条件均未说明），且**没有做"加衰减 vs 不加衰减"的消融对照**，因此这是一条方向一致但强度较弱的经验性佐证，不能当作因果证明。

## 训练协议（本次核查重点，逐句带页码）

物理页 7，§3.3"Training Strategy"：

> "This study adopts the cross-entropy loss function for both binary and multi-class classification tasks. **AdamW is used as the optimizer, and learning rate decay and early stopping are employed to control the training process.**... During training, **learning rate decay and early stopping are combined to improve convergence stability and reduce the risk of overfitting.**"

物理页 10，§4.3"Experimental Environment and Implementation Details"：

> "In the main FT-Transformer binary classification experiment, the default configuration was set as follows: **d_token = 64, n_layers = 4, dropout = 0.1, batch size = 2048, and learning rate = 1×10⁻³**. An early stopping mechanism was used to select the best model during training."

注意本文的结构与学习率取值**均偏离 Gorishniy 2021 默认配方**：`d_token=64`（非 192）、`n_layers=4`（非 3）、学习率 `1e-3`（比 Gorishniy 默认的 `1e-4` 高一个数量级，落在 Gorishniy Table 13 调参空间 `[1e-5,1e-3]` 的上界）——即本文并未照搬原论文默认值，而是自行选择了一组不同的结构与学习率，衰减策略也是在此基础上叠加的自定义选择。

## 训练稳定性：实测报告为稳定，且明确关联训练策略

物理页 13，§5.2"Analysis of the Training Process"：

> "The training process of FT-Transformer in the binary classification task was generally stable... validation attack-class F1-score gradually increased from 0.9761 to 0.9804, while the validation ROC-AUC reached approximately 0.9952. These results indicate that the model converged steadily during training, **without obvious training instability or severe overfitting**."
>
> "As shown in Figure 6, both the training loss and validation loss generally decrease as the number of training epochs increases... **In addition, no severe fluctuation or obvious overfitting is observed, which further supports the effectiveness of the adopted training strategy.**"

"adopted training strategy" 在上下文中即指 §3.3 的"AdamW + 学习率衰减 + 早停"组合——作者把稳定收敛的结果直接归功于该训练策略，但这是**单臂观察性陈述，不是消融证据**：论文没有报告"若不使用学习率衰减，同一模型/同一数据集会怎样"的对照实验，因此"衰减→稳定"这一因果链只能算作者的经验性主张，不是本文自证的实验结论。

## 证据等级

- 原件级别：完整论文，31 个物理页，MinerU flash-extract 分段转换（第 1-20 页整体 + 第 5、6、7、9、10、11、12、13 页单页核验），精确定位关键段落（物理页 7、10、13）。
- 可支撑：本文训练策略确实包含学习率衰减，且报告训练过程稳定、无明显震荡；这与"衰减→稳定"的方向一致。
- 不可支撑：不能证明"衰减是稳定的原因"——无消融对照，且本文的学习率（1e-3）、结构（d_token=64/n_layers=4）均偏离本课题与 Gorishniy 2021 默认配方，混杂因素多，不能孤立学习率衰减这一个变量的效应。
- 命名提醒：`raw/papers/3712285.3759853.pdf`（未纳入本 worktree，仅在主工作目录）题名同为"FT-Transformer"，但内容是容错计算领域的"Fault-Tolerant Transformer"（UC Riverside/USF，IEEE 会议论文），与本笔记的表格深度学习 FT-Transformer（Feature Tokenizer Transformer）**是两篇完全不相关的论文，纯属缩写撞车**，本次核查已排除该文件。
