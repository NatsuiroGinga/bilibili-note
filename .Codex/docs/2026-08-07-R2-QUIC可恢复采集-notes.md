# R2 QUIC 可恢复采集证据笔记

## 已冻结事实

- 旧 v5 正式运行状态必须保持 `failed`，已完成 `23/120`，不得追溯改写。
- 冻结 `index24` 的新诊断身份自然完成，但诊断制品不得直接并入旧矩阵。
- 下一步是设计可恢复采集规则，再运行剩余 97 项；QUIC 不阻塞 E2。

## 阶段 2 已核对结果（2026-08-07）

### 接口定位

- 采集器：`scripts/r2_quic_controlled_collect.py`（1403 行）。入口 `main()`（1210 行起），参数解析 `parse_arguments()`（1199 行）。
- 索引选择：`--only-index`（1 基），`specs = [matrix_specs[only_index - 1]]`，`run_expected = len(specs)`。这正是计划所需的「单索引恢复单位」。
- 状态落盘：`output_root/run-state.json`（每条完成后原子重写）与 `output_root/connections/<id>/status.json`（逐连接）。
- 启动器：`scripts/run_r2_quic_controlled_collection.sh`（116 行）。位置参数依次为 `PHASE RUN_ID STOP_AFTER ONLY_INDEX OUTPUT_ROOT CONFIG`；用 `screen -dmS` 后台化；完整保留 `PIPESTATUS` 两端；`status.json` 已存在时**拒绝重复启动**（第 74–77 行）。
- 冻结正式配置：`configs/r2_quic_stratified_pilot120_v5.json`（305 行）。
- 相关测试：`tests/test_r2_quic_v8_contract.py`、`test_r2_quic_v3_contract.py`、`test_r2_quic_v4_contract.py`、`test_r2_quic_v8_1_receipt_patch.py`、`test_audit_r2_quic_v7_gate.py`。
- 审计门禁：`scripts/audit_r2_quic_v8_1_gate.py`（487 行）。

### 服务器实际状态（只读核验）

| 运行目录 | connections | finished | run-state.status |
| --- | ---: | ---: | --- |
| `r2-quic-v8-1-stratified-pilot120-v1` | 1 | 0 | `interrupted` |
| `r2-quic-v8-1-stratified-pilot120-v2` | 1 | 0 | 无 `run-state.json` |
| `r2-quic-v8-1-stratified-pilot120-v3` | 11 | 10 | `running` |
| `r2-quic-v8-1-stratified-pilot120-v4` | 12 | 11 | `running` |
| `r2-quic-v8-1-stratified-pilot120-v5` | 24 | 23 | `running` |

- v5 即总控所称「旧 v5 正式运行」，`23/120` 完成，第 `24` 个连接目录存在但未完成。
- **待澄清**：v5 的 `run-state.json` 停在 `running`（进程中途死亡，未回写终态），而总控记为 `failed`。需核对启动器 `runs/launchers/` 下对应 `status.json` 的终态，确认「`failed`」这一表述的证据来源，两者不一致时以启动器收据为准并在总控注明。
- 诊断目录 `runs/data-raw/r2-quic-v8-1-index24-diagnostic-20260806T145516Z` 与正式目录同级。

## 阶段 2 结论修正（重要）

初稿曾把 `D1`–`D5` 五项都列为阻塞缺陷。继续核验源码后**该判断有一半不成立，已作废**，改以下事实为准。

### 采集器本来就支持断点续采

`collect_connection()`（第 524 行起）开头即检查 `connections/<id>/status.json`：

- `status == "finished"` → 直接返回，**跳过已完成连接**，不重采；
- 存在但非 `finished` → 抛 `RuntimeError("连接目录已有非完成状态，禁止自动覆盖")`；
- 不存在 → `mkdir(exist_ok=False)` 新建后采集。

因此对 v5 输出根重跑**完整矩阵**（不带 `--only-index`）就是正确的续采方式：跳过已完成的 23 条，从未完成处继续。终态判定 `finished_count == run_expected` 在完整矩阵下 `run_expected=120`，逻辑正确。

### 唯一真实阻塞点

`connections/f48643ea2f99d01d72b1bd1e`（第 24 条）存在且 `status="failed"`：

- `error_type="TimeoutExpired"`，`elapsed_seconds=602.034`，`client_timeout_seconds=600.0`；
- `client_natural_completion=false`，`client_exit=-15`，`server_exit=-15`，`capture_exit=0`、`proxy_exit=0`；
- `collection_config_sha256=7595d0b36b148f76e182b2fe6d173b53493d67216e32ddf4539a518ae1fe3c19`。

重跑完整矩阵会在这一条上按上述规则抛错终止。**这是唯一需要处理的东西。**该冻结连接的独立诊断身份已于 `120.644` 秒自然完成，证明不是确定性失败，可以重采。

### 各原缺陷的最终判定

| 编号 | 最终判定 |
| --- | --- |
| D1 输出根可复用 | **作废**。复用输出根正是续采机制本身，并由逐连接非完成态检查兜底，不是缺陷。 |
| D2 单索引终态判定 | **降级为非阻塞**。仅在使用 `--only-index` 时成立；完整矩阵续采不受影响，因此不必为本次采集修改。 |
| D3 无 120 项发布门禁 | **未证实**。尚未核验 `scripts/audit_r2_quic_v8_1_gate.py`（487 行）与 `scripts/r2_quic_formal_materialize.py`（873 行）是否已承担该职责，核验前不得当作缺陷。 |
| D4 恢复项无绑定校验 | **部分不成立**。逐连接 `status.json` 已记录 `collection_config_sha256` 与 `four_tuple_contract_sha256`；完整覆盖面待核验。 |
| D5 诊断身份可被误用 | **推测，未证实**。无实际误用证据，降为待观察。 |

### 容量与耗时估算

- v5 现占 `3.7 GiB` / 24 条，约 `154 MiB` 每条。剩余 97 条约需 `14.5 GiB`。
- 服务器可用 `39 GiB`；配置 `minimum_free_bytes_before_formal = 21474836480`（`20 GiB`）为硬门禁，正式阶段每条采集前都会检查，不足即写 `storage_gate_stopped` 并停止。
- 预计采完后剩余约 `24 GiB`，**高于门禁但余量仅约 4 GiB**，属于需要监控的窄裕度。
- 单条耗时参照 index24 诊断的 `120.644` 秒，97 条粗估 `1.5～3.5` 小时。

### 二次修正：不得向 v5 续采（以用户 2026-08-07 重申的冻结事实为准）

上一节「对 v5 输出根重跑完整矩阵就是正确的续采方式」**在合同层面不成立，已作废**。冻结约束为：

- 旧 v5 正式矩阵只完成 `23/120`，必须保持 `failed` 历史状态，**禁止追加或改写**；
- `index24` 独立诊断只证明旧超时不是确定性失败，**禁止直接并入旧 v5 矩阵**。

这与原始计划一致：「恢复单位为单个索引，而不是向旧 v5 目录补写」「正式发布只接受绑定同一冻结配置、连接身份、代码和输出哈希的 `120` 条全新正式身份」。因此续采路径是**全新 attempt 跑满 120 条**，v5 原样冻结。

由此 `D2` 重新成为真实阻塞项：若按原计划用 `--only-index` 逐项跑进新根，`run_expected=1` 而 `finished_count` 统计全根，终态判定必错。

### 容量：这是当前第一阻塞

- 单条约 `150 MiB`（v3 `11` 条 `1.6 GiB`、v4 `12` 条 `1.9 GiB`、v5 `24` 条 `3.7 GiB`，互相印证）。
- 全新 `120` 条 attempt 约需 **`18 GiB`**。
- 服务器可用 `39 GiB`，硬门禁 `minimum_free_bytes_before_formal = 20 GiB`，**实际可用余量只有约 `19 GiB`**。
- 净裕度约 `0.5 GiB`，正式阶段每条采集前都检查，**几乎必然中途触发 `storage_gate_stopped`**。因此不先腾空间就启动，等于重演 v5 的中断。

可回收候选（均为被 v5 取代的部分尝试，回收前应先拉回本机留存）：

| 路径 | 占用 | 状态 |
| --- | ---: | --- |
| `runs/data-raw/r2-quic-v8-1-stratified-pilot120-v4` | `1.9 GiB` | `11/120` 完成，被 v5 取代 |
| `runs/data-raw/r2-quic-v8-1-stratified-pilot120-v3` | `1.6 GiB` | `10/120` 完成，被 v5 取代 |
| `runs/data-raw/r2-quic-v8-1-matrix600-v2` | `266 MiB` | 旧 600 矩阵尝试 |
| `runs/data-raw/r2-quic-v8-1-stratified-pilot120-v2` | `69 MiB` | `0/120` 完成 |
| `runs/data-raw/r2-quic-v8-1-stratified-pilot120-v1` | `69 MiB` | `0/120` 完成 |
| 合计 | 约 `3.9 GiB` | 回收后净裕度升至约 `4.4 GiB` |

`pilot120-v5`（`3.7 GiB`）与 `index24` 诊断（`379 MiB`）是冻结失败证据与诊断证据，**不在回收范围**。

### 因此「可恢复采集规则」的最小正确形态

1. 新建全新正式输出根（如 `...-stratified-pilot120-v6`）与全新启动器身份，v5 原样保留；
2. **跑完整矩阵而不用 `--only-index`**，使终态判定 `finished_count == run_expected == 120` 成立，同时绕开 `D2`，不必改动 1403 行采集器的索引语义；
3. 出现 `TimeoutExpired` 类非确定性失败时，把该连接目录原子归档到本运行根内带日期的失败归档，再重启完整矩阵——采集器会跳过已完成项、只重采被归档项；
4. 重试有界（建议单索引至多 `3` 次、全局至多 `10` 次），每次尝试的状态、日志与退出码全部保留；
5. 不放宽 `600` 秒超时，不修改任何冻结科学参数。

该形态是启动器层的有界重试循环，不需要重写采集器。
