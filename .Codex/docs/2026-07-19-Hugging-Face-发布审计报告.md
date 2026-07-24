# Hugging Face 发布审计报告

## 结论

**本轮没有执行上传。**服务器令牌存在，但 Hugging Face 网络连接超时，且无法通过官方接口确认用户名或组织归属。当前已经完成制品、哈希、许可、仓库结构和卡片草案，待网络恢复、归属确认和软件许可证确定后，可以从独立暂存目录执行上传。

推荐先发布两个**私有研究预览模型仓库**：

1. `<归属>/qwen3-1.7b-genis-10s-qlora-preview`
2. `<归属>/qwen3-1.7b-hikari-2021-qlora-preview`

数据处理制品建议放入单独的**私有复现仓库**：

`<归属>/malicious-traffic-llm-reproducibility`

在 H1 多随机种子、防泄漏正式划分和跨数据验证完成前，不建议把任何仓库改为公开，也不应把现有满分写成正式方法结论。

## 审计范围

- 本地输入：`thesis/experiments/llm_probe/` 下的代码、配置、运行摘要、清单和聚合指标。
- 服务端输入：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/` 下四个已完成历史运行的 `final_adapter/`。
- 第三方数据：GeNIS 1.0.0、HIKARI-2021 1.4.0、DEDALE 2.0。
- 未修改：主实验代码、`output/开题改进交接文档.md`、现有运行目录和服务器数据目录。

## 可发布制品裁决

| 对象                         | 结论         | 理由                                                                       |
| ---------------------------- | ------------ | -------------------------------------------------------------------------- |
| GeNIS QLoRA 适配器           | 首选私有预览 | 权重完整，34,917,504 字节；仅有单种子、200 条训练样本和 100 条平衡测试样本 |
| HIKARI 标准跟踪 QLoRA 适配器 | 次选私有预览 | 权重完整；测试宏平均 F1 为 0.9800，但 HIKARI 分组证据较弱                  |
| HIKARI 早期烟雾适配器        | 不发布       | 测试宏平均 F1 为 0.3333，误报率为 1.0                                      |
| HIKARI 早期未标准跟踪适配器  | 不优先       | 与标准跟踪版本结果相同，但制品链较弱                                       |
| 处理代码                     | 条件发布     | 敏感信息扫描未命中，但项目尚无软件许可证                                   |
| 聚合清单与哈希               | 条件发布     | 不含地址、端口和原始 FlowID；需清理绝对路径并按 CC BY 4.0 署名             |
| 原始或逐行数据               | 默认不发布   | 即使许可允许，也没有必要复制官方归档；逐行派生数据增加隐私、维护和版本风险 |
| Qwen 基座权重                | 禁止发布     | 必须从 `Qwen/Qwen3-1.7B` 获取，不得复制到适配器仓库                        |

完整文件大小和 SHA-256 见 `.Codex/docs/2026-07-19-Hugging-Face-发布审计笔记.md`。

## 许可核验

| 数据或模型        | 官方许可                                                                                                | 再分发判断                                   | 本项目动作                                               |
| ----------------- | ------------------------------------------------------------------------------------------------------- | -------------------------------------------- | -------------------------------------------------------- |
| GeNIS 1.0.0       | [CC BY 4.0](https://zenodo.org/records/14919237)                                                        | 允许再分发和改编，要求署名                   | 不镜像原始数据，只发布处理说明、清单和哈希               |
| HIKARI-2021 1.4.0 | [CC BY 4.0](https://zenodo.org/records/6463389)                                                         | 允许再分发和改编，要求署名                   | 不镜像原始数据，只发布处理说明和哈希                     |
| DEDALE 2.0        | [CC BY 4.0](https://entrepot.recherche.data.gouv.fr/dataset.xhtml?persistentId=doi%3A10.57745%2FY5JLDG) | 数据页允许再发布与镜像，并要求引用和原页链接 | 只记录完整 CICFlowMeter 归档哈希；部分 Zeek 归档禁止上传 |
| Qwen3-1.7B        | [Apache 2.0](https://huggingface.co/Qwen/Qwen3-1.7B)                                                    | 可作为适配器基础模型                         | 模型卡署名并链接基座，只上传项目适配器                   |
| 项目处理代码      | 当前未许可                                                                                              | 公开发布后他人没有明确复用授权               | 权利人选择许可证后再公开，建议 Apache 2.0                |

CC BY 4.0 允许分享和制作改编材料，但发布时必须保留创作者信息、许可说明、原材料链接并标明修改。派生清单应明确写出“仅保留文件名、哈希、大小、划分计数和聚合统计；未包含原始流量”。

## 模型仓库结构

```text
qwen3-1.7b-genis-10s-qlora-preview/
├── README.md
├── adapter_config.json
├── adapter_model.safetensors
└── artifacts/
    ├── source_checksums.json
    ├── training_config.redacted.yaml
    ├── training_summary.redacted.json
    └── evaluation_summary.redacted.json
```

发布前处理：

1. 从历史运行复制到独立暂存目录，不原地修改运行目录。
2. 把 `adapter_config.json` 的 `base_model_name_or_path` 改为 `Qwen/Qwen3-1.7B`。
3. 把配置和摘要中的服务器绝对路径改为公开模型标识或仓库相对路径。
4. 不复制分词器、`training_args.bin`、检查点、优化器状态和日志。
5. 对最终暂存目录重新计算逐文件大小和 SHA-256，再创建仓库。

HIKARI 仓库采用相同结构，但必须使用 `tracked-pilot-qwen3-1.7b-seed42/final_adapter/`，不得误用性能失败的 `smoke-qwen3-1.7b-seed42/`。

## 数据仓库结构

```text
malicious-traffic-llm-reproducibility/
├── README.md
├── THIRD_PARTY_LICENSES.md
├── checksums/
│   ├── archives.sha256
│   └── genis-source-files.sha256
├── manifests/
│   └── genis/
│       ├── dataset_provenance.json
│       ├── sample_manifest.json
│       ├── audit.redacted.json
│       └── hybrid_forward_plan.json
└── processing/
    └── flow_probe/
        ├── adapters/
        ├── genis_audit.py
        ├── genis_forward_split.py
        ├── manifest.py
        ├── prepare.py
        ├── sampling.py
        ├── schemas.py
        ├── serialize.py
        └── split.py
```

`processing/` 只有在权利人确定软件许可证后才进入公开仓库。`audit.json` 需将服务器绝对路径缩减为文件名。`session_assignments.jsonl`、训练 JSONL、预测明细和第三方原始数据不进入仓库。

## 上传清单

### GeNIS 模型仓库

| 暂存目标                                     | 来源                                                      | 当前状态                           | 许可依据                        |
| -------------------------------------------- | --------------------------------------------------------- | ---------------------------------- | ------------------------------- |
| `adapter_model.safetensors`                  | 服务端 `genis-10s-smoke-qwen3-1.7b-seed42/final_adapter/` | 可复制；SHA-256 已记录             | 项目适配器，基础模型 Apache 2.0 |
| `adapter_config.json`                        | 同上                                                      | 必须清理基础模型绝对路径并重算哈希 | 项目适配器配置                  |
| `README.md`                                  | 模型卡草案                                                | 待填仓库归属和许可决定             | 项目文档                        |
| `artifacts/training_config.redacted.yaml`    | 本地 `training_config.yaml`                               | 必须清理路径                       | 项目配置                        |
| `artifacts/training_summary.redacted.json`   | 本地 `training_summary.json`                              | 必须清理模型路径                   | 项目摘要                        |
| `artifacts/evaluation_summary.redacted.json` | 本地评估摘要                                              | 必须清理模型路径                   | 项目摘要                        |
| `artifacts/source_checksums.json`            | 本审计记录                                                | 待从最终暂存文件生成               | 第三方数据 CC BY 4.0 署名信息   |

### 复现数据仓库

| 暂存目标                                   | 来源                       | 当前状态                     | 许可依据                 |
| ------------------------------------------ | -------------------------- | ---------------------------- | ------------------------ |
| `README.md`                                | 数据卡草案                 | 可准备                       | 项目文档                 |
| `THIRD_PARTY_LICENSES.md`                  | 本审计许可矩阵             | 可准备                       | 三个数据集 CC BY 4.0     |
| `checksums/archives.sha256`                | 本审计三个完整归档 SHA-256 | 可准备                       | 事实性哈希与署名说明     |
| `manifests/genis/dataset_provenance.json`  | 本地运行归档               | 可准备                       | GeNIS CC BY 4.0 派生清单 |
| `manifests/genis/sample_manifest.json`     | 本地运行归档               | 需把路径统一为说明性相对路径 | GeNIS CC BY 4.0 派生清单 |
| `manifests/genis/audit.redacted.json`      | 本地 `audit.json`          | 必须删除绝对路径             | GeNIS CC BY 4.0 派生统计 |
| `manifests/genis/hybrid_forward_plan.json` | 本地 `plan_summary.json`   | 可准备                       | GeNIS CC BY 4.0 派生统计 |
| `processing/flow_probe/`                   | 本地处理代码               | 待软件许可证决定             | 项目代码                 |

## 阻塞项

1. **网络阻塞**：服务器到 Hugging Face 连接超时，无法查询身份、创建仓库或上传。
2. **归属阻塞**：`HF_TOKEN` 存在，但用户名和组织未确认；不能根据 SwanLab 工作区推断 Hugging Face 归属。
3. **许可阻塞**：项目处理代码和适配器尚未由权利人明确选择发布许可证。
4. **制品清理阻塞**：适配器配置与摘要包含服务器绝对路径，必须在独立暂存副本中清理。
5. **研究状态限制**：现有适配器只是小样本探针，公开前至少应完成当前 H1 防泄漏正式划分和多随机种子验证。

## 解锁后的最小动作

1. 服务器网络恢复后，仅执行不回显令牌的身份查询，确认用户名或组织。
2. 权利人确认适配器和代码许可证。
3. 在新的暂存目录复制 GeNIS 适配器，完成路径清理和最终哈希清单。
4. 先创建私有仓库并上传 GeNIS 预览包，下载回测 PEFT 加载与严格 JSON 输出。
5. 验收无误后再准备 HIKARI 与复现仓库，是否公开等待 H1 正式裁决。
