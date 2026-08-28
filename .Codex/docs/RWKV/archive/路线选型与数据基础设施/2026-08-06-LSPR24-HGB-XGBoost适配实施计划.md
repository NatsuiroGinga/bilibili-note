# LSPR24 G0-D 到 HGB/XGBoost 最小数据适配实施计划

- **日期**：2026-08-06
- **状态**：待 G0-D 实例通过并发布开发制品后实施；本计划不授权训练、读取原始标签或访问最终区。
- **范围**：只为 HGB 与 XGBoost 增加一个共享的 LSPR24 开发区表格数据适配层。它消费 G0-D 已发布的开发视图和受限开发标签侧车，不直接打开原始 `lspr24_v2.parquet`。
- **合同版本同步（2026-08-06）**：合同已修订为 `lspr24-g0-v5-staged`（SHA-256 `877488f3529c6c862b060a74782d1904aae81512ea1169c713ba20d8c3f31a0e`）。`src/flow_probe/lspr24_g0_tabular_adapter.py` 的 `G0_D_CONTRACT_VERSION` 与 `tests/test_lspr24_g0_tabular_adapter.py` 的 `CONTRACT_VERSION` 已同步为 v5，并新增跨语言常量一致性断言 `test_python_adapter_contract_version_matches_rust_producer_constant`（读取 `tools/lspr24_g0/src/development_router.rs` 的 `LSPR24_G0_CONTRACT_VERSION`）。下文引用的合同节号不变。
- **依据**：`lspr24-g0-v4-staged` 合同第 1、6、8、10、11、13 节（现为 v5，节号未变）；现有 `tabular_baselines.py` 已具备 CPU HGB/XGBoost 拟合、单线程和统一结果写出能力。现有 `shared_b0_tabular_baselines.py` 的输入是固定的共享 B0 协议和 GeNIS/TQH-C2 切分，不能作为 LSPR24 数据读取器。

## 1. 实施边界

1. 仅在 `G0-D` 决策收据发出开发基线放行状态，且开发视图、字段清单、样本索引、评价簇清单、开发标签侧车及其绑定收据完整时实施。
2. 不读取原始标签列、明文 IP、端口、端点映射、攻击叙事或任何 `<LSPR24_G0_SEALED_ROOT>` 对象。最终区对象即使存在也一律拒绝。
3. 不修改 `shared_b0_tabular_baselines.py`、`shared_b0_view.py` 或任何共享 B0 配置。它们仅作为隔离、哈希绑定、独立模型进程和制品登记的实现参考。
4. HGB 与 XGBoost 只共享数据、字段、历史预算、12 个配置上限、候选选择规则和评价协议；不声称与神经模型参数量可比。

## 2. 拟修改文件

| 文件 | 动作 | 责任 |
| --- | --- | --- |
| `thesis/experiments/llm_probe/src/flow_probe/lspr24_g0_tabular_adapter.py` | 新增；验证 G0-D 收据，装载开发窗口、历史样本、字段清单和开发标签侧车，构造统一树模型输入，并完成四段调度与校准冻结。 | LSPR24 适配实现 |
| `thesis/experiments/llm_probe/src/flow_probe/tabular_baselines.py` | 最小扩展；公开一个接受已验证 `PreparedTabularData` 的无数据读取执行入口及模型超参数注入点，仍由同一 HGB/XGBoost 建造器、单线程限制、指标和制品结构执行。不得改变共享 B0 的既有合同。 | 通用执行器 |
| `thesis/experiments/llm_probe/scripts/run_lspr24_g0_tabular_baselines.sh` | 新增；只接受 G0-D 运行根和唯一新运行目录，运行前检查放行收据与最终区零输出声明，调用 Python CPU 入口。 | 本地启动器 |
| `thesis/experiments/llm_probe/tests/test_lspr24_g0_tabular_adapter.py` | 新增；只用合成开发区夹具覆盖下文两条精确目标测试。 | 测试 |
| `thesis/experiments/llm_probe/tests/test_tabular_baselines.py` | 最小补测公开执行入口仍把 HGB/XGBoost 交给同一执行路径。 | 回归测试 |

不修改 G0 合同、Rust 物化器、最终封存程序、原始数据、共享 B0 数据视图或路线总控。

## 3. 统一输入模式

适配器只接受以下绑定对象，全部相对于 `<LSPR24_G0_RUN_ROOT>`；每一个路径、SHA-256、合同版本和 `g0_d_decision_sha256` 都要写入适配收据。

| 输入 | 用途 | 约束 |
| --- | --- | --- |
| `views/development-windows.parquet` | 合法窗口特征的唯一来源 | 只含前 80% 开发区；不得含标签、身份或最终区行。 |
| `views/history-samples.parquet` | `sample_id`、目标窗口、历史窗口列表、`history_length`、`split_name` 的唯一来源 | 只接受 `H in {1,4,16,32}`；所有历史窗口必须同端点、同连续段、同分区。 |
| `manifests/field-manifest.json` 与字段谱系探针 | 冻结特征列顺序和合法性 | 仅接受第 6.1 节语义；递归祖先不得命中任何禁入列。 |
| `<LSPR24_G0_RESTRICTED_ROOT>/development-labels.parquet` | 开发标签的唯一来源 | 由 `lspr24-dev-router-v1` 产生，逐行以 `sample_id` 和稳定顺序绑定；标签列绝不并入特征矩阵。 |
| `manifests/evaluation-clusters.parquet` | 聚类评价与事件统计绑定 | 仅开发区成员；只作评价分组，不进特征。 |
| `receipts/g0-a-decision.json`、`receipts/semantic-hashes.json`、开发标签审计与路由输出清单 | 启动门禁和内容绑定 | 必须证明 `phase=G0-D`、开发放行、最终制品数组均为空，且最终相关谓词为 `NOT_READY`/`G0-F`。 |

对任意历史长度 `H`，树模型一条样本的数值向量固定为按时间从旧到新、每个时间步按 `field-manifest.json` 的 `output_name` 顺序拼接的 `H × F` 矩阵展平结果。只可使用第 6.1 节五类语义：流量规模、方向行为、流完成统计、粗粒度协议/连接状态、质量信息及其显式缺失掩码。训练区拟合的变换和归一化参数原样应用，适配器不得重新拟合。

以下列即使存在也必须在读取 Parquet 列投影前拒绝：所有 `Label*`、`sample_id`、`window_id`、`segment_id`、`protected_endpoint_id`、`evaluation_cluster_id`、任何时间列、IP、端口、`Flow ID`、`Service`、分区名、路径、IDS 字段及所有未登记列。`sample_id` 只在特征、侧车和评价簇之间做一对一连接，连接完成后不得进入 `numpy` 特征数组。

## 4. 标签侧车绑定

1. 适配器先验证路由器版本、开发标签审计、侧车文件哈希和受限目录权限，再读取侧车；普通训练进程没有原始 Parquet 路径参数。
2. 特征样本与侧车按 `(sample_id, stable_order)` 做一对一全连接。重复、缺失、额外样本、顺序哈希不符、标签非 `0/1` 或样本落在 `final-test` 时均立即失败，不发布部分输入。
3. `Label_src` 与 `Label_dst` 仅应已用于 G0-D 重复标签冲突审计；适配器不得读取、修补或导出它们。模型监督标签只将 `0/1` 映射为 `benign/malicious`。
4. 对每个输入矩阵计算冻结字段顺序、样本顺序、特征语义哈希、标签侧车哈希及其绑定哈希。HGB 和 XGBoost 必须引用同一组五个哈希；不相等即拒绝运行。

## 5. 四段开发区使用规则

| 分区 | HGB/XGBoost 允许动作 | 明确禁止 |
| --- | --- | --- |
| `train-fit` | 仅拟合字段变换参数已冻结后的输入；每个预注册配置拟合一次，训练类权重仅从该分区标签计算。 | 读取其他分区标签以训练、早停、重采样或调整权重。 |
| `architecture-selection` | 对每个候选配置和 `H` 只评价一次；按预测前冻结的主排序规则选出唯一骨干配置。 | 选择后回写候选、重复评价、从开发验证或校准反推超参数。 |
| `dev-validation` | 对选中的固定配置一次性做开发验证和簇级指标报告。 | 调参、重新选择 `H`、阈值拟合或再次训练。 |
| `calibration` | 用已冻结骨干的概率在该分区拟合一次预先声明的校准器，并按冻结的单调方向和目标指标冻结阈值。 | 重新训练树、再次选结构、把该分区用于搜索或访问最终区。 |

树模型预算固定为每模型最多 12 个完整枚举配置，每配置 `fit_count=1`、`evaluation_count=1`。配置总数将 `H` 也计入联合配置，不允许每个历史长度另得 12 次机会。`fair-budget-plan-receipt.json` 在首次读取 `architecture-selection` 预测前锁定，执行收据逐尝试记录两模型、配置、`H`、分区、拟合数、评价数和全部共享哈希；零执行条目只能是 `NOT_READY`。

## 6. 最终 20% 拒绝

适配器的路径解析器须在打开文件前拒绝包含 `final-test`、`sealed`、`final-test-features`、`final-test-labels`、`final-test-row-selection` 或 `<LSPR24_G0_SEALED_ROOT>` 的输入。它还须要求 G0-D 路由收据中的 `final_feature_artifacts`、`final_label_artifacts`、`final_row_selection_artifacts`、`final_member_artifacts`、`final_specific_statistics` 均为 `[]`，并要求 `G0-A12` 及最终相关状态保持 `NOT_READY` 和 `phase_assignment=G0-F`。

因此本入口不接受 `final-test` 清单、标签、特征、评价、预测或统计；不得产生最终区的计数、哈希、抽样、日志或调试输出。最终评价只能在另行通过 `final-freeze.json` 与 G0-F 一次性解封流程后，由独立冻结评价程序承担，不能复用本开发入口。

## 7. 两条精确目标测试

1. `test_development_adapter_constructs_identical_hgb_xgboost_input_and_keeps_history_budget`：用合成的 `train-fit`、`architecture-selection`、`dev-validation`、`calibration` 四分区和 `H={1,4,16,32}` 夹具，断言两模型从同一适配器取得字节一致的字段顺序、样本顺序、特征矩阵哈希、标签绑定哈希和训练样本；断言每一行恰为 `H × F`、不含任何标识符或标签列，且每个配置只登记一次拟合和一次架构选择评价。
2. `test_development_adapter_rejects_final_test_and_unbound_or_forbidden_sidecar`：分别提供最终区路径、含 `final-test` 的历史样本、未绑定或乱序标签侧车、以及在字段清单中加入 `SrcPort` 或 `Label` 的夹具；断言均在读取特征矩阵或调用分类器前抛出 `Lspr24G0TabularAdapterError`，输出目录和预测文件均不存在。

## 8. 运行制品与 CPU 入口

正式运行根固定为 `<LSPR24_G0_RUN_ROOT>/baselines/lspr24-g0-d-hgb-xgboost-seed42-<唯一标识>/`，必须不存在后才创建。最低制品为：`config_snapshot.json`、`environment.json`、`data_binding.json`、`fair-budget-plan-receipt.json`、`fair-budget-execution-receipt.json`、`architecture_selection.json`、`dev_validation.json`、`calibration.json`、`threshold_freeze.json`、`summary.json`、`cost.json`、`predictions.jsonl.gz`、`console.log`、`artifact_manifest.json`。所有预测仅来自开发区三段评价和校准；文件名不得出现最终区内容。

计划中的 CPU 入口为：

```bash
python -m flow_probe.lspr24_g0_tabular_adapter \
  --g0-run-root <LSPR24_G0_RUN_ROOT> \
  --restricted-root <LSPR24_G0_RESTRICTED_ROOT> \
  --output-dir <LSPR24_G0_RUN_ROOT>/baselines/lspr24-g0-d-hgb-xgboost-seed42-<唯一标识> \
  --model hgb --model xgboost --seed 42
```

启动脚本须显式设置每模型一个新 CPU 进程、线程上限 `1`，沿用现有 HGB 与 XGBoost 的 `device=cpu`、`tree_method=hist` 和运行时能力收据。实际执行只在 G0-D 放行、计划收据已冻结、独立审查无严重或重要问题后进行。

## 9. 验收与风险

实现阶段按工程规则先写两条目标测试，再实现适配器；仅运行这两条测试及受影响的 `test_tabular_baselines.py`，不运行训练或全量数据读取。之后执行 Python 格式化和受影响模块的静态语法检查。

当前风险是现有通用 `tabular_baselines.py` 将评估切分抽象为单一 `validation`，而 LSPR24 需要显式区分架构选择、开发验证和校准。因此适配器必须持有四段状态机，通用执行器只能接收已验证的单次分区输入，不能由旧 `--stage` 语义代替 LSPR24 合同。
