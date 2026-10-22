# 第五章平台端到端运行收据（2026-10-22 真实 E2E）

> 前端代理经 Web UI 提交 naive 格、平台串行队列执行至完成的运行收据。
> MySQL 数据卷随本机弃用不再保留，本文件为该次运行的持久记录；
> 新机复验＝compose 起 MySQL＋后端（真实 DB 模式）→ UI 再提交一次 naive 格对照。

## 运行身份
- 后端：Go/Gin，真实 DB 模式（`CH5_MYSQL_DSN`），监听 127.0.0.1:8080
- MySQL：Docker 容器 `ch5platform-mysql`（mysql:8.4，healthy），Server 8.4.13，库表 `tasks`（9 列，AutoMigrate）
- 任务：#1，配置 naive/off，经 `POST /api/tasks` 提交（页面操作）
- 数据根：`LAMDA_DATA_ROOT` 指向本机 ch3-drift 工作树内的 lamda-iclr2026-baseline（ad9614bdd5556767）——**新机需设置该环境变量**

## 生命周期时间线（UTC）
- created: 06:21:18.931209Z
- started: 06:21:18.957Z（排队等待 0.026 s）
- completed: 06:26:22.329Z（平台执行墙钟 303.372 s ≈ 5 分 3 秒）

## 读数一致性（平台 vs CLI naive）
- `panel.backward_f1`、`current_year_f1`、`current_year_metrics`、mean/F1-2023/2024/2025：
  **max_abs_delta = 0.0**（逐项完全一致）
- 12y mean 0.7244106926575061；2023 0.7494071146245059；2024 0.6829268292682927

## 性能分解
| 项 | 值 |
|---|---:|
| 内核 cell 墙钟 | 282.1 s |
| 共享数据加载 | 15.6 s |
| 进程/结果读写等残差 | ≈5.7 s |
| 提交→完成总墙钟 | 303.4 s |
| MPS 峰值（current allocated） | 71.4 MiB |
| CLI naive 内核墙钟对照 | 144.0 s |

> 平台内核墙钟约为 CLI 的 1.96 倍；归因待复测（本机后端启动未设 `OMP_NUM_THREADS=4`，CLI 运行有该设置）。
> 墙钟差异不构成结果有效性差异——读数逐位一致。

## 界面截图（已入库）
`thesis/figures/第五章/图5-7~5-10`（1920×1080 PNG，SHA256 已登记图件清单.json）
