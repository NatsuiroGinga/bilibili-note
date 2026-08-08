# 基线实验并行补齐笔记

## 审计口径

- `通过`：接口与 `data-protocol-v1.0-rc1` 一致，并已有服务器最小运行证据。
- `部分通过`：已有旧协议实现或开发集结果，但尚未适配冻结视图。
- `未通过`：必要实现、依赖、权重、配置或验证不存在。

## 初步发现

### 数据

- 文献协议 `data-protocol-v1.0-rc1` 已通过最终验收。
- 正式 `data-protocol-v1.0` 尚未物化，仍需通过 12 项 P0 门禁。
- TQH-C2 C 已解压并进入标签与包级连接审计；A 正在下载，B 排队。

### 代码

- 现有 `traditional_baselines.py` 与 `multiclass_baselines.py` 提供 HGB 开发集入口。
- 现有 `train_sft.py`、`physics_train.py` 和相关评价入口可复用，但绑定旧 JSONL 与旧清单。
- 未检索到 XGBoost、DistilBERT 或冻结 `dataset-v1` 视图加载实现。

### 编号

- 统一实验合同与外部横向对比计划对 M4 至 M7 的编号含义不一致。
- 实现阶段只使用语义键，避免文档编号变化污染代码和结果目录。

## 2026-07-24 TQH-C2 C 首批树模型

- 修复版 C-only 协议 SHA-256 为 `c779ef9ae5513262ddd1ce3a14b571d01ea5e6eff17c98d13f6a634d646030d9`，服务器精确测试 `7 passed in 1.03s`，12 个非自引用制品哈希全部通过。
- 有效运行根目录为 `runs/baselines/theory-selection/tqhc2-c-development/review-pending-c779ef9a-v2/`；HGB 与 XGBoost 的种子 42、43、44 共六个运行全部完成。
- 每个运行只评价 `validation`，包含 2,749 条预测，`test_manifest_visible=false`；六个 SwanLab 云端运行均为 `FINISHED` 且有指标点。
- 两个模型的宏平均 F1 均为 `0.9310799563`，平衡准确率均为 `0.9788940481`，良性误报率均为 `0`；这些结果只建立 C-only 验证门槛。
- XGBoost 平均拟合时间低 `36.30%`、平均推理时间低 `72.73%`，但平均常驻内存高 `14.45%`；成本来自两个单线程会话并发运行，只作同硬件工程测量。
- 详细证据见[树模型基线报告](2026-07-24-TQH-C2-C树模型基线报告.md)。下一门禁是去除 53 个跨开发划分同观测极短流哈希、共 260 条样本后的敏感性分析。
