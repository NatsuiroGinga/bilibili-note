# 可微树启发表格神经骨干审计笔记

## 任务快照

- 日期：2026-08-20
- 主代理：`gpt-5.6-sol`
- 推理强度：`high`
- 最高合同：`.Codex/docs/RWKV/2026-08-20-可微神经骨干替代XGBoost目标合同.md`
- 选择数据：仅 LSPR23 开发证据。
- 性能目标：`XGBoost + CPA + ELP`。

## 本地混合检索

- 初始状态为 schema 1、512 篇、6866 块且 `stale=true`；新解析合同排除 17 个非论文/错误对象。
- 首次 `--offline` 仍触发 Hugging Face 元数据 DNS，失败；加入 `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1` 后离线构建成功。
- 新索引：schema 2、495 篇、7307 块、44,949,504 字节、CPU 322.054 秒、`stale=false`。
- 本地查询数：5。查询覆盖 NODE、FT-Transformer、TabR、DeepGBM、GRANDE；均为 `scope=local/mode=hybrid/offline/top-k=8`。
- 关键命中：Gorishniy 2021、Grinsztajn 2022、Shwartz-Ziv 2022、TabM 2025；本地无 NODE、GRANDE、TabR、DeepGBM 独立全文笔记。

## 原论文与官方实现

- 新增并全文核验 NODE、GRANDE、TabR、DeepGBM；误把 arXiv:1907.06870 当 DeepGBM 后发现实际为 LMA，按 raw 不可变规则保留、纠错并另下正确 Microsoft Research DeepGBM 原件。
- 官方 HEAD：NODE `3bae6a8a...`、GRANDE `07f7278...`、TabR `17baa908...`、FT-Transformer `e3ed46ca...`、DeepGBM `6926d35b...`。
- 许可证：NODE/GRANDE/TabR 为 MIT，FT-Transformer 为 Apache-2.0，DeepGBM 未发现许可证。
- 外部检索式：20 条；仅原论文、正式会议页、作者/官方 GitHub 和 Microsoft Research 原件用于技术结论。

## 筛选记录

- 排序：GRANDE、NODE、FT-Transformer。
- 排除：TabR 当前规模超预算；DeepGBM 许可证不明；TabM 已有独立论文配方任务，不重复；LMA 与任务无关。
- D3=0；D2=3，其中 DeepGBM 因许可证硬门排除；D1=3。
- 核心 E3 全文 8 篇，处置性全文 1 篇。

## 文献归档

- 新增 5 个 PDF 原件、5 篇全文笔记、1 个子域 INDEX、5 个官方源码资源笔记。
- Zotero 导入 5 条：NODE `D4KH9JT8`、GRANDE `4L4MLPEB`、TabR `9C95X4NU`、DeepGBM `UTS5MJAS`、LMA `XS9LTRKE`。
- 并发期间 `evaluate.py` 曾短暂缺失，状态命令报 `ModuleNotFoundError`；生产入口恢复后未修改检索代码，继续完成索引。
- 增量索引：500 篇、7328 块、45,101,056 字节，耗时 6.537 秒；复用 7307 块、重嵌入 21 块，SHA-256 为 `233336912a1945398b1c748cb227ce83a6cdaf21b92abbeab9427d75a3e6775e`。
- 四条归档自检查询均命中第 1 位：GRANDE、NODE、DeepGBM、TabR。

## 未关闭问题

- GRANDE 原论文最大仅 96,320 样本，资源可扩展性只能由真实批次证伪。
- NODE 虽在 1050 万训练样本运行，但官方自述显存低效，仍需当前硬件实测。
- FT-Transformer 不具显式树归纳偏置，只作为可扩展回退。
- 文献代理因线程上限无法创建，已按父代理确认自行完成六阶段。
- 本任务不写实验代码、不访问服务器；候选效果均为实验待证。
