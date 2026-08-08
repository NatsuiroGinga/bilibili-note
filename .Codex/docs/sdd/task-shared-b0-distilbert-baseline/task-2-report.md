# 共享 B0 DistilBERT 基线任务二执行报告

日期：2026-07-30

## 状态

任务二当前为**远程入口阻塞**。本地已完成官方权重可续传下载包装器与固定参数文件，但三次受管远程阶段均在 `guarded_rsync.apply_sync_plan` 的远端父目录准备子进程处失败。三次收据均为 `applied=false`，没有证据表明任务文件已同步、模型下载已启动或正式运行目录已创建。

按连续三次失败停止规则，本轮没有进行第四次远端重试。模型下载、服务器最小测试、16 条非最终样本冒烟和正式种子 42 运行均未执行。

## 修改文件

- 新建 `thesis/experiments/llm_probe/scripts/run_shared_b0_distilbert.sh`。
- 新建 `thesis/experiments/llm_probe/configs/shared_b0_distilbert_model_download_v1.json`。
- 新建 `.Codex/docs/sdd/task-shared-b0-distilbert-baseline/task-2-report.md`。

没有修改任务一文件：

- `thesis/experiments/llm_probe/src/flow_probe/shared_b0_distilbert_baseline.py`
- `thesis/experiments/llm_probe/configs/shared_b0_distilbert_seed42_v1.yaml`
- `thesis/experiments/llm_probe/tests/test_shared_b0_distilbert_baseline.py`

没有修改冻结数据、现有基线、`pyproject.toml`、`scripts/AGENTS.md` 或 `output/` 恢复文档。没有提交或推送 Git。

## 本地下载准备

下载包装器固定以下合同：

- 官方模型仓库：`distilbert/distilbert-base-multilingual-cased`
- 下载端点：`https://hf-mirror.com`
- 续传目录：`/root/autodl-tmp/thesis/models/distilbert-base-multilingual-cased.partial`
- 原子发布目录：`/root/autodl-tmp/thesis/models/distilbert-base-multilingual-cased`
- 下载会话：`shared-b0-distilbert-model`
- 下载日志：服务器项目根下 `runs/setup/shared-b0-distilbert-model-v1/download.log`
- 下载状态：服务器项目根下 `runs/setup/shared-b0-distilbert-model-v1/download_state.json`
- 模型清单：`/root/autodl-tmp/thesis/models/distilbert-base-multilingual-cased.manifest.json`
- 逐文件哈希：`/root/autodl-tmp/thesis/models/distilbert-base-multilingual-cased.checksums.sha256`
- 下载空间门禁：可用空间不得低于 `10,737,418,240` 字节

包装器设计为先查询官方修订哈希，再用 `hf download --revision <修订> --local-dir <续传目录>` 续传。下载完成后验证 `config.json`、`vocab.txt` 和模型权重，原子发布本地镜像，执行 CPU 分词器与二分类模型加载冒烟，并登记来源修订、总字节数、逐文件 SHA-256 清单和清单 SHA-256。令牌不会写入参数、日志、状态或清单。

最终本地文件哈希：

| 文件 | SHA-256 |
| --- | --- |
| `scripts/run_shared_b0_distilbert.sh` | `f8336ee989189a4b47b51b460680af0f30de6f0194b18bf3583d8935afc4a0a5` |
| `configs/shared_b0_distilbert_model_download_v1.json` | `5f47d2003b391b83a4b839105714698bde12ba79e300da9a2c7be5a7fd36c832` |

## 远程启动尝试

三次尝试使用相同白名单计划，均调用：

```bash
python3 scripts/guarded_remote_stage.py \
  --script scripts/run_shared_b0_distilbert.sh \
  --params configs/shared_b0_distilbert_model_download_v1.json \
  --log runs/setup/shared-b0-distilbert-model-v1/launch.log \
  --state runs/setup/shared-b0-distilbert-model-v1/launch_state.json \
  --capabilities runs/setup/shared-b0-distilbert-model-v1/capabilities.json \
  --receipt <本次唯一收据路径> \
  --apply
```

失败证据：

| 尝试 | 本地收据 | 时间 | 变化变量 | 结果 |
| --- | --- | --- | --- | --- |
| 1 | `thesis/experiments/llm_probe/runs/hook-receipts/shared-b0-distilbert-model-launch-v1.json` | `2026-07-30T08:37:31.793942+00:00` | 默认受管环境 | `远端目标父目录创建或验证失败。` |
| 2 | `thesis/experiments/llm_probe/runs/hook-receipts/shared-b0-distilbert-model-launch-v1-retry.json` | `2026-07-30T08:38:20.667529+00:00` | 命令前显式加载 `~/.zshrc` | 同一错误 |
| 3 | `thesis/experiments/llm_probe/runs/hook-receipts/shared-b0-distilbert-model-launch-v1-escalated.json` | `2026-07-30T08:40:58.001460+00:00` | 沙箱外运行相同受管入口 | 同一错误 |

三份收据登记的脚本、参数及其哈希完全一致，且均为：

```json
{
  "status": "failed",
  "applied": false,
  "error": "远端目标父目录创建或验证失败。"
}
```

现有 `guarded_rsync.apply_sync_plan` 在该失败分支只上抛汇总错误，没有把准备子进程的标准输出、标准错误和退出码写入收据。Hook 同时拒绝绕过受管入口直接诊断 `/tmp/gpu-exec.exp`。因此当前只能把根因范围缩小到受管同步的准备子进程，不能在不修改受管基础设施的条件下进一步区分远端登录、命令执行或路径验证失败。

## 验证记录

已通过：

- `bash -n scripts/run_shared_b0_distilbert.sh`，退出码 `0`。
- `jq -e . configs/shared_b0_distilbert_model_download_v1.json`，退出码 `0`。
- `prettier --write configs/shared_b0_distilbert_model_download_v1.json`，文件无需改写。
- `shasum -a 256 scripts/run_shared_b0_distilbert.sh configs/shared_b0_distilbert_model_download_v1.json`，结果与上表一致。

未执行：

- 任务一测试文件的服务器 `pytest`。
- CPU 分词器与模型加载冒烟。
- 16 条非最终样本冒烟。
- 损失有限性、概率范围和预测增量落盘核验。
- 恢复状态行为核验。
- SwanLab 在线数据点与云端图表核验。
- 正式种子 42 训练和评价。

## 模型、运行与 SwanLab 状态

- 本轮模型下载已启动：**否**。
- 本轮新增下载字节：`0`。
- 官方来源修订：尚未查询成功。
- 本地模型总大小与 SHA-256：尚未生成。
- 下载 `screen`：未创建。
- 下载日志：未创建远端可核验日志。
- 正式运行目录：计划为 `runs/baselines/shared-b0-distilbert-seed42-theory-selection-review-pending-v1/`，尚未创建或启动。
- 正式运行 `screen`：无。
- SwanLab 项目：计划为 `mortiswang/malicious-traffic-llm`，本轮无运行号、无数据点。
- 审查状态：继续保持 `theory_selection/review_pending`，没有结果可晋级。

## 阻塞项与解锁动作

唯一阻塞项是受管白名单同步无法完成远端目标父目录准备，而且现有失败收据缺少底层子进程诊断信息。

解锁需要先由负责远程 Hook/受管入口的任务完成以下任一项：

1. 修复当前远端准备子进程失败，并证明同一 `guarded_remote_stage.py` 计划能够完成四个白名单文件的同步与 SHA-256 核验。
2. 为 `guarded_rsync.apply_sync_plan` 的准备失败收据补充脱敏后的退出码、标准输出和标准错误，以便形成新的单一可证伪假设。

解锁后应从模型下载启动继续，不应改动或重构任务一生产代码。只有模型清单和 CPU 加载冒烟通过后，才同步任务一三个文件、运行服务器最小测试、执行 16 条非最终样本冒烟，并在全部门禁通过后创建唯一正式运行目录和 `screen` 会话。
