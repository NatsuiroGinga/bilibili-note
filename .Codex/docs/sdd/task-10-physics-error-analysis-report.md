# 任务十：物理误差与样本分布诊断实现报告

## 实现范围

本任务按 2026-07-21 用户加速授权直接实现，未进入测试驱动开发流程，未新增测试文件，未启动训练或正式诊断运行。

已实现独立只读诊断入口，严格顺序加载 M1 与 M2，释放前一个检查点后才加载下一个检查点。推理使用 `torch.inference_mode()`，模型和状态头全部设置为不可训练，运行摘要固定记录 `optimizer_updates=0`。

## 修改文件

- `thesis/experiments/llm_probe/src/flow_probe/physics_error_analysis.py`
  - 新增 `decompose_queue_balance(...)`，输出四窗口的 `storage`、`received`、`dequeued`、`dropped_before`、`dropped_after` 与合成 `residual`。
  - 新增 `classify_physics_regime(...)`，标记场景、攻击状态、容量变化、接收负载活动度、目标队列活动度和联合工况编号。
  - 新增 `summarize_rows(...)`，分别按模型、场景、接收负载活动度、目标队列活动度、容量变化、攻击状态和联合工况汇总。
  - 逐样本保存五锚点预测、五锚点平方误差、四窗口残差、四窗口残差平方误差和五个守恒组成项。
  - 在模型加载前复算数据 SHA-256、记录数、样本唯一性、样本顺序 SHA-256、M1/M2 训练输入哈希和真值零残差。
  - 状态头通过 `strict=True` 加载，M1/M2 的验证集哈希、训练完成状态和变体标识不一致时立即终止。
  - 生成 `config_snapshot.yaml`、`environment.json`、`input_sha256.json`、`sample_metrics.jsonl`、`group_summary.json`、`comparison.json`、`console.log`、`artifact_manifest.json` 和 `swanlog/`。
  - SwanLab 固定使用 `mortiswang/malicious-traffic-llm` 在线模式，记录两个模型总体指标和 M2 减 M1 的配对比较。
- `thesis/experiments/llm_probe/scripts/run_physics_error_analysis.sh`
  - 固定任务九 M1/M2、Qwen3-1.7B 绝对路径、807 条验证集和正式输出目录。
  - 使用 `uv run --no-sync`，不执行环境同步，不覆盖既有输出。
- `thesis/experiments/llm_probe/pyproject.toml`
  - 新增 `flow-probe-analyze-physics-errors = "flow_probe.physics_error_analysis:main"`。

未修改 `output/第一创新点实验总控.md`，未修改 M1/M2 运行制品，未新增稀疏监督、新残差或训练策略。

## 本地文件哈希

| 文件                                       | SHA-256                                                            |
| ------------------------------------------ | ------------------------------------------------------------------ |
| `src/flow_probe/physics_error_analysis.py` | `022f5c24de37e1bae9711f7ac633a76ca6ca67d4ceb8f24e7eec46ba292e0eab` |
| `scripts/run_physics_error_analysis.sh`    | `e650974fb29085a755943ae497d6818b0bdd8ee49ce6ebc9ee0ae6630a2990e5` |
| `pyproject.toml`                           | `e83fabdd6b388625d9ceb5b1a029dd689d7f4cec45d449879f477c0b65717491` |

## 后置验证

已通过：

```bash
UV_CACHE_DIR=/tmp/flow-probe-uv-cache uv run --no-sync black src/flow_probe/physics_error_analysis.py
UV_CACHE_DIR=/tmp/flow-probe-uv-cache uv run --no-sync ruff check src/flow_probe/physics_error_analysis.py
UV_CACHE_DIR=/tmp/flow-probe-uv-cache uv run --no-sync python -m py_compile src/flow_probe/physics_error_analysis.py
bash -n scripts/run_physics_error_analysis.sh
git diff --check -- thesis/experiments/llm_probe/src/flow_probe/physics_error_analysis.py thesis/experiments/llm_probe/scripts/run_physics_error_analysis.sh thesis/experiments/llm_probe/pyproject.toml
```

本机项目环境未安装 `torch`，因此纯函数运行时冒烟在导入阶段以 `ModuleNotFoundError: No module named 'torch'` 终止，未进入函数断言。按仓库规则，GPU 相关运行时验证应在服务器 `gpu` 环境执行。

## 建议的服务器白名单同步

从本地实验项目根目录执行，禁止加入 `--delete`：

```bash
cd /Users/bilibili/personal/note/thesis/experiments/llm_probe
source ~/.zshrc
rsync -av --relative \
  src/flow_probe/physics_error_analysis.py \
  scripts/run_physics_error_analysis.sh \
  pyproject.toml \
  "${GPU_SSH}:/root/autodl-tmp/thesis/experiments/llm_probe/"
```

同步后在服务器项目根目录仅刷新可编辑安装，不执行裸 `uv sync`：

```bash
source ~/.bashrc
cd /root/autodl-tmp/thesis/experiments/llm_probe
uv pip install --no-deps -e .
```

随后复算服务端三个文件 SHA-256，与本报告中的本地哈希逐项核对。

## 建议的最小服务器验证

先检查命令入口和纯函数模块可导入，再用 `--limit 2` 写入独立冒烟目录。冒烟仍会先核验完整验证集 807 条、两个运行输入哈希和全量真值零残差，只限制模型推理样本数。

```bash
uv run --no-sync flow-probe-analyze-physics-errors --help
uv run --no-sync flow-probe-analyze-physics-errors \
  --base-model /root/autodl-tmp/thesis/models/Qwen3-1.7B \
  --run M1=runs/physics-m012/qwen3-1.7b-seed42-m1-fullphys202-v1 \
  --run M2=runs/physics-m012/qwen3-1.7b-seed42-m2-lp0p01-fullphys202-v1 \
  --data runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2/validation.jsonl \
  --output runs/physics-error-analysis/task10-smoke-limit2-v1 \
  --tracking-mode online \
  --limit 2
```

冒烟预期 `sample_metrics.jsonl` 为 4 行，清单状态为 `finished`，M1/M2 各 2 条且样本顺序相同。正式运行不传 `--limit`，预期逐样本文件为 1614 行。

## 遗留风险

- 本地缺少 `torch`，尚未验证真实 4 位量化模型、LoRA 适配器与 `state_head.pt` 的联合加载。
- 尚未同步服务器，未执行 SwanLab 在线冒烟或正式 807 条诊断。
- 当前只有随机种子 42；输出只支持机制诊断和候选筛选，不支持统计显著性或稳定增益结论。
