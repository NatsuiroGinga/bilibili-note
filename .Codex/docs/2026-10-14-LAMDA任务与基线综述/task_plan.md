# 任务计划：LAMDA 任务与基线综述

- 日期：2026-10-14
- 代理：文献-LAMDA任务与基线综述（opus，effort=high）
- 工作树：`/Users/bilibili/personal/note/.worktrees/ch3-lamda-20260908`（分支 `exp/ch3-lamda-20260908`）
- 任务性质：**只读文献调研**，不跑训练、不跑大批量前向、不启动任何 MPS 任务。

## 目标

为学位论文第三章找一个**可做、有新意、能快速迭代**的研究任务，宿主数据集 LAMDA
（ICLR 2026，Android 恶意软件长期概念漂移基准，HF `IQSeC-Lab/LAMDA`）。
四条判据同时满足：指标提升空间（有数字）、工作量（撑起一章）、创新空间（指出具体空位）、
实验成本（分钟级一臂）。

## 交付物

1. `task_plan.md`（本文件）＋ `notes.md`（过程笔记，边做边写）
2. `literature-survey.md`：任务家族综述（Android 恶意软件时间泛化/概念漂移/持续学习）
3. `task-candidates.md`：2–4 个候选任务，逐条回答四判据
4. `baselines.md`：外部基线清单与证据等级

## 已确定的本地事实（直接引用，不重复调研）

- 速度：单年 train parquet 11–16 MB、约 7–10 万行、4,561 维稀疏二值特征；
  594,753 参数 MLP 全流程（训练＋多年评价）513 秒（MPS）。
- 标签正例率崩塌：2013 `51.35%` → 2017 `21.54%` → 2023 `14.52%` → 2024 `1.64%` → 2025 `0.05%`。
- 逐年 AP（安全记忆臂）：2020 `0.9965`／2021 `0.9973`／2022 `0.9986`／2023 `0.9743`／
  2024 `0.7515`／2025 `0.0555`（FNR 1.000）。余量全在正例率崩塌的年份。
- 发布特征空间用了未来协变量（`VarianceThreshold=0.001` 全年一次性筛选）⇒ 结论只能是 `screening_only`。
- 发布 train/test 是每年内部 80/20 分层随机，跨年任务必须自建切分。
- `vt_count` 列不能当特征（标签由 `vt_detection ≥ 4` 定义，用即泄漏）。

## 步骤与检查点

| # | 步骤 | 状态 |
| --- | --- | --- |
| 1 | 建目录、task_plan.md、notes.md | 完成 |
| 2 | 读本地已有 LAMDA 工作（综述、方案卡、筛选台账），记录已试/被否方向 | 进行中 |
| 3 | 本地混合索引检索（status + query --scope local --mode hybrid） | 待办 |
| 4 | Zotero 语义检索（LAMDA / 概念漂移 / Android 恶意软件时间泛化） | 待办 |
| 5 | 在线检索：引用 LAMDA / IQSeC-Lab/LAMDA 的工作（arXiv、OpenReview、PapersWithCode、HF） | 待办 |
| 6 | 在线检索：任务家族已发表方法（时间泛化、域增量、持续学习、概念漂移适应） | 待办 |
| 7 | 落盘 `literature-survey.md` | 待办 |
| 8 | 落盘 `task-candidates.md` | 待办 |
| 9 | 落盘 `baselines.md` | 待办 |
| 10 | 回报：文件路径、候选数、最有希望者与理由、最大不确定 | 待办 |

## 检索登记（每跑一组查询立即追加到 notes.md）

见 `notes.md` 的「查询式登记」节。

## 纪律

- 零命中先看 `warnings`，再 `rg -il` 复核，不得据零结果断言不存在。
- 摘要级证据不得写成可对比基线。
- 每完成一节立即落盘并 `git commit`（Conventional Commits，禁止 Co-Authored-By）。
- 不下最终裁决——选哪个任务由主代理与用户定。
