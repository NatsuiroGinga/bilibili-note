# 任务 05R PPP 头修复独立复审

日期：2026-08-03  
结论：`存在重要问题`  
复审方式：只读静态审查与制品哈希核对；未修改生产实现，未运行格式化、Pyright、全量测试、独立冒烟或正式矩阵

## 发现

### 重要：任务 04 冻结拥塞控制与任务 05 场景互相矛盾

任务计划第 5.2 节和任务 05 最小行为均固定第一轮 TCP 为 `ns3::TcpNewReno`。任务 05 场景也在 `ns3/r2_protocol_queue_scenario.cc` 第 28 行声明 `ns3::TcpNewReno`，并在第 787 至 788 行把 `TcpL4Protocol::SocketType` 设置为 `TcpNewReno::GetTypeId()`；Python 源码审计器在 `src/flow_probe/r2_ns3_protocol_runner.py` 第 455 至 456 行和第 488 行绑定同一语义。

但是，任务 04 冻结配置 `configs/r2_ns3_protocol_matrix_v1.yaml` 第 109 行声明 `tcp_congestion_control: ns3::TcpCubic`，SHA-256 为 `971e91659e6c1cc00b575823d384bfaf2975139cb022dd924a96ccc6dda22565`；512 行冻结清单也逐行携带 `ns3::TcpCubic`，清单 SHA-256 为 `a0efc42ed26c0e4bc2c1622f850f5ee61a20348f29693bafa8008108792be793`。

运行时，C++ CSV 会写出 `ns3::TcpNewReno`，而 Python 运行器在第 638 至 643 行要求 `truth_tcp_congestion_control` 精确等于冻结清单中的 `ns3::TcpCubic`。因此首条正式运行即使完成编译和模拟，也会在 CSV 身份校验中必然失败，不能形成任何有效配对。

该冲突不应通过删除身份校验、改写 CSV、接受两种值或把场景临时切到 Cubic 来绕过。计划已经固定 NewReno，正确处理方式是另立明确的任务 04R：只把任务 04 配置中的拥塞控制修正为 NewReno，重新生成 256 组/512 条清单，并更新所有直接绑定的清单、矩阵配置、受控参数和运行器预期哈希；其余矩阵字段、标签、丢失率、种子、配对和输出合同必须保持不变。修复前的正式矩阵结果均不得视为有效。

## PPP 修复核对

未发现 PPP 修复本身的严重或重要问题：

1. `OnDownstreamErrorLoss` 使用 `PeekHeader(PppHeader&)` 返回的实际解析长度，不是固定盲减常量。
2. 回调先检查包长，再要求解析长度等于 `PppHeader::GetSerializedSize()`，并要求协议号为 IPv4 PPP `0x0021`；任一不满足都会中止。
3. 网络层丢失字节只累计 `packet->GetSize() - parsedPppHeaderBytes`，旧的整包累计表达式已不存在。
4. Python 审计器绑定了 ns-3.48 中 `PhyRxDrop` 位于错误分支、`ProcessHeader(packet, protocol)` 位于互斥成功分支的真实顺序，同时检查 `ProcessHeader` 的 `RemoveHeader`、PPP 序列化长度为 2、`Packet::PeekHeader` 的反序列化实现及场景显式扣除。
5. 本机 ns-3.48 原始源码进一步证明 `EtherToPpp(0x0800)` 返回 `0x0021`，`PppHeader::Deserialize` 返回实际序列化长度 2，`Packet::PeekHeader` 不移除头部。

## 哈希与不变性

- 修复后 C++ 场景：`8a6fbfdb88784c7f951ef880bbd223a1f5df041a56f4615d62b7589a60af76c5`
- 修复后 Python 运行器：`c3db006fb053a9fcc8b0efeaf5431181049bb71195b1fc8a731f6631b9ea26ac`
- 受控运行参数：`2c9784ac6aac960dc2a72f4917e8a474ee1ff53a76d5178f141d7f6a177e0b23`
- Shell 包装器：`61e54d85602263b8a53d0692b24ebc9e7504e368a9d9fa7e78f4b2d7045ba228`
- 任务 04 清单：`a0efc42ed26c0e4bc2c1622f850f5ee61a20348f29693bafa8008108792be793`
- 任务 04 清单校验文件：`43bbf0056d66fa6841285a18f426a895d645bd4762908b06e46a98ec4869f5ca`
- 任务 04 冻结配置：`971e91659e6c1cc00b575823d384bfaf2975139cb022dd924a96ccc6dda22565`

清单仍为 512 行，TCP/UDP 各 256 条，二分类标签各 256 条；丢失率计数仍为 `0.0` 216 条、`0.01` 232 条、`0.03` 44 条、`0.05` 20 条。第一次失败目录 `runs/launchers/r2-ns3-protocol-matrix-v0/` 仍保留，日志 SHA-256 仍为 `1a3a443e967f9a42bb3cd3c638d1fe92ec4028f646ba7967f66a5c77fcec1af5`；本地正式输出根 `runs/ns3-data/r2-protocol-paired-v0/` 不存在。

## 复审裁决

PPP 头修复可以保留，不需要因本复审重新设计。任务 05R 整体暂不能标记通过，因为任务 04 的 Cubic/NewReno 冲突会使正式矩阵必然失败。主线程已在发现后立即收到阻断通知；任务 04R 修正并重新绑定全部相关哈希前，不得把后续矩阵结果用于 R2 数据发布或论文结论。

