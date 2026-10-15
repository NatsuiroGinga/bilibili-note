# task_plan：缺陷 2（分配信号低信噪比）文献解法检索

## 任务边界

- **只做文献检索与判读，不跑任何实验**。本机 CPU 正跑训练任务，禁止启动训练、评价、张量计算。
- 缺陷：LAMDA 第三章回放复用倍数 m_r（1–40）由梯度夹角 ρ（历史批梯度与当前批梯度余弦）驱动；只读重复实验实测 ρ 轮间波动约 80% 是批采样噪声（重抽批次 σ=0.755 vs 固定批次 σ=0.012；噪声方差占比 78–81%；真实信号 σ_s≈0.15–0.17）。机制实际在按噪声随机重分配历史权重。
- 已试过且未复现：EMA 平滑（β=0.7，11 年平均 88.42→88.76 = +0.34；补 seed 43 后 −0.28）。
- 已知线索：① Energy-based OOD 检测（p.1-2 的「softmax 分数有缺陷 → 换 energy 量」决策陈述）；② aL-SAR（Seo 2025，本地全文）附录 A.8 单信号有害、合成后显著（60.76 → 56.15 → 62.72 → 64.60）。

## 要回答的问题

1. 低信噪比下估计/使用相似度或重要性信号的通行做法（EMA、多信号合成、贝叶斯收缩、置信加权、方差惩罚 bandit/UCB），附原文出处与公式。
2. 明确处理「测量噪声主导」的分配/调度文献。
3. 每条候选解法在本文设置下的可证伪性与最小验证实验（数据/指标/门槛/成本）。
4. 诚实结论：无对症解法就直说。

## 交付物

- 本目录 `report.md`：候选解法清单（出处、页码/公式号、证据等级）、移植公式、最小验证实验、未取得原文清单、一句话裁决。
- 入库：确认有用的论文 → `raw/papers/attack-detection/lamda-related/`（或更贴切目录）+ `wiki/papers/attack-detection/lamda-related/` 结构化笔记（frontmatter 八字段、source_pdf 指向 raw）+ 更新方向 `INDEX.md`。
- 汇报：模型名、实际 effort、检索式清单、入库清单、一句话裁决。

## 检索策略

入口顺序：本地 Zotero 语义检索（防重复）→ 本地混合索引 → Google Scholar（挂代理 `HTTPS_PROXY=http://127.0.0.1:7890`，`scholar search --json`）→ arXiv/出版社主站定位全文。读 PDF 只用 `pdf-converter` 技能。

检索主题（预计多轮）：
- A. 噪声信号下的分配：bandit/best-arm identification with noise、variance-penalized allocation、UCB
- B. 梯度相似度样本选择：GSS、ASER、MIR 等 replay 采样方法的信号噪声问题
- C. 换更稳的信号：energy score（Liu et al. 2020 NeurIPS）核实原文 p.1-2
- D. 多信号合成：aL-SAR 附录 A.8 复核 + 其他 composite score 文献
- E. 估计器降噪：shrinkage/Kalman/多批平均，不同于等权 EMA 的方式

## 时间线与检查点

- [ ] T0（约 14:05）：task_plan.md + notes.md 落盘
- [ ] T0+30min：本地检索完成，Scholar 首轮检索落盘 notes.md
- [ ] T0+60min：候选论文定位、全文下载
- [ ] T0+90min：核心全文（≥3 篇）转换与精读，页码/公式登记
- [ ] T0+120min：入库 raw/wiki/INDEX
- [ ] T0+150min：report.md 完成

## 阻塞与风险

- Google Scholar 直连 HTTP 000，必须挂本机代理；失败禁止改用 WebSearch 替代 `scholar`。
- 在线结果只作候选，全文未取得前证据等级只标「仅题录/在线摘要」。
- 上个代理未落盘、工作归零——本任务一切中间结论立即写 notes.md。
