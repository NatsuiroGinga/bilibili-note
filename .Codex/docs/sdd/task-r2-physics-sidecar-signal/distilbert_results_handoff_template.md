# R2 DistilBERT 四组三种子结果验收与写回模板

> 本文件仅用于十二组正式运行完成后的结果验收、裁决和总控写回。所有标为“待登记”的单元格必须从服务器原始制品、SwanLab 在线记录或离线分析制品中核验后填写，不得依据日志片段、预期或单个最好种子补造结果。

## 1. 验收范围

- 数据范围：仅 TQH-C2 冻结开发训练 `2,048` 条和开发验证 `512` 条。
- 最终测试：必须保持 `final_test_visible=false`，不得读取或用于选择配置。
- 基座：`distilbert/distilbert-base-multilingual-cased`。
- 组别：`A`（`T-A`）、`P`（`T-P`）、`S`（`T-S`）、`R`（`T-R`）。
- 种子：精确为 `42/43/44`，不得缺失、替换、增加或选择最好种子。
- 主任务：判断真实物理旁路 `P` 是否在每个种子上都严格优于基础组 `A`、置换组 `S` 和随机组 `R` 的宏平均 F1。
- 结果性质：开发集结构适配探针，不进入论文主表，不等同于完整 R2 或 Qwen 正式验证。

依据文件：

- [Transformer 探针计划](transformer_probe_plan.md)
- [HGB 负对照分布报告](hgb_null_control_report.md)
- [DistilBERT 探针实施报告](distilbert_probe_impl_report.md)
- [三种子分析器实施报告](distilbert_multiseed_analysis_impl_report.md)
- [第一创新点实验总控](../../../../output/第一创新点实验总控.md)

## 2. 冻结输入与执行合同

下表是运行前已经冻结的输入合同，不是本轮实验结果。

| 制品 | 相对项目根路径 | 预注册 SHA-256 | 验收结果 |
| --- | --- | --- | --- |
| 输入摘要 | `runs/r2-physics-sidecar-pilot/inputs/input-summary.json` | `028d18d41d5703b3792f6440948716edea43b6f45ddf1ebb427f816ebd829462` | 待登记 |
| 检测视图 | `runs/r2-physics-sidecar-pilot/inputs/tqhc2/tqhc2-pilot-detection-view.parquet` | `6d8019dc15f2cd11abc2b4aa8a92ca81608b8000ef0c39eb83aae04607d9a126` | 待登记 |
| 18 维旁路 | `runs/r2-physics-sidecar-pilot/inputs/tqhc2/tqhc2-pilot-sidecar.parquet` | `56658ea8886a57cdefe1dba2268e658f9072e24a94b93d5bf7a3711db9de2553` | 待登记 |

四组语义固定如下：

| 简写 | 实现名 | 18 维输入 | 旁路启用掩码 | 归因责任 |
| --- | --- | --- | ---: | --- |
| `A` | `T-A` | 全零 | `0` | 保留相同结构和参数，只关闭旁路贡献 |
| `P` | `T-P` | 真实旁路 | `1` | 保留样本与真实旁路的对应关系 |
| `S` | `T-S` | 同来源、同传输族、同划分整行置换旁路 | `1` | 排除旁路边际分布和额外维度解释 |
| `R` | `T-R` | 仅由对应训练池逐维生成的随机旁路 | `1` | 排除训练池边际分布和随机输入解释 |

固定训练合同：每设备训练批量 `16`、每设备验证批量 `64`、梯度累积 `2`、学习率 `2e-5`、权重衰减 `0.01`、训练 `3` 轮、预热比例 `0.1`、最大梯度范数 `1.0`、每组 `192` 个优化步。十二组的样本顺序、基础文本、标签、模型结构、参数量、优化器和训练预算必须一致。

## 3. 服务器、本地与 SwanLab 路径

| 类型 | 路径或标识 |
| --- | --- |
| 服务器项目根 | `/root/autodl-tmp/thesis/experiments/llm_probe/` |
| 服务器十二组运行根 | `/root/autodl-tmp/thesis/experiments/llm_probe/runs/r2-transformer-sidecar-probe/distilbert-v0/` |
| 服务器分析根 | `/root/autodl-tmp/thesis/experiments/llm_probe/runs/r2-transformer-sidecar-probe/distilbert-v0-analysis-v1/` |
| 本地项目根 | `/Users/bilibili/personal/note/thesis/experiments/llm_probe/` |
| 本地十二组镜像根 | `/Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/r2-transformer-sidecar-probe/distilbert-v0/` |
| 本地分析镜像根 | `/Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/r2-transformer-sidecar-probe/distilbert-v0-analysis-v1/` |
| SwanLab 项目 | `mortiswang/malicious-traffic-llm` |
| 详细验收与裁决记录 | `.Codex/docs/sdd/task-r2-physics-sidecar-signal/distilbert_results_handoff_template.md` |

离线分析固定调用合同：

```text
python3 -m flow_probe.r2_distilbert_multiseed_analysis \
  --run-root runs/r2-transformer-sidecar-probe/distilbert-v0 \
  --output runs/r2-transformer-sidecar-probe/distilbert-v0-analysis-v1 \
  --bootstrap-repetitions 2000 \
  --bootstrap-seed 20260803
```

## 4. 十二组运行、SwanLab、状态与总清单登记

状态门禁：每组必须实际核验为 `finished / theory_selection / review_pending`，`run_state.json` 必须满足 `status=finished`、`latest_checkpoint=null`、`failure=null`，且 `final_test_visible=false`。SwanLab 云端运行必须结束，在线指标与本地制品一致。任一组缺失或无效时先记为 `NOT_READY`，不得提前形成科学 `NO_GO` 裁决。

| 运行键 | 种子 | 组别 | 相对运行目录 | SwanLab 运行号及地址 | SwanLab 云端状态 | 本地运行状态 | 阶段及复审状态 | `artifact_manifest.json` SHA-256 | 清单逐项复核 | 本地镜像复核 |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `42-A` | 42 | `T-A` | `seed-42/t-a/` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| `42-P` | 42 | `T-P` | `seed-42/t-p/` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| `42-S` | 42 | `T-S` | `seed-42/t-s/` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| `42-R` | 42 | `T-R` | `seed-42/t-r/` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| `43-A` | 43 | `T-A` | `seed-43/t-a/` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| `43-P` | 43 | `T-P` | `seed-43/t-p/` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| `43-S` | 43 | `T-S` | `seed-43/t-s/` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| `43-R` | 43 | `T-R` | `seed-43/t-r/` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| `44-A` | 44 | `T-A` | `seed-44/t-a/` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| `44-P` | 44 | `T-P` | `seed-44/t-p/` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| `44-S` | 44 | `T-S` | `seed-44/t-s/` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| `44-R` | 44 | `T-R` | `seed-44/t-r/` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |

### 4.1 逐组关键哈希

下列 SHA-256 必须从服务器原始文件重算，并与 `artifact_manifest.json`、收尾收据及本地镜像逐项核对。`run_state.json` 按收尾合同单独核验，不要求登记在制品清单中。

| 运行键 | `run_binding.json` | `finalization_receipt.json` | `best_model_receipt.json` | `metrics/validation_metrics.json` | `predictions/validation_predictions.jsonl` | `summary.json` | 核验结论 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `42-A` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| `42-P` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| `42-S` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| `42-R` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| `43-A` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| `43-P` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| `43-S` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| `43-R` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| `44-A` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| `44-P` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| `44-S` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| `44-R` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |

### 4.2 完整性门禁

- [ ] 运行根精确包含 `seed-42/43/44`，没有缺失、替换或额外 `seed-*`。
- [ ] 每个种子精确包含 `t-a/t-p/t-s/t-r`，十二组全部通过状态门禁。
- [ ] 每组的配置快照、输入绑定、模型绑定、运行绑定、指标、预测、`summary.json`、种子汇总、制品清单、收尾收据和最佳模型收据均存在且相互一致。
- [ ] 十二组训练与验证的样本顺序、文本摘要、标签摘要和预测配对身份一致。
- [ ] 十二组模型结构、参数合同、优化器、`192` 步预算、探针实现摘要和五项语义依赖摘要一致。
- [ ] 每组预测精确为 `512` 个唯一开发验证样本，字段、概率、标签和阈值预测均合法。
- [ ] 四项指标已从预测重算，并与指标文件、`summary.json` 和种子汇总逐项一致。
- [ ] 完成组没有残留 `checkpoint-*`，`model-selection/` 只保留一个最佳模型。
- [ ] `artifact_manifest.json` 与最终文件集合、文件大小和 SHA-256 一致。
- [ ] 服务器制品已回收到本地镜像，关键制品逐文件 SHA-256 一致。
- [ ] 没有疑似最终测试路径、最终测试预测或最终测试指标。

完整性总状态：`待登记`。

阻塞或异常说明：`待登记`。

## 5. 逐种子四组指标

指标只从 `metrics/validation_metrics.json` 和同组 `predictions/validation_predictions.jsonl` 复算结果填写。宏平均 F1 越高越好；良性误报率、Brier 分数和期望校准误差越低越好。

| 种子 | 组别 | 宏平均 F1 | 良性误报率 | Brier 分数 | 期望校准误差 | 预测行数 | 指标复算一致 |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 42 | `A` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| 42 | `P` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| 42 | `S` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| 42 | `R` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| 43 | `A` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| 43 | `P` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| 43 | `S` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| 43 | `R` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| 44 | `A` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| 44 | `P` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| 44 | `S` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| 44 | `R` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |

### 5.1 三种子汇总

样本标准差按三个预注册种子计算，不得用总体标准差替代。

| 组别 | 宏平均 F1 均值 ± 样本标准差 | 良性误报率均值 ± 样本标准差 | Brier 分数均值 ± 样本标准差 | 期望校准误差均值 ± 样本标准差 |
| --- | --- | --- | --- | --- |
| `A` | 待登记 | 待登记 | 待登记 | 待登记 |
| `P` | 待登记 | 待登记 | 待登记 | 待登记 |
| `S` | 待登记 | 待登记 | 待登记 | 待登记 |
| `R` | 待登记 | 待登记 | 待登记 | 待登记 |

## 6. 配对差值与自助法置信区间

- 差值统一定义为 `P - 对照`。
- 宏平均 F1 的正差值表示改善。
- 良性误报率、Brier 分数和期望校准误差的负差值表示改善。
- 配对自助法使用相同开发验证样本，按二分类真实标签分层抽样，重复 `2,000` 次，基础种子为 `20260803`，报告 2.5% 与 97.5% 分位点组成的 95% 区间。
- 每个种子、每个比较分别登记点差值和配对 95% 置信区间；不得用不配对区间或跨种子均值区间替代。

| 种子 | 比较 | 宏平均 F1 差值 | 宏平均 F1 配对 95% 区间 | 良性误报率差值 | 良性误报率配对 95% 区间 | Brier 差值 | Brier 配对 95% 区间 | 期望校准误差差值 | 期望校准误差配对 95% 区间 |
| ---: | --- | ---: | --- | ---: | --- | ---: | --- | ---: | --- |
| 42 | `P-A` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| 42 | `P-S` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| 42 | `P-R` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| 43 | `P-A` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| 43 | `P-S` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| 43 | `P-R` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| 44 | `P-A` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| 44 | `P-S` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |
| 44 | `P-R` | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 | 待登记 |

宏平均 F1 配对区间证据强度登记：

| 种子 | `P-A` 区间完全高于 0 | `P-S` 区间完全高于 0 | `P-R` 区间完全高于 0 |
| ---: | --- | --- | --- |
| 42 | 待登记 | 待登记 | 待登记 |
| 43 | 待登记 | 待登记 | 待登记 |
| 44 | 待登记 | 待登记 | 待登记 |

### 6.1 三种子差值汇总

此处只登记三个种子点差值的均值与样本标准差，不将其误写为配对自助法置信区间。

| 比较 | 宏平均 F1 差值均值 ± 样本标准差 | 良性误报率差值均值 ± 样本标准差 | Brier 差值均值 ± 样本标准差 | 期望校准误差差值均值 ± 样本标准差 |
| --- | --- | --- | --- | --- |
| `P-A` | 待登记 | 待登记 | 待登记 | 待登记 |
| `P-S` | 待登记 | 待登记 | 待登记 | 待登记 |
| `P-R` | 待登记 | 待登记 | 待登记 | 待登记 |

## 7. 主 GO/NO-GO 裁决

### 7.1 裁决前提

只有第 4 节完整性总状态通过且离线分析器成功生成完整分析包，才允许执行主裁决。输入门禁失败、组别缺失、状态不合法、哈希不一致或预测不可配对时，状态为 `NOT_READY`，不是科学 `NO_GO`。

### 7.2 唯一主门槛

`GO_TO_QWEN` 当且仅当以下九个严格不等式全部成立：

```text
seed 42: F1(P) > F1(A), F1(P) > F1(S), F1(P) > F1(R)
seed 43: F1(P) > F1(A), F1(P) > F1(S), F1(P) > F1(R)
seed 44: F1(P) > F1(A), F1(P) > F1(S), F1(P) > F1(R)
```

任意一个点差值小于或等于 `0`，主裁决即为 `NO_GO`，并逐项登记失败种子与比较对象。良性误报率、Brier 分数、期望校准误差或单个种子的改善不能替代该主门槛。

配对 95% 置信区间是否全部支持宏平均 F1 正差值只决定证据强度，不改变预注册主裁决：

- 九个点差值均为正且九个区间均完全高于 `0`：`point_superiority_with_paired_ci95_support`。
- 九个点差值均为正但至少一个区间未完全高于 `0`：仍按合同输出 `GO_TO_QWEN`，同时明确记录统计证据不足警告。
- 至少一个点差值不为正：`NO_GO`。

### 7.3 裁决登记

| 项目 | 登记值 |
| --- | --- |
| 完整性总状态 | 待登记 |
| 九个宏平均 F1 点差值是否全部为正 | 待登记 |
| 九个宏平均 F1 配对 95% 区间是否全部高于 0 | 待登记 |
| 自动裁决 | `待登记：GO_TO_QWEN / NO_GO / NOT_READY` |
| 证据强度 | 待登记 |
| 失败种子与比较对象 | 待登记 |
| 配对区间警告 | 待登记 |
| 校准与误报诊断 | 待登记 |
| 最终测试是否可见 | 待登记，必须为 `false` |

裁决说明：`待登记`。

`GO_TO_QWEN` 只表示当前小型 Transformer 开发集探针通过检测增量门槛，不表示完整 R2 已通过数据、物理、多协议、正式多种子或最终测试门槛。

## 8. 当前 TQH-C2 开发验证的物理指标边界

物理指标状态必须登记为：

```text
not_evaluable_on_current_public_tqhc2_development_validation
```

原因与边界：

1. 当前 TQH-C2 开发验证没有隐藏队列真值。
2. `T-A` 没有与正式 R2 同口径的状态头，不能形成可比的未观测状态误差或物理残差基线。
3. 既有 ns-3 状态估计器和旁路摘要只能作为就绪背景绑定，不能计入本探针的 `P-A` 物理增益。
4. 本探针只能裁决当前 18 维旁路对 DistilBERT 开发集检测指标的增量，不能伪造或外推物理指标。
5. 正式 R2 仍要求种子 `42/43/44` 的未观测状态误差和物理残差相对同分区基线均改善至少 `10%`；该门槛不因本探针 `GO_TO_QWEN` 而取消。

物理门槛登记：

| 项目 | 当前可登记结果 |
| --- | --- |
| 当前探针是否可评价未观测状态误差 | 否 |
| 当前探针是否可评价物理残差增益 | 否 |
| 物理门槛是否阻塞 DistilBERT 探针自身裁决 | 否 |
| 物理门槛是否仍阻塞完整 R2 冻结 | 是 |

## 9. `NO_GO` 后唯一多窗口修复分支

只有十二组完整有效且主裁决为 `NO_GO` 时，才允许启动以下唯一一次修复分支：

1. 从逐包被动可观测字段构造严格因果的多窗口序列，不读取最终测试、标签、场景编号、采集单元编号或仿真内部真值。
2. 增加一个等信息量原始历史 Transformer 基线，使真实物理旁路的收益不能由额外历史信息本身解释。
3. 在相同样本、划分、文本、训练预算和种子 `42/43/44` 上重新比较真实、置换和随机物理旁路。
4. 修复机会只允许一次。不得通过修改学习率、样本比例、旁路维度、随机种子或查看最终测试来补救。
5. 若多窗口分支仍失败，停止当前 R2 检测增益路径，不进入 Qwen，不再以调参或挑种子恢复该路线。

分支登记：

| 项目 | 登记值 |
| --- | --- |
| 是否满足启动条件 | 待登记 |
| 多窗口合同路径 | 待登记 |
| 等信息量原始历史基线路径 | 待登记 |
| 是否为唯一一次修复 | 待登记，必须为 `true` |
| 分支裁决 | 待登记 |

## 10. 离线分析制品验收

分析器不登记 SwanLab。以下文件必须来自唯一全新分析目录，且 `artifact_manifest.json` 必须覆盖前五项文件的大小与 SHA-256。

| 分析制品 | 服务器路径 | 本地路径 | SHA-256 | 核验结果 |
| --- | --- | --- | --- | --- |
| `analysis_config.json` | `runs/r2-transformer-sidecar-probe/distilbert-v0-analysis-v1/analysis_config.json` | `runs/r2-transformer-sidecar-probe/distilbert-v0-analysis-v1/analysis_config.json` | 待登记 | 待登记 |
| `input_manifest.json` | `runs/r2-transformer-sidecar-probe/distilbert-v0-analysis-v1/input_manifest.json` | `runs/r2-transformer-sidecar-probe/distilbert-v0-analysis-v1/input_manifest.json` | 待登记 | 待登记 |
| `analysis_summary.json` | `runs/r2-transformer-sidecar-probe/distilbert-v0-analysis-v1/analysis_summary.json` | `runs/r2-transformer-sidecar-probe/distilbert-v0-analysis-v1/analysis_summary.json` | 待登记 | 待登记 |
| `metrics.csv` | `runs/r2-transformer-sidecar-probe/distilbert-v0-analysis-v1/metrics.csv` | `runs/r2-transformer-sidecar-probe/distilbert-v0-analysis-v1/metrics.csv` | 待登记 | 待登记 |
| `summary.md` | `runs/r2-transformer-sidecar-probe/distilbert-v0-analysis-v1/summary.md` | `runs/r2-transformer-sidecar-probe/distilbert-v0-analysis-v1/summary.md` | 待登记 | 待登记 |
| `artifact_manifest.json` | `runs/r2-transformer-sidecar-probe/distilbert-v0-analysis-v1/artifact_manifest.json` | `runs/r2-transformer-sidecar-probe/distilbert-v0-analysis-v1/artifact_manifest.json` | 待登记 | 待登记 |

分析参数核验：

| 参数 | 预注册值 | 实际值 | 是否一致 |
| --- | --- | --- | --- |
| 种子 | `[42, 43, 44]` | 待登记 | 待登记 |
| 组别 | `[T-A, T-P, T-S, T-R]` | 待登记 | 待登记 |
| 比较 | `[P-A, P-S, P-R]` | 待登记 | 待登记 |
| 自助法重复次数 | `2000` | 待登记 | 待登记 |
| 自助法基础种子 | `20260803` | 待登记 | 待登记 |
| 抽样方式 | `paired_stratified_by_binary_label` | 待登记 | 待登记 |
| 差值方向 | `T-P_minus_comparator` | 待登记 | 待登记 |
| 最终测试可见性 | `false` | 待登记 | 待登记 |
| 分析阶段 SwanLab 登记 | `false` | 待登记 | 待登记 |

## 11. 总控写回位置与内容

详细制品、逐种子数值、哈希和统计警告先完整登记在本文件，再更新[第一创新点实验总控](../../../../output/第一创新点实验总控.md)。不得只更新总控而遗漏详细证据。

总控精确更新位置：

1. 文首“当前阶段”：更新十二组完成状态、分析状态与本地回收状态，但不得覆盖仍独立存在的 R2 数据门禁或其他任务实况。
2. `5.3 R2：共享守恒与协议自适应多动力学 PINN`：在 HGB 负对照段落之后登记 DistilBERT 主裁决、三种子方向、配对区间证据强度、分析制品链接和物理指标不可裁决边界。
3. `6. 当前执行顺序` 的 `P2：R1/R2/R3 技术路线筛选`：按裁决登记下一门禁。

写回措辞边界：

- 若为 `GO_TO_QWEN`：只写“DistilBERT 开发探针通过预注册检测增量门槛，可以进入 Qwen 前的后续门禁”，不得写“R2 已成功”“物理指标已通过”或“可以进入论文主表”。
- 若为 `NO_GO`：只启动第 9 节唯一多窗口分支，不得直接调参、挑种子或启动 Qwen。
- 若为 `NOT_READY`：只记录具体缺失或不一致项，不得形成方法有效性结论。
- 若唯一多窗口分支再次失败：登记停止当前 R2 检测增益路径及失败边界。
- 本结果不改变课题定位、第三四章关系或长期研究纪律，因此默认不更新 `output/开题改进交接文档.md`。

总控写回完成登记：

| 项目 | 登记值 |
| --- | --- |
| 详细记录已完成 | 待登记 |
| 总控更新日期 | 待登记 |
| 总控更新段落 | 待登记 |
| 总控相对链接已核验 | 待登记 |
| 未修改开题交接文档 | 待登记 |

## 12. 最终移交摘要

| 项目 | 登记值 |
| --- | --- |
| 十二组运行完整性 | 待登记 |
| SwanLab 在线核验 | 待登记 |
| 服务器与本地逐哈希一致 | 待登记 |
| 离线分析制品完整性 | 待登记 |
| 主裁决 | 待登记 |
| 物理指标边界 | `not_evaluable_on_current_public_tqhc2_development_validation` |
| 下一门禁 | 待登记 |
| 遗留风险 | 待登记 |
