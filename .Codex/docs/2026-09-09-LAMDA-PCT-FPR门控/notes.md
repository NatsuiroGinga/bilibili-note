# LAMDA PCT 与 FPR gate 证据笔记

## 来源

- PCT 原件：`raw/papers/attack-detection/lamda-related/2021-Yan-PCT-Regression-Free-Model-Updates-CVPR.pdf`，SHA-256 `8487b8afa1f272c4a3e37ab44e9b1b3ffad8030d9e6b7342dd7eaba2e9fdae5f`。
- PCT 公式：Section 4，Eq.（4）总体目标，Eq.（7）Focal Distillation，Eq.（8）温度 KL，Eq.（9）logit matching；MinerU 全文见 `source-extract/pct-full.md`。
- PCT 论文实验默认 alpha=1、beta=5，lambda=1；这些值只作为外部起始配置，不预示 LAMDA 最优。
- Cotter JMLR 与 ICML 原件及 Kumar ICO 原件已下载，分别见 `source-extract/cotter-jmlr_p*.md`、`cotter-two-dataset.md` 和 `kumar.md`。

## 本地病灶

- 已完成的缺口修复单臂在开发期把 FNR 从 `0.059478156` 降至 `0.030904579`，但 FPR 升至 `0.138637245`。
- 已完成的条件风险门控单臂把 FPR 降至 `0.012231661`，但 FNR 升至 `0.070306038`，与始终双风险投影行为一致。
- 因此 PCT 的筛选问题是：它能否保护旧正确决策而不完全阻断恶意漏判修复。

## 分析边界

- 当前发布特征视图含未来协变量，全部运行标记 `screening_only`。
- 本轮只使用来源年和项目开发层；封印年不读取。
- 单种子筛选不能产生运行级显著性结论；只用于候选排序和止损。

## 本机预筛收据（2026-09-09）

- 运行身份：`ch3-lamda-pct-fpr-screening-mps-seed42-v1`；状态 `completed`；四臂为 `experience_replay`、`pct`、`gap_repair`、`gap_repair_pct`。
- 实际设备来自 `runtime-receipt.json` 的 `device=cpu`；当前环境复核为 `mps_built=true`、`mps_available=false`，不能称为 MPS 速度。续跑墙钟来自 `resource-receipt.json`：`629.00211875` 秒（约 10 分 29 秒）；该运行使用 `--resume`，因此不是空目录全量墙钟。
- 开发层 pooled 指标（`development-summary.json`，单种子、筛选用途）：ER 的 AP/FPR/FNR 为 `0.987124589/0.014981141/0.050154147`；PCT 为 `0.975372679/0.025097818/0.060606061`；缺口修复为 `0.963426337/0.108040467/0.031806903`；联合臂为 `0.906948860/0.073566217/0.023310023`。
- 相对 ER，PCT 的 `ΔAP=-0.011751910`、`ΔFPR=+0.010116677`、`ΔFNR=+0.010451914`；缺口修复与联合臂虽降低 FNR，但分别增加 FPR `+0.093059325` 与 `+0.058585075`。四臂均未同时满足“FPR 不增加、旧恶意负向翻转不增加、FNR 下降”的继续门槛。
- 上述数字只支持开发期筛选否决或保留 ER 基线的方向判断，不支持封印年表现、无泄漏正式基线或第三章主方法有效性结论；独立分析报告应再次核对逐样本预测哈希与转移计数。
