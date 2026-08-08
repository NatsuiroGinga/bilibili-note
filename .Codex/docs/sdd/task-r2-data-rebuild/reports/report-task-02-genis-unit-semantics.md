# R2 任务 02：GeNIS 四字段单位、缩放与聚合语义审计

日期：2026-08-01

## 1. 结论

本报告中的 `GO` 仅表示字段语义已经足以驱动实现，不表示 R2 数据集已经允许发布或训练。现有合同要求四项同时通过，因此最终状态仍是 **`NO-GO`**。

| 字段 | 字段语义裁决 | 原始单位 | 规范换算 | 聚合语义摘要 | 对 R2 的直接影响 |
| --- | --- | --- | --- | --- | --- |
| `TotBytes` | **`NO-GO`** | 与抓包链路类型相关的 Argus 包长度总和 | 未批准 | 源、目的两个方向逐包长度求和 | 与冻结的“网络层字节”合同未统一，继续阻塞全部 R2 训练 |
| `TcpRtt` | **`GO`，仅字段语义级** | 秒 | `tcp_rtt_ms = TcpRtt * 1000` | TCP 建连 `SynAck + AckDat`；不是流内全部数据包的平均往返时间 | 可实现，但当前校验器单位判断错误，且总门禁仍被 `TotBytes` 阻塞 |
| `SrcWin` | **`GO`，仅字段语义级** | 字节 | 原值，要求数值可精确转为整数 | 源方向最近一次保留的非零 TCP 通告窗口，输出时应用窗口缩放 | 可作为 TCP 路由或审计观测，不能作为 `cwnd` 真值 |
| `DstWin` | **`GO`，仅字段语义级** | 字节 | 原值，要求数值可精确转为整数 | 目的方向最近一次保留的非零 TCP 通告窗口，输出时应用窗口缩放 | 可作为 TCP 路由或审计观测，不能作为 `cwnd` 真值 |

**最终裁决：四字段总门禁保持 `NO-GO`。不得启动 R2 最终双构建或训练。**

## 2. 审计边界

本轮只核对以下证据：

1. GeNIS 官方论文、官方字段字典和服务器只读官方流归档。
2. HERA 作者公开的生成期实现。
3. OpenArgus 官方传感器与客户端实现。
4. 一个官方 10 秒 TCP 成员的只读汇总，用于核对实现与实际输出是否矛盾。

本轮没有读取本机历史损坏的 `2-flows.zip`，没有修改任务 03，没有生成包级重算器，也没有把经验相关性当作字段语义证据。

## 3. 证据锁

### 3.1 GeNIS 官方原件

| 制品 | 标识 | SHA-256 | 用途 |
| --- | --- | --- | --- |
| GeNIS 论文 PDF | `raw/papers/1-s2.0-S2352340925002197-main (2).pdf` | `58d2180a12b7e89739d384c0b27a4f1af3904213e67a483c43edf64049f76ad5` | 证明 HERA 以 5、10、30、60 秒间隔生成流 |
| GeNIS 官方字段字典 | `raw/datasets/GeNIS-2025/0-info.zip` | `7ef636cc758586f18a5d9958e68eede9b85925610331283cce802f45542701bc` | 字段角色与字段间关系 |
| GeNIS 官方流归档 | `zenodo:14919237/2-flows.zip` | `72033b5e3df6e45cda9a339985194d8232c437c243a5037a62ebeff457489b30` | 实际输出 |
| 代表性 TCP 成员 | `zenodo:14919237/2-flows.zip!/2-flows/flows-10-sec/attack-bruteforce-ftp.csv` | `5efb91f4b4befa847bb8ef166f464fca526a942e4e0b6ea02a26c4dfd9b9e25e` | 实际字段格式和代数关系 |

官方字典只给出：

- `TotBytes`：总事务字节数。
- `TcpRtt`：TCP 建连往返时间，为 `SynAck + AckDat`。
- `SrcWin`、`DstWin`：源、目的 TCP 窗口通告。

字典没有声明这四项的精确单位、窗口缩放方式或跨记录聚合方式，因此字典不能单独放行。

### 3.2 HERA 作者公开实现

生成期公开提交固定为 [`c3b586f61ae60411f89c99604c24042969e91c44`](https://github.com/danielaapp/HERA/tree/c3b586f61ae60411f89c99604c24042969e91c44)，提交日期为 2024-10-26。

| 文件 | SHA-256 | 关键事实 |
| --- | --- | --- |
| `Makefile` | `a8fe63d7a51ad96f014ebaf172245dab1fe47612298b233b5f47f53ce5b8cca9` | 使用 Ubuntu `argus-server` 与 `argus-client` 软件包，但未固定包版本 |
| `hera.ipynb` | `d62bee6b42cfbc90d9a1aa3aee5626c78966fd18a1058bd9b0dc4e15272a463d` | 调用 `argus -S <秒> ... -r <pcap> -w <hera>`；随后调用 `ra` 或 `racluster` 直接打印字段 |
| `utils.py` | `3800a394588dc69ee7d4588fd27e8f0cf83a63c5be49e9bfa057c1dd9be32aa6` | 将 `bytes`、`tcprtt`、`swin`、`dwin` 直接列为 Argus 字段 |

HERA 的 CSV 路径没有对这四个字段做二次单位换算。`-u` 只把绝对时间戳打印为 Unix 秒，不改变 `TcpRtt`。

HERA 允许选择 `ra` 或 `racluster`。公开界面的默认首项是 `ra`。GeNIS 论文所述“长流按给定秒数持续产生更新”与 `ra` 保留 Argus 状态记录一致；`racluster` 官方手册则声明默认会合并同一流和探针的状态记录。代表性 GeNIS 成员中 3,344 行的 `Trans` 全为 `1`，同时有 361 行重复 `FlowID`，与未做客户端二次聚合的 `ra` 输出一致。

GeNIS 没有随数据发布实际运行时的 HERA 配置、客户端选择回执或 Argus 软件包版本。该缺口影响逐位重现和来源锁完整性，但不改变下述由 Argus 实现直接确定的单位与字段角色。

### 3.3 OpenArgus 官方实现

传感器源码固定为 [`openargus/argus` 的 `v3.0.8.4`](https://github.com/openargus/argus/tree/v3.0.8.4)，提交 `4de1ed766560e584b5331265a6bb70b44a289eaa`。

| 文件 | SHA-256 | 关键位置 |
| --- | --- | --- |
| `argus/ArgusModeler.c` | `954050847574c321145f18b9349961715d322f6849d209c8873c1576dd6fa74c` | `ArgusThisBytes = length`；`metric.*.bytes += ArgusThisBytes` |
| `argus/ArgusSource.c` | `fc41449ab16a00ac12c54fd964dc745222f3e872b902b21598cd6ce334bf0124` | 以太网路径把 `pcap_pkthdr.len` 原样传给 `ArgusProcessPacket` |
| `argus/ArgusUtil.c` | `29b6a92de9792debb8c162f898baa78d61a9a0754c72ac4f9f65ed6e84335a24` | 状态记录清零时保留 TCP 握手时间、窗口和窗口缩放状态 |
| `argus/ArgusTcp.c` | `4630821996d4c0709ca7116ca4cc7c552b8a95843c066d40efb8d29e67211e6d` | 握手时间以微秒保存；窗口取 TCP 头通告值并解析 `WSCALE` |

客户端源码固定为 [`openargus/clients` 的 `v3.0.8.4`](https://github.com/openargus/clients/tree/v3.0.8.4)，提交 `04688538a0d0f5ecc466ba84b2882b98a46072d2`。

| 文件 | SHA-256 | 关键位置 |
| --- | --- | --- |
| `common/argus_client.c` | `8a2b9e3fa790fc7acba51d281159f9c9f461ed8a042f33500028a7b1337075e5` | `TcpRtt` 求和后除以 `1,000,000`；聚合时保留首个非零握手时间并取后到记录窗口 |
| `common/argus_util.c` | `8fd47e58ceebffbe6be21043dfe9f7b448eeb3d2f31189377cffa062e498d53e` | `TotBytes = src.bytes + dst.bytes`；窗口输出为 `win << winshift` |
| `man/man1/ra.1` | `9e803b58868c0eff9b34100e6ad1c410f06d6809d981b93d3f9f95ee13ed4ce8` | 官方字段定义与 `-u` 含义 |
| `man/man1/racluster.1` | `05c088f637a4662b7b622d54418242837ea9ea4a5022a5c02898c2e5785a4d34` | 默认合并同一流状态记录 |

HERA 没有固定安装版本，因此上述 `v3.0.8.4` 是同一官方 3.0.8 系列的一手参考实现，不冒充 GeNIS 机器上的逐位相同二进制。

## 4. 字段裁决

### 4.1 `TotBytes`：`NO-GO`

#### 实现语义

客户端打印：

```text
TotBytes = metric.src.bytes + metric.dst.bytes
```

传感器对每个方向执行：

```text
metric.direction.bytes += ArgusThisBytes
```

`ArgusThisBytes` 取传给包处理器的 `length`。在以太网抓包路径中，该值来自 `pcap_pkthdr.len`，并在解析以太网头之前保存。因此该字段是 **Argus 输入包长度的方向总和**，字节层级随抓包链路类型变化。对于以太网输入，它不是由 IPv4 `total_length` 或 IPv6 `40 + payload_length` 重算的纯网络层字节。

#### 缩放与聚合

- 输出缩放因子：`1`。
- 行内聚合：源、目的两个方向逐包长度相加。
- 若经过 `racluster`：度量对象仍执行加法，不改变字节层级。
- 代表性成员 3,344 行全部满足 `TotBytes = SrcBytes + DstBytes`，但这只能确认字段代数关系，不能证明网络层口径。

#### 裁决理由

R2 冻结合同要求 `TotBytes` 与 TQH-C2、ns-3 的网络层字节完全同口径，并要求对冻结候选逐行精确整数匹配。当前服务器没有 `1-packets.zip`，也没有 PCAPNG 接口描述块、链路类型和逐包复算制品。HERA 一手实现没有证明网络层口径，反而显示该口径依赖输入链路类型。

因此：

- `unit = network_layer_bytes`：**未证明**。
- `semantic_role = network_layer_byte_sum`：**未证明**。
- 冻结候选逐行精确比较：**未执行**。
- 字段裁决：**`NO-GO`**。

#### R2 训练影响

`TotBytes` 参与共同 8 字段中的总字节、平均包长和字节速率口径。未统一时，模型可以学习数据源或链路层开销，而不是恶意流量规律。现有合同不允许用缺失掩码绕过该 P0 门禁，因此 R2 训练必须停止。

### 4.2 `TcpRtt`：语义级 `GO`

#### 实现语义

传感器分别记录：

```text
synAckuSecs = time(SYN_ACK) - time(SYN)
ackDatauSecs = time(ACK) - time(SYN_ACK)
```

客户端执行：

```text
TcpRtt = (synAckuSecs + ackDatauSecs) / 1_000_000
```

因此 GeNIS CSV 的原始 `TcpRtt` 单位是 **秒**，不是毫秒。它表示连接建立阶段的握手往返时间，不是连接持续期间的平均数据 RTT。

#### 缩放与聚合

- 规范字段：`tcp_rtt_ms`。
- 规范换算：`tcp_rtt_ms = TcpRtt * 1000.0`。
- Argus 状态记录切分时不清除握手时间，因此同一连接的后续状态记录可以重复携带同一握手值。
- 若使用 `racluster`，合并逻辑分别保留首个非零 `synAckuSecs` 与 `ackDatauSecs`，不是均值、最大值或跨连接求和。
- 原始值为空或 `0.0` 时，无法区分未完成握手和时间分辨率下的零值，应物化为空并设置缺失掩码，不能把 `0 ms` 当作有效测量。

#### 原件核对

代表性 10 秒 TCP 成员共 3,344 行：

- 3,344 行都满足十进制精确关系 `TcpRtt = SynAck + AckDat`。
- `TcpRtt` 范围为 `0.0` 到 `0.005492` 秒。
- 41 行为 `0.0`，应按缺失语义处理。

该核对只用于确认官方数据没有反驳一手实现，不替代实现证据。

#### R2 训练影响

字段语义、原始单位、换算和聚合规则已经闭合，可进入后续证据清单。但当前生产代码仍把全部值写空，且校验器要求 `unit == "milliseconds"`。在 `TotBytes` 放行前不应单独改写生产物化路径；最终修改时必须把原始单位登记为秒并执行乘 `1000` 的显式换算。

### 4.3 `SrcWin`：语义级 `GO`

#### 实现语义

Argus 从源方向 TCP 头读取 16 位窗口字段，并从 TCP `WSCALE` 选项保存 `winshift`。客户端输出：

```text
SrcWin = tcp.src.win << tcp.src.winshift
```

输出单位为 **字节**。传感器在正常数据包上只用非零窗口更新保存值，因此字段通常表示源方向在当前记录结束前最近一次保留的非零通告接收窗口。它不是发送端拥塞窗口，也不是记录内窗口的均值、最小值或最大值。

#### 缩放与聚合

- 内部缩放：`raw_16bit_window * 2^winshift`。
- CSV 到规范字段的额外缩放因子：`1`。
- HERA 经 Pandas 写出时可能表现为 `64256.0`；只接受可精确转为整数的值，禁止四舍五入小数。
- 状态记录切分保留上一窗口；若该方向在新记录中有包，最后一次非零通告覆盖旧值。
- 若使用 `racluster`，合并代码取后到记录的窗口值，不做统计平均。
- TCP 零窗口不会稳定地作为“当前窗口为零”传播，因为正常更新路径保留旧的非零值。该字段不能用于检测零窗口持续时间。

#### 原件核对

代表性成员 3,344 行均有 `SrcWin = 64256.0`，全部可以无损转为整数。该值与 `win << winshift` 的实现形式一致，但数值分布本身不承担语义证明。

#### R2 训练影响

该字段可以作为 TCP 适用的路由或审计观测，但存在终端协议栈指纹捷径风险。若进入模型，必须保留 `src_window_bytes_applicable` 与缺失掩码，并设置按协议分层和字段置换审计。它永远不能替代 ns-3 `cwnd` 真值。

### 4.4 `DstWin`：语义级 `GO`

#### 实现语义

目的方向与源方向完全对称：

```text
DstWin = tcp.dst.win << tcp.dst.winshift
```

输出单位为 **字节**，表示目的方向最近一次保留的非零 TCP 通告接收窗口，不是 `cwnd`。

#### 缩放与聚合

- 内部缩放：`raw_16bit_window * 2^winshift`。
- CSV 到规范字段的额外缩放因子：`1`。
- 只接受可精确转为整数的 CSV 数值。
- 状态记录与 `racluster` 的保留、覆盖规则和 `SrcWin` 相同。
- 零窗口限制与 `SrcWin` 相同。

#### 原件核对

代表性成员 3,344 行均有 `DstWin = 29056.0`，全部可以无损转为整数。

#### R2 训练影响

用途和风险与 `SrcWin` 相同。必须保持 TCP 适用性掩码，进行终端指纹捷径审计，且不得解释为拥塞控制内部状态。

## 5. 当前生产代码差距

本轮没有修改 `thesis/experiments/llm_probe/src/flow_probe/r2_protocol_genis.py`。当前代码继续保持安全失败：

1. `tcp_rtt_ms`、`src_window_bytes`、`dst_window_bytes` 全部写空。
2. `semantic_gate_status` 固定为 `NO-GO`。
3. `validate_genis_units()` 对 `TcpRtt` 强制要求原始 `unit == "milliseconds"`，与 Argus 一手实现不符。
4. `TotBytes` 仍要求网络层逐包精确比较，当前没有伪造通过。

待 `TotBytes` 证据闭合后，生产修改应保持最小范围：

1. 将 `TcpRtt` 证据模型区分为原始单位 `seconds` 与规范单位 `milliseconds`，固定换算因子 `1000.0`。
2. 对 TCP 且 `TcpRtt > 0` 的行物化 `tcp_rtt_ms`；空值和零值保持缺失。
3. 对 TCP 窗口接受空值或可精确转为非负整数的值，拒绝非整数小数和负数。
4. 在四字段全部通过前继续禁止把三项 TCP 字段单独发布为规范 R2 视图。

## 6. 解锁 `TotBytes` 的最小动作

1. 从 Zenodo 记录 `14919237` 取得官方 `1-packets.zip`，严格核对精确大小 `1028741083` 字节、官方 MD5 `5afbceaadfe3c3476f54723434d59b4a` 和新计算的 SHA-256。
2. 读取 PCAPNG 接口描述块并锁定每个成员的链路类型，不得默认所有成员都是以太网。
3. 按用户约束使用 Rust 实现完整包级重算器。IPv4 采用 `total_length`，IPv6 采用 `40 + payload_length`，并明确处理分片、截断包、多接口和异常包。
4. 复现 HERA 的方向、五元组、10 秒状态切分和精确候选连接，只比较冻结的 3,973 条 GeNIS 候选。
5. 对每条候选登记源包制品 SHA-256、算法版本、比较行数和精确整数匹配数。只有 `exact_integer_matches == compared_rows` 才能把 `TotBytes` 标为 `GO`。
6. 若不全等，不得调整容差。应在用户批准后选择重新从包构造 GeNIS 网络层字节、修改共同字段合同或排除该字段；当前合同下继续 `NO-GO`。

建议同时向 GeNIS/HERA 作者索取生成时的 HERA 配置、`ra` 或 `racluster` 选择、`argus --version`、`ra --version` 和系统软件包回执。这是来源锁和逐位重现所需的最小外部材料。

## 7. 验证与未执行事项

- 已只读核对服务器官方流归档存在；服务器没有 `1-packets.zip`。
- 已只读核对代表性 10 秒 TCP 成员的 3,344 行字段关系和整数可表示性。
- 已计算并登记所有引用源码文件和代表性数据成员的 SHA-256。
- 按本轮用户约束，未运行格式化、静态检查、测试、语法树检查、独立冒烟或重复校验。
- 未修改任务 03、冻结候选、服务器数据或任何运行制品。
