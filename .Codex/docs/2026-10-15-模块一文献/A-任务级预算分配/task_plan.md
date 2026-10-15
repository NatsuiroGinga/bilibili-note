# 任务计划：任务级/经验级记忆预算分配文献检索

- 日期：2026-10-15
- 代理：文献检索代理（Claude Opus）
- 约束：只检索与判读，不跑任何实验（本机 CPU 正在训练）；读 PDF 一律 pdf-converter（MinerU）
- 交付：本目录 `report.md`；入库论文落 `raw/papers/attack-detection/lamda-related/` 与 `wiki/papers/attack-detection/lamda-related/`

## 研究问题

固定容量 N=200 的缓冲**按已到达年度等额分配**（每年度 ⌊N/k⌋ 个位置，年度内正负各半）。
文献里任务级/经验级的预算分配有哪些做法？有没有最优性结论？有没有等额 vs 比例的直接对照？

**层次边界（不混）**：只查任务级/经验级分配；类级平衡（class-balanced）是另一代理的任务。

## 阶段

1. [x] 建目录、task_plan.md、notes.md
2. [ ] 本地盘点：Zotero 语义检索 + 本地混合索引（避免重复调研）
3. [ ] Google Scholar（scholar CLI，挂代理 HTTPS_PROXY=http://127.0.0.1:7890）多轮检索
4. [ ] 候选清单确定后逐篇取原文（arXiv / 出版社主站），pdf-converter 转全文
5. [ ] 每篇全文读完立即写 notes.md（查询式、出处、页码/公式、证据等级、与候选关系）
6. [ ] 确认有用的论文入库（raw + wiki 笔记 + INDEX.md 更新）
7. [ ] 写 report.md（候选表、公式移植、可证伪性、最小验证实验、未取得原文清单、裁决）

## 检索式清单（滚动更新）

- Zotero 语义：replay buffer memory allocation across tasks continual learning
- 本地混合索引：缓冲区 预算分配 / replay buffer budget
- scholar: "memory allocation" continual learning replay buffer tasks
- scholar: "samples per class" replay buffer continual learning
- scholar: reservoir sampling continual learning budget
- scholar: herding exemplar selection budget "number of samples per class"
- scholar: "memory management" continual learning "task budget"
- scholar: optimal memory allocation continual learning
- scholar: replay buffer "class-balanced" "task-balanced" allocation
- scholar: minimax / coverage / regret memory continual learning

## 候选与状态

（随检索滚动填写）

## 已知风险

- scholar CLI 需挂本机代理，直连 HTTP 000；失败先挂代理重试，禁止改用 WebSearch 替代
- 在线结果只作候选，核原文须在 arXiv / 出版社主站重新定位 ID
- 类级平衡文献极多，容易混入；每条候选必须标注它分配的「单元」是类别还是任务
