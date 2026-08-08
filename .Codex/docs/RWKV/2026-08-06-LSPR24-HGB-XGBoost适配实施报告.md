# LSPR24 HGB/XGBoost 共享适配实施报告

- **日期**：2026-08-06
- **范围**：仅实现 LSPR24 G0-D 开发区 HGB/XGBoost 共享适配层、最小启动入口和目标测试。
- **数据边界**：测试只使用临时目录中的合成 Parquet 夹具；未读取真实 LSPR24 数据、原始标签或最终区制品，未训练分类器。

## 变更内容

1. 新增 `thesis/experiments/llm_probe/src/flow_probe/lspr24_g0_tabular_adapter.py`。
   - 只接受 G0-D 开发放行决策、开发窗口、历史样本、字段清单、评价簇和绑定的开发标签侧车。
   - 在任何 Parquet 特征读取前拒绝最终区/封存路径、未放行的决策收据、禁入字段和不匹配的标签侧车。
   - 对 `H={1,4,16,32}` 按旧到新的时间顺序和字段清单顺序构造 `H×F` 展平特征。
   - HGB 与 XGBoost 共享同一只读输入映射、字段顺序、样本顺序、特征矩阵哈希、标签绑定哈希和预算计划。
   - 四段开发区固定为 `train-fit`、`architecture-selection`、`dev-validation`、`calibration`；预算收据只登记开发区的单次拟合和单次架构选择评价，初始状态为 `NOT_READY`。
2. 最小扩展 `thesis/experiments/llm_probe/src/flow_probe/tabular_baselines.py`，公开 `run_prepared_tabular_baseline_suite`，使已验证的 `PreparedTabularData` 可进入原有 HGB/XGBoost 执行路径而不重新读取数据路径。
3. 新增 `thesis/experiments/llm_probe/scripts/run_lspr24_g0_tabular_baselines.sh`。
   - 仅接受 G0-D 运行根、开发标签受限根和不存在的唯一输出目录。
   - 预先拒绝 `final-test` 与 `sealed` 路径，再调用 Python CPU 入口并固定传入 `hgb` 与 `xgboost`。
4. 新增 `thesis/experiments/llm_probe/tests/test_lspr24_g0_tabular_adapter.py`，使用合成四分区夹具覆盖两条实施计划指定的目标测试。

## 红绿验证

### 红灯

运行：

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --no-sync pytest -q \
  tests/test_lspr24_g0_tabular_adapter.py::test_development_adapter_constructs_identical_hgb_xgboost_input_and_keeps_history_budget \
  tests/test_lspr24_g0_tabular_adapter.py::test_development_adapter_rejects_final_test_and_unbound_or_forbidden_sidecar
```

结果：适配器尚不存在时，5 个参数化用例均因 `flow_probe.lspr24_g0_tabular_adapter` 缺失失败。这是预期的有效红灯。

### 绿灯

对同一命令仅重跑目标测试，结果为：`5 passed in 2.01s`。

通过内容：

- HGB/XGBoost 引用同一 `H×F` 输入映射，训练样本保持夹具定义的稳定顺序。
- `H={1,4,16,32}` 的每个训练矩阵宽度严格为 `H×F`。
- 预算计划中每个模型和历史长度组合只登记一次拟合、一次架构选择评价。
- 最终区路径、乱序未绑定侧车、`SrcPort` 和 `Label` 禁入字段均在构造特征矩阵或分类器调用前被拒绝。
- 失败路径未创建输出目录或预测文件。

## 未执行项

- 未运行训练、真实数据读取、最终区访问或预测生成。
- 按本次任务的明确限制，未运行格式化、静态检查、全仓测试或独立复审。
- 未修改 Rust G0 文件、数据合同、路线总控、共享 B0 视图或配置。

## 复审修复记录

- **修复日期**：2026-08-06
- **复审结论**：首轮实现存在 5 类严重或重要问题，已按同一任务边界完成一次最小红绿灯修复。

### 修复红灯

先扩充 `tests/test_lspr24_g0_tabular_adapter.py`，只运行该目标测试文件：

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --no-sync pytest -q \
  tests/test_lspr24_g0_tabular_adapter.py
```

修正测试注入点后得到稳定行为红灯：`17 failed, 3 passed in 3.38s`。失败分别证明 CLI 未执行基线、重复身份未提前拒绝、窗口多余列被投影隐藏、谱系与历史证明未验证、登记的最终区路径未被使用。

### 修复内容

1. 正式 Python CLI 在 G0-D 门禁通过后逐个历史长度调用 `run_prepared_tabular_baseline_suite`，脚本仍调用该 CLI。合成测试用执行替身代替分类器拟合，验证 4 次调用并生成计划要求的 14 项根制品。
2. `history-samples.parquet`、开发标签侧车和评价簇清单分别在绑定比较与标签字典构造前拒绝重复 `sample_id`，包括不同 `stable_order` 和冲突标签。
3. 在读取开发窗口列投影前，使用 Parquet 全模式严格比较 `window_id + field-manifest.json` 的冻结顺序；`Label`、IP、端口和任意未登记列均立即失败。
4. 语义哈希收据现在登记并绑定字段谱系与历史不变量收据。适配器验证字段递归祖先、字段清单哈希、历史样本哈希，以及同端点、同连续段、同分区和旧到新的逐样本证明。
5. 最终区回归夹具保留普通开发历史文件，同时让语义收据真实指向 `final-test-history-samples.parquet`。适配器先解析全部登记路径并拒绝最终区，再进行任何 Parquet 全模式或数据读取；测试确认 Parquet 打开次数为零。

### 修复绿灯

仅重跑相同目标测试文件，结果为：`20 passed in 5.06s`。

本轮未读取真实数据、未运行真实 HGB/XGBoost 训练、未访问最终区、未修改 Rust G0、数据合同或路线总控。按修复任务限制，未运行格式化、静态检查、全仓测试或额外复审。

## 四段状态机协议修复记录

- **修复日期**：2026-08-06
- **新增严重问题**：首轮正式入口把同一份含 `architecture-selection`、`dev-validation`、`calibration` 的评价映射交给每个历史长度的执行器，在冻结候选前暴露了后两段；三个阶段制品只是同一汇总的复制件。

### 状态机红灯

新增合成执行回归后，仅运行目标测试文件：

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --no-sync pytest -q \
  tests/test_lspr24_g0_tabular_adapter.py
```

结果为：`1 failed, 19 passed in 2.55s`。失败证据显示当前只有 4 次全分区调用，而不是 4 次架构选择、1 次开发验证、1 次校准；同时 `architecture_selection.json`、`dev_validation.json`、`calibration.json` 的 SHA-256 完全相同。

### 状态机修复

1. 为每次执行构造阶段专用 `PreparedTabularData`，评价映射严格只含当前阶段：架构选择阶段只含 `architecture-selection`，候选冻结后才构造 `dev-validation`，开发验证收据落盘后才构造 `calibration`。
2. 架构选择对 `H={1,4,16,32}` 的冻结默认配置按“两模型宏平均 F1 的均值最大、并列时历史最短”排序，写入唯一 `selected_candidate` 后冻结 `architecture_selection.json`。
3. 通用执行器增加已拟合模型状态捕获与复用参数。四个候选在架构选择时各拟合一次；开发验证和校准复用所选候选的同一模型对象，两个后续阶段的 `fit_count=0`。
4. `dev_validation.json` 绑定 `architecture_selection.json` 的 SHA-256；`calibration.json` 同时绑定架构选择与开发验证收据；`threshold_freeze.json` 绑定校准收据。
5. 校准阶段按模型使用 `calibration` 概率拟合单调递增等距回归校准器，并按“宏平均 F1 最大、并列时阈值最高”冻结每个模型的阈值。
6. 架构选择、开发验证和校准三个制品分别保存本阶段结果，内容和 SHA-256 均不同，不再复制同一汇总。

### 状态机绿灯

仅重跑同一目标测试文件，结果为：`20 passed in 3.92s`。

合成执行替身确认实际调用顺序为 4 次 `architecture-selection`、1 次所选候选 `dev-validation`、1 次同一候选 `calibration`；未运行真实 HGB/XGBoost 训练，未读取真实数据，未修改 Rust G0、合同或路线总控，也未运行格式化、静态检查或全仓测试。
