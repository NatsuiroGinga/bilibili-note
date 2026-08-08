# 任务十四 G2-G4 实现报告

## 状态

**带关注项完成。** G2、G3、G4 纯数学协调器、共享梯度写入、状态头私有更新、统一训练入口、命令入口、逐步指标和本地制品协议均已实现。按仓库强制规则，本机未运行 pytest；服务器目标测试和两步在线冒烟仍是正式运行前门禁。

## 修改文件

- 新建 `thesis/experiments/llm_probe/src/flow_probe/game_coordination.py`
- 新建 `thesis/experiments/llm_probe/src/flow_probe/game_train.py`
- 修改 `thesis/experiments/llm_probe/pyproject.toml`
- 新建 `thesis/experiments/llm_probe/tests/test_game_coordination.py`
- 新建 `thesis/experiments/llm_probe/tests/test_game_train.py`
- 新建 `.Codex/docs/sdd/task-14-g234-report.md`

未修改物理残差、数据划分、状态掩码生成、模型加载基座或现有任务十三求解器。

## 已实现接口

- `solve_symmetric_bargaining(gram, resolution) -> CoordinationSolution`
  - 复用任务十三 `validate_gram_matrix`、`_simplex_weights` 与 `direction_margins`。
  - 只接受三个严格正边际，最大化等权对数边际和。
  - 无严格共同下降方向时退化为纯生成方向。
- `solve_asymmetric_bargaining(gram, powers, resolution) -> CoordinationSolution`
  - 固定训练议价权为 `(0.6, 0.2, 0.2)`。
  - 校验三个议价权均为正且总和为 1。
  - 最大化固定议价权加权对数边际和。
- `solve_reliability_protected(gram, reliability, generation_floor, resolution) -> CoordinationSolution`
  - 枚举状态、物理、状态与物理三个辅助活跃集合。
  - 约束生成边际不低于 `0.95`，活跃辅助边际严格为正。
  - 跨活跃集合采用按总议价权归一化的可靠性加权对数效用。
  - 可靠性为零时拒绝物理目标；无可行辅助时退化为纯生成。
  - 返回生成否决、辅助接受和纯生成退化元数据。
- `train_game_variant(probe, settings, tracking, raw_config) -> dict[str, object]`
  - G2、G3、G4 共用数据、样本顺序、状态掩码、状态头、物理残差和最终评价协议。
  - 三目标共享梯度按非零范数严格归一化；零辅助梯度不伪造方向，G2/G3 退化，G4 只枚举可用目标。
  - 共享 LoRA 梯度按协调权重组合，并乘生成梯度范数恢复更新尺度。
  - 状态头不参与议价，只写入协调解已接受的状态和物理私有梯度；G4 物理私有梯度再乘物理可靠性。
  - G4 可靠性实现为 `v_p * (1 + cos(g_s, g_p)) / 2`；`v_p` 复用现有状态记录校验，严格对应容量、可观测输入和边界锚点有效比例。
  - 每步同步写入 `step_metrics.jsonl` 并调用 SwanLab 在线记录。
  - 固定允许 2 步在线冒烟或 202 步正式预算、0.02 单纯形网格、0.95 生成底线、生成 `4x4` 累积批量和物理批量 4。
- 命令入口 `flow-probe-train-game = "flow_probe.game_train:main"`。

## 制品与指标

单次运行要求保存以下制品：

- `config_snapshot.yaml`
- `environment.json`
- `input_sha256.json`
- `sample_order.json`
- `state_mask.json`
- `console.log`
- `step_metrics.jsonl`
- `training_summary.json`
- `final_adapter/`
- `state_head.pt`
- `artifact_manifest.json`
- `swanlog/game-train/`

逐步指标包含三目标损失、三目标范数、三组余弦、协调权重、方向边际、效用、物理有效比例、物理可靠性、生成否决、状态/物理拒绝、纯生成退化、LoRA 与状态头梯度范数、学习率、优化器更新、吞吐和峰值显存。

## 验证结果

### Black

命令：

```bash
uv run --offline --group dev black src/flow_probe/game_coordination.py src/flow_probe/game_train.py tests/test_game_coordination.py tests/test_game_train.py
```

结果：首次受限执行因无法访问 `~/.cache/uv` 失败；获得沙箱许可后同一命令成功。三个文件被格式化，一个文件无需修改。

### Ruff

命令：

```bash
uv run --offline --group dev ruff check src/flow_probe/game_coordination.py src/flow_probe/game_train.py tests/test_game_coordination.py tests/test_game_train.py
```

结果：已按规则运行一次。未发现语法或结构缺陷；报告两项不影响执行的问题：`game_coordination.py` 中一个未使用的类型导入，以及 `test_game_coordination.py` 的导入排序。依据仓库规则，不因格式偏好继续修改或重复 Ruff。

### 语法与差异检查

成功命令：

```bash
env PYTHONPYCACHEPREFIX=/tmp/flow-probe-task14-pycache .venv/bin/python -m py_compile src/flow_probe/game_coordination.py src/flow_probe/game_train.py tests/test_game_coordination.py tests/test_game_train.py
git diff --check -- pyproject.toml src/flow_probe/game_coordination.py src/flow_probe/game_train.py tests/test_game_coordination.py tests/test_game_train.py
```

结果：项目解释器为 Python 3.10.20；四个 Python 文件语法检查通过，差异空白检查通过。语义校准后对 `game_train.py` 的最小语法检查及差异空白检查再次通过。

补充记录：第一次误用系统 Python 3.9 执行 `py_compile`，因其全局字节码缓存路径不在沙箱可写范围而失败；改用项目 Python 3.10.20 并把缓存定向到 `/tmp` 后通过。

### pytest

**本机未运行 pytest。** 这是根 `AGENTS.md` 的强制要求，不代表目标测试已通过。测试文件是在实现完成后编写，等待同步到 GPU 服务器后执行。

建议服务器最小目标测试：

```bash
source ~/.bashrc
cd /root/autodl-tmp/thesis/experiments/llm_probe
uv run --no-sync pytest -q tests/test_game_coordination.py tests/test_game_train.py tests/test_gradient_feasibility.py::test_common_and_protected_solvers_use_deterministic_integer_simplex tests/test_gradient_feasibility.py::test_gradient_gram_and_g5_response_use_per_parameter_tensors tests/test_physics_train.py::test_masked_state_loss_ignores_unobserved_errors_and_dense_matches_existing_loss
```

## 建议服务器冒烟

同步白名单文件、核对 SHA-256 并执行 `uv pip install --no-deps -e .` 后，分别运行 G2 与 G4 两步在线冒烟：

```bash
uv run --no-sync flow-probe-train-game --config configs/physics_sparse_seed42.yaml --variant G2 --output-dir runs/game-coordination/g2-smoke-seed42 --run-name qwen3-1.7b-g2-smoke-seed42 --max-steps 2 --validation-limit 8 --model-path /root/autodl-tmp/thesis/models/Qwen3-1.7B
uv run --no-sync flow-probe-train-game --config configs/physics_sparse_seed42.yaml --variant G4 --output-dir runs/game-coordination/g4-smoke-seed42 --run-name qwen3-1.7b-g4-smoke-seed42 --max-steps 2 --validation-limit 8 --model-path /root/autodl-tmp/thesis/models/Qwen3-1.7B
```

冒烟验收重点：每次恰好两次优化器更新、两行逐步 JSONL、SwanLab 云端逐步点可见、生成边际满足 G4 底线、适配器与状态头存在、制品清单状态为 `finished`。

## 遗留关注项

- 本机未执行 pytest，服务器目标测试是行为门禁。
- 未连接服务器、未执行 GPU 反向冒烟、未启动正式训练。
- Ruff 的两项非执行性提示仍保留，独立审查可决定是否在提交前整理；不得因此重复本轮 Ruff。
- G4 跨不同辅助活跃集合的效用采用总议价权归一化，以避免不同参与目标数量直接改变效用量级；正式实验前应由独立审查确认该数学选择与论文公式表述一致。

## 服务器确定性并列排序修复

服务器目标测试发现完全同向 Gram 矩阵下的 G4 并列解不稳定：数学上效用与三个边际相同的候选因浮点舍入噪声被原始比较键区分，实际选择 `(0.56, 0.34, 0.10)`，而不是既定活跃集合与权重键应选择的 `(0.96, 0.02, 0.02)`。

根因位于 `game_coordination.py` 的 `_protected_key`，同类 `_bargaining_key` 具有相同风险。两个键原先直接比较未经归并的 `objective` 和 `margins`，使约 `1e-16` 的数值噪声先于确定性权重规则参与排序。

最小修复如下：

- 新增 `_stable_key_value`，按既有 `STRICT_MARGIN_TOLERANCE=1e-12` 把效用和边际统一量化为整数比较键。
- `_protected_key` 与 `_bargaining_key` 只量化 `objective` 和三个 `margins`。
- 活跃集合优先级、原始权重排序、议价公式、可靠性、生成底线、训练代码和测试预期均未修改。

修复门禁：

```bash
uv run --offline --group dev black src/flow_probe/game_coordination.py
env PYTHONPYCACHEPREFIX=/tmp/flow-probe-task14-pycache .venv/bin/python -m py_compile src/flow_probe/game_coordination.py
```

结果：Black 通过且文件无需重排；项目 Python 3.10 语法检查通过。按修复要求未运行 Ruff，也未在本机运行 pytest。服务器需重跑原失败目标节点确认完全同向 Gram 矩阵选择 `(0.96, 0.02, 0.02)`。
