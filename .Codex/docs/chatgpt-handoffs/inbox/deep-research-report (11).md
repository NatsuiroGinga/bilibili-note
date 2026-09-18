# DGA 对抗鲁棒方案的误报攻击威胁模型与“同源多扰动组内相对训练”近邻排重

**状态：外部候选，待本地全文和实验复核；本地保留最终裁决权。本报告不验证实验有效性、不修改冻结合同，也不接触任何未授权数据或目标期信息。**

## 执行信息与核心结论

| 返回字段 | 本次实际情况 |
|---|---|
| `actual_model` | GPT-5.5 Thinking |
| `actual_effort` | high |
| `actual_mode` | deep-research |
| `used_apps` | Web、Consensus、GitHub |
| GitHub 状态 | 按白名单尝试读取所给 commit 下的 `task_plan.md`，GitHub 返回 404；因此**没有取得或使用任何仓库文件内容**，也没有访问白名单外路径 |
| 文献范围 | 2000–2026 为主题一目标窗口；主题二向前追溯到直接机制近邻 |
| 证据等级 | **全文**＝已查看原始论文全文及对应章节/公式；**摘要**＝仅原始论文摘要足以支持所述结论；**仅题录**＝确认题录，机制仅有另一篇原始论文的引用性描述，尚未核原文 |
| 结果性质 | 文献排重意见，不是创新性法律判断、实验裁决或论文入账结论 |

**最重要的结论有两个。**

第一，主题一的“让良性对象被安全系统误判，从而形成 availability failure”有非常扎实的历史先例。最强的直接证据不是现代“alert fatigue”论文，而是早期 adversarial machine learning／自动签名学习攻击：Nelson 等在 LEET 2008 明确定义 **Causative Availability attack** 为通过污染训练数据**增加 false positives**，并实测仅控制 SpamBayes 约 1% 的训练邮件即可使过滤器失去实用性；同文还追溯到 2006 年针对 Autograph 自动蠕虫签名系统的 **Allergy attack**，以及针对 Polygraph 的 **Paragraph** poisoning，其中 correlated-outlier attack 可使学习器屏蔽带有特定特征的正常流量。citeturn25view0turn27view0

但是，必须严格拆开两个威胁模型：**“攻击分类器使 FPR 上升/使正常业务被拦截”已有直接正式先例；“攻击者主动制造大量假 IDS 告警，消耗 SOC 人类告警预算，并趁噪声掩护真实入侵”作为一个明确形式化的攻击目标，本轮没有检得同样强度、且已核原文的 NIDS 论文。** 后一机制的“后果链”有实验支持——更高 IDS false-alarm rate 会降低分析员 precision 并延长处理时间，现代 SOC 论文也明确把大量 false alerts 与 alert fatigue、真实攻击被噪声分散注意力联系起来——但这些属于**运营影响证据，不等于攻击者意图的形式化先例**。citeturn37academia0turn41academia0

第二，也是对当前方案排重更重要的结论：**“同一个干净训练样本生成多个变体，再依据这些兄弟变体之间的困难度/损失/误分类情况决定选择或梯度权重”绝不能作为宽口径机制创新点。** 本轮至少找到四条逐级逼近的成熟先例：

1. Tramèr & Boneh，NeurIPS 2019：每个原样本同时构造多种攻击的 adversarial examples，使用组内 **Max** 选损失最大的一个，或 **Avg** 全部平均训练。citeturn40view1turn40view2
2. Gong 等，MaxUp，2020：对**同一数据点生成 \(m\) 个随机扰动/增强副本**，只以组内最大损失副本驱动更新。citeturn40view0
3. Yi 等，MMEL，2021：对**同一训练样本的 augmented-sample set** 直接做**组内归一化损失重加权**；其闭式权重就是同组损失的 softmax，高损失兄弟获得更大梯度权重。这已经非常接近“组内相对信号→梯度权重”的抽象结构。citeturn32view0
4. Wu 等，Batch-in-Batch，2025：明确将每个原样本复制 \(m\) 次形成多个 adversarial versions，再按当前分类器结果从**每一个原样本自己的 \(m\)-候选组**进行 misclassification-based selection；其 CP 选组内“已误分类且距离最小”的一个，GS 则留下全部误分类变体。这是当前 DGA “K 个同源扰动→按 fooled 信号 top-k/过滤”的**最危险直接近邻**。citeturn30view0

因此，经过本轮外部排重，**当前方案若还要主张机制差量，不能写成“同源多扰动分组”“根据模型是否被欺骗选择困难扰动”“组内相对困难样本加权”中的任何一个宽口径表述。** 尚未检得直接先例的是更窄的结构：**明确以 sibling-centered／group-centered advantage（例如减组均值、leave-one-out baseline 或相对组内基线）而不是绝对 loss/misclassification 形成权重，并将其同时用于 DGA 恶意侧漏检压力与良性侧误报压力的双侧对称构造。** 这里的关键词是“**本轮未检得**”，不是“证明不存在”。

## 误报注入、可用性攻击与告警疲劳的文献链

### 正式的 false-positive availability attack 已经存在

最明确的历史锚点是 Blaine Nelson、Marco Barreno、Fuching Jack Chi、Anthony Joseph、Benjamin Rubinstein、Udam Saini、Charles Sutton、J. D. Tygar、Kai Xia 的 **“Exploiting Machine Learning to Subvert Your Spam Filter”**，LEET 2008。【证据等级：**全文**】

论文 §3.1 *Attack framework* 明确把安全违规分为两类：制造 false negatives 是 **Integrity violation**，而使正常邮件被错误过滤、即制造 false positives，是 **Availability violation**。作者随后直接写明，其研究对象就是通过操纵训练数据提高 false positives 的 **Causative Availability attacks**；在 indiscriminate 情况下，false positives 多到足以迫使受害者关闭过滤器或不断人工检查被过滤内容。citeturn25view0turn26view0

其机制不是泛泛的“误报有害”，而是主动攻击。§3.2 *Dictionary attacks* 中，攻击者把大量正常邮件可能出现的词置入被标为 spam 的攻击邮件，使这些正常词学到更高 spam score，于是未来正常邮件更容易被判为 spam。§3.3 又构造 targeted availability attack，目标是让某一类正常邮件被过滤。citeturn25view0

实验强度也足够成为威胁模型锚点：§4.2 报告，在 10,000 条训练邮件的设置下加入 101 条攻击邮件，即大约控制 1%，已足以显著破坏过滤器；Figure 1 将攻击效果直接画成“test ham misclassified”。§7 总结给出的一个具体结果是，Usenet dictionary attack 在仅控制 1% 训练邮件时使 36% 的 ham 被错误分类，并使 SpamBayes 达到不可用状态。citeturn27view0turn26view1

这对当前“良性侧 CharBot 近邻组→诱发误报”威胁模型的含义很清楚：**攻击者通过恶意操纵，使本应属于负类/良性的对象进入检测器正类，从而伤害可用性**，并不是一个需要从 alert-fatigue 文献临时发明的新安全目标；至少在垃圾邮件学习系统中，它在 2008 年已经以明确 taxonomy 和实证形式存在。citeturn25view0

### NIDS/自动签名系统还有更早、更贴近网络检测的先例

Nelson 等的 §6 *Related work* 给出了两条更贴近 NIDS/自动网络防御的 2006 年先例，但本轮没有取得这两篇原始全文，因此必须降低核验等级。citeturn27view0

| 原始题录 | 本轮可确认的攻击含义 | 精确出处锚点 | 核验状态 |
|---|---|---|---|
| Simon P. Chung, Aloysius K. Mok, **“Allergy Attack Against Automatic Signature Generation”**, RAID 2006, pp.61–80 | 针对 Autograph 自动蠕虫签名生成。Nelson 等概述其攻击顺序为：攻击节点先发送使自己被判 suspicious 的流量，随后发送类似合法流量，诱使系统生成会伤害合法流量的 blocking rule，形成 denial of service / availability attack | Nelson 2008 §6；参考文献 [2] 给出 RAID 2006 题录 | **仅题录；机制由另一篇原始论文全文交叉描述，尚未核 Chung–Mok 原文** citeturn27view0 |
| James Newsome, Brad Karp, Dawn Song, **“Paragraph: Thwarting Signature Learning by Training Maliciously”**, RAID 2006 | 针对 Polygraph 式多态蠕虫签名学习；Nelson 等特别指出其 *correlated outlier attack* 可向 positive training instances 加入虚假特征，使学习器将具有这些特征的 benign traffic 一并阻断，即 causative availability effect | Nelson 2008 §6；参考文献 [16] 给出 RAID 2006 题录 | **仅题录；机制由 Nelson 原始全文复述，Paragraph 原文未完成本轮核验** citeturn27view0 |

这里有一个值得本地全文复核时优先补齐的链条：Nelson 2008 并不是凭后来的 taxonomy 把它们强行解释成 availability attack，而是在 §6 明确把 Chung–Mok 称为 **Causative Availability attack**，并明确说明 Paragraph 的 correlated-outlier attack 会让系统“block benign traffic”。citeturn27view0

因此，若当前方案的良性侧威胁模型表述为：

> 攻击者不仅追求恶意样本漏检，也可能操纵检测系统使合法对象被恶意类规则覆盖，从而消耗系统的可用性预算。

这条文献链是成立的。若进一步写成“**攻击者的目的就是让 SOC 人员疲劳并利用假告警掩护一次真实入侵**”，则证据等级会明显下降，不能用上述 poisoning 文献直接替代。

### 现代 malware 文献进一步明确“benign adversarial examples → false positives”

Matouš Kozák 与 Martin Jureček 的 **“Effectiveness of Adversarial Benign and Malware Examples in Evasion and Poisoning Attacks”**，2025，研究 PE malware detector。【证据等级：**摘要**；2025 年 Springer 章节版本已可检到题录，但本轮技术结论仅按作者公开原始摘要核验。】

原始摘要明确把 **benign adversarial examples** 单独作为攻击面：它们虽然自身不恶意，却能**增加 false positives 并削弱用户对 antivirus solution 的信任**；论文还比较了 benign 和 malware AEs 在 poisoning 中的作用，并报告 benign AEs 对训练后的模型性能具有更明显的破坏作用。citeturn36academia25

它与当前 DGA 良性侧构造非常值得并列，因为二者都在挑战一个常被忽略的假设：

> adversarial robustness 不只等于“malware/DGA 不被改成 false negative”；攻击者也可以从真正 benign 的一侧制造 detector-positive 输入或污染效应。

但目前不能声称 Kozák–Jureček 与“同一良性域名生成 K 个 CharBot 式邻居并组内重加权”具有机制一致性；本轮核验只支持**威胁目标一致**，不支持**训练机制相同**。citeturn36academia25

### Alert fatigue 能证明攻击后果，但还不能单独证明攻击者模型

Lucas Layman 与 William Roden 的 **“A Controlled Experiment on the Impact of Intrusion Detection False Alarm Rate on Analyst Performance”**，2023。【证据等级：**摘要**】

这项受控实验让分析人员处理不同 false-alarm-rate 的模拟 IDS 警报，比较 50% 与 86% FAR 条件；作者报告，高 FAR 组的 median precision 低 47%，完成任务时间慢 40%，而 sensitivity 差异没有达到统计显著。它证明了 **FPR/false-alert volume 不只是一个离线 ML 指标，而会转化为真实的人类分析成本。** citeturn37academia0

2024 年 Oliver 等的 **Carbon Filter** 则从生产 SOC alert triage 角度称 alert fatigue 是核心问题之一，并指出大量 false alerts 会分散分析员对真实攻击的注意力；作者的系统目标就是降低人工必须检查的 alert 数量。【证据等级：**摘要**】citeturn41academia0

2026 年 Karner 等的 **AlertBERT** 同样把大量 security alerts 与 SOC alert fatigue、反应变慢和错误决策联系起来，并专门研究高 false-positive noise 环境下的 alert grouping。【证据等级：**摘要**】citeturn26academia0

这些证据支持下面这条链：

\[
\text{attacker-induced FP}
\rightarrow
\text{更多无效警报}
\rightarrow
\text{更高分析负载}
\rightarrow
\text{真实告警更难处理}.
\]

但最后一步必须谨慎措辞：**本轮没有检得一篇已经全文核验的 NIDS 原始论文，把“主动生成大量 false alerts 消耗 analyst alert budget，并以此掩护同期真实攻击”作为其完整、主要、实验化 threat model。** 因而论文里最好将它写成 *operational motivation / plausible consequence*，而把已经有直接文献锚定的 **availability attack / false-positive poisoning** 作为正式威胁模型。

### 对主题一的排重裁决建议

按证据强度，可以把当前相关威胁模型拆成三层：

| 命题 | 本轮证据强度 | 能否直接写成已有先例 |
|---|---|---|
| 攻击者故意使正常对象被检测器判恶意，从而提高 FPR、伤害可用性 | **强** | **可以**；Nelson 2008 是直接 taxonomy＋实验锚点 citeturn25view0turn27view0 |
| 在网络自动签名系统中通过 poisoned learning 产生会伤害合法流量的规则 | **中强** | **可以，但需要本地补核 2006 原文**；Allergy / Paragraph 已由 Nelson 原始全文明确追溯 citeturn27view0 |
| 攻击者用大量假 IDS 告警主动耗尽 SOC 告警预算，借噪声掩护真实入侵 | **中弱** | **本轮不建议声称已有完全同构正式先例**；alert-fatigue 后果有实证，但 attacker-intent 这一环未完成原文锚定 citeturn37academia0turn41academia0 |

换言之，**“false-positive injection”可以立威胁模型；“alert-budget exhaustion to hide a real attack”目前更适合作为该模型的安全运营动机，而不是声称已有 NIDS 定式。**

## 同源多扰动的组内选择与重加权近邻

### 最早的强结构近邻：多攻击组内 Max/Avg

Florian Tramèr 与 Dan Boneh 的 **“Adversarial Training and Robustness for Multiple Perturbations”**，NeurIPS 2019。【证据等级：**全文**】

论文在引言中已经明确说明：**for each training point**，分别为所有 perturbation types 构造 adversarial examples，然后有两种训练方式：对全部样本平均的 `avg`，以及只保留最坏 adversarial example 的 `max`。citeturn40view1

§3 *New Attacks and Adversarial Training Schemes* 给出精确定义。令 \(A_k(x)\) 是第 \(k\) 种攻击，那么 Max strategy 选：

\[
k^\star
=
\arg\max_k
L(f(A_k(x)),y),
\]

并只用 \(A_{k^\star}(x)\) 训练；Avg strategy 则平均所有 \(A_k(x)\) 的损失。也就是说，**组的边界就是同一个 clean \(x\)**，选择规则就是 sibling candidates 内的损失比较。citeturn40view2

它与当前方案的主要区别是：Tramèr–Boneh 的 siblings 来自**不同 perturbation set / attack type**，如 \(\ell_1,\ell_2,\ell_\infty\) 或 rotation-translation；当前方案则是在一个 DGA 字符扰动任务下给同一域名采样多个同类型/同预算变体。此外，它使用 absolute worst-loss argmax，没有均值基线、leave-one-out 或组内 centered advantage。citeturn40view2

因此：

**“同一样本多个 adversarial candidates，按同组难度选择最坏者”已明确不是空白。**

### MaxUp：同一个样本生成多个随机副本，再由组内最大损失决定更新

Chengyue Gong、Tongzheng Ren、Mao Ye、Qiang Liu 的 **MaxUp: A Simple Way to Improve Generalization of Neural Network Training**，arXiv 2020。【证据等级：**全文**；本次原始 arXiv 页面未给出正式会议归属，因此不额外替它补会议名称。】

其核心设计比 multi-attack AT 更接近“一个生成机制多次采样”：对一个 data point 生成一组 random perturbations / transforms，然后优化其中的 maximum/worst-case loss。原始摘要就是这样定义 MaxUp 的。citeturn40view0

其方法部分可写成：

\[
\tilde x_{i,1},\ldots,\tilde x_{i,m}
\sim
\mathcal A(x_i),
\qquad
L_i^{\text{MaxUp}}
=
\max_{j=1,\ldots,m}
\ell(f_\theta(\tilde x_{i,j}),y_i).
\]

这里同一个 \(x_i\) 的 \(m\) 个副本构成天然 group，只由组内 hardest copy 贡献该样本的主要训练信号。MaxUp 的论证目标主要是 augmentation 下的 generalization / robustness regularization，而不是 DGA adversarial detector，但“**same origin → multiple variants → within-origin hard selection**”这一抽象结构已经存在。citeturn40view0

对当前方案而言，若 \(K=4\) 最后实际只取 top-1 fooled/loss 最大变体，则和 MaxUp 的机制差量会尤其难写；即使取 top-\(k\)，本质差量也不能只说“不是只取一个”。

### MMEL：已经出现真正的“同组兄弟样本相对权重”

本轮最容易被忽略、但对“组相对优势”命名风险最大的邻居，是 Mingyang Yi、Lu Hou、Lifeng Shang、Xin Jiang、Qun Liu、Zhi-Ming Ma 的 **“Reweighting Augmented Samples by Minimizing the Maximal Expected Loss”**，arXiv 2021。【证据等级：**全文**；原始 arXiv 页面没有在本轮核验结果中标正式会议，故会议归属保留待本地题录确认。】

论文一开始就把问题限定为：

> 对 **augmented samples from the same training example** 不应全部等权，而应给予不同权重。citeturn32view0

§3.1 *Why Maximal Expected Loss* 令同一个原样本 \(x_i\) 的增强集为 \(B(x_i)\)。传统目标在组内使用均匀权重：

\[
\frac{1}{|B(x_i)|}
\sum_{z\in B(x_i)}
\ell(f_\theta(z),y_z).
\]

作者随后把每个 sibling 的权重解释成条件分布 \(\mathbb P_B(z\mid x_i)\)，并对所有可能的组内 reweighting 求 maximal expected loss。citeturn32view0

更关键的是 Theorem 1 / Eq. (6)。最优组内权重具有闭式：

\[
\mathbb P_\theta^\star(z\mid x_i)
=
\frac{
\exp\!\left(\ell(f_\theta(z),y_z)/\lambda_P\right)
}{
\sum_{z'\in B(x_i)}
\exp\!\left(\ell(f_\theta(z'),y_{z'})/\lambda_P\right)
}.
\]

因此，一个 variant 的权重**不是由其绝对 loss 单独决定，而是由它相对于同一 \(x_i\) 的所有 sibling losses 经组内 softmax 归一化决定**；作者明确说明，高 loss augmented samples 获得更高权重。citeturn32view0

§3.2 还给出以原样本预测作为 soft target 的组内重加权形式，§3.3 Algorithm 1 的训练流程则是：为每个 \(x_i\) 生成 \(B(x_i)\)，获取一个 mini-batch 的这些 augmentation sets，计算上述组内权重，然后以 reweighted loss 更新 classifier。citeturn32view0

这意味着：

> **“来自同一原样本的多个变体不等权；利用兄弟变体在组内的相对困难度，给 classifier gradient 分配不同权重”这一宽口径机制已经有明确先例。**

当前方法如果把 “GRPO-inspired group relative” 的创新解释成“因为每个域名有自己的 K 个变体，所以权重是相对同组而不是全 batch 计算”，**MMEL 会构成很强的反例。**

它仍有重要区别。MMEL 的相对性来自**正的 softmax-normalized loss weights**；它不构造类似 RL advantage 的零均值 centered quantity，也没有“高于组均值为正、低于均值为负”的 signed advantage；它使用一般 augmentation，并非 malware/DGA adversarial semantics；它也没有当前设想的 malicious-side fooling 与 benign-side FP pressure 双侧设计。citeturn32view0

所以真正还能保留的窄差量不是“group reweighting”，而可能是：

\[
A_{ij}
=
s_{ij}
-
b_i,
\]

其中 \(b_i\) 明确是同一 clean origin 内的 mean／leave-one-out mean／rank-derived baseline，并且后续选择/权重直接依赖这个 **centered sibling advantage**。本轮没有检到 MMEL 采用这种中心化 advantage。citeturn32view0

### Batch-in-Batch：与 K 个扰动后 fooled 过滤最直接的 adversarial-training 邻居

Yinting Wu、Pai Peng、Bo Cai、Le Li 的 **“Batch-in-Batch: a new adversarial training framework for initial perturbation and sample selection”**，*Complex & Intelligent Systems*, Vol. 11, Article 132, 2025。【证据等级：**全文**】

这篇是本轮建议本地**必须全文排重**的第一优先级论文。

作者在摘要中就明确说，框架为**每一个 original sample 联合生成 \(m\) 套 initial perturbations**，然后进行 sample selection，使更高质量的 adversarial samples 优先进入训练。citeturn30view0

Introduction 对结构描述得更具体：original batch 被复制 \(m\) 次；每份副本得到不同 initial perturbation，再经过 N-FGSM 或 PGD 得到 adversarial batch；最后由 SELECT procedure 根据模型状态形成 final training batch。作者还明确指出，其出发点之一就是“multiple copies of a single original sample”。citeturn30view0

在 § *Sample selection strategies* 中，作者把同一个 \(x_i\) 对应的 adversarial group 写成：

\[
r_i
=
\{x_i^{(1)},\ldots,x_i^{(m)}\}.
\]

这与当前“每个干净域名一个 \(K=4\) variant group”的组织单位几乎完全同构。citeturn30view0

其 **Checkpoint (CP)** 策略首先构造：

\[
M_i
=
\{
x_i^{(j)}
:
f_\theta(x_i^{(j)})\neq y_i
\},
\]

若组中已有误分类 adversarial variants，就从 \(M_i\) 中取离原样本 \(\ell_\infty\) 距离最小的一个；没有误分类时则采用另一备选规则。因此这是显式的 **same-origin + current-model misclassification + within-group selection**。citeturn30view0

其 **Greedy Selection (GS)** 更接近当前 fooled filtering：

\[
B_f
=
\{
x:
x\in B_{\rm adv},
\;
x\text{ is misclassified by } f_\theta
\}.
\]

作者强调，对同一个 \(x_i\)，CP 恰选一个 variant，而 GS 可以选择零个或多个；如果一个原样本的所有 attack attempts 都没有使模型出错，则 GS 可以不给它额外 adversarial training。citeturn30view0

这和当前方法的差别主要只剩：

- BB 的多个 sibling 是连续图像扰动空间中的 adversarial examples，当前是域名字符扰动；
- BB-GS 是**绝对 misclassification predicate**，不是“一个变体比自己的 siblings 更有优势多少”；
- BB-CP 还使用扰动距离作次级选择；
- BB 没有当前描述的良性侧“让 detector 产生 FP”的镜像训练目标。citeturn30view0

但如果当前 P3 实现其实只是：

> 对同一域名生成 4 个攻击变体；把 fooled=1 的留下；若太多则取其中 top-k；

那么 **“group-relative”这一名字本身不会形成足够差量**。在机制审稿视角，BB 已经完成了 same-origin grouping 和 model-dependent misclassified-variant selection。citeturn30view0

### 四个近邻放在同一坐标系中

| 方法 | 同一原样本多变体 | 组内比较/归一化 | 选择/加权规则 | 是否 adversarial-training classifier | 与当前 K=4 方案的碰撞 |
|---|---|---|---|---|---|
| Tramèr & Boneh, 2019 | 是 | 是 | max loss 或 avg | **是** | 中高：确立“同源多攻击组内 max” citeturn40view2 |
| MaxUp, 2020 | 是 | 是 | 多个随机变体中取 worst loss | 广义 robustness / augmentation | 中高：同一 generator 多采样＋组内 hardest copy citeturn40view0 |
| MMEL, 2021 | **是** | **是，而且显式组内 softmax normalization** | sibling loss 决定 continuous weight | 判别分类；受 AT 启发的 augmentation reweighting | **很高**：已经覆盖“同源组内相对权重”抽象结构 citeturn32view0 |
| Batch-in-Batch, 2025 | **是** | 是 | 组内误分类筛选；CP/GS/BG | **是** | **极高**：same-origin adversarial variants＋fooled/misclassified selection citeturn30view0 |
| 当前候选 | K=4 | 计划如此 | fooled-relative top-k；良性侧 FP weighting | DGA detector AT | 只能在更窄的 relative-baseline / 双侧任务化上寻找差量 |

这张表带来的排重结论比“没找到完全一样的论文”更重要：**机制空间实际上已经被从 hard max、absolute misclassification filtering 到 continuous within-group reweighting 三个方向覆盖。**

## 当前方案还能主张什么，不能主张什么

### 不宜再作为创新点的宽表述

基于上述全文证据，本轮建议把下列说法全部视作**高碰撞**，不要单独作为章级机制创新：

**“一个干净样本生成多个对抗样本，再选择更难的样本训练。”** Tramèr–Boneh、MaxUp、Batch-in-Batch 都已经给出直接先例。citeturn40view2turn40view0turn30view0

**“不像普通 AT 均匀使用所有扰动，我们根据 classifier 当前表现动态选择 fooled examples。”** Batch-in-Batch 的 SELECT/GS 已经明确根据当前模型是否 misclassify adversarial samples 做动态筛选。citeturn30view0

**“对同一原样本的多个变体给予不同梯度权重，而不是把它们作为独立样本。”** MMEL 已经直接把 same-origin augmented samples 作为一个条件分布并进行组内 softmax loss weighting。citeturn32view0

**“使用组内相对困难度，而不是跨 batch 比较困难度。”** 只要所谓“相对”只是 sibling loss 经归一化后决定权重，MMEL 基本已经覆盖这一抽象。citeturn32view0

因此，本轮外部排重不支持把“GRPO 的 group relative 思想第一次搬进 adversarial training”作为未经限定的主张。至少 MMEL 提供了一个非 RL、判别式分类、same-origin-group relative weighting 的明确反例。citeturn32view0

### 尚未检得精确同构先例的窄机制

本轮用了专门检索式搜索 *group mean*、*leave-one-out*、*ranking*、*top-k*、*same sample multiple perturbations* 等组合，**没有检得非 RL 判别式 adversarial training 中明确采用 GRPO/RLOO 式 centered sibling advantage 的精确同构论文。**

这里的区别需要写到数学层面。

MMEL 是：

\[
w_{ij}
=
\frac{\exp(\ell_{ij}/\tau)}
{\sum_{k=1}^{K}\exp(\ell_{ik}/\tau)},
\qquad
w_{ij}>0,\quad
\sum_jw_{ij}=1.
\]

它表达的是**组内归一化重要性**。citeturn32view0

Tramèr–Boneh / MaxUp 则近似：

\[
w_{ij}
=
\mathbf 1
\left[
j=\arg\max_k \ell_{ik}
\right].
\]

这是**组内 hard maximum**。citeturn40view2turn40view0

Batch-in-Batch GS 更像：

\[
w_{ij}
=
\mathbf 1[
\hat y_{ij}\neq y_i],
\]

即**absolute fooling predicate**。citeturn30view0

只有当当前方法真正使用类似：

\[
A_{ij}
=
r_{ij}
-
\frac{1}{K}
\sum_{k=1}^{K}r_{ik},
\]

或者 leave-one-out：

\[
A_{ij}^{\mathrm{LOO}}
=
r_{ij}
-
\frac{1}{K-1}
\sum_{k\ne j}r_{ik},
\]

随后让选择/梯度权重依赖 \(A_{ij}\) 的符号、排序或幅度，而不是只依赖 \(r_{ij}\) 是否 fooled，才存在一个本轮检索没有被上述四种成熟机制直接覆盖的**更窄差量**。

即便如此，也只能写：

> “在本轮覆盖的非 RL 判别式 adversarial-training/augmentation 文献中，未检得明确使用 sibling-centered mean/leave-one-out advantage 的精确同构实现。”

**不能写“首次”。** “未检得”不是不存在证明。

### 良性侧对称组可能是更有价值的任务差量，但仍不是成熟机制本身

当前背景提出恶意侧：

\[
x_i
\rightarrow
\{\tilde x_{i1}^{m},\ldots,\tilde x_{iK}^{m}\}
\]

以 fool detector / false-negative pressure 选样；良性侧则拟对称构造：

\[
b_i
\rightarrow
\{\tilde b_{i1}^{b},\ldots,\tilde b_{iK}^{b}\}
\]

以诱发 false positives 的信号选样。

本轮找到的 Batch-in-Batch、MaxUp、MMEL 都没有提供“DGA detector 中把 **FN adversarial group** 与 **FP adversarial benign group** 成对组织”的证据；Nelson 2008 和 Kozák–Jureček 2025 则为“攻击者也可以故意制造 false positives”提供了独立的安全威胁依据。citeturn30view0turn32view0turn25view0turn36academia25

因此一个更合理的文献定位不是：

> “我们首次提出 group-relative adversarial training。”

而是类似：

> 现有 multi-perturbation AT、MaxUp、MMEL 和 Batch-in-Batch 已分别覆盖 worst-case selection、same-origin hard augmentation、within-origin reweighting 和 misclassification-based adversarial selection；当前候选若最终通过，其待验证差量需要落在**面向 DGA 检测双侧错误风险的、显式 centered sibling-relative signal 及其恶意/良性对称构造**，而不是同源分组本身。citeturn40view2turn40view0turn32view0turn30view0

这是目前最安全的外部候选定位。

## 题录与精确出处锚点

下面按“可以直接进入本地全文核查队列”的形式整理。

| 文献 | 题录 | 精确机制位置 | 证据等级 | 与当前任务关系 |
|---|---|---|---|---|
| **Exploiting Machine Learning to Subvert Your Spam Filter** | Nelson, Barreno, Chi, Joseph, Rubinstein, Saini, Sutton, Tygar, Xia；USENIX LEET 2008 | §3.1：false positive = Availability violation；明确研究 Causative Availability attack；§3.2 Dictionary attack；§4.2 Figure 1；§6 对 Allergy/Paragraph 的追溯；§7 总结 | **全文** | 主题一最强正式 FP-availability threat anchor citeturn25view0turn27view0 |
| **Allergy Attack Against Automatic Signature Generation** | Simon P. Chung, Aloysius K. Mok；RAID 2006，pp.61–80 | 本轮仅从 Nelson §6 和 refs [2] 确认；攻击 Autograph，诱导产生伤害合法流量的 blocking rule | **仅题录；待原文核** | NIDS/自动签名方向极重要老近邻 citeturn27view0 |
| **Paragraph: Thwarting Signature Learning by Training Maliciously** | James Newsome, Brad Karp, Dawn Song；RAID 2006 | 本轮从 Nelson §6 和 refs [16] 确认；correlated-outlier attack 使正常流量被学习规则阻断 | **仅题录；待原文核** | 网络恶意软件／自动签名 poisoning 的 FP availability 先例 citeturn27view0 |
| **A Controlled Experiment on the Impact of Intrusion Detection False Alarm Rate on Analyst Performance** | Lucas Layman, William Roden；2023 | 原始摘要：50% vs 86% false-alarm treatment；precision、time-on-task 结果 | **摘要** | 告警预算／alert fatigue 的人因后果实证，不是 attacker-intent threat model citeturn37academia0 |
| **Carbon Filter: Real-time Alert Triage Using Large Scale Clustering and Fast Search** | Jonathan Oliver et al.; 2024 | 原始摘要：SOC alert fatigue、false alerts 分散真实攻击分析、production alert triage | **摘要** | 现代安全运营后果证据 citeturn41academia0 |
| **Effectiveness of Adversarial Benign and Malware Examples in Evasion and Poisoning Attacks** | Matouš Kozák, Martin Jureček；2025 | 原始摘要：benign AEs 可增加 false positives、削弱 AV 信任；比较 benign/malware poisoning | **摘要** | malware 场景直接支持“良性对抗侧也是攻击面” citeturn36academia25 |
| **Adversarial Training and Robustness for Multiple Perturbations** | Florian Tramèr, Dan Boneh；NeurIPS 2019 | §3 *New Attacks and Adversarial Training Schemes*；Max/Avg strategies；\(k^\*= \arg\max_k L(f(A_k(x)),y)\) | **全文** | 同一输入多 adversarial candidates 后组内 max/avg 的成熟先例 citeturn40view1turn40view2 |
| **MaxUp: A Simple Way to Improve Generalization of Neural Network Training** | Chengyue Gong, Tongzheng Ren, Mao Ye, Qiang Liu；arXiv 2020 | Abstract；§2 Main Method：每个 data point 生成 \(m\) 个随机变体，优化 max loss | **全文** | “同源 K 变体→hardest sibling”直接结构近邻 citeturn40view0 |
| **Reweighting Augmented Samples by Minimizing the Maximal Expected Loss** | Mingyang Yi, Lu Hou, Lifeng Shang, Xin Jiang, Qun Liu, Zhi-Ming Ma；arXiv 2021 | §3.1 Eq.(1)–(6)，尤其 Eq.(6) 同源 augmentation losses 的组内 softmax；§3.2 Eq.(7)–(9)；§3.3 Algorithm 1 | **全文** | **组内相对加权的最强宽机制排重证据** citeturn32view0 |
| **Batch-in-Batch: a new adversarial training framework for initial perturbation and sample selection** | Yinting Wu, Pai Peng, Bo Cai, Le Li；*Complex & Intelligent Systems* 11, Article 132, 2025 | Introduction；§ *Batch-in-Batch: duplication for better preparation*；§ *Sample selection strategies*；Eq.(3) CP、Eq.(4) GS、Eq.(5) BG | **全文** | **K 同源 adversarial variants＋fooled/misclassification selection 的最直接近邻** citeturn30view0 |

特别值得注意的是 Batch-in-Batch 自己在 related work 中也承认“为一个原样本生成多个 adversarial versions”的文献非常少，并追溯了 Free-AT 与 Kim 等的 checkpoint selection；作者随后把“parallel generation + sample selection”作为其主要贡献之一。这个 2025 论文的位置决定了当前工作不能仅靠“Drichel 2024 没有 group selection”完成排重。citeturn30view0

换言之：**Drichel 是 DGA task-neighbor；Batch-in-Batch/MMEL/MaxUp/Tramèr–Boneh 是 mechanism-neighbor。两条轴都必须排。**

## 检索覆盖、未命中项与不确定性

### 实际使用的主要检索式

主题一实际使用了以下语义族及其组合变体：

```text
"false positive" attack intrusion detection alert flooding attacker generate alerts
"alert flooding" intrusion detection false positives attack
"operator fatigue" Stick Snot IDS paper
"Snot" "false positives" intrusion detection system attack paper
adversarial machine learning poisoning increase false positives malware detector availability attack
Nelson Barreno spam filter availability false positive LEET 2008
"availability" attack spam filter machine learning false positives poisoning paper
"dictionary attack" poisoning spam filter false positive
Chung Mok Autograph poisoning availability attack
"Allergy Attack Against Automatic Signature Generation"
"Paragraph: Thwarting Signature Learning by Training Maliciously"
"alarm flooding" intrusion detection adversary
"false alarm flooding" cybersecurity intrusion detection
"alert fatigue" attacker "false positives" intrusion detection
```

这些查询检得了很强的 **availability/FP poisoning** 链，但没有得到一篇本轮可以全文确认的原始 NIDS 论文，其主要正式目标明确写为“以主动制造大量 false alerts 消耗 SOC analyst budget，从而掩护同步真实入侵”。因此这个缺口必须如实保留，而不能用一般 alert-fatigue 文献补成“已发现”。citeturn25view0turn37academia0

主题二实际覆盖了：

```text
adversarial training multiple perturbations same sample max loss select worst variant
"multiple adversarial examples" same sample adversarial training max loss weighting
"MaxUp" adversarial training multiple augmented samples max loss
"group" adversarial examples weighting same sample
adversarial training multiple perturbations same clean sample hard example selection
Batch-in-Batch adversarial training initial perturbation sample selection
"adversarial training" "leave-one-out" perturbation samples same input
"adversarial training" "group mean" perturbations same sample weighting
"adversarial training" ranking multiple adversarial examples same sample select top-k
"adversarial training" multiple augmentations same sample hard example mining max top-k
"same training example" augmented samples reweighting hard examples
```

该组查询出现了一个重要的“由弱到强”检索过程：开始时看起来最接近的是 Max/MaxUp/Batch-in-Batch；继续加入“same training example + augmented samples + reweighting”以后检得 **MMEL**，它把近邻从“硬样本选择”推进到了“同源组内 continuous relative weighting”。citeturn32view0

因此，**本轮真正的排重更新是 MMEL，而不仅仅是 Batch-in-Batch。**

### 没有检得的东西

本轮未检得以下精确组合的非 RL 判别式训练论文：

\[
A_{ij}
=
r_{ij}
-
\bar r_i
\]

式的**显式组均值 centered advantage**；

\[
A_{ij}^{LOO}
=
r_{ij}
-
\frac{1}{K-1}\sum_{k\neq j}r_{ik}
\]

式的**同源 leave-one-out baseline**；

以及把这种 centered sibling signal 同时用在**恶意 FN pressure group 与良性 FP pressure group**的 DGA adversarial training。

但这里有三个不确定性必须保留。

其一，术语高度不统一。相同思想可能不叫 “group-relative advantage”，而叫 augmentation reweighting、hard-view mining、multi-view robust training、worst-view selection、distributionally robust augmentation、instance-conditioned sampling。因此本轮的“未检得”不是 exhaustive proof。

其二，MMEL 已经说明**数学上只差一个 centered baseline 并不自动等于足够大的方法创新差量**。其 Eq.(6) 已经用 sibling set 内的全部损失确定每个权重；若当前 centered advantage 最终只产生与 loss-softmax 几乎相同的排序，那么机制差异可能更多是参数化差异而不是新的训练原理。citeturn32view0

其三，Batch-in-Batch 的 GS 已经把 misclassification 直接变成组内样本是否入批的开关。因此如果当前所谓“fooled relative top-k”在 \(K=4\) 下最终主要等价于“保留 fooled variants、丢弃 non-fooled variants”，那么即使数学表达使用了 group mean，**功能上仍可能退化为 BB-GS 的任务化版本**。这需要本地用动作等价性而不是命名来复核。citeturn30view0

### GitHub 与本地证据边界

按交接包给定 repository、commit 和白名单路径，本轮曾尝试读取：

` .Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/task_plan.md `

GitHub 返回 404，因此没有成功读取该文件，也没有继续访问任何白名单外路径。故本报告**完全没有用仓库内容验证当前实现究竟是 centered advantage、absolute fooled filtering、top-k rank，还是其他权重形式**。

这使最终排重有一个非常具体的本地未回答问题：

> 当前 P3 的实际数学权重在去掉“GRPO-inspired”命名后，是否仍然包含一个 Batch-in-Batch、MaxUp 和 MMEL 都没有的不可约运算？

本地复核时最值得直接做的是把三者都写成每个 clean origin 的权重向量：

\[
\mathbf w_i
=
(w_{i1},\ldots,w_{iK}),
\]

然后检查当前方案分别在什么输入条件下与

\[
\mathbf w_i^{\rm Max},
\qquad
\mathbf w_i^{\rm BB-GS},
\qquad
\mathbf w_i^{\rm MMEL}
\]

产生完全相同的 selected set／梯度方向。若大部分情况下等价，仅靠“来源于 GRPO”不足以形成机制差量；若 centered baseline 会在绝对 loss/fooling 相同而**组内结构不同**时改变权重，并且该变化对双侧 DGA 风险有独立实验增益，才有更强的任务化机制论证基础。该判断是根据上述文献机制作出的排重推论，不是本轮实验验证。citeturn30view0turn32view0turn40view2

**外部候选结论：主题一可以把“攻击者诱发 false positives 造成检测系统 availability failure”作为有正式历史先例的威胁模型，但“假告警洪泛掩护真实入侵”目前应降格为有 alert-fatigue 实证支撑的运营动机；主题二则已发现明显近邻碰撞，尤其是 MMEL 2021 与 Batch-in-Batch 2025，因此“同源 K 变体＋组内选择/重加权”不能再作为宽创新声明。尚可继续核查的窄差量是显式 centered/leave-one-out sibling advantage，以及它在 DGA 恶意漏检与良性误报双侧上的不可约作用。以上均须由发起方在本地全文与实际实现上独立复核后，才能进入台账。**