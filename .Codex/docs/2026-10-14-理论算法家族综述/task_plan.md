# 任务计划：理论／算法家族综述（LAMDA 第三章）

- 任务派发：2026-10-14，代理 `文献-理论算法家族综述`，模型 opus，effort high
- 工作树：`/Users/bilibili/personal/note/.worktrees/ch3-lamda-20260908`
- 产出目录：`.Codex/docs/2026-10-14-理论算法家族综述/`
- 任务空间已核定（不重查）：LAMDA 4,561 维二值特征、正例率崩塌（2013 51.35% → 2025 0.05%）、
  2024 FNR 34.59%／2025 FNR 100%、家族单例率 98.7%、跨年家族 Jaccard≈0.001–0.006、
  发布特征空间使用了未来协变量 ⇒ screening_only。
- 官方 8 条任务轴编号：①二分类+时间泛化 ②Domain-IL（15.8 点间隙）③Class-IL（154 家族）
  ④Task-IL ⑤家族分类/开集 ⑥主动学习/半监督适应 ⑦标签漂移 ⑧表示学习对比。

## 交付物

1. `task_plan.md`（本文件）
2. `notes.md`——查询日志与中间发现，边做边写
3. `families.md`——主表：理论/算法家族清单（家族名、问题、先例、理论保证、任务轴、成本、本地占据）
4. `ranked-shortlist.md`——按「一小时可证伪 + 真实余量 + 本地未占据」排前 5
5. `evidence-index.md`——证据索引（查询式、URL、证据等级）

## 步骤

- [x] S0 建目录与计划文件
- [ ] S1 读本地已占区域：`thesis/methods/` 关键文档（第三章定案、筛选台账、联合框架），
      `wiki/papers/**` 各方向 INDEX，确定「本地已被占据」清单
- [ ] S2 本地混合索引查询（在 ch3-drift-20260908 工作树跑，只查不写），
      覆盖 10+ 个家族方向的查询式
- [ ] S3 Zotero 语义检索，覆盖同批家族方向
- [ ] S4 在线检索（WebSearch / arXiv API / google-scholar 技能）补空白：
      重点 Android 恶意软件 + 时间漂移先例、DRO/保形/TTA/CL 在恶意软件上的应用
- [ ] S5 写 `families.md` 主表（目标 ≥25 条家族）
- [ ] S6 写 `ranked-shortlist.md` 前 5 条
- [ ] S7 写 `evidence-index.md` 并收尾提交

## 硬性纪律（自我约束）

- 只读：不跑训练、不跑大批量前向、不启动 MPS 任务。
- 每读完一篇或跑完一组查询立即落盘到 notes.md 并 commit。
- 检索顺序强制：本地混合索引 → Zotero → 在线。
- 严禁凭记忆列举论文；零命中先看 warnings 再 rg 复核。
- 不跑 black；不用 sleep 轮询；不写凭据；不用 pdftotext。

## 边界

- 另一位「任务与基线综述」代理负责任务轴/基线；本代理只做理论/算法家族。
- 不下最终裁决；产出为候选清单与可执行顺序，供主代理与用户裁决。
