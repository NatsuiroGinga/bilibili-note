# GeNIS 候选数据与树模型基线证据笔记

## 恢复与规则核对

- `output/第一创新点实验总控.md` 明确规定：GeNIS 正式协议需要训练、验证、域内测试、时间前向测试和未知攻击测试，并以会话、时间和采集场景隔离优先。
- `.Codex/docs/2026-07-24-统一数据冻结与PINN候选顺序实验合同.md` 明确规定：所有方法共享同一 `sample_id`、标签、划分和样本顺序；`eval300` 只能作为开发裁决集，不能作为未触碰最终测试。
- 当前任务仅构建 GeNIS 候选开发协议和验证基线，不发布完整三源 `dataset-v1`，也不据此选择 R1、R2 或 R3。

## 服务器前置核对

- 核对日期：2026-07-24。
- `screen -ls`：无会话。
- GPU 计算进程：无。
- `/root/autodl-tmp`：总计 `50 GiB`，已用 `30 GiB`，可用 `21 GiB`，使用率 `59%`。
- 首次文件盘点因服务器缺少 `fd` 未完成；下一步改用 `rg --files`。

## 待核验问题

1. `genis-hybrid-forward-v1-20260719-v3` 是否包含稳定来源行标识、采集场景、会话键和可验证时间字段。
2. 既有训练/验证/时间前向/未知攻击清单是否来自原始划分证据，而非 `eval300` 二次抽样。
3. 家族与子类标签映射是否可由明确契约复现，未知子类是否在训练与阈值校准中完全缺席。
4. 哪些字段可作为树模型输入，哪些必须归为 `label_target`、`split_metadata` 或 `audit_only`。
5. 现有树模型入口是否已支持同清单、三种子、SwanLab 在线与完整制品保存；不足部分需最小扩展。

## 输入追溯结论

- v3 物化文件：训练 `151,324` 行、验证 `12,884` 行、时间前向测试 `29,314` 行；三个开放集文件分别为 `393,216`、`392,736`、`393,216` 行。
- v3 物化摘要的 `assignment_sha256` 为 `d4d3909abab9900f5c38bc5d3799991b52d3dc1eceb9d79ff02026e128eb4cae`，与 `runs/data-splits/genis-hybrid-forward-v1-20260719-v2/session_assignments.jsonl` 完全一致。
- v3 摘要与 v2 划分计划列出的 11 个原始 CSV 文件名、大小和 SHA-256 逐项一致；划分比例为 `0.8/0.1/0.1`，整类留出的未知子类为 `dos-icmp`、`dos-pushack`、`dos-udp`。
- 会话分配共 `201,343` 行，包含 `session_id`、`subtype`、`binary_label`、`start_time`、`last_time`、`row_count` 和 `assignment`，因此旧 v3 缺失的子类字段可由已绑定分配清单恢复，不需要推断或补造。
- 本地与服务器当前 `genis_forward_split.py`、适配器、模式文件和两个脚本的 SHA-256 一致；当前代码写 `genis_materialized_split_v2` 和 `attack_subtype`，旧 v3 明确是较早的 v1 制品。

## 开发集字段与标签

- 训练/验证共同记录字段为 `sample_id`、`group_id`、`source_dataset`、`binary_label`、`attack_family`、`features`、`prompt`、`completion`。
- 八个数值观测字段为 `total_packets`、`total_bytes`、`packet_length_mean`、`packet_length_min`、`packet_length_max`、`iat_mean_ms`、`packet_rate`、`byte_rate`；其中训练加验证共有 `47,977` 条 `iat_mean_ms` 缺失，其余字段无已发现缺失。
- 家族开发标签为 `benign`、`bruteforce`、`dos`；训练和验证均覆盖八个已知子类。三个整类留出对象都属于 `dos` 家族，因此开放集结论只能表述为未知子类，不得表述为未知家族。
- 旧 `sample_id` 形式为 `genis:<源文件名>:<行号>`，源文件名直接含攻击子类。虽然现有树加载器不会读取标识列，候选协议仍须使用不含文件名的单向哈希新标识，并把旧标识仅用于内存连接。

## 泄漏审计决策

- 会话分配已证明按子类执行前向时间切分并清除跨边界会话，`group_id` 是源文件名与原始 `FlowID` 的不可逆哈希。
- 训练集有 `135,291` 个唯一八字段观测签名，验证集有 `11,520` 个；两者共有 `1,155` 个精确签名。
- 共有 `2,485` 条验证记录命中训练签名，家族分布为 benign `726`、bruteforce `10`、dos `1,749`。
- 主训练清单保持原训练记录；主验证清单按预注册纯特征规则排除上述记录，确保严格验证清单与训练清单的精确观测签名交叉为 0。排除动作不读取测试或开放集指标，原记录保留在主表并记录排除原因。
- 时间前向测试和开放集只生成不可变清单与哈希，本轮树模型入口只接受 `split_id=validation`，不会读取这些清单进行调参或结果选择。

## 既有运行接口

- `flow_probe.frozen_protocol` 已能验证协议版本、制品哈希、字段角色、清单顺序、样本成员关系和同套件跨划分冲突。
- `flow-probe-tabular-baselines` 已限制 `theory_selection` 只能读取 `validation`，支持 HGB/XGBoost、纯 CPU、三随机种子、SwanLab 在线、预测、成本、环境、日志与制品清单。
- 因此本任务只需新增 GeNIS 候选协议物化模块和测试，不修改通用加载器、树模型入口、`pyproject.toml` 或 TQH-C2 候选构建器。
