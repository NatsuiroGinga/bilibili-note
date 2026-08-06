# 生成式恶意流量探针实验

本目录用于验证生成式主实验基座 `Qwen/Qwen3-0.6B` 能否从统一流级表示中学习恶意流量检测任务，并保存 DistilBERT 候选筛选、`Qwen3-1.7B` 规模验证及历史实验的可复现证据。

## 历史 HIKARI 烟雾实验（Qwen3-1.7B）

先生成按通信主机对分组的完整切分：

```bash
uv run flow-probe-prepare \
  --dataset hikari \
  --input /root/autodl-tmp/thesis/datasets/HIKARI-2021/extracted/ALLFLOWMETER_HIKARI2021.csv \
  --output-dir data/processed/hikari-grouped \
  --group-basis originh-responh \
  --seed 42
```

再从已隔离的切分中无放回抽取平衡烟雾集：

```bash
uv run flow-probe-sample \
  --source-dir data/processed/hikari-grouped \
  --output-dir data/processed/smoke \
  --train-size 200 \
  --validation-size 50 \
  --test-size 100 \
  --seed 42
```

以下命令只用于复现早期 `Qwen3-1.7B` 烟雾实验，不是当前主实验入口：

```bash
uv run flow-probe-train --config configs/smoke_qwen3_1_7b.yaml
uv run flow-probe-evaluate \
  --config configs/smoke_qwen3_1_7b.yaml \
  --adapter-path runs/smoke-qwen3-1.7b-seed42/final_adapter
```

## Pyright 静态类型检查

安装开发依赖后运行默认检查：

```bash
uv sync --group dev
uv run --no-sync pyright
```

默认范围由 `pyproject.toml` 的 `[tool.pyright]` 固定，当前只覆盖 Shared B0 物理侧车和 R2 数据合同两个高风险新模块。新增或实质重构的 Python 模块应先单文件检查，清零后再加入默认范围：

```bash
uv run --no-sync pyright src/flow_probe/模块名.py
```

全仓扫描用于盘点历史类型债务，不作为实验启动门禁：

```bash
uv run --no-sync pyright src/flow_probe
```

Pyright 不能证明运行时数组长度、物理公式或实验语义正确；这些问题仍由目标测试、数据合同和制品校验负责。详细策略与首次基线见 `../../../.Codex/docs/2026-07-31-Pyright渐进启用计划.md`。

## Pyright 静态类型检查

安装开发依赖后运行默认检查：

```bash
uv sync --group dev
uv run --no-sync pyright
```

默认范围由 `pyproject.toml` 的 `[tool.pyright]` 固定，当前只覆盖 Shared B0 物理侧车和 R2 数据合同两个高风险新模块。新增或实质重构的 Python 模块应先单文件检查，清零后再加入默认范围：

```bash
uv run --no-sync pyright src/flow_probe/模块名.py
```

全仓扫描用于盘点历史类型债务，不作为实验启动门禁：

```bash
uv run --no-sync pyright src/flow_probe
```

Pyright 不能证明运行时数组长度、物理公式或实验语义正确；这些问题仍由目标测试、数据合同和制品校验负责。详细策略与首次基线见 `../../../.Codex/docs/2026-07-31-Pyright渐进启用计划.md`。
