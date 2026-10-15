# 实施计划：跨年度动量状态的先导（机制待证）

> **日期**：2026-10-15
> **状态**：**提案，零文献支撑**（本地库对优化器状态／动量／可塑性丧失零命中；文献代理在跑）。本实验的作用是**给出实测佐证或否决**，不是验证一个已成立的方向。
> **上位**：`thesis/methods/第四章-候选方向比较与选择.md`（该文件记录了三个已否决方向）
> **实现代理**：唯一，`sonnet`。

---

## 0. 假说（**必须逐字写进 `e4m_protocol.json`**）

**H**：在年度序列的分布漂移下，SGD 的动量缓冲会把**上一个年度的梯度方向**带进当前年度的训练；跨年度边界时这些方向来自**分布已经变了的年度**，因而拖累适应。

**观测量（机制层，免费）**：年度边界处，进入新年度时的动量缓冲 $\mathbf{m}$ 与该年度**前若干批梯度方向** $\mathbf{g}_{\text{new}}$ 的**余弦相似度** $\cos(\mathbf{m},\mathbf{g}_{\text{new}})$。
- 若 $\cos\lesssim 0$ ⇒ 动量携带的是**无关甚至反向**的历史方向 ⇒ 假说有机制层支撑
- 若 $\cos$ 显著为正 ⇒ 动量仍是有效加速项 ⇒ **假说不成立，即使 F1 有变化也不能归因于它**

**H0（证伪面）**：年末重置动量不提高 2024 年度 F1；或提高但 $\cos>0$（即提升另有原因）。

---

## 1. 文件边界

| 动作 | 路径 |
| --- | --- |
| **新建**（唯一新建代码） | `thesis/experiments/llm_probe/tools/ch4_lamda_momentum_state_pilot.py` |
| **禁止改动** | `ch3_lamda_domain_il_e4.py`、`ch4_lamda_rank_gated_acquisition_e2.py`、`ch4_lamda_group_robust_pilot.py` |
| **禁止改动** | `thesis/chapters/**`、`thesis/figures/**` |
| **制品目录** | `runs/diagnostics/ch4-lamda-momentum-state-pilot/` |

**可参考不可改**：`ch4_lamda_group_robust_pilot.py`（734 行）已示范「新脚本导入 E4、自带训练循环、复现门逐位通过、均匀参数下与 `nn.BCELoss()` 等价」的写法，**照它的结构写**。

## 2. 干预与臂（**冻结**）

**干预**：年度边界（进入新年度的第一个 batch 之前）对动量缓冲做 $\mathbf{m}\leftarrow \beta\cdot\mathbf{m}$。**其余一字不动**（缓冲构成、复用倍数、轮数、批大小、学习率、阈值、种子）。

| 臂 | β | 含义 |
| --- | --- | --- |
| `beta1` | 1.0 | 现状（**必须逐位复现 `0.8170`**） |
| `beta05` | 0.5 | 部分衰减 |
| `beta0` | 0.0 | 完全重置 |

**只允许动量缓冲被 $\beta$ 改变**——用运行内断言或打印证明（照 group-robust 先导的三条自检格式）。

## 3. 观测与制品

- **逐年 F1**（三臂）
- **每年的边界余弦 $\cos(\mathbf{m},\mathbf{g}_{\text{new}})$**：用新年度**前 5 个 batch** 的梯度均值与进入该年度时的 $\mathbf{m}$ 计算；**逐年度列出**
- `e4m_protocol.json`（**跑前写出**：假说原文、观测量定义、三臂、判据、种子、不确定性口径）
- `e4m_results.json`、`full_pilot.log`

## 4. 判据（**跑前冻结**）

**主判据**：2024 年度测试分片 F1，`beta0 − beta1` 与 `beta05 − beta1`。

| 结论 | 条件 |
| --- | --- |
| **支持** | 至少一臂 $\Delta F_1(2024)>0$ 且配对 bootstrap 95% CI 不含 0，**且** $\cos$ 的年度分布显著非正 |
| **部分支持** | $\Delta F_1(2024)>0$ 但 CI 含 0，**或** $\cos$ 非正但 F1 未动 |
| **证伪** | 两臂 $\Delta F_1(2024)\le 0$，或 $\cos$ 显著为正（提升另有原因） |
| **强证伪** | 两臂 $\Delta F_1(2024)\le 0$ **且** CI 不含 0 |

**不确定性**：单一冻结种子 42（禁多种子）；测试集配对 bootstrap $n$=2000，**只量化样本不确定性，不冒充训练随机性**。

**辅助**：12 年平均 F1（与第三章基线 `0.8170` 对照）。

## 5. 验收命令（按序，任一步失败即停）

```bash
PY=/opt/miniconda3/envs/rwkv/bin/python
TOOLS=thesis/experiments/llm_probe/tools
export LAMDA_DATA_ROOT=/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe/runs/data-raw/lamda-iclr2026-baseline-ad9614bdd5556767

$PY -m py_compile $TOOLS/ch4_lamda_momentum_state_pilot.py
$PY $TOOLS/ch4_lamda_momentum_state_pilot.py --beta 1.0    # 必须逐位复现 0.8170
$PY $TOOLS/ch4_lamda_momentum_state_pilot.py --beta 0.5
$PY $TOOLS/ch4_lamda_momentum_state_pilot.py --beta 0.0
```

## 6. 阻塞条件

- `--beta 1.0` 复现不出 `0.8170` ⇒ 停，报主代理，**不得调数凑**。
- 需要改动 E4／E2／group-robust 三份脚本才能完成 ⇒ 停，报主代理。
- `LAMDA_DATA_ROOT` 未设置 ⇒ 报错退出。

## 7. 成本

每臂一次 12 年度流，约 2 分钟；三臂约 6 分钟。**同刻只跑一个进程。**

## 8. 报告必须含

技能收据（`daily-coding` 路径／SHA256／读取时刻 ＋ 清单勾选）／新建文件路径与行数／**每条命令原样输出**（尤其 `--beta 1.0` 的实际 F1 与「只有动量缓冲被改动」的证据）／三臂逐年 F1 对照表／$\Delta F_1(2024)$ 与 CI／**每年的边界余弦表**／与判据逐条机械对照（支持/部分支持/证伪/强证伪）——**只做机械对照，不替主代理裁决**／未做项与任何偏离（**有偏离必须显式写出**）。

**并且必须明确回答一句**：这个实验是**支持还是否决**了 §0 的假说——**不得因为 F1 有变化就声称机制被证实**，机制层要看 $\cos$。
