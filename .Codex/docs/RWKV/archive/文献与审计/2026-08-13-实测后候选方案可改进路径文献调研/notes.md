# RWKV 官方仓库机制盘点 + 实测后候选路径文献调研 — 工作笔记

- 任务开始：2026-08-13
- 主代理：本文件只记录**主代理亲自核验**的内容；三个子代理的结果单独汇总。
- 铁律：所有机制作用必须引官方原文或源码行号，禁止臆想；无证据一律标"未知"。

## 0. 本次调研绑定的实测事实（用户提供，禁止修改）

LSPR23（16,353,511 流，π=0.1005655006）训练 → LSPR24（20,227,356 流，π=0.0257073138）零样本，83 字段，逐流 AP。

| 档 | 模型 | 跨年度 AP |
| --- | --- | ---: |
| A | 逐流 MLP | 0.1590128242（AUC 0.8501） |
| B | A + 2-IP 序列 + 因果前缀均值上下文 | **0.2878764332**（AUC 0.9462） |
| C | B 的上下文换成 RWKV-7 状态递归 | 运行中 |
| — | XGBoost 全量 83 字段（复现 Dijk 配置） | 0.2244424863 |

B 档实现：`cum=cumsum(h); ctx=cum/cumsum(mask); out=Linear([h,ctx])`，无注意力/循环/门控。

对比 Dijk 2026 表 5（印刷 p.30）LSPR23→24：XGB 0.2416、GRU(SesH) 0.1758、Transformer(2-H) 0.0742。
本课题候选 B 早期 RWKV 状态递归：对照 0.0192059594、创新 0.0101230212。

**核心疑问**：序列轴有用，但复杂状态递归远不如最简前缀均值。

## 1. 仓库身份

- 远程 `https://github.com/BlinkDL/RWKV-LM`，本次读取的是 `main` 当前状态（未固定到冻结提交 `952102498e9ed367ea0a59ee64106916d474d30f`）。
- 冻结文档 `.Codex/docs/RWKV/2026-08-05-RWKV7官方实现锁定与公式代码映射.md` 记录的是 2026-08-05 状态。**本次盘点发现 main 已有该文档未记录的内容**（见第 3 节）。

## 2. 已核验的官方文件（主代理亲自读取）

| 文件 | 状态 |
| --- | --- |
| 仓库完整文件清单（`path=/`） | 已核验 |
| `README.md`（61209 B，1094 行） | 已核验（全文抽取到 /tmp/rwkv_readme.txt） |
| `RWKV-8.md`（3250 B） | 已核验全文 |
| `RWKV-v8/README.md` | 已核验全文 |
| `RWKV-v8/251014_rosa_1bit_layer.py` | 已核验全文 |
| `Research/rwkv7-g0-7.2b.md` | 已核验全文 |
| `RWKV-v7/README.md` | 已核验全文 |
| `RWKV-v7/train_temp/README.md` | 已核验全文 |

## 3. 冻结文档未记录 / 本次新发现（重点）

### 3.1 `RWKV-v8/` 整个目录存在（冻结文档只提到 `RWKV-8.md` 与 `RWKV-v7/rwkv_v8_rc00_*demo.py`）

文件（含日期前缀，251014=2025-10-14 → 260222=2026-02-22）：
```
251014_rosa_1bit_layer.py   251014_rosa_1bit_train.py   251014_rosa_onlyemb_train.py
251016_rosa_1bit_run.py/.pth   251018_rosa_4bit_run.py/.pth
251024_rosaQKV_run.py   251024_rosaQKV_L2_digit20.pth   251024_rosaQKV_L4_digit40.pth
251105_reverse_run.py   251105_reverse_L2.pth
260123_reverse_L2.pth   260123_reverse_L2_only_rwkv7.pth
260212_rosa1bitLM_L12.py   260222_rosa4bitLM_L12.py
README.md   cuda/wkv7_cuda.cu   cuda/wkv7_op.cpp
```

### 3.2 ROSA 机制实体（官方源码已核验）

`RWKV-v8/README.md` 标题原文：`# RWKV-8 "Heron" with ROSA (Rapid Online Suffix Automaton)`

`251014_rosa_1bit_layer.py` 实现（已读全文）：
- `bits = (x>0)`，**对每个 (batch, channel) 独立**把激活二值化成 bit 序列；
- 函数 `rosa(x)` 在线构建后缀自动机（标准 SAM：`b`=转移表、`c`=suffix link、`d`=len、`e`=endpos）；
- 每步输出 `a = x[e[v]+1]`，即"历史上最长匹配后缀之后出现过的那个 bit"；无匹配输出 -1；
- 输出为 `emb0/emb1` 查表（idx=-1 时输出 0）。参数只有 `emb0`、`emb1` 两个 `[1,1,C]` 向量。
- 类注释两处标注 `# !!! extremely slow !!!`（前向后向都是纯 Python 双重循环 + 逐位翻转求梯度）。

官方自述能力（`RWKV-v8/README.md` 原文）：
- `260212_rosa1bitLM_L12.py - pure ROSA1bit + FFN (no RWKV)`，minipile 1.5B tokens 训练，"can already copy & count"；
- `251105_reverse_run.py - RWKV7+ROSA with 40K params (L2-D32) reversing 1-60 digits input with 99.8% ... digit accuracy`；
- `251024_rosaQKV_run.py for arithmetic demo (1M params can solve 40 digits plus/minus with 99% digit accuracy, without CoT)`。

**性质判定**：ROSA 是对序列自身历史做**精确后缀匹配的非参数检索**，官方展示的能力全部是 copy / count / reverse / 算术，即**精确记忆与复制**类任务。
**对跨年度分布漂移的相关性：未知**（官方无任何相关陈述，且精确匹配机制在跨年度上是否退化没有任何已发表或官方证据）。需要序列轴：**是**。

社区 ROSA 实现（`RWKV-v8/README.md` 列出，**非官方**）：
`wjie98/rosa_soft`、`johanwind/wind_rosa`、`zyaaa-ux/ROSA-Tuning`、`bcml-ai/rosa-plus`、`x-0D/RASP`。

### 3.3 `RWKV-v7/rwkv_v7a_demo.py`、`rwkv_v7b_demo.py`（冻结文档未提及的 v7 变体）—— 已核验

- **v7a**：参数名与标准 RWKV-7 **完全一致**（`x_r,x_w,x_k,x_v,x_a,x_g, w0/w1/w2, a0/a1/a2, v0/v1/v2, g1/g2, k_k, k_a, r_k`）。
  状态更新原文：`state = state * w.view(H,1,N) + state @ ab.float() + vk.float()`，其中 `vk = v@k`、`ab = (-kk_)@(kk_*a_)`。
  **判定：实现变体（GPT 模式 + RNN 模式），非新机制。**
- **v7b**：标准参数全部保留，但**额外含 `k_emb.weight`、`v_emb.weight`、`k_emb_x`、`v_emb_x`**，以及"embedding residual merging operations"。文件头注明 "This version is GPT-mode + RNN-mode, and a bit more difficult to understand"。
  **判定：含标准 RWKV-7 之外的逐 token 嵌入矩阵。是否即作者在 X 上公布的 DeepEmbed，尚未由官方文字确认**（子代理正在核 X 原文）。
  **对本课题的关键限制**：`k_emb`/`v_emb` 是按**离散 token 索引**查表的嵌入矩阵；本课题输入为连续流特征、无词表。除非先离散化，否则不可直接搬运。（此为接口事实，非效果推测。）

### 3.4 官方推荐的核已更新，冻结文档锁定的 `rwkv7_clampw` 可能已非最新
`RWKV-v7/train_temp/README.md` 原文推荐升级为：
```
rwkv7_clampw_v3 (try rwkv7_clampw_v3_for_h100 and rwkv7_clampw_v3_for_h100_alt too)
rwkv7_cmix_bf16_v5, rwkv7_tmix_mix6_bf16_v5, rwkv7_tmix_kk_pre_bf16_v5,
rwkv7_tmix_lnx_rkvres_xg_bf16_v1, rwkv7_tmix_a_gate_bf16,
rwkv7_tmix_vres_gate_bf16_v1, rwkv7_l2wrap_ce_bf16_v2
```
冻结文档第 2.3 节把 `rwkv7_clampw.cu` 记为"正式 BF16 WKV 前后向核"。**README 明确建议用 `_v3`。**

另存在 `rwkv7_clampw128_v2.cu/.cpp` —— 冻结文档 §5.3/§9.5 称"融合核硬编码 N=64、头宽必须 64"，**128 头宽核的存在与该结论冲突，需复核**。

### 3.5 L2Wrap 损失核（冻结文档未记录）
`train_temp/cuda/rwkv7_l2wrap_ce_bf16_v2.cu/.cpp`、`rwkv7_head_l2wrap_ce_bf16_v4.cu/.cpp`。
train_temp/README 推荐清单含 `rwkv7_l2wrap_ce_bf16_v2`。作用待核（需读源码，不得凭印象）。

### 3.6 官方状态传递 / 状态调优核在**另一个仓库**（直接关系冻结文档未关闭的 P0）
`README.md` 原文：
> More RWKV-7 CUDA kernels (vanilla, **state-tuning, state-passing infctx**, simpler but slower than train_temp/cuda): https://github.com/BlinkDL/RWKV-CUDA/tree/main/rwkv7_fast_fused

冻结文档 §9.1 记的 P0 是"默认 train_temp 核不接受外部初始状态，状态传递接口尚未冻结"。
**该 README 行表明官方已提供 state-passing infctx 核，只是不在本仓库。** 已派子代理核实接口。

### 3.7 `RWKV-v7/cuda/wkv7s.cu`（`s` 疑为 state）、`RWKV-v5/cuda/wkv6state_cuda.cu`
存在专门的 state 核。待核。

### 3.8 作者公开但未写进论文的机制（`Research/rwkv7-g0-7.2b.md` 原文提到）
> 2. add DeepEmbed (https://x.com/BlinkDL_AI/status/1926941496684519805) and maybe DeepEmbedAttention (https://x.com/BlinkDL_AI/status/1939532655823040545)

已派子代理抓取。

## 4. 不依赖序列轴的机制（README 官方自述，已核验）

| 机制 | README 原文（节选） | 需要序列轴 |
| --- | --- | --- |
| PreLN LayerNorm（非 RMSNorm） | "Use PreLN LayerNorm (instead of RMSNorm) for RWKV. I think it's related to better initial state, because I am not using trainable initial state (found it useless when using LayerNorm)." | 否 |
| 只对大矩阵做 weight decay | "Only apply weight decay to large matrix parameters (basically projections) in your model instead of all parameters. THIS IS VERY IMPORTANT." | 否 |
| 正交初始化方案 | README "Initializing RWKV 5/6 Models" 节：`att.key.weight => orthogonal_(gain=0.1)`、`att.output.weight => zero`、`att.ln_x.weight => ((1+layer_id)/total_layers)**0.7` 等 | 否 |
| 小模型/小数据配方 | "When I train RWKV music models, I use deep & narrow (such as L29-D512) dimensions, and apply wd and dropout (such as wd=2 dropout=0.02). Note RWKV-LM dropout is very effective - use 1/4 of your usual value." | 否 |
| 训练尖峰修复 | "Fixing RWKV-6 Spikes"：`--adam_eps 1e-18`、`--beta2 0.95`、warmup `lr*(0.01+0.99*step/w_step)` + `--warmup_steps 20`、`--weight_decay 0.1`（配 lr_final=lr_init/100） | 否 |
| fp32 状态 | "In [state = kv + w * state] everything must be in fp32 because w can be very close to 1." | 状态相关 |
| state-tuning | "State-tuning (tuning the initial state. zero inference overhead)"，`--train_type "states" --load_partial 1 --lr_init 1 --lr_final 0.01 --warmup_steps 10 (yes, use very high LR)` | 是（状态） |

**注意**：`att.gate.weight`、`ffn.receptance.weight` 属 RWKV-5/6 初始化清单；RWKV-7 的权重/初始化以 train_temp/README 的 1.5B 表为准（已抄录在第 2 节读取的文件里）。

## 5. README 记录的"想法"（作者自述，非已验证机制，证据等级低）

- "Idea: Better Initial States"：① 生成所有 wiki 文档的最终状态；② 对用户问题检索最佳文档，用其最终状态作初始状态；③ 训练模型直接生成最优初始状态。
- "Some old ideas"：多成分衰减 `A^T+B^T+C = fast-decay + slow-decay + constant`；复数衰减（旋转）；可训练初始隐状态；layerwise/elementwise LR。
- Vision Tasks：2D 位置编码；**tokenShift of N tokens**（图像 N×N 时移位 N 个 token 相当于混合"上一行同列"），"You can use try different tokenShift styles for ATT & FFN, or mixing different tokenShift styles"。
  → 这是**无天然序列轴领域如何定义"上一步"**的官方做法，与本课题 2-IP 序列构造同类。
- RWKV-8.md 四大方向：Larger State（状态阶梯 scalar→vector→matrix→tensor→function）、Smaller State（sparse/structured/shared/compressed/low-rank/**quantized** state）、Mixed State（跨头/跨层混合状态）、Fancy State Evolution（`exp(sA)-1`、`1/(1-sA)`、DeltaProduct）。
  RWKV-8.md 原文自评：`### Conclusion: we have room for 100 architecture papers here.` —— **全部是方向草图，无公式、无实验、无论文**。

## 5.5 逐版本机制演化（README 官方自述，已核验）

| 版本 | 机制 | README 原文要点 | 需序列轴 |
| --- | --- | --- | --- |
| v1 | time-mix / channel-mix 交替 | `TM = sigmoid(R)·Σ_u W_{t,u,c}·softmax_t(K_u)·V_u`；channel-mix "similar to GeGLU with an extra R factor" | 是 / 否 |
| v1 | **α β γ 补偿因子** | `W_{t,u,c}=f_h(t-u)·α_h(u)·β_h(t)`，并对 time-mix 输出乘 γ(t)。原文理由："**the context size is smaller when t is small, and this can be compensated using the α β γ factors**"。**（UPDATE: We remove α β γ factors in v2-RNN）** | 是 |
| v1 | 零初始化 | "Initialize K and R matrices (and the output projection matrix) to ZERO for fast & stable convergence." | 否 |
| v1 | **token-shift** | "explicitly uses (half the channels of this token) & (half the channels of prev token)"；作者理论："The shifted channels can focus on (2) [collect all previous context info] ... It's like some kind of residual connection, or a small RNN inside the transformer." | 是 |
| v1 | token-shift 的**规模门槛** | "for BPE-level English LM, it's only effective if your embedding is large enough (**at least 1024** - so the usual small L12-D768 model is not enough)"；"I also found you may want to use **less mixing in higher layers**." | 是 |
| v1 | **Head-QK Trick** | "learning to copy and avoid tokens"：在最终输出上加一路 `c=(q@kᵀ)/256`，掩码后乘 one-hot(idx)，`x = head(x) + c`，使模型能直接复制上下文中的 token | 是 |
| v1 | top-a 采样 | 自适应阈值 `0.2*p_max²` | 否（推理） |
| v2 | 去掉 α β γ，限制 W 形式 | "We remove α β γ factors in v2-RNN and **restrict W to be of a simple form and hence able to rewrite it as RNN**" | 是 |
| v2 | 改回 AFT 归一化 | "(UPDATE: We are using the original AFT normalization in v2)" | 是 |
| v3 | R/K/V 各自独立 TimeMix 系数 | `xk = x*time_mix_k + xx*(1-time_mix_k)` 等三路分开 | 是 |
| v3 | preLN 取代 postLN | "more stable & faster convergence"；第 0 层额外 `ln0` | 否 |
| v4 | — | README 只有一张图 `RWKV-v3-plan.png`，无文字机制说明 | — |
| v5 | **多头 + 矩阵值状态 + GroupNorm** | "RWKV-5 is multi-head and here shows one head. There is also a LayerNorm for each head (hence actually GroupNorm)." | 是 |
| **v4→v5 归一化变更** | **去掉分母** | README 对照表原文：RWKV-4 为 `r_1·(uk_1v_1+k_0v_0)/(uk_1+k_0)`（**有分母 = 加权平均**）；RWKV-5 为 `r_1(uk_1†v_1+k_0†v_0)`（**无分母 = 加权求和**） | 是 |
| v6 | **Dynamic Mix & Dynamic Decay（ddlerp）** | `time_mix_k = time_mix_k + (x@w1)@w2`，低秩投影使混合系数随输入动态变化；TimeMix 与 ChannelMix 都做 | 是 |
| v7 | 并行生成状态 + 全 RNN 微调 | "Use parallelized mode to quickly generate the state, then use a finetuned full RNN (the layers of token n can use outputs of all layer of token n-1) for sequential generation." | 是 |

**对本课题最重要的一条**：官方在 v4→v5 把状态从**归一化加权平均**改成**未归一化加权求和**。
本课题 B 档胜出的上下文正是**归一化均值** `cumsum(h)/cumsum(mask)`；而候选 B 的 RWKV-7 状态递归继承的是**未归一化求和**式状态。
同时 v1 的 α β γ 因子正是为"t 小时上下文更短"做补偿，官方在 v2 为了能写成 RNN 而**删除**了它。
以上均为官方原文事实。**这两条是否解释本课题的 0.2879 对 0.0192 差距，属未验证假设，需实验裁决。**

## 5.6 其他已核验官方训练技巧（不需序列轴）

- **变分法 LR 调度**（README "Better Learning Rate Schedule via Variantional Method of Loss Curve"）：
  "Try this: fixed lr for 1 hr, then exponential decay to 0.2 * lr in 12 hrs, and choose the t=[1hr, 13hr] segment."
- **头宽 128 核存在**：`train_temp/cuda/rwkv7_clampw128_v2.cpp` 已读全文，绑定名 `TORCH_LIBRARY(rwkv7_clampw128_v2)`，函数签名 `cuda_forward_128_v2(int B,int T,int H, bf*r,w,k,v,a,b,y, float*s,float*sa)` 与 `cuda_backward_128_v2(...)`。
  **与冻结文档 §5.3/§9.5 "融合核硬编码 N=64、头宽必须 64" 冲突。** 精确状态：绑定与函数名指示 128；`.cu` 内部头宽常量**尚未逐行核验**。
- **L2Wrap 损失核**：`rwkv7_l2wrap_ce_bf16_v2`、`rwkv7_head_l2wrap_ce_bf16_v4` 存在且被 train_temp/README 列入推荐升级清单；**具体作用未读源码，不做推测**。

## 5.7 `RWKV-v7/cuda/wkv7s.cu` 已读全文（状态传递核，主仓库内）

签名：`cuda_forward(int B,int T,int C,int H, float *state, bf16 *r,w,k,v,a,b,y)`

- **确实接受外部初始状态并写回最终状态**：核开头 `state[j] = _state[j]` 载入，结尾 `_state[j] = state[j]` 写回。
- **但有三条硬限制**（源码原文）：
  1. `assert(B == 1); // only for B=1`，且 `_state += h*_N_*_N_ + i*_N_; // wrong if B > 1 !!!`；
  2. **只有 forward，没有 backward** → 仅推理，不能训练；
  3. `typedef at::Half bf16;`（默认 fp16，bf16 行被注释掉）。
- 状态演化式：`s = s*w[j] + k[j]*vv + sa*b[j]`，`sa = Σ_j a[j]*state[j]`，读出 `y += s*r[j]`。

**结论**：主仓库的状态传递核只解决推理侧、B=1。冻结文档 §9.1 的 P0（训练侧跨截断状态传递）**在主仓库内仍未解决**；官方指向的训练侧方案在 `BlinkDL/RWKV-CUDA` 的 `rwkv7_fast_fused`（已派子代理核实接口）。

## 5.8 官方材料中**不存在**的东西（负面结论，同样重要）

以下在 README、`RWKV-8.md`、`RWKV-v8/README.md`、`RWKV-v7/README.md`、`train_temp/README.md`、`Research/rwkv7-g0-7.2b.md` 全文中**均未出现**：

- 任何关于**分布漂移、跨域、跨年度、OOD 泛化**的机制、实验或建议。检索词 `distribution shift|domain shift|out-of-distribution|covariate shift|concept drift|generalization gap` 在 README 中零命中。
- 任何"**何时该用状态递归、何时用简单聚合**"的判据。
- 任何**非语言建模任务上的定量对比**（唯一的非 LM 建议是 Vision Tasks 的 2D 位置编码与 tokenShift 变体，无数字）。
- 任何**与简单池化/均值基线的对比**。官方对照组只有 MHA+Rotary+GeGLU（README "Performance" 节，字符级 simplebooks-92）。

因此：**RWKV 官方材料无法为"跨年度分布漂移下该用多复杂的聚合"提供任何直接依据。** 这是负面结论，不是检索不足——上述文件已全文核验。

## 5.9 问题 3：RWKV 系在分布漂移/跨域下的表现（主代理亲自核验）

先在 `raw/papers/rwkv/` 29 篇原件全文检索 `distribution shift|domain shift|out-of-distribution|covariate shift|zero-shot transfer|cross-domain|concept drift`，只有 6 篇命中。逐个核验结果：

| 论文 | 原文位置 | 原文要点 | 判定 |
| --- | --- | --- | --- |
| Hou 2024 RWKV-TS | pdftotext -layout 第 136–152 行，§3.1 "Normalization and Patching" | "Instance Normalization. The first step is instance normalization. This technique has recently been proposed to **mitigate the distribution shift effect between training and testing data** [Kim et al., 2022]." | **漂移处理归因于实例归一化（RevIN），不是 WKV 状态递归。** WKV 只在同段落被描述为"linear time and space complexity"的自注意力替代 |
| Yang 2026 FRWKV+ | 第 282 行、参考 [44] | "and variable-wise distribution shifts [44]"，[44] 即 Kim 等 RevIN | 同上，漂移由归一化处理 |
| Sharma 2026 PLM-NIDS | 第 829–832 行，局限性节 | "**Single dataset evaluation. We evaluate on CIC-IDS-2017 only.** Cross-dataset generalisation to UNSW-NB15, HIKARI-2021, and real enterprise traffic is important future work." | **最接近本课题的 RWKV-NIDS 工作明确声明没有跨数据集评价** |
| Kulatilleke 2026 MambaNetBurst | 第 35 行摘要；第 577 行 | 摘要："moderate **state sizes are sufficient for robust generalization**"；"early downsampling through striding is consistently harmful"。第 577 行："we incur **zero risk of negative transfer from mismatched pre-training corpora, a well-known failure mode in traffic analysis under concept drift**" | Mamba-2 非 RWKV；结论是"更大状态没必要"，且把跨域失败归因于预训练语料不匹配 |
| Dong 2024 Decision-RWKV | 第 160 行 | "aims to address the distribution shift problem common in **offline RL**" | 离线 RL 语境，与跨年度检测无关 |

**问题 3 结论：RWKV 系在分布漂移/跨域设定下无先例。**
- 无任何 RWKV-7 / RWKV-8 ROSA 工作报告跨域或跨年度结果（官方 README/论文/仓库亦零命中，见 §5.8）。
- RWKV 时序线中处理漂移的机制是**实例归一化（RevIN）**，属于输入/输出归一化层，**与状态递归无关**。
- 最接近的 RWKV 网络入侵检测工作（PLM-NIDS）**自述只做了单数据集评价**。

## 5.10 RevIN（可搬运候选，但原件未取得）

- 题录：Kim, Kim, Tae, Park, Choi, Choo, "Reversible Instance Normalization for Accurate Time-Series Forecasting against Distribution Shift", **ICLR 2022 Poster**, OpenReview `cGDAkQo1C0p`。**无 arXiv 版本。**
- 证据等级：**仅题录 + 二手引用**（经 Hou 2024 RWKV-TS 与 Yang 2026 FRWKV+ 两篇本地全文交叉引用确认其作用是对抗分布漂移）。
- **下载失败，需用户手动下载**。已尝试并失败的入口：
  1. `https://openreview.net/pdf?id=cGDAkQo1C0p` → 返回 HTML（站点机器人验证），非 PDF；
  2. `https://openreview.net/pdf?id=cGDAkQo1C0p&noteId=...` → 同样返回 HTML；
  3. `https://seharanul17.github.io/RevIN/assets/paper.pdf` → 返回 HTML。
  与冻结文档 §9.3 记录的"OpenReview PDF 直链在本环境返回 403"一致。
- 备用入口供用户手动取：项目页 `https://seharanul17.github.io/RevIN/`、ICLR 虚拟会场 `https://iclr.cc/virtual/2022/poster/6034`、KAIST 机构库 `https://pure.kaist.ac.kr/en/publications/reversible-instance-normalization-for-accurate-time-series-foreca/`。
- **待验证线索（未核原文，不得当结论用）**：网络检索摘要称 "Li et al. (2023) showed that a simple linear model using RevIN can outperform most deep models"，以及后继方法 Dish-TS / SAN / SIN / FAN。这条与"简单基线胜过复杂模型"直接相关，**必须取得原文核验后才能引用**。

## 5.11 子代理 1（跨域/简单聚合文献）已完成 — 关键结论

新下载并核验入库 10 篇（`raw/papers/methodology/` 8 篇、`raw/papers/attack-detection/drift/` 1 篇、`raw/papers/datasets/data-protocol/` 1 篇）。

**最重要的五条**：
1. **Bartos 2016（USENIX Sec）= 本课题最直接同域先例**。`raw/papers/methodology/multiple-instance/2016-Bartos-Optimized-Invariant-Representation-USENIX.pdf`，行 1034/1094 "Flow-based representation shows very unsatisfactory results"；行 1077–1078 袋级聚合在**未见恶意家族**上 90% precision / 67% recall；行 110–111 把问题定义为 conditional shift。
2. **Shen 2018 SWEM（ACL）**：行 745–750 "overfitting issues in CNN or LSTM-based models ... mainly stems from **over-complicated compositional functions, rather than the word embedding layer**"。给出可搬的证伪实验：打乱顺序看性能是否掉。
3. **Zeng 2023 DLinear（AAAI）**：Table 5 打乱输入后 Transformer MSE 仅变 ≤0.20%（"do not preserve temporal order well"）；Table 7 "the training data scale is not the limiting reason" —— 与本课题"数据量 ×115 倍 AP 反降"同构。
4. **Leoste 2025（TalTech 硕士论文，副导师 Allard Dijk）= 同 LSPR23→24 数据**：Table 11 跨年度含 IAT，**CNN F1 18.42% vs RF 18.41%（平手）**；Table 10 无 IAT 时 CNN 13.78% 反超 RF 2.20%。**"树天生胜深度"在同源数据上不成立**，主论点应走"聚合复杂度"而非"树 vs 深度"。
5. **TESSERACT 2019（USENIX Sec）= 反例，不得隐瞒**：24 个月时间衰减下 **DL 最鲁棒**（AUT 0.64 > 线性 SVM 0.58）。作者自设边界"we are not claiming that deep learning is always more robust to time decay"。→ 本课题不能主张"越简单越抗漂移"，只能主张"**归纳偏置与任务结构不匹配时，增加序列组合参数会放大跨域退化**"。

**Ilse 2018（ICML）对 B 档的设计辩护**：§2.4 行 174–176 "the mean operator is definitely a bad MIL pooling to aggregate **instance scores**, although, it could succeed in calculating the **bag representation**"。B 档 `ctx=cumsum(h)/cumsum(mask)` 是**嵌入层**均值，正落在"可以成功"一侧。

**文献冲突（本课题机会）**：Gehri 2023 主张去掉时序特征（LS19 F1 0.007→0.638，但跨组织 ≤0.185 失败）；Leoste 2025 实测加 IAT 更好并点名反驳 Gehri。**二者都只在逐流特征层面争论，都没做跨流聚合。**

**空白点**：无任何论文测试过"**因果前缀**跨流聚合"。Bartos 用非因果整袋直方图；Ilse/Pevny 的 MIL 池化是置换不变整袋聚合。B 档兼具袋级跨分布不变性与在线因果性。

**未获取**：Jacobs et al. CCS 2022 "The Emperor has no Clothes"（非开放，需用户手动下载 https://dl.acm.org/doi/10.1145/3548606.3560609）；Apruzzese SoK arXiv:2305.00550 建议补。

## 5.12 子代理 3（RWKV 生态论文）已完成 — 关键结论

数据源：`https://www.rwkv.cn/api/papers`（HTTP 200，206,622 B，**247 条**，截至 2026-08-07）。条目覆盖 100%，全文级证据 32 篇（约 13%）。
**证据分级警告**：rwkv.cn 的 `content` 是站方编辑中文摘要，**不是论文摘要原文**，标 `生态目录条目` 者不可用于论断。

### ★ 头号发现：B 档是 Vision-RWKV 的因果特例，不是朴素基线（主代理已独立复核原文）

**Vision-RWKV（ICLR 2025）** `raw/papers/rwkv/2024_Duan_Vision-RWKV_视觉双向扫描.pdf`，SHA-256 前缀 `97b67f08fa033269`。
主代理用 `pdftotext -layout` 独立复核，三条修改逐字命中：
- 行 333：`into bidirectional global attention.`（丢弃因果性）
- 行 334：`difference t − i and divide it by the total number of tokens (denoted as T ) to represent the relative bias`（**衰减指数 ÷T**）
- 行 335：`(3) Flexible decay: We no longer restrict the learnable`（允许衰减为负）
- 行 620：`The result of Variant 3 shows the global attention mechanism brings a 2.3 points increase in the`

式(5) 分母为归一化项 → 它是**加权平均**而非无界累加；`w→0` 且 `k_i≈const` 时**退化为算术平均**。
Table 5（p.9, VRWKV-T, ImageNet-1K）：原始因果 RWKV 71.1 → 因果+Q-Shift 72.8 → **双向归一化平均 75.1**。
**即：在无天然序列轴的领域，把因果状态递归换成对称归一化平均 +2.3 点。方向与本课题 A(0.1590)→B(0.2879) 一致。**
105 篇图像论文（占生态 42.5%）建立在这一改动之上。

### 生态结构
图像 105（42.5%）、序列/强化 52、3D/视频 32、通用/架构 26、语言 19、音频 13。
**137/247（近六成）输入无天然序列轴**——本课题 2-IP 分组序列属于生态主流类别。
**安全与流量方向仅 7 篇** → 本课题处于生态空白区。

### ★ RWKV 输给简单基线的报告（观察点 2，确实存在且不止一处）
- **RWKV-CVM**（Electricity 7(2):58, 2026）逐字：`RWKV-CVM beats both DLinear and iTransformer on zero full-data datasets. We therefore make no full-data superiority claim.`（PDF 行 1062–1066）
- **RWKV-TS** 插补任务被 TimesNet 碾压：ETTm1 MSE **0.149 vs 0.027**（差 5.5 倍）；异常检测 F1 83.89 < TimesNet 85.24
- **RWKV-TS+**（IEEE TKDE 2026）劣于自己骨干：ETTh1 0.444 vs RWKV-TS 0.433；自陈分类分支跨批时序机制 "meaningless" 并已替换
- **MambaNetBurst**：`d_state` 128 时反而退化（AVG 0.9909→0.9849，方差涨 4.6 倍）；Linear Transformer+FlashAttn-2 的 F1 最高 0.9925 超过 Mamba-2
- **GoldFinch**：混合后长度外推鲁棒性**反而不如**纯线性主干
- 另有 STWGRL、4G/5G 预测、QuantumRWKV、BlackGoose Rimer 的负面/持平结果

### ★ 现成的适用性判据（不用自己编）
1. **《Why Are Linear RNNs More Parallelizable?》ICML 2026**（本次下载，SHA 前缀 `24ed4db3`）：Definition 5 的 DPLR 线性 RNN `A_t = D_t − k_tᵀv_t` **字面就是 RWKV-7 的转移矩阵**；其额外表达力（PNC¹ 严格强于对角型的 NC¹）被**迭代矩阵乘法、状态跟踪、召回**这类**顺序敏感不可交换**任务消耗。
   → **推论（论文未声明，属待验证假设）**：若标签信号是顺序不敏感的聚合统计量，前缀均值已是充分统计量，DPLR 额外表达力无处施展。
2. **RWKV-CVM p.2–3 逐字**：`CD methods tend to overfit spurious correlations, especially when inter-variate relationships are non-stationary`；主张 `selectively incorporating cross-variate information when it is reliable, while avoiding indiscriminate mixing that introduces noise`。
   → LSPR23→24 正是"关系非平稳"的教科书情形。
3. **生态内不存在"历史越长越好"的共识**：RWKV-TS+ 自陈 SMAP 需更短回看窗、MSL 需更长；STWGRL 为六数据集分别搜窗口。

### 可搬到"同一 2-IP 对流按时间排序"的三条做法
1. **顺序随机化消融**（源自 Random Shuffle RWKV，Information Fusion / NeurIPS 2025）——最小成本最高信息量，**建议优先跑**
2. **双向 vs 因果对比**（源自 Vision-RWKV Table 5）
3. **重排＋连续性补偿**（源自 CLUIE / CVPR 2026 Multigrain 语义原型扫描，SHA 前缀 `f318eb5c`）
另：**PointRWKV**（SHA 前缀 `8783c123`）p.1 明确否定对无序输入强加单向顺序：`the inherent property of unidirectional modeling of the vanilla SSM hinders them ... for the unordered point cloud data`

### 新增原件 4 篇（`raw/papers/rwkv/` 29→33）
`2024_Duan_Vision-RWKV_视觉双向扫描.pdf`、`2024_He_PointRWKV_点云序列化.pdf`、`2026_Multigrain_语义原型扫描重排序_全色锐化.pdf`、`2026_线性RNN可并行性理论.pdf`（SHA-256 见上）。

### 需用户手动下载
Random Shuffle RWKV（NeurIPS 2025）`https://openreview.net/forum?id=gqfQfqDQhx`（curl 403）；期刊版 `https://www.sciencedirect.com/science/article/pii/S1566253526004239`（需订阅）。

## 5.13 知识库合规缺口（主代理核验）

`git status --porcelain raw/papers/` 显示 **46 项未跟踪**。新下载论文**均无 `wiki/papers/` 结构化笔记**：
Bartos 0、Ilse 0、Grinsztajn 0、Pendlebury 0、Dacrema 0、Keogh 0、SWEM 0。
按 `wiki/AGENTS.md` 与 RWKV 路线规则，原件入库后须写全文笔记并更新 INDEX 与 Zotero。**本次未执行（任务要求不写 .md 报告），需用户决定是否派发补齐。**

## 5.14 子代理 2（实体级聚合与决策层）已完成 — 关键结论

新增 10 篇原件到新建目录 `raw/papers/methodology/multiple-instance/`（主代理已核验为真 PDF）。

### ★ 问题 B 最强先例：Gehri 2023（同一篇内的表示层失败 / 聚合层成功对照）
主代理独立复核 `pdftotext -layout` 原文：
- 行 646：`completely unfamiliar environments is an open problem for future research`（**流级表示在陌生环境失败**；Table VII 最好表示在 LS19 precision 仅 0.474、LS21B 仅 0.491）
- 行 648：`we demonstrated that models that sum up the number of malicious flows`
- 行 656：`detection rate of over 90% and FPR below 4%, even for network environments not`（**同一模型输出经主机级聚合后成功**）
- 行 618：Country B 主机级结果 `surprisingly good compared with the F1 scores`
**同一 Locked Shields 数据集家族，与本课题实体级 AP 0.5233–0.5475 同向。本课题增量在于用排序指标而非点估计，且跨的是年度而非国家。**

### ★ 问题 A 答案：top-n 远不是文献上限，五类更强做法可搬
| 做法 | 出处（已核验行号） | 额外输入 | 替换 top-n 的哪部分 |
| --- | --- | --- | --- |
| **学习型 Lp 范数池化**（p 可学） | Gulcehre 2014 行 13–25 | **无** | 整体替换；max=p→∞、mean=p=1 是两端点 |
| noisy-OR / noisy-AND / log-sum-exp | Ilse 2018 行 155–166 | 无 | 软化硬取最大，对实体内流数不均更稳 |
| 嵌入级池化替代分数级池化 | Ilse 2018 行 138–166、455–470；Pevny 1609.07257 行 181–196 | 需重训（即 B 档） | "打分再聚合"→"聚合再打分" |
| 实体图上到已知恶意实体的跳数 | Zhang ACSAC'23 行 570–580（该文最重要特征 Top-3 全是图距离） | LSPR23 恶意实体清单（已有） | 加一维特征 |
| 实体流行度（被多少对端访问） | BAYWATCH 行 349–355 | 无 | 加一维特征 |
| 同实体内客户端行为相似度/分数方差 | DISCLOSURE 行 175–200 | 无 | top-n 只用极值，这里用离散度 |

### ★ 机制解释（现成，不用自编）：Pevny & Somol 2016 AISec
行 521–545 受控比较：**max 池化过拟合**（作者归因：网络退化成"复杂的签名检测器"，学到训练集感染机特有的具体流模式）；**mean 池化训练/测试差距远小于 max**（归因：学到的是**行为**而非专有模式）。测试数据比训练晚一个月。
→ 与本课题 GRU 0.1758 / Transformer 0.0742 / RWKV 0.0192–0.0101 全部低于前缀均值 0.2879 高度一致。
**这是唯一一篇把"聚合算子选择"与"架构复杂度"放进同一组受控实验、并报告前者更关键的安全领域论文。**

### ★ 领域外最清晰归因：Wieting ICLR 2016（行 23–32、81–88）
**LSTM 域内最好；域外词向量平均大幅胜出**，22 个 SemEval 数据集上平均高 **16.5 Pearson r**。但情感分类上 LSTM 仍强 → **不是"简单永远更好"，而是任务性质 + 分布偏移共同决定**。

### 重要修正（简报原假设有误）
- **Zhang ACSAC 2023 的 "Aggregation" 不是分数聚合**，而是跨校园网把同一 FQDN 的**时间序列相加**；其决策层贡献是"排序 + 分析师预算 + 主动学习 + 图距离特征"（平均 10 案例/天送人工，73% 的日子 ≤10）。
- **BAYWATCH 不只是目的地级**：数据抽取以 `H(s,d)` **源/目的对**为 key（行 345–365），目的地级另作**流行度**分母用（行 349–355）。→ **本课题 2-IP 实体轴有直接文献依据。**
- **Bartos 把 bag 聚合称为"表示（representation）"改进**，不是"聚合层"。本课题若主张"聚合层"，须自行定义"改变分类单元粒度" vs "改变单元内编码方式"，文献没做这个区分。
- CBSeq（TIFS 2023）行 109–110 把 channel 定义为 **same source IP and destination IP** 的多流聚合 → 2-IP 实体的第三条依据。

### 因果性纪律（可引用的规范依据）
arXiv:2602.05594 综述 Table 4（行 570–585）明确写 Packet→Flow 层 `Causal aggregation only`、Flow→Host 层 `Lagged windows only`。
**注意：A1-1 Bartos（5 分钟全窗）、A1-2 Pevny（5 分钟全窗）、A1-6 CBSeq（24 小时全窗）三篇实际做法全是非因果全窗。本课题的因果前缀比它们更严格 → 这是创新点差异，不是缺陷。**

### 明确的否定结论
**没有**任何安全领域论文做过本课题这样的受控设计：固定数据与预算，把**表示层多变体**（序列构造、状态演化、时间编码、残差形式）与**聚合层改动**放进同一张表对比并报告前者全败、后者有效。**这个空位是真实的。**

### 未获取（需用户手动下载）
Prasse et al. IEEE SPW 2017 `https://ieeexplore.ieee.org/document/7965579`；Springer 2025 MIL 加密恶意流量 DOI `10.1007/978-3-031-97629-2_19`（登录墙）；Lee & Stolfo ACM TISSEC 2000 DOI `10.1145/382912.382914`（KDD'99 "past two seconds same-host count" 是**因果前缀实体聚合的最早范式**，四个镜像全失效）。

## 5.15 对"同年度对照"建议的修正（主代理核验既有制品后）

子代理 2 建议跑 LSPR23→LSPR23 同年对照以对齐 Wieting ICLR 2016 的"域内 LSTM 胜、域外平均胜"结构。
**但本仓库既有证据显示同年度已接近天花板，该对照可能不可判别**：
- `.Codex/docs/RWKV/2026-08-12-LSPR24同年基线天花板与标签删失诊断.md` 第 26–27 行：同年强树基线 `AP = 0.9690…`，可用余量 `1 − AP = 0.03096512`。
- Dijk 2026 表 5 同分布列：XGB `1.0000`、GRU `0.9984`、Transformer `0.9964` —— **三者全部饱和**。
→ 同年度 A/B/C 三档大概率同样饱和在 0.97–1.00，无法区分。
**因此优先级应调整为：顺序随机化消融（子代理 3 建议 1）与 Lp 池化扫描（子代理 2 建议 1）优先于同年度对照。**

## 5.16 子代理 4（未发表机制与周边仓库）已完成 — 关键结论

### ★ 冻结文档 §9.1 的 P0 可关闭（主代理已独立复核源码）
仓库 `BlinkDL/RWKV-CUDA`，HEAD `9b17d5d80a0e9d2cbf090590725672464daa3aee`（2025-12-10，提交信息 `+ rwkv7 state-passing (infctx) kernel`）。
主代理直接读取 `rwkv7_fast_fused/cuda/rwkv7_statepassing_clampw.cpp` 全文，**逐字确认**：
```
void cuda_forward (int B,int T,int H, float*s0, bf*r,w,k,v,a,b, bf*y, float*sT, float*s, float*sa);
void cuda_backward(int B,int T,int H, bf*r,w,k,v,a,b, bf*dy, float*dsT, float*s, float*sa, float*ds0, bf*dr,dw,dk,dv,da,db);
TORCH_LIBRARY(rwkv7_statepassing_clampw, m)
```
**s0 入、sT 出、ds0 出三者齐全，梯度可回传到初始状态。**

三套核并存：`rwkv7_clampw`（vanilla，无状态接口）、`rwkv7_state_clampw`（state-tuning，**只有 s0 无 sT，无法链式跨截断**）、`rwkv7_statepassing_clampw`（**完整**）。
采用约束（源码硬断言）：`s0/sT` 形状 `(B,H,N,N)` 且**必须 float32**；`T % 16 == 0`；张量须 contiguous。
官方代价声明（RWKV-LM README:59）：`simpler but slower than train_temp/cuda`。
**原 P0 判断针对 `train_temp` 准确**：`train_temp/cuda/wkv7_op.cpp:5,12` 的 `wind_backstepping` 签名无 s0/sT/ds0（其中 `s` 是 backward 分块检查点缓冲）。`infctx` 一词在整个 RWKV-LM 仓库只出现在 README。

### DeepEmbed / DeepEmbedAttention（官方源码已核验，但**本课题不可直接用**）
- `RWKV-8.md` 全文 61 行**无 "DeepEmbed" 字样**，README 亦无；但源码有可运行实现，证据强于推文。
- **DeepEmbed 最简形（`enn`）**：`RWKV-v7/rwkv_v8_rc00_demo.py:255-259`，`return (k @ V_) * E_`，`E_ = z[ffn+'enn.weight'][idx]` —— 每层 FFN 输出乘以**按 token 索引查表**的逐通道向量。
- **低秩形（`s_emb`）**：`rwkv_v7a_demo.py:257-263`，每 token 查出 32×32 矩阵门控 FFN 隐层。→ **修正主代理 §3.3 的判断：v7a 不只是实现变体，含 DeepEmbed 低秩形。**
- **重参数化**：`rwkv_v7a_demo.py:105-106`，`s_emb.weight = s_emb.weight + emb.weight @ s_emb_x.weight.t()`，源码注 `# !!! merge emb residual !!!`
- **DEA**：`rwkv_v7b_demo.py:151-171`，K/V 只写 32 维进 cache，读取时上投影并乘按 token 查表向量；`:122` 注 `kv cache = 12*2*32 numbers per token`。→ 证实主代理 §3.3 对 v7b 的观察。
- **硬性前置条件（源码事实）**：`enn`/`s_emb`/`k_emb`/`v_emb` 全部由**离散 token 索引 `idx` 查表**。本课题 83 字段逐流表格数据无天然词表 → **不可直接移植**，自造离散键属新设计且无任何跨年度证据。
- X 推文原文**未取得**：`x.com/BlinkDL_AI/status/1926941496684519805` 与 `/1939532655823040545` 均返回 **HTTP 402 Payment Required**；已尝试 `r.jina.ai`（Socket closed）、`nitter.net`（空页）、两次定向 WebSearch（未索引）。**因此"作者近期是否还公布了其他新机制"无法排除。**

### ★★ 作者亲自把本课题的核心疑问列为公开未决问题
`RWKV-8.md:57` 原文：
> These are all beneficial, and the question is {depth-L1 model with fancy state evolution} vs {depth-L2 model with simple state evolution} where L2 > L1 and speed-matched.

**可直接引用为研究空白依据。**

### ★ 独立第三方同向证据：WKV 状态作表征远差于 hidden state
BlinkDL 本人在 issue #349（2026-08-09）回帖原文：`and please check https://github.com/cgisky1980/rwkv7-state-embedding too`。
该仓库 README（HEAD `bc6755a1`，**社区、非官方**）"失败方向"表：

| 方法 | 结果 | 仓库给的原因 |
| --- | --- | --- |
| Pure WKV state (Q-Readout) | **0.11** | State value range small, std=0.13 |
| WKV state aggregation stats | **0.10** | row_sum/diag/trace have no clustering info |
| 对照：hidden state + 监督 MLP | **0.93** | — |

**与本课题"完整 RWKV-7 状态递归 0.0192/0.0101 远差于最简前缀均值 0.2879"同向。**
该仓库另一结论：hidden state 存在 severe anisotropy，无监督抽取失败（STS 0.46），须加监督投影头。

### 工程陷阱（社区，非官方，但与本课题 P0 同域）
issue #338（icophy, 2026-08-09）：`RWKV_Tmix_x070_infctx` "silently ignores `time_state` entirely and falls back to WKV-carried state"，作废整批实验。**该函数属 RWKV-PEFT，不在 BlinkDL/RWKV-LM 内。** → 本课题接入任何第三方 infctx 实现前必须断言初始状态确实被消费。
同帖另一条（非官方）：跨域注入 mid-sequence WKV state 判 FAIL，"mid-sequence WKV state is path-dependent and context-coupled, not a portable representation" → 对"跨年度直接搬运状态"是负面证据。

### 其他
RWKV-LM 只有 `main` 一个分支；近 25 次提交（2026-05-22 至 2026-07-23）均为 README 更新与核优化，**无新机制发布**。Discussions 无机制相关新内容。本条线未发现值得下载的新论文（DeepEmbed/DEA/ROSA/state-passing 核均无对应论文）。

## 6. 待办

- [ ] 读 `rwkv_v7a_demo.py` / `rwkv_v7b_demo.py` 判断 v7a/v7b 是什么
- [ ] 读 `wkv7s.cu`、`wkv6state_cuda.cu` 确认状态核接口
- [ ] 读 `train_temp/src/model.py` 的 L2Wrap 与 dropout 实际实现
- [ ] 核对 `rwkv7_clampw128_v2` 是否支持头宽 128（推翻冻结文档 §9.5）
- [ ] 逐版本 v1→v7 机制演化（token shift / time-mix / channel-mix 形式变化）
- [ ] 三个子代理结果汇总

## 7. 子代理台账（模型 → effort）

| 代理 | 任务 | 模型 |
| --- | --- | --- |
| 跨域树胜序列文献核验 | 原问题 1、2（已发更正：改为"简单聚合胜过复杂序列模型"） | opus |
| 实体级聚合与决策层文献核验 | 原问题 4、5（已发更正：扩展为建模期+决策期两层聚合） | opus |
| RWKV 生态论文页盘点 | 生态论文逐篇（已发更正：先读本地 29 原件 + 28 笔记） | opus |
| RWKV 未发表机制与周边仓库 | RWKV-CUDA / Albatross / X / issues / 社区 | opus |
