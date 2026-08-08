# 任务十五 GPU 执行报告

## 结论

G4R-A2 双锚点契约测试和两步 SwanLab 在线冒烟均通过。202 步正式实验完整结束且运行制品验收通过，但四项研究门槛仅通过两项，因此 G4R-A2 整体不通过。按既定分支应停止继续扫描锚点比例或博弈权重，转入物理状态显式连接生成表征的结构性方案设计。

## 文件同步与散列

主进程依据用户明确授权，将以下三个白名单文件通过 `rsync` 同步到服务端固定项目 `/root/autodl-tmp/thesis/experiments/llm_probe`，三个传输退出码均为 `0`。本执行代理随后在服务端核对 SHA-256：

- `src/flow_probe/game_train.py`：`ff35fc0bf407dc54c302a3840dfbd7552b08c98ebee5d7172007cf355f6fa67c`
- `tests/test_game_train.py`：`5b868d227614ca7babdda6d4ce883b6f6e990c958cab525537a3229c591bcac6`
- `configs/physics_dual_anchor_seed42.yaml`：`d528f875977766731e51f2b53797c124c4d14e8f7011e230946126f2ced9be64`

三份服务端散列与本机记录逐字一致。启动前数据盘占用 `74%`，可用空间 `14 GiB`，未触发容量门禁。

## 精确契约测试

服务端仅运行以下四个精确节点：

```text
tests/test_game_train.py::test_settings_accept_independent_g4r_variant
tests/test_game_train.py::test_settings_accept_g4r_dual_anchor_state_mode
tests/test_game_train.py::test_settings_reject_dual_anchor_for_other_variants
tests/test_game_train.py::test_state_mask_persists_dual_anchor_mode_and_each_mask_structure
```

结果：`8 passed in 1.25s`，退出码 `0`。

- 日志：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/game-coordination/verification-20260722-task15/contract-tests.log`
- 退出码：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/game-coordination/verification-20260722-task15/contract-tests.exit`

## 两步在线冒烟

- 输出目录：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/game-coordination/qwen3-1.7b-seed42-g4r-a2-dual-anchor-smoke2-v2`
- 外部日志：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/game-coordination/verification-20260722-task15/smoke2-v2.log`
- 外部退出码：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/game-coordination/verification-20260722-task15/smoke2-v2.exit`
- 验收日志：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/game-coordination/verification-20260722-task15/smoke2-v2-validation.log`
- SwanLab 运行号：`mnj6n2cv`
- SwanLab 地址：`https://swanlab.cn/@mortiswang/malicious-traffic-llm/runs/mnj6n2cv`
- SwanLab 云端核验日志：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/game-coordination/verification-20260722-task15/smoke2-v2-swanlab-cloud.log`

验收结果：

- 训练退出码为 `0`，`status=finished`。
- `max_steps=2`，`optimizer_updates=2`，指标文件恰有两行且步号为 `[1, 2]`。
- `private_state_anchor_forced` 两步合计为 `2`。
- `state_mask.mode=anchor0_plus_one`。
- 共 `807` 个状态掩码，每个掩码第 `0` 位均为真，每个掩码的真值数均为 `2`。
- SwanLab 跟踪模式为 `online`，本地运行目录 `swanlog/game-train/run-20260722_142253-mnj6n2cv` 存在。
- SwanLab 云端接口返回 `state=FINISHED`，并能列出训练指标和五项验证指标序列。
- 峰值 GPU 显存为 `3972.68408203125 MiB`，运行时间为 `15.831736881285906` 秒。
- 生成验证损失为 `0.7969037890434265`。
- 物理残差均方误差为 `0.1677069514989853`。
- 状态均方误差为 `0.18087875843048096`。
- 已观测状态均方误差为 `0.006449662148952484`。
- 未观测状态均方误差为 `0.29716481765111286`。

首次制品验收脚本错误地将 `step_metrics.jsonl` 中嵌套在 `.metrics` 下的指标当作顶层字段，因而求和得到空值。该脚本错误未改变训练制品，首次日志已保留为 `smoke2-v2-validation.attempt1.log` 和 `smoke2-v2-validation.attempt1.exit`；修正查询路径后全部断言通过，未重跑冒烟。

## 202 步正式实验

- `screen` 名称：`task15-g4r-a2-202`
- `screen` 进程：`321305`
- GPU 训练进程：`321314`，运行结束后正常退出
- 正式退出码：`0`
- 训练状态：`finished`
- 更新数：`202 / 202`
- 私有状态锚点强制次数：`202`
- 运行时间：`485.50150445848703` 秒
- 峰值 GPU 显存：`5831.7822265625 MiB`
- 收尾状态：`screen` 已退出，GPU 显存已释放到 `0 MiB`
- 输出目录：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/game-coordination/qwen3-1.7b-seed42-g4r-a2-dual-anchor202-v1`
- SwanLab 运行号：`yv5wfs11`
- SwanLab 地址：`https://swanlab.cn/@mortiswang/malicious-traffic-llm/runs/yv5wfs11`
- 外部日志：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/game-coordination/verification-20260722-task15/formal-202.log`
- 外部退出码：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/game-coordination/verification-20260722-task15/formal-202.exit`
- 启动命令：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/game-coordination/verification-20260722-task15/formal-202.command`
- 启动时间：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/game-coordination/verification-20260722-task15/formal-202.started_at`
- 完整性验收日志：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/game-coordination/verification-20260722-task15/formal-202-integrity.log`
- SwanLab 云端核验日志：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/game-coordination/verification-20260722-task15/formal-202-swanlab-cloud.log`

正式命令使用双锚点配置、`--variant G4R`、`--max-steps 202` 和绝对模型路径，未设置 `validation-limit`。

正式验证指标与固定门槛：

| 指标 | 实际值 | 门槛 | 裁决 |
| --- | ---: | ---: | --- |
| 生成验证损失 | `0.010701656247307019` | `<= 0.030804` | 通过 |
| 物理残差 | `0.0009892649964733731` | `<= 0.097318` | 通过 |
| 未观测状态误差 | `0.5179845730365185` | `<= 0.125748` | 失败 |
| 已观测状态误差 | `0.5109034163653481` | `<= 0.101337` | 失败 |

总体状态均方误差为 `0.5153812264451886`。四项门槛必须同时满足，因此整体裁决为失败。

正式制品完整性验收结果：

- `step_metrics.jsonl` 共 `202` 行，首尾步号为 `1` 和 `202`，优化更新和私有锚点强制次数均合计为 `202`。
- 共 `807` 个状态掩码，模式为 `anchor0_plus_one`；每个掩码第 `0` 位均为真，且真值数均为 `2`。
- 制品清单列出的 `12` 项路径全部存在。
- 外部日志未匹配到 `Traceback`、错误、异常、显存溢出或非数值信号。
- SwanLab 本地运行目录存在；云端接口返回 `state=FINISHED`，并能列出训练指标和五项验证指标序列。

## 变更与验证边界

- 未修改本地生产代码、测试或配置。
- 未执行 Git 操作。
- 未运行完整测试、Ruff、Black 或 Prettier。
- 所有训练和测试命令均使用 `uv run --no-sync`。
