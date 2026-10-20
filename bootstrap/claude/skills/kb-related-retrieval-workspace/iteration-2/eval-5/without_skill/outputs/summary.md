# 检索结果汇总：MCDN 配置 http=baidu.com 后 miner 如何探测

## 结论优先

发起 HTTP 探测的不是 mcdn 节点自己，而是**执行该任务的 miner 云主机 noded**。miner 用标准库 `http.Client.Get()` 从它自己的网络出口直接访问配置里的完整 URL（如 `http://baidu.com`），测的是"**执行方到百度的可达性**"，与 mcdn 节点的 `TargetIP` 毫无关系。

## 为什么不是 mcdn 节点自己测

两个独立原因共同锁死这个结论（代码确证）：

1. **mcdn-v 节点没有自探测入口**：`GET /task` 生成自探测 `ProbeTasks` 的条件是 `fromIDC.IsNCDN() || fromNode.CheckAbility("miner")`。实测 254 个 mcdn 节点 Idc 全部以 `03` 开头（非 `01` 前缀的 NCDN），且 0 个带 miner 能力，条件恒为 false——节点连自探测的代码路径都进不去。
2. **HTTP 探测实现本身不读 `TargetIP`**：noded 的 `generateHTTPEtorCfg` 只传 `pt.HTTP`（URL 列表），`pingAddr` 用 `http.Client.Get(rAddr)` 裸连配置的完整 URL，无自定义 Transport、无 Host 绑定、无 DialContext 覆盖。ICMP/SNMP/TCP/Bandwidth 才用 `pt.TargetIP`，HTTP 是系统性设计区分。

## miner 执行的具体链路

```text
admin -- GET /v1/task --> noded(miner 云主机) -- http.Client.Get("http://baidu.com") --> baidu.com
noded -- POST /v1/taskresult --> admin --> Redis / Taishan
```

- admin 只负责筛选节点、读取配置、生成 `ProbeTasks`、接收并存储结果，**本身不执行网络探测**。
- 有 miner 能力的 noded（云主机，如 `tx-bj-video-ost-miner-1`、`hw-sz-video-ost-miner-1`）从节点所在网络领取批量目标任务并执行探测。
- 结果以 `(TargetNodeID, url)` 为 key 存储，`TargetNodeID` 打上这台 mcdn 节点的标签，但 `Source` 字段记录真正执行探测的 miner 渠道（如 `OSTHWEAST`），两者是不同网络位置。

## 与候选池/抽样相关（附带）

- 候选任务通过 `/api/bban2/v1/all-probe-task` 查看并精确匹配节点 ID；单台 miner 实际获得的任务还受 `minerProbePercentage` 确定性抽样影响，候选池 ≠ miner 实际任务。
- mcdn 节点要进候选池，需满足：IsMCDN（节点 ID 前缀 `mcdn`）+ SID 可解析 + 北斗同步的 `service_type == "v"` + 有人工探测配置。

## 来源条目

- `bban-api/Knowledge/mcdn-v-probe-task-system.md`（主要来源，2026-08-25 已用 noded 源码确证）
- `bban-api/Knowledge/bban-mcdn-probe-targets.md`
- `bban-api/Knowledge/bban-probe-task-api.md`
- Obsidian 跳转：`obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system.md`
