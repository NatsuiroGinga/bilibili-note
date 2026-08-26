# 本目录不是当前 LSPR 主线的冻结数据

`runs/data-frozen/` 里没有一个字节属于 LSPR23／LSPR24。名字里的「frozen」指的是
**已停用的 PINN／R2 历史路线**冻结下来的 genis、tqh-c2 与 shared-b0 数据集。
当前论文主线是 RWKV／LSPR，任何在 RWKV 路线上工作的代理都不应该从这里取数。

目录名叫 `data-frozen`，和 LSPR 主线真正的冻结产品 `runs/data-prepared/ch3-protocol-a-raw83-shared-v1/`
只差一层目录名，是极易误取的一对。

## 一、部署与副本

| 位置 | 路径 |
| --- | --- |
| 服务器 | `/root/autodl-tmp/thesis/experiments/llm_probe/runs/data-frozen/README.md` |
| 仓库权威副本 | `.Codex/docs/RWKV/数据目录身份说明/README-runs-data-frozen.md` |

部署方式与 `README-runs-diagnostics-dijk-repro-cache.md` 第一节相同，改目的路径即可。

本目录在 2026-08-25 的 B76 盘点中被判为「用户已授权删除、但尚未回收」。部署前先确认它还在；
若已被回收，本文件保留在仓库里作为历史身份记录即可，不必重建目录。

## 二、里面是什么

顶层子目录（取自仓库内配置引用，不是服务器实测 `ls`）：

| 子目录 | 路线 |
| --- | --- |
| `dataset-v1`、`dataset-v1-provisional` | R2 历史路线 |
| `dataset-v1-shared-b0`、`dataset-v1-shared-b0-physics-v1` | R2 共享 B0 数据集（BERT／Qwen 训练文件） |
| `dataset-candidate-genis-v0` | genis 候选协议与切分 |
| `dataset-candidate-tqhc2-abc-v0` | tqh-c2 ABC 候选协议与切分 |
| `dataset-candidate-r2-protocol-v0` | R2 协议候选 |
| `r2-protocol-tqhc2-handoff-v0`（含两个 `.partial`） | R2 到 tqh-c2 的交接构建 |

2026-08-25 B76 只读盘点：整目录 `1,534,543,038` 字节。本机主工作树同名目录
`files=165 bytes=797,274,437`，远端 `files=124 bytes=1,534,495,708`——
**文件数多而字节少，两侧内容不同，本机副本不完整，不能当作远端备份。**

## 三、谁在引用它

仓库内 `33` 个文件引用本目录：`19` 个 `.yaml`、`6` 个 `.sh`、`5` 个 `.py`、各 `1` 个 `.json` 与 `.rs`
（统计范围 `configs/`、`tools/`、`src/`、`scripts/`）。
其中 YAML 配置全部是 PINN／R2 路线的历史训练与评测配置，例如
`configs/r2_final_detection_development_split_v1.yaml`、`configs/shared_b0_qwen_seed42_200.yaml`。

**引用数多不代表它属于当前主线。** 这些引用是历史路线留下的，按仓库根 `AGENTS.md`，
PINN／R2 只有在用户明确指定时才进入上下文。

## 四、当前主线该去哪里取数

| 需要什么 | 路径 |
| --- | --- |
| LSPR23 raw83 冻结产品 | `runs/data-prepared/ch3-protocol-a-raw83-shared-v1/generations/source-v1/` |
| LSPR24 原始 Parquet | `data/raw/lspr24-v1/lspr24_v2.parquet` |
| LSPR23 原始 Parquet | `data/raw/lspr23-v1/` |
| 序列索引与掩码 | `runs/diagnostics/dijk-repro/cache/I{23,24}.npy`、`M{23,24}.npy`（先读该目录的 `README.md`） |

## 五、判定规则

1. 目录名里的「frozen」「final」「shared」只说明它当时被冻结过，**不说明它属于哪条研究路线**。
2. 取数前先确认数据集身份（LSPR 还是 genis／tqh-c2／shared-b0），再确认路线（RWKV 还是 PINN／R2）。
3. 本目录的任何内容不得进入 RWKV 路线的实验、结论或论文正文。
