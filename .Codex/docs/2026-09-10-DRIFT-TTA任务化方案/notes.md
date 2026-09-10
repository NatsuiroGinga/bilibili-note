# DRIFT TTA 任务化方案 · 过程笔记（2026-09-10）

## 任务与身份

- 任务：按恢复卡"唯一下一动作"拟定 N13 测试时适应（TTA）的协议四项与 TENT 式最小证伪最小臂方案，落盘 `task_plan.md`。
- 身份：Sol 职责（纯文档）。**未实现、未运行、未改代码、未访问 T19–T25 数据。**
- 重派说明：前次同任务代理因配额 429 中断未交付；本次为重新派发。

## 本机读取顺序（均为只读）

1. `.Codex/docs/DRIFT/DRIFT第三章恢复卡.md`（全文）
2. `.Codex/docs/2026-09-09-DRIFT正锚点核查/task_plan.md` §八 与 `methodology-postmortem.md`
3. `.Codex/docs/DRIFT/DRIFT路线总控.md`
4. `thesis/methods/第三章-DRIFT数据角色与评价协议.md`
5. `.Codex/docs/2026-09-07-DRIFT方案A最小证伪实验/最小证伪实验计划.md`（格式与阈值惯例参照）
6. `wiki/papers/datasets/2026-Lee-DRIFT-DGA-Temporal-Drift.md`（行 87–156）
7. `wiki/papers/attack-detection/` 的 SoTTA、MADCAT、CANDI 结构化笔记
8. `wiki/papers/grpo/` 目录与变体选型笔记、若干全文的相关工作段

## 本次核验（真实命令与实测数字，均为只读）

| # | 命令/方法 | 实测结果 | 对方案的作用 |
|---|---|---|---|
| V1 | `rg -n 'BatchNorm'` 与 `'LayerNorm'` 扫官方快照 `model.py` | `LayerNorm` 由 `nn.TransformerEncoderLayer` 隐式提供，**`BatchNorm` 零命中** | 协议项③成立：不存在 BN 统计量等价选项 |
| V2 | 本机 `torch.load(..., weights_only=True)` 枚举 state-dict 键 | 总张量 `296`；总参数 `24,180,226`；LayerNorm 仿射张量 `96`（每支 48 = 12 层 × 2 × weight/bias）；**无 `encoder.norm`**；可更新参数 `24,576`（占 `0.1016%`） | 冻结更新对象与实施断言值 |
| V3 | `utility/dataset.py` 第 5–22 行 + `finetuning.py` 第 265–266 行 | `get_train_set()` 合并 T17–T19 的 `*_train` 与 `*_test` 十二个文件；微调脚本正调用该函数 | **发现口述规格的实质问题**：T18 `*_test` 属官方训练集 |
| V4 | 本机 `pyarrow.parquet` footer 行数 | T18 `val` 各 `150,000`（合 300k）；T18 `*_test` 为 `15,166,488` + `13,465,679` 行 | 修正最小臂流为 T18 `val`；并证明 T18 `test` 与 20–40 分钟预算不相容 |
| V5 | `rg` 全库检索 TENT／CoTTA／SAR | 仅命中原有路线文档的"计划"段落，**无原件、无笔记** | 全部标"待本地全文核验" |
| V6 | `rg` 全库检索 GTPO／GFPO／P-GRPO／LitePPO／GMPO | 前四者零命中；GMPO 仅 1 句被引 | GRPO 融合节逐项标注核验状态 |
| V7 | `rg` 全库检索 `ch3-drift-tta` | 零命中，无稳定键冲突 | 确定稳定键 `ch3-drift-tta-tent-ln-entropy-t18-v1` |
| V8 | 设备与预算依据复核 | 官方模型批量 `1024` 的既有入口跑在 **CUDA**（`ch3-drift-official-branch-conflict-t17-t18-t19-v1/result.json` 第 872 行 `"device": "cuda"`）；MPS 侧已验证批量是 `4096`（`positive_anchor_probe.py` 第 35 行）；正锚点核查的"20–40 分钟"是**运行前估算**，未取得实测墙钟 | 修正两处依据陈述：批量取 `1024` 并标为判定性超参；预算标为待实测确认的目标 |

## 本次相对派发简报的实质修正（须由用户裁决）

- **派发简报写"更新对象=全部 LayerNorm affine，T18 test 无标签流单 pass 在线适应"。核验后冻结流改为 T18 `val`。**
  理由：T18 `*_test` 在官方微调时即被 `get_train_set()` 并入训练（V3），在该数据上做适应与评价不能支持任何漂移适应主张；且其规模（约 2,860 万行）与 20–40 分钟预算相差两个数量级（V4）。
  处置：写进 `task_plan.md` §2.2 与 §零（D2），并列禁止令与三条独立证据；如用户仍要求 T18 `test`，须显式裁决并接受该读数的解释边界。
- **更新对象参数量由（结构推导的）25,600 修正为实测 24,576。** 差异来源：检查点无 `encoder.norm`，每支只有 12 层 × 2 个 LayerNorm（V2）。该值写入实施断言（§八）。
- **补入 C3–C6 保守护栏**（塌缩、噪声地板、非退化、操作点一致性）：只收紧、不放宽主判据 C1，标为 D4 交用户裁决。
- **主口径操作点明确为源冻结阈值**，默认 `0.5` 并列报告；阈值规则沿用本路线既有的"T17 `val` 良性分数 99% 分位 + 并列概率组整体选择"，不是新造数值。

## 决策记录

- 第一棒坚持**无额外状态**（无样本内存、无 EMA、无伪标签、无增强），把 SoTTA 的筛选内存、CANDI 的精选门、GFPO 式门控全部推到第二棒设计空间；理由是"最小证伪"要求失败可归因到单一机制。
- 到达顺序采用**严格因果在线**，并把 MADCAT 的"当月 70% 前视"写成明确对照反例（MADCAT 笔记已核）。
- 逐年复位（不跨年继承状态）冻结为第一棒口径；跨年持续适应归入 §六 第二棒，并要求与"逐年复位"同预算对照。
- 命名纪律单列一节（§5.4）：禁止把 TENT／CoTTA／SAR／GRPO 系名称用作本课题方法名。

## 未关闭项

1. TENT／CoTTA／SAR 全文核验（阻断 §2.3 的优化器与超参最终冻结，须在开跑前完成一次冻结修订）。
2. GRPO 系五个变体（GTPO／GFPO／P-GRPO／LitePPO／GMPO）原件与全文笔记。
3. 低误报数值预算（数据合同 §六 第 6 项）未关闭，源冻结阈值只是筛选口径。
4. T20 两个无后缀文件缺失，面板 28/30。
5. §5.2 机制的"保持标签语义的输入增广"视图族未定义。
6. 跨年持续适应在 T20–T25 上的信息协议未单独提交裁决。

## 交付与提交

- 新目录：`.Codex/docs/2026-09-10-DRIFT-TTA任务化方案/`，含本文件与 `task_plan.md`。
- Git：按任务要求只 `git add` 该目录并提交一次；工作树内其他未提交改动（含 `.Codex/docs/DRIFT/` 的恢复卡与总控修改）**不属于本次范围，不暂存、不提交**。
