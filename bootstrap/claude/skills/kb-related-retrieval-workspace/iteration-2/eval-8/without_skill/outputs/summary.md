# 检索结果汇总：云主机探测 MCDN 的任务配置

> 检索方式：research-knowledge MCP（lexical 模式）+ Obsidian CLI 兜底 + 知识库文件直接读取
> 检索库：~/Dev/Research（bban-api / manba-bi）
> 检索时间：2026-08-27

## 结论优先

**知识库中有直接且高相关度的参考沉淀。** 核心有四篇：`mcdn-v-probe-task-system`（探测任务体系代码级拆解）、`mcdn-vod-probe-config-rollout`（246 台 mcdn-v 节点探测配置的批量灰度实战记录，与"云主机探测 mcdn 的任务配置"需求吻合度最高）、`bban-probe-task-api`（任务候选接口调用说明）、`mcdn-probe-prometheus-exporter`（探测结果转指标出口）。可直接作为新需求设计与落地的参考底座。

---

## 一、核心参考（直接命中，推荐优先阅读）

### 1. `bban-api/Knowledge/mcdn-v-probe-task-system.md` —— MCDN 探测任务体系

**一句话结论：** mcdn-v（视频云 MCDN）探测任务分三层：候选池由 `isMcdnVodProbeTarget`（IsMCDN + SID + service_type=="v"）构建，miner 实际任务由 `percentage` 确定性抽样产生，结果查询用独立的 `generateNodeProbeTaskForResult` 严格分派——读路径不容错、写路径降级。

关键内容对本需求的参考价值：

- **候选池构建与抽样下发**：
  - `GenerateProbeTaskForMinerNoded(ctx, percentage)`：percentage=0 返回空，=100 返回全部候选（`app/ba/app/admin/internal/service/probe.go:106-110`）
  - 候选池按节点类型短路分派：MCDN 走 `isMcdnVodProbeTarget`；非 MCDN 走 Idc 前缀"01"或 edge-live 前缀
  - 抽样是**确定性**的：`sort.Strings(allIds)` 后取前 `ceil(len*percentage/100)`，非随机
  - 下发路径对 Taishan service_type 查询失败降级（跳过 mcdn，ncdn 不受影响）
- **mcdn-v 目标判定链**（三步全命中）：`IsMCDN()`（id 前缀 "mcdn"）→ `GetMCDNSid()`（id 第 5 段，如 `mcdn-qny-gxnn-cu-1001` → `1001`）→ `serviceTypes[sid] == "v"`（点播）。service_type 取值集：`"v"`（点播）、`"live"`（直播）、`"bvcmix"`（混跑），只有 `"v"` 进探测候选池
- **执行方是云主机（miner），不是 mcdn 节点本身**：
  - mcdn-v 节点没有自探测入口（`GET /task` 条件 `fromIDC.IsNCDN() || CheckAbility("miner")` 对 mcdn-v 恒为 false）
  - 真正执行探测的是带 `miner` 能力的**云主机**，`Source` 字段记录 `MinerChannel`（如 `OSTALIWEST`/`OSTHWNORTH`/`OSTTXEAST`/`OSTTXSOUTH`），与 `TargetNodeID`（被探测的 mcdn 节点）分开记录
  - **`minerProbePercentage` 配置表里配了 8 台机器，全部是云主机命名格式**（如 `tx-bj-video-ost-miner-1` 腾讯云北京、`hw-sz-video-ost-miner-1` 华为云深圳、`ali-cd-video-ost-miner-1` 阿里云成都）——这就是"云主机探测 mcdn"中云主机侧的任务配置入口
- **六类探测方式**：ICMP/SNMP/TCP/Bandwidth 直连 `TargetIP`；HTTP 裸连配置的完整 URL（不读 TargetIP）；VodPlay/LivePlay 用 ffmpeg 拉流解码（唯一做真实媒体解码）。平台配置的 "vod 拨测" 是 bool 开关，URL 由 admin 经 Hebe `VodUrlGenerate` 现算
- **noded 执行链路**：`admin -- GET /v1/task --> noded -- 执行 --> 目标`；admin 负责筛选节点、读配置、生成 ProbeTasks、接收结果，本身不执行网络探测
- **候选池 ≠ 实际任务**：`GenerateProbeTaskForMinerNoded` 遍历的是 `BatchQueryProbeConfig` 查到的已配置记录，不是候选 ID 全集——"判定通过"只是有资格，还需平台人工配置过拨测项才有任务
- **发布影响**：mcdn 节点的 noded 连接 **prod admin**，只在 pre 发布新版 admin 不会生效，需 prod 发布
- **关联**：`bban-probe-task-api`、`bban-mcdn-probe-targets`、`mcdn-probe-prometheus-exporter`、`json-to-prometheus-textfile-workflow`、`et-bban-probe-design-docs`

### 2. `manba-bi/Knowledge/mcdn-vod-probe-config-rollout.md` —— MCDN 探测配置批量写入实战记录

**与"云主机探测 mcdn 的任务配置"需求吻合度最高**，是真实执行的探测配置灰度记录。

- **目标配置口径**（写入 probe-config 的字段）：
  ```text
  node_id=<BBAN id>  icmp=false  snmp=false  vod_play=true  live_play=false
  tcp_ports=[80,443] http_urls=[] bw_nics=[]
  ```
- **候选口径三层**（勿混）：page-node `tags=["vod-play"]` 全量 874（含 ncdn/ec）；其中 mcdn 前缀 246；schedule `vod-play.can=true` 242
- **接口与工具链**：
  - 读候选：`POST /api/bban2/v1/bban/page-node`（挂 /v1，必须带 request body 的签名）
  - 读写 probe-config：`/api/bban2/v0/probe-config`（无鉴权直连）
  - 脚本：`go-op/.claude/scripts/moni/mcdn_probe_config_batch.py`（`--node-file` + `--apply --opuser --yes`），固定种子 20260825 可复现
- **灰度实施**：三批（40/80/122 台），已配置一致 124/246，幂等（已正确的命中 SKIP）
- **zsh 长参数坑**：未加引号的 `$ARGS` 不做词分割，40 组 `--node` 变成单参数，须用 `--node-file` 文件传参
- **关联**：`mcdn-probe-prometheus-exporter`、`json-to-prometheus-textfile-workflow`、`bban-signature-body-coverage`、`bban-node-field-semantics`

### 3. `bban-api/Knowledge/bban-probe-task-api.md` —— 探测任务接口使用说明

- 查询目标是否进入候选探测池：应查询已签名的 SLB 接口 `/api/bban2/v1/all-probe-task`，精确匹配节点 ID；不要用 bvc-hub 代理 URL 重新签名
- 直连 SLB 时：`bvc-hub.bilibili.co` → `bvc-ost-oss.bilibili.co`，`api/ost-bban2` → `api/bban2/v1`；自动化脚本也可用无鉴权的 `/v0` 分组直连（`http://bvc-ost-oss.bilibili.co/api/bban2/v0/all-probe-task`）
- 命中 = 返回目标 IP 和 ICMP、SNMP、TCP、HTTP、带宽等探测配置；未命中不能说明节点不在系统内，依次检查节点筛选、人工探测配置、可用探测 IP
- **不要把候选池当作 miner 实际任务**：实际任务还受 `minerProbePercentage` 影响
- 关联：`bban-api-evidence`、`01-Plan`

### 4. `bban-api/Knowledge/bban-mcdn-probe-targets.md` —— MCDN 探测目标与配置约定

- mcdn 是否可被下发探测：先看北斗同步的 service_type（点播类用 `v`），再看人工探测配置和目标 IP；**不要根据主机名或 BA 节点 ID 字面形式自行判断**
- 配置键使用 BA 节点 ID，不能使用北斗主机名；配置由管理员手工维护，系统不会自动创建
- SID 无法解析、类型映射缺失、类型不匹配、无人工配置、无可用目标 IP 时，不进入候选任务；候选池不以在线/离线/实时状态作为额外判定
- **身份关联限制**：BBAN 与北斗资源以 SID 关联；同名重建而 SID 改变时，不能仅凭同一主机名视为同一身份

### 5. `bban-api/Knowledge/mcdn-probe-prometheus-exporter.md` —— 探测结果转 Prometheus 指标出口

- 三套独立体系勿混：A 探测任务结果（`all-probe-task`/`all-probe-result`，`mcdn_probe_*` 指标）；B 拨测 dialing（`bban2_dialing_*`）；C 跨运营商丢包（`mcdn_network_quality`）
- 脚本 `mcdn_probe.py` 用 textfile collector 部署（cron 每 1 分钟原子写 `.prom`），中心化查询 admin，不部署到每台节点
- 实测字段结构：`all-probe-result` 的 `tcp` 字段 key 是探测源 miner channel（`OSTALIWEST`/`OSTHWNORTH`/`OSTTXEAST`/`OSTTXSOUTH`），印证 `Source=MinerChannel`
- 踩坑记录：`target_node_id` 是 BBAN sid 风格 id，需脚本查 schedule 映射到 `instance_name`（hostname）；候选池数量≠实际任务数量（仅 1 台 mcdn 被配置过所以只有 1 条，设计如此）；bvc-hub 网关要登录态与 admin 内部签名鉴权是两层机制；响应是 `{code,message,ttl,data}` 包装；目标环境 Python 3.5 不能用新语法；单文件独立部署不能依赖仓库相对路径

---

## 二、间接相关（任务体系的周边知识，可作为扩展参考）

| 条目 | 所在库 | 与本需求关系 |
| --- | --- | --- |
| `bban-taishan-probe-mapping` | bban-api | 探测结果与 Taishan 存储映射 |
| `json-to-prometheus-textfile-workflow` | bban-api | 探测指标 textfile 导出工作流 |
| `et-bban-probe-design-docs` | bban-api | 探测任务设计文档（来源文档） |
| `bban-signature-body-coverage` | bban-api | 带 request body 的签名机制（批量写配置必需） |
| `bban-node-field-semantics` | bban-api | 节点字段语义 |
| `mcdn-cross-isp-packet-loss` | manba-bi | MCDN 跨 ISP 丢包（探测结果应用侧） |
| `mcdn-promql-monitoring` | manba-bi | MCDN PromQL 监控 |
| `mcdn-vod-forbidden-scheduling` | manba-bi | MCDN VOD 禁止调度 |
| `2026-08-17` / `2026-08-21` | bban-api/manba-bi Daily | 探测任务相关每日记录 |

---

## 三、检索过程中未命中的方向（可跳过）

- `云主机 探测 mcdn 任务配置`、`探测任务配置 协议 HTTP DNS`、`bban-probe-task-api 任务接口` 等词汇在 lexical 索引和 Obsidian CLI 中无直接命中（推测索引词为英文/代码标识符，如 probe-config、isMcdnVodProbeTarget 等）
- 通过 `knowledge_search("mcdn 探测任务")` 命中 00-Hub 与上述核心条目，再经 `knowledge_related`（depth=2）与文件直读补齐关联网络

---

## 四、对本新需求的落地建议（基于上述参考）

1. **任务配置模型**可直接复用 `ProbeConfig` 字段口径：`icmp / snmp / vod_play / live_play / tcp_ports / http_urls / bw_nics`，其中平台上的 "vod 拨测" 是 bool 开关，URL 由 admin 现算（Hebe `VodUrlGenerate`），HTTP 探测则直接配完整 URL
2. **候选与抽样**：参考 `GenerateProbeTaskForMinerNoded` + `percentage` 确定性抽样，注意"候选池 ≠ 实际任务"（实际受 `minerProbePercentage` 与是否人工配置过拨测项双重影响）
3. **云主机（miner）作为执行方**：参考 `minerProbePercentage` 配置表中 8 台云主机（`tx-bj-video-ost-miner-1` 等命名）与 `Source=MinerChannel` 的结果记录方式
4. **接口**：候选查询 `/api/bban2/v1/all-probe-task`（签名）；配置读写 `/api/bban2/v0/probe-config`（无鉴权）；候选读取 `POST /api/bban2/v1/bban/page-node`（需带 body 签名）
5. **灰度经验**：参考 `mcdn-vod-probe-config-rollout` 的三层候选口径、固定种子分批放量、幂等 SKIP 机制与 zsh `--node-file` 传参坑

---

## 附：Obsidian 跳转链接

- [mcdn-v-probe-task-system](obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system.md)
- [mcdn-vod-probe-config-rollout](obsidian://open?vault=Research&file=manba-bi/Knowledge/mcdn-vod-probe-config-rollout.md)
- [bban-probe-task-api](obsidian://open?vault=Research&file=bban-api/Knowledge/bban-probe-task-api.md)
- [bban-mcdn-probe-targets](obsidian://open?vault=Research&file=bban-api/Knowledge/bban-mcdn-probe-targets.md)
- [mcdn-probe-prometheus-exporter](obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-probe-prometheus-exporter.md)
- [bban-taishan-probe-mapping](obsidian://open?vault=Research&file=bban-api/Knowledge/bban-taishan-probe-mapping.md)
- [et-bban-probe-design-docs](obsidian://open?vault=Research&file=bban-api/Sources/Docs/et-bban-probe-design-docs.md)
- [bban-signature-body-coverage](obsidian://open?vault=Research&file=bban-api/Knowledge/bban-signature-body-coverage.md)
- [bban-node-field-semantics](obsidian://open?vault=Research&file=bban-api/Knowledge/bban-node-field-semantics.md)
