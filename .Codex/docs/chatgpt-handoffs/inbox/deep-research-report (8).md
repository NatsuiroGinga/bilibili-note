# DRIFT：博弈 × 强化学习 × MARL × 对抗鲁棒性交叉文献深度调研

**状态：外部候选，待本地全文和实验复核；本地保留全部裁决权。以下内容不验证既有实验有效性、不改写冻结合同，也不授权 T20–T25 进入设计、调参或机制选择。**

| 返回字段 | 实际情况 |
|---|---|
| `actual_model` | GPT-5.5 Thinking |
| `actual_effort` | high |
| `actual_mode` | deep-research |
| `used_apps` | Web；Consensus（仅辅助发现候选，不作为下文证据来源）；GitHub（按白名单对指定 commit 做一次只读读取尝试，返回 404，因此未使用任何仓库文件内容） |
| Git 操作 | 无修改、无提交、无代码执行 |
| 证据边界 | 用户提供的脱敏实验摘要 + 公开原始论文/论文官方页面 |
| 文献截止核查日 | 2026-09-10 |
| 输出性质 | 外部候选建议，不是立项、存废或实验有效性裁决 |

为避免把“搜到论文”和“全文核过机制”混为一谈，下文采用三档核验状态：

**✅ 原文核验**：已检查原论文正文或原始论文页面中的对应机制位置。  
**◐ 原文部分核验**：题录、摘要和关键机制已由原始来源核对，但本轮没有逐页复核全部实验细节。  
**△ 线索锚定**：交接包已指定或搜索发现，但本轮未重新全文核对；不得据此单独承担核心创新判断。  
**🧭 检索性结论**：本轮系统检索没有找到直接先例；这表示“未发现”，不表示数学意义上的“不存在”。

## 执行摘要与核心判断

对 P3→P4 的最重要结论不是“MARL 值不值得做”，而是首先要**重新界定 P4 究竟是什么**。

如果攻击者用 RL/GRPO-style policy 学一次域名扰动，而检测器仍通过标准分类损失反向传播更新，那么严格地说，它更接近：

> **RL attacker + gradient-trained defender 的两玩家重复学习博弈／对抗共演化**

而不是标准意义上“两个 RL agent 都在 Markov game 中行动”的 MARL。MADDPG 的标准 MARL 形式要求每个 agent 有策略、动作和自己的回报，训练时通过集中式 \(Q_i(x,a_1,\ldots,a_N)\) 处理其他 agent 行为；仅仅把分类器称作“defender agent”并不会自动把监督式 min-max 训练变成 MARL。Lowe 等的原始 MADDPG 形式化和算法都明确建立在这一 joint-action critic 上。citeturn18view0

这反而是好消息：**DRIFT 的攻击动作是一次域名扰动，episode horizon 可以取 \(H=1\)**。因此，时间上的 Bellman credit assignment 基本消失；真正困难的是**训练轮次之间对手不断变化造成的非平稳性**。MAB-Malware 已经给出了很有价值的安全领域先例：作者刻意把恶意软件逃逸生成改成 stateless multi-armed bandit，以避免组合状态爆炸，并报告其黑盒逃逸率高于当时多个现成攻击框架。citeturn25academia2turn27view0

由此，本报告的优先级判断是：

**P3 通过后，不建议立即进入“攻击者和检测器每个 minibatch 同步更新”的完整 P4。应先插入 P3.5：学习型攻击者预训练后冻结 + 固定攻击器/攻击者快照池。** 这一步能把两个科学问题拆开：

\[
\text{学习型攻击者是否真的更强？}
\]

和

\[
\text{双方同时学习本身是否提供额外收益？}
\]

PSRO 的核心就是针对“只对当前对手过拟合”的问题维护策略集合、对混合策略求近似 best response；MADDPG 本身也专门提出 policy ensemble 来提高对不同竞争策略的鲁棒性。citeturn17academia0turn18view0 AlphaStar 后来把这一人口/对手池思想规模化为 league training，通过历史快照和专门 exploiter 避免主策略遗忘已有弱点。这个思想对 DRIFT 的单步博弈比复杂时序 MARL 更容易直接迁移。

对“GRPO × MARL 是否已有先例”的检索也给出了明确边界：**截至 2026 年已经不能声称“把 GRPO 引入 multi-agent 是新的”。** 2026 年的 M²GRPO 明确把 group-relative optimization 扩展到 CTDE 多机器人协作；Graph-GRPO 在多智能体通信拓扑学习中按 query 采样一组图并做相对奖励；2025 年 OPERA 更直接使用了 `MAPGRPO` 这一名称。citeturn25academia3turn27academia0turn27academia6 但本轮**没有找到一个已经成为成熟、同行评议标准算法的“二玩家零和 adversarial GRPO”对应物**。因此未来可论证的差量只能落在“**DGA 单步有效扰动约束下、同源域名成组采样、面对自适应检测器的训练动力学**”，而不能落在“multi-agent GRPO”四个字本身。

最后，现有文献**不能替你们推导出“learned attacker 一定比 CharBot/MaskDGA 强”**。恶意软件领域有学习型 bandit/RL 攻击显著有效的证据，RELEVAGAN 和 2026 年的 malware co-evolution 工作甚至直接研究了攻击者随检测器学习；但本轮没有发现一个干净的 DGA 同协议实验，在相同合法扰动预算下直接证明 learned policy 稳定优于 CharBot/MaskDGA。citeturn24view0turn27view6 **这恰好应该成为 P4 前的资格门，而不是由文献替代实验。**

## 网络安全中的攻击者—防守者双侧学习先例

### 从固定攻击器到真正双侧学习，应分四层看

网络安全文献很容易因为“有 GAN 两个网络”就被误读成“攻击者与实际检测器同时学习”。为了避免把成熟工作改名，建议按下面四级区分。

| 层级 | 典型工作 | 实际学习关系 | 与 P4 的距离 |
|---|---|---|---|
| 固定/算法攻击 + 学习检测器 | CharBot、MaskDGA、Drichel 等多攻击 AT | 攻击器规则或优化过程固定；检测器学习 | P2/P3 附近 |
| 学习型攻击者 + 固定目标检测器 | MAB-Malware 等 | attacker 学，deployed detector 不学 | P3.5 attacker 资格验证 |
| 学习型攻击者 + 学习 surrogate | MalGAN、IDSGAN | attacker 和 surrogate 同时学，但真正 target 固定 | 比 P3.5 深，仍非 P4 |
| attacker + 实际 defender 共演化 | RELEVAGAN、2026 bilevel malware co-evolution | 攻击侧随 defender 改变；defender 也随攻击改变 | 最接近 P4 |

### DGA：CharBot、MaskDGA 与 Drichel 的边界

CharBot 的核心价值恰恰在于**极其简单且不需要知道目标分类器**；它是攻击算法，而不是一个根据当前 detector reward 更新的攻击 policy。Peck 等把它作为简单黑盒 DGA 逃逸方法提出。**核验状态：◐ 原文摘要核验；作者 Peck 等，2019，原始 arXiv 题录与摘要。** citeturn21academia2

MaskDGA 同样不是 P4 意义上的学习型对手。Sidi、Nadler、Shabtai 的设计根据代理模型相关信息产生字符扰动并攻击未知结构目标；原实验中四种 DGA classifier 的平均 F1 从 0.977 降到 0.495，但攻击过程不是“目标 detector 每更新一次，攻击 policy 就把新 reward 纳入 RL”。**核验状态：◐；Sidi、Nadler、Shabtai，2019 预印本/后续正式发表版本；原文摘要。** citeturn21academia1

Drichel、Meyer、Meyer 的 **Towards Robust Domain Generation Algorithm Classification** 是这里更重要的成熟强基线：ASIA CCS 2024，DOI 题录已由原文核验。作者实现 32 种 white-box attack，其中 19 种可令未加固模型 FNR 接近 100%，并明确指出只用一种攻击做 AT 再用同一攻击验证不足以说明一般鲁棒性；他们采用 leave-one-group-out 的方式检验对未参与 hardening 的攻击的泛化。**核验状态：✅；ASIA CCS 2024；§1、§2.1–2.4，尤其 §2.4 和引言对 LOGO robustness evaluation 的说明。** citeturn22view0

这直接约束 P4 的论文定位：**“我们做了 adversarial training”不够；“我们让攻击器产生更多 hard examples”也不够。** Drichel 已经把多攻击、未知攻击泛化、离散 adversarial domain 与 latent adversarial vector 联合 hardening 推得很深。P4 真正可能贡献的是“**对手分布随 defender 改变时，如何学到持续有效的攻击分布以及如何稳定双方训练**”。citeturn22view0

交接包给出的“联合 AT 相对仅 embedding-space AT 改善 10.15%”本轮没有在网页文本中重新定位到原文对应表格，因此这里**不把 10.15% 当作独立核验数字**；应由本地全文再查对应实验位置。

### Intrusion：IDSGAN 是“学习攻击者 + 学习 surrogate”，不是双侧实际 detector

Lin、Shi、Xue 的 IDSGAN 让 generator 学习变换恶意流量，同时训练 discriminator 去**动态逼近真实黑盒 IDS**。它还限制可以修改的特征以保持原始攻击 functionality。这里双方神经网络确实一起训练，但 discriminator 的角色是 target model 的 surrogate；被真正攻击的 IDS 本身没有随着 generator 一起训练。**核验状态：✅ 摘要级机制核验；Lin、Shi、Xue，2018；原文摘要。** citeturn21academia3

因此，把 IDSGAN 写成“已有攻击者—真实检测器双侧学习”会过度解读；更准确的近邻关系是：

\[
\text{learned attacker}
\leftrightarrow
\text{learned opponent model}
\rightarrow
\text{fixed deployed detector}.
\]

这对 P4 的意义主要在“**opponent modeling**”而不是 simultaneous defense learning。

### Malware：MalGAN 与 MAB-Malware分别覆盖 surrogate 与 adaptive attacker

Hu、Tan 的 MalGAN 也是一个容易被混淆的例子。它训练 generator，同时训练 substitute detector 去拟合黑盒 malware detector；generator 再攻击 surrogate。真正黑盒 target 仍然固定。作者报告 MalGAN 可把若干黑盒检测模型的检测率压到接近零。**核验状态：◐；Hu、Tan，2017，原始 arXiv；摘要。** citeturn23academia37turn24view2

Song、Li、Afroz、Garg、Kuznetsov、Yin 的 **MAB-Malware** 更贴近你们攻击者侧。论文把 black-box PE malware evasion 建模为 multi-armed bandit，并明确强调 stateless 化以避免 action combinations 的状态空间爆炸，同时通过最小化修改帮助正确归因 reward；作者报告在两个 ML detector 上达到约 74%–97% evasion，在商业 AV 上约 32%–48%。**核验状态：✅；Song 等，RAID 2020；摘要、§2.2、§3.2 及实验部分。** citeturn25academia2turn26view0turn27view0

这是“learned attacker 相比固定/现成 attack framework 有实证价值”的最好证据之一，但应非常谨慎地外推：**它证明的是 malware problem space 中 bandit attacker 能胜过当时若干 off-the-shelf frameworks，不证明 DGA 上 learned policy 必然胜过 CharBot/MaskDGA。** citeturn25academia2

### 最接近 P4 的先例：RELEVAGAN

Randhawa、Aslam、Alauthman、Khalid、Rafiq 的 RELEVAGAN 是本轮找到的最接近 P4 的早期网络安全先例之一。它让 DRL attacker 持续攻击一个作为 botnet detector 的 discriminator；训练继续进行时，agent 学会规避当前 discriminator，而 discriminator 每个迭代又用 DRL 产生的 evasive samples 和 generator samples 继续更新。原文明确写道，随着训练推进 attacker 学习 evasion，discriminator 也被这些新样本 harden。**核验状态：✅；原始预印本 2022；§2.7–2.8、§3.1 Motivation、§3.2 Architecture。** citeturn24view0

它对双侧非平稳性的处理却没有达到现代 MARL/league 的深度：论文主要依靠**限制语义空间 + 迭代 adversarial training + GAN/DRL 联合结构**，并报告相较 EVAGAN 更早收敛和较稳定的训练；没有看到 PSRO 式 opponent population、policy fingerprint、显式 exploitability 控制或 opponent-learning-aware 二阶更新。citeturn24view0

所以它是**“P4 不是空白”**的证据，同时又是**“仍有训练动力学差量可做”**的证据。

### 2026 malware bilevel co-evolution：最直接但证据仍新

Jurečková、Jureček、Kozák、Lórencz 在 2026 年提出 **Adversarial Co-Evolution of Malware and Detection Models: A Bilevel Optimization Perspective**，显式把 defender–attacker 看成迭代对抗共演化过程，并使用 MAB-Malware attacker。其摘要报告：标准分类器或基础 adversarial retraining 的 evasion 可高达 90%，而其 bilevel framework 在所测三类 malware 上把 evasion 降到 0–1.89%，同时显著提高 attacker query cost。该工作也出现在 SECRYPT 2026 的会议日程索引中。**核验状态：◐；2026 arXiv v1 + SECRYPT 2026 program listing；摘要，本轮未逐表复核。** citeturn27view6turn23search4

对 P4 来说，它带来一个重要的先占边界：

> **到 2026 年，“attacker 和 defender 一起演化比一次 adversarial retraining 更好”本身已经不能安全视为新命题。**

P4 的差异必须进一步落到**DGA 的离散一次扰动、同源样本组相对 credit、训练非平稳性稳定机制，或者对未见攻击策略的泛化**。citeturn27view6

### Spam：有战略对抗先例，但不应写成现代双侧 MARL

Lowd 与 Meek 的 **Adversarial Learning** 是早期垃圾邮件/对抗分类的重要历史锚点：攻击者根据分类结果推断并规避 classifier，属于“对手会适应”的经典 adversarial classification 问题。它不是两个深度 agent 同时训练，作用是证明**固定 IID 对手假设在 spam 等任务里从一开始就不成立**。**核验状态：◐；Lowd & Meek，KDD 2005；原始论文题录/正文入口已核验。** citeturn23search5

因此，从 cybersecurity 先例来看，真正的文献图景不是“大量 P4 已有工作”，而是：

\[
\boxed{
\text{固定攻击}
\gg
\text{学习攻击者对固定目标}
>
\text{surrogate 对手建模}
>
\text{实际 defender–attacker 共学习}
}
\]

最后一类有明确先例，但仍远少于前三类。这个稀疏性是本轮文献检索得到的判断，而不是“绝对不存在更多论文”的证明。citeturn22view0turn24view0turn27view6

## MARL 非平稳性技术：哪些能借给单步攻击—检测博弈

### 非平稳性在你们问题里发生在哪里

经典 MARL 的问题是：agent \(i\) 看到的环境转移/收益分布取决于其他 agent 的策略，而其他策略训练过程中一直变化；因此对单个 agent 来说环境不是 stationary。Lowe 等明确指出这会破坏普通 Q-learning/experience replay 的假设。citeturn18view0

你们却没有必要把一次 domain perturbation 人为展开成很长轨迹。可以把一次训练交互写成：

\[
x\sim\mathcal D_{\text{src}},
\]

攻击者：

\[
a\sim\pi_\theta(a\mid x),
\qquad
x'=\tau(x,a),
\]

检测器：

\[
p_\phi(x')=D_\phi(x'),
\]

攻击奖励：

\[
r_A(x,a;\phi)
=
\mathbf 1[\text{valid}(x')]
\mathbf 1[D_\phi(x')=\text{benign}],
\]

而检测器在 adversarial batch 上最小化分类风险。

当 detector 参数从 \(\phi_t\) 变成 \(\phi_{t+1}\) 时：

\[
r_A(x,a;\phi_t)
\neq
r_A(x,a;\phi_{t+1}).
\]

因此非平稳性存在，但主要是**跨 optimization round 的 opponent drift**，而非 episode 内的多步 temporal dynamics。这与 Hernandez-Leal 等将 multi-agent non-stationarity 概括为“moving target”问题的核心一致。citeturn18view0turn19view6

### 可迁移技术清单

| 技术 | 原始出处与位置 | 单步 DRIFT 可迁移性 | 本报告判断 |
|---|---|---:|---|
| **CTDE / joint-action critic** | Lowe et al., NeurIPS 2017, §4.1，Eq. 4–6 | 中 | 原理有用，完整 MADDPG critic 暂不优先 |
| **显式 opponent model** | Lowe et al., §4.2，Eq. 7–8 | 中 | 黑盒 defender 时有意义；训练内完全可访问 detector 时可能冗余 |
| **policy ensemble** | Lowe et al., §4.3 | **高** | 可直接转成 attacker snapshot pool |
| **replay importance correction** | Foerster et al., ICML 2017，stabilised replay 方法部分 | 高，若使用 replay | 给旧 transition 降权，防止旧 detector reward 污染当前 attacker |
| **policy fingerprint / training-age conditioning** | Foerster et al., ICML 2017，fingerprint 方法与 §6.2 | **高**，若跨版本 replay | 把 detector version/训练轮次随经验保存 |
| **PSRO / population best response** | Lanctot et al., NeurIPS 2017，PSRO 方法/Algorithm 1 | **很高** | 最适合 P3.5 |
| **opponent-learning awareness** | Foerster et al., AAMAS 2018，LOLA | 理论适用，工程低优先 | 需要预测对手更新，复杂且易引入高阶梯度 |
| **trust-region / clipped policy movement** | PPO/GRPO 家族 | 高 | 限制 attacker 每次剧烈漂移 |
| **recurrent opponent history** | 多种 MARL | 低 | \(H=1\) 时没有必要，除非把历史 detector versions 当 meta-state |
| **VDN/QMIX/hysteretic cooperative credit** | cooperative MARL | 低 | 与攻击者—检测器零和/冲突利益不匹配 |
| **COMA 式 team counterfactual credit** | cooperative CTDE | 低 | 两玩家单动作且 reward 直接可观测时解决了错误问题 |

MADDPG 的集中式 critic：

\[
Q_i^{\pi}
(\mathbf x,a_1,\ldots,a_N)
\]

显式以所有 agent 的动作作为输入。Lowe 等的理由很直接：**给定所有 joint actions 后，transition dynamics 不再因为其他策略参数改变而显得非平稳。** 同一论文还指出竞争策略很容易过拟合当前 opponent，因此在 §4.3 额外提出 policy ensembles。**核验状态：✅；Lowe et al., NeurIPS 2017, §4.1–4.3。** citeturn18view0

但这一思想迁移到 DRIFT 时应“取机制、不照搬形状”。当 \(H=1\) 时：

\[
Q(x,a)
=
\mathbb E[r\mid x,a],
\]

没有真正需要 bootstrap 的未来 return。你已经可以直接观察当前 detector 对扰动的 reward，因此再学习一个深度 \(Q\) 网络会引入额外 function approximation error、replay staleness 和超参数，而它最主要的 temporal-value 优势被削弱。这是基于 MADDPG 公式和你们 \(H=1\) 设定作出的**方法学推论**。citeturn18view0

### Replay fingerprint：对 P4 很实用，但只在你真的 replay 时需要

Foerster 等针对 independent learners 的 replay non-stationarity 提出两类修复：一类利用 multi-agent importance sampling 让过时经验衰减；另一类给 observation 加“fingerprint”，例如训练迭代编号或 exploration 参数，使网络能判断这条经验来自训练哪个阶段。实验中 fingerprint 明显改善了 feed-forward agent 的表现。**核验状态：✅；Foerster et al., ICML 2017，方法部分、§6.2、Conclusion。** citeturn11view4

对 P4 的直接映射可以非常简单：

\[
e=(x,a,r,\text{detector\_version}),
\]

不要让 attacker 把在 \(D_{\phi_{t-20}}\) 上成功的 evade transition 当作当前 \(D_{\phi_t}\) 下同分布经验。

但若 P4 使用真正 on-policy 的 GRPO-style rollout，**更简单的办法是完全不 replay 旧组**：一个 attacker update window 内冻结 detector，组采样全部完成后再更新 detector。此时无需为了“使用 MARL 技术”而人为加 replay buffer。

### LOLA：理论相关，但不应成为第一稳定器

Foerster 等的 LOLA 不是仅对“当前 opponent policy”作 best response，而是让 agent 的更新显式考虑**自己的策略会如何影响对手下一步参数更新**。作者将这作为 opponent-learning awareness，并在 repeated games 中展示了与 naive learning 不同的策略动力学。**核验状态：◐；Foerster et al., AAMAS 2018；摘要机制已核验。** citeturn16academia0turn19view6

这在 \(H=1\) 的 DRIFT 里理论上仍然成立，因为“opponent learning”发生在**训练轮次**而非环境时间步；但是它需要对对手更新求导或近似高阶影响。后来关于 LOLA 的研究还指出原始 LOLA 存在参数化敏感性和 opponent-modeling 下的不一致性问题。citeturn15academia3turn16academia3

因此它更适合作为“为什么 P4 的学习动力学很难”的文献，而不是第一实现件。

### 用户给出的综述锚点如何放进章节

Hernandez-Leal 等的多智能体学习综述把处理对手变化的方法按认知深度概括为从**忽略非平稳性、遗忘旧经验、响应预定义目标模型、显式学习 opponent model，到更深层的 theory-of-mind**；另一篇 deep MARL survey 则将 moving target、credit assignment、exploration 等列为核心挑战。**核验状态：✅/◐；Hernandez-Leal et al., Autonomous Agents and Multi-Agent Systems 2019 及其 non-stationarity survey。** citeturn19view6turn18view0

交接包指定的李艺春等《多智能体强化学习的博弈综述》（自动化学报 2025）、杜威与丁世飞《多智能体强化学习综述》（计算机科学 2019 46(8)）、罗彪等《多智能体强化学习控制与决策研究综述》（自动化学报 2025）、Tampuu et al. PLoS One 2017、Tan ICML 1993，本轮按用户要求**不重复全文检索**。它们可作为中文/历史综述锚点，但凡涉及具体算法机制和你们 P4 的设计判断，本报告以上述 Lowe、Foerster、Lanctot 等一级原始方法论文承担证据。**核验状态：△，交接包指定题录，本轮未重新确认具体节号。**

## GRPO × MARL：已有先例以及与 MADDPG 的本质区别

### 原始 GRPO 到底提供了什么

Shao 等在 **DeepSeekMath** 中提出 GRPO，核心动机是去掉 PPO 的 learned value critic：对同一个 question/prompt 采样一组 outputs，以该组 reward 的均值和标准差构造相对 advantage，再使用 PPO-style policy-ratio/clipping 与参考策略约束更新模型。**核验状态：✅；Shao et al., 2024，DeepSeekMath §4.1 Group Relative Policy Optimization、§4.1.2 Outcome Supervision。** citeturn26search0turn26search2

抽掉语言模型的 token 结构后，你们同一个原域名 \(x\) 采样 \(K\) 个扰动：

\[
a_1,\ldots,a_K
\sim
\pi_\theta(\cdot\mid x),
\]

得到：

\[
r_k=r(x,a_k;D_\phi),
\]

组相对 advantage 可以写成：

\[
A_k
=
\frac{r_k-\bar r_x}
{s_x+\epsilon},
\]

其中

\[
\bar r_x=\frac1K\sum_{j=1}^{K}r_j,
\qquad
s_x^2=
\frac1K
\sum_{j=1}^K
(r_j-\bar r_x)^2.
\]

这种构造在 DGA 上有一个非常自然的解释：**同一原域名内部比较 perturbations，自动消掉一部分“这个域名本身就很容易/很难逃逸”的 context difficulty。** 这是把 GRPO 的 group baseline 迁到 contextual one-shot attack 后得到的推论。citeturn26search0

一个命名边界尤其重要：

> **如果 P3 只是根据这些相对分数给 detector 的 supervised adversarial examples 加权，而没有优化攻击 policy，那么 P3 不是 GRPO 算法；准确说法应是“借用了 group-relative advantage/normalization 的结构”。**

同样，若 P4 只做：

\[
\nabla_\theta
\log\pi_\theta(a_k|x)A_k
\]

而没有 GRPO 原方法的 policy-ratio clipping/reference KL 等组件，更稳妥的名称也是 **group-relative policy gradient / GRPO-style objective**，而不是声称完整 GRPO 复现。原始 GRPO 是成熟方法，不能只取“组内减均值”就重新命名。citeturn26search0

### 截至 2026，multi-agent GRPO 已经存在

本轮发现三类直接相关工作。

**M²GRPO**：Feng、Wu、Wu、Gu、Yu，2026，面向仿生水下机器人 cooperative pursuit，采用 CTDE，并将 rewards 在 episode 内跨 agents 归一化形成 group-relative advantages，作者明确称其为 GRPO 的 multi-agent extension。它还结合 Mamba 处理长期部分可观测序列。**核验状态：◐；2026 arXiv preprint，摘要；本轮未发现成熟同行评议 venue。** citeturn25academia3

**Graph-GRPO**：Cang 等，2026，在 LLM multi-agent communication topology 中，同一个 query 采样一组通信图，以组内相对表现给 edge credit。它不是 attacker–defender game，但其“**同一 context 采多个结构、组内归一 reward**”与 P3/P4 的 \(K\)-perturbation grouping 结构其实比 M²GRPO 更相似。**核验状态：◐；2026 arXiv preprint，摘要。** citeturn27academia0

**MAPGRPO**：OPERA 工作在 2025 年已经使用 “Multi-Agents Progressive Group Relative Policy Optimization” 这一名称来训练 planner/executor 式 multi-agent retrieval system。它同样不是经典 zero-sum MARL，但意味着 `MAPGRPO` 这一命名不能作为你们可自由占用的新方法名。**核验状态：◐；2025 arXiv preprint，摘要。** citeturn27academia6

所以目前能支持的结论是：

\[
\boxed{
\text{GRPO→multi-agent：已有先例}
}
\]

但：

\[
\boxed{
\text{GRPO→二玩家网络安全单步攻防共演化：
本轮未发现成熟标准先例}
}
\]

后一句为 **🧭 检索性结论**，不能写成“世界首创”。

### Group-relative attacker 与 MADDPG critic 到底差在哪里

这部分可以成为以后方法章节非常清楚的一段。

MADDPG 对 agent \(i\) 学：

\[
Q_i^{\pi}
(\mathbf x,a_A,a_D),
\]

并用：

\[
\nabla_{\theta_i}J
=
\mathbb E
[
\nabla_{\theta_i}\pi_i
\nabla_{a_i}
Q_i^{\pi}
(\mathbf x,a_A,a_D)
].
\]

它的 critic 是**跨样本学习出来的函数近似器**，显式观察所有 agent 的 joint actions，训练时使用 replay 和 delayed target policies；actor 执行时才只保留自己的 local observation。**核验状态：✅；Lowe et al., NeurIPS 2017，§4.1 Eq. 4–6。** citeturn18view0

你们的 group-relative attacker 则可以完全不用 \(Q_\psi\)：

\[
x
\rightarrow
\{a_1,\ldots,a_K\}
\rightarrow
\{r_1,\ldots,r_K\}
\rightarrow
\{A_1,\ldots,A_K\}.
\]

二者的本质区别不是“一个单智能体、一个多智能体”，而是：

| 维度 | MADDPG | 同域名 group-relative attacker |
|---|---|---|
| advantage 来源 | learned centralized critic | 同一 context 的实际组内 rewards |
| critic | 有 | 无 |
| temporal bootstrap | 有 | \(H=1\) 时不需要 |
| 对 joint action 建模 | 显式 | 可通过固定 opponent snapshot 间接条件化 |
| 跨 context 泛化 | critic 可以学 | group baseline 本身不学 |
| opponent drift 风险 | critic/replay 会 stale | detector 在一组采样内改变则 reward baseline 也 stale |
| sample cost | critic 可复用经验 | 每个 \(x\) 要采 \(K\) 次 |
| function approximation bias | 有 critic bias | 无 value-critic bias，但 Monte Carlo 方差仍在 |

因此对你们的**单步、reward 可直接观察**场景，critic-free 是有实质理由的，而不是为了追 GRPO 热点：MADDPG critic 的主要 temporal-value 建模价值在 \(H=1\) 下明显降低，而 learned critic 本身还会随 opponent 改变变成另一个 moving target。这是由 MADDPG 和 GRPO 原始形式共同支持的方法学推论。citeturn18view0turn26search0

### 一个 P4 实现上的硬要求：同一组 reward 必须来自同一 detector snapshot

假设同一个域名的 \(K\) 个样本中，前一半由 \(D_{\phi_t}\) 评分，后一半在 detector 已经更新成 \(D_{\phi_{t+1}}\) 后评分，则：

\[
r_k
=
r(x,a_k;\phi_k)
\]

已经不是同一个 reward function 下的 group comparison。

此时：

\[
r_k-\bar r
\]

同时包含“扰动相对强弱”和“detector 在中间改变了”两个因素，group-relative advantage 的解释被污染。

因此如果 P4 最终实施，**攻击组采样期间冻结 detector 是比“同步更新双方”更合理的第一版本**：

\[
\boxed{
\text{freeze defender}
\rightarrow
\text{sample/update attacker}
\rightarrow
\text{freeze attacker}
\rightarrow
\text{update defender}
}
\]

而不是：

\[
A\leftarrow\text{update},
D\leftarrow\text{update},
A\leftarrow\text{update},
D\leftarrow\text{update}
\]

逐 minibatch 互追。

这和 PSRO 的 approximate best response to a policy mixture，以及 2026 malware bilevel co-evolution 的分层思想都更接近。citeturn17academia0turn27view6

### 二值 bypass reward 有一个 GRPO 特有的退化点

如果：

\[
r_k\in\{0,1\}
\]

且某组 \(K\) 个扰动全部失败：

\[
r_1=\cdots=r_K=0,
\]

或全部成功：

\[
r_1=\cdots=r_K=1,
\]

则：

\[
s_x=0.
\]

带 \(\epsilon\) 的实现会得到几乎全零 advantage；不正确处理则会出现数值问题。换句话说，**group-relative credit 只在同一组内真的出现 relative ordering 时才产生学习信号。** 原始 GRPO 同样依赖组内 reward 差异，只是数学推理任务常使用更丰富的 correctness/reward signal。citeturn26search0

因此 P4 立项前应该先测一个纯源期诊断：

\[
P(0<\sum_k r_k<K),
\]

即“mixed-outcome group rate”。若绝大多数组都是 all-zero/all-one，换 GRPO 并不能凭空创造攻击 credit。

## 单步 adversarial generation 的 RL 形式化与 reward hacking

### 最准确的形式不是长轨迹 MDP，而是 contextual bandit / horizon-one game

MAB-Malware 已明确展示：安全攻击并不总需要复杂 stateful MDP。作者认为许多有效 malware modification 由一个或少数关键 actions 决定，因此将其 stateless 化，避免组合爆炸。**核验状态：✅；Song et al., RAID 2020，§3.2 与摘要。** citeturn25academia2turn27view0

对于 DRIFT，可以更直接写成 contextual bandit：

\[
x\sim\mathcal D,
\qquad
a\sim\pi_\theta(a|x),
\qquad
x'=\tau(x,a),
\qquad
r=r(x,a).
\]

然后 episode 结束。

若 \(a\) 一次性包含：

\[
a=(\text{positions},\text{replacement chars},\text{optional operator type}),
\]

那么“生成一个攻击域名”就是一个动作，不需要虚构：

\[
s_0\to s_1\to\cdots\to s_T
\]

去获得 MARL 的外观。

P4 仍然可以视为**重复 zero-sum stage game**：每个样本内部 \(H=1\)，训练轮次上 attacker policy 和 defender parameters 共演化。这一写法在理论上比“多步 DGA 控制过程”更干净，也更贴 MAB-Malware 的安全领域经验。citeturn25academia2

### 奖励不应该只有“骗过 detector”

最朴素：

\[
r_{\text{evade}}
=
\mathbf 1[
D_\phi(x')=\text{benign}
]
\]

会天然允许 reward hacking：

> 生成一个根本不再代表原恶意 DGA 行为的奇怪字符串，只要 detector 把它判 benign，就拿满分。

Pierazzi 等的问题空间攻击形式化恰好指出：security adversarial examples 除了“让 classifier 错”，还必须考虑**允许的 transformations、preserved semantics、无异常 artifacts，以及 plausibility**。**核验状态：✅/◐；Pierazzi/Cortellazzi 等，IEEE S&P 2020 extended version，problem-space formalization；摘要明确列出四类约束。** citeturn25academia4turn27view4

Drichel 在 DGA 领域也明确要求把 embedding-level adversarial vector 离散回**RFC-valid adversarial domains**，否则向量攻击不能直接当成实际 DGA 输入。**核验状态：✅；Drichel et al., ASIA CCS 2024，§1、攻击离散化讨论。** citeturn22view0

因此攻击 policy 的实际 action space 应首先是：

\[
\mathcal A_{\mathrm{valid}}(x)
=
\{
a:
V_{\mathrm{syntax}}=1,
V_{\mathrm{threat}}=1,
V_{\mathrm{semantic}}=1
\}.
\]

最佳策略不是让无效动作生成后靠 soft penalty 教它慢慢学，而是**尽可能从 decoder/action mask 层面令非法动作不可采样**。

### DGA 中“语义保持”至少要拆成四层

**语法有效性**：

\[
V_{\text{syntax}}(x')=1
\]

要求域名符合预先固定的合法字符、长度和域名语法约束。Drichel 明确把 RFC-validity 作为 adversarial vector 离散化的约束。citeturn22view0

**扰动预算有效性**：

若 threat model 是 CharBot-style 两位替换：

\[
d_H(x,x')\le 2.
\]

若允许一般编辑：

\[
d_{\mathrm{edit}}(x,x')\le\epsilon.
\]

但这里必须引用 Drichel 的反提醒：**在 DGA 问题中，小编辑距离本身并非天然的真实威胁约束**；攻击者生成 AGD 时并不像图像攻击必须保持肉眼不可见。因此 edit bound 是你们选择的攻击能力模型，不等价于“恶意语义保证”。citeturn22view0

**家族／生成机制保持**：

若本地实验协议已有合法的 family-validity 或 generator-validity 判定，则可要求：

\[
V_{\text{family}}(x,x')=1.
\]

但“一个分类器认为它像某 family”并不足以证明真实 malware 会产生它。更强的含义应该是：**变换在该威胁模型下不会破坏该 DGA 的可用生成/解析条件。** Pierazzi 对 problem-space semantics 的区分正说明，feature similarity 与真实 functionality 不能等同。citeturn25academia4

**可实现性／plausibility**：

攻击不能仅利用 tokenizer、padding 或未定义字符制造一个实验室字符串，而应处于预注册 attack interface 能实际产生的集合中。Pierazzi 将 plausibility 和 artifact constraints 与 semantic preservation 分开处理，这一点非常适合用来反驳“只要编辑距离小就是合法攻击”的写法。citeturn27view4

### 推荐奖励结构

在只允许有效动作被采样时，可写：

\[
r_A(x,a;\phi)
=
r_{\mathrm{evade}}
-\lambda_c C(x,x')
+\lambda_d R_{\mathrm{div}}.
\]

其中 \(C\) 是预先定义的 perturbation cost，\(R_{\mathrm{div}}\) 只能作为很弱的探索辅助。

若不能从动作空间层面完全排除非法样本，可以采用：

\[
r_A
=
V(x')
\big[
r_{\mathrm{evade}}
-\lambda_c C
\big]
-
M(1-V(x')),
\]

其中 \(M\) 应足够大到使 invalid bypass 不值得选择。

但对于**恶意语义是否保持这种硬安全约束**，本报告更支持：

\[
V(x')=0
\Rightarrow
\text{reject before detector reward}
\]

而不是允许 policy 用极高 evade reward 抵消 validity penalty。

### 二值 reward、dense reward 与黑盒威胁模型不可混写

若 attacker 只允许获得 hard label，则：

\[
r\in\{0,1\}
\]

更符合 black-box label-only threat model，但探索会很稀疏；MAB-Malware正是面向 hard-label black-box 场景设计其 bandit attack。citeturn25academia2

如果使用 detector logit：

\[
r_{\text{dense}}
=
-p_\phi(y=\mathrm{DGA}\mid x'),
\]

或者 margin：

\[
r_{\text{margin}}
=
z_{\text{benign}}(x')
-
z_{\text{DGA}}(x'),
\]

组内 ordering 会明显更丰富，但你已经把 attacker interface 改成 score-access。不能训练时吃 logits，最后却把方法叙述成“label-only black-box RL attacker”。

一种干净的章节协议是：

\[
\text{训练 reward：dense score，白盒/score-access setting}
\]

与

\[
\text{正式绕过指标：binary ASR at fixed threshold}
\]

明确分开；若论文目标坚持 hard-label black-box，则不能使用前者。

### 预注册 reward-hacking 诊断

不仅报 ASR，还应源期同步监测：

\[
\text{ValidRate}
=
\frac{\#\text{valid adversarial domains}}
{\#\text{all generated}},
\]

\[
\text{UniqueRate}
=
\frac{\#\text{unique valid perturbations}}
{\#\text{valid perturbations}},
\]

以及 edit-position entropy、replacement-character entropy、按 family 的 valid-ASR。

最危险的伪成功形态是：

\[
ASR\uparrow
\quad\text{but}\quad
ValidRate\downarrow,
\]

或者：

\[
ASR\uparrow,\;
UniqueRate\rightarrow0,
\]

即 policy 找到了一个 detector artifact 或单一字符串模板，而不是学会了攻击策略。Pierazzi 的 problem-space constraints 和安全领域的 functionality-preserving RL 文献都说明，这类“feature-space 成功、problem-space 无效”必须排除。citeturn25academia4turn24view0

## P4 相对 P3 的预期增量、风险与建议的 P3.5 中间层

### P3 和 P4 真正差在哪

按交接包定义，P3 已经有：

\[
\{x'_1,\ldots,x'_K\}
\]

同源扰动组，以及基于 group-relative hardness 的 detector gradient weighting。

P3 解决的是：

> 在**给定攻击分布**下，哪些 perturbations 应对 detector 更新贡献更大？

P4 才改变：

\[
q_{\text{attack}}(a|x)
\]

本身，使其依赖 detector feedback：

\[
q_t(a|x)
=
\pi_{\theta_t}(a|x;D_{\phi_t}).
\]

因此真正可检验的增量命题是：

\[
\boxed{
\text{adaptive attack distribution}
>
\text{fixed perturbation distribution}
}
\]

以及进一步：

\[
\boxed{
\text{co-evolving adaptive distribution}
>
\text{frozen learned attacker distribution}
}
\]

这两层必须分别证，否则 P4 的增益无法归因。

### 文献对“P4 会增益”的支持有多强

支持面存在，但强度并不均匀。

MAB-Malware 证明 learned stateless/bandit attacker 在 malware black-box evasion 上可以显著有效，并报告高于若干已有攻击框架的 evasion。citeturn25academia2

RELEVAGAN 表明，一个根据当前 detector feedback 学习的 DRL attacker 可以被嵌入 detector 的 adversarial training loop，双方随训练共同变化。citeturn24view0

2026 的 bilevel malware co-evolution 更直接报告 adaptive attacker 会重新突破 basic adversarial retraining，而分层 co-evolution 可显著增强 defender。citeturn27view6

但 Drichel 在 DGA 领域同时提醒：很多过去看起来很强的 CharBot/对抗 DGA 攻击，在更现实的 NXD-trained classifier 上可能表现完全不同；他们甚至报告某些此前攻击会被真实数据训练的 classifier 以超过 99% TPR 检出。**攻击强度高度依赖 detector/data protocol。** citeturn22view0

所以“别的 malware RL attacker 强”不足以跳过 DRIFT 自己的资格测试。

### 为什么不建议 P3 通过后立刻开完整 P4

P4 至少同时新增四个失败源：

\[
\text{policy optimization variance},
\]

\[
\text{opponent non-stationarity},
\]

\[
\text{semantic/reward hacking},
\]

\[
\text{strategic overfitting/cycling}.
\]

MARL 原始研究明确观察到 agent policy 同时变化导致 moving-target non-stationarity；competitive policies 还能过拟合训练对手，在对手改变后失效。citeturn18view0turn17academia0

如果 P4 相对 P3 有增益，你还必须排除它只是因为“P4 使用了一个更强的 learned attacker”，而不是因为**simultaneous/alternating co-learning dynamics**真正重要。

因此，最干净的因果链是：

\[
P2
\rightarrow
P3
\rightarrow
\boxed{P3.5}
\rightarrow
P4.
\]

### P3.5 首选：预训练后冻结的 learned-attacker pool

第一步，在一个**冻结 detector** 上训练 one-shot attacker：

\[
\theta^*
=
\arg\max_\theta
\mathbb E_{x,a\sim\pi_\theta}
[
r_A(x,a;D_{\phi_0})
].
\]

第二步，保存少量预定义训练阶段的 attacker snapshots：

\[
\Pi_A
=
\{
A_{\text{CharBot}},
A_{\text{MaskDGA}},
A_{\theta_1},
A_{\theta_2},
\ldots,
A_{\theta_m}
\}.
\]

第三步，**冻结整个 attacker pool**，再训练 defender：

\[
\min_\phi
\mathbb E_{A_j\sim\mu}
L_D
(
D_\phi,
A_j(x)
).
\]

这样 detector 面对的 attack population 比 P3 丰富，但训练期间攻击策略本身不漂移。

这不是要创造一个新方法名，而是用一个必要对照回答：

> **P4 的潜在收益究竟来自 learned attacks，还是必须来自 co-learning？**

MADDPG 的 policy-ensemble 设计本身就是为了避免 agent 对单一竞争策略过拟合；Lanctot 等的 PSRO 更系统地维护 policy population 并对对手混合求 approximate best response。**核验状态：✅；Lowe et al. §4.3；Lanctot et al., NeurIPS 2017，PSRO/Algorithm 1。** citeturn18view0turn17academia0

### 更完整的 P3.5：PSRO-lite

Lanctot 等观察到 independent RL 可能严重过拟合当前其他 agent 的策略，提出基于 policy-space response oracles 的 population 方法：维护策略集合，计算 meta-strategy，再训练对这个混合策略的近似 best response。**核验状态：✅/◐；Lanctot et al., NeurIPS 2017；摘要与 PSRO 方法。** citeturn17academia0turn19view1

DRIFT 可以做一个极简版本：

\[
A_0=\text{fixed attack pool},
\]

训练：

\[
D_1=BR_D(A_0),
\]

然后：

\[
A_1=BR_A(D_1),
\]

把 \(A_1\) 冻结加入 pool：

\[
\Pi_A\leftarrow\Pi_A\cup\{A_1\},
\]

再训练：

\[
D_2=BR_D(\mu(\Pi_A)).
\]

这已经把“永远只追当前 opponent”改成“对历史 opponent mixture 做 robust response”，却不需要每个 minibatch 双方同步漂移。

### AlphaStar 给出的可借机制，不是方法名

Vinyals 等的 AlphaStar 采用 league：历史 agent snapshots 留在 population；main agents 不只打当前自身版本，还面对一系列旧策略；专门的 exploiters 被训练去暴露 main agent 的弱点，从而减轻 strategic forgetting。**核验状态：◐；Vinyals et al., Nature 575, 2019，Methods 中 league training / prioritized opponent sampling；本轮以原论文题录和已有原始论文索引核查机制。**

迁移到 DRIFT 不需要模仿 StarCraft 的复杂 league，只需要取三个机制：

\[
\boxed{\text{冻结历史攻击者}}
\]

\[
\boxed{\text{保留固定攻击算子作为永久 league members}}
\]

\[
\boxed{\text{当前 detector 必须同时面对旧攻击者}}
\]

就足以防止一种典型循环：

\[
A_1\text{ 打穿 }D_0
\rightarrow
D_1\text{ 修好 }A_1
\rightarrow
A_2\text{ 打穿 }D_1
\rightarrow
D_2\text{ 却重新被 }A_1\text{ 打穿}.
\]

### P4 真正值得做之前，建议设置四道源期资格门

这里不是裁决现有候选，而是基于文献给出**外部实验排序建议**。

**学习型攻击者增量门。** 固定同一个 source-period detector，在完全相同 perturbation budget 和 validity constraints 下比较：

\[
ASR_{\mathrm{learned}}
\quad\text{vs}\quad
ASR_{\mathrm{CharBot}},
ASR_{\mathrm{MaskDGA}},
ASR_{\mathrm{best-fixed}}.
\]

要比较的是 **valid ASR**，不是包含无效字符串后的 raw ASR。MAB-Malware 说明 learned attack 值得测试，但 Drichel 说明攻击排名必须在真实目标模型上重新建立。citeturn25academia2turn22view0

**对手过拟合门。** learned attacker 不只攻击训练它的 \(D_0\)，还攻击一个源期合法、未参与 policy optimization 的 detector snapshot \(D_1\)。若：

\[
ASR(A_{\theta^*},D_0)\gg
ASR(A_{\theta^*},D_1),
\]

则它可能只学会了一个 narrow opponent model。PSRO 与 MADDPG ensemble 都直接针对这一泛化问题。citeturn17academia0turn18view0

**冻结池增量门。** 先跑 P3.5：

\[
P3.5=P3+\text{frozen learned attacker pool}.
\]

如果 P3.5 已经捕获全部收益，则没有证据表明必须支付 P4 的 simultaneous non-stationarity 成本。

**小规模共演化稳定门。** 仅在源期保存少量 attacker/defender snapshots，构造 cross-play matrix：

\[
M_{ij}
=
ASR(A_i,D_j).
\]

理想状态不是只看 diagonal：

\[
M_{tt}\downarrow,
\]

而是新 defender 对历史 attackers 的整列都不重新恶化。否则就是典型 strategic forgetting/cycle：

\[
D_{t+1}
\text{ 抗 }A_t
\quad\text{但重新怕 }A_{t-2}.
\]

policy-population 文献正是用跨策略相互作用而非只看“当前 vs 当前”来处理这种过拟合。citeturn17academia0

### 如果最终进入 P4，建议不是“同步”，而是 windowed alternating game

第一个 P4 版本建议按以下节奏：

\[
\boxed{D_t\text{ frozen}}
\]

同一 detector snapshot 下，对每个 \(x\)：

\[
a_{1:K}\sim\pi_{\theta_t}(\cdot|x),
\]

计算组相对 advantage，做固定数量 attacker updates；

然后：

\[
\boxed{A_{t+1}\text{ frozen}}
\]

生成 adversarial training set/batches，再做固定数量 detector updates：

\[
\phi_t\rightarrow\phi_{t+1}.
\]

最后：

\[
A_{t+1},D_{t+1}
\]

按预注册周期进入 historical pool。

这种设计的优势是每个 optimization window 的 objective 至少短时间 stationary，而且 group rewards 可比较。它更接近 PSRO/alternating best response/bilevel 共演化文献，而不是两个网络每个 minibatch 无约束互追。citeturn17academia0turn27view6

### 什么时候 P4 不值得继续投入

文献层面最强的否定条件不是“MARL 很难”，而是下面三种源期结果之一：

\[
ASR_{\mathrm{learned}}
\le
ASR_{\mathrm{best-fixed}}
\]

在等预算有效攻击下成立；

或者：

\[
P3.5
\approx
P4
\]

即冻结 learned attacker pool 已得到全部 defender 增益；

或者：

\[
D_t
\text{ 对当前 }A_t\text{ 改善}
\quad\text{但}\quad
\max_{i<t}ASR(A_i,D_t)
\uparrow,
\]

表现出历史攻击遗忘。

出现这些结果时，MARL/co-evolution 的额外训练动力学就缺少必要性证据。反过来，若 learned attacker 确实稳定发现固定攻击器找不到的有效绕过、冻结池仍留下 adaptive residual，而 windowed co-learning 能降低**整个人口攻击池**的 worst-case ASR，那么 P4 才获得了清楚的机制增量。

## 来源核验、证据强弱与未回答问题

### 核心原始文献台账

| 文献 | 原始出处 | 精确机制位置 | 核验状态 | 在本课题中的证据角色 |
|---|---|---|---|---|
| Drichel, Meyer & Meyer, *Towards Robust Domain Generation Algorithm Classification* | ACM ASIA CCS 2024 | §1；§2.1–2.4；LOGO robustness 说明 | ✅ | DGA 多攻击 AT 强近邻；限制 P4 创新口径 |
| Sidi, Nadler & Shabtai, *MaskDGA* | 2019 原始预印本/后续正式版 | 摘要；攻击方法正文节号待本地全文重核 | ◐ | 固定/非自适应 DGA 攻击锚 |
| Peck et al., *CharBot* | 2019 原始预印本/后续正式版 | 摘要 | ◐ | 简单固定 attack operator 锚 |
| Lin, Shi & Xue, *IDSGAN* | 2018 原始预印本 | 摘要 | ✅/◐ | learned attacker + learned surrogate，不是实际 detector 共学习 |
| Hu & Tan, *MalGAN* | 2017 原始预印本 | 摘要 | ◐ | learned generator + substitute detector |
| Song et al., *MAB-Malware* | RAID 2020 | 摘要；§2.2；§3.2 | ✅ | stateless/bandit adversarial generation；learned attacker 实证 |
| Randhawa et al., *RELEVAGAN* | 原始预印本 2022；后续期刊版题录需本地再核 | §2.7–2.8；§3.1–3.2 | ✅ | 最接近 RL attacker + evolving detector 的网络安全先例 |
| Jurečková et al., *Adversarial Co-Evolution of Malware and Detection Models* | arXiv 2026；SECRYPT 2026 program listing | 摘要；bilevel 正文待本地全文重核 | ◐ | 最新直接 co-evolution 先例 |
| Lowe et al., *Multi-Agent Actor-Critic for Mixed Cooperative-Competitive Environments* | NeurIPS 2017 | §4.1–4.3，Eq. 4–9 | ✅ | MADDPG、opponent model、policy ensemble |
| Foerster et al., *Stabilising Experience Replay for Deep Multi-Agent RL* | ICML 2017 | importance sampling、fingerprints、§6.2、Conclusion | ✅ | stale replay 修复 |
| Foerster et al., *Learning with Opponent-Learning Awareness* | AAMAS 2018 | 摘要；LOLA 方法正文 | ◐ | opponent-learning-aware 高阶更新 |
| Lanctot et al., *A Unified Game-Theoretic Approach to MARL* | NeurIPS 2017 | PSRO 方法、Algorithm 1；摘要 | ✅/◐ | P3.5 population / best-response 理论锚 |
| Shao et al., *DeepSeekMath* | 2024 | §4.1、§4.1.2 | ✅ | GRPO 原始定义 |
| Feng et al., *M²GRPO* | arXiv 2026 | 摘要 | ◐ | explicit multi-agent GRPO 先例 |
| Cang et al., *Graph-GRPO* | arXiv 2026 | 摘要 | ◐ | per-query group sampling 的 MAS 先例 |
| OPERA / MAPGRPO | arXiv 2025 | 摘要 | ◐ | `MAPGRPO` 名称已有使用 |
| Pierazzi/Cortellazzi et al., *Intriguing Properties of Adversarial ML Attacks in the Problem Space* | IEEE S&P 2020 / extended version | problem-space formalization；摘要 | ✅/◐ | semantics、artifact、plausibility 约束 |
| Lowd & Meek, *Adversarial Learning* | KDD 2005 | 原始论文 | ◐ | spam strategic evasion 历史锚 |
| Hernandez-Leal et al., MARL surveys | Autonomous Agents and Multi-Agent Systems 2019 等 | non-stationarity taxonomy | ✅/◐ | MARL moving-target 总框架 |
| 李艺春等、杜威/丁世飞、罗彪等 | 交接包指定中文综述 | 本轮按要求未重复全文核验 | △ | 中文综述背景锚，不承担核心机制证据 |

核心论断所依赖的原始来源包括：Drichel 对 DGA 多攻击与 leave-one-group-out 评测的讨论；MADDPG 对 non-stationarity、centralized critic、opponent model 和 policy ensemble 的原始推导；MAB-Malware 对 stateless attack learning 的直接安全领域形式化；DeepSeekMath 对 GRPO critic-free group baseline 的原始定义；以及 Pierazzi 等对 problem-space semantic constraints 的形式化。citeturn22view0turn18view0turn25academia2turn26search0turn25academia4

### 目前可以比较有把握写进第三章 related work 的结论

**第一，安全领域已经有学习型 attacker，但“真实 detector 与 attacker 同步学习”的先例明显少于 learned attacker vs frozen detector。** RELEVAGAN 和 2026 bilevel malware co-evolution 是最直接的近邻；MalGAN/IDSGAN 需要明确标成 surrogate-learning，而不是 actual defender co-learning。citeturn24view0turn27view6turn21academia3turn23academia37

**第二，DGA adversarial training 本身早已不是空白。** Drichel 2024 对 32 种攻击、多攻击 hardening 和 unknown-attack evaluation 已构成很强先占，因此 P4 必须讲 adaptive opponent / training dynamics，而非泛泛讲“增加对抗样本提高鲁棒性”。citeturn22view0

**第三，单步攻击不需要为了 MARL 名称而人为造长序列。** MAB-Malware 提供了直接 security precedent；\(H=1\) contextual-bandit/repeated-game 形式与当前动作定义更匹配。citeturn25academia2

**第四，group-relative advantage 与 MADDPG centralized critic 是实质不同的 credit mechanism。** 前者以同 context 实测 reward 做 critic-free control variate，后者训练 joint-action \(Q\) critic；在 \(H=1\) 情况下，这一区别尤其清楚。citeturn18view0turn26search0

**第五，不能再把“multi-agent GRPO”本身作为创新主张。** 2025–2026 已出现 MAPGRPO、M²GRPO、Graph-GRPO 等不同形态；可以研究的仍是安全问题中的具体 game formulation 和稳定化机制。citeturn25academia3turn27academia0turn27academia6

### 仍然存在的关键不确定性

最重要的未回答问题是**DGA 场景中 adaptive learned attacker 是否在等 perturbation budget、等 validity constraints、等 detector information 下稳定胜过 CharBot/MaskDGA**。本轮检索没有找到足以替代本地实验的 apples-to-apples 证据；因此这是 P4 前必须直接证伪的资格问题，而不是一个可由 related work 解决的问题。citeturn21academia1turn21academia2turn25academia2

第二，交接包中的 P3 “组相对加权”究竟保留多少 GRPO 原机制，会直接影响论文措辞。若只将 relative score 用作 defender sample weight，就不能称其为 GRPO；若 P4 attacker 使用 group-normalized reward 但没有 clipped importance ratio/reference policy，也应称为 GRPO-style 而不是未经限定的 GRPO。citeturn26search0

第三，P4 的 defender 若继续用 supervised BCE 而非 RL policy gradient，则学术上建议称作 **adversarial two-player co-learning / RL-attacker adversarial training**，而不要仅凭“两边都更新”称为标准 MARL。若以后确实需要“MARL 形态”作为章级定义，本地应先明确 detector 的 action space、policy 与 reward；否则 MADDPG 等 MARL 近邻在 reviewer 眼里会与实际优化对象不匹配。citeturn18view0

第四，2026 的 malware bilevel co-evolution 与多智能体 GRPO 工作都很新，部分仍是预印本；它们适合作为**创新边界预警**，但不能和 ASIA CCS、NeurIPS、ICML、IEEE S&P 等已正式发表成熟方法给予同等证据权重。citeturn27view6turn25academia3turn27academia0

**综合外部候选排序因此为：P3 过门后，先做“冻结 detector 上 learned attacker 是否真的超过固定攻击器”的最小资格实验；若通过，再做 frozen learned-attacker pool / PSRO-lite 的 P3.5；只有 P3.5 仍留下稳定 adaptive residual，才投入 windowed alternating P4。** 这一顺序把攻击分布增益、人口多样性增益和真正共演化增益逐级分离，也与 MAB-Malware、MADDPG policy ensembles、PSRO 和最新 malware co-evolution 文献形成清晰证据链。所有步骤均应只在获准的源期数据与冻结协议内完成，T20–T25 不承担设计、选择、调参或早停作用。citeturn25academia2turn18view0turn17academia0turn27view6