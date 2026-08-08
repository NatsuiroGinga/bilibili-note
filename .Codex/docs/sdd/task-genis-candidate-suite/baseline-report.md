# GeNIS 家族验证树模型基线报告

- **状态**：已完成并验收
- **日期**：2026-07-29
- **实验阶段**：`theory_selection`
- **数据协议**：`data-protocol-v1.0-rc1`、`provisional`、`theory_selection`
- **调参试次**：`0`，公开默认配置
- **计算设备**：CPU，单模型线程上限为 `1`
- **SwanLab 项目**：`mortiswang/malicious-traffic-llm`

## 1. 实验边界

本轮只读取以下开发清单：

- 训练：`splits/genis-family-development-train.jsonl`
- 验证：`splits/genis-family-development-validation.jsonl`
- 标签：`family_label`
- 模型：HGB、XGBoost
- 种子：`42`、`43`、`44`

本轮未读取时间前向测试清单或开放集清单，也没有按测试结果选种、调参或修改数据协议。因此，本报告只建立 GeNIS 家族开发验证门槛，不能作为论文最终测试结论。

## 2. 输入合同

| 项目             | 固定值                                                             |
| ---------------- | ------------------------------------------------------------------ |
| 协议目录         | `runs/data-frozen/dataset-candidate-genis-v0/protocol`             |
| 协议 SHA-256     | `ec2c81f404da48edae5c518cdd8ce8269cb979e73cc506a42c8933b63b35a9f0` |
| 样本 SHA-256     | `2b0d8b49ef81db3a9f9338dfbabe185bab54c02512786c9f64f52718ee8c55a0` |
| 训练清单 SHA-256 | `f82775ce8fcc43e2acc27a04fcc4da919f6b2010ef242131a1dde0cf480cfaa7` |
| 验证清单 SHA-256 | `52cce0c3b36273542e1fb05956e30876a8add1f6defd769ffa69b43bfaf19fca` |
| 训练样本数       | `151324`                                                           |
| 验证样本数       | `10399`                                                            |
| 家族标签         | `benign`、`bruteforce`、`dos`                                      |

训练输入为协议登记的 `tree_flat_view`，包含八个公共数值观测和对应缺失掩码。六次运行使用相同训练、验证样本顺序与字段预算。

## 3. 启动与恢复记录

两个模型使用互不写同一输出目录的持久化会话，每个模型在自己的会话内顺序执行三个种子：

- HGB 会话：`genis-family-hgb`
- XGBoost 会话：`genis-family-xgb`
- 服务端启动器目录：`runs/baselines/theory-selection/genis-v0/launchers/genis-family-20260729-v1`

每个种子的完整命令、启动日志、运行状态与退出码均保存在上述目录。六个种子均为 `state=finished`、`exit_code=0`；两个批次状态也均为 `finished`。

首次启动时，`screen` 命令返回 `0`，但会话立即退出且日志为空。根因为启动器先执行 `set -u`，随后读取 `.bashrc`；服务器 `.bashrc` 的非交互判断访问了未定义的 `$PS1`，导致脚本在写入首个状态文件前退出。最小修复仅把 `source ~/.bashrc` 移到 `set -u` 之前。修复后远端 `bash -n`、命令能力检查、两个会话和首个状态文件均通过，模型与实验参数未改变，首次失败也没有生成任何输出目录。

## 4. 验证结果

| 模型    | 种子 | 宏平均 F1 | 平衡准确率 | 良性误报率 |   准确率 | 期望校准误差 | 对数损失 | 拟合时间（秒） |
| ------- | ---: | --------: | ---------: | ---------: | -------: | -----------: | -------: | -------------: |
| HGB     |   42 |  0.999181 |   0.999389 |   0.001119 | 0.999327 |     0.000600 | 0.003381 |          5.059 |
| HGB     |   43 |  0.999181 |   0.999389 |   0.001119 | 0.999327 |     0.000600 | 0.003381 |          5.084 |
| HGB     |   44 |  0.999181 |   0.999389 |   0.001119 | 0.999327 |     0.000600 | 0.003381 |          5.261 |
| XGBoost |   42 |  0.999298 |   0.999298 |   0.001678 | 0.999423 |     0.000262 | 0.002779 |          3.784 |
| XGBoost |   43 |  0.999298 |   0.999298 |   0.001678 | 0.999423 |     0.000262 | 0.002779 |          3.894 |
| XGBoost |   44 |  0.999298 |   0.999298 |   0.001678 | 0.999423 |     0.000262 | 0.002779 |          4.008 |

两个公开默认模型在固定开发划分上的结果均不随种子变化。XGBoost 的宏平均 F1、准确率、校准和拟合时间略优；HGB 的平衡准确率略高，良性误报率更低。两者都接近开发验证上限，这表明后续创新性不能靠同分布家族验证的小幅绝对提升论证，必须依赖统一协议下的未知攻击、时间前向、跨加密条件、物理状态和成本证据。

## 5. SwanLab 验收

| 模型    | 种子 | 运行编号   | 云端状态   | 宏平均 F1 数据点 |
| ------- | ---: | ---------- | ---------- | ---------------: |
| HGB     |   42 | `ynewg8ej` | `FINISHED` |         0.999181 |
| HGB     |   43 | `jzyzv4a8` | `FINISHED` |         0.999181 |
| HGB     |   44 | `hj93ljh1` | `FINISHED` |         0.999181 |
| XGBoost |   42 | `m4sjaou7` | `FINISHED` |         0.999298 |
| XGBoost |   43 | `biijp4ec` | `FINISHED` |         0.999298 |
| XGBoost |   44 | `f2chz9yh` | `FINISHED` |         0.999298 |

六次运行均通过云端 `run info`、`run summary` 和指定指标键的 `run metrics` 核验。每次运行在步骤 `0` 均存在一个宏平均 F1 标量点，云端值与本地 `summary.json` 完全一致。云端查询原始结果保存在启动器目录的 `cloud-*-info.json`、`cloud-*-summary.json` 和 `cloud-*-metrics.json`。

## 6. 制品与完整性

- 服务端运行根：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/baselines/theory-selection/genis-v0`
- 本地归档根：`/Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/baselines/theory-selection/genis-v0`
- 核心哈希清单：`runs/baselines/theory-selection/genis-v0/launchers/genis-family-20260729-v1/core-sha256.txt`
- 云端验收状态：`runs/baselines/theory-selection/genis-v0/launchers/genis-family-20260729-v1/cloud-verification.status`

使用不带 `--delete` 的 `rsync` 回收了六个运行目录、SwanLab 原始日志和启动器目录，共 `178` 个文件。随后按服务端生成的哈希清单核对本地 `24` 个核心文件，全部通过 SHA-256 校验。

## 7. 当前裁决

1. GeNIS 家族开发验证的树模型门槛已经建立，XGBoost 的宏平均 F1 门槛为 `0.999298`，HGB 的良性误报率门槛为 `0.001119`。
2. 该结果仍属于 `theory_selection/provisional`，不得进入论文最终主表，也不证明 PINN 已产生检测收益。
3. 下一步应继续完成三源统一主记录、共享视图和冻结预算；后续 HGB、XGBoost、神经模型与 PINN 必须读取同一清单，才能形成可归因的横向比较。
