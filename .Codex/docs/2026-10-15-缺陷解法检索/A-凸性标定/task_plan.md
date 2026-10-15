# 任务计划：A-凸性标定——凸映射放大分布漂移的文献解法检索

- 日期：2026-10-15
- 执行代理：文献检索代理（模型 glm-5.3-flash，经 Claude Code Agent SDK）
- 性质：**只检索与判读，不跑任何实验**（本机 CPU 正在训练，禁止启动任何计算）
- 任务目录：`/Users/bilibili/personal/note/.worktrees/ch3-lamda-20260908/.Codex/docs/2026-10-15-缺陷解法检索/A-凸性标定/`

## 缺陷（已实测，输入为准）

第三章 LAMDA 缓冲容量 N=200，每轮历史样本复用倍数由梯度夹角 ρ 决定：

```
λ_r = (1 − a*) / (1 − ρ_r)
m_r = λ_r·N / (N − λ_r·N)      （等价于 m_r = λ_r / (1 − λ_r)，与 N 无关）
m_r 再按上界 m_cap 截断
```

- 标定量 a\* 不是不变量：m_r 对 ρ 是凸函数，ρ 分布漂移被放大；同一 a\* 套不同训练轨迹，平均复用倍数在 3.25–4.76 漂移（目标 4）。
- 加 cap 截断后 3.97≈4，说明上界是解法的一部分，但只压长尾，没解决「标定量依赖分布」。

## 要回答的四个问题

1. 有没有把「一次性标定常数」换成「闭环/自适应控制」且明确处理凸映射放大分布漂移的做法？（已给线索：PPO adaptive KL 控制器，需核原文页码/公式/更新式，并判断能否移植到每轮一次的 m_r 更新）
2. 有没有直接针对凸映射的鲁棒标定（分位数、截断、对偶变量、控制屏障函数、DRO 等）？
3. 每条候选能否在 our setting 证伪？写最小验证实验（数据、指标、通过/失败门槛、成本）。
4. 诚实结论：没有对症解法就明说；「有人做过类似的事」≠ 解决方案，必须能落到我们的公式上。

## 检索路线（顺序）

1. 本地查重：`mcp__zotero__zotero_semantic_search` + 本地混合索引（仓库根 `uv run --project scripts/literature_search --locked python -m scripts.literature_search query "..." --scope local --mode hybrid --json`）
2. Google Scholar（必须挂本机代理）：`HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890 scholar search "<查询>" --json`；**失败挂代理重试，禁止用 WebSearch 替代**
3. 对候选按标题在 arXiv / 出版社主站重新定位 ID（在线结果只作候选）
4. 原文核验：下载 PDF → `pdf-converter`（MinerU）转全文；禁止 `pdftotext`
5. 入库：PDF → `raw/papers/attack-detection/lamda-related/`（命名 `年份-一作-主题.pdf`）；全文笔记 → `wiki/papers/attack-detection/lamda-related/`（frontmatter 八字段，`source_pdf` 指向 raw 原件）；更新 `wiki/papers/attack-detection/INDEX.md`
6. 报告：本目录，中文文件名（勿用 `report.md`）

## 候选方向（预检索清单，逐条核原文后裁定）

- C1 PPO adaptive KL penalty（Schulman et al. 2017, arXiv:1707.06347）
- C2 对偶梯度下降 / 拉格朗日约束（Tessler et al. 2019 Reward Constrained Policy Optimization）
- C3 PID Lagrangian（Stooke, Achiam, Abbeel 2020）
- C4 截断重要性采样（Precup 2000 TIS；Munos 2016 Retrace；Espeholt 2018 V-trace/IMPALA）
- C5 Lyapunov 虚拟队列 / 在线原始-对偶约束跟踪（Neely）
- C6 DRO / CVaR 分位数标定（Rockafellar & Uryasev 2000；Esfahani & Kuhn 2018）
- C7 自适应重放倍数 / UTD ratio 控制（待检索确认是否存在）
- C8 超梯度下降在线调节超参（Baydin et al. 2018）
- C9 梯度夹角选样（MIR, Aljundi et al. 2019）——同用 ρ 但非标定，仅作背景

## 落盘纪律

- 每 30 分钟更新 `notes.md`：已完成项、下一条查询、未关闭疑点、无法获取原文清单
- 只操作本任务文件，不 git 提交
