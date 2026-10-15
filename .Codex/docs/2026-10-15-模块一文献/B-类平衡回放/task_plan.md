# B-类平衡回放：文献判读计划

- 日期：2026-10-15
- 代理：文献判读代理（Claude Opus / glm-5.3-flash）
- 任务边界：**只读本地已有全文，不跑任何实验**。本机 CPU 正在跑训练，禁止启动任何计算（训练、评价、张量操作一律禁止）。PDF 转换只允许走 MinerU API 模式（云端处理），不用本地 OCR。
- 研究问题：缓冲内的「类平衡／分层抽样」在持续学习／恶意软件漂移文献中有多少既有结论？有没有人做过「标签分层 vs 不分层」的直接消融？
- 我方设定（判读参照）：每个年度取 ⌊N/k⌋ 个位置，年度内部正负各半（正例不足由负例补足）。官方全局蓄水池不做标签分层；配额臂同时改了「年度间等额」与「年度内按标签分层」，两者未实验分离。

## 文件所有权

- 本目录 `task_plan.md`（本文件）、`notes.md`（逐篇笔记，读完即写）、`report.md`（最终裁决）由本代理独占。
- 只读访问：`raw/papers/attack-detection/lamda-related/*.pdf`、`wiki/papers/attack-detection/lamda-related/*-全文.md`。
- 转换中间文件放 `/tmp/b-class-balance-replay/`，不进 raw/wiki/output。

## 阅读清单（8 篇，按优先级）

| # | 原件 | wiki 全文笔记 | 状态 |
|---|---|---|---|
| 1 | 2020-Chrysakis-CBRS-Online-Continual-Learning-Imbalanced-Data.pdf | 无 | 待转换 |
| 2 | 2024-Park-PBR-Prior-Free-Balanced-Replay.pdf | 无 | 待转换 |
| 3 | 2025-Mohamed-MADAR-Diversity-Aware-Replay.pdf | 无 | 待转换 |
| 4 | 2025-Rahman-MADAR-Distribution-Aware-Replay-Malware.p.pdf | 无 | 待转换 |
| 5 | 2023-Amalapuram-ECBRS-PAPA-Continual-NIDS.pdf | 无 | 待转换 |
| 6 | 2023-Hemati-类增量学习中的重复.pdf | 有（全文 md） | 可直接读 |
| 7 | 2019-Aljundi-MIR-Maximally-Interfered-Retrieval.pdf | 无 | 待转换 |
| 8 | 2019-Wei-GSS-Gradient-Sample-Selection-Online-Continual-Learning.pdf | 无 | 待转换 |

## 每篇提取五项

1. 平衡/分层做在哪一层（类别层／任务层／两者）
2. 具体规则与公式（写出式子）
3. 有没有「分层 vs 不分层」直接消融？有则给数字与页码
4. 数据集与设定（在线？不平衡？存储约束？）
5. 证据等级与页码

## 验收

- report.md 逐篇五项齐全，含页码；未取得全文的条目单列。
- notes.md 在每篇读完后立即更新（不得攒到最后）。
- 结论区分「全文已核／仅摘要／未取得」，只给可回溯页码的判断。

## 状态与阻塞

- [2026-10-15] 计划建立。下一步：加载 pdf-converter 技能，确认 API 模式用法后批量转换。

## 状态更新（2026-10-15 完结）

- 8 份 PDF 全文转换成功（8/8，MinerU 云端 extract）；MADAR 两份经归一化 diff 确认为**同文异版**，实际独立论文 7 篇。
- 7 篇判读全部完成并即时写入 notes.md；report.md 已交付（总体裁决 + 逐篇五项 + 四问回答 + 页码核对表 + 未读条目单列）。
- 页码核对：13 项关键表格/公式回 PDF 原件核对完成（见 notes.md 末表）；1 项（Hemati Algorithm 3）未逐字定位，已在报告中标注。
- 遗留：ECBRS 补充材料（γ/缓冲消融）未读，报告中单列；后续如需「分层 vs 不分层」的进一步隔离证据可补读。
- 本机未运行任何实验或本地 OCR；全部转换走 MinerU 云端 API，符合任务约束。
