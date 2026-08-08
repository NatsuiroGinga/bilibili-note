# 任务十五双锚点最小契约修复报告

## 结论

已完成 G4R 双锚点监督的最小契约修复。生产代码仅放宽 G4R 的状态监督模式，并让状态掩码制品记录运行时实际模式；未修改协调算法、物理公式或训练预算。

## 根因

- `game_train.py` 的全局状态监督门禁要求所有协调训练变体均使用 `anchor0_only`，导致 G4R-A2 在模型加载前拒绝 `anchor0_plus_one`。
- `_write_state_mask` 将制品中的 `mode` 固定写成 `STATE_SUPERVISION_MODE`，即使训练使用双锚点，制品仍会错误记录为 `anchor0_only`。

## 修改文件

- `thesis/experiments/llm_probe/src/flow_probe/game_train.py`
- `thesis/experiments/llm_probe/tests/test_game_train.py`
- `.Codex/docs/sdd/task-15-dual-anchor-contract-fix-report.md`

## 生产变更

- G4R 允许 `anchor0_only` 和 `anchor0_plus_one`。
- G2、G3、G4、G5、G5-STOP-RESPONSE 继续只允许 `anchor0_only`。
- `_write_state_mask` 新增必填关键字参数 `mode`，并将该值写入 `state_mask.json`。
- 训练调用点传入 `settings.state_supervision_mode`。

## 契约测试

新增以下最小测试，未在本机执行：

- `tests/test_game_train.py::test_settings_accept_g4r_dual_anchor_state_mode`
- `tests/test_game_train.py::test_settings_reject_dual_anchor_for_other_variants`
- `tests/test_game_train.py::test_state_mask_persists_dual_anchor_mode_and_each_mask_structure`

第三项测试同时检查：

- `state_mask.mode` 等于 `anchor0_plus_one`。
- 制品中的逐样本掩码与掩码构造器输出一致。
- 每个掩码长度为既有五锚点结构，`q0` 必为真，且内部锚点恰有一个为真。

## 本地验证

### Black

首次通过 `uvx --offline black` 启动时，沙箱拒绝访问本机 uv 缓存，命令退出码为 `2`，Black 未初始化。随后直接调用本机 uv 缓存中的 Black 可执行文件完成唯一一次实际格式化：

```text
env BLACK_CACHE_DIR=/tmp/codex-black-cache /Users/bilibili/.cache/uv/archive-v0/OhdDOq7ZSSMpkmRP/bin/black thesis/experiments/llm_probe/src/flow_probe/game_train.py thesis/experiments/llm_probe/tests/test_game_train.py
```

结果：退出码 `0`，两个文件完成格式化。

### Python 语法检查

```text
env PYTHONPYCACHEPREFIX=/tmp/task15-dual-anchor-pycache thesis/experiments/llm_probe/.venv/bin/python -m py_compile thesis/experiments/llm_probe/src/flow_probe/game_train.py thesis/experiments/llm_probe/tests/test_game_train.py
```

结果：退出码 `0`，无输出。

### 未执行项

- 按任务约束未在本机运行 pytest。
- 按任务约束未运行 Ruff。
- 未连接 GPU 服务器，未生成训练或测试制品。

## 建议的服务器验证

建议在服务端项目根目录使用现有 uv 环境且禁止依赖同步：

```bash
source ~/.bashrc
cd /root/autodl-tmp/thesis/experiments/llm_probe
uv run --no-sync python -m pytest -q \
  tests/test_game_train.py::test_settings_accept_independent_g4r_variant \
  tests/test_game_train.py::test_settings_accept_g4r_dual_anchor_state_mode \
  tests/test_game_train.py::test_settings_reject_dual_anchor_for_other_variants \
  tests/test_game_train.py::test_state_mask_persists_dual_anchor_mode_and_each_mask_structure
```

其中既有节点 `test_settings_accept_independent_g4r_variant` 用于确认 G4R 的单锚点兼容性；其余三个节点覆盖本次新增契约。

## 遗留风险

- 新增契约仅完成本地语法检查，行为结果必须以上述服务器精确测试为准。
- 本任务开始前，`game_train.py` 与 `test_game_train.py` 已被 Git 显示为未跟踪文件，因此无法依赖基线差异统计区分文件中的历史内容；本次修改已按目标符号和调用点逐项核对。
