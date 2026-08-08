# R2 数据源恢复与任务 01 正式预检报告

## 结论

- 本阶段完成 **A/B/C 处理制品与 `approved-inputs.json` 恢复**：服务器共恢复并逐项验签 `28/28` 个文件，精确总大小 `300,894,341` 字节。
- 任务 01 服务器目标测试通过：`52 passed`，退出码 `0`，耗时 `4.90s`；未运行格式化。
- `raw/datasets/GeNIS-2025/0-info.zip` 已补齐，大小 `3,308` 字节，SHA-256 与计划一致。
- 任务 01 的 `verify_genis_archive` 独立预检通过：正式 `2-flows.zip` 大小、官方 MD5、归档 SHA-256、四尺度成员数量和 10 秒尺度物化成员数量均通过。
- 完整 `verify_frozen_inputs -> write_source_lock` 正式入口 attempt-3 的真实退出码为 `1`，当前首个阻塞为服务器缺少 `raw/datasets/TQH-C2-2026/extracted/A/A_i1800_j0/conn.log`。
- `source-lock.json` **未生成**。R2 数据门禁继续为 `NO-GO`，未启动 GPU 训练、下载、原始数据上传或正式物化。

## 输入与边界

- 本机项目根：`/Users/bilibili/personal/note/thesis/experiments/llm_probe`
- 服务器项目根：`/root/autodl-tmp/thesis/experiments/llm_probe`
- 服务器日志根：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/validation/r2-source-restore-preflight-20260731/`
- 唯一需求源：`.Codex/docs/sdd/task-r2-data-rebuild/task_plan.md`
- 未上传本机约 `98 GiB` 的 `raw/datasets/TQH-C2-2026/`。
- 未下载任何数据，未删除服务器或本机实验文件，未启动训练、SwanLab、GPU 任务或 `screen` 会话。

## 同步前状态

- 服务器 A/B/C 与 `approved-inputs.json` 四个固定目标均不存在。
- `/root/autodl-tmp` 同步前可用 `15,763,484,672` 字节，已用 `71%`。
- GPU 计算进程为 `0`，`screen` 会话为 `0`，R2/任务 01 运行进程为 `0`。
- 服务器任务 01 代码、配置和测试与本机逐字节一致：
  - `r2_protocol_contract.py`：`f73334ff2e4b4d84adabcf96939a5f891073a366d73b78a1668eff186f678b76`
  - `r2_protocol_data_v1.yaml`：`0793d00a3b67a20960b32efb33c5a5e45cd5bae04d2e7bb24d5e7cd629c5a935`
  - `test_r2_protocol_contract.py`：`e47b1b5c39f50acc1653e9559f5ea69ea861bab0af2a4b9e6af28baf15c3c841`
- 服务器项目树没有可解析的 Git `HEAD`；`git rev-parse HEAD` 退出 `128`。

## 同步执行与中断恢复

1. 仓库现有 `guarded_rsync.py` 在计划阶段拒绝 `runs/` 源与目标，返回“路径命中隐藏、缓存、数据、模型、运行或凭据禁区”，因此没有通过该入口传输任何字节。
2. 按控制器裁决，改用项目既有 `/tmp/gpu-rsync-push.exp`，只同步明确的 `28` 个白名单文件。
3. 首轮长同步在运行约 `18s` 后被会话主动中断。只读回查发现服务器已有 A 的 `3` 个完整小文件；三者 SHA-256 与本机一致，因此未重复覆盖。
4. 后续按缺失文件续传并逐文件执行服务器 `sha256sum`。A 包表首次 Expect 返回非零，但服务器最终文件大小为 `161,878,279` 字节，SHA-256 为 `2366a25dc3a3c847ecb3549c4d79d131e172a17aa53b709dd65949a26647a32f`，与本机和冻结清单一致，因此记录传输告警且未重传。
5. 最终服务器文件清单为 `28` 项，逐文件哈希均与本机源一致；同步后可用空间为 `15,462,395,904` 字节，已用 `72%`。

## 恢复制品验收

### 清单哈希

| 输入 | SHA-256 |
| --- | --- |
| A `artifact_checksums.provisional.json` | `f26723b0a10deb383aff9f7f9fa5893d30b883f1f602cbbc633e4e1846015a68` |
| B `artifact_checksums.provisional.json` | `44900a6bee08f0d339693524a42975d1ad9e47721f38bb70c1a6c886ce17a6f5` |
| C `artifact_checksums.provisional.json` | `2203113a7cf198de5b393923a20cba22ad06127545123471f033cccb8a3e925e` |
| `approved-inputs.json` | `191f737ae18eec982b8031b1ced2e6f74b3f122e6c1fa0bc97596ab3cdada610` |

### 关键 Parquet 元数据

| 档位 | 主记录字节 | 主记录行数 | 包表字节 | 包表行数 | 来源记录数 |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 18,395,426 | 181,556 | 161,878,279 | 15,761,376 | 73 |
| B | 11,739,958 | 115,734 | 101,019,345 | 9,857,089 | 73 |
| C | 3,840,469 | 36,671 | 3,897,491 | 396,271 | 73 |

- 三份 `source_checksums.json` 各为 `442` 个文本行。
- A/B/C 各包含 `9` 个服务器文件：`8` 个登记处理制品和 `1` 份制品清单。
- 加上 `approved-inputs.json` 后总计 `28` 个文件、`300,894,341` 字节。

## 任务 01 验证

### 目标测试

```text
....................................................                     [100%]
52 passed, 1 warning in 4.90s
```

- 测试退出码：`0`
- 日志：`runs/validation/r2-source-restore-preflight-20260731/task01-tests.log`
- 退出码：`runs/validation/r2-source-restore-preflight-20260731/task01-tests.exit-code`
- 唯一警告是重复 ZIP 成员失败测试触发的标准库 `UserWarning`，不影响通过状态。

### GeNIS 正式归档

`verify_genis_archive` 退出码为 `0`：

- 大小：`380,755,720` 字节
- 官方 MD5：`063b7a2ec6e6b73cc302151d2b3ba6d7`
- 归档 SHA-256：`72033b5e3df6e45cda9a339985194d8232c437c243a5037a62ebeff457489b30`
- 5/10/30/60 秒四个尺度均为 `11` 个成员
- 10 秒尺度物化成员数：`11`
- 日志：`runs/validation/r2-source-restore-preflight-20260731/genis-archive-preflight.log`

### 完整正式入口

正式调用顺序为：

```text
load_r2_config -> verify_frozen_inputs -> write_source_lock
```

执行记录：

1. 首轮日志正确记录缺少 `raw/datasets/GeNIS-2025/0-info.zip`，但 Shell 中 `$?` 被本地提前展开，错误写入退出码 `0`。该退出码文件明确标记为无效证据，日志本身保留，不覆盖。
2. attempt-2 采用不含本地展开的调用，真实退出码为 `1`，同样停在缺少 `0-info.zip`。
3. 本机 `0-info.zip` 经核验后同步到 `/root/autodl-tmp/thesis/raw/datasets/GeNIS-2025/0-info.zip`：大小 `3,308` 字节，SHA-256 `7ef636cc758586f18a5d9958e68eede9b85925610331283cce802f45542701bc`。
4. attempt-3 真实退出码为 `1`，首个错误推进到：

```text
R2ProtocolContractError: 冻结输入不存在：
raw/datasets/TQH-C2-2026/extracted/A/A_i1800_j0/conn.log
```

- attempt-3 日志：`runs/validation/r2-source-restore-preflight-20260731/task01-source-preflight-attempt-3.log`
- attempt-3 退出码：`runs/validation/r2-source-restore-preflight-20260731/task01-source-preflight-attempt-3.exit-code`
- `write_source_lock` 未执行，`runs/data-freeze-configs/r2-protocol-v1/source-lock.json` 未生成。

## 阻塞判定

### 已完成

- **处理制品恢复成功**：A/B/C 与批准输入已恢复，28/28 文件逐项验签。
- **本机原始 PCAP 存在**：A/B/C 各 `12` 个 PCAP 和 `12` 个 `conn.log`；各 profile 的 `73` 项来源记录全部存在。原始 PCAP、`conn.log`、标签和审计文件没有缺失或登记大小差异。
- **任务 01 行为验收通过**：52/52 服务器测试通过。
- **GeNIS 正式归档通过**：大小、MD5、SHA-256 和 ZIP 成员合同通过。

### 当前硬阻塞

1. **服务器缺少 TQH 原始源**：attempt-3 首个缺项为 A 的 `conn.log`。本机完整原始根约 `98 GiB`，而服务器同步后仅余约 `15.46 GiB`，且任务禁止新增超过 `5 GiB` 的动作；不得盲目上传。
2. **A/C 提取器历史快照阻塞**：A/C 的来源清单登记旧提取器大小 `46,140` 字节及 SHA-256 `7daa2b2de3878660bb02860f416892d5a64aba3cc7edf5de561faa575047a617`；当前 `src/flow_probe/tqh_c2.py` 为 `55,523` 字节。该差异不是原始数据缺失，必须继续标记为 `approved_manifest_only_blocked`。
3. **服务器 Git 提交绑定阻塞**：服务器工作树没有可解析的 `HEAD`。即使补齐原始源，`verify_frozen_inputs` 最终仍需要可验证的代码提交绑定；不得把当前未提交代码错误记为旧提交。
4. **后续单位语义仍未闭合**：`TotBytes`、`TcpRtt`、`SrcWin`、`DstWin` 继续保持计划中的 `blocked_pending_semantics`，本阶段未尝试猜测或解除。

## 服务器证据路径

- `processed-files.txt`：28 项固定文件清单
- `processed-file-count.txt`：文件数
- `processed-artifact-sha256.txt`：28 项服务器 SHA-256
- `processed-artifact-byte-counts.txt`：逐文件字节与总字节
- `processed-manifest-sha256.txt`：三份制品清单与批准输入哈希
- `processed-parquet-rows.json`：关键 Parquet 行数和字节
- `source-record-counts-attempt-2.json`：A/B/C 各 73 项来源记录
- `disk-after-sync.txt`：同步后磁盘证据
- `task01-tests.log`：52 节点测试日志
- `genis-archive-preflight.log`：GeNIS 正式归档预检
- `task01-source-preflight-attempt-2.log`：补字典前正式预检
- `task01-source-preflight-attempt-3.log`：补字典后正式预检与当前首个阻塞

以上文件均位于：

```text
/root/autodl-tmp/thesis/experiments/llm_probe/runs/validation/
r2-source-restore-preflight-20260731/
```

`source-record-counts.json` 是一次 Shell 变量提前展开产生的无效 `0/0/0` 记录；正确证据为 `source-record-counts-attempt-2.json`。首轮 `task01-source-preflight.exit-code` 同样无效；正式退出码以 attempt-2 和 attempt-3 文件为准。

## 本机文件变更

- 新建本报告：`.Codex/docs/sdd/task-r2-data-rebuild/reports/report-r2-source-restore-preflight.md`
- 曾生成但未同步、未执行的两份本机运行助手：
  - `.Codex/docs/sdd/task-r2-data-rebuild/reports/r2_source_restore_preflight.py`
  - `.Codex/docs/sdd/task-r2-data-rebuild/reports/run_r2_source_restore_preflight.sh`
- 控制器随后要求直接执行现有命令，因此两份助手没有参与任何服务器操作。删除操作受当前“不得删除文件”边界约束，故保留并在此披露。
- 未修改任务 01 的生产代码、配置、测试、计划或高层恢复文档。
- 按用户要求未执行 Black、Ruff、Prettier 或其他格式化工具。

## 下一门禁

1. 不在当前服务器上传约 `98 GiB` 原始 TQH 根。先提供足够磁盘的新实例、只读挂载或其他经批准的源访问方式。
2. 取得并验签 A/C 历史提取器快照，或通过独立计划正式修订证据合同；不得把当前 B 快照冒充 A/C 历史快照。
3. 建立服务器可验证的 Git 提交或等价、经审查的实际代码文件绑定。
4. 三项条件满足后重新运行任务 01 正式预检，要求 `source-lock.json` 生成且所有阻塞状态如实保留。
5. 只有源锁、单位语义、ns-3 trace 与其余 P0 门禁通过后，才允许进入后续 R2 数据构建；当前不得启动 GPU 训练。

## 本机损坏 GeNIS 副本清理登记

日期：2026-08-01

- 待删除绝对路径：`/Users/bilibili/personal/note/raw/datasets/GeNIS-2025/2-flows.zip`
- 实际大小：`14,520,320` 字节
- 实际 MD5：`aeda3d98b04d792fd38dad4d5ae80f36`
- 实际 SHA-256：`4909099b9a1ea53c547b0b7753bed4885d1d29080cd5183a3e20debb9643c089`
- 权威期望大小：`380,755,720` 字节
- 权威官方 MD5：`063b7a2ec6e6b73cc302151d2b3ba6d7`
- 已核验权威 SHA-256：`72033b5e3df6e45cda9a339985194d8232c437c243a5037a62ebeff457489b30`
- 判坏依据：实际文件比权威大小少 `366,235,400` 字节，且 MD5 与 SHA-256 均不匹配；该路径已被实施计划明确禁止读取、续传、拼接、修补或物化。
- 清理边界：只删除上述已核验损坏副本；不删除正式 TQH 双物化载荷、原始 TQH、`0-info.zip` 或任何未核验文件。
- 清理结果：上述损坏副本已删除，释放 `14,520,320` 字节；删除后路径不存在。
- 保留复核：build-a 与 build-b 的 `packet-observations.parquet` 仍分别为 `17,446,431` 字节，未被清理操作触碰。
