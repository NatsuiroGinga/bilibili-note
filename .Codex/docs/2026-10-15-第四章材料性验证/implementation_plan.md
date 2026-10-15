# 实施计划：训练过程缺陷的**材料性验证**（2×2）

> **日期**：2026-10-15
> **目的**：只回答一个问题——**"首年度/次年度被浪费的训练轮次"对最终指标有没有可测影响**。
> **这是靶子存废的判决实验**：三臂（或四臂）全落在种子噪声内 ⇒ 靶子作废，第四章重新选题。
> **上位**：`thesis/methods/第四章研究问题卡-训练过程.md`
> **实现代理**：唯一，`sonnet`。

---

## 0. 背景（**实测，非推演**）

- 2013 年度十轮损失 `0.6931 → 0.6923`（$=\ln 2$，只学出基率）
- 2014 年度前 4 轮不动、第 5 轮才降
- 初始化 = PyTorch 默认（逐层实测吻合 `kaiming_uniform_(a=√5)`），**7 层连乘信号衰减到 0.2%**
- **零训练假设分离已完成**：偏置假设 ✗、死 ReLU ✗、**尺度衰减 ✓**（换 He 尺度使输出 std 放大 488 倍）
- 文献候选（Gorishniy 2026 等，**外推级**）：**SGD→Adam/AdamW** 在表格数据上多数更优

## 1. 设计：2×2 分离两个因

| 臂 | 初始化 | 优化器 |
| --- | --- | --- |
| `base` | 默认 | SGD（**必须逐位复现 0.8170**） |
| `he` | **He 尺度** | SGD |
| `adam` | 默认 | **Adam** |
| `he_adam` | He 尺度 | Adam |

**只允许这两处改动**，其余一字不动：缓冲构成、复用倍数、轮数、批大小、学习率、阈值、种子、年内正负比例。

**Adam 的超参**：**保持 lr=0.01 不变**（只换优化器类型，不调 lr——否则变量不唯一）。**若 Adam arm 发散或明显不稳，如实报告并把"lr 也需调整"记为发现，不得自行调 lr 重跑。**

## 2. 判据（**跑前冻结，写进 `e4x_protocol.json`**）

**主判据**：**12 年平均 F1**，各干预臂相对 `base` 的差 $\Delta$。

**种子噪声尺度（本课题实测，跑前写死）**：跨配置种子波动 **0.14–1.16 点**。

| 结论 | 条件 |
| --- | --- |
| **材料（靶子成立）** | 至少一臂 $|\Delta|$ 超过噪声上界，且方向为**改善** |
| **不可分辨** | 全部 $|\Delta|$ 落在噪声内 |
| **恶化** | 至少一臂显著恶化 ⇒ 该干预不成立（但仍说明该因**材料**） |

**辅助**：**2013／2014／2024 三个年度的 F1**（缺陷所在年度与目标年度）。若材料性只体现在 2013／2014 而不传导到整体，**如实报告——那说明缺陷是局部的，不构成章级问题**。

**不确定性**：单一冻结种子 42（禁多种子）；测试集配对 bootstrap $n$=2000，**只量化样本不确定性，不冒充训练随机性**。

## 3. 文件边界

| 动作 | 路径 |
| --- | --- |
| **新建**（唯一新建代码） | `thesis/experiments/llm_probe/tools/ch4_lamda_training_process_2x2.py` |
| **禁止改动** | `ch3_lamda_domain_il_e4.py`、`ch4_lamda_rank_gated_acquisition_e2.py`、`ch4_lamda_group_robust_pilot.py`、`ch4_lamda_momentum_state_pilot.py` |
| **禁止改动** | `thesis/chapters/**`、`thesis/figures/**` |
| **制品目录** | `runs/diagnostics/ch4-lamda-training-process-2x2/` |

**可参考不可改**：`ch4_lamda_group_robust_pilot.py`（734 行）与 `ch4_lamda_momentum_state_pilot.py`——两者都已示范「新脚本导入 E4、自带训练循环、复现门逐位通过、参数隔离自检」。**照它们的结构写。**

## 4. 必须带的自检（照前两个先导的格式）

1. `base` 臂**逐位复现** `0.8169830287`
2. **参数隔离证明**：除初始化与优化器外，其余配置逐字相同（打印比对）
3. **`he` 臂的初始化尺度**：实测打印各层 weight std，与 He 理论值比对
4. **`adam` 臂**：打印实际使用的优化器类型与 betas

## 5. 验收命令（按序，任一步失败即停）

```bash
PY=/opt/miniconda3/envs/rwkv/bin/python
TOOLS=thesis/experiments/llm_probe/tools
export LAMDA_DATA_ROOT=/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe/runs/data-raw/lamda-iclr2026-baseline-ad9614bdd5556767

$PY -m py_compile $TOOLS/ch4_lamda_training_process_2x2.py
$PY $TOOLS/ch4_lamda_training_process_2x2.py --arm base       # 必须 0.8170
$PY $TOOLS/ch4_lamda_training_process_2x2.py --arm he
$PY $TOOLS/ch4_lamda_training_process_2x2.py --arm adam
$PY $TOOLS/ch4_lamda_training_process_2x2.py --arm he_adam
```

## 6. 阻塞条件

- `--arm base` 复现不出 `0.8169830287` ⇒ 立即停，报主代理，**不得调数凑**。
- 需要改动四份既存脚本才能完成 ⇒ 停，报主代理。
- `LAMDA_DATA_ROOT` 未设置 ⇒ 报错退出。

## 7. 成本

每臂一次 12 年度流约 2 分钟；四臂约 10 分钟。**同刻只跑一个进程。**

## 8. 报告必须含

技能收据（`daily-coding` 路径／SHA256／读取时刻 ＋ 清单勾选）／新建文件路径与行数／**每条命令原样输出**（尤其 `--arm base` 的实际值）／四臂 12 年平均 ＋ 2013／2014／2024 年度 F1 对照表／各 $\Delta$ 与 bootstrap CI／四条自检的输出／与判据逐条机械对照（材料／不可分辨／恶化）——**只做机械对照，不替主代理裁决**／未做项与任何偏离。

**最后必须明确回答一句**：**这个靶子材料吗**——即"浪费的训练轮次"对最终指标有没有超过噪声的影响。**若不可分辨，直接说不可分辨，不得用"略有改善"之类的措辞软化。**
