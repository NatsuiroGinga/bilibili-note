# 门控组合方案实证审核 · 检索计划

- 建档时间：2026-09-04
- 任务类型：文献审核（找先例 + 主动找反证）
- 工作树：`/Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819`
- 边界：不改代码、不改既有文档、不跑实验、不入库；只在本目录建 `task_plan.md` / `notes.md`

## 被审机制（一句话）

多损失训练中，**依据上一步的运行时状态**（某内部活动集是否为空）在两种损失聚合形式间**逐训练步**切换：

- 上一步活动集为空 → 本步共同底座损失的实体聚合用尾部均值（tail mean, α=0.5）
- 否则 → 用 `maximum`

切换依据是运行时观测状态，不是 epoch 计划表，不是梯度方向。目的：让排序损失 BER 与尾部聚合 ETA 在时间上不相交。

## 关键结构特征（检索时用于判定「是否真先例」）

1. 门控信号来自**模型自身上一步的内部状态**（活动集空/非空）→ 构成状态反馈回路
2. 切换粒度是**训练步**（高频），不是阶段/轮次（低频）
3. 被切换的是**同一损失项的聚合算子**（tail mean vs max），不是不同损失项的权重
4. 声称有「下界论证」→ 需核查交替优化的收敛条件是否被数据依赖随机切换破坏

## 五条检索线

| 线 | 主题 | 核心待答问题 | 主要检索式（英文优先） |
| --- | --- | --- | --- |
| 1 | 课程学习与损失调度 | 切换依据是运行时状态还是预设 schedule？ | curriculum learning loss scheduling; loss annealing; dynamic loss weighting; automated curriculum learning teacher-student |
| 2 | 交替优化 | 收敛保证要求什么条件？数据依赖随机条件交替是否破坏保证？ | alternating minimization convergence; block coordinate descent randomized rule; Gauss-Southwell rule convergence; ADMM alternating |
| 3 | 多任务梯度冲突消解 | 有没有人试过「取消同时性」（时间分离而非梯度调和）？结果如何？ | PCGrad; CAGrad; ConFIG; GradNorm; uncertainty weighting Kendall; gradient vaccine; Nash-MTL; task scheduling MTL; sequential vs joint multi-task |
| 4 | 运行时状态触发的损失切换 | 有没有按 loss 值/梯度范数/统计量切换损失形式的先例？ | state-dependent loss switching; adaptive loss selection; conditional objective switching; bandit loss selection; RL-based loss selection; self-paced learning |
| 5 | 非平稳目标 SGD 与反馈切换稳定性 | 反馈切换会不会震荡/不收敛？ | non-stationary objective SGD convergence; switched systems stability arbitrary switching; hybrid dynamical systems chattering; self-referential feedback instability training |

## 检索顺序（强制）

1. 本地混合索引：`uv run --project scripts/literature_search --locked python -m scripts.literature_search status --json` → `query ... --scope all --mode hybrid --json`
2. Zotero 语义检索（避免重复入库）
3. 在线 MCP（search_papers / discover_papers / search_literature / semanticSearch）+ WebSearch + google-scholar 技能
4. PDF 一律走 `pdf-converter`（MinerU），禁止 `pdftotext`

## 证据等级标注

`本地全文` / `在线全文已下载` / `在线摘要` / `仅题录`。仅摘要或题录不得支撑「有先例」或「无先例」结论。

## 落盘纪律

每完成一条线立即写入 `notes.md` 并 `git commit`（Conventional Commits，英文描述，禁 Co-Authored-By）。

## 进度

- [x] 建档
- [x] 线 1 课程学习与损失调度 —— 部分先例，不可迁移（Bengio 定义要求单调性）
- [x] 线 2 交替优化收敛条件 —— 存在条件级反证（本质循环前提不成立）
- [x] 线 3 多任务梯度冲突消解 / 取消同时性 —— **有先例（新颖性主张不成立）+ 存在反证**
- [x] 线 4 运行时状态触发切换 —— 无先例，且同一聚合问题上有方向明确的反证
- [x] 线 5 非平稳目标与反馈切换稳定性 —— 条件级反证，无构造性发散结果

## 本轮来源可用性

- Zotero：`Errno 61 Connection refused`，**去重检查未执行**
- Elicit：`api_access_denied`（套餐不含 API）
- 本地索引、Scholar Gateway、alphaXiv、scite、WebSearch/WebFetch：可用
