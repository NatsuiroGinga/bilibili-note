# GeNIS 候选协议物化阶段 3 实现报告

## 结论

阶段 3 的本机实现已经完成，但**尚未执行服务器测试、真实数据物化或最终验收**。新增模块只消费计划固定的 GeNIS v3 JSONL、绑定会话分配和划分摘要，不读取 `eval300`，不修改通用冻结协议加载器、树模型入口、依赖文件或任何 TQH-C2 目录。

## 变更范围

### 新增生产代码

- `thesis/experiments/llm_probe/src/flow_probe/genis_candidate.py`

实现内容：

1. 验证 `genis_materialized_split_v1`、`genis_hybrid_forward_split_v1`、固定比例、来源清单和会话分配 SHA-256。
2. 从绑定的 `session_assignments.jsonl` 恢复子类，不从文件名、提示词或标签文本猜测子类。
3. 校验六个固定 JSONL 的会话、行数、文件归属、二元标签、家族标签、八个公共观测字段和严格时间顺序。
4. 使用 `genis:` 加 SHA-256 生成不含标签语义的新稳定 `sample_id`；旧标识只参与内存哈希，不写入候选制品。
5. 展平八个公共观测及八个缺失掩码，生成字段角色、标签合同、家族/子类/开放集清单和泄漏审计。
6. 用训练观测签名排除严格验证中的精确重复；被排除记录仍保留在主表，并写 `development_eligible=false` 与固定原因。
7. 以 `_INCOMPLETE` 标记未完成目录，成功写完全部制品和协议哈希后才删除标记；拒绝覆盖已有输出目录。
8. 提供 `python -m flow_probe.genis_candidate` 命令入口，不修改 `pyproject.toml`。

### 新增隔离测试

- `thesis/experiments/llm_probe/tests/test_genis_candidate.py`

测试夹具不含 `attack_subtype`，覆盖：

- 绑定会话恢复子类、家族和开放集语义；
- 旧标识和来源文件名不进入模型或主记录制品；
- 训练/验证精确观测重复的保留与清单排除；
- `load_frozen_protocol` 加载家族、子类和开放集清单；
- 两份输出逐字节一致和拒绝覆盖；
- 分配哈希、来源摘要、未知会话、会话行数、文件归属、时间交叉与非有限特征的拒绝路径。

## 本机验证

### 已通过

```text
PYTHONPYCACHEPREFIX=/tmp/genis-candidate-pycache python3 -m py_compile \
  thesis/experiments/llm_probe/src/flow_probe/genis_candidate.py \
  thesis/experiments/llm_probe/tests/test_genis_candidate.py
```

结果：退出码 `0`。

```text
thesis/experiments/llm_probe/.venv/bin/black \
  thesis/experiments/llm_probe/src/flow_probe/genis_candidate.py \
  thesis/experiments/llm_probe/tests/test_genis_candidate.py
```

结果：退出码 `0`，两份文件完成格式化。

### 非代码失败与处置

1. 首次直接调用 `black` 返回命令不存在。根因是格式化器只位于项目虚拟环境；随后使用项目内固定路径成功执行。
2. 首次 `py_compile` 尝试写入沙箱外的系统 Python 缓存目录，返回权限错误。根因是缓存位置，不是源码语法；将 `PYTHONPYCACHEPREFIX` 指向 `/tmp` 后同一检查通过。
3. `Ruff` 只报告 3 个 `UP012` 风格提示，没有语法或结构问题。依照实验局部规则，不为纯风格提示继续修改，也不重复运行 `Ruff`。

### 明确未执行

- 未在本机或服务器运行 `pytest`。
- 未连接或启动 GPU 服务器。
- 未读取 `eval300`、时间前向测试内容或开放集内容来选择字段、阈值和超参数。
- 未运行真实 137 万行数据物化、双份确定性比较和冻结协议加载验收。
- 未启动 HGB、XGBoost 或任何 GPU 训练。

## 服务器后续精确命令

以下命令应在代码通过 `rsync` 白名单同步、服务器启动并完成硬件与磁盘预检后执行。

### 1. 最小目标测试

```bash
source ~/.bashrc >/dev/null 2>&1
cd /root/autodl-tmp/thesis/experiments/llm_probe
uv run --no-sync pytest -q \
  tests/test_genis_candidate.py \
  tests/test_frozen_protocol.py \
  tests/test_tabular_baselines.py
```

预计耗时：`1～3` 分钟。退出码必须为 `0`；失败时不得开始真实物化。

### 2. 双份确定性物化

```bash
source ~/.bashrc >/dev/null 2>&1
cd /root/autodl-tmp/thesis/experiments/llm_probe

PREPARED=runs/data-prepared/genis-hybrid-forward-v1-20260719-v3
ASSIGNMENTS=runs/data-splits/genis-hybrid-forward-v1-20260719-v2/session_assignments.jsonl
PLAN=runs/data-splits/genis-hybrid-forward-v1-20260719-v2/plan_summary.json
OUT_A=runs/data-candidate-builds/genis-v0/build-a
OUT_B=runs/data-candidate-builds/genis-v0/build-b
PARTIAL_A=runs/data-candidate-builds/genis-v0/build-a.partial
PARTIAL_B=runs/data-candidate-builds/genis-v0/build-b.partial

test ! -e "$OUT_A"
test ! -e "$OUT_B"
test ! -e "$PARTIAL_A"
test ! -e "$PARTIAL_B"

uv run --no-sync python -m flow_probe.genis_candidate \
  --prepared-dir "$PREPARED" \
  --assignments "$ASSIGNMENTS" \
  --plan-summary "$PLAN" \
  --output-dir "$PARTIAL_A"
mv "$PARTIAL_A" "$OUT_A"

uv run --no-sync python -m flow_probe.genis_candidate \
  --prepared-dir "$PREPARED" \
  --assignments "$ASSIGNMENTS" \
  --plan-summary "$PLAN" \
  --output-dir "$PARTIAL_B"
mv "$PARTIAL_B" "$OUT_B"

diff -qr "$OUT_A" "$OUT_B"
```

预计耗时：每份约 `8～20` 分钟，两份顺序执行约 `16～40` 分钟。预计峰值内存和输出体积必须在启动后实测记录；若数据盘达到既定停止门槛，立即停止第二份物化并通知用户。

### 3. 协议加载冒烟

```bash
source ~/.bashrc >/dev/null 2>&1
cd /root/autodl-tmp/thesis/experiments/llm_probe
uv run --no-sync python -c 'from pathlib import Path; from flow_probe.frozen_protocol import load_frozen_protocol; p=load_frozen_protocol(Path("runs/data-candidate-builds/genis-v0/build-a"), expected_protocol_version="data-protocol-v1.0-rc1", expected_status="provisional", expected_phase="theory_selection"); print(p.protocol_sha256, len(p.manifests))'
```

预期：输出一个协议 SHA-256 和清单数 `7`。

## 按量服务器重启恢复

1. 代码、输入和输出均位于 `/root/autodl-tmp/thesis/`，不依赖 `/tmp` 或进程内唯一状态。
2. 物化任务本身不做中途检查点；若关机时存在 `build-a.partial` 或 `build-b.partial`，其中 `_INCOMPLETE` 表示该目录不能使用。保留失败目录和日志作为证据，以新的唯一临时目录从相同输入重跑，不覆盖或伪装续跑。
3. 只有模块、六个输入 JSONL、物化摘要、会话分配和计划摘要哈希均与启动记录一致时才允许重跑。
4. 单份完成后立即把配置、协议、审计、清单和哈希回收到本机；大型 `samples.parquet` 至少在第二份逐字节验收后再决定是否完整回收。
5. `build-a` 与 `build-b` 逐字节一致、加载器通过且独立审查无严重或重要问题后，才能原子发布到 `runs/data-frozen/dataset-candidate-genis-v0/protocol/`。

## 遗留风险

1. 本机没有六个真实 JSONL，因此实际 v1 记录只能依据已核验摘要、既有生成代码和隔离夹具实现；服务器最小测试不能替代真实物化。
2. 137 万行候选主表需要实测内存和 Parquet 体积。当前实现使用列式列表降低 Python 字典峰值，但双份物化仍应顺序执行。
3. 当前输出仍是 `provisional`、`theory_selection`、`review_pending`。它不是完整三源 `dataset-v1`，不能形成最终测试结论。
4. 时间前向与开放集清单会被物化并冻结，但阶段 3 不读取其指标，也不允许据此修改字段或超参数。
