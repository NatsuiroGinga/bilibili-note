# 笔记：重放比率／暴露倍数文献核验

> 代理每完成一个子问题**立即**在本文件追加。禁止任务结束后凭记忆补写。

## 主代理已核事实（跑前基线）

| 事实 | 来源 | 等级 |
| --- | --- | --- |
| 「提高历史样本复用次数」在 RL 称 replay ratio / UTD ratio | WebSearch 命中（IEEE MARL 论文、Experience Replay 综述） | **在线摘要**（未取全文） |
| 已知失效形态：对陈旧样本过拟合、可塑性丧失、primacy bias、样本多样性下降、离策略发散 | 同上 | **在线摘要** |
| 本地 `wiki/papers/` 全文 `rg`「replay ratio／重放比／重放频率」**零命中** | 主代理 `rg`（683 篇笔记） | **实测**（但仅覆盖本地入库范围） |
| 本地文献索引在本工作树**未构建**，无法用混合检索 | `status --json` → `missing_index` | **实测** |

## Q1 — replay ratio / UTD 的定义与出处

（待代理 A 填写）

## Q2 — 持续学习设定下「记忆样本重复暴露」的既有工作

（待代理 A 填写）

## Q3 — 存储预算 × 复用预算的联合约束（**预判缝隙，重点查**）

（待代理 A 填写）

## Q4 — 失效形态在持续学习设定下的实验证据

（待代理 A 填写）

## 代理 B — MEMO / Forget Forgetting

（待代理 B 填写）

## 代理 C — Boyd §5.5.3 / Rahman 2022

（待代理 C 填写）

---

## 主代理直接检索（Google Scholar CLI，2026-10-14）

**用户质询「为什么不用 google scholar」后主代理亲自执行。** 命令：
`~/.local/bin/scholar lookup "<查询式>" --json --limit N`（须 export 代理，见 task_plan）。

**证据等级：仅题录 + 摘要片段**——以下**全部未取全文**，只用于确定下一步读什么。

### 高相关命中（**可能占据主代理预判的缝隙**）

| 论文 | 年份/被引 | 为什么相关 |
| --- | --- | --- |
| **Seo, Koh, Choi,「Budgeted online continual learning by adaptive layer freezing and frequency-based sampling」** ICLR 2025 | 19 | 标题同时含 **Budgeted** 与 **frequency-based sampling**——即「预算 × 采样频率」联合，**正是主代理预判为唯一缝隙的形态** |
| **Ma et al.,「Joint memory optimization for continual learning」** IEEE TNNLS 2025 | 10 | 「**联合记忆优化**」——可能已在做存储与使用的联合求解 |
| **Bagus & Gepperth,「An investigation of replay-based approaches for continual learning」** IJCNN 2021 | 71 | 摘要片段：「**A higher number of epochs or iterations correlates with a better …**」——**直接落在 $m$ 轴** |
| **Zhang, Pfahringer, Frank,「Repeated augmented rehearsal」** NeurIPS 2022 | 91 | 「**Repeated** rehearsal」——记忆样本的重复使用 |
| **Smith et al.,「Adaptive memory replay for continual learning」** 2024 | 62 | 记忆回放的**自适应**调度 |
| **Chaudhry et al.,「Continual learning with tiny episodic memories」** 2019 | 576 | 小容量记忆的奠基作之一 |
| **Brignac & Lobo,「Improving replay sample selection and storage」** 2023 | 31 | 同时动**选择**与**存储** |
| **Rolnick et al.,「Experience replay for continual learning」** NeurIPS 2019 | 2577 | 该方向最高被引奠基作 |
| Cho et al.,「Forget forgetting」ICLR 2026 | 9 | 已下载全文，代理 B 在读 |

### 主代理即时判读（**待代理核实，不得直接引用**）

**「存储预算 × 复用频率的联合约束」大概率不是空白。** 至少两篇（ICLR 2025 的 Budgeted＋frequency、
TNNLS 2025 的 Joint memory optimization）在标题层面就指向该形态。
⇒ 第三章**不能**以「未被联合研究过」立论；差异化必须另找落点。
**⇒ 这正是「用 Google Scholar 而不用摘要式检索」的直接价值：它在我把错误主张写进方案前就命中了。**

### 待办

- 上述九篇**均需取全文**后按 `raw/`→`wiki/` 入库，再作引用与划界
- 优先取：ICLR 2025 Budgeted、TNNLS 2025 Joint memory optimization、IJCNN 2021 Bagus（三篇直接决定主张边界）
