# B76 磁盘回收只读盘点 notes

## 会话身份

代理 `b76_disk_reclaim_audit_opus_high`，模型 `claude-opus-5`，`effort=high`。全程只读，未执行任何 `rm`、`mv`、`truncate`、`tar`、`gzip`、重定向写入或 `dd`。

## 与 2026-08-22 审计的结论对照

| 2026-08-22 结论 | 2026-08-25 复核 | 裁定 |
| --- | --- | --- |
| 可用 `21,235,464 KiB`，已用比例 `79.7483%` | 本次基线可用 `20,817,158,144` 字节，已用比例 `80.6125%` | 已过期，磁盘继续被写满 |
| `.venv` `6,988,954,589` 不可删 | 今日 `6,988,950,732`，仍是 CUDA 训练依赖 | 仍成立（数值有 3,857 字节漂移） |
| Raw83 共享产品 `16,952,934,536` 不可删 | 今日同值，且 CUDA RWKV 与表格 ResNet 的 `/proc/<pid>/fd` 直接命中其 `split/*.npy` | 仍成立，证据加强 |
| Dijk 缓存 `14,456,764,859` 不可删 | 今日同值。首次读到成员清单，确认是 LSPR23/LSPr24 冻结数组 | 仍成立，理由更正 |
| 原始数据目录 `4,701,076,796` 不可删 | 今日 `data/raw` 同值，只含 `lspr24-v1` 与 `lspr23-v1` | 仍成立 |
| 四项历史运行合计 `6,104,331,179`，本机无完整副本 | 今日实测四项 `du -sb` 合计 `6,104,331,143`；本机 ch4 worktree 已有逐文件一致副本 | 已过期，改判为低风险可删 |
| 宽视图数据产品 `5,439,656,623` 保留 | 今日同值，仍无完整本机副本 | 仍成立 |
| 未发现明确临时审计目录，`0` 字节 | 发现 `runs/diagnostics/_resume_audit_tmp` `342,705,713` 字节 | 已过期 |

`shared-b0-qwen-standard-pinn-seed42-200-v1` 在 2026-08-22 记为 `1,125,176,357`，今日实测 `1,125,176,321`，差 `36` 字节。四项今日合计 `6,104,331,143` 与任务简报给的数字完全一致，故以今日读数与简报为准，旧审计该行有误。

## 关键判定证据

### dijk-repro 是 LSPR，不是 Dijk2026

```
ls -la runs/diagnostics/dijk-repro/cache/
X23.npy 5,429,365,780 / X24.npy 6,715,482,320 / I23 278,338,688 / I24 205,644,928
M23 139,169,408 / M24 102,822,528 / y23 65,414,172 / y24 80,909,552
ent23 130,828,216 / t23_flow 130,828,216 / cat24 21,475,328 / t24 161,818,976
d24 495,445,716 / s24 494,808,757 / E23 2,174,648 / T23 2,174,648
```

`configs/ch3-tabm32-paper-recipe-protocol-a-seed42-v1.json` 第 9 行：
`"cache_root": "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"`。
全仓 `grep -rl 'dijk-repro' configs/ tools/ src/ scripts/` 共 `107` 个文件命中。判定依据是内容与被引用关系，不是目录名。

### 运行占用探测方法

```
pgrep -af python | grep llm_probe
grep -o '/root/autodl-tmp/[^ ]*' /proc/<pid>/maps | grep -v '\.venv'
ls -l /proc/<pid>/fd | grep -o '/root/autodl-tmp/[^ ]*'
```

基线时刻（`2026-08-25` 约 `10:5x` UTC）命中：`runs/data-prepared/ch3-protocol-a-raw83-shared-v1/generations/source-v1/split/train_rows.npy`、`validation_rows.npy`、CUDA `.so`、`runs/launchers/*/worker.lock`。没有任何历史路线目录被命中。

### 非 LSPR 归属的四步判据

1. `grep -l <路径> configs/ch3-*.json configs/ch4-*.json` → 全部 `0` 命中。
2. `/proc/<pid>/maps` 与 `/proc/<pid>/fd` → 全部 `0` 命中。
3. `grep -ril 'lspr' <目录>` → `12` 个大目录全部 `0`；反向 `grep -ril 'ns3|genis|tqh|dataset-v1'` 命中 `39/0/37/62/63/4985/66/4/32/24/26/19`。
4. 唯一双 `0` 的 `r2-minimal-sidecar-probe` 追到 `configs/r2_final_distilbert_f-a_seed42.yaml`，数据源是 `runs/data-prepared/r2-final-sidecar-candidate-v1-server/detection-view-*.parquet`。

`ab-pilot` 与 `thesis/experiments/genis` 的 `lspr` 命中来自 `.parquet` 与 `.npy` 二进制内容，是假阳性，逐个打开文件名核对后排除。

### 本机副本比对方法

两侧都用「只数普通文件」的口径，避免目录 inode 差异：

- 远端：`find <dir> -type f -printf '%s\n' | awk '{s+=$1;n++} END {printf "files=%d bytes=%.0f\n", n, s}'`
- 本机：`find <dir> -type f -exec stat -f %z {} + | awk '{s+=$1;n++} END {printf "files=%d bytes=%.0f\n", n, s}'`

必须同时查两处本机路径：`.worktrees/ch4-dtep-pbc-20260819/.../runs/` 与主工作树 `/Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/`。两处内容不同，只查一处会漏判。

## 踩到的坑

- `/root/.cache/uv` 有 `9,560,029,342` 字节，但 `df -B1 /root/.cache` 显示它在 `overlay` 根文件系统（`32,212,254,720` 字节，`42%`），不是 `81%` 的 `/dev/md0`。删它对本次磁盘毫无帮助。这是一个必须排除的假线索。
- `timeout 12` 对 `game-coordination` 等目录的 `find` 返回 `files=0`，一度误判为「测量超时」。实际是这些目录已被主代理删除。诊断方式是直接 `ls -la`，读到 `No such file or directory`。
- 本机 zsh 下 `for d in $DIRS` 不做词拆分，循环会把整串当成一个路径。改用 `/bin/bash -c` 执行。
- `awk` 默认对大数用科学计数法输出（`2.72998e+09`），必须 `printf "%.0f"` 才能拿到精确字节。

## 测量期间的状态变化

主代理在收到早报后已开始删除，本次盘点跨越了这次删除。基线与当前两组读数都记录在审计报告中，未把删除前的数字当作现状陈述。

运行集合也在变：基线时刻是 TabM32、CUDA RWKV、表格 ResNet 三个；`11:18:37Z` 时刻变成 TabM32、FT-Transformer 两个训练进程加一个 CUDA RWKV `--validate-config` 瞬时进程。审计报告按时刻标注。
