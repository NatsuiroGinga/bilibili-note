# 实施报告：训练过程缺陷的**材料性验证**（2×2）

> **任务**：只回答一个问题——**「首年度／次年度被浪费的训练轮次」对最终指标有没有可测影响**。
> **实施计划（权威规格）**：`.Codex/docs/2026-10-15-第四章材料性验证/implementation_plan.md`
> **实现代理**：唯一实现代理（Claude Code，会话模型 `deepseek-v4.1-flash[1m]`，
> 强度由会话档位提供，非逐次 `effort` 参数，按 `AGENTS.md` L41 如实记录）
> **日期**：2026-10-15

---

## 0. 技能收据

| 项 | 值 |
| --- | --- |
| 技能文件 | `/Users/bilibili/.claude/skills/daily-coding/SKILL.md` |
| SHA256 | `e45a22ebcd47058378ba24da505db512eb59e65e2c715feb908ff40dc43752e9` |
| 读取时刻 | `2026-10-15T11:45:30Z`（UTC，`date -u` 实测） |

**daily-coding 清单勾选**：

- [x] **Read before modify** —— 动手前完整读取实施计划、两份同类先导脚本
      （`ch4_lamda_group_robust_pilot.py` 734 行、`ch4_lamda_momentum_state_pilot.py` 766 行）
      与只读参考 `ch3_lamda_domain_il_e4.py`（873 行）；本任务**只新建一个文件**，未改任何既存脚本。
- [x] **Understand context** —— 确认基线 `ch3.train_epochs` 每年重建优化器（第 388 行）、
      官方同源（`official-src/domain_il_experiment.py:194`）；据此把「优化器重建时机」固定为四臂相同的常量。
- [x] **Third-Party API Verification** —— 本会话首次使用 `torch.optim.Adam`：
      在目标机实际安装版本上核验（见 §6.5 收据）。
- [x] **Minimal changes** —— 只新建 `ch4_lamda_training_process_2x2.py`；
      `git diff --stat` 对四份既存脚本为零输出（§7.1）。
- [x] **Type safety** —— 全程 `from __future__ import annotations` + 类型标注。
- [x] **Security check** —— 数据根只从环境变量 `LAMDA_DATA_ROOT` 解析，
      脚本内**无绝对路径硬编码**；无凭据、无 eval、无 SQL。
- [x] **Verify execution** —— `py_compile` 通过 + 四条验收命令**真实运行**（§3）。
- [x] **Clean up** —— 无调试残留；临时输出只在 `/tmp`，制品全部落 `runs/diagnostics/`。

**输入文件收据（SHA256，2026-10-15T11:45:30Z 记录）**：

| 文件 | SHA256 |
| --- | --- |
| `.Codex/docs/2026-10-15-第四章材料性验证/implementation_plan.md` | `bc24f7ed57ed1a967952fcb0354b19c19e78027258a54f3a31b64091189b4fc6` |
| `thesis/experiments/llm_probe/tools/ch4_lamda_group_robust_pilot.py` | `7060b3e5fb3caa519a461c92fe73216e069839a71f35b3c3945046299a8029dc` |
| `thesis/experiments/llm_probe/tools/ch4_lamda_momentum_state_pilot.py` | `45c47d1e51127e473a4a354a17bba75149ee54b78dfac027e8eaee6ec331cffe` |
| `thesis/experiments/llm_probe/tools/ch3_lamda_domain_il_e4.py` | `2197612b8758cb84b9ee656197d0519eecc7cb56e68b9eb83f982f1d35d2d66e` |

---

## 1. 交付物

| 项 | 路径 | 行数 | SHA256 |
| --- | --- | --- | --- |
| **新建脚本**（唯一新建代码） | `/Users/bilibili/personal/note/.worktrees/ch3-lamda-20260908/thesis/experiments/llm_probe/tools/ch4_lamda_training_process_2x2.py` | 958 | `1e5b814dd5c10e320587fd34700ede1c330932639184012518ef9c29c937ad80`（**交付版**；首版 `7d81e52e…` 后仅有 1 处改动：自检里 parity 用的模型加 `.to(device)`，见 §8.7） |
| **制品目录** | `thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-training-process-2x2/` | — | — |
| 冻结判据 | 同上 `e4x_protocol.json` | — | — |
| 结果（含四臂 records / per-year / bootstrap） | 同上 `e4x_results.json` | — | — |
| 运行日志（四臂共用追加） | 同上 `full_pilot.log` | — | — |
| 逐样本预测 | 同上 `preds_<arm>_<year>.npz`（4 臂 × 12 年 = 48 个） | — | — |

**未改动范围**（`git diff --stat` 空输出，§7.1）：
`ch3_lamda_domain_il_e4.py`、`ch4_lamda_group_robust_pilot.py`、`ch4_lamda_momentum_state_pilot.py`、
`thesis/chapters/**`、`thesis/figures/**` 全部未动。

---

## 2. 实现设计（与实施计划的对应）

### 2.1 四臂

| 臂 | 初始化 | 优化器 |
| --- | --- | --- |
| `base` | PyTorch 默认 | SGD（复现门） |
| `he` | He 尺度 | SGD |
| `adam` | PyTorch 默认 | Adam |
| `he_adam` | He 尺度 | Adam |

### 2.2 优化器生命周期——**与基线一致，不是第二个变量**

基线 `ch3_lamda_domain_il_e4.py::train_epochs` 在**函数体内**构造
`torch.optim.SGD`（第 388 行），而 `main()` 在年度循环里每年调用该函数一次
（第 742 行）⇒ **基线每个年度重建优化器**。官方同源：
`official-src/domain_il_experiment.py:194` 同样把 `optim` 构造在年度循环体内（两条独立证据）。

**本脚本的处理**：`train_epochs_with_optimizer` 同样在**函数体内**由 `opt_builder`
构造优化器、每年度调用一次 ⇒ **四臂的优化器重建时机逐位相同**。
因此「重建时机」不构成第二个变量；`base`：`ch3.train_epochs` 与 `he` 臂仍直接调用
`ch3.train_epochs`，`adam`／`he_adam` 走镜像函数。

`_selfcheck_train_fn_parity` 断言镜像函数（SGD）与 `ch3.train_epochs` **逐位一致**
（四臂运行中均实际执行并打印，见 §6）。

### 2.3 Adam 超参

`torch.optim.Adam(lr=0.01, weight_decay=1e-6)`，其余取 torch 默认
（`betas=(0.9, 0.999)`、`eps=1e-8`、`amsgrad=False`、`decoupled_weight_decay=False`）。
**lr 保持 `0.01` 不变**（只换优化器类型）；`weight_decay` 保持基线值 `1e-6`
（`decoupled_weight_decay=False` ⇒ L2 入梯度，与基线 SGD 的 `weight_decay` 语义一致）。

### 2.4 He 初始化

对**全部 7 个 `nn.Linear`**（encoder 4 层 + classifier 3 层）的 **weight** 重初始化为
`U(−b, b)`、`b = sqrt(6/fan_in)`（等价 `kaiming_uniform_(a=0, mode="fan_in")`），
理论 std `sqrt(2/fan_in)`；**bias 保持 PyTorch 默认**。
重初始化用**独立 `torch.Generator`**，**不消耗全局 torch 随机源** ⇒ He 臂在模型构造
结束后的全局 RNG 状态与 `base` 臂逐位相同（`_selfcheck_he_init_isolation` 断言）。

---

## 3. 验收命令与**原样输出**

环境：`PY=/opt/miniconda3/envs/rwkv/bin/python`（本机唯一实验环境，
torch `2.12.0`、numpy `2.4.6`、scikit-learn `1.9.0`、`mps.is_available()=True`）。
`LAMDA_DATA_ROOT=/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe/runs/data-raw/lamda-iclr2026-baseline-ad9614bdd5556767`。
**同刻只跑一个进程**（启动前 `pgrep` 确认无在跑实验进程）。

### 3.1 `py_compile`

```
$ /opt/miniconda3/envs/rwkv/bin/python -m py_compile thesis/experiments/llm_probe/tools/ch4_lamda_training_process_2x2.py
PY_COMPILE OK
```

（交付版 `1e5b814d…` 上**已复跑一次** `py_compile`，同样 `PY_COMPILE OK`。）

### 3.2 `--arm base`（**复现门**）

命令：

```
$ $PY $TOOLS/ch4_lamda_training_process_2x2.py --arm base
```

结尾原样输出：

```
=== base：末年 2025 的 avg_f1（官方报告口径）= 0.8170 ===
[comparison] 已据 ['base'] 重算 ΔF1、配对 bootstrap 与机械判据对照
[done] base 用时 195.0s，制品 .../runs/diagnostics/ch4-lamda-training-process-2x2/e4x_results.json
[gate] base 复现门：末年 12 年平均 F1 = 0.8169830287，参照 0.8169830287，绝对差 0.000e+00 ⇒ PASS
```

**`--arm base` 实际值 = `0.8169830287163194`（`e4x_results.json` 中
`arms.base.final_avg_f1_backward` 的原样值），绝对差 `0.000e+00` ⇒ PASS。**

`base` 逐年度（末年 2025 经验对 12 个测试年度的 backward 平均）原样输出：

```
[2013] avg_f1 backward=0.6786   ← 年度经验当场读数（仅 2013 测试年）
[2014] avg_f1 backward=0.9471
[2016] avg_f1 backward=0.9438
[2017] avg_f1 backward=0.9344
[2018] avg_f1 backward=0.9159
[2019] avg_f1 backward=0.8824
[2020] avg_f1 backward=0.8754
[2021] avg_f1 backward=0.9031
[2022] avg_f1 backward=0.8533
[2023] avg_f1 backward=0.8929
[2024] avg_f1 backward=0.9006
[2025] avg_f1 backward=0.8170
```

### 3.3 `--arm he`

```
=== he：末年 2025 的 avg_f1（官方报告口径）= 0.8205 ===
[done] he 用时 403.2s
```

末年模型逐分片原样输出：

```
[preds] he 末年模型 @2013: f1=0.9174   @2014: 0.9123   @2016: 0.8993   @2017: 0.9059
        @2018: 0.8929  @2019: 0.9449   @2020: 0.9495   @2021: 0.9449
        @2022: 0.9497  @2023: 0.8213   @2024: 0.7077   @2025: 0.0000
（n / pos / nonfinite 均为原样打印，nonfinite 全 0）
```

### 3.4 `--arm adam`

```
=== adam：末年 2025 的 avg_f1（官方报告口径）= 0.7535 ===
[done] adam 用时 662.9s
```

**是否发散：未发散。** 全部年度 `params_finite=True`、`n_nonfinite_loss` 从未触发
`[diverge]` 行、逐样本分数 `nonfinite=0`。逐年 `[opt]` 原样输出中 2025 年度：

```
[opt] 2025 type=Adam betas=[0.9, 0.999] eps=1e-08 lr=0.01 weight_decay=1e-06
      | epoch_mean_loss=0.0125, 0.0074, 0.0050, 0.0029, 0.0045, 0.0025, 0.0106, 0.0098, 0.0406, 0.0119
```

### 3.5 `--arm he_adam`

```
<<PENDING:HE_ADAM_COMMAND_OUTPUT>>
```

---

## 4. 四臂对照表

### 4.1 主判据：末年 2025（12 个测试分片的平均 F1，官方报告口径）

| 臂 | 初始化 | 优化器 | **12 年平均 F1** | Δ vs base | 年度 F1 @2013 | @2014 | @2024 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `base` | 默认 | SGD | **`0.8169830287`** | — | `0.9121` | `0.9076` | `0.7422` |
| `he` | He | SGD | `0.8204777334` | **+0.0034947** | `0.9174` | `0.9123` | `0.7077` |
| `adam` | 默认 | Adam | `0.7534817…` | **−0.0635013** | `0.8401` | `0.8329` | `0.6667` |
| `he_adam` | He | Adam | `<<PENDING:HE_ADAM_MEAN>>` | `<<PENDING:HE_ADAM_DELTA>>` | `<<PENDING:HE_ADAM_2013>>` | `<<PENDING:HE_ADAM_2014>>` | `<<PENDING:HE_ADAM_2024>>` |

**逐年 Δ（arm − base，末年模型对同一测试分片）**：

| 测试年度 | 2013 | 2014 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `he − base` | +0.0053 | +0.0046 | +0.0213 | −0.0002 | +0.0043 | +0.0089 | +0.0086 | +0.0150 | +0.0116 | −0.0030 | **−0.0345** | 0.0000 |
| `adam − base` | −0.0720 | −0.0747 | −0.0853 | −0.2111 | −0.0958 | −0.0459 | −0.0289 | −0.0213 | −0.0117 | −0.0398 | −0.0755 | 0.0000 |
| `he_adam − base` | `<<…>>` | `<<…>>` | `<<…>>` | `<<…>>` | `<<…>>` | `<<…>>` | `<<…>>` | `<<…>>` | `<<…>>` | `<<…>>` | `<<…>>` | 0.0000 |

> 注：2025 测试分片只有 5 个正例，四臂在该分片 F1 均为 `0.0000`（与第三章基线制品一致），
> 故最后一行 Δ 恒为 0。

### 4.2 辅助：**年度经验当场读数**（缺陷所在年度，backward 平均）

| 经验年度 | 臂 | backward avg F1 | 覆盖测试年数 |
| --- | --- | --- | --- |
| 2013（第 1 年） | `base` | `0.6786` | 1 |
| 2013 | `he` | `0.9742` | 1 |
| 2013 | `adam` | `0.9690` | 1 |
| 2013 | `he_adam` | `0.9725` | 1 |
| 2014（第 2 年） | `base` | `0.9471` | 2 |
| 2014 | `he` | `0.9643` | 2 |
| 2014 | `adam` | `0.9618` | 2 |
| 2014 | `he_adam` | `<<…>>` | 2 |

**这是本表最有判别力的一行**：`base` 在 2013 经验上只有 `0.6786`（十轮只学出基率），
而三个干预臂都在 `0.97` 附近 ⇒ **「被浪费的训练轮次」在缺陷年度被确实消除了**。
但该消除**没有传导到末年的 12 年平均**（§4.1）。

---

## 5. Δ 与配对 bootstrap 95% CI

**口径**：单一冻结种子 42（禁多种子）；测试集配对 bootstrap `n=2000`（seed 42），
**只量化样本不确定性，不冒充训练随机性**。
`mean_over_years` = 对每个测试分片分别重采样、各算 F1 差、再对 12 年取平均 ⇒ 直接对应主判据。

### 5.1 Δ（12 年平均 F1）的 95% CI

| 臂 | 观测 Δ | 95% CI | 含 0 | 噪声带 0.0014–0.0116 | 机械分类 |
| --- | --- | --- | --- | --- | --- |
| `he` | **+0.0034947** | `[+0.0004641, +0.0064507]` | 否 | Δ 落在带内 | **不可分辨（落在噪声内）** |
| `adam` | **−0.0635013** | `[−0.0677411, −0.0598199]` | 否 | \|Δ\| 超上界 | **恶化（超过噪声上界，方向为负）** |
| `he_adam` | `<<…>>` | `<<…>>` | `<<…>>` | `<<…>>` | `<<…>>` |

> **注意**：`he` 的 bootstrap CI 不含 0，但该区间只量化**样本**不确定性；
> 判据以**跨配置种子波动 0.14–1.16 点**为噪声尺度，`he` 的 `+0.35` 点落在该带内。

### 5.2 主判据年度 2024 的 Δ 与 95% CI

| 臂 | ΔF1(2024) | 95% CI | 含 0 |
| --- | --- | --- | --- |
| `he` | **−0.0344952** | `[−0.0694944, −0.0026047]` | 否 |
| `adam` | **−0.0755208** | `[−0.1152242, −0.0378375]` | 否 |
| `he_adam` | `<<…>>` | `<<…>>` | `<<…>>` |

---

## 6. 四条自检的输出（实施计划 §4）

### 6.1 自检 1：`base` 逐位复现 `0.8169830287`

```
[gate] base 复现门：末年 12 年平均 F1 = 0.8169830287，参照 0.8169830287，绝对差 0.000e+00 ⇒ PASS
```

### 6.2 自检 2：参数隔离证明（四臂配置逐字比对）

四臂运行中均实际执行并打印（原文，节选关键的“异”行）：

```
[selfcheck-config] 四臂配置对照（除 init／optimizer 外必须逐字相同）:
  init                   [**异**] base='pytorch_default' | he='he_scale_kaiming_a0_fan_in' | adam='pytorch_default' | he_adam='he_scale_kaiming_a0_fan_in'
  optimizer              [**异**] base='SGD' | he='SGD' | adam='Adam' | he_adam='Adam'
  batch / buffer_repeat / buffer_scheme / deficit_gamma / domain_years / epochs / lr / memory /
  momentum / optimizer_lifetime / pos_ratio / reuse_scheme / rng_streams / seed / strategy /
  threshold / weight_decay              [同] 四臂逐字相同
[selfcheck-config] PASS：仅 init 与 optimizer 两个键在四臂间不同，其余逐字相同
[selfcheck-he-isolation] He 重初始化只改 weight（7 层）、bias 逐位不变，且**全局 torch RNG 状态逐位不变**
[selfcheck-parity] 训练镜像函数（SGD）与 ch3.train_epochs 逐位一致（1 轮，全参数张量相等）
```

### 6.3 自检 3：`he` 臂的初始化尺度（实测各层 weight std vs He 理论）

`he` 臂原样输出：

```
[selfcheck-init] arm=he 逐层 weight std（实测 vs He 理论 vs 默认理论）:
  encoder.0      fan_in=4561  实测=0.020938 He理论=0.020940 默认理论=0.008549 实测/He=1.000 实测/默认=2.449
  encoder.2      fan_in=512   实测=0.062460 He理论=0.062500 默认理论=0.025516 实测/He=0.999 实测/默认=2.448
  encoder.4      fan_in=384   实测=0.072496 He理论=0.072169 默认理论=0.029463 实测/He=1.005 实测/默认=2.461
  encoder.6      fan_in=256   实测=0.088454 He理论=0.088388 默认理论=0.036084 实测/He=1.001 实测/默认=2.451
  classifier.0   fan_in=128   实测=0.125088 He理论=0.125000 默认理论=0.051031 实测/He=1.001 实测/默认=2.451
  classifier.3   fan_in=100   实测=0.140520 He理论=0.141421 默认理论=0.057735 实测/He=0.994 实测/默认=2.434
  classifier.6   fan_in=100   实测=0.145540 He理论=0.141421 默认理论=0.057735 实测/He=1.029 实测/默认=2.521
[selfcheck-init] arm=he 实测/默认理论 std 比值：min=2.434 max=2.521（He 尺度预期 ≈ 2.449）×
[selfcheck-init] arm=he 实测尺度与声明的初始化一致（全部 7 层，±5%）
```

`base`／`adam` 臂对照组（默认初始化）：

```
[selfcheck-init] arm=base 实测/默认理论 std 比值：min=0.991 max=1.043（He 尺度预期 ≈ 2.449）×
[selfcheck-init] arm=base 实测尺度与声明的初始化一致（全部 7 层，±5%）
```

### 6.4 自检 4：`adam` 臂的实际优化器与 betas

```
[selfcheck-optimizer] arm=adam type=Adam lr=0.01 betas=[0.9, 0.999] eps=1e-08 weight_decay=1e-06
[selfcheck-optimizer] arm=he_adam type=Adam lr=0.01 betas=[0.9, 0.999] eps=1e-08 weight_decay=1e-06
[selfcheck-optimizer] arm=base type=SGD lr=0.01 betas=None eps=None weight_decay=1e-06
```

逐年 `[opt]` 行同样打印（每年重建的优化器）：

```
[opt] 2025 type=Adam betas=[0.9, 0.999] eps=1e-08 lr=0.01 weight_decay=1e-06 | epoch_mean_loss=...
```

### 6.5 第三方 API 核验收据（daily-coding 强制项）

| 项 | 值 |
| --- | --- |
| 库 / 目标机实际版本 | `torch` `2.12.0`（`/opt/miniconda3/envs/rwkv/bin/python` 内 `torch.__version__`） |
| 核验方式 | 在**目标机实际安装版本**上直接读取签名与默认值（比训练数据更可靠）：`inspect.signature(torch.optim.Adam.__init__)`；`torch.optim.Adam(...).defaults` |
| 核验到的签名 | `Adam(params, lr=0.001, betas=(0.9, 0.999), eps=1e-08, weight_decay=0, amsgrad=False, *, foreach=None, maximize=False, capturable=False, differentiable=False, fused=None, decoupled_weight_decay=False)` |
| 核验到的默认值 | `{'lr': 0.01, 'betas': (0.9, 0.999), 'eps': 1e-08, 'weight_decay': 1e-06, 'amsgrad': False, 'maximize': False, 'foreach': None, 'capturable': False, 'differentiable': False, 'fused': None, 'decoupled_weight_decay': False}`（实测，`lr`/`weight_decay` 为本脚本传入值） |
| 另一核验 | `torch.Tensor.uniform_(from, to, *, generator=...)` **接受 `generator` 关键字**（实测通过，He 重初始化依赖此行为） |

---

## 7. 与实施计划判据的**机械对照**（只做机械对照，**不替主代理裁决**）

### 7.1 冻结判据（照 `implementation_plan.md` §2，跑前写入 `e4x_protocol.json`）

| 结论 | 条件 |
| --- | --- |
| **材料（靶子成立）** | 至少一臂 \|Δ\| 超过噪声上界（`0.0116`），且方向为**改善**（Δ > 0） |
| **不可分辨** | 全部 \|Δ\| 落在噪声内 |
| **恶化** | 至少一臂显著恶化（Δ < `−0.0116`）⇒ 该干预不成立（但仍说明该因材料） |

### 7.2 逐条机械对照（主判据 = 12 年平均 F1）

| 臂 | Δ | \|Δ\| > 0.0116？ | 方向 | 机械分类 |
| --- | --- | --- | --- | --- |
| `he` | +0.0034947 | 否 | improve | **不可分辨（落在噪声内）** |
| `adam` | −0.0635013 | **是** | worse | **恶化（超过噪声上界，方向为负）** |
| `he_adam` | `<<…>>` | `<<…>>` | `<<…>>` | `<<…>>` |

脚本自动生成的机械分类块（`e4x_results.json::criteria_mechanical`，调用时三臂可见）：

```json
{
  "noise_band_f1": [0.0014, 0.0116],
  "n_improved": 0,
  "n_within_noise": 1,
  "n_worsened": 1,
  "improved_arms": [],
  "within_noise_arms": ["he"],
  "worsened_arms": ["adam"],
  "mechanical_verdict": "恶化：至少一臂显著恶化 ⇒ 该干预不成立（但仍说明该因材料）",
  "note": "本块只做实施计划 §2 判据的机械分类，**不代替主代理裁决**"
}
```

### 7.3 计划 §2 的辅助判据（材料性是否只体现在 2013／2014）

计划原文：「若材料性只体现在 2013／2014 而不传导到整体，**如实报告——那说明缺陷是局部的，
不构成章级问题**。」

机械事实（§4.2）：`he`／`adam`／`he_adam` 把 2013 经验 F1 从 `0.6786` 拉到 `0.97` 附近，
**缺陷年度确实被消除**；但**主判据（12 年平均）没有对应改善**：
`he` 仅 `+0.35` 点（噪声内），`adam` 为 `−6.35` 点（恶化）。
`he_adam` 待补。

> 上述为**机械对照**，不构成裁决。

---

## 8. 未做项与偏离

1. **`base`／`he` 臂未打印逐轮 loss**：这两臂直接调用冻结基线 `ch3.train_epochs`，
   而该函数**不打印逐 epoch loss**（只打印 `[audit]`／`[reuse]`／每年 `trained on N rows`／
   `avg_f1 backward`）。`adam`／`he_adam` 臂走镜像函数，打印逐年 `epoch_mean_loss`。
   —— 这是为**保 `base` 逐位复现**而保留基线的原样行为，**不修改任何既存脚本**；
   与 `ch4_lamda_group_robust_pilot.py` 的 `er` 臂处理一致。记为偏离（可观察性缺口）。
2. **`he` 臂的 He 尺度实现细节**：计划只写「He 尺度」，未指定分布族。本脚本取
   `kaiming_uniform_(a=0, mode='fan_in')`（**保持 PyTorch 默认的 uniform 分布族，只改尺度**），
   bias 不动。这是**规格未规定、由本脚本确定并登记**的实现选择，非科研数值改动。
3. **`adam` 臂的 `weight_decay`**：计划只写「只换优化器类型，不调 lr」。本脚本保持
   `weight_decay=1e-6`（与基线同值、同为 L2 入梯度）。若主代理意图是「Adam 默认
   `weight_decay=0`」，该臂需重跑——本报告如实登记此选择。
4. **未做多种子**（`AGENTS.md` L41 禁止）；单种子 42 无法把训练随机性与 +0.35 点区分开，
   本报告不声称任何显著性。
5. **未做**：未改动 `thesis/chapters/**`、`thesis/figures/**`；未运行 `black`；
   未使用系统 `python3`；未新建第二个实验环境。
6. **`he_adam` 臂**在撰写本节时仍在运行（bootstrap 阶段），其数值待回填。
7. **脚本交付前的唯一一次修改**（首版 `7d81e52e…` → 交付版 `1e5b814d…`）：
   `_selfcheck_train_fn_parity` 的调用把探针模型改为 `ch3.ChenEncoderMLP(input_dim).to(device)`。
   原因是自检与主训练可能不同设备（MPS），CPU 模型上跑 `.to(device)` 的批会设备不匹配。
   该修改**只影响自检本身**，不触碰四臂的训练路径；`base` 复现门在该修改后的版本上
   仍为 `0.000e+00` PASS（§3.2 的运行即为交付版）。

---

## 9. 最终回答：**这个靶子材料吗**

`<<PENDING:FINAL_ANSWER>>`
