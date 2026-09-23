# DGA 对抗规避鲁棒组相对方案 · 过程笔记（2026-09-10）

## 任务与身份

- 任务：按用户 2026-09-10 裁决（病灶轴从“跨年概念漂移”切换为“DGA 对抗规避鲁棒”，方向原文“从 GRPO 家族提取机制”），起草新病灶方向的方案文档并登记。
- 身份：Sol 职责（纯文档）。**未实现、未运行、未改代码、未访问 T19–T25、未读 T20+ 数据。**
- 工作树：`/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908`（分支 `exp/ch3-drift-20260908`）。

## 本机读取顺序（均为只读）

1. `.Codex/docs/DRIFT/DRIFT第三章恢复卡.md`（全文）与 `DRIFT/AGENTS.md`、`DRIFT路线总控.md`
2. `thesis/methods/第三章-数据模型机制统一候选筛选台账.md`（格式参照；**该文件为 DRIFT 树当前唯一候选筛选台账**，任务书写的 `第三章-LAMDA候选方案统一筛选台账.md` 不在本工作树，实际位于 `ch3-lamda-20260908` 工作树）
3. `.Codex/docs/2026-09-10-DRIFT-TTA任务化方案/task_plan.md`（§十 三臂设计与 §5.2 机制证伪表述为写作参照）
4. `.Codex/docs/2026-09-07-DGA检测系统综述/文献综述.md` 与 `基线证据表.md`（病灶读数唯一来源）
5. `wiki/papers/grpo/INDEX.md` 与 GRPO／GFPO／SAPO／Simoni-GTPO／Tan-GTPO 五篇笔记（机制引用与核验状态）
6. `thesis/methods/第三章-朱焱雷第三章机制构思与创新声明分析.md`（检索段：DS／RGO 与公式位置）
7. `thesis/methods/第三章-DRIFT数据角色与评价协议.md`（数据角色与源期筛选口径）
8. `.Codex/docs/2026-09-10-文献入库-GRPO与TTA/notes.md`、`.Codex/docs/2026-09-10-RL家族盘点/notes.md`（家族入库与纠错状态）

## 本次核验（真实命令与实测结果，均为只读）

| # | 命令／方法 | 实测结果 | 对方案的作用 |
|---|---|---|---|
| V1 | `git status --short -- .Codex/docs/DRIFT/` + `git ls-files .Codex/docs/DRIFT/` | 恢复卡与总控**已跟踪且干净**；`AGENTS.md`／`CLAUDE.md`／`DRIFT历史交接入口.md` 为未跟踪 | 确认 HEAD `bfffe64` 即恢复卡的改前快照，无需空提交 |
| V2 | `git diff --cached --name-only` | 暂存区为空 | 可安全做快照与提交 |
| V3 | `fd -t f 'LAMDA'`／`ls thesis/methods/` | 本工作树**无** LAMDA 台账；DRIFT 树仅有 `第三章-数据模型机制统一候选筛选台账.md`（其 §零 为“DRIFT 活动区”） | 确认 DRIFT 侧候选登记位 = 恢复卡 §五（按路线规则，新 DRIFT 状态收敛到路线链，不回写台账矩阵） |
| V4 | `rg -n 'N15'` | 第三章序列当前用到 `N14`；`N15` 仅出现在第四章基线清单（不同编号体系） | **本次不新造编号**：登记以机制描述名为主，编号是否补 `N15` 由主代理裁决 |
| V5 | `rg -l -i` 两关键词 `charbot`、`maskdga` 扫 `wiki/ raw/ --no-ignore` | 命中原件 `raw/papers/attack-detection/2019-Peck-CharBot.pdf`、`2019-Sidi-MaskDGA.pdf` 与短笔记 `wiki/papers/attack-detection/dga/2019-*.md`；**`git status` 显示该目录整体未跟踪** | 病灶原文入库确实**进行中**；方案只引综述读数，原文页码锚点标“待补” |
| V6 | `rg -n '对抗' thesis/methods/第三章-数据模型机制统一候选筛选台账.md` | 仅 `N03 跨架构稳健表示` 一行含“域对抗”，与 DGA 规避无关；台账矩阵**无对抗规避候选** | 确认本方向不是既有候选改名 |
| V7 | 综述逐行定位 | E1–E4 读数在综述 §1 第 4 条（文件第 10 行）、§5.3（第 123 行）、§7（第 171 行）、§8 第三类候选（第 195 行）、§10.4（第 254 行） | 方案 §二 的出处可回指 |
| V8 | 基线证据表 `rg` | CharBot/MaskDGA 行：无时间角色、攻击从良性或 DGA 字符串构造、非开放集协议、CharBot 明确在 0.1%/1% FPR、无多种子区间 | 评价口径差异必须随引用转述 |
| V9 | `shasum -a 256 runs/models/drift-official-dsn2026/finetuning.pt` | `090e5f844492ee532f72f8b1db1cb335bf67c9468fd2e0329344fe209b5969c3`，与 N13 TTA 方案 §2.2 记录一致；文件存在（96.8 MB） | P0 对象与模型身份可核，写入 §5.1 |
| V10 | `git log --oneline -3`／`git show --stat` | 提交 `03f0225` 仅含本次 3 个文件（2 新增 + 恢复卡），无 Co-Authored-By，未夹带他人改动 | 交付核验 |
| V11 | 读取 `p2p3-result-DRYRUN.json` 逐字段 | 三臂 `adv_AP` 均 `1.0`；`P2_pass=false`／`P3_pass=false`；`n_params=133,954`（≈ `0.134M`；**主代理裁决以制品为准**，简报口述与脚本 docstring 的“约 0.4M”均为口径错误） | 登记为 §5.5 P-E2 |
| V12 | `git status --short -- wiki/papers/attack-detection/dga/` + `git ls-files` | CharBot／MaskDGA／Drichel 三篇**全文笔记已被 `8b8c597` 提交**（其余 2026-09-07 短笔记仍未跟踪） | §二 E1–E3 与 §七 依赖表状态刷新 |
| V13 | `rg '2404\.06236'` + 读全文笔记 | Drichel 2024 = 离散扰动对抗训练的**已发表先例**：联合 AT 优于仅嵌入空间 AT `10.15%`、优于仅离散域 AT `3.6%`（p.10）；笔记明确要求“任何新方案必须说明相对本文的增量” | §6.4 查重节 |
| V14 | 逐节读 Drichel 笔记 §4.4（p.7） | 其三种 AT 均为**标准对抗样本训练**：批次按攻击等量取样、随机交替两类批；**无熵项、无组相对重加权、无连续信任域软门**（相近的只有扰动预算随机化） | §6.4 三组件对照表；差量归位到求解器机制 |

## 本次相对派发简报的登记项（不改变任务范围）

- **病灶原文的入库位置与状态已实测**：简报写“MaskDGA/CharBot 原文由另一代理入库，页码锚点待补”。实测确认：原件与短笔记**已存在于本工作树但未提交**（2026-09-07 建立）。方案据此写“入库进行中、页码锚点待补”，并额外声明**未提交笔记不得支撑正文级论断**——比简报更严，未放宽。
- **候选登记位已核**：简报要求先确认 DRIFT 树是否另有台账。结论：DRIFT 树无独立候选登记册；`第三章-数据模型机制统一候选筛选台账.md` 的 DRIFT 活动区仍属 DRIFT 树，但按 `DRIFT路线总控.md` §六“新 DRIFT 状态应逐步收敛到本路线链”，本次**只登记恢复卡 §五／§六**，不新增台账矩阵行。
- **数据合同未变**：本方向不依赖跨年结构，但最小臂仍按源期 `screening_only` 口径（T17，单种子），未触碰 T20+。

## 与主代理 2026-09-10 裁决的一致性核对

| 裁决要点 | 方案落位 | 是否一致 |
|---|---|---|
| 病灶轴切换为 DGA 对抗规避鲁棒 | §1.1、§零 D1 | 一致（正式化本身列为 D1 待裁决） |
| 数据复用 DRIFT 域名、任意年份 | §1.1、§5.2（T17 单年） | 一致 |
| 四机制映射（组相对／熵受控／信任域／子集过滤） | §3.1 映射表、§3.3–§3.6 | 一致，且每个机制标了核验状态与“本课题推论”身份 |
| 与朱的边界必须写扎实 | §4.1（五维对照表） | 一致 |
| 查重：MaskDGA 对抗训练消融／CharBot 重训 | §4.2、§4.3 | 一致；受原文入库阻断，当前只到综述可支撑的粒度 |
| 三臂设计（静态／朴素对抗／＋组相对） | §5.2 | 一致，并补入公平算力对照与噪声地板门 |
| 判据冻结“对抗 F1/TPR 改善且干净 FPR 不增”，数值待病灶复现后定 | §5.3（G2／G3 结构先写、数值后冻） | 一致 |
| 停止条件：朴素对抗训练无信号则组相对不加 | §七.2 | 一致 |

## E-A1 v2 病灶复现完成（2026-09-10 增量登记）

**裁决：病灶坐实。** 由主代理按冻结判据裁决，本轮只登记读数与脚本演进，不改判据。

### 一、读数（`ea1-result.json`，本机复核逐字段一致）

- 标定（良性流 `T18_benign_val` 1.5 万）：FPR=1% 阈值 `0.831275`；FPR=0.1% 阈值 `0.990418`；参考口径 `score<0.5`。
- 干净 DGA 检出率：`96.36%`（FPR1%）／`83.74%`（FPR0.1%）。
- 对抗变体（各 1.5 万，种子 `42`）：
  - **CharBot 2 位替换**：检出率 `64.00%`／`54.92%` → **相对降 `33.6%`／`34.4%`**；
  - **MaskDGA 半替换近似**：检出率 `29.81%`／`22.82%` → **相对降 `69.1%`／`72.8%`**；
  - `score<0.5` 参考口径同向：CharBot 降 `27.7%`、MaskDGA 近似降 `60.9%`。
- **判据**：`best_relative_drop = 0.6906 ≥ 0.5` → **病灶坐实**；三个工作点方向一致（无符号冲突）。制品：`e-a1-v2.py`、`ea1-result.json`、`ea1-v2-console.log`（均在本目录，**当前未跟踪**）。

### 二、脚本演进史（登记，供后续复用与防再犯）

| 版本 | 状态 | 问题 | 处置 |
|---|---|---|---|
| `e-a1-attack-success-probe.py`（v1） | 未用于出数 | ① **四算子自造**，不对应 CharBot 原文的单算子定义（攻击面不忠实）；② 缺 `inference_mode` 包裹，带梯度前向导致 MPS OOM／长时不可跑 | 由文献代理按**页码级原文核验**修正算子定义；OOM 根因诊断（`branch_features` 缺 `inference_mode`，仓库既有 `extract_features`／`evaluate` 均有包裹）**采纳执行代理结论** |
| `e-a1-v2.py`（v2，出数版） | **已出数** | **文献忠实算子**：CharBot 取 2 位替换；MaskDGA 取**半替换近似**（并显式标为近似，非原文算子复现） | 本表与 task_plan §二 E8、§5.1 执行结果行同步登记 |
| `diag-1..4-*.py` | 诊断脚本 | 批量—内存标度、no-grad 稳定性、梯度 vs no-grad 数值、numpy-on-grad 检查 | 支撑 OOM 根因与数值等价判断（数值差最大绝对值 `8.35e-07`、`0` 次 `0.5` 判定翻转） |

**边界（必须随引用转述）**：MaskDGA 臂是**半替换近似**、CharBot 臂是 2 位替换；单种子、单年、`screening_only` 口径；**不得**把 E-A1 v2 写成"已复现 MaskDGA 原法"或跨年结论。

## P2／P3 proxy 干跑与博弈论定位登记（2026-09-10 增量二）

### 一、P2／P3 proxy 干跑（登记进 task_plan §5.5）

- 制品：`p2p3_grpo_proxy.py`、`p2p3-result-DRYRUN.json`（本目录，**均未跟踪**；本次干跑**未落盘 console log**）。
- 结果：`--dry-run 2000`，字符 CNN（`n_params=133,954`）三臂 A／B／C 的**对抗 AP 全部 `1.0`** → `P2_pass=false`、`P3_pass=false`（**无信息**：判据无空间，不是对机制层的否决）。
- 根因（登记）：E-A1 的病灶是 24.2M 官方 Transformer 的属性；`0.134M` CNN proxy 的局部感受野＋池化对 CharBot 2 位替换天然鲁棒，**病灶不继承**——proxy 比口述的“0.4M”小约三倍，**该归因因此更强**（主代理 2026-09-10 裁决）。
- 四个修正方向 (a)–(d) 与主代理倾向 (d)＋(a)、下一步 1–3，均已登记进 §5.5。
- 注意：简报口述“0.4M 参数字符 CNN”与制品 `n_params=133,954` 不符，**以制品为准**（脚本 docstring 亦写“约 0.4M”，登记为文档不一致）。

### 二、博弈论定位与求解器差量（登记进 task_plan §六）

- 定位：`min_θ max_a L`，离散域字符梯度无定义、PGD 式内层不可用；MaskDGA（代理模型＋显著度、半替换）、CharBot（无梯度、两字符替换）、Drichel（嵌入空间攻击＋可控离散化）三例为证。
- 求解器：GRPO 家族结构与本问题同型（组采样＝攻击者动作尝试、组相对优势＝哪些扰动骗过检测器、熵受控＝对未见扰动族的探索、信任域软门＋子集过滤＝外层更新）。
- 与朱**机制族不同**：朱＝连续 PGD 轨迹＋RGO 展开优化（梯度可用域）；本方案＝离散组采样＋组相对聚合（梯度不可用域），**不是同一方法换域**。
- Drichel 2024 查重（正面命中）：三组件“是否使用”逐条判定（**均未使用**）见 §6.4；差量只能落在求解器机制，且若要主张“优于其标准交替训练”，必须以**其复现形态为对照臂**实测。
- 分层路线图 P2（固定攻击者）→ P3（组相对求解器）→ P4（MARL 双侧学习，仅 P3 过门后投入；P4 文献线索登记为**待入库**，不得引用）。

### 三、原文入库状态刷新（本次同步）

- CharBot／MaskDGA／Drichel 三篇**全文笔记已入库并提交**（commit `8b8c597`，含页码锚点与算子精确形式），`wiki/papers/attack-detection/INDEX.md` 同步。
- 据此把 §二 E1–E3 的“原文入库进行中”改为“全文笔记已入库”，§七 依赖表第 1／2 项关闭并新增第 5 项（Drichel），§4.2／§4.3 补入已核验的防御消融数字。
- 阻断点转移：从“原文未入库”转为“**P2／P3 proxy 无空间待修正**（§5.5）”与“判据数值门未冻结（§5.3）”。

## 判据统一与精读移交（2026-09-10 增量三）

### 一、P0 判据口径统一裁决（主代理 2026-09-10）

- **裁决**：以 **E-A1 v2 的 `relative_drop ≥ 0.5`** 为准；恢复卡 §五 的旧判据行（ASR ≥ `0.30` 坐实／< `0.10` 降级、`score<0.5` 口径）**订正**。
- **版本链（如实登记，不隐瞒判据曾变更）**：v1 冻结 `score<0.5` → 文献代理**页码级核验确认该口径无文献对应**（CharBot §V p.5 的规避评价用 FPR 标定阈值口径）→ **升级为 v2 `relative_drop ≥ 0.5`**（有 CharBot §V p.5 锚点）→ v2 出数。
- **不构成“看结果后改判据”的依据**：判据升级**发生在 v2 运行之前**，且 **v1 从未产生任何读数**（v1 脚本 `--dry-run` 以 OOM 追溯到缺 `inference_mode`，见上文脚本演进史）。
- 落位：恢复卡 §五 §六 订正；task_plan §5.1 新增“判据口径版本链”行；本节为过程详录。

### 二、参数量修正（主代理裁决）

- 以**制品**为准：`n_params = 133,954`（≈ `0.134M`）。简报口述“0.4M”为转述错误，脚本 docstring 同错；proxy 实际比口述小约三倍，**“proxy 不继承 24.2M 模型病灶”的归因因此更强**。
- 落位：task_plan §5.5.2 根因行、notes 本文件 V11 与增量二·一。

### 三、Drichel 2404.06236 精读移交（不在本代理范围）

- 主代理裁决：精读任务**移交文献代理 `ab7083c2`**（其上下文含 CharBot／MaskDGA 原文核验经验）。**本代理不写精读结论**（不抢跑），只在其结论交付后更新 task_plan §6.4 查重节。
- 精读五项问题（(a) 联合 AT 精确形式与交替轮次；(b) 32 种攻击清单是否覆盖 CharBot 2 位替换与 MaskDGA 半替换；(c) 评价协议（FPR 工作点、干净护栏）与三臂的差异；(d) 是否使用组相对／熵受控／信任域任一机制；(e) AT 后干净指标代价）已登记进 task_plan §6.4 的“精读状态”段。
- **臂 C 冻结前置**：若 Drichel 已用组相对或等价机制 → 臂 C 重新设计；若未使用 → 差量成立、臂 C 按 §5.2 现设计冻结。
- 本代理已执行的辅助动作（可复用）：用 MinerU `extract` 模式转换原件 —— `mineru-open-api extract raw/papers/attack-detection/2024-Drichel-Robust-DGA-Classification.pdf -o /tmp/drichel-2024-extract/ --language en`（7.9 s，产出 `2024-Drichel-Robust-DGA-Classification.md` ＋ `images/`，`/tmp` 可丢弃中间产物）。**未读取与分析其内容**，仅登记路径供文献代理按需复用。

### 四、文档结构裁决（用户 2026-09-10，覆盖此前分散写法）

- 对抗鲁棒方向**只保留两个文档**：① 方案文档 = `task_plan.md`（含候选机制筛选清单、博弈论定位、Drichel 查重、三臂与判据等全部章节）；② 实验计划文档 = `notes.md`（滚动实验计划与进度）。
- 两文档均链接在恢复卡；**后续所有更新在原文件内原地更新，不再新建第三份文档**（本 notes 的“增量一／二／三”节即为该纪律下的原地追加）。

## 创新定位节与用词统一（2026-09-10 增量四）

### 一、新增 §七「创新定位：训练过程组织层（朱焱雷方法论同构）」（主代理裁决）

- 与 §6.4 Drichel 查重节并列：查重界定“已被占用什么”，本节界定“创新落在哪一层”。
- §7.1 登记朱的方法论五条（换评价切面／成熟家族不重造、创新取组织层／两组件正交耦合可分别关闭／固定对标锚／边界明写“不是新损失”），出处逐条指向[朱分析文档](../../../thesis/methods/第三章-朱焱雷第三章机制构思与创新声明分析.md)与[对位表](../../../thesis/methods/第三章新四格-朱论文对位表.md)行号；**“饱和／切面”的概括标为主代理映射**，不写成朱原文表述。
- §7.2 同构映射表：评价切面 ↔ 规避检出率（本课题实测相对降 `69.1%`）；成熟家族 ↔ 对抗增广训练（不重造）；创新层一 ↔ **组相对信用分配**；创新层二 ↔ **熵受控＋信任域软门**；对标锚 = CharBot `5.58%` → 量化相对 `55.19%` 的差距（**只作量级参照，不是判据**）。
- §7.3 三重差异（离散字符域 vs 连续扰动域；GRPO 家族求解器 vs RGO 展开优化；DRIFT/DGA vs 加密流量域）——**相同的是创新层位置，不是机制本身**。
- §7.4 与 Drichel 的关系：两层正交（其占“对抗训练有效性”，本方案占“过程组织层”），正交性以“Drichel 未用组相对等机制”为前提，精读结论交付后重估。
- §7.5 命名统一：§5.2 臂 C 与 §6.5 的 P3 层统一为**“组相对信用分配＋熵受控对抗训练”**。
- 章节重编号：新 §七 之后，原文入库依赖→§八、停止条件→§九、开放问题→§十、证据入口→§十一，内部引用同步（6 处）。
- **纪律**：朱分析文档行 181 明确“不照抄 `4.2%–8.6%`／`+9.30/+12.30` 作为门槛”，已在 §7.1 原样保留该约束。

### 二、用词统一（用户裁决）

- 裁决：一律用**“GRPO 家族机制（层）”**，不用单数“GRPO 机制／GRPO 求解器”——本方案引用的是 32 条目全谱系的机制原理（组相对优势→GRPO 原文；熵受控→GTPO 变体；信任域→SAPO 软门；子集过滤→DAPO/GFPO）。
- **修正处数：0**。逐条核查两文件的全部 GRPO 提及：均为“GRPO 家族”“GRPO 原文”“Dr. GRPO”“GRPO-S”或“PPO／GRPO 策略优化循环”等不窄化文献依据的写法，**未发现单数“GRPO 机制／GRPO 求解器”表述**。本轮仅把 P3 层的“组相对求解器”按 §7.5 统一为“组相对信用分配＋熵受控对抗训练”（属命名统一，非用词纠正）。

## 章节规划节（2026-09-10 增量五）

### 新增 §八「章节规划：第三章／第四章的机制分配策略」（用户裁决）

- **分配原则**：完整框架 `P2 → P3 → P3.5 → P4` 的工作量若超过朱第三章对标线，则第三章只承载主干（P2 朴素对抗训练基线 ＋ P3 组相对对抗优化＝统一主方法「组相对信用分配＋熵受控对抗训练」），**P3.5（学习型攻击者资格门）＋ P4（双侧共演化／league 稳定化）整体移入第四章**。
- **承接逻辑**：第三章末按参照论文体例声明“固定对手下已达增益，真实攻击者会适应检测器” → 第四章引入学习型攻击者与共演化，解决“对手建模深度不足”。**定性为缺陷导向的承接、框架的自然升级，不是残次品补救**。
- **两章合同边界**：第三章 = 固定攻击者 ＋ 组相对机制（单数据集单协议，既有预算可完成）；第四章 = 学习型攻击者 ＋ 双侧学习稳定化（MAB-Malware 式资格门 → PSRO／league 稳定化）；两章**共用 DRIFT 数据与组构造器**。
- **优先级**：P2／P3 = 第三章主干（最高优先，当前 proxy 全量与官方版三臂均属此范围）；P3.5／P4 = 第四章主体（第三章成稿后启动）。
- **前提声明**：以 **P2／P3 过门**为前提，若失败则第三章主干重设计、本分配作废重议。
- 配套改动：§6.5 路线图升级为 **P2 → P3 → P3.5 → P4**（新增 P3.5 行与“归属”列，P4 增列 PSRO／league 稳定化与 P3.5 前置）；后续章节顺次重编号（依赖→§九、停止条件→§十、开放问题→§十一、证据入口→§十二），同步 6 处内部引用。
- **未决登记项**：§8.3 引用的“**四级先例表**”（主代理原话指其 “report (8)”）在本工作树内**检索零命中**（`rg -i '四级先例|PSRO|league|MAB-Malware'` 只命中无关语料），已标“**出处待登记**，补登记前不得引用其中具体先例”。

### 成本分工追加（用户 2026-09-10 追加，写进 §8.6）

- **代价登记**：臂 C 训练成本显著高于臂 B（组相对评分的额外前向）。**制品复算为主口径**：`p2p3-result.json` 的 `wall_seconds` A／B／C = `103.6/159.1/655.7 s` → **C／B = `4.12` 倍**（C／A = `6.33`、B／A = `1.54`）；逐 epoch 训练段墙钟和 C `655.0 s` ／ B `158.4 s` = `4.14` 倍（`p2p3-console.log`）。**主代理口述值 `4.4` 登记备查**，与制品差 `0.28`，引用一律以制品复算值为准。**官方模型上的比值待官方三臂登记**（官方版目前仅有 A 臂干跑 `official-p2p3-DRYRUN.json`，6000 样本 1 epoch `98.4 s`，无 B／C 对照）。
- **P-E3 登记（proxy 全量完成）**：12 万训练样本、6 epochs、评价干净 1.5 万／对抗 7500；三臂 `adv_AP` 仍全 `1.0`、`P2_pass=false`／`P3_pass=false`（**仍无信息**，非机制否决）；干净 FPR `0.0288/0.036/0.0488`（A／B／C）、对抗 FNR `0.0969/0.03/0.0228`。制品 `p2p3-result.json`、`p2p3-console.log`。**算子未换**（仍是 CharBot 2 位替换），故 §5.5.3 的 (d)＋(a) 路线仍待裁决执行；§5.5.4 已标注当前处于“proxy 仍无空间 → 上报 (b)／(c)”分支入口。
- **三条分工**：① 第三章判据**不含成本项**（G2／G3 文本不变，成本只作报告量）；② 第四章议题新增「组相对采样的效率优化」（增量计算与缓存／小批量评分／评分与训练流水线重叠）；③ 第三章末边界声明追加「组相对信用分配的额外计算成本为已知代价，其优化见第四章」。
- **结构同构**：朱第三章的对抗生成与展开优化同样成本高昂，效率议题正是其第四章内容。
- **纪律**：不改变 §5.3 判据门；若要把成本纳入第三章门，须先经用户裁决并同步改 §5.3 与 §8.5。

## 臂 C 机制措辞修正（2026-09-10 增量六，用户裁决）

- **裁决**：臂 C 组相对加权的登记措辞由“**无文献依据的任务化设定**”改为「**无先例的任务化机制（新颖性空间）**」——GRPO 家族的组相对思想（**组内相对优势替代绝对损失阈值**）从 LLM token 级迁移到**扰动组级**，这正是**机制提取**；“无先例”是**新颖性空间本身**（差量 = Drichel 均匀混合 ＋ 本方案加权），**不是依据缺陷**。
- **两面必须同时写**：①「无先例（新颖性空间）」＋ ②「实验验证路径（P3 判据：加权后对抗检出改善且干净 FPR 不增）」；该机制**不需要文献背书作为“标准做法”**。
- **类别区分**：EATA 式熵阈值属“**所解决的问题不存在**”（有监督设定下“该变体是否骗过当前模型”是直接可观测量）→ **不加**结论不变；本条的组相对加权属“**问题真实存在但无先例**”→ 登记为待验证差量。两类不混用同一套措辞。
- **三处已统一**：① 文献入库笔记 Q4 登记（`.Codex/docs/2026-09-10-DGA对抗文献入库/notes.md` §17）；② 本目录 `task_plan.md` §5.2 臂 C 行下方新增“臂 C 机制的性质”条；③ §7.2③ 创新层一行的证据状态格。

## LLM 生成 DGA 空白定位（2026-09-10 增量七，用户裁决）

- **新增 §6.5a「LLM 生成 DGA 的空白定位」**（位于 §六 内、§6.5 路线图之后、§6.6 表决状态之前）：
  - **空白定位**：arXiv 检索未获——“用 LLM 生成恶意域名以规避检测”**尚无正式论文**；已发表生成式规避仍属 **GAN 系**（DomainGAN `1911.06285` 等），CharBot／MaskDGA 为字符扰动族；两条流行线索被证伪（“LADB”＝扩散模型域迁移；“MaskDGA＝BERT-style”被全文精读证伪为 JSMA 字符替换）。
  - **三点含义**：(a) 是否作为**第三个攻击算子族**＝**开放问题不预设**（LLM 生成是低熵词形模仿，与扰动近邻分布的攻击面不同，不能默认并入同一组构造器）；(b) 对 `69.1%` ASR 病灶是**加强**，但**只是推理不是实测**；(c) 若纳入须先冻结生成成本与评测协议（推理成本／可解析性约束／与 CharBot 同工作点比较）。
  - **登记性质**：空白定位＝**动机强化**；纳入＝**待 P3 过门后裁决**，**不得写成“已纳入”**，不得据此改判据门或停止条件。
- **依据指向**：恢复卡「文献综述更新」节的《LLM 生成 DGA 攻击文献盘点（2026-09-10）》（12 个检索式逐条核验；主代理已验收存在）——方案节只指向、**不重复其检索表与正文**。
- **配套**：§十一 开放问题新增 7a 条（第三个攻击算子族的开放登记）；§十二 证据入口的恢复卡条目补注 §6.5a 依据锚点。

## 遗留与未完成项（登记，不含结论）

1. ~~MaskDGA／CharBot 原文入库进行中~~ → **已关闭（2026-09-10，commit `8b8c597`）**：三篇全文笔记（CharBot／MaskDGA／Drichel）入库并提交，页码锚点齐备。
2. **P0 病灶复现已完成（2026-09-10，E-A1 v2）**：本课题数据上该病灶实测读数由 **0 条** 更新为 **1 条**，裁决【病灶坐实】；见上文对应节。
3. **数值门冻结仍待主代理执行**：§5.1 通过门与 §5.3 的 G2／G3 数值此前明确“读数出来后一次冻结”，本次只登记读数、不代冻。
4. **P2／P3 proxy 硬伤待修正**：干跑 `adv_AP` 三臂全 `1.0`、判据无空间；修正方向 (a)–(d) 与主代理倾向 (d)＋(a) 已登记，**待主代理裁决与执行**（若走 (c) 需用户豁免 ≤1M 本机规则或服务器开机）。
5. 熵受控方向（低熵 vs 高熵）未定，前置诊断未设计。
6. 扰动族定义（合法域名字符集、TLD、长度）与“未见扰动族”的族划分未定义；若按 (a) 增强攻击强度（4–8 位替换），该强度须登记为**非 CharBot 原文算子**的校准参数。
7. 恢复卡 §一 Goal 与路线总控“当前目标”仍写时间漂移口径，属 D1／D6 待裁决，本文件未擅自改写。
8. **制品跟踪状态（已更新）**：E-A1 v2 三项制品、四个诊断脚本、v1 脚本，以及 P2／P3 的 `p2p3_grpo_proxy.py`／`p2p3-result-DRYRUN.json` **已随本目录入库**（commit `3a79cff`，13 文件；`__pycache__` 由 .gitignore 排除）。
9. **P4 文献线索未入库**（李艺春 2025、杜威 2019、罗彪 2025、Hernandez-Leal 2019、Tampuu 2017、Tan 1993、Lowe MADDPG 2017）：题录／全文／页码均未核验，**不得引用**，投入 P4 前须完成入库。
10. **Drichel 精读待交付（前置臂 C 冻结）**：由文献代理 `ab7083c2` 进行中；task_plan §6.4 已标“基于笔记级核验、未精读”，精读结论交付后由主代理裁决并回填页码锚点。

## H 臂前置核验：RLOO 定理与误报注入近邻（2026-09-10）

> **本节核验执行日期为 2026-09-11**（节标题沿用任务书给定字面串，便于检索）。本节只登记文献核验结果，不构成任何已支持机制、已批准方向或已冻结判据；判据数值门仍待主代理冻结。
> **覆盖范围**：任务 1（RLOO 组内基线定理精确核验）、任务 2（误报注入攻击近邻检索）。

### H.1 RLOO（arXiv 2402.14740）组内留一基线定理核验

**核验物件**：原件 `raw/papers/grpo/2024-Ahmadian-Back-to-Basics-RLOO-REINFORCE-Style.pdf`（*Back to Basics: Revisiting REINFORCE Style Optimization for Learning from Human Feedback in LLMs*，Ahmadian 等，arXiv:2402.14740v2，28 页）。既有笔记：`wiki/papers/grpo/2024-Ahmadian-Back-to-Basics-RLOO-REINFORCE风格.md`。

**核验方法（证据等级：MinerU 全文 + 逐页复核）**：MinerU `extract` 模式全篇转 Markdown（产物 `/tmp/rloo-mineru/`，一次性中间物，不入库）；页码用 `pypdf 6.18.0` 逐页文本索引独立复核。**印刷页码 = PDF 页码**（逐页页脚实测：PDF p.5 页脚 `5`、p.6 页脚 `6`、p.13 页脚 `13`）。

#### H.1.1 留一均值基线的精确定义与公式

| 项 | 核验结果 | 页码锚点 |
| --- | --- | --- |
| LOO 估计量主式 | `(1/k) Σ_{i=1}^{k} [ R(y_(i),x) − (1/(k−1)) Σ_{j≠i} R(y_(j),x) ] ∇logπ(y_(i)\|x)`，`y_(1..k) ~i.i.d. π_θ(·\|x)` | **§2.3，p.6**；**该式在原文无编号** |
| 基线本体 `b_LOO` | `b_LOO(y_(i)) = (1/(k−1)) Σ_{j≠i} R(y_(j),x)`，即**其余 k−1 条**样本奖励的均值 | p.6 |
| 一般基线减除式 | `(R(y,x) − b)∇logπ(y\|x)` = **式(7)** | p.6 |
| 全局移动平均基线 | `b_MA = (1/S) Σ_s R(x^s,y^s)` = **式(8)** | p.6 |
| 式(6) REINFORCE 梯度 | `E[R(y,x)∇logπ_θ(y\|x)]` | p.5 |

**⚠️ 对既有 wiki 笔记的更正（必须登记，防复发）**：`2024-Ahmadian-Back-to-Basics-RLOO-REINFORCE风格.md` 第 17、46 行写「RLOO 估计量（**式(9)** 附近，§2.3，**p.5**）」。经原件双路径抽取（MinerU + pypdf）核验：

1. **§2.3 位于 p.6，不是 p.5**（p.5 是 §2.2 REINFORCE 与式(5)(6)）。
2. **RLOO 估计量在原文没有编号**——公式后直接接 `Where k refers to...`，无 `(9)` 标签。
3. **式(9) 实际在 p.8**，是 Vanilla PG 的「轨迹回报 − 学习基线」优势项 `Σ_{t} γ^{T−i−1} R_t(x,y_t) − b_φ(s_t)`（`b_φ(s_t)` 为学习到的价值网络基线），**与 RLOO 无关**。

该误链会把「学习基线（有偏的价值网络）」与「无参留一基线（无偏）」两类完全不同的基线机制混为一谈，是 H 臂理论表述的直接风险源。**该笔记的 `method` 与「机制」两处锚点已按本次核验就地更正**；`key_finding` 字段未含方程编号，无需改动。

#### H.1.2 无偏性陈述：原文有无正式命题／推导

**结论：没有。** 全文不存在针对 RLOO 无偏性的命题、定理、引理或附录推导；只有三处**散文级**陈述：

| 位置 | 原文陈述（摘） | 性质 |
| --- | --- | --- |
| p.5（式(7) 上下文） | "...reduce the variance of the estimator in Eq. 6, **while keeping it unbiased**, by subtracting a baseline b that has high covariance with the stochastic gradient estimate of Eq. 6 (Williams, 1992; Mnih & Gregor, 2014)" | 断言 + 转引 |
| p.6 | "...can be used for further **unbiased variance reduction**" | 断言 |
| p.6 | "uses the remaining k − 1 samples to create an **unbiased estimate of the expected return** for the prompt, akin to a parameter-free value-function, but estimated at each training step" | 断言 |

- **前提条件**：原文未显式列出。可核到的唯一结构假设写在公式尾部的 `y_(1),...,y_(k) ~i.i.d. π_θ(.|x)`（p.6）；`E[∇logπ]=0` 与「跨样本独立性使交叉项为零」这两步**原文没有写出来**。
- **方法出处**：RLOO 估计量被明确归给 **Kool et al. 2019, "Buy 4 REINFORCE Samples, Get a Baseline for Free!"（DeepRLStructPred@ICLR）**，见 p.6 正文与参考文献（p.19–20）。**该文原件不在本仓库**，本次未检索、未核验其定理。
- **能否作为我们 proposition 的引用依据**：**不能（证据不足）**。2402.14740 只能被引作「该文如此陈述／沿用 Kool 等的结果」；本课题正文若要写「留一基线减除不引入偏差」的正式命题，只有两条路——(a) **自证**（如下 H.1.4 的两步推导，本代理已给并已数值自检），或 (b) 取得 Kool 2019 原文后引其定理与前提。

#### H.1.3 方差缩减陈述：形式化 or 实证

**结论：无形式化论证，只有直觉陈述 + 一条经验表格。**

| 类型 | 内容 | 位置 |
| --- | --- | --- |
| 直觉陈述（唯一） | "resulting in a **variance-reduced multi-sample Monte-Carlo (MC) estimate**"，并以两条理由说明：(1) 每条样本奖励可为其余样本当基线；(2) 策略更新在多样本梯度估计的均值上做 | p.6 |
| 经验读数 | **Table 2**（Anthropic-HH）`Reward-Var.` 列 | p.13 |

Table 2 `Reward-Var.` 实测值：RLOO(k=4) `3.1`／RAFT(k=4) `3.2`／RLOO(k=2) `3.0`／RAFT(k=2) `3.1`／REINFORCE w/ baseline `2.7`／Vanilla PG `3.7`／PPO `2.3`／DPO `N/A`。

**三条防误引（逐条有原文锚点）**：

1. **口径错位**：`Reward-Var.` 度量的主语是「**生成的奖励方差**」（原文 p.13：*"lower reward variance **amongst the generations**"*），**不是梯度估计量的方差**。用它支撑「梯度估计器方差下降」是换口径，属无效引用。
2. **「27% 更小方差」的主语是 REINFORCE-with-baseline，不是 RLOO**（p.13–14：*"REINFORCE with baseline, however, empirically results in 27% less variance"*）。可复算：`(3.7 − 2.7)/3.7 = 27.0%`。
3. **RLOO 的奖励方差并非最低**：PPO 为 `2.3`，低于 RLOO 的 `3.0–3.1`。Table 2 因此**不能**支撑「RLOO 方差最小」。

**能否作为引用依据**：方差缩减只能引作「作者的经验观察（Table 2 `Reward-Var.` 列，p.13）」，**不能引作形式化方差缩减定理**。

#### H.1.4 与 GRPO（2402.03300）全组均值基线的差异

两文互不引用（同为 2024-02 投稿，各自独立）。

**GRPO 侧的基线定义**：`Â_{i,t} = r̃_i = (r_i − mean(r)) / std(r)`，正文**内联、无编号**，位置 **2402.03300 p.14**（印刷页码 = PDF 页码，页脚实测），原文为 *"these rewards are normalized by subtracting the group average and dividing by the group standard deviation"*。注意 GRPO 是**两步**：先减全组均值，再除全组标准差。

**无偏性差别（本代理推导 + 精确枚举数值自检）**：设组 `y_(1..k) ~i.i.d. π_θ(·|x)`，记 `g_i = ∇logπ_θ(y_(i)|x)`。利用 i.i.d. 下 `E[R_j g_i] = E[R]·E[g_i] = 0 (j≠i)` 与 `E[g] = 0`：

- **留一版**：`E[G_LOO] = (1/k) Σ_i E[R_i g_i] = E[R∇logπ]` ⇒ **期望精确等于式(6) REINFORCE 梯度，无偏**。
- **全组均值版**：`E[G_group] = (1 − 1/k)·E[R∇logπ]` ⇒ **系统性缩放到 `(1−1/k)` 倍**，作为梯度估计量**有偏**（自身样本 `R_i` 与 `g_i` 的相关项未被消去）。

**数值自检（合成玩具分布，非实验）**：3 个动作、`k=3`、精确枚举全部 27 个组（脚本 `/tmp/rloo-mineru/unbiased_check.py`，一次性中间物）。留一版逐分量比值 `1.000000`（最大绝对误差 `2.22e-16`，机器精度）；全组均值版逐分量比值 `0.666667`，与 `1 − 1/k = 0.6666667` 的最大偏差 `3.33e-16`。**该自检只验证代数恒等式，不构成对本课题数据或任务的任何结论。**

**必须与结论一起书写的限定**：`(1−1/k)` 是**正的标量倍数**，只缩放期望梯度方向上的步长、不改变期望方向（等价于有效学习率的缩放）。这解释了为何 GRPO 在主流实现中长期可用，而对其「有偏」的批评只以副作用形式出现；但把 GRPO 优势称为「无偏梯度估计」在数学上不成立。

**独立佐证（本地全文）**：REINFORCE++（`wiki/papers/grpo/2025-Hu-REINFORCE-plus-plus全局优势归一化.md`，arXiv:2501.03262v9）摘要与 §2.2（p.2）明确把 GRPO／RLOO 一类的**提示级（局部）优势归一化**列为「有偏估计」，并指出 k=1 时局部归一化不存在（p.3）；解法是把统计量搬到全局批次（式(5)，p.3），随批量增大渐近无偏。**注意该文的批评对象是「除以组内标准差」这一步**；它与本代理的代数结论（留一键的**均值**减除本身无偏）并不冲突，引用时不得把两者合并成一条笼统结论。

#### H.1.5 对 H 臂的可用性裁决（文献层，非实验层）

| 主张 | 可否引用 2402.14740 支撑 | 可用替代依据 |
| --- | --- | --- |
| 留一均值基线的定义与形式 | **可以**（p.6，须注明该式无编号） | — |
| 「留一基线不引入偏差」的正式命题 | **不可以**（原文无命题、无推导、无前提） | 自证（H.1.4 两步推导）或 Kool et al. 2019 原文 |
| 「组内基线带来方差缩减」的形式化陈述 | **不可以**（只有 p.6 直觉陈述） | 无可替代；若须写，需自证或另找来源 |
| 「RLOO 方差低于 X」的经验比较 | **可以但须限定**为 Table 2 的**奖励方差**（p.13），且该列不支持「RLOO 最低」 | — |
| 与 GRPO 全组均值基线的无偏性差别 | **不可以**（两文互不引用，原文无此比较） | 自证（H.1.4）＋ REINFORCE++ p.2 的「局部归一化有偏」佐证 |

**一条边界**：上述裁决只针对「引用依据是否充分」，**不构成对留一基线或组相对机制在本课题检测任务上是否有效的任何判断**；该判断仍须由本课题实验裁决。

#### H.1.6 对 H 臂设计的文献层提示（三条，均不构成对 H 臂有效性的判断）

> 对症 [H 臂 Research Question Card](h-arm-research-question-card.md)（2026-09-10 冻结）第 11 行假设、第 20–21 行证据表与第 42 行最小下一步。**以下三条不改动该卡的冻结判据**，只登记文献层约束与本课题推论。

**① H 卡的「组内相对信号（组均值基线）提供方差缩减」不能引 2402.14740。** 该文的方差缩减只有散文直觉（p.6）与 Table 2 的**奖励方差**经验列（p.13）；且该列**不支持「RLOO 方差最低」**（PPO `2.3` 低于 RLOO 的 `3.0–3.1`），「27%」的主语也**不是 RLOO 而是 REINFORCE-with-baseline**。H 臂若要在正文写这一主张，须自证或另找来源（见 H.1.3、H.1.5）。

**② 组均值基线 vs 留一基线在 H 臂的 `k=2` 下会产生一个标量差。** H 卡第 42 行写「良性样本 CharBot 近邻 **1 变体/样本**」⇒ 若组按「{原样本, 1 变体}」构造，组大小 `k = 2`。由 H.1.4 的代数结论：

| 基线形式 | 期望优势 | 在 `k=2` 下的后果 |
| --- | --- | --- |
| **留一**（其余 `k−1` 条） | `E[R∇logπ]`，**无偏** | 无额外缩放 |
| **全组均值**（含自身） | `(1 − 1/k)·E[R∇logπ]` | **系统性缩放到 `0.5`** |

- 该缩放是**正的标量倍数**：**方向不变、幅度减半**（等价于有效学习率减半）。
- **设计含义（本课题推论，非文献主张）**：H 臂与 F 臂若用**同一学习率**做同预算对比，这个 `0.5` 会成为**混淆项**。建议二者之一——(a) H 臂显式采用**留一式**基线（无缩放、期望无偏），或 (b) 保留全组均值但在登记中写明缩放，并确保与 F 臂的**有效**步长可比。
- **证伪成本**：低——是否真的受影响可由 H 臂实测（同一设定下两种基线的读数差）判定；本提示**不预测** H 臂结果。

**③ 算子同族提示：H 臂会使 `k2` 面板从「异族」降为「同族」。** H 卡证据行（第 19 行）确认 H 臂的训练算子是 **CharBot 2 位替换**（作用于**良性** SLD）；评价面板 `k2` 同样是 **CharBot 2 位替换**（作用于 **DGA**，task_plan §5.6.1）。两者**同算子、不同样本类**——**不是样本级泄漏**，但模型在该算子的扰动分布上受过训练。task_plan §5.2 已强制「训练用扰动族与评价用扰动族必须分组报告，**泛化主张只能基于异族列**」；**H 臂适用该条，且 `k2` 应归入同族列**。这是本课题的推论，不是文献结论；H 卡第 34 行「maskdga 主面板」的判读口径不受影响（maskdga 为不同算子）。

### H.2 误报注入攻击近邻检索（任务 2）

**检索目标**：判断「攻击者**故意**制造误报（false positive）以耗尽 defender 告警预算／掩护真实攻击」是否有正式学术文献。

**结论（三句）**：
1. **该攻击模式有正式文献支撑**，但**术语分散、无单一主流命名**（`alarm poisoning`／`false-positive alarm flooding`／`FPR manipulation attack`／`alert flooding` 各有人用）。
2. **本地库（`wiki/` 第 917 篇 + Zotero 254 篇全文索引）中该攻击模式零命中**；本地命中的全部是**防御侧**材料（告警预算作为设计变量、告警聚合、误报率优化）。
3. **与本课题场景最贴合的一篇已撤稿**（Ahsan & Liu，arXiv:2601.14505，v2 于 2026-05-05 撤稿），**不得作为正文支撑**。

#### H.2.1 逐条证据（五档标注）

| # | 题名 / 作者 / venue | 证据等级 | 相关强度 | 关键原文片段（英文原句） |
| --- | --- | --- | --- | --- |
| 1 | **Crying Wolf in Cyberspace: A Cybersecurity Dynamics Study of Alarm Fatigue Attacks** · Barbierato（单人）· *Information* (MDPI) 2026, 17(5):434 · DOI `10.3390/info17050434` · 附代码库 | **在线摘要**（MDPI 正文 HTTP 403） | **直接定义** | 主张把「告警疲劳」当作**蓄意的社会技术攻击向量**而非系统副产物，提出 **"alarm poisoning"**：攻击者入侵监控基础设施、按可配置强度注入假告警（含安全关键告警）；明确指出其 **targets the human response layer**，与针对自动化过程的 false data injection 相区别 |
| 2 | **Potential Disguising Attack Vectors on Security Operation Centers and SIEM Systems** · Drahuntsov & Rabchun · *CEST* 2(14):6–14, 2021 · DOI `10.28925/2663-4023.2021.14.614` | **在线摘要**（另有乌克兰语版本，题录双源核验） | **直接定义** | "An attacker may trigger the malfunctioning alarm continuously to **distract the analytics stuff and perform its actions under the cover of noise**."（SIEM/SOC 三规避向量之第三 = false-positive alarm flooding） |
| 3 | **Uncovering and Understanding FPR Manipulation Attack in Industrial IoT Networks** · Ahsan & Liu · arXiv:2601.14505 · **v2 已于 2026-05-05 撤稿** | **在线摘要 + 撤稿状态** | **直接定义，且与本课题最贴合** | 提出 FPR manipulation attack (FPA)：对良性流量做 packet-level perturbation 使其被误判为攻击。摘要："a systematic simple packet-level perturbation is performed to alter the labels of benign traffic samples"（成功率 80.19%–100%）；"even a small fraction of false positive alerts … can increase the delay of genuine alerts investigations up to 2 hr in a single day"。arXiv comments 原文撤稿理由："Technical contributions have some flaws" |
| 4 | **False Alarms, Real Damage: Adversarial Attacks Using LLM-based Models on Text-based Cyber Threat Intelligence Systems** · Shafee, Bessani, Ferreira · arXiv:2507.06252（2025-07-05） | **在线全文片段**（ar5iv HTML，未下载入库） | **直接定义，但场景是 CTI 文本分类器，不是流量 NIDS** | §IV-A："injecting a high volume of deceptive FaN and **Fake Positive (FaP)** texts"；"flooding attacks waste the analyst's effort, leading to system failure" |
| 5 | **Alert Flooding Attack on Snort and Its Mitigation** ·（KSU 站点 PDF） | **仅网页 PDF·题录未完整核验**（HTTPS 证书域名不匹配，作者与年份未确证） | **直接定义**（标题即攻击名） | 内容为告警关联／限流缓解；检索摘要指出知晓窗口式关联的攻击者可**故意把恶意包排在关联窗口之外**——即防御算法本身构成新攻击面 |
| 6 | **Can Machine Learning Be Secure?** · Barreno, Nelson, Sears, Joseph, Tygar · ASIACCS 2006 · DOI `10.1145/1128817.1128824` | **在线摘要** | **近似（理论母类）** | 对抗 ML 三轴分类学的 **availability attack** 定义正是「制造足够多的误报与漏报使系统实际不可用」，举例：使 IDS 误拒大量合法连接直到管理员被迫关掉 IDS |
| 7 | **Insertion, Evasion, and Denial of Service: Eluding Network Intrusion Detection** · Ptacek & Newsham, 1998 | **在线摘要（经二手转述，未取原件）** | **近似** | DoS 类别的经典来源，但方向是 **IDS 计算资源耗尽**，非「制造误报消耗人力」 |

**明确不是攻击模式、列出以避免误引的防御侧材料**：Landauer 等 *Dealing with Security Alert Flooding*（ACM TOPS 25(3), 2022，DOI `10.1145/3510581`，标题含 "Alert Flooding" 但全文是**防御方**的告警聚合）、NoDoze（NDSS 2019，防御方自动化分诊，Zotero `3K6INJU2`）、本地 `wiki/papers/methodology/soc-alert-operations/` 全目录（告警预算作为**设计变量**）。

#### H.2.2 两条已知本地线索的强制核验结论

**① StealthCup 2025：不含误报注入／告警预算耗尽攻击向量。**

`wiki/papers/datasets/2025-Kern-StealthCup规避导向IDS基准CTF.md` 的规则设计是「**触发告警即扣分**」（行 20），罚分 `P_t = Σ_k Σ_s w_{k,s}·a_{t,k,s}` 的目标是**最小化**（行 47）。**攻击者被规则设计为避开告警**，与本课题研究目标的**方向相反**。其可用价值在 **defender 侧**：该计分函数本身就是一个加权告警预算，且 Table 2 的「误报率 vs 漏检」权衡（Wazuh 默认 94.79%/95.30%/67.86%，商业方案 0.00% 但漏检更多，行 75–77）是本课题「同时报告 AP 与固定误报预算检出率」的**实测例证**（行 121–123 已作此定位）。**不可引作误报注入攻击的先例。**

**② Zotero `XG6NP6QH`（Schroeder de Witt 等 2021）：不覆盖误报注入模式。**

题录核验：*Fixed Points in Cyber Space: Rethinking Optimal Evasion Attacks in the Age of AI-NIDS*，Schroeder de Witt / Huang / Torr / Strohmeier，arXiv:2111.12197v1，2021-11-23；本地全文笔记 `wiki/papers/datasets/locked-shields-related/2021-SchroederdeWitt-AI-NIDS博弈不动点与规避攻击.md`。该文报告的**误报率上升**（2018 训练在自身验证 FPR 0.8%，换 2017 验证升至 5%，笔记行 70）是**分布漂移的观测后果**，作者**明确自限因果关系**（行 110 逐字："we cannot establish any causal relationship for these changes"），从未提出攻击者蓄意抬高误报；其对抗攻击（FAST）的奖励条件是 `C(x+δ)<0.5`，即**骗过分类器**＝漏报方向，与误报注入**方向相反**。**判定：不覆盖。**

#### H.2.3 已查检索式清单与工具状态（如实披露）

**本地混合检索**（入口 `uv run --project scripts/literature_search --locked python -m scripts.literature_search`，自 worktree 根执行）：

| 查询式 | 模式 | 结果 |
| --- | --- | --- |
| `status --json` | — | 成功：2172 笔记 / 154253 chunk / papers 917，**`stale=true`**（source_added 32、source_changed 3） |
| `query "误报注入 告警预算 耗尽" --scope local --mode hybrid --json` | hybrid | **失败**：`intfloat/multilingual-e5-small is not a local folder and is not a valid model identifier` |
| 同上（加 `HF_HUB_OFFLINE=1`） | lexical | **超时未返回**（>600 s，已终止） |
| `query "false positive injection intrusion detection" --scope local --mode hybrid --json` | hybrid | 输出仅为 `索引构建中，等待锁：.cache/literature-search/index.sqlite3.build.lock` |
| `告警疲劳 攻击 规避`、`alert flooding attack alert budget`、`adversarial false positives camouflage attack` | — | **未执行**（工具在本轮不可用） |

> **工具状态声明（必须随结论转述）**：本轮**无任何一条本地查询成功返回检索结果**，**向量通道未运行**。原因为模型标识无法解析（`HF_HUB_OFFLINE=1` 后转索引增量构建，`timeout 180` 未完成）＋ `stale=true` 且**另有一会话的 `build` 进程持锁重建索引**。因此 H.2 的「本地零命中」结论**主要由 rg 扫描与 Zotero 直查支撑**，不是由混合索引支撑。

**rg 扫描**（`rg -il/-n --no-ignore`，覆盖 `wiki/`、`thesis/`、`output/`、`raw/`）共 **11 组模式**，其中：
- 关键词组（`误报注入`／`告警洪水`／`alert flooding`／`false positive injection`／`alert fatigue`／`告警疲劳`／`alert budget`／`告警预算`）命中 26–35 个文件，**逐条判读后全部为误报率／告警疲劳的泛化讨论，无一为该攻击模式**；
- 针对性正则组（攻击性修饰 + false positive/alarm；`exhaust|deplete|drain|overwhelm|saturate` + analyst/defender/alert/budget；`alert flooding` 变体；`adversarial false positive` 变体；IDS DoS；资源耗尽）**除 2 条无关命中外全部 0 命中**。

**Zotero**：MCP 工具本轮**全部不可用**（本地 API `Connection refused`，Zotero 应用未运行）。改用 `zotero.sqlite` **只读直查**替代（`mode=ro&immutable=1`），执行：语义检索返回的 18 个 key 题录解析、标题扫描 2 组、全文索引词级查询 4 组（库内 254 篇有全文索引 / 77381 词）。`fatigue ∧ alert` → 3 条；`flooding ∧ alert` → 2 条；`alerts ∧ exhaustion` → 1 条（CALIBURN）；均非该攻击模式。

**在线补充**：8 条查询式（WebSearch）+ 5 次 WebFetch 核验（`arxiv.org/abs/2507.06252`、ar5iv HTML、`arxiv.org/abs/2601.14505` 成功；MDPI 正文 403、KSU PDF 证书错误失败）。

#### H.2.4 检索未获声明（不得外推为「不存在」）

- **本地全域未获**：`wiki/` 全文、`wiki/papers/` 917 篇、Zotero 254 篇全文索引中，该攻击模式**零命中**（已查清单见 H.2.3）。
- **顶会未获**：USENIX Security／CCS／NDSS／S&P／ICML／NeurIPS 中，以「alert budget exhaustion attack」或「false positive injection」为主张的论文，**本轮 8 条在线查询式未获**。**这是「本轮已查渠道未获」，不是「不存在」的断言。**
- **未确证项**：KSU 的 "Alert Flooding Attack on Snort" 因站点证书错误无法核验作者与年份，**存在性未确证**。
- **MITRE ATT&CK 的对应项未确证**：T1562.011（Impair Defenses: Spoof Security Alerting）来自**安全厂商博客解读，非学术文献**；本轮未取得 MITRE 官方定义文本，**不得据此断言 ATT&CK 收录了该战术**。

#### H.2.5 对 H 臂「原创性边界」的含义（文献层，非实验层）

**这是本方向迄今最主要的原创性风险，必须正面处理**：

1. **攻击模式本身不是空白**——「故意制造误报以掩护／耗尽预算」在 2006 年（Barreno 的 availability attack）已有理论母类，2021 年（Drahuntsov）、2026 年（Barbierato）已有正式命名。**不得把「提出该攻击模式」当作本课题贡献。**
2. **但「把误报注入作为训练信号」未检索到先例**——现有文献全部停在**威胁建模与影响评估**（攻击可行性、告警延迟、分析师疲劳），**没有一篇把它反用为防御侧的训练目标**（即：让模型对「良性近邻被误判」这一信号敏感）。H 臂的机制差量正落在这一层。
3. **最贴合的那篇已撤稿**，因此「已被严格实验验证的 FPA」在本轮检索中**不存在可引用的证据**。若要引用该文，只能标为「已撤稿的待验证主张」。
4. **H 卡需要补一条边界声明**：正文不得写「本课题首次提出误报注入威胁」，只能写「本课题将已有威胁模型（Barbierato 2026 的 alarm poisoning／Drahuntsov 2021 的 false-positive alarm flooding）转化为防御侧的训练信号」。**该措辞调整须经用户裁决**，本文件不代改 H 卡正文。
5. **若要引用，排序建议**：① Barbierato 2026（同行评议期刊、附代码，用其 **"alarm poisoning"** 命名）与 ② Drahuntsov & Rabchun 2021（明确命名 false-positive alarm flooding，有逐字句）作「攻击模式已被正式命名」的锚点；③ Barreno 2006 作上位理论框架（availability attack）。**三篇均须先按 `raw/AGENTS.md` 与 `wiki/AGENTS.md` 完成入库与全文核验，方可进入正文**；本文件仅登记为**在线候选**。

#### H.2.6 强相关但未入库的论文（仅题录·未入库，未下载）

| 题名 | 作者 / 年份 / venue | ID |
| --- | --- | --- |
| Crying Wolf in Cyberspace: A Cybersecurity Dynamics Study of Alarm Fatigue Attacks | Barbierato, 2026, *Information* 17(5):434 | DOI `10.3390/info17050434` |
| Potential Disguising Attack Vectors on Security Operation Centers and SIEM Systems | Drahuntsov & Rabchun, 2021, *CEST* 2(14):6–14 | DOI `10.28925/2663-4023.2021.14.614` |
| Uncovering and Understanding FPR Manipulation Attack in Industrial IoT Networks | Ahsan & Liu, 2026 | arXiv:2601.14505（**已撤稿**） |
| False Alarms, Real Damage: Adversarial Attacks Using LLM-based Models on Text-based Cyber Threat Intelligence Systems | Shafee, Bessani, Ferreira, 2025 | arXiv:2507.06252 |
| Dealing with Security Alert Flooding: Using Machine Learning for Domain-independent Alert Aggregation | Landauer 等, 2022, ACM TOPS 25(3):1–36 | DOI `10.1145/3510581` |
| Can Machine Learning Be Secure? | Barreno 等, 2006, ASIACCS | DOI `10.1145/1128817.1128824` |

#### H.2.7 检索代理另报的两项发现（转登记，独立复核结论附后）

1. **凭据暴露（已由本代理独立复核，确证）**：`Zotero.txt`（worktree 根，30 字节）内容为一条 Zotero API key，且**被 Git 跟踪**（`git ls-files` 确证）、**未匹配任何 `.gitignore` 规则**、**历史中有 1 次提交**。检索代理在排查 Zotero 配置时用 `cat` 读取并在会话中回显了它。**处置建议（须用户授权，本代理未执行未授权操作）**：① 立即轮换该 key；② 将文件移出 Git 跟踪并加入忽略；③ 若需清历史，按根规则用 BFG／filter-branch 处理。**本文件与本次汇报均不回显该值。**
2. **检索索引状态**：`status --json` 报告 **`stale=true`**（source_added 32、source_changed 3）；本轮执行期间另有一会话的 `literature_search build` 进程持锁重建索引，检索代理未干预。**后续使用本地混合检索前须先确认索引已重建且 `stale=false`。**

#### H.2.8 三篇误报注入文献全文入库（2026-09-11）

> 承接 §I.2 的裁决（摘要级不足以支撑正文论断，须过 `raw/` + `wiki/` 全文门）。**三篇终态均为「本地全文」。**

| # | 原件（`raw/papers/attack-detection/`） | SHA-256（前 16） | 页数 | wiki 全文笔记 | 证据等级终态 |
| --- | --- | --- | --- | --- | --- |
| 1 | `2008-Barreno-Security-of-Machine-Learning.pdf` | `f65321cc2714ada9` | 26 | `2008-Barreno-机器学习安全与误报可用性攻击.md` | **本地全文**（MinerU + pypdf 逐页复核） |
| 2 | `2021-Drahuntsov-Disguising-Attack-Vectors-SOC-SIEM.pdf` | `79d510a9a9990a8b` | 9 | `2021-Drahuntsov-SOC与SIEM误报洪水攻击向量.md` | **本地全文** |
| 3 | `2026-Barbierato-Crying-Wolf-Alarm-Fatigue-Attacks.pdf` | `22dac4e0c8663c4e` | 25 | `2026-Barbierato-告警疲劳攻击与告警投毒.md` | **本地全文** |

**入库时解决/发现的三项事实问题（登记，防复发）**：

1. **Barreno 的版本问题（最重要）**：任务线索称「2006 ASIACCS 有 CMU 公开版」——**该 CMU 版不存在**（检索确认：只有 ACM 版与 Berkeley TRUST 海报）。按 `raw/AGENTS.md` 不使用不可信镜像的纪律，**未采用第三方课程页副本**，改用**作者所在机构（UC Berkeley EECS）的公开技术报告 UCB/EECS-2008-43**。**TR 正文 p.9 自述其分类学为「a preliminary version ... appears in previous work」，参考文献 p.23 指向 ASIACCS'06 ⇒ 分类学的优先权在 2006 会议版**。**后果：引用 2006 版的具体页码前必须取得该版全文；笔记内的页码锚点只对 2008 TR 有效。**
2. **Barbierato 是单一作者**，不是 "Barbierato et al."；任务线索的写法已作废。MDPI 站点 403 为反爬，改用**出版方 CDN 直链**取得全文（CC BY）。
3. **Drahuntsov 的页码**：出版方 OJS 元数据标 `6-16`，而**实际页眉为印刷 pp.6–14**（PDF 页 `N` ＝ 印刷页 `N+5`，逐页核对）。**引用以页眉为准。**

**三篇的核心可引锚点（供 H 臂威胁模型一节取件）**：
- Barreno：**p.8**「Availability attacks cause denial of service, usually via false positives」；**p.7**「false positives tend to violate the availability goal because the learner itself denies benign instances」；**p.19** SpamBayes 上 `10% FP ⇒ 不可用`（唯一定量锚点）；**p.14**「针对学习组件的探索式可用性攻击并不常见」。
- Drahuntsov：**印刷 p.6** 摘要逐字「...distract the analytics stuff and perform its actions **under the cover of noise**」；**印刷 p.10**「**there were no actual incident but the alert still raised**」＋「consume too much SOC specialists' time ... adversary has more chances to stay undetected」；**印刷 p.11–12**「狼来了」使规则被关闭。
- Barbierato：**p.1** alarm poisoning 定义（含 `deliberate injection`）；**p.4** 与 false data injection 划界（`targets the human response layer`）；**p.13** 三策略构成向量与 `Λ_fake = 1.0 h⁻¹` 固定；**p.15** 排序在 24 个参数设定中 22 个保持。

**三条必须随引用转述的自限**：① Barreno 未涉及分析师人力与告警队列（与 Drahuntsov/Barbierato 层级不同，**不得合并引用**）；② Drahuntsov 为**概念性论文，无实验无数据，作者两次声明无在野证据**；③ Barbierato 为**仿真研究**，作者自述证据是**描述性排序**（p.22），联合不确定性下严格排序仅 21% 保持（p.16）。

**同步更新**：`wiki/papers/attack-detection/INDEX.md` 新增「误报注入与告警疲劳攻击威胁模型（2026-09-11 入库）」节。

**✅ Zotero 导入已完成（2026-09-11 更新）**：Zotero 应用恢复后经 MCP 导入成功，**各条 item key 见 §K**。以下保留当时（应用未运行）的阻塞登记原文，作过程记录：

**⚠️ Zotero 导入未完成（阻塞登记，已于 2026-09-11 解除）**：本轮 **Zotero 应用未运行**（无进程、本地 API `127.0.0.1:23119` 连接被拒），MCP 全部工具返回 `[Errno 61] Connection refused`。已按裁决改用 `zotero.sqlite` **只读**直查完成查重：**库内 952 条中三篇均未收录（零命中），确认需要导入**。**未对 `zotero.sqlite` 做任何写入**（避免在应用未运行时损坏库）。**待办**：Zotero 启动后按 DOI/URL 导入三条并按 `raw/AGENTS.md` 关联本地全文——
- Barreno：`https://www2.eecs.berkeley.edu/Pubs/TechRpts/2008/EECS-2008-43.pdf`（会议版 DOI `10.1145/1128817.1128824`）
- Drahuntsov：DOI `10.28925/2663-4023.2021.14.614`
- Barbierato：DOI `10.3390/info17050434`

## J D 臂选择规则的动作等价性分析（2026-09-11，任务 B）

> **目的**：ChatGPT 深调研指出「若 `K=4` 下 centered advantage 功能退化为 BB-GS，则差量消失」。本节把 D 臂的**实际选择规则**写成可分析对象，给出与三个近邻的**等价域**与**必然不同域**，并判定差量是否「不可约」。
> **边界**：本节是**代数分析**，不是实验。所有关于「实际运行落没落在某个域」的陈述一律标为**待实测**。

### J.1 实现事实（回代码核验，非命名）

`official_p2p3.py` **L201–L211**（本机只读核验，2026-09-11）：

```
fooled = (p_cand < 0.5).astype(np.float64)   # 二值被骗指示
f      = fooled[js]                          # 取该组（同一恶意原样本）的 K=4 个变体
adv_g  = f - f.mean()                        # 组内中心化
scored.sort(key=lambda t: -t[0])
adv_batch = [cands[j] for _, j in scored[:64]]   # 跨组全局 top-64
```

**结论：当前 D 臂的选择信号就是显式 centered sibling advantage**——这一点**由代码确认**，不是从命名推的。但有两个必须写进分析的实现细节：

1. **信号是二值的**（`fooled ∈ {0,1}`），不是连续分数；
2. 中心化后做的是**跨组全局 top-64 配额竞争**，不是逐组独立过滤。

### J.2 记号与两条基本性质

设批内恶意原样本 `i = 1..N`（实测 `N ≈ 64`），每组建 `K = 4` 个变体 `j = 1..K`。记：

- `f_ij ∈ {0,1}`：变体 `v_ij` 是否被骗（`p < 0.5`）；
- `c_i = Σ_j f_ij ∈ {0..K}`：组 `i` 的被骗数；`f̄_i = c_i/K`；
- **中心化优势** `a_ij = f_ij − f̄_i`；
- **选择** `S = argtop_Q (a)`，`Q = 64`，并列按候选生成顺序（Python `sort` 稳定）。

由定义立得两条**与数据无关**的性质：

> **性质 1（组内序不变）**：对任意逐组常数 `b_i`，按 `f_ij − b_i` 在**组内**的排序与按 `f_ij` 的排序**完全相同**。
> **⇒ 中心化的唯一可能作用面是「跨组分配」，它不可能改变任何一组内部的优先级。**

> **性质 2（值域极小）**：`a_ij` 只有 `2K` 个可能取值——
> 被骗者：`a = 1 − c_i/K ∈ {1, 3/4, 1/2, 1/4, 0}`（`c_i = 1,2,3,4` 时递减）；
> 未骗者：`a = −c_i/K ∈ {0, −1/4, −1/2, −3/4, −1}`。
> **正优势只有 `K − 1 = 3` 个不同取值。**

**性质 2 的一个直接后果（重要）**：`c_i = K`（全组被骗）的被骗变体 `a = 0`，与 `c_i = 0`（全组未被骗）的未骗变体 `a = 0` **数值完全相同**。

> **性质 3（0.0 并列簇跨语义）**：`a = 0` 的并列簇同时包含两类**语义相反**的候选——「最容易被骗的组里的被骗者」与「完全骗不动的组里的未被骗者」。配额一旦切到这一簇，**具体谁入选由候选生成顺序决定，与机制语义无关**。

### J.3 与三个近邻的等价域 / 必然不同域

三个近邻的规则（各篇笔记的页码锚点见其入库笔记）：

| 近邻 | 规则 | 组间竞争 |
| --- | --- | --- |
| **BB-GS**（Wu 2025） | `B_f = {x ∈ B_adv : x misclassified}`——**绝对误分类谓词**，取全部被骗者，无配额 | **无** |
| **MaxUp / Tramèr-Boneh Max**（Gong 2020 / Tramèr 2019） | 逐组 `argmax_j ℓ_ij`——**每组恰取 1 个** | **无**（每组等权） |
| **MMEL**（Yi 2021） | `w_ij = softmax_j(ℓ_ij/τ)`——**全正、组内归一、不产生零权重** | **无** |
| **本课题 D 臂** | `a_ij` 全局 top-`Q` | **有（配额竞争）** |

#### (a) D ≡ BB-GS 的等价域

**充分条件（E1）**：`|{f_ij = 1}| = Q` **且** 对所有 `i` 有 `c_i < K`（不存在全组被骗的组）。

- 证明草图：`c_i < K` ⇒ 每组被骗者的 `a = 1 − c_i/K > 0`，严格大于一切未骗者（`a ≤ 0`）；故 top-`Q` 先取全部正优势者。由 `|{fooled}| = Q` 恰好吃满配额 ⇒ `S = {fooled}`，与 BB-GS 的 `B_f` 相同。∎
- **强化条件（E2）**：`∀i, c_i ∈ {0,1}`（每组至多一个被骗）且 `|{fooled}| ≤ Q` ⇒ 全部被骗者 `a = 3/4` 并列最高，必然全部入选。此时 `S ⊇ B_f`（若 `|{fooled}| < Q`，`S` 还会补入 0.0 并列簇中的候选，与 BB-GS 的集合不同——**这是 E2 不是全等的原因**）。

**必然不同域（D1）**：`|{fooled}| ≠ Q`。
- `|{fooled}| < Q`：D 必须从**未骗者**中补足配额，BB-GS 不收未骗者 ⇒ **集合必然不同**。
- `|{fooled}| > Q`：D 必须丢弃部分被骗者，BB-GS 全收 ⇒ **集合必然不同**。

#### (b) D ≡ MaxUp / Max 的等价域

**充分条件（E3）**：`∀i, c_i = 1`（每组**恰一个**被骗变体）**且** `N = Q`。
- 证明草图：`c_i = 1` ⇒ 每组恰有一个 `a = 3/4` 的候选，组内无并列；`N = Q` ⇒ 全局正优势候选数 `= N = Q`，恰好吃满配额且**每组一个** ⇒ `S = {每组唯一被骗者} = MaxUp 的逐组 argmax 集`。∎
- **必要条件方向**：只要存在 `c_i ≠ c_{i'}`（组间被骗数不等）且正优势候选数 `≥ Q`，`a` 的降序会**先抽干 `c` 小的组**，再抽 `c` 稍大的组——**不是「每组一个」**，与 MaxUp 必然不同。

**必然不同域（D2）**：`∃ i, i': c_i ≠ c_{i'}`（**组间被骗数方差 > 0**）且配额被正优势候选填满。
**退化等价域**：`c_i ≡ c`（所有组完全相同）⇒ 所有正优势候选 `a` 相同 ⇒ 配额内的选择**完全由并列破法决定**（性质 2/3），此时 D 既不等价于 MaxUp（若 `c ≥ 2` 则一次取走多组多个），也不等价于 BB-GS（若 `c·N ≠ Q`）——**是一个由任意的并列破法主导的规则**。

#### (c) D ≡ MMEL 的等价域

**不存在集合等价域。** 理由：

- MMEL 的权重**严格为正**（softmax），**支撑集是整组**；D 的权重是 0/1 硬选择，**支撑集是配额子集**。两者的**梯度支撑集不同** ⇒ 不存在「selected set 相同」的意义。
- MMEL **不做跨组竞争**（组内归一、逐组独立）；D 的核心恰恰是跨组竞争。
- MMEL 的极限情形 `τ → 0` 退化为 **逐组 one-hot = Max**，**不是** D 的形态（D 可在一组内取多个、也可整组不取）。

**唯一可比的通道**是「梯度方向」而非「选择集」：若把 D 的 0/1 权重归一化后与 MMEL 的权重比较，则二者**只有在 `K` 与温度使 softmax 逼近 one-hot 且 `c_i ≡ 1` 且 `N = Q` 时**才接近——即回到 E3。

### J.4 差量判定：**不可约，但信号脆弱**

| 问题 | 判定 | 依据 |
| --- | --- | --- |
| 能否退化为 BB-GS？ | **不能一般性退化** | 只在 E1／E2 的窄条件成立；D1 是**必然不同域** |
| 能否退化为 MaxUp？ | **不能一般性退化** | 只在 E3（`c_i ≡ 1` 且 `N = Q`）成立；D2 是**必然不同域** |
| 能否退化为 MMEL？ | **不能（无集合意义）** | 支撑集与竞争结构都不同（J.3c） |
| 差量是否「不可约」？ | **结构上不可约，但**：**承载差量的信号只有 `K−1 = 3` 个正优势取值**，且 0.0 并列簇跨两类语义 ⇒ 相当一部分选择由**任意的并列破法**决定（性质 2、3）。**「不可约」成立的是运算结构，不是可分辨性。** | 性质 1–3 |

**一句话**：D 臂的不可约运算可以被精确命名——**「按组内被骗比例对组排序（比例越低越优先），再在组内取被骗者，最后跨组按全局配额截断」**。三个近邻都没有这个运算：BB-GS 无配额、MaxUp 逐组等权取一、MMEL 无零权重组内归一。

### J.5 三条必须与结论一起写出的限定

1. **J.3 的等价域/差异域是代数结论，不是「实际运行落在哪个域」的陈述**。要判定实际运行落在哪个域，须读取该臂**每个 batch 的 `c_i` 分布**与**实际入选集合**——`official_p2p3.py` 当前**只保留了 `fpr_curve` 等汇总，未落盘逐候选分数**（L201–L211 无写盘），因此**本机无法回算**。**这是当前证据缺口，须另行取数。**
2. **`Q = 64` 与 `N ≈ 64` 的巧合值得注意**：`N` 是批内恶意数（期望 64），`Q` 固定 64。当 `N < 64` 时正优势候选上限 `= K·N` 可能仍大于 `Q`；当 `N` 因批抽样波动而偏离 64 时，D1 条件（`|{fooled}| = Q`）成立的概率很低 ⇒ **运行大概率落在 D1/D2 这两个「必然不同域」**。**这是由 `Q` 的设定方式推出的一般性判断，不是实测。**
3. **退化风险的真实位置不是「等价于 BB-GS」，而是「并列破法主导」**：由于信号二值 + `K = 4`，正优势只有 3 个取值，配额切在 `a = 0` 簇内的概率不低；一旦切入该簇，**选谁入选由候选生成顺序决定**。这让机制行为部分地**不可归因**——这是比「与 BB-GS 碰撞」更需要处理的问题。

### J.6 对 H 臂设计的修正建议（承接主代理裁决 3）

1. **把选择信号从二值 `fooled` 换成连续兄弟分数**（如 `p_mal`、或 `0.5 − p_mal` 的间隔），再做组内中心化。理由：性质 2 —— 二值信号经中心化后只剩 `K−1` 个正取值，**排序信息量被压到极低**；连续分数使 `a_ij = s_ij − s̄_i` 在组间可比且可分辨。
2. **显式登记并列破法**：若保留二值信号，必须在方法描述中写明并列如何打破（当前实现是**候选生成顺序**），或在实现中改为确定性且与机制语义一致的破法。
3. **显式登记配额 `Q` 与 `N` 的关系**：`Q` 固定 64、`N` 随批波动 ⇒ 正优势候选数与被选数无固定关系。建议把 `Q` 改为**与正优势候选数挂钩的规则**（如「取全部正优势候选」或「取正优势候选的前 ρ 比例」），使机制语义清晰且可复算。
4. **「跨组配额竞争」应被写成机制的显式组成部分**，而不是实现细节——它正是与 BB-GS（无配额）、MaxUp（逐组等权）的**主要可辨差量**。
5. **论文表述**：用「未检得同构先例」，**禁「首次」**；差量主张须同时给出 J.3 的等价域与差异域，承认「在 `c_i ≡ 1` 且 `N = Q` 时与 MaxUp 等价」这一边界。

### J.7 落盘产物

- 本节（`notes.md` §J）
- 四近邻全文笔记：`wiki/papers/methodology/adversarial-training/`（Tramèr 2019／MaxUp 2020／MMEL 2021／BiB 2025）+ 该目录 `INDEX.md`
- 威胁模型新增两篇：`wiki/papers/attack-detection/2008-Nelson-垃圾邮件过滤器的可用性攻击.md`、`wiki/papers/attack-detection/2006-Newsome-Paragraph-签名学习投毒.md`

### J.8 本轮新增 7 篇的 Zotero 导入登记（**已于 2026-09-11 完成，见 §K**）

**✅ 已解除**：Zotero 应用恢复后已全部导入成功，各条 key 见 §K。

**（原阻塞登记，保留作过程记录）** ~~**Zotero 应用仍未运行**（无进程、本地 API `127.0.0.1:23119` 连接被拒），MCP 不可用。~~已用 `zotero.sqlite` **只读**直查完成查重：**库内 952 条中本轮 7 篇（Nelson／Paragraph／Tramèr／MaxUp／MMEL／BiB／Allergy）全部零命中**，确认均需导入。**未对 `zotero.sqlite` 做任何写入。**

**待办（Zotero 启动后按 DOI/arXiv 导入并关联本地全文）**：

| 篇 | 标识 |
| --- | --- |
| Nelson 2008 LEET | USENIX 页 `https://www.usenix.org/conference/leet-08/exploiting-machine-learning-subvert-your-spam-filter`（无 DOI） |
| Newsome 2006 Paragraph | DOI `10.1007/11856214_5` |
| Chung & Mok 2006 Allergy | DOI `10.1007/11856214_4`（**仅题录，无本地全文**） |
| Tramèr & Boneh 2019 | arXiv `1904.13000` |
| MaxUp 2020 | arXiv `2002.09024` |
| MMEL 2021（**ICLR 2021**，题录已更正） | arXiv `2103.08933` |
| Batch-in-Batch 2025 | arXiv `2406.04070`；期刊版 *Complex & Intelligent Systems* 11:132, 2025 |

**题录更正登记（防复发）**：本轮下载时先按记忆试了两个 arXiv 编号，**两个都错**（`1901.10565` 实为 *Ulam-Warburton Automaton*、`2002.08155` 实为 *CodeBERT*）；后经 arXiv API（须用 **https**，`http` 端点无响应）按题名反查才得正确编号。**教训：`raw/AGENTS.md` 的「新增前用稳定信息去重」必须落到 arXiv API 直查，不得凭记忆填编号。**

## K Zotero 导入完成登记（2026-09-11）

Zotero 应用恢复后，经 MCP 逐条导入。**成功 10 / 失败 0**（Tramèr 首次 `The read operation timed out`，单独重试成功）。统一 `attach_pdf=false`——本地全文已在 `raw/`，不重复挂网附件。**抽查 3 条**（`VQZ2X3DM`／`UU8DERCD`／`S5DEP4QH`）：题录字段、类型、DOI 与原文一致。

| Zotero key | 条目 | 类型 | 导入方式 |
| --- | --- | --- | --- |
| `UU8DERCD` | Barreno 等，*Can machine learning be secure?*（**ASIACCS'06 会议版**；本地全文为 TR 扩展版） | conferencePaper | DOI `10.1145/1128817.1128824` |
| `G7EG4ZDS` | Drahuntsov & Rabchun 2021 | paper | DOI `10.28925/2663-4023.2021.14.614` |
| `S5DEP4QH` | Barbierato 2026 | journalArticle | DOI `10.3390/info17050434` |
| `TIMNV9PN` | Newsome 等 Paragraph RAID 2006 | paper | DOI `10.1007/11856214_5` |
| `DT9UGSPX` | Chung & Mok **Allergy** RAID 2006（**仅题录，无本地全文**） | paper | DOI `10.1007/11856214_4` |
| `I2PNUU5T` | Nelson 等 **LEET '08**（无 DOI） | **webpage** | 按 URL 入（USENIX 官方页） |
| `HBURW3K5` | Tramèr & Boneh 2019 | paper | arXiv `1904.13000`（首次超时，重试成功） |
| `JPG8TXXZ` | MaxUp 2020 | paper | arXiv `2002.09024` |
| `IVRS5GKV` | MMEL（**ICLR 2021**） | paper | arXiv `2103.08933` |
| `VQZ2X3DM` | Batch-in-Batch（**arXiv 预印本版**，非期刊版） | preprint | arXiv `2406.04070` |
| `9WUKHNGP` | GRPO / DeepSeekMath | journalArticle | 本条为既有条目，本轮**只读核验** |
| `UNYRKIG9` | GFPO | preprint | 同上 |
| `HXRQG7PU` | RLOO | preprint | 同上 |
| `QVI7J5QD` | Drichel 2024 *Towards Robust DGA Classification* | preprint | 同上 |
| `CPILDEPS` | CharBot | preprint | 同上 |
| `K3VYSJSY` | MaskDGA | preprint | 同上 |
| `JJ5J9YR3` / `HMF49WET` | DRIFT（**库内有重复两条**） | preprint | 同上 |
| **未核验** | Drichel 2020 B-ResNet（`2006.11103`）、pAUC-DRO（2022-Zhu） | — | 本轮未查到，待补 |

**两条必须登记的库内问题（未擅自处置）**：
1. **重复条目**：DRIFT（`JJ5J9YR3`／`HMF49WET`）、DAPO、Provable Dynamic Fusion、Lee 2024 中文域 DGA 各出现两条。**去重属破坏性操作，须用户明确授权。**
2. **`Allergy` 的 Zotero 条目 ≠ 可引证据**：该条仅为题录，**本地无全文**，正文引用仍受 §H.2.1 的降级约束（只能标「据 Nelson 2008 §6 转述」）。

**统一去向**：以上全部 key 已同步进 [第三章方法来源台账](../../../thesis/methods/第三章-方法来源台账.md) 的对应条目与 §七 Zotero 状态汇总。

## L 组件 2 的定点排重（2026-09-11）：阈值诱导的逐样本误报加权

> **被排重对象（组件 2）**：良性误报加权——batch 内**当前模型判恶意**的真良性样本 CE × `3.0`。
> **数学对象**：固定决策阈值诱导的超额风险 `ψ_b(s) = ℓ_b(s) + 2(ℓ_b(s) − c_t)₊`，`c_t = −log(1−t)`，`t = 0.5`。
> **等价化简（本代理推导，供核对）**：`c_t = −log(1−t)`，而良性样本的 `ℓ_b(s) = −log(1−p)`（`p`＝模型判恶意概率）⇒ **`ℓ_b(s) > c_t ⟺ p > t`** ⇒ `(ℓ_b(s) − c_t)₊` **恰是「该良性样本在当前工作点上被判恶意的指示」的平滑化**。故本组件的精确形态是：**以分类工作点为激活点、按当前模型输出逐样本决定的良性类线性放大**。

### L.1 结论：**未检得精确同构先例**（但两个组成成分**各自都有先例**）

| 成分 | 是否已有先例 |
| --- | --- |
| **阈值／工作点进入损失函数** | **有**（AdaCSL、ASL、label-dependent-cost 校准代理损失） |
| **逐样本、依赖当前模型输出的加权** | **有**（Seesaw、NuCE、LiLAW、Focal、AFL） |
| **二者的精确复合**（以工作点为激活点 ＋ 逐样本 ＋ 对良性类在阈值以上**线性放大**） | **未检得同构先例** |

### L.2 最近邻（按接近程度降序；**全部为在线候选，未入库**）

| # | 题录 | 机制位置 | 与本组件的精确差异 |
| --- | --- | --- | --- |
| 1 | **ASL** — Ridnik, Ben-Baruch, Zamir, Noy, Friedman, Protter, Zelnik-Manor，*Asymmetric Loss For Multi-Label Classification*，ICCV 2021（arXiv `2009.14119`；官方实现 `github.com/Alibaba-MIIL/ASL`） | 负类项做**概率平移** `p_m = max(p − m, 0)` 后再施聚焦指数：`L = −[y(1−p)^{γ+}log p + (1−y)p_m^{γ−}log(1−p_m)]` | **最接近**：同样是「负类 ＋ 模型输出依赖 ＋ 阈值平移」。**三处不同**：① ASL 对困难负样本是**封顶/丢弃**（`−log(1−p_m) → −log m` 有界），本组件是**线性放大**（无上界）；② ASL 的 `m` 是**超参**，不由决策工作点推出，本组件的 `c_t` **由 `t` 唯一确定**；③ ASL 面向多标签正负不平衡，无「良性误报」的安全语义 |
| 2 | **AdaCSL** — Volk & Singer，*Adaptive Cost-Sensitive Learning in Neural Networks for Misclassification Cost Problems*，*Intelligent Systems with Applications* 2023（arXiv `2111.07382`） | 把**阈值比**与**代价比**乘进负类损失：`L = −y log ŷ − (C(1,0)/C(0,1))·((1−T′)/T′)·(1−y)log(1−ŷ)`（其 Theorem 2）；阈值按验证集**分组最优阈值**逐 epoch 更新 | **第二接近**：阈值**确实进入损失权重**。**两处不同**：① 权重是**类级**（作用于**全部**负样本），本组件是**逐样本**（只作用于当前判恶意的良性样本）；② 阈值来自验证集分组搜索，本组件由**分类工作点直接解析给出** |
| 3 | **Seesaw Loss** — Wang, Zhang, Cui 等，*Seesaw Loss for Long-Tailed Instance Segmentation*，CVPR 2021（arXiv `2008.10032`） | **动态**利用「累计样本数比」＋「**训练中的实例级误分类**」；compensation factor 明确写为「compensate the gradients of **misclassified samples** to **avoid false positives**」 | 目标函数措辞与本组件最像（误分类＋避免假阳）。**两处不同**：① 服务长尾类别频率校正，不涉及**决策阈值**；② 作用在**被误分类样本自身类别项**上，不是「良性类 ＋ 阈值以上额外线性罚」 |
| 4 | **Calibrated Surrogate Losses for Classification with Label-Dependent Costs**（arXiv `1009.2718`） | 铰链情形给出**铰链位于工作点 `α`** 的分段线性代理：`H(η) = η − α`（`η ≥ α`）／`(α−η)/γ`（`η < α`），`γ` 重加权阈值下分支 | 结构上与「铰链在工作点」同源。**三处不同**：① 铰链在**预测概率轴**、面向成本敏感的**校准一致性**；② 其阈值下分支是**缩小**（`/γ`），本组件是**放大**；③ 不针对假阳性的安全语义 |
| 5 | **NuCE**（per-sample uncertainty-driven reweighting，`w = (1 − max_k p_k)^γ`）、**LiLAW**（由当前分数构造 `W_α/W_β/W_δ` 三段权重）、**Focal Loss**（`(1−p_t)^γ`）、**AFL**（学出来的难度系数） | 逐样本、模型输出依赖的**连续**调制 | **无阈值**：权重随输出**平滑**变化，没有「越过工作点后改变斜率」的**折点**。⇒ 反过来说，**Focal 类不是本组件的特例，本组件也不是 Focal 的特例** |
| 6 | **OHEM**（已入库，见 [台账](../../../thesis/methods/第三章-方法来源台账.md) §6.1） | 按损失排序取 top-k 入批 | 是**选择**（0/1 入批），不是**加权**；且用**绝对损失**排序，无工作点诱导 |
| 7 | **cost-sensitive learning with prediction-dependent costs** `c_i(ŷ_i)` | — | 该**子类**在综述性材料中被明确承认（代价可同时依赖实例与模型输出），但**本轮未检得以它为标题的经典论文**；且其代价通常来自**外生变量**（金额、寿命），非模型输出 |

### L.3 已查检索式与工具状态（如实登记）

- **本地混合检索**（索引 `built_at 2026-09-11T02:52`，`note_count 2229`，`chunk_count 156766`，**非 stale**）：查询式 `cost-sensitive learning asymmetric misclassification cost false positive weighting`、`threshold-dependent sample weighting decision threshold loss reweighting`、`误报加权 代价敏感 不平衡 损失函数`、`loss amplification above threshold false positive penalty detection`。**返回的是近邻家族**（Neyman-Pearson 分类、CALIBURN 保形风险控制、Extreme-FPR 恶意软件检测、Online Adaptive Anomaly Thresholding、QuantTree），**无一篇命中本组件的精确形态**。
- **Zotero 语义检索**：`cost-sensitive learning asymmetric misclassification cost false positive weighting` → 返回 10 条但**相似度全为负**（−0.077 ~ −0.242），命中集中在标签移位与域适配，**无相关项**。
- **rg 扫描**：`wiki/papers/` 全库 5 组模式（`cost-sensitive`／`代价敏感`／`threshold-dependent`／`decision threshold`／`focal loss`；`false positive.*weight`／`误报.*加权`／`asymmetric.*loss`／`class weight`；`ramp loss`／`loss truncation`／`hinge`；`AdaCSL`／`prediction-dependent`／`instance-dependent cost`；`extreme FPR`／`operating point`／`工作点`）**均无本组件的同构记载**。
- **在线补充检索式**：`asymmetric loss multi-label false positive probability threshold shift`、`instance-dependent cost-sensitive learning loss weighting depends on model prediction false positive penalty threshold`、`AdaCSL adaptive cost-sensitive learning negative class weight validation threshold`、`"loss reweighting" misclassified samples current model prediction per-sample weight false positive penalty detection`、`training loss piecewise linear reweighting hinge above threshold decision boundary operating point aware loss`。

### L.4 表述纪律（**强制，随结论一起写**）

1. **禁「首次」**，一律写 **「未检得同构先例」**——「未检得」不是不存在证明（同族术语高度不统一：instance-dependent cost／prediction-dependent cost／augmentation reweighting／hard-view mining／operating-point-aware loss／calibration-consistent surrogate）。
2. **不得把「未检得复合」当作创新差量已成立**。**每一半的成分都有先例**；按本路线 MMEL 的先例教训，**「只差一个复合」不自动等于足够大的方法创新差量**。本组件若要作为正式机制主张，须由 **H 臂的同预算单因素实验**（判据 G2／G3／G4）支撑，**不能靠文献空白支撑**。
3. **与组件 1 的关系不变**：组件 2 的职责已由 F／G 臂实测界定为**纯 FPR 保护**（G 臂检出与 A 持平而 FPR `0.0120` 低于 A `0.0145`，见 [task_plan](task_plan.md) §5.6.2）——**该实验结论不因本次文献排重而改变**。
4. **可安全借鉴之处（不是差量主张）**：ASL 的「负类概率平移」提示**阈值可作超参之外的解析选择**；AdaCSL 的「阈值比进权重」给出了 `(1−T′)/T′` 这一**可直接对照的参数化**；Seesaw 的 compensation factor 提供了「**误分类 → 避免假阳**」的**目标函数措辞先例**。若正文需要为「为什么以工作点为激活点」给文献依据，这三条**是可以引的**（但均需先按 `raw/`+`wiki/` 流程入库）。

### L.5 待办

- 若正文要引 ASL／AdaCSL／Seesaw 中任一，**须先入库全文**（`raw/` 原件 + `wiki/` 全文笔记 + Zotero + INDEX），当前状态为**仅在线候选，不得支撑正文论断**。
- `1009.2718` 的作者与 venue **未核验**（本轮只取到 ar5iv 页面），入库时须补题录。

## I 主代理验收问答与结论（2026-09-11）

> 本节回应主代理对 `beffd50` 的验收反馈（三采纳、一待定）与五个疑问。**只作文献层与设计层回答，不构成任何实验授权或判据冻结。**

### I.1 裁决反馈 1 确认：自证命题的引用结构成立，但须加三条精确化

**成立。** 「作为命题给出 + 我们自己的推导 + 引 REINFORCE 基线理论经典与 RLOO 作对照」这条路可行，但有三处必须写死：

1. **命题前提必须显式编号写出**：① 组内基线 `b_i` **只用 `y_(i)` 之外的样本**构造；② `y_(1..k) ~i.i.d. π_θ(·|x)`。证明只用一步 `E_{y~π_θ}[∇_θ log π_θ(y|x)] = 0`（对 `Σ_y π_θ = 1` 求导）。**前提缺失则命题不成立**（这正是全组均值基线 `(1−1/k)` 缩放的来源）。
2. **RLOO 不能作无偏性的证成者**，只能作「同一基线的另一处表述」的对照引用（其 p.6 是散文断言，非定理）。
3. **方差缩减不得写进命题**——不是保守，而是**数学上不成立**：`Var[(R−b)G] = E[R²G²] − 2E[b]·E[RG²] + E[b²]·E[G²]`，只有 `b` 与 `R` 相关性足够时方差才下降；LOO 的 `b` 是组内噪估计，**无一般性方差缩减保证**。本课题的方差主张若要有，只能由 H 臂**同预算实测**承担，不由命题承担。

**文献可得性提示（证据纪律）**：**Williams 1992 与 Kool et al. 2019 均不在本仓库**（`fd` 逐项核验，2026-09-11，零命中）。正文若要指名引用，须先按 `raw/` + `wiki/` 完成入库与全文笔记；否则改为不指名的标准事实表述。**建议入库 Williams 1992**（成本低、经典、可稳定获取）。

### I.2 Q2：摘要级证据**不够**支撑「威胁模型存在性」

仓库纪律两处明文，不因引用场合（威胁模型 vs 方法）而放宽：

- 根 `AGENTS.md`：「在线题录、摘要……只作候选发现；**没有 `raw/` 原件与 `wiki/` 全文笔记的来源不得升级为全文证据**」。
- `thesis/AGENTS.md`：「**摘要、在线题录和搜索结果不得支撑正文论断**」「正式参考文献只接收经 `raw/` 原件与 `wiki/` 全文笔记核验的条目」。

**判定：三篇都必须在正式引用前完成全文入库**（`raw/` 原件 + `wiki/` 全文笔记 + 对应 `INDEX.md` 更新）。摘要级只够支撑「候选存在」与检索方向，**不够支撑正文任何一句**。

**可获取性评估（供排期，**不是**下载授权）**：Barreno 2006 有 CMU 技术报告公开版；Drahuntsov & Rabchun 2021 所在 CEST 为机构开放获取；Barbierato 2026 的 MDPI 为开放获取，本轮 403 属反爬而非 paywall。**三篇均属「能拿到全文」类别**，因此**没有理由降到摘要级引用**。

### I.3 Q3：撤稿论文（arXiv:2601.14505）的处理

**建议：正文与参考文献均不引。**

1. 它**不能支撑任何主张**（撤稿理由为「技术贡献有缺陷」），且未过全文核验门 ⇒ 按纪律进不了正文。
2. 其「场景最贴合」恰恰是最危险处：审稿人若认识此文，**引而未标撤稿＝诚信问题；标了撤稿＝对主张零贡献、只增篇幅**。
3. **威胁模型存在性已有更稳支撑**（Barbierato 2026 + Drahuntsov 2021 + Barreno 2006），不需要它。

**唯一例外**：导师／学院明确要求全面覆盖时，以**脚注**出现，措辞限于「该预印本已撤稿，不作为依据」，**不得进参考文献表**。过程文档保留完整登记（已做，§H.2.1 第 3 行）。

### I.4 Q4：H 臂正文措辞边界（两句示例）

**✅ 可写**（差量落在「反用为训练信号」，不宣称威胁模型首创；引用部分待 I.2 入库后生效）：

> 「误报注入已被归入针对检测系统的可用性攻击与告警疲劳攻击范畴 [Barreno 2006; Barbierato 2026]，相关工作集中于威胁建模与影响评估。本章的差量在于把该威胁模型**反用为训练信号**：对良性样本构造字符扰动近邻组，以组内相对误报优势驱动更新，使模型在源期即对『良性近邻被误判』敏感。」

**❌ 不可写**（三处硬伤）：

> 「本章首次提出误报注入攻击，攻击者通过制造误报耗尽防御方告警预算；本章提出的组相对机制通过方差缩减显著提升了对该类攻击的鲁棒性。」

硬伤：①「首次提出」与 2006／2021／2026 已有文献冲突；②「方差缩减」无支撑（见 I.1.3）；③ 在 H 臂按 `task_plan` 判据（G2／G3／G4）出数前，「显著提升」属未证。

**时态纪律**：可写版本的**引用部分**须等 I.2 全文入库，**机制部分**须等 H 臂出数。**两者齐备前，任何一段都不进正文。**

### I.5 Q5：本课题的理论深度档位建议

**建议档位：1–2 个自证命题 ＋ 完整初等证明（正文给陈述与编号前提，附录给 3–5 行证明）＋ 1 段可复现数值核验 ＋ 1 条适用边界声明。**

| 件 | 内容 |
| --- | --- |
| 命题 P1 | 留一基线下的组相对优势是 REINFORCE 梯度的**无偏**估计（前提两条，见 I.1.1） |
| 命题 P2（可选） | 全组均值基线的期望为 `(1−1/k)` 倍 ⇒ 为「用留一而非全组均值」这一设计选择提供依据 |
| 证明 | 3–5 行，只用 `E[∇logπ]=0`；不引入未验证假设 |
| 数值核验 | 精确枚举（27 组 / 机器精度）作附录一小节，脚本落盘可复现 |
| 边界声明 | 命题只保证**期望无偏**；**不承诺方差缩减、不承诺收敛率** |

**为什么该档位「不低于参照」**：朱的账本是 3 定理／引理，但 **0 个给出编号假设、误差界或收敛率**，其中 1 个前提是被假定的（引理 1）、1 个「证明」是论证散文（定理 2）。**实质标准是「每条理论主张可被独立核验」，不是条数。** 1–2 条能被复算的命题，占据的是朱用 3 条空转定理想要占据的同一位置。

**为什么「不过度声称」**：命题数刻意压到 1–2——每多一条就多一份被追问「前提成立吗」的风险。**并明确放弃朱式强度词**（全局更优均衡点／严格约束 Hessian 迹／充要条件／从根本上提升）。

### I.6 C 臂改造（Drichel 恒定 1:1）：**建议加，但主代理理解须更正一处**

**更正（按实现核验 `official_p2p3.py` L151–L217，2026-09-11）：D 臂当前不在 1:1。**

- 主批 `idx = order[bi*128:(bi+1)*128]` 取自 6 万混合池（良性／DGA 各 3 万）⇒ 期望 **64 良性 : 64 DGA**；
- B／D 各追加约 64 个变体（全部标 1）⇒ **整批 64 良性 : 128 恶意 = `1:2`**；
- C 追加 `K=4` 全变体（约 256）⇒ **64 : 320 ≈ `1:5`**（与恢复卡登记的「批内恶意:良性 ≈ 5:1」一致）；
- 且**脚本自身注释（L172–L174）已声明**：D 与 B **同为 64 变体配额、批次规模 192、恶意:良性倾斜度相同，唯一差量 = 变体选择机制**。

**因此三点结论**：

1. **「配比 × 选择机制」的正交分离已由 B vs D 完成**（同配额、同倾斜度、唯一差量＝随机选 vs 组内 `fooled−组均值` top-64）。**现有归因链不缺这一条，不需要新臂来补。**
2. **C'（`1:1`、随机选）vs D（`1:2`、组过滤）同时改变两个因素 ⇒ 不构成正交对照**。若要真正正交，C' 还须再配一个「`1:1` + 组过滤」臂才补齐 2×2 的另一半——那不是「一个臂」的成本。
3. **C' 的真正价值是外部效度，不是内部归因**：Drichel §4.4.2 用恒定 `256:256 = 1:1`；本课题若要在正文说「对齐 Drichel 配比」或与其做任何对照，**必须先有 1:1 下的读数**。

**结论：建议加（~10 分钟 screening 成本可接受），但归类为「配比／外部效度基线臂」，不是机制消融臂，也不进 A／G／D／F 的 2×2 链**——进链会破坏既有归因结构（AGENTS：`2×2` 不得夹带第三模块）。它回答的问题是「本方法在文献配比下是否仍成立」，**不是**「配比是不是增益来源」。

**前置冻结项**：「恒定 1:1」必须先写明分子分母——**良性数 : 对抗数？DGA 原样本计入哪一侧？**（Drichel 的 1:1 是 256 clean : 256 adversarial，其中 clean 为**纯良性**）。定义不冻结，该臂不可比。

---

## 定性更正：`K = 8` 是实验自变量，**不是**门禁违规（P 臂，2026-09-11）

> **本节日志的更正对象是本日早些时候的初版登记**——初版把 P 臂 `K = 8` 记为「魔法数字门禁违规」并认领违规；**经用户反问后由主代理重新定性：该登记属过度自我归责，予以更正**。

**正确类型**：`K = 8` 是 **`V3` 理论预测驱动的对照实验自变量**（探针扫描维度：`V3` 的缺口收缩 `Θ(K^{−1/τ})` 实测曲线 `K = 1–4` 已齐全 ⇒ 取相邻点 `K = 8` 检验「覆盖-收益转化」），**不是结论参数** ⇒ **不适用魔法数字门禁**——**与「扫描学习率不需要为每个 `lr` 提供文献依据」同理**。

**由此登记的规则（口径）**：**结论参数**（要进入最终方法／论文的超参）**须过门禁七项**；**实验自变量**（探针扫描维度）**只需合理覆盖 ＋ 事后登记**。

**真正的门禁时刻（预告，已在方案 §5.12.5 第 5 条落盘）**：**P 臂若阳性、要把 `K = 8` 写入最终方法** ⇒ **必须先补 `K` 扫描（`4`／`8`／`16`）＋ 成本权衡登记**（时间约 ×1.8，须实测）；完成前不得进入正式方法或正式运行合同。

**误判归因（防复发）**：把「**实验自变量**」与「**结论参数**」混为一谈，导致**在错误的环节自我归责**。**识别方法（一句话）**：**先问该数值是否要进入最终方法／论文**——**否**＝实验自变量（登记覆盖与用途即可）；**是**＝结论参数（须过门禁七项）。

---

（以下为初版登记的留痕，已被上方更正覆盖，保留以供追溯）

**初版登记（同日，已更正）**：`K = 8` 曾按「流程违规」登记——`K = 8` **在写入代码时未登记任何可追溯依据**。

**事实**：P 臂把 D 的候选数由 `K = 4` 改为 `K = 8`（实现见 `official_p2p3.py`，注释「搜索预算扩展，定理 3／`V3` 的训练级检验：与 D 唯一差量 ＝ `K` `4→8`」）。**该值的写入没有经过**根 `AGENTS.md` 的「**魔法数字门禁**」：数值写入方案／代码／配置前须登记**用途与值、全文文献页码或公式、数学或统计推导、真实数据诊断或源侧实验制品路径、适用边界、是否接触最终目标标签、核验状态**，并同时通过**机制依据与本数据可行性**核验。实际写入时**上述各项全缺**，「`K` 翻倍」属**朴素直觉**。

**（初版正文中「与上次事故的关系（模式识别）」「补登记与止损」「防复发」三段随更正一并作废**——它们都建立在「**本次构成门禁违规**」这一**已被推翻的前提**上；其中仍成立的内容（`K = 8` 的依据、二值问题、成本登记、门禁关卡预告）已按正确类型改写于上方与方案 §5.12.5。）

## 2026-09-23 O 臂 `K(L)` 依据核查：V3 长度归因更正

**事实源**：`verify_thm3_budget.py` SHA-256 `6ed0b531a8c0a0c0ed39795407058fe47cf650e11703085794b99e802f836d91` 及 `verify-thm3-result.json` 只对 T18 DGA 验证前7,500个域名、每域4候选汇总 `K'=1…4` 的总体曲线，没有长度字段、分层表或 `K(L)` 试验。原先方案 §5.14 将“V3 缺口在长短域名间不均”写成已证，**超出了该制品**，现予以更正。

**同一旧制品的探索性分面**：`verify-thm1-real-scores.npz` SHA-256 `b6f555d85baf8039801630cdc2f1f4db65ed4b0ffc21cecddd97d5eed8d0ea38` 含 `u[7500,4]` 与30,000个变体字符串；先复算域列表 SHA-256 与内置摘要一致，再确认每组4个变体的 eSLD 主体长度完全相同。按这7,500个源验证域名的长度四分位数 `7/15/25` 形成仅用于描述的区间。`E_1` 为四候选的均值，`E_4` 为四候选最大值；`E_4−E_1` 是当前候选池内把搜索数由1增加到4的平均增益。

| 主体长度 | 域名数 | `E_1` | `E_4` | `E_4−E_1` | `1−E_4` |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4–7 | 1,955 | 0.428397 | 0.751891 | 0.323495 | 0.248109 |
| 8–15 | 1,944 | 0.650409 | 0.924229 | 0.273820 | 0.075771 |
| 16–25 | 2,017 | 0.296343 | 0.510870 | 0.214527 | 0.489130 |
| 26–41 | 1,584 | 0.319149 | 0.612079 | 0.292931 | 0.387921 |

四档的边际收益**不随长度单调增加**。`1−E_4` 只是对分数上界1的剩余量，不是已知合法攻击全集的真实 `sup` 缺口；样本又是 T18 验证文件的前7,500行，未证明代表全部源期成员。该分面只支持“长度与搜索收益可能有关、需重新设计真实源侧检验”，不支持“长域必需更大 `K`”、任何具体 `K(L)` 公式、训练收益或正式论文结论；未读取 T20–T25。

**数学动机与下一证伪**：若单步两位置替换且字符集37种，长度为 `L` 的位置组合数为 `C(L,2)`；但候选总空间增大不能推出随机候选的成功概率下降，因为成功编辑数也可能增长。先在独立源侧成员上冻结长度分面，测 `K=1/2/4/8` 的边际最难分数与成功率，再预先固定 `K(L)` 与固定 `K=4` 的相同平均候选生成／评分预算、相同入批配额和更新步数，比较干净FPR与对抗FNR。若不存在稳定长度条件收益或等预算下两轴无改进，O 不晋级。公开论文直接依据仍由网页版检索回收并需本地原文核验。
