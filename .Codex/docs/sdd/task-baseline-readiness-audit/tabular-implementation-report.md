# 冻结协议树模型基线实施报告

## 结论

- 冻结协议只读加载器与统一 HGB/XGBoost 入口已经实现，并通过服务器隔离夹具的最终验收。
- **代码、依赖、运行配置和评价协议门禁已通过。**
- **候选数据门禁未通过。** 截至 2026-07-24，只读核验确认服务器
  `runs/data-frozen/dataset-candidate-c-v0/protocol/protocol.yaml` 不存在，因此不得启动首批候选基线。
- 未创建伪造 `dataset-v1`，未读取下载目录中的半成品，未启动任何正式基线，也没有本任务对应的 SwanLab 运行。

## 修改文件

| 文件 | 变更 |
|---|---|
| `src/flow_probe/frozen_protocol.py` | 新增冻结/候选协议只读加载、哈希校验、字段预算校验、划分校验和只读数值视图 |
| `src/flow_probe/tabular_baselines.py` | 新增统一 HGB/XGBoost 入口、阶段门禁、验证调参预算、CPU 能力探测、统一评价与制品输出 |
| `tests/frozen_protocol_fixture.py` | 新增与真实下载目录隔离的最小协议夹具 |
| `tests/test_frozen_protocol.py` | 新增协议版本、哈希、样本唯一性、成员关系、字段预算和顺序测试 |
| `tests/test_tabular_baselines.py` | 新增统一输入、CPU-only、候选阶段、测试清单拒绝、调参上限、XGBoost 依赖和概率归一化测试 |
| `pyproject.toml` | 本任务新增 `xgboost>=3.0,<4` 与 `flow-probe-tabular-baselines` 命令入口；保留其他代理已有改动 |
| `uv.lock` | 更新锁文件以纳入 XGBoost 及其平台依赖；保留其他代理已有改动 |

未修改数据下载目录、模型权重目录、历史基线制品和既有训练实现。

## 协议门禁

加载器以 `protocol.yaml` 为唯一入口。目录存在但缺少该文件时立即拒绝，不会退回读取旧 GeNIS prepared 根或其他散落文件。

加载时验证以下条件：

1. `protocol.yaml`、`field-roles.yaml`、`samples.parquet` 和全部 `splits/*.jsonl` 的协议版本一致。
2. `protocol.yaml` 中登记的基础制品与划分清单集合必须和磁盘文件集合完全一致。
3. 所有登记的 SHA-256 必须和实际文件一致，清单必须绑定当前 `samples.parquet` 的 SHA-256。
4. `samples.parquet.sample_id` 全局唯一且非空；清单内样本唯一并且都属于主表。
5. 同一 `suite_id` 的样本不得跨划分重复。
6. Parquet 每一列必须在字段角色文件中恰好分类；树视图只能包含数值型 `model_input`，不得越过字段预算读取标签、物理目标、划分元数据或审计字段。
7. 数值矩阵、标签和样本编号严格保持清单顺序，返回数组设为只读。

阶段契约固定为：

| 运行阶段 | 协议版本 | 状态 | 协议阶段 | 允许的评估划分 |
|---|---|---|---|---|
| `theory_selection` | `data-protocol-v1.0-rc1` | `provisional` | `theory_selection` | 仅 `validation` |
| `final_tuning` | `data-protocol-v1.0` | `frozen` | `final_tuning` | 仅 `validation` |

命令行提供显式 `--expected-protocol-version`，默认值为正式版本 `data-protocol-v1.0`。候选阶段必须显式传入 RC1；阶段与版本不匹配时在读取数据前拒绝。

每个基线保留一个公开默认配置，`--tuning-trial-index=0` 表示公开默认配置，`1..10` 表示最多 10 次验证集调参试次；其他编号拒绝。调参与路线选择入口拒绝任何 `split_id=test` 清单。

## 模型与评价

- HGB 与 XGBoost 使用同一 `tree_flat_view`、同一列顺序、同一样本顺序、同一标签编码、同一训练清单派生的平衡样本权重和同一评价函数。
- 标签编码和样本权重仅由训练清单派生，不读取验证标签分布生成拟合项。
- HGB 使用公开固定默认：学习率 `0.1`、100 轮、31 个叶节点、关闭早停。
- XGBoost 使用公开固定默认：`hist`、学习率 `0.1`、100 棵树、深度 6、单线程，并显式固定 `device=cpu`。
- XGBoost 仅在被选择时延迟导入；导入失败时给出先 dry-run、后锁定同步的明确命令，不静默退回其他模型。
- 统一评价输出宏 F1、平衡准确率、已知类对数损失、期望校准误差、良性误报率、未知真值召回、逐类指标和混淆矩阵。
- XGBoost 原生 `float32` 概率在统一评价前按行归一化到 `float64`，避免精度提升后因容差收紧产生虚假概率和警告；落盘概率行和有 `1e-12` 绝对误差回归门禁。

## CPU 与服务器能力

代码不调用或假定存在 `nvidia-smi`。能力探测通过标准库和可选 `torch.cuda` 完成，探测失败不会阻止 CPU 运行。

服务器实测记录：

| 项目 | 结果 |
|---|---|
| 选择的模型设备 | `cpu` |
| CPU 架构 | `x86_64` |
| 逻辑线程 | 208 |
| 执行线程上限 | 1 |
| 系统内存 | 810,158,202,880 字节 |
| 可选 CUDA | 可见 1 张 NVIDIA GeForce RTX 5090，33,668,988,928 字节 |
| 磁盘 | `/root/autodl-tmp` 可用 21G |

GPU 仅作为能力元数据记录，不改变数据、随机种子、评价协议或模型设备。运行设备、CPU/GPU 型号、线程和内存同时写入配置、摘要、成本、环境与 SwanLab 元数据。

## 运行制品

正式入口拒绝复用已存在的输出目录。每次运行计划写入：

- `config_snapshot.json`
- `environment.json`
- `console.log`
- `predictions.jsonl.gz`
- `summary.json`
- `cost.json`
- `swanlab_metrics.json`
- `swanlab_metadata.json`
- `artifact_manifest.json`
- `swanlog/tabular-baselines/`

SwanLab 固定为在线模式，工作区 `mortiswang`、项目 `malicious-traffic-llm`、阶段 `tabular-baselines`。当前没有新运行编号或运行链接。

## 依赖处理

先执行 `uv sync --locked --extra gpu --dry-run`，确认没有移除既有训练依赖，再执行唯一一次 `uv sync --locked --extra gpu`。命令返回等待窗口后，远端进程仍在下载 XGBoost/NCCL，因此只按进程条件轮询，未重复启动、未中断；最终自然结束。

服务器最终状态：

- `uv pip check`：112 个包全部兼容。
- `xgboost==3.2.0` 可导入。
- `accelerate==1.14.0`
- `peft==0.19.1`
- `swanlab==0.9.0`
- `torch==2.13.0`
- `transformers==4.57.6`
- `trl==0.29.1`

全程没有执行裸 `uv sync`。

## 验证记录

### 本地静态门禁

通过：

```bash
.venv/bin/black --check src/flow_probe/frozen_protocol.py src/flow_probe/tabular_baselines.py tests/frozen_protocol_fixture.py tests/test_frozen_protocol.py tests/test_tabular_baselines.py
.venv/bin/ruff check src/flow_probe/frozen_protocol.py src/flow_probe/tabular_baselines.py tests/frozen_protocol_fixture.py tests/test_frozen_protocol.py tests/test_tabular_baselines.py
PYTHONPYCACHEPREFIX=/tmp/llm-probe-pycache .venv/bin/python -m py_compile src/flow_probe/frozen_protocol.py src/flow_probe/tabular_baselines.py tests/frozen_protocol_fixture.py tests/test_frozen_protocol.py tests/test_tabular_baselines.py
UV_CACHE_DIR=/tmp/llm-probe-uv-cache uv lock --check
git diff --check -- thesis/experiments/llm_probe/src/flow_probe/frozen_protocol.py thesis/experiments/llm_probe/src/flow_probe/tabular_baselines.py thesis/experiments/llm_probe/tests/frozen_protocol_fixture.py thesis/experiments/llm_probe/tests/test_frozen_protocol.py thesis/experiments/llm_probe/tests/test_tabular_baselines.py thesis/experiments/llm_probe/pyproject.toml thesis/experiments/llm_probe/uv.lock
```

过程中的非代码失败及处理：

- 系统 Python 的默认字节码缓存目录受沙箱限制；改用项目 `.venv` 并把缓存定向到 `/tmp` 后通过。
- 首次 `uv lock --check` 因默认 `~/.cache/uv` 受沙箱限制失败；设置任务专用 `/tmp` 缓存后通过。
- 首次 Ruff 检查发现 7 项未使用导入、行宽、导入顺序和简化问题；逐项最小修正后最终零问题。

未在本地运行 pytest，也未接触真实下载目录。

### 白名单同步

首次只同步 7 个任务文件；概率归一化修复后只再次同步以下 2 个文件：

```text
src/flow_probe/tabular_baselines.py
tests/test_tabular_baselines.py
```

最终本地/服务器 SHA-256 一致：

```text
02ec1275961702dfbe2a82fba51e773a0c8b580e522001919d47565a6cf7b743  src/flow_probe/tabular_baselines.py
8c277b64780904147f128b5cb91aca95e9baf261672dd93d493b45cebbabc0b9  tests/test_tabular_baselines.py
```

### 服务器精确测试

初次测试为 11 项通过，但出现一条 XGBoost 概率行和警告。将警告提升为错误后，堆栈确认根因为 `float32` 概率被提升为 `float64` 后容差变严，而不是数据或模型异常。完成按行归一化与回归断言后，最终命令为：

```bash
uv run --no-sync pytest -q tests/test_frozen_protocol.py tests/test_tabular_baselines.py -W error::UserWarning
```

最终结果：`11 passed in 2.85s`，零警告。

命令行帮助已确认暴露 `--stage`、`--expected-protocol-version` 和 `--tuning-trial-index`。

## 候选协议现状

服务器只读核验结果：

```text
runs/data-frozen/dataset-candidate-c-v0/protocol/protocol.yaml: 不存在
相关统一树模型基线进程: 无
screen 会话: 无
```

服务器存在 `runs/traditional-baselines/` 和 `runs/multiclass-baselines/` 下的 2026-07-19 历史制品，但它们不使用本次冻结协议入口，不是本任务的新基线结果。

## 待协议就绪后的三随机种子命令

以下命令仅记录，**本任务未执行**。运行前必须先用加载器确认候选根满足 RC1、`provisional`、`theory_selection`、哈希和字段预算全部门禁。

### GeNIS 家族开发套件

计划输出：
`runs/baselines/theory-selection/genis-family-development/public-default-seed{42,43,44}/`

```bash
cd /root/autodl-tmp/thesis/experiments/llm_probe
mkdir -p runs/baselines/theory-selection/genis-family-development
screen -L \
  -Logfile runs/baselines/theory-selection/genis-family-development/launcher.log \
  -dmS tabular-genis-theory bash -lc '
source ~/.bashrc >/dev/null 2>&1
cd /root/autodl-tmp/thesis/experiments/llm_probe
for seed in 42 43 44; do
  uv run --no-sync flow-probe-tabular-baselines \
    --protocol-dir runs/data-frozen/dataset-candidate-c-v0/protocol \
    --stage theory_selection \
    --expected-protocol-version data-protocol-v1.0-rc1 \
    --tuning-trial-index 0 \
    --train-manifest splits/genis-family-development-train.jsonl \
    --evaluation validation=splits/genis-family-development-validation.jsonl \
    --label-field family_label \
    --model hgb \
    --model xgboost \
    --output-dir runs/baselines/theory-selection/genis-family-development/public-default-seed${seed} \
    --seed ${seed} \
    --run-name theory-selection-genis-family-public-default-seed${seed}
done
'
```

### C/HTTP+AES 二分类开发套件

计划输出：
`runs/baselines/theory-selection/tqhc2-c-development/public-default-seed{42,43,44}/`

```bash
cd /root/autodl-tmp/thesis/experiments/llm_probe
mkdir -p runs/baselines/theory-selection/tqhc2-c-development
screen -L \
  -Logfile runs/baselines/theory-selection/tqhc2-c-development/launcher.log \
  -dmS tabular-tqhc2-c-theory bash -lc '
source ~/.bashrc >/dev/null 2>&1
cd /root/autodl-tmp/thesis/experiments/llm_probe
for seed in 42 43 44; do
  uv run --no-sync flow-probe-tabular-baselines \
    --protocol-dir runs/data-frozen/dataset-candidate-c-v0/protocol \
    --stage theory_selection \
    --expected-protocol-version data-protocol-v1.0-rc1 \
    --tuning-trial-index 0 \
    --train-manifest splits/tqhc2-c-development-train.jsonl \
    --evaluation validation=splits/tqhc2-c-development-validation.jsonl \
    --label-field binary_label \
    --model hgb \
    --model xgboost \
    --output-dir runs/baselines/theory-selection/tqhc2-c-development/public-default-seed${seed} \
    --seed ${seed} \
    --run-name theory-selection-tqhc2-c-public-default-seed${seed}
done
'
```

## 启动裁决

- **可以启动首批基线：否。** 原因仅为候选协议尚未发布，缺少 `protocol.yaml`，数据门禁无法通过。
- **代码侧是否仍有阻塞：否。** 加载、模型、CPU 运行、依赖、评价、输出和服务器精确测试均已通过。
- **完整基线矩阵是否就绪：否。** `final_tuning` 必须等待三源完整 `dataset-v1` 的正式 `data-protocol-v1.0/frozen/final_tuning` 协议，当前候选协议即使发布也只能用于理论路线选择。
