# 过程笔记：理论／算法家族综述

> 派发 2026-10-14；模型 opus、effort high。本文件边做边写，不等任务结束补写。

## 判据（经主代理两次修正后的最终版）

- **主判据（决定能否成章）**：① 机制故事 ② 可写的形式化（收敛/结构/界/复杂度都算）
  ③ 本机快速可实测。
- **风险指标（不排序、不筛除）**：定理是否落在指标上。
- **主表最重要的两列**：「分析套路怎么写」（该族理论小节的常见形态 + 2–3 个已写并被接受的
  论文例证，只核存在不核对错）＋「机制词汇表」（该族提供的现成机制说法）。
- **排序主键**：分析套路好不好套 > 机制词汇能否套到 LAMDA 任务 > 恶意软件先例（有先例好写）
  > 成本 > 本地占据。指标定理降为风险指标。
- **空白分两类**：机制空白（没人提出过该机制）vs 应用空白（机制有、未用到 Android 恶意软件/
  该任务）。分别标注，主代理按两类分别排序。

## 网络通路（主代理实测）

- HuggingFace 等被重置站点：`curl -x http://127.0.0.1:7890`；arXiv 直连。
- `WebFetch` 对部分站点不可用，报错即换 curl 重试，不得判「来源不可得」。

## 本地已占区域（依据，2026-10-14 读）

来源：`.Codex/docs/LAMDA/LAMDA路线总控.md`、`LAMDA第三章恢复卡.md`（2026-09-09 状态）、
`thesis/methods/第三章-LAMDA任务与方案筛选矩阵.md`（2026-10-14 筛选计划）。

**已在 LAMDA 上实验并被否决/封顶的（不得再作为第三章主机制）**：

| 家族/实现 | 运行身份 | 结果 |
| --- | --- | --- |
| 标准经验回放 ER | `ch3-lamda-domain-il-naive-replay-screening-seed42-v1`（阶段 A） | 资格通过：FPR 与旧恶意负向翻转率降，AP/FNR 略差。**只作基线**，不承担创新 |
| 安全记忆（PCT 式保护集合） | 阶段 B `ch3-lamda-security-regression-ablation-seed42-v1` | 未全面占优；实现偏差（用了当前模型分数非上一冻结模型）已作废该复现资格 |
| 角色记忆 M＋双侧修复 O（ER+M/ER+O/ER+M+O） | 阶段 C `ch3-lamda-mo-source-dev-screening-seed42-v1` | 三臂均 `reject_screening` |
| 缺口感知条件风险门控 | `ch3-lamda-gap-repair-screening-seed42-v1` | `reject_implementation`：修复 FNR 降但 FPR 升至 0.139 |
| 双风险梯度投影（A-GEM 类） | `ch3-lamda-dual-risk-projection-screening-seed42-v1` | 安全保持有信号、恶意修复不足 |
| 双玩家速率约束（Lagrangian 乘子）v1/v2 | `ch3-lamda-dual-player-screening-mps-seed42-v1/v2` | v1 乘子发散全塌缩；v2 乘子几乎不介入、无独立信号 → `reject_implementation` |
| 尾锚约束（尾部高分良性推回） | E1 oracle 检验 `oracle-tail-clip.json` | 受损良性不在冻结高分尾，损伤是全局表征漂移 → `oracle_e1_rejected` |
| 无重训阈值诊断 | 开发期诊断 | F1 仅 +0.00008，不作为机制 |
| PCT+FPR gate 四臂（Cotter/Kumar） | `ch3-lamda-pct-fpr-screening-mps-seed42-v1` | `reject_implementation` |

**本地已有全文、已评估、未运行**（候选池内近邻对照，不是空白）：

- TERM（指数倾斜经验风险）、IWMS（延迟标签持续学习）、DGR（深度生成回放）
- DRO 四篇：GroupDRO／DORO／pAUC-DRO／类别条件 Wasserstein-DRO（L1–L4 本地全文齐）
- TTA 四篇：TENT／EATA／CoTTA／SoTTA＋OWAD（本地全文齐，`wiki/papers/attack-detection/`）
- Chen Android 持续学习、Cebere 九项假设审计（Web 记录）
- V-REx（第四章挖掘代理已核）

**DRIFT 旧线（非本工作树主线，但共享机制史）**：组相对选择与课程调度被自身消融否掉；
累积编辑深度与全局交叉熵选择有效但非设计产物。博弈在 DRIFT 上的具体形式（双侧对手）
被数学否决（目标精确分解为两个独立单侧最坏值）——**新博弈形式必须避开同型塌缩**。

## 查询日志

### 本地混合索引（ch3-drift-20260908 工作树，1,934 条笔记，stale=false）

原始 JSON 落 `raw-queries/`。分块后台执行：
