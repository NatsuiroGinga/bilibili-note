---
title: "PINN 引文链与恶意流量检测理论映射"
authors:
  - Maziar Raissi 等
  - George Em Karniadakis 等
  - Sifan Wang 等
  - Aditi Krishnapriyan 等
year: 2026
date: 2026-07-17
journal: "多篇 PINN 原始论文与综述的综合阅读笔记"
source_pdf: "[[raw/papers/pinn/1711.10561.pdf]]"
source_pdfs:
  - "[[raw/papers/pinn/1711.10561.pdf]]"
  - "[[raw/papers/pinn/1711.10566.pdf]]"
  - "[[raw/papers/pinn/2410.13228.pdf]]"
  - "[[raw/papers/pinn/2501.06572.pdf]]"
  - "[[raw/papers/pinn/MDPI-ApplSci-2025-15-8092-PINN综述.pdf]]"
  - "[[raw/papers/pinn/paper_0dd9fd2db26952889e10293d9209c0bf.pdf]]"
  - "[[raw/papers/pinn/paper_390db51220335dc4b705f12f777ef9eb.pdf]]"
  - "[[raw/papers/pinn/paper_520fcb7d7e085e3081e0ab5f0c5b4dd5.pdf]]"
  - "[[raw/papers/pinn/paper_ced7ef2c6ebf5b388931d1671a9e9520.pdf]]"
  - "[[raw/papers/pinn/基于物理信息的神经网络：最新进展与展望.pdf]]"
tags:
  - PINN
  - 物理信息机器学习
  - 恶意流量检测
  - 生成式大模型
  - 引文核验
  - 类型/论文
aliases:
  - PINN恶意流量理论映射
  - PINN引文链
key_finding: "标准 PINN 的约束必须作用于模型预测的可微物理状态；当前只生成二分类标签的流量大模型无法从输入侧常数残差获得训练信号。公开流级特征最多支撑一致性正则的类比实验，只有加入时序、拓扑、队列与丢包观测并让模型预测动态状态，才接近严谨的 PINN 路线。"
method: "本地 PDF 全文核查 + 引文链追踪 + Consensus/Sider Scholar 元数据交叉核验 + DOI、出版社和 arXiv 一手来源核验"
baseline: "标准 PINN、纯监督生成式分类、输入侧物理特征工程、输出依赖的一致性约束训练"
---

# PINN 引文链与恶意流量检测理论映射

> 核心判断：**不要把“从输入流量字段计算一个统计量”直接称为 PINN。** 对当前生成式恶意流量探针，物理约束只有在残差依赖模型输出并能对训练参数产生非零梯度时，才可能改变模型训练。

## 1. 结论分级

### 1.1 有直接文献证据的结论

1. 标准 PINN 用神经网络逼近受微分方程支配的状态函数，通过自动微分构造方程残差，并联合优化观测数据、方程、初始条件和边界条件损失。[1]
2. 物理信息机器学习可以比标准 PINN 更宽，物理知识可通过软损失、硬结构或其他可计算约束注入模型；但约束必须与被预测的状态或函数发生关系。[2]
3. 多项损失会造成反向传播梯度失衡和刚性训练，梯度统计或神经切线核可用于解释、诊断和重新加权标准全连接 PINN 的损失分量。[3][4]
4. PINN 的软方程正则可能让优化问题更病态。课程正则和按时间分段的序列学习能在若干偏微分方程基准上降低误差。[5]
5. 残差点的分布会影响 PINN 精度；残差自适应分布和细化方法在偏微分方程正、逆问题中以更少残差点提高了精度。[6]
6. 对真实时间演化系统，若训练忽略时间因果顺序，模型可能先拟合晚期状态而没有解析早期状态；时间加权残差可缓解此问题。[7]

### 1.2 只能作为方法类比的结论

1. **梯度平衡可以迁移为生成式模型的训练诊断。** 可以比较标签生成损失与辅助约束损失的梯度范数和夹角，但 Wang 等人的神经切线核结论建立在无限宽全连接网络及特定偏微分方程假设上，不能直接宣称对 Qwen3 与低秩适配微调成立。[3][4]
2. **残差自适应采样可以类比为困难样本选择。** 原论文选择的是连续时空域中的方程配点，而恶意流量实验选择的是带标签离散样本。两者采样空间和优化目标不同，必须重新做消融。[6]
3. **课程正则可以迁移为逐步增加约束强度或任务难度。** 原始证据来自逐步增加偏微分方程复杂度，不等价于按攻击类别、残差或奖励方差排序流量样本。[5]
4. **因果训练只能迁移到同一系统的有序窗口。** 独立流记录、随机打乱行和缺失稳定时间轴的数据不满足该前提。[7]
5. **硬约束可迁移为输出参数化。** 非负队列、非负速率和严格代数关系可通过模型结构保证；这比事后给损失加一个输入侧常数更接近物理信息机器学习，但仍需验证是否帮助标签生成。[2][9]

### 1.3 当前仍是未经验证的假设

1. 物理一致性辅助任务会提高生成式大模型的恶意流量宏平均 F1、少样本能力或跨数据集泛化。
2. 请求/响应比、握手缺失、流量熵偏移等统计量在 GeNIS、HIKARI 和 CICIoT 上都具有稳定且同向的攻击区分力。
3. 物理残差可以代表“样本难度”。残差大可能意味着显性洪泛，反而是容易样本；也可能只是字段缺失、测量噪声或正常业务切换。
4. 当前公开流级数据足以支撑严格 PINN。现有字段审计反而表明，多数严谨动态约束不可观测。
5. 物理残差可直接用作组相对策略优化奖励。若残差只由输入决定，它对同一样本的所有生成结果相同，组内中心化后不会提供策略更新信号。

## 2. 本地 PINN 语料核验

| 本地文件                                     | 已核验身份                                      | 在引文链中的作用                                 | 注意事项                                                                                                                                   |
| -------------------------------------------- | ----------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `1711.10561.pdf`                             | Raissi 等 2017，Part I，数据驱动求解偏微分方程  | 标准 PINN 正问题来源                             | 正式引用优先使用 2019 年《Journal of Computational Physics》合并版 [1]                                                                     |
| `1711.10566.pdf`                             | Raissi 等 2017，Part II，数据驱动发现偏微分方程 | 标准 PINN 逆问题来源                             | 证明原框架预测的是连续物理状态或未知方程参数，不是分类标签                                                                                 |
| `paper_b002d83866255ef3bd48ae3819cf2520.pdf` | `1711.10561.pdf` 的逐字节重复文件               | 无新增证据                                       | 两者 SHA-256 均为 `2a8db677...75fdc400d`，引用时不得计为两篇论文                                                                           |
| `paper_0dd9fd2db26952889e10293d9209c0bf.pdf` | Cuomo 等，arXiv:2201.05624                      | 多任务损失、方法谱系和局限综述                   | 适合发现原始论文，不替代关键论断的一手引用 [8]                                                                                             |
| `paper_ced7ef2c6ebf5b388931d1671a9e9520.pdf` | Cai 等，arXiv:2105.09506，流体力学综述          | 说明 PINN 最成熟的应用依赖真实连续状态与守恒方程 | PDF 首页 DOI 是占位符，不应按占位 DOI 引用；使用 arXiv 标识 [14]                                                                           |
| `基于物理信息的神经网络：最新进展与展望.pdf` | 李野、陈松灿，2022，中文综述                    | 国内研究脉络和中文术语                           | 关键理论仍回到英文原始论文核验                                                                                                             |
| `paper_520fcb7d7e085e3081e0ab5f0c5b4dd5.pdf` | Farea、Yli-Harja、Emmert-Streib，2024 综述      | 技术、应用和挑战补充                             | DOI 为 `10.3390/ai5030074` [12]                                                                                                            |
| `2410.13228.pdf`                             | Toscano 等，2024，From PINNs to PIKANs          | 训练、硬约束、采样、域分解和理论的系统索引       | 适合建立引文链，关键结论需追溯其引用的原论文 [9]                                                                                           |
| `2501.06572.pdf`                             | Wong 等，2026，Evo-PINN 综述                    | 进化优化与混合优化展望                           | **现有 `PINN综述群.md` 将作者写为 Cognola 等，属于元数据错误**；正式作者为 Jian Cheng Wong 等，期刊 DOI 为 `10.1109/MCI.2025.3607749` [10] |
| `MDPI-ApplSci-2025-15-8092-PINN综述.pdf`     | Ren 等，2025 综述                               | 最新方法概览                                     | 其中大量汇总数值不能替代各原始实验，本文不以其百分比作为关键证据 [13]                                                                      |
| `paper_390db51220335dc4b705f12f777ef9eb.pdf` | Luo 等，2025 综合综述                           | 追踪自适应采样、损失加权和失败模式原论文         | DOI 为 `10.1007/s10462-025-11322-7` [11]                                                                                                   |

## 3. 引文链：从标准 PINN 到可迁移训练机制

```text
Raissi 等 2017 Part I/II
  └─ 合并为 Raissi 等 2019：标准 PINN 正问题与逆问题 [1]
      ├─ Karniadakis 等 2021：扩展为物理信息机器学习总框架 [2]
      ├─ Wang、Teng、Perdikaris 2021：复合损失梯度病态与自适应平衡 [3]
      ├─ Wang、Yu、Perdikaris 2022：神经切线核解释损失收敛速率失衡 [4]
      ├─ Krishnapriyan 等 2021：软正则失败、课程正则和序列学习 [5]
      ├─ Wu 等 2023：残差自适应采样 [6]
      └─ Wang、Sankaran、Perdikaris 2024：时间因果加权 [7]

Cuomo 等 2022、Toscano 等 2024、Luo 等 2025
  └─ 汇总上述主线，并扩展到硬约束、域分解、局部权重和新架构 [8][9][11]

Wong 等 2026
  └─ 把损失平衡、架构搜索和元学习视为进化优化机会，而非已证明适合恶意流量的结论 [10]
```

这条引文链对本课题最有价值的不是“再找一个新 PINN 变体”，而是提供四个可检验机制：**输出依赖的约束、复合损失梯度诊断、残差驱动的样本选择、时间有序训练**。

## 4. 严格 PINN 的最小数学条件

设模型预测连续状态 $u_\theta(t,x)$，系统满足：

$$
\frac{\partial u}{\partial t}+\mathcal{N}[u]=0,
\qquad
\mathcal{B}[u]=g.
$$

标准残差和损失为：

$$
r_\theta(t,x)=\frac{\partial u_\theta}{\partial t}+\mathcal{N}[u_\theta],
$$

$$
\mathcal{L}(\theta)
=\mathcal{L}_{\text{data}}
+\lambda_r\,\mathbb{E}_{(t,x)\sim\Omega}\|r_\theta(t,x)\|_2^2
+\lambda_b\,\mathbb{E}_{(t,x)\sim\partial\Omega}
\|\mathcal{B}[u_\theta]-g\|_2^2.
$$

这里有三个不可省略的条件：

1. $u_\theta$ 是模型输出的物理状态或其可微代理，而不是外部预先计算好的输入统计量。
2. 残差 $r_\theta$ 依赖参数 $\theta$，使 $\nabla_\theta \mathcal{L}_{\text{physics}}$ 通常非零。
3. 方程或不变量描述的是研究系统的可验证机制，并且数据提供计算残差所需的状态、边界或代理观测。

如果只满足“损失中出现一个带公式的项”，不满足以上条件，最多属于特征工程或一般一致性正则，不能据此宣称实现了标准 PINN。

## 5. 当前生成式探针为何还不能直接引入 PINN

当前探针学习：

$$
p_\theta(y\mid s(x)),
\qquad
y\in\{\texttt{benign},\texttt{malicious}\},
$$

其中输出严格限制为：

```json
{ "label": "benign" }
```

或：

```json
{ "label": "malicious" }
```

模型没有预测队列、窗口、流量场或下一时刻网络状态。因此，直接从输入 $x$ 计算残差 $c(x)$ 并加入损失会出现以下问题。

### 5.1 输入侧常数残差没有约束梯度

若：

$$
\mathcal{L}_{\text{physics}}(\theta)=\mathbb{E}_x[c(x)^2],
$$

且 $c(x)$ 完全由输入字段计算，则：

$$
\nabla_\theta\mathcal{L}_{\text{physics}}(\theta)=0.
$$

它不会改变任何模型参数。把它写进总损失只是形式上的相加。

### 5.2 输入侧常数奖励会在组相对更新中抵消

对同一输入 $x$ 生成 $G$ 个答案 $y_i$，若奖励是：

$$
R_i=R_{\text{task}}(x,y_i)+\lambda c(x),
$$

则组内中心化后：

$$
R_i-\bar R
=R_{\text{task}}(x,y_i)
-\overline{R_{\text{task}}}.
$$

常数 $c(x)$ 完全抵消。它可以作为**样本权重或采样概率**，但不能冒充区分不同生成结果的可验证奖励。

### 5.3 确定性派生字段不会增加标签信息

若新增物理特征 $z=g(x)$ 是现有输入的确定性函数，则：

$$
I(Y;Z\mid X)=0.
$$

它可能因数值尺度、有限样本或模型优化偏好而改善训练，但不会增加相对于完整输入 $X$ 的贝叶斯信息。实验必须区分“新增信息”“更好表示”和“约束正则”三种解释。

## 6. 当前八个规范字段能支撑什么

当前 `canonical_core_v1` 只有：

```text
total_packets
total_bytes
packet_length_mean
packet_length_min
packet_length_max
iat_mean_ms
packet_rate
byte_rate
```

### 6.1 能构造但理论价值有限的代数一致性

可以近似检查：

$$
r_{\text{size}}
=\frac{B-N\bar\ell}{|B|+\varepsilon},
$$

$$
r_{\text{duration}}
=\frac{B}{\lambda_B+\varepsilon}
-\frac{N}{\lambda_P+\varepsilon},
$$

其中 $N$、$B$、$\bar\ell$、$\lambda_P$ 和 $\lambda_B$ 分别表示总包数、总字节数、平均包长、包速率和字节速率。

但这些字段往往由同一流导出器相互计算，残差对良性与恶意样本都应接近零。它们更适合：

1. 检查数据转换错误；
2. 约束缺失字段重建；
3. 检测被破坏或伪造的流量记录；
4. 作为辅助头的可微一致性正则。

它们不天然构成恶意检测信号，也不证明攻击“违反物理定律”。

### 6.2 当前规范字段不能构造的约束

| 候选             | 缺失观测                                                 | 当前结论 |
| ---------------- | -------------------------------------------------------- | -------- |
| 节点流量平衡     | 拓扑、端口方向、队列变化、丢弃量、节点消费量、同步时间窗 | 不可计算 |
| 请求/响应比      | 前向与后向包/字节字段、应用会话语义                      | 不可计算 |
| TCP 握手状态     | 协议、标志序列、超时和包级顺序                           | 不可计算 |
| 熵平稳性         | 同一时间窗内的多流源/目的分布                            | 不可计算 |
| TCP/AQM 流体方程 | 拥塞窗口、队列、往返时延、容量、丢包概率、连续时序       | 不可计算 |
| 时间因果训练     | 同一实体的可靠时间顺序和连续状态                         | 不可计算 |

因此，当前 H1 探针应保持为纯监督生成式分类，先证明基座可学性。此时引入 PINN 会同时改变输入、输出和训练目标，无法判断增益来源。

## 7. 网络流量“守恒”最容易出现的理论误区

### 7.1 完整守恒方程不会因攻击自动失效

对路由节点的同步窗口，正确的离散队列平衡更接近：

$$
Q_{t+1}
=Q_t+B_t^{\text{in}}-B_t^{\text{out}}
-B_t^{\text{drop}}-B_t^{\text{consume}}.
$$

对应残差为：

$$
r_Q
=\hat Q_{t+1}-Q_t-B_t^{\text{in}}
+B_t^{\text{out}}+B_t^{\text{drop}}+B_t^{\text{consume}}.
$$

**DDoS 流量也服从字节和队列守恒。** 攻击改变输入强度、队列积压和丢弃量，却不会让守恒定律失效。如果把队列变化或丢弃量漏掉，所谓“攻击残差”实质上是未观测状态，不是物理定律被破坏。

严格的检测信号应来自以下至少一种机制：

1. 模型基于良性状态和控制条件预测 $\hat Q_{t+1}$，攻击造成动力学分布偏移，使预测残差上升；
2. 攻击篡改遥测数据，多个测量之间不再满足守恒；
3. 模型联合估计未观测的队列或丢弃量，并通过完整守恒式限制解空间；
4. 攻击被建模为未知外部输入，再估计该外部输入是否显著偏离正常边界条件。

### 7.2 请求/响应比不是守恒律

请求和响应字节比是协议与业务相关的统计规律。下载、上传、视频、域名查询、重传和单向遥测的正常比例可以相差数个数量级。它可以是**协议先验或统计不变量**，但不应称为质量守恒。

### 7.3 握手一致性是协议约束

SYN 与 SYN-ACK 的匹配可以识别部分 SYN 洪泛，但丢包、服务不可达、扫描和正常失败都可能产生半开连接；UDP 和其他协议不适用。它属于有限场景的协议状态机约束。

### 7.4 熵平稳性是分布假设

业务发布、热点事件、备份和故障切流都能改变流量熵。熵偏移可作异常特征，但不是物理守恒，也不能保证跨域稳定。

## 8. 可行的输出依赖约束架构

### 8.1 推荐的最小结构

保留生成式标签头，同时从共享隐藏表示 $h_\theta(x)$ 增加连续辅助头：

$$
\hat s=g_\phi(h_\theta(x)),
$$

其中 $\hat s$ 可以是被遮蔽的流量状态、下一窗口状态或未观测状态代理。总损失为：

$$
\mathcal{L}
=\mathcal{L}_{\text{SFT}}
+\lambda_{\text{rec}}\mathcal{L}_{\text{masked-rec}}
+\lambda_{\text{con}}\mathcal{L}_{\text{constraint}}.
$$

约束残差必须由 $\hat s$ 构造，例如：

$$
\mathcal{L}_{\text{constraint}}
=\|A\hat s-b\|_2^2,
$$

或：

$$
\mathcal{L}_{\text{dyn}}
=\left\|
\frac{\hat s_{t+1}-s_t}{\Delta t}
-F_\psi(s_t,u_t)
\right\|_2^2.
$$

这样物理损失可以通过辅助头和共享表征更新模型参数。

### 8.2 为什么需要遮蔽重建

若模型输入已经包含 $N$、$B$、$\bar\ell$、$\lambda_P$ 和 $\lambda_B$，辅助头只需复制输入便可满足代数关系。应随机遮蔽一部分相关字段，要求模型根据其余字段重建，再比较：

1. 只有遮蔽重建；
2. 遮蔽重建加代数一致性；
3. 遮蔽重建加动态或拓扑约束。

只有第 2 项优于第 1 项，才能把增益归因于一致性约束，而不是一般多任务学习。

### 8.3 生成文本中附带数值不是首选

让模型生成 `label` 和连续物理量虽然可计算完成后残差，但存在两个问题：

1. 离散令牌采样使数值残差不能直接通过监督生成过程反向传播；
2. 模型可能学会代数运算而没有改善恶意检测。

连续辅助头更容易控制变量、计算梯度和做消融。若后续使用强化学习，输出依赖的数值残差才可作为候选奖励，但必须防止模型通过输出虚假数字获得高分。

## 9. 可迁移机制及其适用边界

| PINN 理论或机制        | 原论文证据                             | 对生成式恶意流量模型的迁移               | 证据等级   | 边界                                            |
| ---------------------- | -------------------------------------- | ---------------------------------------- | ---------- | ----------------------------------------------- |
| 方程残差联合损失       | 神经网络预测连续解，方程残差约束解 [1] | 共享表征加连续状态辅助头                 | 方法类比   | 只输出类别令牌时不成立                          |
| 硬约束参数化           | 结构直接满足边界或不变量 [2][9]        | 非负状态、完整平衡式参数化               | 方法类比   | 不能把类别由残差阈值硬编码                      |
| 梯度统计平衡           | 缓解标准 PINN 复合损失梯度失衡 [3]     | 记录标签与约束梯度范数、夹角并自适应加权 | 方法类比   | 神经切线核定理不直接适用于 Transformer 低秩适配 |
| 神经切线核分析         | 解释全连接 PINN 不同损失收敛率 [4]     | 只作为“为何要测梯度冲突”的理论动机       | 弱类比     | 不应写成 Qwen3 收敛定理                         |
| 课程正则               | 逐步增加方程复杂度改善若干基准 [5]     | 逐步增加约束强度、序列长度或攻击扰动     | 方法类比   | 物理残差不等于样本难度                          |
| 残差自适应采样         | 在连续时空中增加高残差配点 [6]         | 重新采样高模型残差且有学习信号的流量窗口 | 方法类比   | 输入侧固定残差可能只是在重复采样异常值          |
| 因果时间权重           | 早期状态未解析前抑制晚期残差 [7]       | 同一主机、会话或拓扑的有序窗口训练       | 有条件类比 | 独立流记录和社区随机镜像不可用                  |
| 进化损失平衡或架构搜索 | 综述认为是研究机会 [10]                | 可作后期自动权重搜索候选                 | 未验证假设 | 计算开销大，不应先于简单梯度平衡基线            |

## 10. 建议的实验裁决顺序

### 阶段 0：先完成当前 H1

不修改当前严格 JSON 二分类任务。先确认 Qwen3-1.7B 在三套数据上的可学性、输出合法率、跨组泛化和效率。H1 失败时，不应叠加物理约束掩盖基座或数据问题。

### 阶段 1：无训练的约束可计算性审计

对每个候选残差分别报告：

1. 所需原始字段及单位；
2. 字段是否直接观测、导出计算或估计；
3. 良性与各攻击家族的残差分布；
4. 分组自助法置信区间、效应量和单残差受试者工作特征曲线下面积；
5. 跨数据集方向是否一致；
6. 缺失、截断、测量窗不同步对残差的影响。

若代数残差对良性和攻击都接近零，应保留为数据质量或辅助重建约束，不得宣称它直接检测攻击。

### 阶段 2：公开流级数据上的最小消融

在同一基座、数据、随机种子、令牌数和训练预算下比较：

| 组别 | 训练目标                    | 用途                     |
| ---- | --------------------------- | ------------------------ |
| A    | 仅标签监督微调              | 主基线                   |
| B    | 标签监督微调 + 遮蔽字段重建 | 控制一般多任务正则       |
| C    | B + 输出依赖的代数一致性    | 检验一致性约束的独立增益 |
| D    | C + 梯度统计自适应权重      | 检验损失平衡机制         |

除宏平均 F1、误报率、未知攻击和跨数据集性能外，还要报告：

$$
\rho_t
=\frac{\|\nabla_\theta\mathcal{L}_{\text{constraint}}\|_2}
{\|\nabla_\theta\mathcal{L}_{\text{SFT}}\|_2+\varepsilon},
$$

$$
\cos_t
=\frac{
\langle\nabla\mathcal{L}_{\text{SFT}},
\nabla\mathcal{L}_{\text{constraint}}\rangle
}{
\|\nabla\mathcal{L}_{\text{SFT}}\|_2
\|\nabla\mathcal{L}_{\text{constraint}}\|_2+\varepsilon
}.
$$

若 B 优于 A 而 C 不优于 B，结论只能是多任务学习有效，不能归因于物理一致性。

### 阶段 3：有拓扑与时序的严格动力学实验

若第三章必须使用 PINN 作为理论主轴，应使用自构造测试床或具备以下观测的数据：

1. 同步时间窗；
2. 拓扑和端口方向；
3. 入站、出站、丢弃、节点消费与队列变化；
4. 可选的链路容量、往返时延、拥塞窗口和协议状态；
5. 正常与攻击边界条件；
6. 按场景或拓扑划分的独立测试集。

此时比较：

1. 仅状态预测；
2. 状态预测加完整守恒残差；
3. 生成式标签训练；
4. 共享表征的状态预测、守恒残差和标签生成联合训练。

攻击本身是边界条件或外部输入，不应被描述为“违反守恒定律”。若研究的是遥测篡改或虚假数据注入，物理测量不一致才更接近已有物理信息攻击检测文献的设定，参见 [[PIGCRN-化工过程攻击检测]]。

### 阶段 4：再考虑课程或强化学习

只有阶段 2 或阶段 3 证明约束损失产生独立增益后，才测试残差引导的样本调度或奖励。强化学习奖励必须依赖生成结果，例如正确性、结构合法性或由生成的可核验状态得到的残差；输入侧残差只能作为采样或权重变量。

## 11. 对第三章理论深度的具体建议

如果使用公开流级数据，章节应暂定为“**一致性约束的生成式恶意流量训练**”，而不是“PINN 恶意流量检测”。可形成的理论内容包括：

1. 输入侧常数残差的零梯度命题；
2. 组相对奖励中输入常数项的抵消命题；
3. 确定性派生特征不增加条件标签信息的说明；
4. 输出依赖的辅助状态与约束损失；
5. 标签梯度与约束梯度的尺度和冲突分析；
6. 遮蔽重建控制组，分离一般多任务增益与约束增益；
7. 训练效果、未知攻击、跨域泛化、效率和显存开销消融。

如果获得拓扑与时序数据，章节才可以严谨升级为“**动力学约束的生成式恶意流量训练**”，并加入：

1. 完整队列守恒方程及可辨识性条件；
2. 状态、控制、外部攻击输入和测量噪声的定义；
3. 软约束与硬参数化对比；
4. 时间因果权重；
5. 约束误差、状态预测误差和检测误差之间的关系；
6. 不同拓扑、带宽和攻击速率下的外推实验。

**建议裁决**：当前先做 H1 和约束可计算性审计；若没有拓扑时序数据，不把 PINN 作为第三章正式名称。这样不会削弱理论深度，反而避免把不可微统计量包装成物理损失的根本漏洞。

## 12. 可写与不可写的论文表述

### 可以写

- “受 PINN 复合损失思想启发，本文将可微一致性约束作用于共享表征预测的辅助流量状态。”
- “本文通过遮蔽重建控制组区分一般多任务正则与约束项的独立贡献。”
- “本文监测标签损失与约束损失的梯度尺度和方向冲突，并依据实验选择权重策略。”
- “协议状态、业务统计不变量与物理守恒处于不同证据等级，本文分别报告。”

### 不能写

- “DDoS 打破了字节守恒定律。”
- “请求/响应比就是网络质量守恒。”
- “把输入残差加到损失后，PINN 约束了大模型。”
- “物理残差天然等于困难样本难度。”
- “标准 PINN 的神经切线核定理证明了 Qwen3 低秩适配训练收敛。”
- “输入侧物理残差可直接作为组相对策略优化的有效奖励。”

## 13. 检索与核验记录

1. 本地 11 个 PDF 均通过 `pdftotext` 读取正文，通过 `pdfinfo`、首页、参考文献和 SHA-256 核验身份。
2. `Consensus` 用于发现并抓取梯度病态、失败模式、因果训练、自适应采样和纲领综述的完整记录；关键元数据再由 DOI、出版社或 arXiv 核验。
3. `Sider Scholar` 用于 Google Scholar 与开放学术索引交叉检索。其对精确标题的召回不稳定，因此不作为最终元数据权威来源。
4. `Scite` 首次检索返回调用失败，随后提示本月 MCP 额度已用尽，无法取得其全文片段与支持/反驳引文分类。本笔记没有把未返回的 Scite 内容当证据。
5. 所有关键科学论断优先使用《Journal of Computational Physics》、SIAM、NeurIPS、Elsevier、Nature、IEEE 或 arXiv 原始页面；综述只用于建立引文链。
6. 引用计数会随时间变化，本文不把插件显示的引次数写入理论结论。

## 参考文献

[1] Raissi M, Perdikaris P, Karniadakis G E. Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations[J]. Journal of Computational Physics, 2019, 378: 686-707. https://doi.org/10.1016/j.jcp.2018.10.045

[2] Karniadakis G E, Kevrekidis I G, Lu L, et al. Physics-informed machine learning[J]. Nature Reviews Physics, 2021, 3: 422-440. https://doi.org/10.1038/s42254-021-00314-5

[3] Wang S, Teng Y, Perdikaris P. Understanding and mitigating gradient flow pathologies in physics-informed neural networks[J]. SIAM Journal on Scientific Computing, 2021, 43(5): A3055-A3081. https://doi.org/10.1137/20M1318043

[4] Wang S, Yu X, Perdikaris P. When and why PINNs fail to train: A neural tangent kernel perspective[J]. Journal of Computational Physics, 2022, 449: 110768. https://doi.org/10.1016/j.jcp.2021.110768

[5] Krishnapriyan A S, Gholami A, Zhe S, et al. Characterizing possible failure modes in physics-informed neural networks[C]//Advances in Neural Information Processing Systems. 2021, 34: 26548-26560. https://proceedings.neurips.cc/paper/2021/hash/df438e5206f31600e6ae4af72f2725f1-Abstract.html

[6] Wu C, Zhu M, Tan Q, et al. A comprehensive study of non-adaptive and residual-based adaptive sampling for physics-informed neural networks[J]. Computer Methods in Applied Mechanics and Engineering, 2023, 403: 115671. https://doi.org/10.1016/j.cma.2022.115671

[7] Wang S, Sankaran S, Perdikaris P. Respecting causality for training physics-informed neural networks[J]. Computer Methods in Applied Mechanics and Engineering, 2024, 421: 116813. https://doi.org/10.1016/j.cma.2024.116813

[8] Cuomo S, Schiano Di Cola V, Giampaolo F, et al. Scientific machine learning through physics-informed neural networks: Where we are and what's next[EB/OL]. arXiv:2201.05624, 2022. https://arxiv.org/abs/2201.05624

[9] Toscano J D, Oommen V, Varghese A J, et al. From PINNs to PIKANs: Recent advances in physics-informed machine learning[EB/OL]. arXiv:2410.13228, 2024. https://arxiv.org/abs/2410.13228

[10] Wong J C, Gupta A, Ooi C C, et al. Evolutionary optimization of physics-informed neural networks: Evo-PINN frontiers and opportunities[J]. IEEE Computational Intelligence Magazine, 2026. https://doi.org/10.1109/MCI.2025.3607749

[11] Luo K, Zhao J, Wang Y, et al. Physics-informed neural networks for PDE problems: A comprehensive review[J]. Artificial Intelligence Review, 2025, 58: 323. https://doi.org/10.1007/s10462-025-11322-7

[12] Farea A, Yli-Harja O, Emmert-Streib F. Understanding physics-informed neural networks: Techniques, applications, trends, and challenges[J]. AI, 2024, 5(3): 1534-1557. https://doi.org/10.3390/ai5030074

[13] Ren Z, Zhou S, Liu D, et al. Physics-informed neural networks: A review of methodological evolution, theoretical foundations, and interdisciplinary frontiers toward next-generation scientific computing[J]. Applied Sciences, 2025, 15(14): 8092. https://doi.org/10.3390/app15148092

[14] Cai S, Mao Z, Wang Z, et al. Physics-informed neural networks for fluid mechanics: A review[EB/OL]. arXiv:2105.09506, 2021. https://arxiv.org/abs/2105.09506

## 关联笔记

- [[Raissi-PINN开山框架]]
- [[PINN综述群]]
- [[TCP-AQM二维流体模型]]
- [[PIGCRN-化工过程攻击检测]]
- [[INVARLLM-物理不变量提取]]
- [[PI-RF-电力网入侵检测]]
- [[PPINN-FDIA-工业IoT]]
