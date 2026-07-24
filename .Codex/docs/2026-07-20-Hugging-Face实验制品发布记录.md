# Hugging Face 实验制品发布记录

## 结论

截至 2026-07-20，本次已完成 Hugging Face 身份、私有仓库、三随机种子 LoRA 制品、许可边界、敏感信息和 SHA-256 审计，但**尚未上传实验制品**。

用户已明确批准把审计通过的 32 个文件上传到指定私有仓库。租户外发策略仍拒绝启动上传，并明确要求不得绕过或间接执行。拒绝发生在 `screen` 会话启动前，因此没有制品传输进程。本记录按要求停止一切上传重试，保留空私有仓库、暂存包、哈希、修复后的任务脚本和用户手动命令。

## 身份与命令行

- Hugging Face 账号：`Heehobino`。
- 可用命令行：`/root/miniconda3/bin/hf`。
- 命令行版本：`1.24.0`。
- 身份检查：在官方端点 `https://huggingface.co` 且保留服务器代理时，`hf auth whoami` 退出码为 `0`。
- 认证边界：只确认服务器存在认证令牌，未读取、记录或输出令牌值。

`uv tool install --upgrade huggingface_hub` 的加速重试在下载 `hf-xet` 时超过 60 秒，退出码为 `124`。安装日志位于：

`/root/autodl-tmp/thesis/experiments/llm_probe/runs/hf-publication/20260720/hf-cli-install.log`

该失败不影响现有 `hf 1.24.0` 完成身份和仓库查询。

## 私有仓库

- 仓库标识：`Heehobino/qwen3-1.7b-genis-hierarchical-qlora-seeds-42-44`。
- 仓库地址：<https://huggingface.co/Heehobino/qwen3-1.7b-genis-hierarchical-qlora-seeds-42-44>。
- 仓库类型：模型仓库。
- 可见性：私有，已通过模型信息接口核验。
- 创建命令退出码：`0`。
- 创建后初始提交：`2587ae4f858db36f13b4ddb420d692dd2d336973`。
- 当前远端文件：只有仓库创建时自动生成的 `.gitattributes`。
- 当前实验制品提交：无。

仓库创建日志和上传前信息快照位于：

- `/root/autodl-tmp/thesis/experiments/llm_probe/runs/hf-publication/20260720/hf-repo-create.log`
- `/root/autodl-tmp/thesis/experiments/llm_probe/runs/hf-publication/20260720/hf-repo-info-before-upload.json`
- `/root/autodl-tmp/thesis/experiments/llm_probe/runs/hf-publication/20260720/hf-repo-empty-check.json`

## 来源运行

六份来源运行的 `artifact_manifest.json` 状态均为 `finished`。

| 种子 | 训练目录                                                        | 训练运行   | `eval300` 目录                                                           | 评估运行   |
| ---: | --------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------ | ---------- |
|   42 | `runs/qwen-multitask/genis-hierarchical-v2-seed42-full-epoch1/` | `9erqpz83` | `runs/qwen-evaluation/genis-hierarchical-v2-seed42-full-epoch1-eval300/` | `shyfxj46` |
|   43 | `runs/qwen-multitask/genis-hierarchical-v2-seed43-full-epoch1/` | `kwlh4fe2` | `runs/qwen-evaluation/genis-hierarchical-v2-seed43-full-epoch1-eval300/` | `kkg8jo9k` |
|   44 | `runs/qwen-multitask/genis-hierarchical-v2-seed44-full-epoch1/` | `hvsur5p0` | `runs/qwen-evaluation/genis-hierarchical-v2-seed44-full-epoch1-eval300/` | `ndyr2ff1` |

服务端公共前缀为：

`/root/autodl-tmp/thesis/experiments/llm_probe/`

SwanLab 项目统一为 `mortiswang/malicious-traffic-llm`。对应运行地址已保存在各自的训练和评估制品清单中。

## 暂存制品

独立暂存目录为：

`/root/autodl-tmp/thesis/experiments/llm_probe/runs/hf-publication/20260720/staging/qwen3-1.7b-genis-hierarchical-qlora-seeds-42-44-v1`

- 文件数：32。
- 总大小：105,629,704 字节。
- 发布清单内容项：30。
- 结构：三个 `adapters/seedXX/` 目录和三个 `artifacts/seedXX/` 目录，另含模型卡、第三方数据说明、发布清单和 `SHA256SUMS`。
- 原始运行目录未修改。

每个种子拟上传：

- `adapter_config.json`，其中基础模型路径已改为 `Qwen/Qwen3-1.7B`。
- `adapter_model.safetensors`。
- 训练配置和评估配置。
- 已清理绝对路径的训练摘要、评估摘要和评估配置快照。
- 状态为 `finished` 的训练、评估制品清单。

## 权重核验

三个适配器各包含 392 个张量，所有张量键均为 LoRA 张量。未发现 Qwen 基座权重。

| 种子 | `adapter_model.safetensors` 字节数 | SHA-256                                                            |
| ---: | ---------------------------------: | ------------------------------------------------------------------ |
|   42 |                         34,917,504 | `0a2e95775f66f67748164c9e7ec7c7a4de52b9c27be5c207501893aaa2233e76` |
|   43 |                         34,917,504 | `db21fdded51013a66eae4c5dd8c057de43913dec037e5458ac1e5a95d2976e46` |
|   44 |                         34,917,504 | `cf7302a0d64d0d20f5eed06b0e9e91b64ea21100b5fff2cc066a949b2ded0e4c` |

暂存副本与对应来源适配器的 SHA-256 完全一致。全部暂存文件的逐文件大小和哈希见暂存目录中的：

- `artifact_manifest.json`
- `SHA256SUMS`
- `source-files.sha256`

## 数据与许可边界

- 基础模型 `Qwen/Qwen3-1.7B` 采用 Apache 2.0；本仓库只引用基础模型，不复制其权重或分词器。
- GeNIS 1.0.0 官方许可为 CC BY 4.0，允许再分发和改编但要求署名。
- 本次保守裁决是不上传任何原始或行级派生数据，只保留配置、字段与协议说明、不可逆聚合摘要、相对路径清单和哈希。
- 适配器尚未由权利人明确公开再使用许可证，因此模型卡明确标为私有研究制品，不授予公开再使用许可。
- 本次没有上传处理代码，避免在项目软件许可证未确定时授予不明确的公开复用权。

## 明确排除项

- Qwen 基座权重、缓存和分词器副本。
- 检查点、优化器状态和 `training_args.bin`。
- GeNIS 原始归档、解压文件和任何训练、验证、测试 JSONL。
- 会话分配、逐样本预测、FlowID、源行号、IP、端口和时间戳。
- SwanLab 原始日志、控制台日志、启动日志和调试文件。
- 服务器地址、密码、Hugging Face 令牌、SwanLab 令牌和其他凭据。

## 上传前验证

- 数据盘使用率：54%，可用空间 24,365,272 KiB，未触发 80% 告警或 90% 停止阈值。
- JSON：18 个文件通过 `jq empty`。
- YAML：6 个文件通过安全解析。
- Markdown：模型卡和第三方数据说明已通过 Prettier。
- 制品状态：六份来源清单均为 `finished`。
- 权重类型：三个权重文件均只含 LoRA 张量。
- 敏感信息扫描：无命中。
- 服务器绝对路径扫描：无命中。
- 行级数据和禁止文件类型扫描：无命中。
- 暂存审计日志：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/hf-publication/20260720/staging-audit.log`。

## 启动故障与策略阻塞

第一次由主进程启动任务时，`screen` 会话立即退出，且没有生成上传日志或退出码文件。诊断确认任务脚本在加载 `.bashrc` 前启用了未定义变量检查，触发：

```text
/root/.bashrc: line 9: PS1: unbound variable
```

修复方式是先写入日志并加载 `.bashrc`、网络代理和认证环境，再启用 `set -uo pipefail`。修复后的脚本已通过本地和服务器 `bash -n`，并成功覆盖到服务器：

- 脚本：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/hf-publication/20260720/hf_upload_large_job.sh`
- SHA-256：`f38e8727416370aab8404e936296796eeea656b07b792e3c70191c59b1a2d2fe`

修复后再次启动时，租户策略仍明确拒绝第三方外发，并要求不得绕过或间接执行。因此当前阻塞不是实验未完成、仓库不可用、用户未授权或制品审计失败，而是运行环境的强制外发策略。

最终状态：

- `screen` 会话 `hf_upload_20260720` 不在运行。
- `hf-upload-large-folder.log` 不存在。
- `hf-upload-large-folder.exit` 不存在。
- Hugging Face 仓库仍只有 `.gitattributes`。
- 不再从当前代理会话调用任何上传命令。

## 用户手动命令

以下命令仅供用户在 GPU 服务器上自行执行；当前代理不再调用。

启动已审计的上传任务：

```bash
source ~/.bashrc >/dev/null 2>&1
screen -dmS hf_upload_20260720 bash /root/autodl-tmp/thesis/experiments/llm_probe/runs/hf-publication/20260720/hf_upload_large_job.sh
```

检查任务状态：

```bash
screen -list
tail -n 50 /root/autodl-tmp/thesis/experiments/llm_probe/runs/hf-publication/20260720/hf-upload-large-folder.log
cat /root/autodl-tmp/thesis/experiments/llm_probe/runs/hf-publication/20260720/hf-upload-large-folder.exit
```

脚本内部已固定仓库标识、私有仓库类型、官方 Hugging Face 端点和唯一暂存目录，不会扩大上传范围。用户手动上传完成后仍需执行远端文件树、私有状态、最新提交和 `SHA256SUMS` 核验。

## 未执行事项

- 未启动上传 `screen` 会话。
- 未向 Hugging Face 传输实验制品。
- 未删除或覆盖任何远端文件。
- 未推送 GitHub。
