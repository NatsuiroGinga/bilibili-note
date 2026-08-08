# Shared B0 物理旁路服务器失败修复报告（第 2 轮）

## 状态

- 代码根因修复已完成，服务器目标测试待重跑。
- 服务器上一轮结果为 `8 passed, 18 failed`，其中 17 个失败共享本报告处理的 `zip(..., strict=True)` 根因。
- 第 18 个失败不在本任务中诊断或处理；本任务不处理配置同步。
- 未修改测试、配置或其他生产源码，未运行服务器、网络或同步命令。

## 根因核验

`_physics_record` 先构造五个锚点时间：

```python
anchor_times = [window_starts[0], *window_ends]
```

随后使用 `zip(anchor_times, anchor_times[1:], strict=True)` 比较相邻锚点。前者固定为 5 项，后者固定为 4 项，长度天然相差 1。对合法的严格递增锚点，`any(...)` 会消费完四个相邻对，随后 `zip` 因两个迭代器没有同时耗尽而抛出：

```text
ValueError: zip() argument 2 is shorter than argument 1
```

同一错误模式还存在于 `_validated_output_record`。如果只修物化阶段，生成制品进入独立复核时仍会再次抛出相同异常，因此两处属于同一代码根因，必须同时修复。

修复前使用五锚点最小输入复现，命令退出码为 `1`：

```bash
python3 -B -c 'anchor_times=[0.0,0.1,0.2,0.3,0.4]; print(list(zip(anchor_times, anchor_times[1:], strict=True)))'
```

文件中另外两处 `strict=True` 分别连接两个已固定为 4 项的窗口序列、两个已固定为 4 项的丢弃量序列。它们的输入应当等长，故保持不变。

## 修改内容

修改文件：

- `thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py`
- `.Codex/docs/sdd/task-shared-b0-physics-baselines/reports/fix-task-01-server-failure-round-2.md`

生产代码仅修改两处参数：

- `_physics_record` 的相邻锚点比较改为 `zip(anchor_times, anchor_times[1:], strict=False)`。
- `_validated_output_record` 的相邻锚点比较改为 `zip(anchor_times, anchor_times[1:], strict=False)`。

`strict=False` 明确表达此处需要按较短切片结束，恰好产生 `(t0, t1)` 至 `(t3, t4)` 四个相邻对，同时满足 Ruff `B905` 对显式 `strict` 参数的要求。未修改错误类型、错误信息、锚点数量合同或其他物理字段逻辑。

源文件 SHA-256：

- 修改前：`7fe2aee8c64ef1b357559274a0c7f5bdf1b8914fc0081ea63ce269233b9c3a9c`
- 修改后：`1e61a21982639c19804697b6be7d64242ffbb71a95f51ce2a896eacf17a01ee8`

## 本地验证

### 通过项

无缓存语法树解析通过：

```bash
.venv/bin/python -B -c 'import ast, pathlib; path=pathlib.Path("src/flow_probe/shared_b0_physics_sidecar.py"); ast.parse(path.read_text(encoding="utf-8"), filename=str(path)); print("AST_OK")'
```

结果：项目虚拟环境为 Python 3.10.20，命令退出码 `0`，输出 `AST_OK`。

相邻配对最小验证通过：

```bash
.venv/bin/python -B -c 'anchor_times=[0.0,0.1,0.2,0.3,0.4]; pairs=list(zip(anchor_times, anchor_times[1:], strict=False)); assert pairs==[(0.0,0.1),(0.1,0.2),(0.2,0.3),(0.3,0.4)]; print("ADJACENT_PAIR_OK", len(pairs))'
```

结果：退出码 `0`，产生 4 个相邻对。

聚焦语法、名称解析和 `zip` 严格性参数的静态检查通过：

```bash
.venv/bin/ruff check --no-cache --select E9,F,B905 src/flow_probe/shared_b0_physics_sidecar.py
```

结果：退出码 `0`，输出 `All checks passed!`。

目标模式核对通过：两处相邻锚点比较均为 `strict=False`，其余两处等长序列比较仍为 `strict=True`。

### 未通过但不属于本轮缺陷的检查

首次通过 `uv run` 启动 Ruff 时，沙箱拒绝写入用户级 `uv` 缓存，Ruff 未实际启动：

```text
Failed to initialize cache at /Users/bilibili/.cache/uv
Operation not permitted
```

随后改用项目已有 `.venv/bin/ruff` 和 `--no-cache` 完成聚焦静态检查。

完整 Ruff 检查报告两个既有问题：第 569 行 `UP012` 和第 702 行 `SIM102`。两处均不在本次两行差异中，不影响语法或本次相邻配对修复；按禁止格式化和最小变更边界未处理。

项目目录中的默认 `/usr/bin/python3` 为 Python 3.9.6，不满足 `pyproject.toml` 声明的 Python `>=3.10,<3.13`，因此它对 `zip(strict=...)` 报 `TypeError`。随后改用项目虚拟环境 Python 3.10.20 完成最小验证；服务器项目环境为 Python 3.10。

### 明确未执行

- 未在本机运行 `pytest`。
- 未运行 Black 或其他格式化命令。
- 未修改测试来绕过失败。
- 未执行服务器、网络、同步或 GPU 操作。

## 服务器待重跑命令

由主代理完成本轮源码的受管同步并独立处理范围外配置状态后，在服务器执行：

```bash
cd /root/autodl-tmp/thesis/experiments/llm_probe
uv run --no-sync pytest -q tests/test_shared_b0_physics_sidecar.py
```

验收要求：命令退出码为 `0`；与相邻锚点严格 `zip` 相关的 17 个失败全部消失。完整测试文件能否全部通过还取决于本任务范围外的配置状态。

## 遗留风险

- 服务器目标测试尚未重跑，因此本报告不声明行为测试已经通过。
- 目标源文件和对应测试当前均为工作区未跟踪文件；本任务没有暂存、提交或覆盖它们的其他既有内容。
