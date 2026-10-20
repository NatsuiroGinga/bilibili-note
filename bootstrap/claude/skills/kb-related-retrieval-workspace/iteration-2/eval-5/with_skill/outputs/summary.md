# 知识库关联检索总结

> 检索意图：给一台 mcdn 节点配置 HTTP 探测目标 `http://baidu.com` 后，探测由谁执行？是不是只有 mcdn 节点自己能测试能否访问到 baidu？
> 检索库：`~/Dev/Research`（Obsidian vault）→ `bban-api` 项目库
> 检索时间：2026-08-27

## 检索结果

- **HTTP/ICMP/TCP 探测的真实执行方（mcdn-v-probe-task-system）**（`bban-api/Knowledge/mcdn-v-probe-task-system.md`）
  - 摘要：直接回答"给 mcdn 节点配置 http 探测目标（如 baidu.com）后，到底是谁在发起这个 HTTP 请求"。2026-08-25 已用 noded 源码（`/Users/bilibili/Dev/bi`，`bvccdn-noded`）将结论从"强推断"坐实为**代码确证**：HTTP 探测由执行任务的探测方（miner 云主机）用标准库 `http.Client.Get()` 裸连配置的 URL，与 `TargetIP`（mcdn 节点 IP）完全无关。
  - 跳转：`obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system.md`

## 回答用户问题（核心结论）

**不是"只有 mcdn 自己能测"，恰恰相反：mcdn 节点自己既不能测、也没机会测，真正发起 HTTP 请求的是 miner。**

具体链条（均为代码确证）：

1. **执行方是 miner，不是被配置的 mcdn 节点**
   - noded（部署在 CDN 节点机的常驻代理）里 HTTP 探测的 `generateHTTPEtorCfg` 只把 `pt.HTTP`（完整 URL 列表，如 `http://baidu.com`）传给 `http.PingExecutorCfg`，不含 `TargetIP`。
   - 真正发请求的是 `library/http/ping_executor.go` 的 `pingAddr`：`hc.Get(rAddr)`，标准库 `http.Client.Get` 直接 GET 配置的 URL，无自定义 Transport / DialContext / Host 绑定，`TargetIP` 在整条链路从未被读取。
   - 交叉验证：ICMP/SNMP/TCP/Bandwidth 四类探测都把 `RemoteAddr` 设为 `pt.TargetIP`，唯独 HTTP/VodPlay/LivePlay 用各自独立的 URL 列表——这是系统性设计区分，不是遗漏。
   - 所以"访问 baidu.com"实际发生在**执行该任务的 miner（云主机，如 `tx-bj-video-ost-miner-1`）自己的网络出口**，测的是"miner 到 baidu 的可达性"，与这台 mcdn 节点到 baidu 的连通性无关。

2. **mcdn 节点为什么自己测不了（两个独立原因锁死）**
   - 原因一（无入口）：`GET /task` 生成自探测任务的条件是 `fromIDC.IsNCDN() || fromNode.CheckAbility("miner")`。mcdn 节点的 Idc 全部以 `03` 开头（非 `01`，`IsNCDN()` 为 false），且 254 个 mcdn-v 节点 0 个带 `miner` 能力，两个条件恒为 false，`ProbeTasks` 根本不会被赋值。
   - 原因二（实现本身不读 TargetIP）：即便进了探测路径，HTTP 探测也是裸连 URL，不读 mcdn 节点 IP。

3. **结果归属记录**
   - 结果会被打上这台 mcdn 节点的 `TargetNodeID` 标签存储，但 `Source` 字段记录的是真正执行探测的 miner 渠道（如 `OSTHWEAST`），两者是不同维度、分开记录。

补充：VodPlay/LivePlay 是唯一动用外部进程（ffmpeg 拉流解码）的探测类型，且其 URL 由 admin 用节点 nodeId 现算（如 `{nodeId}.bilivideo.com`），意图指向该节点——与 HTTP 探测配置任意第三方域名在语义上本质不同，尽管执行层同为"裸连 URL、不读 TargetIP"。

## 关联文档

- 出链（该条目引用谁）：
  - `bban-api/Knowledge/bban-probe-task-api.md` ×1
  - `bban-api/Knowledge/bban-mcdn-probe-targets.md` ×1
  - `bban-api/Sources/Docs/et-bban-probe-design-docs.md` ×1
  - `bban-api/Knowledge/mcdn-probe-prometheus-exporter.md` ×1
  - `bban-api/Knowledge/json-to-prometheus-textfile-workflow.md` ×1
- 入链（谁引用它）：
  - `bban-api/00-Hub.md`、`bban-api/02-Index.md`、`bban-api/01-Plan.md`、`bban-api/_system/registry.md`（导航/索引文件，降权）
  - `bban-api/Daily/2026-08-17.md` ×1
  - `bban-api/Knowledge/bban-node-status-silent-success.md` ×1
  - `bban-api/Knowledge/mcdn-probe-prometheus-exporter.md` ×1
  - `bban-api/Knowledge/bban-node-field-semantics.md` ×1
  - `bban-api/Knowledge/bban-mcdn-probe-targets.md` ×1
  - `bban-api/Knowledge/json-to-prometheus-textfile-workflow.md` ×1
  - `bban-api/Knowledge/bban-taishan-probe-mapping.md` ×1
  - `bban-api/Sources/Docs/et-bban-probe-design-docs.md` ×1

## 图谱提示

可在 Obsidian Graph View 查看可视化图谱：打开 `~/Dev/Research` vault，点击左侧图谱图标，聚焦 `mcdn-v-probe-task-system` 即可看到它与 `bban-probe-task-api`、`bban-mcdn-probe-targets`、`bban-taishan-probe-mapping`、`mcdn-probe-prometheus-exporter` 等条目的互相关联。图谱 canvas 入口：`bban-api/Maps/bban-api-knowledge.canvas`。

## 检索备注

- lexical 模式（FTS5）对中文多词查询返回为空；改用 `mode="semantic"` 命中质量显著（score 0.92），符合 SKILL.md 中"中文语义检索效果最佳"的说明。首次语义调用已加载 E5 模型。
- 检索词 `HTTP ICMP TCP 探测真实执行方 mcdn miner`（scope=bban-api）直接命中目标条目。
