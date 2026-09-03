---
title: "Word_基于流形约束与课程式强化学习的网络攻击检测大模型研究_王童童"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "根目录"
source_pdf: "raw/Word_基于流形约束与课程式强化学习的网络攻击检测大模型研究_王童童.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

学号： 245617

# 东南大学专业学位型研究生学位论文开题报告及论文实施计划

院（系、所） 网络空间安全学院

学 位 类 别 工程硕士

专 业 领 域 网 络 与 信 息 安 全

研究生姓名 王童童

指导教师（校内） 万长胜

指导教师（校外） 闫新成

开题报告日期 2026.1.30

东南大学研究生院制表

## 填 表 须 知

1、论文开题报告由研究生本人向审议小组报告并听取意见后，由研究生本人填写此表。

2、论文开题报告填写完成后，必须经导师审批，通过后方能提交。

3、博士生应在第四学期内、硕士生应在第三学期内完成此开题报告。开题报告经研究生秘书在网上审核确认（硕士生至少半年、博士生至少一年）后方可申请答辩。

4、研究生开题前应填写查新报告。查新报告对专业学位博士作为必要环节。博士生查新工作可委托图书馆负责，也可在完成网络文献检索类研究生课程的学习或参加学校组织的网络文献检索培训后，自行组织查新检索，自行组织查新需要详细文献查新述评作为附件。自行查新报告须经导师审查后由开题报告审核专家组审核签字（或盖章）。硕士生开题查新参考上述办法，不作硬性要求。

5、本表一式两份，一份研究生自留放入本人“研究生档案材料袋”；一份由院（系、所）保存并归入院（系、所）研究生教学档案。

6、学位类别为：工程硕士；公共管理硕士；法律硕士（非法学）；工商管理硕士；建筑学硕士；风景园林硕士；临床医学硕士；公共卫生硕士；旅游管理硕士；会计硕士；国际商务硕士；资产评估硕士；工程管理硕士；艺术硕士；工程博士；医学博士等。

7、本表下载区：http://seugs.seu.edu.cn/3676/list.htm 。本表电子文档打印时用 A4 纸张，格式不变，内容较多可以加页。

## 一、学位论文开题报告

<table><tr><td>论文题目</td><td colspan="9">基于流形约束与课程式强化学习的网络攻击检测大模型研究</td></tr><tr><td>研究方向</td><td colspan="9">人工智能安全</td></tr><tr><td rowspan="2">题目来源</td><td>国家</td><td>部委</td><td>省</td><td>市</td><td>厂、矿</td><td>自选</td><td>有无合同</td><td>经费数</td><td>备注</td></tr><tr><td></td><td></td><td></td><td></td><td></td><td>√</td><td></td><td></td><td></td></tr><tr><td rowspan="2">题目类型</td><td>理论研究</td><td>应用研究</td><td>工程技术</td><td>跨学科研究</td><td>其他</td><td colspan="4"></td></tr><tr><td></td><td>√</td><td></td><td></td><td></td><td colspan="4"></td></tr><tr><td colspan="10"></td></tr></table>

开题报告内容（具体要求见《东南大学研究生论文选题和开题报告的原则和要求》）

## 1 研究意义和背景

## 1.1 研究背景

随着网络空间威胁环境的日益复杂，针对“零日漏洞”及复杂变种攻击的检测已成为网络防御的痛点。传统的入侵检测系统（Intrusion Detection System，IDS）依赖特征匹配，难以应对未知威胁<sup>[1,</sup> <sup>2]</sup>；而基于监督微调（Supervised Fine-Tuning，SFT）的大语言模型虽然具备一定的语义理解能力，但在处理高维度安全日志时，往往因缺乏深层逻辑推理而产生“特征腐蚀”和“逻辑漂移”，导致严重的过拟合现象<sup>[3,</sup> <sup>4]</sup>。

特征腐蚀是指原始输入数据（如网络报文中的特定Payload字符、异常的流量五元组特征）在经过深度神经网络（如数十层的 Transformer）多层非线性变换后，关键的底层细节逐渐模糊、扭曲甚至丢失的现象<sup>[5]</sup>。

逻辑漂移是指模型在进行长链条思维链（Chain-of-Thought, CoT）推理时，后续的推理步骤逐 渐偏离初始事实或预设逻辑轨道，导致推理过程与最终结论产生断层的现象<sup>[6,</sup> <sup>7]</sup>。

## 1.2 研究意义

探索将Stiefel流形正交约束引入大模型跨层超连接（Hyper-Connections）设计中，通过几何约束解决深层安全推理网络训练的稳定性问题；同时验证“自我验证”机制在非数学领域的安全推理任务中的有效性。

针对受限算力环境，提出一套可落地的基于Stiefel流形约束的课程式群体相对策略优化（GroupRelative Policy Optimization，GRPO）训练范式，显著提升企业级防御系统在低资源消耗下发现未知变种攻击的成功率与准确率。

## 2 国内外研究现状

## 2.1 大语言模型在安全检测中的应用

OpenAI、Google等机构验证了GPT-4、Gemini在静态代码分析与恶意软件分类中的有效性<sup>[8]</sup>，提出了利用检索增强生成（Retrieval-Augmented Generation，RAG）缓解安全知识滞后的方案<sup>[9]</sup>。

奇安信、深信服等厂商推出了“安全垂直大模型”，通过SFT 将传统IDS 日志转化为自然语言进行检测。

## 局限性：

（1）过度依赖 SFT 导致模型对训练集外的变种攻击缺乏识别能力。

（2）缺乏推理逻辑，无法解释为何将某一流量判定为攻击。

## 2.2 推理原生模型与CoT研究

DeepSeek-R1 与 OpenAI o1 证明了通过强化学习可以激发模型的思维链能力<sup>[10]</sup>；DeepSeekMath-V2 提出了“自我验证”逻辑<sup>[11]</sup>。

## 局限性:

（1）在安全长文本下，思维链容易产生“幻觉”，推理过程与结论不符。

（2）目前的自我验证机制多集中于数学或者代码领域，网络安全领域的逻辑对齐研究尚处于起步阶段。

## 2.3 神经网络几何约束与强化学习的课程采样策略

Wang等人（2025）探讨了在Stiefel流形上进行LoRA优化的黎曼流形算法，证明了正交约束能稳定深层网络训练<sup>[12]</sup>。

Feng 等人（2025）提出了基于奖励的课程采样（Reward-based Curriculum Sampling，RCS），利用离线分阶段训练提升了意图检测的泛化性<sup>[13]</sup>。

## 局限性:

（1）尚未有研究将流形几何约束应用于解决安全日志处理中的“特征腐蚀”问题。

（2）现有课程学习多为“离线静态”模式，缺乏根据模型实时能力进行动态调整的“在线”机制。3 研究方案

如图 3-1，本课题围绕复杂网络攻击检测，设计一个通用的安全检测与校准框架 H-ORL（Hyper-Connections Online Reinforcement Learning）：

（1）架构层：通过跨层流形约束解决特征腐蚀；

（2）机制层：通过引入 <check> 审计环节解决逻辑漂移；

（3）策略层：通过强化学习动态采样跳出泛化性陷阱。

![](images/a61d250235b4d53b64841788ccdb7fd1850bb6b9971da2125f273a31bf5ed47d.jpg)  
图 3-1 H-ORL 总体架构

## 3.1 在线自适应课程采样算法 Online RCS

在复杂网络威胁环境下，传统检测器往往难以有效识别具有深层逻辑伪装的攻击行为及分布外流量样本。针对上述挑战，本研究提出了一种基于逻辑推演的自适应检测框架。

在泛化性能方面，本框架通过对“困惑样本”的针对性训练，克服了传统模型过度依赖特征记忆的局限性，显著提升了模型的逻辑泛化能力。为解决反馈滞后问题，本研究摒弃了传统的 训练-筛选-重练”循环，实现了采样策略与模型状态的近实时同步。同时针对数据噪声引入方差判定机制识别“低分低方差”样本，通过自动过滤不可学习的噪声数据防止梯度污染。

本算法的创新之处在于：首先，将 GRPO 算法的组内方差转化为在线课程的学习权重，构建了模型能力的闭环反馈机制。其次，引入Jaccard软奖励函数，缓解了网络安全检测中离散打分导致的强化学习信号稀疏问题。最后，通过将底层 Stiefel 流形物理约束与高层自适应课程策略相耦合，实现了检测架构稳定性与策略灵活性的有机统一。

## （1） 系统建模与问题形式化

为了引导模型在生成检测结论时兼顾逻辑深度与表达规范，本研究设计了一种综合考量语义准确性与格式规范性的多维度奖励模型。

$$
R _ {t o t a l} = \lambda_ {a n s w e r} \cdot R _ {a n s w e r} + \lambda_ {f o r m a t} \cdot R _ {F o r m a t}
$$

首先，在过程规范性方面，本研究引入了格式奖励函数 $R _ { f o r m a t }$ 。该机制强制约束模型生成包含<thought>和<check>标签的标准思维链结构，从而确保推理路径的可解释性。此举旨在防止模型在强化学习过程中出现“奖励作弊”现象，即避免模型因过度追求结果得分而跳过必要的逻辑推理步骤，导致推理过程坍缩。

$$
R _ {\text { format }} = \left\{ \begin{array}{l} 1, \text { if   format   is   correct } \\ 0, \text { otherwise } \end{array} \right.
$$

其次，在结果准确性方面，针对网络安全检测任务中常见的奖励信号稀疏问题，本研究摒弃了传统的二元奖励（0/1）模式，引入了基于Jaccard系数的软奖励机制。该机制通过评估检测结论与真实威胁标签集合之间的语义重合度，为模型提供更具连续性的梯度信号，从而有效缓解因“非黑即白”的硬性打分导致的收敛困难问题，提升模型在复杂攻击检测下的泛化表现。

$$
R _ {a n s w e r} = \frac {\mid Y _ {p r e d} \cap Y _ {t r u e} \mid}{\mid Y _ {p r e d} \cup Y _ {t r u e} \mid + \epsilon}
$$

式中， $Y _ { p r e d }$ 和 $Y _ { t r u e }$ 分别代表预测与真实的网络攻击标签集合。

在强化学习训练过程中，均匀采样往往会导致模型在已收敛样本上浪费大量算力。为此，本研究提出了一种基于奖励方差驱动的动态采样模型，旨在实现计算资源的精准投放。

其一，构建基于决策确定性的奖励方差模型。在 GRPO 框架下，针对特定攻击样本生成的多个推理轨迹，本研究通过量化组内奖励的差异程度来衡量模型的决策确定性。其计算公式为：

$$
\sigma^ {2} (x) = \frac {1}{G} \sum_ {j = 1} ^ {G} (r _ {j} - \overline {{r}}) ^ {2}
$$

其中，G为组大小， $\boldsymbol { \mathrm { r } } _ { j }$ 为第j个轨迹的奖励值。高方差表征模型在面对该样本时生成的推理路径存在显著歧义，即该样本处于模型的“认知边缘”或“决策困惑区”。这类样本具备极高的学习价值，是提升模型逻辑鲁棒性的关键。

其二，实现样本权重的动态归一化与概率采样。基于上述方差指标，本研究建立了一种实时反馈机制。通过对所有待学习样本的权重进行归一化处理，计算下一轮迭代的采样概率：

$$
P _ {t + 1} (x) = \frac {W _ {t + 1} (x)}{\sum_ {x ^ {\prime} \in D} W _ {t + 1} (x ^ {\prime})}
$$

其中t表示第t轮迭代， $W ( x )$ 表示样本的权重值。

在算法的优化阶段，本研究旨在构建一个既能驱动逻辑推演能力进化，又能维持架构稳定性的学习框架。

其一，构建 GRPO策略梯度损失函数。区别于传统的 Actor-Critic架构，GRPO 通过组内相对得分获取基准反馈。本研究设计的策略损失函数 $\mathcal { L } _ { \mathit { G R P O } }$ 定义如下：

$$
\mathcal {L} _ {G R P O} (\theta) = \mathbb {E} \left[ \frac {1}{G} \sum_ {i = 1} ^ {G} \left(\min \left(\frac {\pi_ {\theta} \left(o _ {i} \mid q\right)}{\pi_ {\theta_ {o l d}} \left(o _ {i} \mid q\right)} A _ {i}, \operatorname{clip} \left(\frac {\pi_ {\theta} \left(o _ {i} \mid q\right)}{\pi_ {\theta_ {o l d}} \left(o _ {i} \mid q\right)}, 1 - \epsilon , 1 + \epsilon\right) A _ {i}\right) - \beta D _ {K L} \left(\pi_ {\theta} \| \pi_ {r e f}\right)\right) \right]
$$

其中， $A _ { i }$ 为组内奖励的相对表现计算优势函数：

$$
A _ {i} = \frac {r _ {i} - \operatorname{mean} \left(\left\{r _ {1} , r _ {2} , \dots , r _ {G} \right\}\right)}{\operatorname{std} \left(\left\{r _ {1} , r _ {2} , \dots , r _ {G} \right\}\right)}
$$

其二，构建耦合几何约束的联合损失函数。为了实现逻辑层面与物理层面的双重对齐，本研究提出了一个端到端的联合损失优化目标 $\mathcal { L } _ { t o t a l }$ 。该损失函数由两部分组成：

$$
\mathcal {L} _ {t o t a l} = \mathcal {L} _ {G R P O} + \boldsymbol {\lambda} \cdot \mathcal {L} _ {m a n i f o l d}
$$

其中， $\mathcal { L } _ { m a n i f o l d }$ 代表作用于模型底层参数的 Stiefel流形几何约束,用于保证权重更新在高维流形上的物理稳定性； 为平衡系数。

## （2） 核心算法流程

## Step 1：系统初始化

在训练启动阶段，将样本池中所有检测样本的初始权重 统一设为 $1 . 0 \circ$ 。通过构建均匀的初始分布，确保模型在首轮迭代中能够对各类攻击变体进行无偏的探索性学习。

## Step 2：动态加权采样

进入主循环后，系统根据实时更新的权重分布构建当前 Batch。采样策略采取非对称增强原则：降低已掌握样本的出现频率，提高“困难但可学”样本的采样概率，实现算力资源的启发式分配。

## Step 3：多路推演探索

针对 Batch 中的每个 Prompt，模型并行生成 G 个不同的推理轨迹。该步骤不仅要求模型给出检测结论，还强制生成包含推理（Thought）与自检（Self-Verification）的思维链，为后续的组内相对评估提供充足的统计样本。

## Step 4：多维奖励评价

对生成的G个轨迹进行并行打分：

<sub>•</sub> Jaccard 软奖励：衡量检测结论集合与真实威胁标签集合的语义重合度，提供平滑的梯度信号。

<sub>•</sub> Format 奖励：检查<thought>和<check>标签的完备性，防止模型通过跳过推理逻辑来规避计算压力。

## Step 5：实时状态统计

系统即时计算当前组内 G个回复的奖励均值 $\mu$ 与方差 $\sigma ^ { 2 }$ 。通过方差量化模型在该样本上的决策不确定性，从而识别该样本在当前模型认知图谱中的位置。

## Step 6：在线课程更新

根据统计反馈，将样本动态划分为三个区域并更新其在样本池中的权重 ：

<sub>•</sub> 困惑区：方差 $\sigma ^ { 2 }$ 较大，表明模型产生犹豫。系统增加权重，通过“刻意练习”强化逻辑推演。

<sub>•</sub> 熟练区：高分且方差较小，表明模型已稳健掌握。系统降低权重，释放算力并规避过拟合风险。

<sub>•</sub> 盲区/数据噪声：持续低分且方差极小。系统判定为不可学数据或脏数据，执行冷处理（权重衰减），防止无效梯度污染参数空间。

## Step 7：多目标联合更新

最后，模型执行反向传播。联合损失函数 $\mathcal { L } _ { t o t a l }$ 同时融合了 GRPO 策略损失与 Stiefel 流形几何约束损失。这种“逻辑演进+物理约束”的耦合机制，确保模型在快速迭代中既能提升检测精度，又能维持底层权重矩阵的数学稳定性。

## 3.2 内生自我验证推理机制

针对传统检测模型因背景噪声导致的误判问题，本研究提出了一种 二次审计 机制。该机制不再仅依赖初次的模式匹配或概率判定，而是对高频告警执行深度的逻辑回溯，旨在从海量数据中精准剔除由环境噪声引发的虚假威胁。

针对当前大语言模型在网络安全领域应用时普遍存在的逻辑漂移与安全幻觉问题——即模型虽然能够捕捉到攻击特征，却在长文本推演中产生因果断层，甚至自行“脑补”不存在的攻击行为——本研究通过建立强制性的事实核查点，确保检测结论的逻辑自洽与严密性。同时，针对深度学习模型长期存在的“黑盒不可解释性”痛点，本研究致力于将模糊的判定过程转化为结构化的“审计报告”，从而显著提升检测结果的可信度与实战价值。

在技术实现上，本研究的主要创新点在于定义了专用的<check>标签，实现了检测逻辑在原子层面的实时自审。

## 3.3 流形约束的跨层超连接

在处理跨越长文本日志的复杂攻击链路时，传统基于 Transformer的串行架构往往面临记忆衰减与特征表征能力的瓶颈。特别是当攻击载荷经过高度混淆处理时，单一的高层语义信息难以捕捉深藏于字节流中的细微异常。针对这一挑战，本研究提出了一种“物理-语义”协同研判机制，旨在增强模型对长程依赖特征的捕捉能力，并利用底层原始字节特征辅助高层语义进行多粒度联合决策。

在深层网络优化方面，本研究重点解决了传统架构中的特征腐蚀问题。由于底层特征在经过数十层非线性映射后，关键证据极易被高层抽象语义“淹没”，导致模型在处理高度混淆的样本时失去判别依据。通过引入跨层拓扑创新，本研究打破了传统的串行连接范式，构建了物理特征与语义特征并行的异构流。然而，跨层残差注入往往会引发梯度不稳定与数值振荡，进而导致训练发散。为此，本研究创新性地将黎曼几何优化理论引入网安检测领域，通过在 Stiefel 流形上进行架构级的物理约束，利用严格的流形约束替代单纯的数据驱动优化，从数学底层确保了异构特征融合时的数值稳定性与收敛速度。

## （1）系统建模与问题形式化

首先是Stiefel流形约束模型，本研究要求LoRA的低秩适配器矩阵 $A \in \mathbb { R } ^ { r \times d }$ （其中r为秩，d为特征维度）的行向量相互正交。在数学上，这意味着矩阵 必须被约束在Stiefel流形 $\mathcal { V } _ { r } ( \mathbb { R } ^ { d } )$ 之中，其定义如下：

$$
\mathcal {V} _ {r} (\mathbb {R} ^ {d}) := \{A \in \mathbb {R} ^ {r \times d}: A A ^ {T} = I _ {r} \}
$$

其中， $I _ { r }$ 表示 $r \times r$ 的单位矩阵。该物理约束确保了权重更新在高维空间中始终沿着正交基演进，从而有效避免了深度学习中常见的特征坍塌现象。

然后是流形正则化损失 $\mathcal { L } _ { m a n i f o l d }$ ，该项用于衡量矩阵 偏离正交状态的 Frobenius 距离：

## （2）架构设计

$$
\mathcal {L} _ {m a n i f o l d} = \left\| A A ^ {T} - I _ {r} \right\| _ {F} ^ {2}
$$

如图 3-2 所示，为了在保证基础模型泛化性能的同时实现高效的特征重定向，本研究采取了冻结主干参数的策略，并实施了一种非侵入式的轻量化架构改造。

在拓扑结构层面，本研究开发了专用的 HyperConnectionManager 模块。该模块通过调用PyTorch 的 Hook 机制，在不修改 Transformer 原始计算图的前提下，精准捕获浅层表征特征并缓存。捕获的特征随后经由适配器（Adapter）进行流形变换与维度对齐，并以残差注入的方式馈送至深层网络，从而建立起跨越长距离层级的异构特征流。

![](images/7d86dde99ad890e973d868d2dd443b7c6a34bda8e607863e4346d98bed330bf5.jpg)  
图3-2流形约束的跨层超连接架构

## 4 参考文献

[1] Hubballi, Neminath, and Vinoth Suryanarayanan. "False alarm minimization techniques in signature-based intrusion detection systems: A survey." Computer Communications 49 (2014): 1-17.

[2] Touré, Almamy, et al. "A framework for detecting zero-day exploits in network flows." Computer Networks 248 (2024): 110476.

[3] Xie, Zhixin, Xurui Song, and Jun Luo. "Attack via Overfitting: 10-shot Benign Fine-tuning to Jailbreak LLMs." arXiv preprint arXiv:2510.02833 (2025).

[4] Li, Ziniu, et al. "Entropic Distribution Matching in Supervised Fine-tuning of LLMs: Less Overfitting and Better Diversity.(2024)." URL https://arxiv. org/abs/2408.16673.

[5] Koukoulis, Ippokratis, Ilias Syrigos, and Thanasis Korakis. "Self-Supervised Transformer-based Contrastive Learning for Intrusion Detection Systems." arXiv preprint arXiv:2505.08816 (2025).

[6] Li, Songze, et al. "Last Layer Logits to Logic: Empowering LLMs with Logic-Consistent Structured Knowledge Reasoning." arXiv preprint arXiv:2511.07910 (2025).

[7] He, Kaifeng, et al. "AdaDec: Uncertainty-Guided Adaptive Decoding for LLM-based Code Generation." arXiv preprint arXiv:2506.08980 (2025).

[8] Jelodar, Hamed, et al. "Large Language Model (LLM) for Software Security: Code Analysis, Malware Analysis, Reverse Engineering." arXiv preprint arXiv:2504.07137 (2025).

[9] Borah, Arnabh, Md Tanvirul Alam, and Nidhi Rastogi. "Adapting Large Language Models to Emerging Cybersecurity using Retrieval Augmented Generation." arXiv preprint arXiv:2510.27080 (2025).

[10] Guo, Daya, et al. "Deepseek-r1: Incentivizing reasoning capability in llms via reinforcement learning." arXiv preprint arXiv:2501.12948 (2025).

[11] Shao, Zhihong, et al. "Deepseekmath-v2: Towards self-verifiable mathematical reasoning." arXiv preprint arXiv:2511.22570 (2025).

[12] Park, Juneyoung, et al. "Riemannian Optimization for LoRA on the Stiefel Manifold." arXiv preprint arXiv:2508.17901 (2025).

[13] Feng, Zihao, et al. "Improving Generalization in Intent Detection: GRPO with Reward-Based Curriculum Sampling." arXiv preprint arXiv:2504.13592 (2025).

研究生签名

年 月 日

## 二、学位论文工作实施计划

# （一）论文的理论分析与硬件要求及其预期达到的水平与结果

## 1. 理论分析

## （1）基于Stiefel 流形的黎曼优化理论

理论上，正交矩阵具有等距变换特性，其奇异值始终为 1。通过将流形损失引入总损失函数，可以证明在跨层超连接中，梯度范数在反向传播过程中能保持稳定，从数学机理上抑制深层推理网络中的“特征腐蚀”现象。

## （2）课程式强化学习的收敛性分析

在线自适应课程采样本质上是在训练过程中动态调整样本分布的信息熵，理论上能使模型始终处于最近发展区，从而比随机采样更快地跨越强化学习的稀疏奖励陷阱。

## （3）形式化逻辑校验

通过引入 标签，将原本隐式的内部状态转化为显式的逻辑审计步骤，利用模型内生的语义对比能力，从概率判别转变为逻辑推导，解决网络安全检测中的“逻辑漂移”问题。

## 2. 硬件要求

（1）显卡 (GPU)

NVIDIA GeForce RTX 4090 (24GB VRAM) \* 1。

（2）存储空间

1TB NVMe SSD。

（3）内存 (RAM)

64GB DDR5。

## 3. 预期水平与结果

在未经训练的分布外数据集上，展示出极强的迁移学习能力，其检测衰减率显著低于传统深度学习模型，证明 H-ORL框架捕捉的是攻击逻辑而非简单特征。

通过 Self-Verification 机制，降低推理过程中的“安全幻觉”率，显著提升检测结果的可解释性，满足工业级研判的需求。

构建一套完整的H-ORL 攻击检测与校准原型系统。包含受 Stiefel 流形约束的 Adapter插件、在线自适应采样引擎及多维奖励评估模块。

## （二）论文工作进度与安排

<table><tr><td>起讫日期</td><td>工作内容和要求</td><td>备注</td></tr><tr><td>2026.01-2026.02</td><td>完成学位论文文献调研,理清学位论文整体脉络和思路</td><td></td></tr><tr><td>2026.03-2026.05</td><td>基于现有工作和结果,完成学位论文“在线自适应课程采样算法”章节的撰写</td><td></td></tr><tr><td>2026.06-2026.08</td><td>基于现有工作和结果,完成学位论文“内生自我验证推理机制”章节的撰写</td><td></td></tr><tr><td>2026.09-2026.11</td><td>基于现有工作和结果,完成学位论文“流形约束的跨层超连接”章节的撰写</td><td></td></tr><tr><td>2026.12-2027.02</td><td>完成学位论文撰写,学位论文定稿</td><td></td></tr><tr><td>2027.03-2027.05</td><td>制作PPT并准备毕业论文答辩</td><td></td></tr><tr><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td></tr><tr><td>学校指导教师对开题报告的综合意见</td><td colspan="2">指导教师(签字) 年 月 日</td></tr><tr><td>校外指导教师对开题报告的综合意见</td><td colspan="2">指导教师(签字) 年 月 日</td></tr><tr><td>开题报告审议情况记录</td><td colspan="2">1、审议小组成员(硕士至少5人,博士5-7人,其中1人须为校外导师):组长:成员:2、审议小组意见3、投票表决结果审议小组出席____人;通过____人;不通过____人。开题报告质量____(优、良、中、通过)4、审议小组组长(签名)审议小组成员(签名)年 月 日</td></tr><tr><td colspan="3">院(系、所)意见:院(系、所)负责人签名(或印章)年 月 日</td></tr><tr><td colspan="3">备注:</td></tr></table>