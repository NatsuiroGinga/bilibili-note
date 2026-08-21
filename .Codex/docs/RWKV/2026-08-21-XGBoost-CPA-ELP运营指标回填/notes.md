# XGBoost＋CPA-ELP 运营指标回填证据笔记

## 已核验代码与合同

### 既有目标评价 continuation

- `tools/ch3_xgb_cpa_elp_eval_continuation.py` 固定父运行 `ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1`。
- 其完整 `model_semantic168.json` SHA-256 常量为 `1805e15d96ac4ebb57df910640a4c5e1af58f692659db2eb80b724851efe42e9`。
- 父选择要求 `semantic168`、`p_raw83=2.0`、`p_semantic168=1.0`、800 树、XGBoost 3.2.0 与 11 项有效配置收据。
- 现有 continuation 同时读 `raw83` 锚点、加载两个模型并执行两次目标推理，最终只保存六个名义预算读数。因此不能直接满足本任务的 C11 单模型、单调用和完整运营制品合同。
- 可复用的实现事实包括 168 维构造公式、LSPR24 冻结规模、CUDA 模型配置和实体键构造；continuation 的时间核验不属于本回填的首次告警轴合同，不能继承为合法性门。

### 父恢复证明器

- `tools/build_ch3_xgb_parent_recovery_proof.py` 证明父训练运行本身曾中断，不能伪称父运行有原生完成清单。
- 它逐项核验父配置摘要、选择收据摘要、11 项有效配置收据、最终模型及折外模型，并实际加载模型确认 800 树。
- 本回填入口只需要最终 `semantic168` 模型，不读取折外模型；同时必须以完成的目标 continuation 作为“目标评价已经发生且完成”的独立证明，不能把恢复证明冒充父完成证明。

### 统一总表完整曲线接口

- `tools/ch3_build_metrics_table.py` 读取 `complete-alert-budget-curves-receipt.json` 与 NPZ。
- C11 完整曲线成员名需为 `C11__n_false_positive_entity`、`C11__nominal_fpr`、`C11__realized_fpr`、`C11__detection_rate`。
- 收据须声明 `complete_over_all_reachable_negative_entity_budgets=true` 或同义字段，并包含 NPZ 的字节数和 SHA-256。
- 六档 DR 应由 `realized_fpr <= 名义预算` 的最接近实际可达点读取，不能对名义点插值。

### 首次告警接口与实现

- 统一总表支持独立 `first-alert-timing-receipt.json` 与 `first-alert-timing-curves.npz`。
- 默认 `timely_detection_v1` 键式为 `C11__fpr_0.001__exposure_index` 与 `C11__fpr_0.001__timely_detection_rate`，其余五档同理。
- 收据 `cells.C11` 需给出 `unalerted_rate_at_fpr`、`realized_fpr_at_fpr` 和 `delay_summary_at_fpr`，横轴必须声明 `exposure_index`，且 `time_delay_available=false`。
- MLP/RWKV 实现按同实体内冻结 `flow_id` 升序，把第一条合法流记为曝光 1；在线 C11 分数为前缀幂平均，`p=1` 时即前缀算术平均。达到同档完整并列阈值时首次告警，按时曲线分母固定为全部正实体，未告警实体作为删失保留。
- RWKV 实现的分位数为 `minimum/p25/median/p75/p90/p95/p99/maximum`，按时曲线采用右连续精确断点，并包含横轴 0 与最大正实体曝光数。

## 本任务采用的差异

- 只输出目标年 C11，不输出源年或四格。
- 只加载 `X24/y24/I24/M24/s24/d24` 六个 LSPR24 数组；`X24` 作为 83 个基础字段进入 `semantic168` 构造，但不形成 `raw83` 评价分支。
- 只加载 `model_semantic168.json`，目标 GPU 分数调用计数必须严格为 1。
- 逐流分数、最终实体分数和逐实体首次告警位置只在内存存在，完成聚合后立即释放，不进入 NPZ 或 JSON。
- `I24/M24` 必须证明全部索引合法、掩码有限且二值、有效位恰为流数，并且每个流索引恰好出现一次。
- 时间数组不进入生产白名单。首次告警只报告 1 基 `exposure_index`；因没有完整流 `available_ns`，`time_delay_available=false`。

## 两次失败证据与裁决

- 初始运行因资源门在控制器 `tee` 建立后执行而误报自身并发；这是启动顺序错误，不是资源不足。修复不放宽真实并发门。
- `rerun1` 在 200,825 条序列核验后报告 5,721,196 个同实体时间逆序相邻对并停止，未执行目标 GPU 打分。这暴露的是计划把非 `available_ns` 时间字段误当顺序合法性门，而不是数据需要重排。
- 统一合同固定首次告警轴为同实体内 `ascending_frozen_flow_index`。不得用逆序对修排序、按时间重排或修改缓存；只撤销错误时间门并加强 `I/M` 无重无漏门。

## 运行身份建议

- 运行标识：`ch3-xgb-cpa-elp-c11-operational-backfill-v1-rerun2`。
- 展示名称：`XGBoost＋CPA-ELP C11目标年完整运营指标零训练回填`。
- 输出根：`runs/diagnostics/ch3-xgb-cpa-elp-c11-operational-backfill-v1-rerun2/`。

## 预期聚合制品

- `operational-backfill-receipt.json`：父身份、目标只评价、调用计数和数据门禁。
- `target-year-metrics.json`：C11 排序指标、六档实际可达 DR 与首次告警摘要。
- `complete-alert-budget-curves.npz` 与对应收据。
- `first-alert-timing-curves.npz` 与对应收据。
- `resource-receipt.json`、`status.json`、`manifest.json`、运行日志。

## 未验证边界

- 两次真实启动均在目标打分前失败，没有产生运营指标；`rerun2` 仍需验证父制品、六个缓存、GPU、资源采样和聚合输出。
- 实现验证只覆盖静态合同与命令入口；真实数据、GPU、资源采样和聚合数值必须由唯一远程命令执行后验收。
