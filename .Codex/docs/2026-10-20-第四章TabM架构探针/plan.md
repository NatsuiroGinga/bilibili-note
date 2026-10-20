# 第四章 TabM 架构探针：实施计划与冻结判据

> **状态**：判据冻结于看到任何 TabM 读数之前（2026-10-20 17:05）。
> **触发**：零训练先验诊断（`ch4-lamda-posthoc-prior-diag`）裁决 `posthoc_family_insufficient`，
> 训练方法线按冻结映射收口；转架构线，按《第四章-架构机制文献调研.md》探针 #1 执行。
> **上游**：`checkpoint-8-第四章进度.md` §十一/§十二；TabM 机制事实源
> `wiki/papers/methodology/2025-Gorishniy-TabM参数高效集成.md`（ICLR 2025，arXiv:2410.24210v3，
> 原件 SHA-256 `a6988aa1…`，Zotero `Y4ICR5KF`）。

---

## 一、机制与移植声明（不是复现）

TabM（Gorishniy et al., ICLR 2025）＝共享主权重＋成员专属低开销适配（BatchEnsemble 型），
优化成员损失均值，推理聚合成员概率。移植要点（全部有 wiki 全文页码锚点）：

| 机制 | 移植形态 | 依据 |
|---|---|---|
| 每层成员适配 | `W_eff_i = W ⊙ (r_i s_i^T)`，等价实现 `y_i = s_i ⊙ (W(r_i ⊙ x_i) + b) + β_i` | 物理页 4，§3.2 |
| 初始化 | 第一组乘性适配（首层 `r_i`）随机符号 ±1；其余 `r=1`、`s=1`、`β=0`，初始网络≈TabM-mini | 物理页 5–6，§3.3 |
| 训练目标 | 成员 BCE 的均值 | README/物理页 9 |
| 推理 | 成员 sigmoid 概率的算术平均 | README/物理页 9 |
| 成员数 | **k∈{4,8}**，不用论文的 k=32：骨干 512/384/256/128 远窄于论文 512–1024 块宽，论文图 7 明示 k 与宽深交互、过大有害 | 物理页 10，§5.3 |

**与论文协议的偏差（任务化适配，须在结果中如实披露）**：论文统一用 AdamW＋全局梯度裁剪＋
验证早停；本探针保持第三章冻结协议（SGD lr=0.01、momentum 0.9、wd 1e-6、batch 1024、10 epoch、
无裁剪无早停），只换结构——单变量原则。结果只能称「TabM 机制在 LAMDA Domain-IL 协议下的
任务化移植」，不得称复现 TabM。

## 二、协议（与 base 臂逐位同源）

- 数据与回放：`ch4_lamda_paat_pilot.build_parts`（quota 200、年度配额、缺口加权复用 m_max=2、
  repeat 2、全局洗牌），`buf_rng`/`rng` 同种子流消费顺序与 PAAT base 臂一致；
- 训练循环：镜像 `ch3.train_epochs`（优化器年度重建、`iterate_batches_parts` 同流），
  仅损失改为成员 BCE 均值；
- 评价：`ch3.evaluate`（阈值 0.5）＋`ch3.score_shard`（末年 12 年 backward 面板）；
- 种子 42；模型随机性（首层符号初始化）由 `torch.manual_seed(42)` 承载；
- 参照：`runs/diagnostics/ch4-lamda-paat-pilot/base-result.json`（12y `0.8169830287163194`），
  只读，不重跑 base。

## 三、臂与判据（冻结）

- 臂：`tabm4`、`tabm8`（k=4、k=8）。
- **支持（章级门，与 PAAT 判据同构）**：2023 与 2024 的 backward F1 均 ≥ base + **1.0 pp**，
  且 12 年平均 ≥ base − **0.20 pp** → 进入任务化设计与消融。
- **否决**：2023 或 2024 增益 < **+0.3 pp**，或 12 年平均 < base − **0.50 pp** → TabM 关闭，
  转探针清单下一项（FM/PNN 或 FT-Transformer，需另行冻结）。
- **中间带**：落在两者之间 → 只做一轮机制诊断（AUC/阈值定位），不追加调参轮。
- **机制核查（披露项，不设门）**：报告 2023/2024 的 `delta_auc`（vs base 预测分数）。
  若 F1 增益伴随 AUC 下降，增益属阈值位置效应——鉴于 M1 的教训（G3），该情形不得写入
  「表示改善」类主张。

## 四、验收

```bash
cd thesis/experiments/llm_probe
/opt/miniconda3/envs/rwkv/bin/python tools/ch4_lamda_tabm_pilot.py --arm tabm4
/opt/miniconda3/envs/rwkv/bin/python tools/ch4_lamda_tabm_pilot.py --arm tabm8
```

- 产物：`runs/diagnostics/ch4-lamda-tabm-pilot/{tabm4,tabm8}-result.json`＋逐年 `preds_*.npz`＋
  `tabm-comparison.json`；
- 每臂打印 12y mean、2023/2024、判据布尔值；脚本对判据机械断言并写进 JSON；
- 成本预期：k=4 约 10–15 分钟，k=8 约 20–30 分钟（MPS，串行）。

## 五、边界

- 不修改任何既有文件；只新增本目录脚本与 `runs/diagnostics/ch4-lamda-tabm-pilot/` 产物；
- 本探针只判 TabM 机制存废，不冻结章级方法；章级方法的任务化改造（若有正信号）另立判据；
- 脚本落盘后按「修改即检查点」规则提交。
