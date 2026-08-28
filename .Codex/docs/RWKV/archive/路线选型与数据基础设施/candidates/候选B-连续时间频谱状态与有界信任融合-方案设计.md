# 候选 B：连续时间频谱状态与有界信任融合——方案设计

- **状态**：未筛选，全部效果主张待实验
- **主任务**：`LSPR23→LSPR24` 的 2-IP 因果流序列
- **接收基座**：因果 Transformer；RWKV-7 状态作为可移植旁路
- **机制组成**：M1 连续时间广义 Delta 状态；M2 因果频谱证据的有界信任融合

## 1. 问题

固定“每一步”衰减把相邻流默认成等时间间隔，但 2-IP 序列的实际流间隔高度不规则，且不同年度的业务密度可能变化。相同 128 步可能表示数秒或数小时，固定步长状态会把时间密度变化误当成行为变化。

另一方面，包到达间隔在 Leoste（2025）的跨年基线中改变了精确率—召回率权衡，说明节律信息可能有用；但频谱支路也可能在稀疏、缺失或非周期序列上制造伪证据。候选分别处理“状态按真实时间如何遗忘”和“何时相信频谱校正”。

## 2. 文献证据与边界

1. RWKV-7 提供动态矩阵状态，但原式按离散 token 更新；连续时间改造是本课题原创候选。
2. FRWKV 在频谱轴使用 RWKV-7 式状态；其消融只证明频域分支在若干预测数据上可训练且有增量，不证明网络攻击检测有效。
3. FRWKV+ 的信任门、零初始化和 `0.20` 幅度上限为保守校正提供结构先例。
4. Dijk 等（2026）的 2-IP 以真实开始时间排序并形成最长 128 流，为不规则时间建模提供合法载体。
5. Leoste（2025）观察到包到达间隔会显著改变跨年结果；该证据只说明时间字段值得保留，不能证明频谱模型更好。

## 3. M1：连续时间广义 Delta 状态

令相邻流开始时间差为 (Delta t_t\ge0)。由当前表示产生非负衰减率：

\[
\boldsymbol\lambda_t=\operatorname{softplus}(W_\lambda\mathbf h_t+b_\lambda),
\qquad
D_t=\operatorname{Diag}\left(\exp(-\Delta t_t\boldsymbol\lambda_t)\right).
\]

令 (hat{\mathbf k}_t=\mathbf k_t/max(\|\mathbf k_t\|_2,\varepsilon))，移除率 (a_t\in[0,1])，写入率 (\beta_t\in[0,1])：

\[
R_t=I-a_t\hat{\mathbf k}_t\hat{\mathbf k}_t^\top,
\qquad
\mathbf S_t=\mathbf S_{t-1}D_tR_t+
\beta_t\mathbf v_t\tilde{\mathbf k}_t^\top.
\]

状态读出为：

\[
\mathbf r_t=W_r\operatorname{vec}(\mathbf S_t)+U_r\mathbf h_t.
\]

这不是把 RWKV-7 原式简单改名：新增的 (Delta t_t) 进入半群衰减，且移除矩阵被限制为非扩张形式，以便建立时间网格细化性质。

## 4. M2：因果频谱证据的有界信任融合

只对当前时刻以前的滚动窗口 (X_{t-H+1:t}) 做实数快速傅里叶变换；禁止用居中窗口或未来补齐：

\[
F_t=\operatorname{rFFT}(W_fX_{t-H+1:t}),
\qquad
F_t=F_t^{\Re}+iF_t^{\Im}.
\]

实部、虚部分支各自生成校正：

\[
\delta_t=\tanh\!\left(W_\delta[phi_\Re(F_t^{\Re});\phi_\Im(F_t^{\Im})]\right).
\]

谱集中度、缺失率与时间抖动共同产生信任：

\[
c_t=\frac{\sum_{k\in\operatorname{TopK}}|F_{t,k}|^2}
{\sum_k|F_{t,k}|^2+\varepsilon},
\qquad
q_t=\sigma(b_q+\eta_c c_t-\eta_m m_t-\eta_j j_t).
\]

频谱支路只作有界残差：

\[
\tilde{\mathbf r}_t=\mathbf r_t+
\bar\gamma q_t\delta_t,
\qquad 0\le\bar\gamma\le0.20,
\]

且 (W_\delta) 末层与 (\bar\gamma) 零初始化。M1 解决时间尺度，M2 解决周期／重复频率证据的选择性注入，两者可独立消融。

## 5. 目标与算法 1

\[
\mathcal L=\mathcal L_{\rm cls}
+\lambda_{\rm rate}\|\boldsymbol\lambda_t\|_1
+\lambda_{\rm ref}\mathcal L_{\rm refine}
+\lambda_{\rm spec}\mathcal L_{\rm specmbox{-}con}
+\lambda_{\rm gate}\mathcal L_{\rm gate}.
\]

(mathcal L_{\rm refine}) 比较同一时间段原序列与合法细分序列的终态；细分只能在 LSPR23 训练区依据已观察流生成，不插入目标年度信息。

**算法 1：连续时间状态与因果频谱联合训练**

1. 从冻结 2-IP 清单读取流序列和真实 (Delta t)，只用 LSPR23 拟合单位、缩放和截断上限。
2. 逐步更新 (D_t,R_t,S_t)，得到连续时间状态读出。
3. 从当前因果前缀构造频谱，计算集中度、缺失率、抖动与信任门。
4. 通过零初始化有界残差融合两支，计算分类和一致性目标。
5. 只在 LSPR23 源验证区选择 (H)、TopK、阈值与早停点。
6. 冻结后一次评价 LSPR24 可见开发区，不进行目标标签适配。

## 6. 核心公式族与工作量

| 公式族 | 数量 | 内容 |
| --- | ---: | --- |
| 连续时间问题定义 | 4 | 时间戳、间隔、强度、源／目标风险 |
| M1 衰减与状态 | 8 | 速率、半群衰减、移除、写入、读出 |
| M2 因果频谱 | 7 | 滚动窗、rFFT、双分支、集中度、信任、融合 |
| 损失与校准 | 5 | 分类、细化、谱一致、门正则、阈值 |
| 性质与复杂度 | 6 | 非扩张、状态界、细化不变、残差界、复杂度 |
| **合计** | **30** | 目标范围 29—33 |

预计 **29—33 页、10 幅图、8 张表、1 个算法**。页面分配：问题与数据 4 页；M1 7 页；M2 6 页；理论 5 页；实验 7—10 页。图包括时间密度示意、半群衰减、频谱支路、信任门、四格消融、密度分面、谱分面、效率与失败案例。表包括文献、字段、参数、主结果、消融、置换诊断、困难分面、效率。

## 7. 证明义务

**引理 1（单步非扩张）**：若 (Delta t_t\ge0)、(lambda_{t,j}\ge0)、(a_t\in[0,1])、(|\hat k_t\|_2=1)，则 (|D_tR_t|_2\le1)。证明须处理 (D_t) 与 (R_t) 不可交换的情况，不能直接相乘特征值。

**命题 1（有限写入下状态有界）**：若 (|\beta_t v_t\tilde k_t^\top|_F\le B_t)，则 (|S_T|_F\le|S_0|_F+\sum_{t=1}^{T}B_t)。若再有统一收缩率 (\rho<1)，给出几何级数上界。

**命题 2（时间网格细化一致性）**：在一段区间内 (lambda) 固定、没有移除和写入时，把 (Delta t) 拆为 (Delta t_1+Delta t_2) 不改变终态，因为 (exp(-\lambda\Delta t_1)\exp(-\lambda\Delta t_2)=\exp[-\lambda(\Delta t_1+\Delta t_2)])。含写入时只给出误差界，不伪造完全不变性。

**命题 3（有界频谱扰动）**：若读出头为 (L_f)-Lipschitz，则频谱支路引起的 logit 改变量不超过 (0.20L_fsqrt d)。必须说明 `tanh` 是逐元素上界。

## 8. 风险

1. LSPR 流序列可能没有稳定周期，频谱支路退化为噪声。
2. 5 秒窗口主视图是规则采样，M1 的不规则时间优势只在流级 2-IP 序列成立；不得混淆两种输入。
3. 连续时间衰减可能只重参数化普通门控，不产生可辨识新行为。
4. rFFT 的滚动开销可能抵消线性状态效率；必须实测吞吐。
5. 与登记册 C6 有机制重合；本候选的新增价值只在“连续时间状态 + 可信频谱”的双机制组合，单独 M1 不能包装为新章。

## 9. 来源

- `wiki/papers/rwkv/2025-Peng-RWKV7-Goose.md`
- `wiki/papers/rwkv/2025-Yang-FRWKV-频域线性注意力长期预测.md`
- `wiki/papers/rwkv/2026-Yang-FRWKV-Plus-信任门控周期校正.md`
- `wiki/papers/datasets/LSPR24/Dijk-2026-LSPR23到LSPR25序列构造跨年评估.md`
- `wiki/papers/datasets/LSPR24/Leoste-2025-LSPR23到LSPR24跨年泛化.md`

