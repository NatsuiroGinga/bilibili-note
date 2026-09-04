# 第四章机制一 EAS：研究问题卡与家族谱系

**状态：待验证方案的研究契约。** 本文件不是结论，是把 EAS 从「一个想法」固化成
「可机械判定的研究问题」的合同。**不得据本文件宣称任何机制已确立。**

- 路线：RWKV 第四章（训练效率）
- 配套审核：[2026-09-04 EAS 方案对抗性审核](../../.Codex/docs/RWKV/2026-09-04-EAS方案对抗性审核.md)
- 被审方案：[第四章机制一-EAS空活动集短路](第四章机制一-EAS空活动集短路.md)
- 家族谱系详表：[第四章机制一-EAS家族谱系](第四章机制一-EAS家族谱系.md)

---

## 零、数据接触声明（**先读这一节**）

仓库规则要求：判据必须能在看到数据前冻结，且必须声明已看过哪些数据。
**本卡是在已经看过下列数据之后写的**，因此下面的判据分成两类，不得混用。

### 0.1 已看过的数据（完整清单）

| 数据 | 来源 | 看到了什么 |
| --- | --- | --- |
| `ch3-ft-c01-entitybce-halfwidth-screening-v1` 第 `1`–`10` 轮 `entity-ranking-diagnostics-*.json` | 服务器收据 | `empty_active_step_frac`、六档活动率、五段计时、`gradient_control` 全部字段 |
| 同运行 `mechanism-coupling-8.json` | 服务器收据 | `cv_xi`、`active_set_size` |
| 同运行 `config.json`、`status.json`、`environment-receipt.json`、`split.json` | 服务器收据 | 冻结超参、精度 profile、切分规模 |
| 十份轮末收据的落盘时刻 | 服务器 `ls` | 整轮墙钟 `451.66` 秒 |
| 全 `E23` 的实体袋长分布 | 服务器 CPU 只读统计 | 正/负实体池规模与片段数分布 |
| `cvar_pauc_loss` 在合成空活动集输入下的梯度 | 本地合成输入公式核验（CPU） | `∂L/∂θ = 0`、`∂L/∂ξ = 1/12` |

**未看过**：任何 EAS 实现的运行结果（尚不存在）；`Ŝ_n` 的实际刷新耗时；
基线重跑的逐位一致性；`C11` 的 `empty_active_step_frac`（第四章耦合预注册另行冻结，本卡不动）。

### 0.2 判据的两类划分（**这是本卡最重要的结构**）

- **A 类（已污染，只作描述，不得再当预注册判据）**：任何关于
  `empty_active_step_frac`、五段计时、活动率、袋长分布的判据。
  这些量本卡作者已经看过，用它们「验证」由它们提出的假设是循环论证。
  **A 类判据在本卡中一律标注为「已见」，其取值只用来估计收益量级，不用来裁决机制存废。**
- **B 类（真正冻结）**：只涉及**尚不存在的观测量**的判据。
  这些量在本卡写下时无人见过，故可作为预注册判据。B 类共三条，见第三节。

---

## 一、Research Question Card

```
Question:
  在 BER（六档 CVaR-pAUC 实体排序损失）的训练中，能否用一个可靠（sound）的充分条件，
  在付出计算之前判定「本步不存在违序对」，从而精确地跳过该步的排序分支，
  且不改变训练轨迹？

Type: confirmatory（机制已提出，问的是它是否成立，不是有没有机制）

Hypothesis:
  H1（弱式，EAS-lite）：存在一个在完整前向之后可 O(1) 判定的条件 C_lite，
     满足 C_lite ⟹ 排序损失对全部可训练状态的更新可由闭式给出，
     从而跳过反传后训练轨迹逐位不变。
  H2（强式，EAS-full）：存在一个在完整前向之**前**可判定的充分条件 C_full，
     其判定代价显著小于被它省下的计算，从而端到端净收益为正。

Why it matters:
  第四章的主题是训练效率，而 BER 是第三章引入的主要开销来源（排序阶段占整轮墙钟 58.05%，
  「已见」）。若 H2 成立，第四章机制一具备「可证明精确等价」的正确性论证强度，
  与参照论文第四章「收敛性/经验对照」的论证强度相比是升级而非同级；
  若只有 H1 成立，它是工程整改，不足以单独作为章级机制。

Current evidence:
  见第二节的 Evidence Record（ER-1 至 ER-6）。

Missing evidence:
  M1  基线自身是否逐位可复现（无确定性设置，bf16 autocast，从未验证）
  M2  Ŝ_n 全量刷新的实测耗时 T_refresh
  M3  闭式 ξ 补偿能否与 autograd 逐位一致
  M4  EAS 实现后的实际端到端墙钟
  M5  空活动集在超过 10 轮后的走向（第 8 轮见顶、第 9–10 轮回落，外推无依据）

What would support it:  见第三节 B 类判据的「支持」列
What would falsify it:  见第三节 B 类判据的「证伪」列

Minimal next action:
  执行 B3（一次前向计时，测 T_refresh）。
  理由：它是三条 B 类判据中成本最低（分钟级、单次前向、零训练）而信息量最大的一条——
  它单独就能决定 H2 的生死，且不依赖任何 EAS 实现。
  **不要先做 ε(Δθ) 的松弛量分析**：那是 H2 的第二个失败原因，
  在第一个失败原因未排除前投入是浪费。

Decision: run experiment（先跑 B3；B3 证伪则 H2 出局，只保留 H1 走 B1→B2）
```

---

## 二、Evidence Record

### ER-20260904-eas-empty-01

```
Evidence ID: ER-20260904-eas-empty-01
Source: runs/diagnostics/ch3-ft-c01-entitybce-halfwidth-screening-v1/receipts/
        entity-ranking-diagnostics-{1..10}.json
Source type: experiment artifact
Supports: 空活动集在训练中确实大量出现（十轮 0.000 → 0.395 → 0.272）
Contradicts: 被审方案 §1.1「随训练单调增强」——第 8 轮见顶后连续两轮回落
Method / dataset / metric: LSPR23 源区训练，C01 臂（只开 BER），每轮 1000 步；
        empty_active_step_frac = 生效袋处置下六档活动率全为 0.0 的步数占比
Limitation: screening_only 运行级别，半宽模型；只有 10 轮；单种子
Project relevance: EAS 的动机量，也是其收益的唯一来源
Claim strength: supported
```

### ER-20260904-eas-zerograd-02

```
Evidence ID: ER-20260904-eas-zerograd-02
Source: 合成输入公式核验（CPU 单线程，CUDA 硬隔离），
        调用 tools/ch3_ft_entity_ranking_loss.py 的 cvar_pauc_loss
Source type: experiment artifact
Supports: 活动集为空时 ∂L/∂θ 精确为 0（max|grad| = 0.000e+00）
Contradicts: 被审方案 §2.1「跳过等价于加零、逐位精确」——
        同一核验测得 ∂L/∂ξ = 0.0833333358（= FP32 的 1/12），**非零**
Method / dataset / metric: N_p=2、N_n=64、六档 K_eff 取冻结实测值、
        构造 pairwise ≈ 0 ≤ ξ；解析真值 1/(N_p·|K|)；偏差 0.000e+00
Limitation: 合成输入，只验证公式实现，不验证真实数据上的分布
Project relevance: 同时是 EAS 地基的确认与其「逐位精确」主张的证伪
Claim strength: strong（解析真值与实测偏差为 0）
```

### ER-20260904-eas-xidynamics-03

```
Evidence ID: ER-20260904-eas-xidynamics-03
Source: 同 ER-02 的对照分支 + mechanism-coupling-8.json 的 cv_xi
Source type: experiment artifact
Supports: ξ 是 bang-bang 分位数追踪器——空步 ∂L/∂ξ = +0.0833，
        全活动步最低档 ∂L/∂ξ = −83.48，不对称度 1002×；
        cv_xi ≈ 0.906–1.016（六档，各 2000 样本）指示 ξ 高度波动
Contradicts: 被审方案 §1「模型排序学得越好 ⟹ A 越小」的因果叙事
Method / dataset / metric: 同 ER-02；cv_xi 出自轮末机制耦合收据
Limitation: cv_xi 只有第 8 轮一个轮次被读取
Project relevance: 决定 EAS-lite 是否会切断把系统拉出空活动集的负反馈
Claim strength: supported
```

### ER-20260904-eas-bagsize-04

```
Evidence ID: ER-20260904-eas-bagsize-04
Source: 服务器 CPU 只读统计，全 E23（271,815 片段 / 150,680 实体）
Source type: experiment artifact
Supports: 正实体池 239 个、片段数均值 54.498（截断后 6.126）；
        负实体池 150,441 个、片段数均值 1.720（截断后 1.211）
Contradicts: 被审方案 §3.2「正例前向约占 2/66 ≈ 3%」——
        期望份额实为 13.65%（低估 4.50 倍），最坏 62.28%
Method / dataset / metric: 截断参数取宿主实际 max_segments = ceil(8192/128) = 64；
        份额 = 2·E[cap(pos)] / (2·E[cap(pos)] + 64·E[cap(neg)])
Limitation: 全 E23 口径，训练区是其子集；未按运行的实际切分重放采样器
Project relevance: 决定 EAS-full 证书的自身代价，以及 Ŝ_n 刷新费的分母
Claim strength: supported
```

### ER-20260904-eas-wallclock-05

```
Evidence ID: ER-20260904-eas-wallclock-05
Source: 十份轮末收据的落盘时刻（ls --time-style=full-iso）+ stage_timing_seconds
Source type: experiment artifact
Supports: 整轮墙钟 451.66 秒（九个间隔，极差 4.9 秒）；
        排序五段合计 262.18 秒（58.05%）；前向+主反传 249.85 秒（55.32%）；
        第 1 轮（0% 空步）与第 8 轮（39.5% 空步）的两段耗时只差 1.3%
        ⟹ 空步当前按满价计算，无隐式短路
Contradicts: 被审方案 §7.1「分母尚未测，不得报告端到端加速比」
Method / dataset / metric: CUDA event 计时，轮末统一 resolve，训练步内无设备同步
Limitation: 收据落盘间隔含评价与检查点时间，是端到端口径而非纯训练口径
Project relevance: EAS 收益的分母；也证明收益尚未被现有实现吃掉
Claim strength: supported
```

### ER-20260904-schultheis-06

```
Evidence ID: ER-20260904-schultheis-06
Source: raw/papers/methodology/training-efficiency/
        2023-Schultheis-Implicit-Negative-Mining-Sparse-XMC-arXiv.pdf
        （arXiv:2306.03725，DOI 10.1007/978-3-031-43418-1_41，题录已在 arXiv 页核验）
Source type: full paper
Supports: 深度学习框架下「利用损失的精确零梯度跳过反传」已有先例；
        §3.3 平方合页损失在 yŷ ≥ 1 时导数精确为零；§4.4 每轮时间降约三分之一
Contradicts: 「首次在深度网络里做可证明精确的反传剔除」这一主张
Method / dataset / metric: XMC，稀疏最后一层 + 中间层，自定义 CUDA；SQH vs BCE 对照
Limitation: **实验设定为固定预训练特征之上的分类层**，端到端训练是其未来工作；
        故它不是端到端深度网络的先例（被审方案 §6 在这一点上把先例说强了）
Project relevance: 决定新颖性主张的收窄边界
Claim strength: strong（本地全文，节号与原文逐字核对）
```

---

## 三、判据（B 类，真正冻结）

**下列三条只涉及本卡写下时尚不存在的观测量，故可作预注册判据。
门槛在看到任何相关结果前冻结，事后不得调整。**

| # | 判据 | 观测量 | 支持 | 证伪 | 成本 |
| --- | --- | --- | --- | --- | --- |
| **B1** | 基线逐位可复现 | 同配置同种子重跑 `2` 轮，与既有收据比对 `empty_active_step_frac`、`pair_loss_batch_mean`、`pair_loss_batch_var`、`c_scaling_median` | 四项全部 `==` 为真 | 任一为假 ⟹ 「逐位相等」不可达，H1 的验收判据须整体改写为容差式，容差由本次差异量级给出 | `2` 轮 GPU ≈ `15` 分钟，须排在第三章四臂链之后 |
| **B2** | 闭式 `ξ` 补偿的逐位一致性 | 实现 `ξ ← ξ − lr/(N_p·\|K\|)` 后，在空步上与 autograd 路径对拍 | 补偿值逐位命中 `0.0833333358`（FP32 的 `1/12`，ER-02 已给出目标值），且整轮指标与 B1 建立的口径一致 | 补偿值不逐位一致 ⟹ H1 只能以容差式成立，「精确等价」的论证强度降级 | 实现后单步对拍，分钟级 |
| **B3** | `Ŝ_n` 维护费 | 一次全量刷新的实测耗时 `T_refresh`（只前向、不反传、不更新） | `T_refresh < 40` 秒 | `T_refresh > 92.9` 秒 ⟹ **H2 出局**，`§3.2` 整节删除，EAS 只保留 lite 档 | 单次前向，分钟级 |

**B3 的门槛来源（可追溯，非拍脑袋）**：`92.9` 秒是 EAS-full 在**最好的一轮**（第 8 轮，
`empty_frac = 0.395`）能省下的全部时间，按「省下负例前向的 `86.35%` 加全部主反传」计得
`0.395 × (0.8635 × 102.303 + 146.732) = 92.9`。刷新费超过它即必然亏本。
`40` 秒是留 `2.3×` 余量后的支持门槛。**两个门槛都只依赖已见数据（A 类）算出，
但被判定的量 `T_refresh` 从未被观测，故判据本身是 B 类。**

**中间带（`40 ≤ T_refresh ≤ 92.9`）的归属**：**归证伪**。
理由：该区间意味着刷新费吃掉一半以上收益，而这还没算 `ε(Δθ)` 的松弛成本与漏判损失，
留着只会制造第二轮争论。**此项现在写死，不得事后解释为「有待进一步优化」。**

### 3.1 A 类（已见，只作量级估计，不得裁决存废）

- 空活动集占比：十轮 `0.000 / 0.003 / 0.056 / 0.133 / 0.176 / 0.230 / 0.347 / 0.395 / 0.354 / 0.272`
- EAS-lite 收益上限：`1.068×`（十轮加权）
- EAS-full 收益上限：`1.114×`（十轮加权，已扣除必付的正例前向）
- 删除整个排序阶段的硬上限：`2.384×`

**这四个数只用于回答「值不值得做」，不用于回答「机制成不成立」。**

---

## 四、Claim Candidate

### CC-1 空活动集的存在性

```
Claim: BER 训练中存在相当比例的步，其排序损失对模型参数的梯度精确为零。
Source evidence: ER-20260904-eas-empty-01, ER-20260904-eas-zerograd-02
Allowed wording: 「在本文的筛选运行中，第 8 轮有 39.5% 的步上六档活动率全部为零，
                该条件下排序损失对共享参数的梯度精确为零。」
Forbidden stronger wording: 「随训练单调增强」「训练后期大部分步为空」
                「模型排序学好后活动集自然清空」
Uncertainty: 单种子、screening_only、10 轮；第 8 轮见顶后回落
Next check: 更多轮次或第二种子下的 empty_frac 曲线
Decision: keep（措辞按 Allowed 收窄）
```

### CC-2 空活动集的成因

```
Claim: 空活动集是 ξ 阈值追踪器高于 L_pn 分布的暂态，不是模型收敛的稳态。
Source evidence: ER-20260904-eas-xidynamics-03
Allowed wording: 「空活动集对应 ξ 高于当前配对损失分布的区间；
                ξ 在该区间以每步 1/(N_p·|K|) 的速率衰减，
                并在重新出现活动对时以约 1/K_eff 的幅度回升。」
Forbidden stronger wording: 「模型学好了所以没有违序对」
                「空活动集是收敛的标志」
Uncertainty: bang-bang 图像由公式与合成核验得出，未在真实训练中逐步记录 ξ 轨迹
Next check: 在既有诊断中增记 ξ 的轮内均值与极差（零额外计算，只是多写两个标量）
Decision: keep
```

### CC-3 家族归属

```
Claim: EAS 属于安全筛除（safe screening）家族。
Source evidence: 见家族谱系文件的 Ogawa、Ghaoui 条目；ER-20260904-schultheis-06
Allowed wording: 「本机制与安全筛除家族共享『可靠但不完备的充分条件』这一分工：
                判定为可跳过时必须真的可跳过，漏判只损失收益不损害正确性。」
Forbidden stronger wording: 「与 Ogawa 的安全样本筛选同构」
                「首次在深度网络里做可证明精确的反传剔除」
Uncertainty: 凸问题的可行域来自对偶间隙，本机制只能来自参数移动量的信赖域，
             两者的构造不同源
Next check: 家族谱系中是否已有针对成对/排序损失的安全筛除工作（若有，新颖性主张不成立）
Decision: weaken（把「同构」降为「共享可靠性—完备性分工」）
```

---

## 五、家族谱系

完整谱系、逐条题录与证据等级见配套文件
[第四章机制一-EAS家族谱系](第四章机制一-EAS家族谱系.md)。本节只记录**定位结论**：

| 分支 | 代表工作 | 筛掉什么 | 是否可证明精确 | 与 EAS 的关系 |
| --- | --- | --- | --- | --- |
| 凸问题安全筛除 | Ghaoui 等（LASSO 特征筛除）、Ogawa 等（SVM 样本筛选，`arXiv:1401.6740`） | 特征／样本 | 是，靠对偶间隙 | **共享性质，不共享构造**——非凸问题无最优解可围 |
| 深度网络近似稀疏反传 | meProp、Selective Backprop | 梯度分量／样本 | 否，启发式 | EAS 相对它们的结构性优势正是「可靠性与收益解耦」 |
| 深度网络精确零梯度剔除 | Schultheis & Babbar（`arXiv:2306.03725`） | 逐点 margin 损失的零梯度项 | 是，靠损失的解析零 | **最近先例**。差别：其零来自逐点 margin、标签维度、固定特征之上的分类层；本机制的零来自成对 CVaR-pAUC、实体袋维度、端到端训练 |

**新颖性主张的许可边界**：可以说「把安全筛除的可靠性—完备性分工，
从凸问题与逐点损失推广到成对 CVaR-pAUC 排序损失的实体袋维度」。
**不可以说「首次」「首个」**，也不可以说「与 Ogawa 同构」。

---

## 六、最小下一步与成本

| 顺序 | 动作 | 成本 | 决定什么 |
| ---: | --- | --- | --- |
| 1 | 跑 **B3**（`T_refresh` 一次前向计时） | 分钟级，零训练 | H2（EAS-full）的生死。证伪则 `§3.2` 整节删除 |
| 2 | 关闭审核报告的 B1–B5 文档级阻断项 | 无算力成本 | 方案文档能否进入下一阶段 |
| 3 | 跑 **B1**（基线逐位可复现前测） | `2` 轮 GPU，须排队 | 验收判据 1 的形式（精确 vs 容差） |
| 4 | 实现 EAS-lite + 闭式 `ξ` 补偿，跑 **B2** | 实现 + `10` 轮 GPU | H1 是否成立 |

**顺序不可颠倒的理由**：1 比 4 便宜三个数量级却决定更大的事；
3 必须在 4 之前，否则 4 的结果无法判读。

**HARD-GATE 说明**：本卡属设计与研究契约，**未通过 B1–B3 前不得进入 `writing-plans`，
不得开始实现**。本卡由子代理产出，子代理无权代替用户批准；
批准与否由主代理与用户裁决。
