# 生成式恶意流量探针实验

本目录用于验证 Qwen3-1.7B 能否从统一流级表示中学习良性/恶意二分类。实验设计见 `output/2026-07-17-生成式恶意流量探针实施计划.md`。

## HIKARI 烟雾实验

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

最后依次执行短训练和严格结构化评估：

```bash
uv run flow-probe-train --config configs/smoke_qwen3_1_7b.yaml
uv run flow-probe-evaluate \
  --config configs/smoke_qwen3_1_7b.yaml \
  --adapter-path runs/smoke-qwen3-1.7b-seed42/final_adapter
```
