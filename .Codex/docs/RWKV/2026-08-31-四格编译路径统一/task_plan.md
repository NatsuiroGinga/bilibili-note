# 四格编译路径统一 · 任务计划

<!-- RESEARCH_ROUTE=RWKV -->

- 日期：2026-08-31
- 目标：满足[第三章恢复卡](../RWKV第三章恢复卡.md)第 33 行「论文正式定稿前硬门禁」中
  与执行路径有关的两条：**路径可观测**（收据记录实际调用路径、图断裂与回退）与
  **四格统一**（共同逐流骨干统一编译、C01／C11 排序检查点统一即时、C10／C11 记忆注意力统一）。
- **不在本任务范围**：启动正式四格重跑；读取任何 LSPR24 数组或读数；恢复 C11。

## 硬边界（逐条自查）

1. 只读既有制品 `ch3-ft-c00-dual-selection-cuda-formal-v1`、
   `ch3-ft-c01-entity-ranking-cuda-formal-v1`、`ch3-ft-c10-entity-memory-cuda-formal-v1`
   及两个目标年评价目录，不写不删。
2. 不恢复 `ch3-ft-c11-cem-ber-cuda-formal-v1`。
3. 不读 LSPR24 数组或读数。
4. 修改 `tools/ch3_ft_c00_dual_selection.py` 会使旧 C10 制品不可复现——报告中须写明。
5. 不提多种子、噪声分析、置信区间。
6. 凭据只内联，不入任何文件、日志、提交。
7. 提交只用 pathspec 精确路径，禁止 `git add .`（工作树有 110 余处他会话改动）。

## 任务分解

| # | 任务 | 交付 | 状态 |
| --- | --- | --- | --- |
| T1 | 读懂现状：门禁原文、三个 C11 提交（`0edd522`／`0a47546`／`ee04ee8`）、四格六个前向调用点 | notes.md 第一节 | 已完成 |
| T2 | 目标机接口核验：GPU、torch／CUDA 版本、`torch._dynamo` 可用接口签名 | notes.md 接口核验表 | 已完成 |
| T3 | 设计并实现路径观测层：调用路径台账 ＋ Dynamo 编译／断裂统计 ＋ 回退清单，写入每臂运行收据 | `tools/ch3_ft_execution_path_receipt.py` ＋ 宿主 7 处埋点，提交 `da1a817` | 已完成 |
| T4 | 探针运行（独立运行身份）验证观测层真实产出，而非只通过语法检查 | 8 个探针臂全部 `exit=0`，收据齐全 | 已完成 |
| T5 | 统一方案：逐格路径表、必须即时执行的子模块、能编译的子模块，并用探针核验统一后四格是否真同路径 | 实施报告第三节，`--compare` 判定 `consistent=true` | 已完成 |
| T6 | 无法统一之处如实报告 ＋ 退而求其次方案（四格全即时）代价估计 | 实施报告第四、五节，代价为实测非估算 | 已完成 |
| T7 | 正式重跑前置条件清单 | 实施报告第六节，8 条 | 已完成 |

## 关键假设与证伪方式

| # | 假设 | 证伪方式 | 证伪成本 |
| --- | --- | --- | --- |
| A1 | `torch._dynamo.utils.counters` 在目标机 torch 2.13 上存在且含 `graph_break` 分类 | 目标机 `python -c` 直接打印 | 秒级 |
| A2 | CEM 注意力的 `if bool(has_history.any())`（`ch3_ft_causal_entity_memory.py:334`）与
      `cls_hidden[has_history]`（335～337、357）是图断裂来源 | 目标机对 `CausalEntityMemoryAttention` 单独 `torch._dynamo.explain`，读断裂原因原文 | 分钟级 |
| A3 | `_entity_ranking_bare_forward`（C01）当前**确实**在编译路径下执行，
      与 `_entity_ranking_memory_forward`（C11，已固定 `_orig_mod`）不一致 | 目标机构造最小前向，读 `counters` 与调用对象类型 | 分钟级 |
| A4 | 把 C01 排序检查点也固定到 `_orig_mod` 即可满足门禁第 2 条，且不改变逐流阶段编译产物 | 探针运行前后 `counters["frames"]` 与 `unique_graphs` 对比 | 十分钟级 |
| A5 | 统一后 C00／C01 的逐流阶段、C10／C11 的逐流阶段各自走同一编译产物 | 探针收据的调用路径台账逐格对比 | 十分钟级 |

**五条假设的裁决**（全部由目标机真实运行裁决，无一停留在推论）：

| # | 裁决 | 依据 |
| --- | --- | --- |
| A1 | 成立 | `counters` 含 `graph_break` 且是 `Counter`；另发现更好的 `graph_break_reasons` 直接给文件行号 |
| A2 | 成立 | `explain` 逐行定位 `334/335/336/337`，`graph_break_count=4` |
| A3 | 成立 | `checkpoint(编译体)` 得 `frames 3/3` 并生成符号维核；`checkpoint(_orig_mod)` 得空 `counters` |
| A4 | 成立 | 改后 C01 探针 `ranking_forward_bare = eager`、`frames 4/4`、`graph_break 0` |
| A5 | 成立 | `--compare` 三条门禁条款全部 `consistent = true`，组内断裂签名逐条相同 |

## 阻塞条件

- 服务器不可达或 GPU 被占：只做本机 miniconda `rwkv`（torch 2.12、MPS）上的接口存在性核验，
  并在报告中显式标注「目标机未核验」，不得把本机结论写成目标机事实。
- `torch._dynamo` 接口在目标机缺失：改用可用的替代接口并记录，不得凭记忆写属性名。
