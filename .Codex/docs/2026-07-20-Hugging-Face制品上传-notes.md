# Hugging Face 实验制品上传审计笔记

## 已确认边界

- 仓库默认设为私有。
- 只上传已完成种子的 QLoRA 适配器、配置、训练与评估摘要及制品清单。
- 排除 Qwen 基座权重。
- 第三方数据许可不明确时排除原始数据及行级派生数据。
- 上传前必须检查制品清单状态、SHA-256 和敏感信息；上传后必须核验远端文件与提交。

## 检查记录

- 服务器 Hugging Face 账号：`Heehobino`。
- 可用命令行：`/root/miniconda3/bin/hf`，版本 `1.24.0`。
- `hf auth whoami` 在 `HF_ENDPOINT=https://huggingface.co` 且保留网络代理时退出码为 `0`。
- 只确认服务器存在认证令牌，未读取或输出令牌值。
- `uv` 独立工具安装因 `hf-xet` 下载超过 60 秒而退出，退出码为 `124`；服务端日志为 `runs/hf-publication/20260720/hf-cli-install.log`。
- 已确认正式训练与 `eval300` 目录均存在：随机种子 42、43、44 各一份训练目录和一份评估目录。
- 六份 `artifact_manifest.json` 的状态均为 `finished`。
- 三个 `adapter_model.safetensors` 各有 392 个张量，所有张量键均为 LoRA，不含基座权重。
- 独立暂存目录：`runs/hf-publication/20260720/staging/qwen3-1.7b-genis-hierarchical-qlora-seeds-42-44-v1`。
- 暂存包共 32 个文件、105,629,704 字节；发布清单记录 30 个内容文件。
- 18 个 JSON 和 6 个 YAML 均可解析；敏感信息、服务器绝对路径、行级数据扫描均无命中。
- 适配器 SHA-256：种子 42 为 `0a2e95775f66f67748164c9e7ec7c7a4de52b9c27be5c207501893aaa2233e76`，种子 43 为 `db21fdded51013a66eae4c5dd8c057de43913dec037e5458ac1e5a95d2976e46`，种子 44 为 `cf7302a0d64d0d20f5eed06b0e9e91b64ea21100b5fff2cc066a949b2ded0e4c`。
- 不上传原始数据、逐行派生数据、训练 JSONL、预测、检查点、分词器、日志或 Qwen 基座权重。
- 私有仓库 `Heehobino/qwen3-1.7b-genis-hierarchical-qlora-seeds-42-44` 已创建并核验为私有，初始提交为 `2587ae4f858db36f13b4ddb420d692dd2d336973`。
- 用户已明确批准上传，但租户外发策略仍拒绝启动任务，并要求不得绕过或间接执行。
- 仓库当前只有自动生成的 `.gitattributes`，没有实验制品提交。
- 修复后的服务器任务脚本 SHA-256 为 `f38e8727416370aab8404e936296796eeea656b07b792e3c70191c59b1a2d2fe`；脚本已通过 `bash -n`，但未运行。
