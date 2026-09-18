# DRIFT-DGA 2026 零训练数据探针计划

## 任务边界

- 目标数据集：`snsec-net/dga-detection-drift26dsn`。
- 目标：在不训练模型、不下载全量数据的条件下，核验公开可访问性、版本、模式与跨年统计的可计算性。
- 不做：模型实现、全量下载、论文正文、路线总控或恢复卡修改。

## 执行步骤

1. 状态：完成。Dataset Viewer 的有效性、配置、切分、模式、总量和 Parquet 分片均可只读访问。
2. 状态：完成。Hugging Face CLI 核验了公开、非门控状态、固定 revision、原始文件树与仓库总存储量。
3. 状态：完成。仅读取三个公开最小行预览，确认 `raw` 的 `domain`、`family`、`label`，以及 `eSLD` 的 `domain`、`label`；未从小样外推总体统计。
4. 状态：完成。已逐项登记字段合同、最小读取范围、流式算法、成本与 Viewer 聚合能力边界。
5. 状态：完成。已写入报告，待执行最终 Markdown、路径与敏感信息检查。

## 验收命令

- `rg --files .Codex/docs/2026-09-07-DRIFT零训练数据探针`
- `rg -n 'hf_[A-Za-z0-9]{8,}|Bearer[[:space:]]+[A-Za-z0-9]' .Codex/docs/2026-09-07-DRIFT零训练数据探针`
- `git diff --check -- .Codex/docs/2026-09-07-DRIFT零训练数据探针`

## 制品与阻塞

- 计划：本文件。
- 发现：`notes.md`。
- 交付：`可行性报告.md`。
- 已知阻塞：Viewer 不提供字符 n-gram、后缀集合、跨年域名交集或家族集合的服务端聚合；这些精确总体统计必须流式扫描相应公开 Parquet 分片。
