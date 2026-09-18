# RWKV-8 ROSA 与 DeepEmbed 候选审查证据日志

## 任务约束

- 路线：`RESEARCH_ROUTE=RWKV`。
- 研究对象：网络攻击状态检测训练方法；候选必须回到真实网络安全数据和自然实体/时间接口。
- 结论等级：全文与官方代码证明机制来源和可试性；本课题真实数据实验才可支持或否决本课题效果。
- 禁止事项：不凭名称推演，不用摘要支撑理论结论，不运行大实验，不修改 Goal、正文或恢复卡。

## 上下文恢复记录

- 已读取根规则、`wiki/AGENTS.md`、`raw/AGENTS.md`、`.Codex/docs/AGENTS.md`、RWKV 局部规则与路线总控。
- 已读取第三章恢复卡和候选登记册；恢复卡指出旧 FT 机制在跨年评价中失败，且源年实体评价样本量不足。
- 已读取 Astra 的第三章方向与新 Goal 裁决；当前方向要求先核实数据与骨干，再以真实病灶和未来开发池证伪候选。
- 已读取 `planning-with-files`、`google-scholar`、`citation-verification`、`pdf-converter`、`huggingface-papers` 与 `hf-cli` 技能。

## 查询与来源日志

### 本地混合索引

- 顺序：先执行 `status --json`，再执行 `paper/hybrid/offline` 查询。
- 全局索引因多个并行任务新增过程文档持续显示 `stale=true`；论文集合本身保持 `891` 篇不变。为避免过程文档竞态，复制现有索引并用只含 `wiki/papers/**/*.md` 的临时配置增量删除非论文集合，得到稳定论文索引。
- 稳定索引收据：`scope=paper`、`mode=hybrid`、`note_count=891`、`chunk_count=126370`、`reused=126370`、`reembedded=0`、`built_at=2026-09-07T05:14:29.176563+00:00`、索引 SHA-256 `c3528f9a2ce9edb69ffda99aac59cff9dacb2272b506b85ed4f9888143721f96`。
- 查询式：`RWKV-8 ROSA DeepEmbed DeepEmbedAttention`、`RWKV-8 ROSA recurrent state tracking suffix automaton`、`RWKV-8 DeepEmbed DeepEmbedAttention architecture`、`RWKV-8 TimeMix DeepEmbed Engram`。
- 关键命中：`wiki/papers/deepseek/2601.07372_Engram-DeepSeek-全文.md`、`wiki/papers/methodology/2024-Hu-SAM-Decoding-Suffix-Automaton-全文.md`、`wiki/papers/rwkv/2025-Peng-RWKV7-Goose.md`、`wiki/papers/attack-detection/encrypted/2023-Cui-CBSeq-Encrypted-Malware-全文.md`。
- 结论：本地没有 RWKV-8 正式论文；Engram 全文把 DeepEmbed 列为逐层大表嵌入的近邻，SAM Decoding 全文证明通用后缀自动机检索已是既有构件。

### Zotero

- 先执行三组语义检索，再执行 `DeepEmbed`、`DeepEmbedAttention`、`ROSA RWKV`、`RWKV-8` 精确题录检索。
- 语义命中 RWKV-7 Goose（`A4M74UVI`）与 SAM Decoding（`DYBA9QVH`），但精确题录检索对三项 RWKV-8 名称均返回空。
- 结论：Zotero 当前没有可把三项候选升级为正式论文证据的条目；RWKV-7 与 SAM Decoding 只支撑来源边界和最近邻比较。

### 在线官方来源

- RWKV 官方仓库：<https://github.com/BlinkDL/RWKV-LM>；核验提交 `9a75f9f037afa4418ee6283b584b92b1adb89ca1`，提交时间 `2026-09-03T11:29:42+08:00`。
- RWKV 官方社区文档：<https://github.com/RWKV/RWKV-wiki/blob/main/docs/basic/architecture.md>。该页自称由人工智能生成、可能含错，只用于定位，结构以源码为准。
- ROSA-Tuning：arXiv `2602.02499`，Hugging Face 全文与题录已读取，代码 <https://github.com/zyaaa-ux/ROSA-Tuning>。它是社区预印本，不是 RWKV-8 正式架构论文。
- Engram：本地 MinerU 全文 `wiki/papers/deepseek/2601.07372_Engram-DeepSeek-全文.md`，原件 `raw/papers/deepseek/2601.07372_Engram-DeepSeek.pdf`；它引用 DeepEmbed 网页并提供更成熟的条件记忆对照，但不是 DeepEmbed 论文。
- Hugging Face 官方临时模型仓库 `BlinkDL/temp-latest-training-models` 含 `rwkv-rosa1bit-minipile-loss3dot81-20260212-ctx512.pth` 与 `rwkv-rosa4bit-minipile-loss3dot44-20260221-ctx512.pth`；未发现名称明确的 DEA 检查点。

## 候选事实表

| 候选 | 官方名称/版本 | 论文全文 | 官方代码 | 公式证据 | 当前等级 |
| --- | --- | --- | --- | --- | --- |
| RWKV-8 ROSA | `ROSA`；官方 README 展开为 Rapid Online Suffix Automaton，社区文档/ROSA-Tuning 又作 RWKV Online Suffix Automaton；至少有 2025-10 至 2026-02 多个脚本版本 | 无 RWKV-8 正式论文；社区 ROSA-Tuning 有 arXiv 全文 | 官方仓库含慢参考、训练演示、QKV 版和 1/4 比特推理演示 | 最长历史后缀匹配后读取后继值；隐状态符号化后作多路 Q/K/V 检索 | 工程原型；设计可行，实验待证 |
| DeepEmbed | `DeepEmbed`/`DE`；`rwkv7a` 实装 | 无独立正式论文；Engram 全文只作近邻与引用证据 | `RWKV-v7/rwkv_v7a_demo.py` | 每层 token 专属矩阵由当前隐藏状态选择，乘法调制 ReLU² FFN 通道 | 有推理参考和模型命名，无完整论文/训练协议；实验待证 |
| DeepEmbedAttention | `DeepEmbedAttention`/`DEA`；`rwkv7b` 实装 | 无独立正式论文 | `RWKV-v7/rwkv_v7b_demo.py` | 低维 K/V 历史缓存经投影并乘 token 专属 K/V 嵌入，再做因果 soft-cap 全注意力 | 低成熟度推理参考；非独立对称候选 |

## 官方源码核验

### DeepEmbed

- `rwkv_v7a_demo.py:105-106` 把输入 token embedding 的线性残差合并进每层 `s_emb.weight`。
- `rwkv_v7a_demo.py:257-273` 的实际计算为 `k=ReLU²(K·shift(x))`，`ss=(xW_s1)E_l[token]`，`k←k⊙(ssW_s2+s0)`，最后 `W_V k`。
- 因而它不是普通输入嵌入，也不是注意力；它是每层、每 token 的条件 FFN 通道调制。

### DeepEmbedAttention

- `rwkv_v7b_demo.py:105-108` 同时保留 DeepEmbed 的 `s_emb`，并为每层加入 `k_emb/v_emb`。
- `rwkv_v7b_demo.py:151-171` 缓存低维 K/V，按历史 token 索引读取 `k_emb/v_emb` 作乘法调制；随后计算 `64*tanh(QK^T/1024)`、因果遮罩、softmax 和加权 V。
- `rwkv_v7b_demo.py:181-186` 把该注意力输出与 RWKV TimeMix 同时残差加入，再运行仍带 DeepEmbed 的 ChannelMix。
- `rwkv_v7b_demo.py:116-125` 明确维护 token 索引、每层两组低维 K/V 缓存和 Q 的 token-shift 状态；源码注释称该演示低效且 KV cache 慢。
- 结论：官方 `rwkv7b` 是 `DE+DEA`，不是 DEA 替换 DE。可人为拆出“无 DE 的压缩全注意力”，但那是新消融定义，不是官方现成独立版本。

### ROSA

- `260222_rosa4bitLM_L12.py:156-173` 用穷举慢参考寻找当前 Q 的最长后缀在历史 K 中的最近匹配，并读取匹配后的 V；代码最坏开销高，不能拿来宣称线性工程性能。
- `260222_rosa4bitLM_L12.py:175-233` 把隐状态按符号打包为 4 比特路由，匹配时按比特解码为带可学习幅度的正负输出；Q/K/V 均含 token-shift 与线性投影。
- `260222_rosa4bitLM_L12.py:274-284` ROSA 是独立残差支路，再接普通 FFN；该脚本没有 RWKV TimeMix，README 也明确称“pure ROSA1bit + FFN (no RWKV)”。
- `251014_rosa_1bit_train.py` 与 `251014_rosa_1bit_layer.py` 自注“极慢”；`251024_rosaQKV_run.py` 是合成算术演示；这些不能证明网络安全效果或正式训练吞吐。
- ROSA-Tuning 全文式（1）至（7）给出对 Transformer 的 post-attn 加法或 pre-attn 混合挂载，式（8）至（22）给出二值多路 Q/K/V、后继位置检索与连续注入；它证明可移植性，不证明本课题适配。

## 已关闭问题

- DeepEmbed 是官方命名的逐层 token 条件 FFN 调制，已有 `rwkv7a` 推理参考，不只是泛称。
- DeepEmbedAttention 有 `rwkv7b` 实现，但官方实现包含 DeepEmbed；它既不替代 DeepEmbed，也不构成与其对称的独立因子。
- ROSA 有两种英文展开并存；报告中保留该命名差异，首次出现时写明来源。
- 时间漂移不是候选必要前提；必要的是自然因果序列、重复离散后缀/事件模式、稳定稀疏 token 语义、强基线余量和至少一个真实泛化轴。

## 最小下一实验

- 首个实现对象冻结为 DRIFT-DGA `T17→T25` 的零训练双探针，不先实现四格模型。
- 主视图用论文确定性规范化后的 eSLD；规范化 raw 仅检验 TLD/平台后缀捷径。
- ROSA 只在单个域名内部匹配当前位置的历史字符/子词后缀并读取后继，域名间强制重置；不得把 DNS 后缀概念混入 ROSA 后缀。
- 已纠正旧材料中的概念混用：跨年域名集合命中、公共后缀命中和跨域共享自动机都不是原生 ROSA 覆盖。DRIFT 的 ROSA 适配由高降为低到中，须由域内可检索位置与后继信息增量决定。
- DeepEmbed 词表、子词器和 n-gram 键只从 T17 冻结，T25 只测位置/域名级 OOV、覆盖和新生/消失质量。
- 任何候选若只在 raw 视图、跨域拼接或 TLD/平台后缀上显示信号，直接淘汰。
