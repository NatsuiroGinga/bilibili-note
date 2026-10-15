# 实施计划：第四章最小先导——跨年度组鲁棒训练

> **日期**：2026-10-15
> **上位**：`thesis/methods/第四章研究问题卡-条件漂移下的鲁棒训练.md`（判据冻结处）
> **目的**：只回答一个问题——**以年度为组的最坏组风险目标，能否把 2024 年度的检测能力拉回来。**
> **实现代理**：唯一，`sonnet`。主代理不放行第二个实现代理改同一范围。

---

## 1. 文件边界（**严格**）

| 动作 | 路径 |
| --- | --- |
| **新建**（唯一新建的代码） | `thesis/experiments/llm_probe/tools/ch4_lamda_group_robust_pilot.py` |
| **禁止改动** | `ch3_lamda_domain_il_e4.py`（第三章全部证据由它产出） |
| **禁止改动** | `ch4_lamda_rank_gated_acquisition_e2.py`（E2 制品链） |
| **禁止改动** | `thesis/chapters/**`、`thesis/figures/**` |
| **新建制品目录** | `thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-group-robust-pilot/` |

## 2. 接口

**导入**（同目录，脚本有 `if __name__ == "__main__"` 保护）：
`load_year, ChenEncoderMLP, split_by_year, ReplayBuffer, iterate_batches_parts, evaluate, reuse_by_deficit, write_json, now_utc`，常量 `DOMAIN_YEARS, OFFICIAL_*, THRESHOLD, SEED`。

**数据根**：从环境变量 `LAMDA_DATA_ROOT` 解析；未设置即报错退出，**不得硬编码**。导入后覆盖被导入模块的 `DATA_ROOT`。

**主线（两臂共用同一数据流）**：与第三章主臂逐字一致——`quota` 切分 ＋ `deficit` 复用、`buffer-repeat=2`、`memory=200`、`epochs=10`、`batch=1024`、`lr=0.01`、`seed=42`、阈值 0.5。

**两臂**：

| 臂 | 目标 |
| --- | --- |
| `er` | 经验风险最小化（第三章基线，**必须复现 0.8170**） |
| `groupdro` | 组鲁棒：按年度分组，用指数梯度更新组权重 $q_g \propto q_g\exp(\eta\,\bar\ell_g)$，样本损失按 $q_{g(x)}$ 加权后归一化 |

**组定义（冻结）**：某次训练用到的 parts 里，**每个年度块自成一組**（当年度分片为一组，缓冲中每个年度块各为一组）。组权重向量长度随已见年度增长。

**关键实现约束**：`groupdro` 只改**损失加权**，**不得改动**缓冲构成、复用倍数、轮数、批大小、学习率——即固定第三章配置，只加风险目标（这是研究问题卡 §2 的硬要求）。

## 3. 判据（**跑前冻结，与本文件同时写出**）

**主判据**：2024 年度测试分片上的 F1，`groupdro − er`。

- **支持**：$\Delta F_1(2024) > 0$ 且配对 bootstrap 95% CI 不含 0，**且**早期年度（2013／2014／2016）的 F1 下降不超过同年零假设尺度。
- **部分支持**：2024 改善但 CI 含 0。
- **证伪**：2024 不升，或早期年度显著下降（搬移错误而非降低最坏风险）。
- **强证伪**：$\Delta F_1(2024) \le 0$ 且 CI 不含 0 ⇒ **卡作废，第四章重新选题**。

**不确定性口径**：单一冻结种子 42（禁多种子）；测试集配对 bootstrap $n$=2000，**只量化样本不确定性，不冒充训练随机性**。

**辅助量（确定性）**：逐年 F1；组权重 $q_g$ 的末轮分布（看最坏组是否真被抬起来——**若 2025 组（18 条正例）吃掉权重，须如实报告**，这是研究问题卡 M2 的风险）。

## 4. 制品

`e4p_protocol.json`（跑前写出）／`e4p_results.json`（逐年 F1 ＋ 组权重轨迹）／`preds_<arm>_<year>.npz`／`full_pilot.log`。

## 5. 验收命令（按序，任一步失败即停）

```bash
PY=/opt/miniconda3/envs/rwkv/bin/python
TOOLS=thesis/experiments/llm_probe/tools
export LAMDA_DATA_ROOT=/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe/runs/data-raw/lamda-iclr2026-baseline-ad9614bdd5556767

$PY -m py_compile $TOOLS/ch4_lamda_group_robust_pilot.py
$PY $TOOLS/ch4_lamda_group_robust_pilot.py --arm er        # 期望末年 12 年平均 F1 == 0.8170
$PY $TOOLS/ch4_lamda_group_robust_pilot.py --arm groupdro
```

## 6. 阻塞条件

- `--arm er` 复现不出 `0.8170` ⇒ 立即停，报主代理；**不得调数凑**。
- `LAMDA_DATA_ROOT` 未设置或不存在 ⇒ 报错退出。
- 需要改动 E4／E2 脚本才能完成 ⇒ 停，报主代理改计划；不自行修改。

## 7. 成本

每臂一次 12 年度流，实测约 2 分钟（MPS 单进程）。两臂合计约 5 分钟。**同刻只跑一个进程。**

## 8. 报告必须含

技能收据（`daily-coding` 路径／SHA256／读取时刻 ＋ 清单勾选）／每条验收命令的**原样输出**（尤其 `--arm er` 的实际 F1）／逐年 F1 两臂对照表／$\Delta F_1(2024)$ 与 bootstrap CI／**末轮组权重分布**／与判据逐条机械对照（支持／部分支持／证伪／强证伪）——**只做机械对照，不替主代理下最终裁决**／未做项与任何对规格的偏离。
