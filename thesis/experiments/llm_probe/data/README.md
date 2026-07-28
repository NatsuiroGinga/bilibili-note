# 数据目录

- `raw/`：不存放在本工程中。原始数据来自 Vault 的 `raw/datasets/` 或服务器数据盘。
- `processed/`：由 `flow-probe-prepare` 生成完整分组切分，再由 `flow-probe-sample` 生成固定预算子集，默认不进入版本管理。
- 完整切分必须包含 `manifest.json`；固定预算子集必须包含 `sample_manifest.json`。
- 正式实验只能使用已完成校验的数据文件；部分下载文件不得进入预处理。
