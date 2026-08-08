# Shared B0 物理旁路任务 01 服务器验收报告

## 结论

- 验收结论：**通过任务 01 的服务器目标测试与生产配置双物化门禁**。
- 唯一目标测试结果：`26 passed in 7.62s`，退出码为 `0`。
- 两个独立预建空目录均完成真实物化与公开接口复核，各产生 `2,421` 条记录，复核状态均为 `passed`。
- 两份物化的规定文件集合均恰为 `5` 个；逐文件字节数、字节内容与 SHA-256 全部一致。
- 三个冻结来源的实际记录数均为 `807`，实际 SHA-256 均与生产配置一致。
- 冻结分类文件在两次物化各自的物化前、物化后及最终复核时 SHA-256 均不变。
- 物理量负值计数为 `0`，非有限数计数为 `0`；接收包累计量的非整数数值和负值均为 `0`。
- 本轮没有修改生产代码、测试或配置，没有发布正式数据目录，没有运行格式化，没有启动冒烟、正式训练或 GPU 任务。
- 放行范围仅限任务 01。任务 02 至 05、完整服务器门禁、训练和评估仍未由本报告放行。

## 输入与边界

已完整读取并遵守：

- `AGENTS.md`
- `output/AGENTS.md`
- `output/开题改进交接文档.md`
- `output/第一创新点实验总控.md`
- `thesis/AGENTS.md`
- `thesis/experiments/llm_probe/AGENTS.md`
- `.Codex/docs/AGENTS.md`
- `.Codex/docs/sdd/task-shared-b0-physics-baselines/task_plan.md`
- `.Codex/docs/sdd/task-shared-b0-physics-baselines/reports/fix-task-01-sidecar-round-1.md`
- `.Codex/docs/sdd/task-shared-b0-physics-baselines/reports/fix-task-01-server-failure-round-2.md`
- `.Codex/docs/sdd/task-shared-b0-physics-baselines/reports/review-task-01-sidecar-round-1.md`

本轮只同步并核验以下三个工程文件：

| 文件 | 本地与服务器 SHA-256 |
| --- | --- |
| `src/flow_probe/shared_b0_physics_sidecar.py` | `1e61a21982639c19804697b6be7d64242ffbb71a95f51ce2a896eacf17a01ee8` |
| `tests/test_shared_b0_physics_sidecar.py` | `4d93b6a720111dae0e768c2eddf241eb1216df9b18f53e43c8a250fa59c2ace1` |
| `configs/shared_b0_physics_sidecar_v1.yaml` | `cfce7175cb3692150dd368ac19dd925b345c15f5bf543931579f2b89cc7056de` |

服务器原始日志与物化制品唯一根目录：

```text
/root/autodl-tmp/thesis/experiments/llm_probe/runs/validation/shared-b0-sidecar-acceptance-20260731T071230Z/
```

该目录最终占用 `4.4 MiB`。没有写入生产配置声明的正式发布目录 `runs/data-frozen/dataset-v1-shared-b0-physics-v1/`。

## 服务器前置检查

只读执行：

```bash
df -h /root/autodl-tmp
screen -ls
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
ls -lt runs/validation
```

结果：

- 无 `screen` 会话。
- 无 GPU 计算进程。
- 数据盘使用率为 `82%`，可用空间为 `9.2 GiB`。
- 已触发“使用率达到 80% 或可用空间不足 10 GiB 时通知用户”的提醒门槛，但尚未触发“达到 90% 或不足 5 GiB 时停止新增大型文件”的停止门槛。
- 本轮只增加 `4.4 MiB` 验收制品，不下载模型或数据，不启动训练。

## 同步命令与结果

登录信息只从 `GPU_SSH`、`GPU_PWD` 和既有受管包装器读取；报告不记录主机、端口或密码。执行命令为：

```bash
source ~/.zshrc >/dev/null 2>&1
expect /tmp/gpu-rsync-push.exp \
  /Users/bilibili/personal/note/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py \
  /root/autodl-tmp/thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py
expect /tmp/gpu-rsync-push.exp \
  /Users/bilibili/personal/note/thesis/experiments/llm_probe/tests/test_shared_b0_physics_sidecar.py \
  /root/autodl-tmp/thesis/experiments/llm_probe/tests/test_shared_b0_physics_sidecar.py
expect /tmp/gpu-rsync-push.exp \
  /Users/bilibili/personal/note/thesis/experiments/llm_probe/configs/shared_b0_physics_sidecar_v1.yaml \
  /root/autodl-tmp/thesis/experiments/llm_probe/configs/shared_b0_physics_sidecar_v1.yaml
```

结果：三个命令均成功。同步后在服务器运行：

```bash
sha256sum \
  src/flow_probe/shared_b0_physics_sidecar.py \
  tests/test_shared_b0_physics_sidecar.py \
  configs/shared_b0_physics_sidecar_v1.yaml
```

三个服务器哈希与上表本地哈希逐项一致。

## 目标测试

执行命令：

```bash
uv run --no-sync pytest -q tests/test_shared_b0_physics_sidecar.py
```

结果：

```text
..........................                                               [100%]
26 passed in 7.62s
```

- 退出码：`0`
- 原始日志：`runs/validation/shared-b0-sidecar-acceptance-20260731T071230Z/pytest.log`
- 日志 SHA-256：`f4aca14410deb9c576a23e81c83fe8c90f5a125a6a066dc9953591e7b8ed248f`
- 命令与退出码：同目录下 `pytest.command.txt`、`pytest.exitcode`

上一轮 `zip(..., strict=True)` 引起的 17 个同根失败和范围外配置失败均未复现。

## 双物化命令

`pyproject.toml` 尚未注册物化命令入口，因此按复审许可使用已有公开 Python 接口：

```python
config = load_shared_b0_physics_sidecar_config(
    Path("configs/shared_b0_physics_sidecar_v1.yaml")
)
manifest = materialize_shared_b0_physics_sidecar(config, output_root)
audit = validate_shared_b0_physics_sidecar(
    output_root, Path(config.classification_manifest)
)
```

两次均先创建新的空目录，再在独立 Python 进程中执行上述接口：

```text
runs/validation/shared-b0-sidecar-acceptance-20260731T071230Z/materialization-a/
runs/validation/shared-b0-sidecar-acceptance-20260731T071230Z/materialization-b/
```

结果：

| 物化 | 记录数 | 校验状态 | 记录 SHA-256 | 退出码 |
| --- | ---: | --- | --- | ---: |
| A | 2,421 | `passed` | `90648400f42697fd9c7235b32bdaa2a978167b203e5c0008dabb8e62df791660` | 0 |
| B | 2,421 | `passed` | `90648400f42697fd9c7235b32bdaa2a978167b203e5c0008dabb8e62df791660` | 0 |

原始日志：

- `materialize-a.log`，SHA-256 为 `aa83fa75b254d897eb5662fc7ac9e1e2d79a33520d7d557dabaafab6b0cc0648`
- `materialize-b.log`，SHA-256 为 `ac37232f512c759bdf71b1b24ceeedcd2b2bf970695373320fa9e6ceb1046340`
- 对应命令与退出码保存在 `materialize-a.command.txt`、`materialize-a.exitcode`、`materialize-b.command.txt`、`materialize-b.exitcode`

## 逐文件比较

| 相对路径 | A 字节数 | B 字节数 | A/B SHA-256 | 字节相同 |
| --- | ---: | ---: | --- | --- |
| `candidate/ns3_physics_train.jsonl` | 2,245,867 | 2,245,867 | `90648400f42697fd9c7235b32bdaa2a978167b203e5c0008dabb8e62df791660` | 是 |
| `dataset_manifest.json` | 2,151 | 2,151 | `af97e6ba1cece41ef932bb724ef70487278b8ba2059667e6956bc5dd631ff2cd` | 是 |
| `join_audit.json` | 670 | 670 | `97341f94f9aeacde3b706165da824988de755344bd1c6d51a89bd572b1d3f541` | 是 |
| `materialization_audit.json` | 1,400 | 1,400 | `43422e5c44a3171bafacea11f346cd0bbe28f6a6961bf4802c9d01065cfe18bf` | 是 |
| `source_manifest.json` | 1,332 | 1,332 | `bf2ba90c903a82aa201eefbd168cc4528f375e649bafbc566fbd5445acd24488` | 是 |

两个目录均不存在额外普通文件或缺失文件。逐文件比较结论：`5/5` 字节相同，`5/5` SHA-256 相同。

## 来源与冻结分类审计

| 来源划分 | 配置计数 | 实际计数 | 配置与实际 SHA-256 | 结果 |
| --- | ---: | ---: | --- | --- |
| `train` | 807 | 807 | `d6a6ca23a985223401e1d650d619c2a50b255d2066769e2478cef72cc6239fa0` | 通过 |
| `validation` | 807 | 807 | `0bbbb4ea483867561c329c896cb4e7745a102cb90024c464654e0b7d673c8723` | 通过 |
| `test` | 807 | 807 | `6e64d2ab290813a246ed8efcefd1bb19f1026c2de7b7904d111af67b4465ef94` | 通过 |

旁路输出按来源划分的记录数也分别为 `807/807/807`，总计 `2,421`；`sample_id` 唯一数为 `2,421`，用途唯一值为 `train_fit_diagnostic`。

冻结分类文件 SHA-256：

```text
3ebb156dc9b47dab3bd5ec6db039ae33eeb43b10d1079662f4cc072952f5b0d4
```

该值在 A 物化前、A 物化后、B 物化前、B 物化后和最终独立重算时完全一致。

## 物理量审计

审计对象为 A 物化的 `2,421` 条旁路记录；由于 A/B 记录文件逐字节相同，该结论同时覆盖 B。

| 字段 | 最小值 | 负值数量 |
| --- | ---: | ---: |
| `anchor_times` | 0.0 | 不适用 |
| `state_targets` | 0.0 | 0 |
| `capacity_by_anchor` | 0.0 | 0 |
| `received_bytes_by_anchor` | 0.0 | 0 |
| `received_packets_by_anchor` | 0.0 | 0 |
| `dequeued_bytes_by_anchor` | 0.0 | 0 |
| `dropped_bytes_by_anchor` | 0.0 | 0 |
| `normalization_scale` | 31,250.0 | 0，且严格为正 |

附加计数：

- 非有限数：`0`
- 接收包累计量数值总数：`12,105`，即 `2,421 × 5`
- 非整数数值包数：`0`
- 负包数：`0`
- JSON 原生整数类型包数：`0`
- JSON 浮点类型但数值为整数的包数：`12,105`

最后一项是当前生产序列化把数值统一转换为浮点数的类型事实，不影响本轮“数值整数性”门禁；若后续合同要求 JSON 类型必须为整数，应在新的代码任务中单独处理，不能在本轮服务器验收中改代码。

## 独立审计命令与制品

一次性只读审计脚本只保存在服务器验证目录，不属于生产代码：

```bash
uv run --no-sync python \
  runs/validation/shared-b0-sidecar-acceptance-20260731T071230Z/acceptance_audit.py \
  runs/validation/shared-b0-sidecar-acceptance-20260731T071230Z
```

结果：`status=passed`，退出码为 `0`。

- 审计 JSON：`acceptance-audit.json`
- 审计 JSON SHA-256：`8ebfcbcde922b93d3063bab6a75db8a807b973c375283329e500f5869a4d22fd`
- 审计脚本 SHA-256：`30e3cb2b773164a1372a1d6dd106402f1562e17a31d64a04a168f568f03363c7`
- 命令与退出码：`acceptance-audit.command.txt`、`acceptance-audit.exitcode`
- 最终退出码与哈希汇总：`final-summary.log`

最终汇总中的四个关键退出码为：

```text
pytest 0
materialize-a 0
materialize-b 0
acceptance-audit 0
```

## 未执行项与遗留边界

- 未运行 Black、Ruff、Prettier 或其他格式化命令；这是本轮明确边界。
- 未运行任务 02 至 05 的测试、Shell 检查、普通 Qwen 等价回归、训练冒烟、恢复等价检查、正式训练或评估。
- 未修改或覆盖冻结分类文件、三个 ns-3 来源、生产发布目录及历史运行目录。
- 数据盘已进入容量提醒区间；后续启动训练或新增大型制品前应重新检查可用空间。
- 任务 01 的服务器验收可以标记为通过，但完整 Shared B0 状态监督与标准 PINN 基线仍须继续执行后续实施计划和独立审查门禁。
