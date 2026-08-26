# 本目录是有界快速缓存，不是全量数据产品

`runs/data-prepared/lspr23-lspr24-bounded-quick-q0-v1/` 里的每个角色最多只有 `262,144` 行，
字段只有 `77` 个，和协议A的 `83` 字段口径不同。它是 Q0 预算档的**有界快速**物化，
用来跑通管线和筛信号，**不能用来出正式结果，也不能和全量产品的数字放在同一张表里比**。

目录名里没有 `screen`、`quick-only` 之类的强提示，`data-prepared/` 这一层还和真正的全量产品
`ch3-protocol-a-raw83-shared-v1` 并排，所以很容易被当成正式数据取用。

## 一、部署与副本

| 位置 | 路径 |
| --- | --- |
| 服务器 | `/root/autodl-tmp/thesis/experiments/llm_probe/runs/data-prepared/lspr23-lspr24-bounded-quick-q0-v1/README.md` |
| 仓库权威副本 | `.Codex/docs/RWKV/数据目录身份说明/README-runs-data-prepared-lspr23-lspr24-bounded-quick-q0-v1.md` |

部署方式与 `README-runs-diagnostics-dijk-repro-cache.md` 第一节相同，改目的路径即可。

## 二、和全量产品的差别

以下取自生成它的配置 `thesis/experiments/llm_probe/configs/lspr-crossyear-c12-seed42-q0-v1.json`。

| 项 | 本目录 | 协议A全量产品 |
| --- | --- | --- |
| `materialization_mode` | `bounded_quick_cache` | 全量物化 |
| `budget_tier` | `Q0` | 不适用 |
| 每角色行数上限 | `262,144` | LSPR23 `16,353,511` 条流、LSPR24 `20,227,356` 条流 |
| 字段数 | `77` | `83`（Dijk 2026 附录 A 口径，含端口与协议） |
| 角色划分 | `source-train` / `source-validation` / `target-prefix` / `target-development` | 训练区／实体不相交验证区／目标年 |
| 变体 | `B0` / `M1` / `M2` / `M1M2` | 候选A标准化视图、候选B分位视图 |
| 规模 | `928,228,474` 字节（2026-08-25 B76 盘点） | `16,952,934,536` 字节 |

字段清单差异不只是数量：本目录的 `77` 字段里**没有端口字段**，
协议A的 `83` 字段包含 `SrcPort` 等端口与协议粗粒度指示。两套口径不能互相替代。

划分比例与归一化参数：`source_train_fraction=0.8`、`target_prefix_fraction=0.1`、
`target_development_end_fraction=0.8`、`normalization_clip=10.0`、`normalization_epsilon=1e-6`。

## 三、本目录自带的身份登记

和 `runs/diagnostics/dijk-repro/cache/` 不同，本目录**有完整清单**，取数前应当直接读：

| 文件 | 内容 |
| --- | --- |
| `dataset-manifest.json` | 数据集身份 |
| `manifests/field-manifest.json` | 字段清单 |
| `experiments/c12-seed42-q0-2ip-v1/experiment-manifest.json` | 实验身份 |
| `experiments/c12-seed42-q0-2ip-v1/normalizer.json` | 归一化统计量 |
| `experiments/c12-seed42-q0-2ip-v1/sample-manifest.parquet` | 逐样本清单 |
| `experiments/c12-seed42-q0-2ip-v1/sequence-manifest.parquet` | 序列清单 |
| `experiments/c12-seed42-q0-2ip-v1/selection-receipt.json` | 选择收据 |
| `experiments/c12-seed42-q0-2ip-v1/python-cache-v1/cache-manifest.json` | Python 缓存清单 |
| `receipts/final-isolation.json` | 最终测试隔离收据 |
| `receipts/materialization.json` | 物化运行收据 |

## 四、谁在引用它

仓库内 `22` 个代码或配置文件引用本目录（统计范围 `configs/`、`tools/`、`src/`、`scripts/`），
主要是 `c12-*`、`candidate-b-physical-time-rwkv-*`、`crossyear-*` 系列配置的 `cache_root` 与 `cache_manifest`。

## 五、判定规则

1. 看到 `bounded`、`quick`、`Q0`、`screen` 这类词，先假定它是**筛选档**，
   按仓库 `llm_probe/AGENTS.md` 的 `screening_only` 边界处理：可用于实现调试、速度诊断和信号筛选，
   结果不得进入论文正式结果、表格、帕累托比较或机制优劣主张。
2. 拟晋级正文的结论必须以独立正式运行身份、按冻结公平合同、在全量产品上重跑。
3. 取数前先读 `dataset-manifest.json` 与 `manifests/field-manifest.json` 确认行数与字段口径，
   不要凭目录名推断。
