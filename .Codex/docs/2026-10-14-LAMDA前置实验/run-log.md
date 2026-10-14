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
