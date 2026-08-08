# R2 数据重建任务 02 实现报告

## 状态

- 任务状态：首个可运行版本已完成，等待独立复审与后续服务器行为验收。
- 实现范围：GeNIS 10 秒官方 CSV 行迭代、旧标识重建、冻结候选哈希回接、逐行字段复算、不可逆来源映射和四字段单位证据门禁。
- 当前单位裁决：`NO-GO`。`TotBytes`、`TcpRtt`、`SrcWin`、`DstWin` 尚未获得本任务合同要求的一手证据，代码没有推断或填充其语义。
- 未访问服务器，未占用 GPU，未触碰正在运行的共享 B0 训练。

## 新增文件

1. `thesis/experiments/llm_probe/src/flow_probe/r2_protocol_genis.py`
2. `thesis/experiments/llm_probe/tests/test_r2_protocol_genis.py`
3. `.Codex/docs/sdd/task-r2-data-rebuild/reports/report-task-02-genis.md`

未修改任务 01 配置、合同模块、既有测试或冻结制品。

## 公开接口

- `iter_genis_10s_rows(archive, inventory)`：复用任务 01 的 `GeNISArchiveInventory`，重新核对归档大小、MD5、SHA-256、10 秒成员大小和成员 SHA-256；按 ZIP 成员 basename 与 CSV 数据行一基序号生成旧标识。
- `reconnect_genis_candidate(candidate, archive, config)`：复用任务 01 的 `R2ProtocolConfig` 和候选制品 SHA-256；只用固定候选哈希连接，逐行复算来源、标签、`group_id`、八字段、缺失掩码、来源记录哈希及非负包计数。
- `validate_genis_units(evidence)`：四项证据全部闭合才返回 `GO`；任一证据缺失、来源层级不足、单位或聚合语义不符时返回带原因的 `NO-GO`。

## 连接合同

旧标识精确复用历史适配器：

```text
genis:<ZIP成员basename>:<CSV数据行一基序号>
```

冻结候选标识精确复用历史候选协议：

```text
genis:sha256("dataset-candidate-genis-v0\0" + old_sample_id)
```

`group_id` 精确复用 `BLAKE2b-128(member_basename + NUL + FlowID)`。标签、协议、时间、地址、端口或特征值均不参与连接。生产运行时拒绝：

- 候选文件 SHA-256 漂移。
- 官方归档或成员 SHA-256 漂移。
- 候选标识重复或原始行生成标识碰撞。
- 一条候选多命中、候选缺失或目标候选未消费。
- 来源、`group_id`、二元标签、家族、子类、来源记录哈希、八字段或缺失掩码不一致。
- `Loss` 或 `Retrans` 为负数或非整数。

## 隐私与映射

`source_row_map` 固定只包含：

- 新样本哈希标识。
- 旧标识 SHA-256。
- 归档 SHA-256。
- 成员 SHA-256。
- 不可逆行引用 SHA-256。
- 连接状态、来源记录 SHA-256 和映射记录 SHA-256。

映射不保存成员名、原始行号、`FlowID`、地址、端口或原始连接标识。`TcpRtt`、`SrcWin` 和 `DstWin` 在单位门禁通过前输出为空和缺失掩码；窗口语义只登记为通告接收窗口，不解释为拥塞窗口。

## 单位门禁

- `TotBytes`：只接受 HERA 一手实现或网络层逐包复算；必须登记证据制品 SHA-256、算法、比较行数，且逐行精确整数一致数等于比较总数。
- `TcpRtt`：只接受一手单位、缩放和聚合语义，语义固定为握手往返时间。
- `SrcWin`、`DstWin`：只接受一手单位、缩放和聚合语义，角色固定为通告接收窗口。
- 四项必须同时通过；经验相关、字段名、样本拟合或部分证据均返回 `NO-GO`。

## 行为测试定义

测试文件定义 10 个行为节点，覆盖：

- 成员与一基行号标识重建。
- 成员哈希漂移拒绝。
- 固定身份哈希连接和字段复算。
- 不回退到标签或特征连接。
- 重复候选拒绝。
- 标签或观测复算漂移拒绝。
- 负数或小数包计数拒绝。
- 单位证据缺失、`TotBytes` 精确整数比较不完整和四项全部闭合。

按本轮用户合同未运行这些测试。

## 已执行检查

仅执行一次精确范围 Pyright：

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --no-sync pyright \
  src/flow_probe/r2_protocol_genis.py \
  tests/test_r2_protocol_genis.py
```

该唯一运行报告 4 项类型错误，均位于生产模块的运行时数值收窄：候选浮点转换、适配器特征联合类型和缺失掩码转换。随后已增加显式类型门禁和数值收窄。遵守“Pyright 最多一次”限制，没有第二次运行，因此修复后的静态状态仍待独立审查或后续统一验收确认。

## 未执行

- 未运行 `pytest`。
- 未执行真实模块导入。
- 未执行抽象语法树解析。
- 未执行任何自动格式化。
- 未运行 `git diff`、服务器预检或训练。

## 当前阻塞

实现本身没有外部数据写入阻塞。R2 正式数据构建仍被四项单位证据门禁阻塞；证据不足时必须保持 `NO-GO`，不得用本模块的连接成功替代单位语义验收。
