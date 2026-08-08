# 任务04：R2 ns-3 TCP/普通 UDP 配对矩阵实施报告

日期：2026-08-03  
状态：`review_pending`

## 结论

任务04R已把任务04错误冻结的 `ns3::TcpCubic` 修正为章级计划既定的 `ns3::TcpNewReno`，并确定性重生成正式清单。正式入口在同一次运行中完成当前任务01共享配置绑定、矩阵数量、因子覆盖、标签配平、种子映射、TCP/UDP 配对同一性、字段顺序和旧奇偶位协议捷径断言，然后写出：

- 256 个不含协议的基础配置；
- 512 条协议运行，其中 TCP 256 条、普通 UDP 256 条；
- 61,440 个预期窗口和 15,360 个预期四窗序列的冻结运行计划；
- 五个划分的基础配置数为 `train-fit=128`、`calibration=32`、`validation=32`、`test=32`、`unseen-configuration=32`。

本任务只冻结配置，不访问服务器、不运行 ns-3，也不产生窗口、序列或 TCP 内部状态真值。

为避免单一身份修复改变预注册随机分配，生成器继续用任务04原始矩阵哈希、原始共享合同哈希和原始拥塞控制文本复算既有 `seed_basis_sha256`、`run_seed` 与 `physics_group_sha256`；实际清单记录仍写当前配置哈希、当前共享合同哈希和 `ns3::TcpNewReno`。该兼容层只维持随机种子和协议顺序，不允许旧拥塞控制进入运行身份。

## 修改文件

- `thesis/experiments/llm_probe/src/flow_probe/r2_ns3_protocol_matrix.py`
- `thesis/experiments/llm_probe/configs/r2_ns3_protocol_matrix_v1.yaml`
- `thesis/experiments/llm_probe/tests/test_r2_ns3_protocol_matrix.py`
- `thesis/experiments/llm_probe/runs/data-freeze-configs/r2-protocol-v1/ns3-config-manifest.jsonl`
- `thesis/experiments/llm_probe/runs/data-freeze-configs/r2-protocol-v1/ns3-config-manifest.sha256`
- `.Codex/docs/sdd/task-r2-data-rebuild/reports/report-task-04-ns3-matrix.md`

未修改任务01、02、03的源码、配置、测试、报告或运行制品。

## 实现要点

1. 先按划分、流量模式、到达过程、队列、负载带和预注册重复槽生成不含协议的基础配置，再把协议作为最后一个笛卡尔维度展开。
2. 每个 `physics_group_sha256` 恰有一个 TCP 和一个普通 UDP；移除 `transport_family` 后，两条记录逐字段相同，包含相同运行种子、负载、拓扑、队列、容量、丢包和到达过程。
3. 环境网格选择的哈希基底不含协议和流量标签。相同划分、重复槽、到达过程、队列和负载带下，良性与攻击配置的环境参数和总提供负载相同，仅发送者组成不同。
4. 每条基础配置显式保存 `seed_basis_sha256`。运行种子由该哈希前8字节映射为非零31位整数；`physics_group_sha256` 再绑定全部基础字段和运行种子，不含协议文本、标签文本或顺序编号。
5. 每个配对组的协议先后顺序由组哈希域分离决定，正式断言要求奇数位和偶数位都同时出现 TCP 与 UDP，防止复现旧版协议与标签共用奇偶索引的捷径。
6. JSONL 使用配置中冻结的字段顺序，`transport_family` 固定为最后一列。输出文件已存在、部分文件已存在或输出目录为符号链接时均拒绝覆盖。
7. 正式清单逐行绑定当前任务01共享配置 SHA-256；任务01配置中的协议枚举、矩阵数量、时间窗口和覆盖门槛任一变化都会在写出前失败。
8. 任务04R逐行比较修复前后512条记录。除 `matrix_config_sha256`、`r2_contract_sha256` 两个来源绑定和 `tcp_congestion_control` 外，所有字段逐项相同；运行种子、种子哈希、配对组哈希和协议顺序均完全不变。

## 正式制品

- 清单：`thesis/experiments/llm_probe/runs/data-freeze-configs/r2-protocol-v1/ns3-config-manifest.jsonl`
- 清单大小：698,732 字节
- 清单 SHA-256：`d867c05013ff9c566d965ec3115bcefe6c905cca69865b042eb81f56e012a111`
- 校验文件：`thesis/experiments/llm_probe/runs/data-freeze-configs/r2-protocol-v1/ns3-config-manifest.sha256`
- 校验文件 SHA-256：`3cfdfc1d2270b38ea3915325abbf8c7f16f1a11492088f15e4706b8adebd53ab`
- 冻结配置 SHA-256：`0adcb49e52a1df156eddf4a3d01dfd51d00fa57752bcc0d04189073ace2edeeb`
- 绑定的任务01共享配置 SHA-256：`aa390129e239aa59d1c6963471e1268498a16740a5f11a916f489fa6a7292566`
- 生成器 SHA-256：`2228a0ac820895fbfbc11c4dda20c2406fcea638c2402e283a160ee96a874395`
- 直接合同测试 SHA-256：`5b6c99090833be0afef8412f57332b7529e075348dc70333e84046912bc64ac8`

## 正式生成

正式命令：

```bash
uv run --no-sync python -m flow_probe.r2_ns3_protocol_matrix \
  --config configs/r2_ns3_protocol_matrix_v1.yaml
```

任务04R使用 `UV_CACHE_DIR=/tmp/uv-cache` 执行同一正式入口，退出码为0；运行回执报告256个基础配置、512条协议运行及上述 SHA-256。

最小核验逐行读取修复前清单与当前清单，确认字段顺序不变、TCP/UDP各256条、二元标签各256条、五个划分仍为256/64/64/64/64条协议运行。逐记录差异集合精确为 `matrix_config_sha256`、`r2_contract_sha256` 和 `tcp_congestion_control`，种子与顺序等价状态为真；排除这三个允许变化字段后的顺序敏感投影 SHA-256 为 `3cef63f086db8d4ae07d57cf306105a394206701a2da829f9665f03183227a9e`。当前清单字节与生成器内存序列化结果完全一致，校验文件内容与清单 SHA-256 一致。

按用户当前规则，没有运行格式化、Prettier、抽象语法树检查、独立冒烟、独立 pytest 或重复 Pyright。正式入口本身已实际加载模块、解析两份 YAML，并执行生成与写出路径中的全部合同断言。测试文件仅作为后置回归合同落盘，未在本任务中独立执行。

## 剩余依赖

1. 任务01仍须把共享配置、生产代码和代码锁绑定到同一干净正式提交。当前清单绑定上述共享配置字节哈希；若任务01正式配置再次变化，本清单必须作废并经明确批准后重新生成，不能原地修改。
2. 任务05须使用更新后的运行器和受控参数消费本清单，原子归档第二次失败输出后从空输出根启动 `attempt3`，生成512条真实运行。
3. 配对完成率、逐窗包与网络层字节守恒、每划分有效因子覆盖及 TCP `cwnd` 窗口覆盖率只能由任务05真实运行验收，本报告不宣称这些运行期门槛已通过。
4. R2 数据重建和模型训练继续保持 `NO-GO`，直到任务01、任务05及后续重建门禁全部闭合。
