# 第四章零训练先验校正诊断：实施计划

> **状态**：判据在看到任何新读数前冻结（2026-10-20 16:35）。
> **目的**：判定 2023/2024 的 F1 损失是**决策边界/先验**问题还是**表示/梯度**问题，从而决定第四章训练方法线是否收口。
> **上游**：`checkpoint-8-第四章进度.md` §十一（cRT 文献结论）。

---

## 一、要回答的问题

cRT/DRW 及 BSM/LA/LADE/OLS/LIMES 的机制前提是 label shift（`p(x|y)` 不变）。本课题实测 `p(x|y)` 跨年漂移 33.5× 采样噪声，因此这些方法不能直接作为机制主张。

在动手实现任何重平衡训练前，先用**零训练**手段确定上界：

> 仅靠事后调整决策阈值（不做任何训练、不使用目标年标签之外的额外信息），最多能把 2023/2024 的 F1 提高多少？

### 关键数学事实（决定本诊断的有效性）

二分类下，任何**单调**的后验变换 `g(s)`（包括 Logit Adjustment、PC Softmax、先验偏移、bias 平移、Platt 缩放）满足：

```
g(s) >= 0.5  <=>  s >= g^{-1}(0.5)
```

即全部退化为对原分数的**一个阈值平移**。因此：

**逐阈值扫描得到的 oracle F1，是整个零训练后验校正族的严格上界。**

只有改变排序的非单调方法（如 kNN、多模型融合）不在此族内——那些方向已在 `ch4-lamda-inversion-pilot/knn-head-diag.json` 中实测关闭。

## 二、输入与文件边界

**唯一输入（只读）**：

- `thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-paat-pilot/preds_base_<year>.npz`（`base` = 第三章回放底座，12 年，`y_true`/`y_score`/`threshold`）
- `.../preds_m1_<year>.npz`（仅用于 M1 归因）
- `.../base-result.json`（复现门：`mean_f1 = 0.8169830287163194`）
- `runs/diagnostics/ch3-lamda-e5-replay-buffer-audit-v1/buffer_composition.json`（各年训练集正例率）

**新增文件（只允许这两个）**：

- `thesis/experiments/llm_probe/tools/ch4_lamda_posthoc_prior_diag.py`
- `thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-posthoc-prior-diag/posthoc-prior-diag.json`

脚本必须幂等、只读输入、不训练、不改动任何已有文件。

## 三、指标定义

对每个年度 `t`（2013–2025，缺 2015），在 `base` 分数上计算：

1. **`f1_05`**：阈值 0.5 的 F1。必须逐位复现 `base-result.json` 的 `backward_f1[t]`（容差 `1e-9`），否则脚本以非零码退出。这是输入完整性门。
2. **`auc`**：ROC AUC（阈值无关的排序质量）。
3. **`test_pos_rate`**：目标年测试集正例率（仅用于描述，**不得**用于选择阈值）。
4. **`tau_oracle` / `f1_oracle`**：在全部唯一分数上扫描阈值（预测为 `s >= tau`），取 F1 最大者。`delta_oracle_pp = (f1_oracle - f1_05) * 100`。
5. **`tau_rate` / `f1_rate`**：**可部署**——按训练年正例率 `π_t`（来自 buffer audit）做分位数匹配，`tau_rate = quantile(s, 1 - π_t)`，预测 `s >= tau_rate`。不使用任何测试标签。
6. **`f1_prev_oracle`**：**可部署**——把上一年度的 oracle 阈值原样用于本年度（年度索引 k≥1；首年为空）。
7. **`f1_prev_rate`**：**可部署**——把上一年度的告警率（告警数/测试数）用于本年度分位数匹配（k≥1）。
8. **M1 归因**：同法计算 `auc_base`、`auc_m1`，以及 `delta_auc = auc_m1 - auc_base`、`delta_f1_05 = (f1_m1 - f1_base)*100`。

## 四、冻结判据（看到读数前）

- **G1｜族上界**：`delta_oracle_pp >= 1.0` 且 **2023 与 2024 同时成立** ⇒ 事后校正族在原理上够得着第四章门槛；否则整个族（含 LA/PC/bias/cRT 的纯决策部分）**不足以**补上缺口。
- **G2｜可部署性**：在 `f1_rate`、`f1_prev_oracle`、`f1_prev_rate` 三个可部署规则中，至少一个满足：2024 `delta >= 1.0 pp`，且 12 年平均不低于 base − 0.20 pp。
- **G3｜归因**：若 2023 或 2024 的 `delta_auc > +0.002`，M1 的增益归为**排序/表示**；若 `|delta_auc| <= 0.002` 但 F1 变化 ≥ 0.5 pp，归为**阈值位置/校准**。

### 裁决映射（预先写死）

| G1 | G2 | 裁决 | 下一步 |
|---|---|---|---|
| 不通过 | — | **事后校正族无效** | 训练方法线收口 → TabM 架构探针 |
| 通过 | 不通过 | **需要目标年先验，但漂移下不可部署** | 事后线收口；训练重平衡至多再给一次机会 |
| 通过 | 通过 | **存在可部署的零训练校正** | 但它属决策层，不能作第四章内容；只能作为“表示可用”的证据，训练重平衡的判据另立 |

- **2025 年**：测试正例 ≤ 5，仅作探索性报告，不进入 G1/G2。
- **12 年平均**：同时报告官方 12 年口径（含 2025）与排除 2025 的 11 年口径。

## 五、验收命令

```bash
cd thesis/experiments/llm_probe
/opt/miniconda3/envs/rwkv/bin/python tools/ch4_lamda_posthoc_prior_diag.py
```

通过条件：

1. 进程退出码 0；
2. 12 年 `f1_05` 与 `base-result.json` 的 `backward_f1` 全部在 `1e-9` 内一致；
3. 生成 `posthoc-prior-diag.json`，含 `criteria`（G1/G2/G3 各自的布尔值与证据）与 `verdict`。

## 六、失败与阻塞

- 任一 npz 缺失 → 停止并报告缺失年份，**不得**用其他臂替代；
- 复现门不一致 → 停止并报告差异，**不得**继续计算；
- 不修改任何已有文件、不重训、不写入 `raw/`、`wiki/`、`thesis/` 正文。

## 七、交给实现代理的边界

- 模型：sonnet（机械实现，规格已冻结；Claude Code 无法逐次设置 `effort`，如实记录为继承默认强度）；
- 只写本计划第二节允许的两个文件；
- 运行后立即把 `posthoc-prior-diag.json` 落盘，再回报关键数字；
- 报告必须给出：G1/G2/G3 的布尔值、2023/2024/12 年平均的 `f1_05`/`f1_oracle`/`f1_rate`、以及 `delta_auc`。
