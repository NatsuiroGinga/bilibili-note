# LAMDA 前置实验 E1/E2 运行日志

> 实现代理：实现-LAMDA前置实验E1E2（opus，effort=high，实际按会话提供强度执行）。
> 计划：[implementation_plan.md](implementation_plan.md)（提交 `e524eec8`）。
> 本文件是过程日志；正式读数以运行目录内 JSON 制品为准。

## 冻结设置（跑前登记，2026-10-14）

以下数值在看到任何 E1 结果前登记，不得按结果回调。

| 项 | 值 | 依据 |
| --- | --- | --- |
| 模型 | `Linear(4561→128)→BatchNorm1d→ReLU→Dropout(0.5) → Linear(128→64)→BN→ReLU→Dropout(0.5) → Linear(64→32)→BN→ReLU→Dropout(0.5) → Linear(32→1)` | 沿用本地 v3 资格探针 `ch3_lamda_source_near_screening.py` 的 `LamdaMLP`（非论文原配置；论文未报告优化器/学习率/损失，已知复现缺口） |
| 参数量断言 | 594,753（含 3 层 BatchNorm 的 weight+bias：583,936+256+8,256+128+2,080+64+33） | 与 v3 `EXPECTED_PARAMETER_COUNTS["all_features"]` 逐层核算一致 |
| 优化 | Adam，lr `1e-3`，`BCEWithLogitsLoss`，epochs `6`，batch `512`，单种子 `42` | 沿用本地 v3 先例 `effective-config.json`（epochs=6/batch=512/lr=1e-3/seed=42）；「沿用本地先例」而非「论文原配置」 |
| 设备 | `torch.device("mps")`，断言 `torch.mps.is_available()` | 用户明确要求使用 MPS |
| 特征 | `feat_0..feat_4560` 共 4,561 列，int8 读取、按批转 float32 | 数据卡；禁用 `vt_count`（标签来源）、`hash`/`family`/`year_month` 不作特征 |
| 标签 | `label` 列（0=良性，1=恶意），运行时断言取值 ⊆ {0,1} | 数据卡：`vt_detection>=4` 为恶意 |
| 官方协议切分（逐字） | **训练 = 2013_train ∪ 2014_train 中 `year_month ∉ {2013-12, 2014-08}` 的行（实测 137,869 行 = 61,599 + 76,270）；IID 测试 = 2013_test ∪ 2014_test 中 `year_month ∈ {2013-12, 2014-08}` 的行（IID 月只从 test 分片取，与上游 `anoshift_experiment_models_separate.py` 逐行一致：该脚本从 `test_dir` 读 IID 月）** | 上游官方脚本 commit `7728bfafcd5539a286b5f8c47b6f1e3b2d1f4249`，本地副本 `/tmp/anoshift_experiment_models_separate.py`（lines 212-261） |
| E1 目标年评价面板 | 每个目标年 = **该年 train+test 分片合并**（2016–2025） | 与计划 §2.1 参考读数口径逐项吻合：2020 正例 37,084+9,271=46,355、2022 41,648、2023 7,892、2024 794、2025 23，五对五全中；主代理独立核验一致 |
| E1 阈值标定集（A 组） | **源期 test 分片全部良性行**（2013_test ∪ 2014_test，`label==0`，全部月份，实测 19,496 行） | 任务化设定（无直接文献依据），理由：训练从未接触任何 test 分片行 ⇒ 严格 held-out；比仅 IID 月良性（约 1.3k 行，0.1% 预算下仅 1–2 个假阳性，噪声不可接受）大 15 倍。0.1% 预算下实测假阳性数≈19，噪声已在报告中披露 |
| E1 阈值约定 | `thr(b) = np.quantile(源标定集良性分数, 1-b, method="linear")`，恶意判定为 `score >= thr`；同时报告标定集上的实测 FPR（可能略低于预算） | 任务化约定（无直接文献依据）；连续分数下实测 FPR ≈ 预算 |
| E1 预算 | `0.1%` 与 `1%` 两档 | 计划 §2.2 冻结 |
| E1 判据 | 计划 §2.3 预注册判据，跑前冻结，不得改动 | 计划 §2.3 |
| E1 披露规则 | 正例数 < 500 的年份不进主表：2024（794）、2025（23）按路线总控 D1 裁决只作探索性披露；该规则与本次结果无关，跑前已定 | 路线总控 D1（2026-09-09）+ 计划 §2.4 |
| E2 复现口径 | MLP 与 LightGBM 按官方脚本协议：训练数据同上（137,869 行），IID = test 分片 IID 月，FAR = 2018–2025 **test 分片**；阈值 0.5；指标 F1/ROC-AUC/PR-AUC/FPR/FNR | 官方脚本逐行口径；注意官方脚本 VT=0.0001（25,460 维）与论文表 7 声称的 Baseline 0.001（4,561 维）存在已登记的阈值/目录不一致，我们用本地 Baseline 4,561 维 |
| E2 模型超参 | LightGBM：官方脚本原值（lr 0.02, num_leaves 256, min_child_samples 30, subsample 0.8/freq 1, colsample 0.8, reg_alpha/lambda 1.5, n_estimators 5000 + 早停 100 轮于 10% 分层验证集, metric auc, n_jobs 8）；XGBoost：官方原值（max_depth 12, eta 0.05, 3000 轮, logloss；`gpu_hist` 不可用于本机，改 `hist` 并登记）；SVM：官方原值 `CalibratedClassifierCV(LinearSVC(max_iter=10000))`（默认 5 折）；MLP：本仓库固定 594,753 参数模型（**非**官方 Ember_MLP_Net 4.67M 参数，偏差已登记） | 官方脚本原值优先；偏差逐项登记 |
| E2 扩围（主代理 2026-10-14 指令） | 四模型 × 两划分（LightGBM/XGBoost/MLP/SVM × IID/FAR），报 F1/ROC-AUC/PR-AUC/FPR/FNR；判据：GBDT 两划分均显著优于 MLP ⇒ 格式利好 GBDT；MLP 在 FAR 不输 ⇒ 神经骨干可用；介于两者之间 ⇒ 如实报告、双骨干保留 | 主代理指令（冻结于跑前） |

## 侦察结论（写码前核验）

- 官方脚本 `anoshift_experiment_models_separate.py`（上游 commit `7728bfa`）核验要点：训练月份集合 = `{2013*,2014*} \ {2013-12, 2014-08}`；IID 测试月从 `test_dir` 读；`pred_bin = (preds >= 0.5)`；FPR/FNR 由混淆矩阵计算；PR-AUC 列用 `average_precision_score`（即 AP）。
- 数据审计（24 个分片全量）：2013 train/test = 69,144/17,287；2014 train/test = 80,946/20,237；2024 全年正例 635+159=794；2025 全年正例 18+5=23；2013/2014 train 分片中 IID 月行数 = 7,545/4,676。
- 本机 16 GiB RAM；训练矩阵 int8 约 629 MB，逐批转 float32 后上 MPS。
- `torch.mps` 内存接口实测存在：`current_allocated_memory`/`driver_allocated_memory`/`recommended_max_memory`（torch 2.12.0）。

## 执行日志

### 2026-10-14

- 侦察阶段（只读）：恢复路线链、下载核验官方脚本、24 分片数据审计、v3 先例配置核对、环境库检查。发现 `lightgbm`/`xgboost` 缺失，上报主代理。
- 主代理裁决（消息确认）：lightgbm/xgboost 经 `uv pip install --python /opt/miniconda3/envs/rwkv/bin/python` 补齐，记录版本，不动既有依赖；E1 不需要它们，排在 E1 之后。
- 12:25 提交 `2e46f08f`：E1 脚本 + run-log（py_compile + 导入检查通过后提交）。
- 12:26 启动 E1（`os.setsid` 脱离会话，`pgrep` 断言 0→1，单进程）；12:27 完成，墙钟 33.96 s。
- 12:30 依赖收据：`lightgbm 4.7.0`、`xgboost 3.4.1`（uv pip 装入 rwkv，dry-run 确认不动既有依赖）；两库 dylib 均缺系统级 `libomp.dylib`，经 `brew install libomp`（可逆，不触碰任何 Python 包）后导入成功；装后复核 torch 2.12.0 / numpy 2.4.6 / sklearn 1.9.0 / scipy 1.18.1 均未变动。
- 独立复算（从 predictions npz 逐样本重算 2017/2020/2023 的 AUROC/AP/A 组 FNR·FPR/B 组阈值）：与 metrics.json 全部 diff = 0。

## E1 结果（2026-10-14，run_id `ch3-lamda-preflight-e1-threshold-transfer-v1`）

**制品**：`/Users/bilibili/personal/note/.worktrees/ch3-lamda-20260908/thesis/experiments/llm_probe/runs/diagnostics/ch3-lamda-preflight-e1-threshold-transfer-v1/`
（`metrics.json` SHA256 `ccfdda7e…234de2a`，`run-manifest.json` SHA256 `f6976967…8e2d28d`，预测逐样本 npz 于 `predictions/<年>.npz`。墙钟 33.96 s，设备 mps，MPS driver 峰值 1.13 GB，进程峰值 RSS 修正后 2.83 GiB。）

**源标定阈值**（源期 test 分片良性 19,496 行，held-out）：0.1% 预算 → `0.99290`（标定集实测 FPR 0.001026，20 个假阳性）；1% 预算 → `0.85114`（实测 FPR 0.010002，195 个假阳性）。

**语境读数**：训练区拟合 AUROC 0.9967；IID 月（test 分片）AUROC 0.99384、AP 0.99324，A 组 FNR@0.1% = 0.3447（源期尾部重叠已不低）；逐 epoch loss 0.2219→0.0953，IID AP 0.9900→0.9932（拟合充分，无欠拟合混杂）。

### 主表（正例 ≥ 500：2016–2023；逐年 train+test 合并）

| 年 | n | 正例 | AUROC（纯排序） | AP | A组 FPR@0.1% | A组 FNR@0.1% | A组 FNR@1% | B组 FPR@0.1% | B组 FNR@0.1% | B组 FNR@1% |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2016 | 109,193 | 45,134 | 0.9458 | 0.9307 | 0.0032 | 0.7691 | 0.4221 | 0.0011 | 0.8693 | 0.5527 |
| 2017 | 99,144 | 21,359 | 0.5712 | 0.3467 | 0.0001 | 0.9909 | 0.9458 | 0.0010 | 0.9681 | 0.9377 |
| 2018 | 104,292 | 39,350 | 0.6423 | 0.5548 | 0.0001 | 0.9779 | 0.9174 | 0.0010 | 0.9476 | 0.8996 |
| 2019 | 91,050 | 41,585 | 0.9549 | 0.9534 | 0.0001 | 0.8574 | 0.6318 | 0.0010 | 0.7265 | 0.4712 |
| 2020 | 102,073 | 46,355 | 0.9562 | 0.9564 | 0.0001 | 0.9205 | 0.7202 | 0.0010 | 0.7892 | 0.3714 |
| 2021 | 81,155 | 35,627 | 0.9460 | 0.4633 | 0.0000 | 0.9766 | 0.7867 | 0.0010 | 0.8636 | 0.3482 |
| 2022 | 86,416 | 41,648 | 0.9610 | 0.9685 | 0.0000 | 0.9388 | 0.7425 | 0.0010 | 0.6791 | 0.2484 |
| 2023 | 54,354 | 7,892 | 0.8821 | 0.7638 | 0.0000 | 0.9568 | 0.8267 | 0.0010 | 0.6603 | 0.4579 |

### 单列披露（正例 < 500，只作探索性，不进主表）

| 年 | n | 正例 | AUROC | AP | A组 FNR@0.1% | B组 FNR@0.1% | B组 FNR@1% |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2024 | 48,427 | 794 | 0.7817 | 0.3774 | 0.9962 | 0.7746 | 0.5844 |
| 2025 | 44,663 | 23 | 0.5958 | 0.0012 | 1.0000 | 1.0000 | 0.9130 |

### 按计划 §2.3 预注册判据的裁定（机械套用，最终裁决归主代理）

- 判据行 1（决策层：B 组大幅回落至个位数百分比且各年量级接近）**不成立**：B 组 FNR@0.1% 在主表年落在 0.66–0.97。
- 判据行 2（表示层：B 组 FNR 仍高）**成立**：2024 B 组 FNR@0.1% = 0.7746 > 25%（判据原文示例）；主表年 2016–2023 也全部 >25%。
- **机械结论：对静态源期模型、0.1% 预算口径，B 组 FNR 仍高 ⇒ 按冻结判据记「存在表示层退化，阈值不是主因」。**
- **主代理裁定（2026-10-14，E1 终审）：按计划 §2.3 冻结判据，命中「B 组仍高（2024 仍 77.46% > 25%）⇒ 存在表示层退化，阈值不是主因」这一支；并指出 2016 为反例（自校准后 FNR 反而变差 0.7691→0.8693），正文必须与判据结论并列报告。**

### 实现代理附注（读数之外的观察，不构成裁决）

1. **A 组源阈值在目标年上向「过保守」方向迁移**：除 2016（0.0032）外，各目标年 A 组 FPR 远低于预算（≈0.0000–0.0001）——目标年良性分数整体压得极低，源阈值几乎不放行。这机械地推高 A 组 FNR；B 组消除该效应后 FNR 仍高，说明残余失败发生在排序质量层。
2. **2025 的病理与 stage-b 参考读数不同**：stage-b 逐年更新模型 2025 AUROC 0.9851（排序完好、阈值失效）；本静态模型 2025 AUROC 仅 0.5958（排序本身已失效）。E1 回答的是「静态协议下」的诊断；两种协议的病理不同型。
3. **与 v3 先例交叉一致**：本模型 2016/2017 AP 0.9307/0.3467 vs v3 独立读数 0.9374/0.3462（同协议不同次训练），方向与量级一致。
4. 已登记的实现缺陷：macOS `getrusage` 峰值 RSS 收据初始按 Linux 习惯 ×1024，膨胀 1024 倍；已修正（2.83 GiB，低于 8 GiB 门），原始值保留在 metrics.json。
5. 模型权重未持久化（分数已逐样本落盘 npz，全部下游数字可从制品复算；MPS 本身非逐位确定，权重重训不会逐位复现）。

## E2 首次运行失败与机器根因（2026-10-14）

**失败形态**：`status.json` 停在 `phase=lightgbm`；console 打印完 MLP 第 6 轮 loss（`0.095318`）后**无任何错误行即终止**。
崩溃报告 `~/Library/Logs/DiagnosticReports/python3.14-2026-10-14-140653.ips`：
`EXC_BAD_ACCESS / SIGSEGV / KERN_INVALID_ADDRESS at 0x580`。

**根因（机器级，非实现级）**：本机内存枯竭。

| 指标 | 实测 |
| --- | --- |
| 物理内存 | `15G used / 126 MB unused` |
| 压缩器 | `6.9 GB` |
| swap | `5,974 / 7,168 MB` 已用（本轮复测 `6,280 / 7,168 MB`） |
| 累计 swapins／swapouts | `298,923,945 / 320,721,584` 页 |
| `ANECompilerService` | **93–96% CPU 连续 19 小时 21 分**（`kill` 无效，系统 XPC 服务由 launchd 管理） |

**⇒ 该状态同样可以解释本轮两次代理卡死（`Agent stalled: no progress for 600s`）。
此前把卡死归因于「代理又卡了」是**错误归因**，已更正。**

**已做的修复（不依赖机器恢复）**：脚本改为
① GBDT 与 SVM 走 **CSR 稀疏输入**（稠密 float32 约 2.5 GiB）；
② **每完成一个模型立即落盘 `metrics.json`**（旧版只在末尾写，导致已完成的 MLP 白跑）。
脚本修订 `380257ba`。

**未做的验证**：E2 **尚未取到任何模型读数**；`Baseline` 之外的两个特征视图（`var_thresh_0.01`／`0.0001`）与 `NPZ_Version` 已补齐但**未核内容**。
