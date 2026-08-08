# 任务 04R/05R NewReno 合同修复独立复审

日期：2026-08-03  
复审方式：只读静态复审与确定性制品核验；未连接服务器，未修改生产文件，未运行格式化、Pyright、pytest、全量测试、独立冒烟或正式矩阵

## 裁决

**任务 04R/05R 对 attempt3 的裁决为 `GO`，未发现严重或重要问题。**

该 `GO` 只允许按任务计划启动第三次正式 ns-3 矩阵，不表示 512 条运行已经通过，也不表示 R2 数据可以发布。启动前必须在服务器现场同时满足以下条件：

1. 第二次失败输出是普通目录，且不是符号链接；
2. 唯一归档目标 `runs/ns3-data/r2-protocol-paired-v0.failed-attempt2-cubic-contract/` 事前不存在；
3. 原子归档后，固定正式输出根 `runs/ns3-data/r2-protocol-paired-v0/` 不存在；
4. 新启动目录 `runs/launchers/r2-ns3-protocol-matrix-v0-attempt3/` 事前不存在。

上述服务器状态未在本复审中核验。任一条件不满足时，attempt3 保持 `NO-GO`，不得删除、覆盖、合并或以恢复模式复用第二次失败输出。

## 发现

### 严重问题

无。

### 重要问题

无。

### 非阻断说明

1. 当前生成器仍保留一个 `ns3::TcpCubic` 字面量，但它只属于修复前随机分配域的冻结兼容常量，不会写入当前清单、运行参数或 C++ 运行身份。删除该常量反而会破坏“修复只改身份、不改种子与顺序”的合同。
2. 任务 01 的正式干净代码锁尚未闭合。因此 attempt3 结果仍须标记为 `review_pending`，R2 数据发布和模型训练继续保持 `NO-GO`。
3. 本复审遵守禁止连接服务器的边界。编译、真实 NewReno 身份、120 窗、双守恒和拥塞窗口覆盖只能由 attempt3 首个正式配对给出运行时证据。

## 1. 当前运行身份核验

当前生产合同的实际运行身份全部为 `ns3::TcpNewReno`：

- `configs/r2_ns3_protocol_matrix_v1.yaml` 第 109 行声明 `tcp_congestion_control: ns3::TcpNewReno`；当前文件 SHA-256 为 `0adcb49e52a1df156eddf4a3d01dfd51d00fa57752bcc0d04189073ace2edeeb`。
- 当前清单 512 条记录的 `tcp_congestion_control` 均为 `ns3::TcpNewReno`；没有记录携带 Cubic。
- `ns3/r2_protocol_queue_scenario.cc` 第 28 行把 CSV 身份固定为 `ns3::TcpNewReno`，第 787 至 788 行把 `TcpL4Protocol::SocketType` 固定为 `TcpNewReno::GetTypeId()`；场景 SHA-256 为 `8a6fbfdb88784c7f951ef880bbd223a1f5df041a56f4615d62b7589a60af76c5`。
- `src/flow_probe/r2_ns3_protocol_runner.py` 第 455 至 456 行与第 488 行要求 trace 合同和 C++ 场景均为 NewReno；第 638 至 643 行要求每个 CSV 的 `truth_tcp_congestion_control` 与冻结记录精确相等。
- 运行器第 510 至 547 行先硬校验当前清单 SHA-256、矩阵配置 SHA-256 和任务 01 合同 SHA-256，旧清单无法进入正式运行。

当前清单、运行器和受控参数的直接绑定一致：

| 制品 | SHA-256 |
| --- | --- |
| `ns3-config-manifest.jsonl` | `d867c05013ff9c566d965ec3115bcefe6c905cca69865b042eb81f56e012a111` |
| `r2_ns3_protocol_matrix_v1.yaml` | `0adcb49e52a1df156eddf4a3d01dfd51d00fa57752bcc0d04189073ace2edeeb` |
| `r2_protocol_data_v1.yaml` | `aa390129e239aa59d1c6963471e1268498a16740a5f11a916f489fa6a7292566` |
| `r2_ns3_protocol_runner.py` | `40a97ee063d2e846b7c5971d0498a886ac67a2b190676c750b16eeca1d3a7c8b` |
| `r2_ns3_protocol_matrix_runtime_v0.json` | `a32978154c4a5203e621bf2e8b8f2789b3777a104eff430b7dcf5b59810a6f05` |

## 2. 512 条清单逐条不变性核验

本复审没有仅采用任务 04R 报告中的结论，而是从当前清单独立重建修复前字节：逐条只把以下三个允许变化字段恢复为修复前登记值，其余字段、字段顺序和记录顺序完全保留：

- `matrix_config_sha256`：恢复为 `971e91659e6c1cc00b575823d384bfaf2975139cb022dd924a96ccc6dda22565`；
- `r2_contract_sha256`：恢复为 `0793d00a3b67a20960b32efb33c5a5e45cd5bae04d2e7bb24d5e7cd629c5a935`；
- `tcp_congestion_control`：恢复为 `ns3::TcpCubic`。

重建字节的 SHA-256 为 `a0efc42ed26c0e4bc2c1622f850f5ee61a20348f29693bafa8008108792be793`，与任务 04R 前由独立复审登记的旧清单 SHA-256 精确一致。这证明修复前后逐条差异集合确实只有上述三个字段，而不是仅由当前测试常量自行证明。

进一步核验结果：

- 记录数为 512，字段数均为 39，字段顺序全部相同；
- TCP 与 UDP 各 256 条；五个划分分别为 256、64、64、64、64 条运行；
- 256 个 `physics_group_sha256`，每组恰有一条 TCP 和一条 UDP，移除 `transport_family` 后两侧逐字段相同；
- 256 个 `run_seed` 与 256 个 `seed_basis_sha256` 均无组间碰撞；
- 奇数位和偶数位都同时包含 TCP 与 UDP；
- 排除三个允许变化字段后的顺序敏感投影 SHA-256 为 `3cef63f086db8d4ae07d57cf306105a394206701a2da829f9665f03183227a9e`；
- 当前运行种子序列 SHA-256 为 `30231475ae75c2be3242d28ffe5d91b46d25e358cee6f487550d5db7d15a42a0`；
- 当前种子基底序列 SHA-256 为 `97ceea9e2d46751122803fa7474daef4d123a92a327114d641f0f7a8cb663c27`；
- 当前配对组序列 SHA-256 为 `caa7789c9059acafe6e8caeab863d9c0f32ae40b726c6a7d8cf774b21362fedb`；
- 当前协议顺序序列 SHA-256 为 `b2409e52ed33d41957b1557c2d45cf1689309ba355b9bb19730ad20b1bb64bbc`。

当前矩阵配置只出现一次 NewReno 文本。将该文本恢复为 Cubic 后，配置字节 SHA-256 精确恢复为旧配置摘要 `971e91659e6c1cc00b575823d384bfaf2975139cb022dd924a96ccc6dda22565`。

## 3. 兼容归一化边界核验

兼容归一化没有掩盖当前合同哈希，也没有让旧身份进入运行：

1. `r2_ns3_protocol_matrix.py` 第 19 至 25 行显式保存旧矩阵哈希、旧共享合同哈希和旧 Cubic 文本，只作为修复前分配域。
2. 第 768 至 788 行只在复算 `seed_basis_sha256`、`run_seed` 和 `physics_group_sha256` 时使用这些旧值。
3. 第 839 至 889 行写入公开记录时使用当前配置对象中的当前矩阵哈希、当前共享合同哈希和 NewReno，兼容值不会进入记录。
4. 当前 512 条记录全部写入当前矩阵哈希 `0adcb49e…`、当前共享合同哈希 `aa390129…` 和 NewReno；运行器再以完整清单摘要和两个当前摘要作硬门禁。
5. 协议顺序仍由已保持不变的 `physics_group_sha256` 域分离决定，见生成器第 1030 至 1034 行。

因此，`seed_basis_sha256` 的语义是“修复前冻结分配域中的种子基底”，不是直接对当前记录原样取摘要。该语义已经在生成器注释和任务 04R 报告中显式记录；生成器源码、旧摘要与当前清单共同足以复现，不构成隐式哈希替换。

## 4. attempt2 归档与 attempt3 唯一启动

任务计划第 654 至 660 行和任务 05 报告第 87 至 93 行给出同一组唯一身份：

- 第二次失败源：`runs/ns3-data/r2-protocol-paired-v0/`；
- 唯一归档目标：`runs/ns3-data/r2-protocol-paired-v0.failed-attempt2-cubic-contract/`；
- 第三次唯一启动目录：`runs/launchers/r2-ns3-protocol-matrix-v0-attempt3/`；
- 第三次固定正式输出：重新创建的 `runs/ns3-data/r2-protocol-paired-v0/`；
- 受控参数固定 `resume=false`。

运行器第 1501 至 1511 行保证 `resume=false` 时正式输出根事前存在就失败，不会混入旧运行；第 1526 至 1535 行写入新的运行绑定与 trace 合同。只要启动器先执行本报告开头的四项服务器存在性检查，并以同文件系统原子重命名归档 attempt2，该步骤就是唯一且可逆的。不得把报告中的路径缩写为其他名称，也不得把 `resume` 临时改为 `true`。

## 5. 首个正式配对的运行时门禁

首个正式配对能够承担计划要求的五项门禁：

1. **编译和执行**：运行器第 1076 至 1118 行构造固定 `scratch/flow-probe-r2-protocol` 命令；第 1258 至 1293 行执行 `ns3 run`，编译或执行返回非零即写失败回执并停止该侧。
2. **NewReno 身份**：C++ 固定 NewReno 并写入 CSV；运行器逐窗与当前清单身份精确比较。
3. **120 个窗口**：C++ 固定 12 秒和 0.1 秒窗口；运行器第 917 至 918 行要求恰有 120 行。
4. **包与网络层字节双守恒**：运行器第 763 至 800 行分别独立复算字节残差与包残差，任一非零即失败。
5. **拥塞窗口覆盖**：C++ 在每个 TCP socket 上连接 `CongestionWindow`；运行器第 837 至 863 行核验适用性、连接发送者和数值边界，第 926 至 932 行要求 TCP 窗口覆盖率至少为 0.95。

运行器第 1577 至 1668 行在一个配对内依次执行两侧、聚合双侧错误，并在配对边界失败后停止矩阵。首个配对通过后只能说明首个参数组通过上述门禁；512 条矩阵、全部因子覆盖和最终配对完成率仍须以后续正式制品验收。

## 已执行的只读核验

- 对任务 04R/05R 白名单文件执行 SHA-256 核对；报告登记摘要与当前文件一致。
- 解析当前 512 条 JSONL，核对记录数、字段顺序、当前合同字段、协议数量、划分数量、配对同一性、种子唯一性和奇偶位协议分布。
- 从当前清单仅还原三个允许字段，重建修复前完整字节并与修复前独立登记摘要比较。
- 从当前矩阵配置仅还原拥塞控制文本并与修复前配置摘要比较。
- 只读检查生成器、运行器、C++ 场景、受控参数、Shell 包装器、直接绑定测试、任务计划和任务 04/05 报告。

## 未执行与未变更

- 未连接服务器，未核验 attempt2 当前远端目录、磁盘、进程、`screen` 或 attempt3 目录状态。
- 未运行格式化、Prettier、Ruff、Pyright、pytest、全量测试、模块导入、独立冒烟或 ns-3。
- 未修改任务 04R/05R 的生产代码、配置、清单、校验文件、测试、既有报告或运行制品。
- 本复审只新增本报告。

