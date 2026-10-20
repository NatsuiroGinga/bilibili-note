# 知识库检索：MCDN 探测相关文档及关联

> 检索时间：2026-08-27；知识库：`~/Dev/Research`（Obsidian vault：Research）；索引 39 个文件
> 方法：`knowledge_search`（lexical）初检无命中后降级为直接遍历知识库目录 + wikilink 反查（rg），命中核心条目 5 个，关联条目 8 个（Knowledge/ 下）

## 检索结果（命中文档）

### 核心命中（bban-api/Knowledge/，MCDN 探测主链 5 篇）

1. **mcdn-v 探测任务体系**（`bban-api/Knowledge/mcdn-v-probe-task-system.md`）
   - 摘要：MCDN 探测任务三层架构——候选池由 `isMcdnVodProbeTarget`（IsMCDN + SID + service_type=="v"）构建，miner 实际任务按 `percentage` 确定性抽样，结果查询用独立分派严格容错（读路径不容错、写路径降级）。含六类探测方式全景对比（ICMP/SNMP/TCP/Bandwidth 直连 TargetIP，HTTP/VodPlay/LivePlay 裸连 URL），noded 源码级确证（2026-08-27 更新）。
   - 跳转：[obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system](obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system)

2. **BBAN 中 mcdn 探测目标与配置**（`bban-api/Knowledge/bban-mcdn-probe-targets.md`）
   - 摘要：mcdn 是否可被下发探测，先看北斗同步的 service_type（点播用 "v"），再看人工探测配置和目标 IP；不要按主机名或节点 ID 字面形式自行判断。候选池不以在线/离线状态为判定条件。
   - 跳转：[obsidian://open?vault=Research&file=bban-api/Knowledge/bban-mcdn-probe-targets](obsidian://open?vault=Research&file=bban-api/Knowledge/bban-mcdn-probe-targets)

3. **MCDN 探测结果转 Prometheus**（`bban-api/Knowledge/mcdn-probe-prometheus-exporter.md`）
   - 摘要："MCDN 质量监控"在 BBAN 生态是三套独立体系（A 探测任务结果 / B 拨测 dialing / C 跨运营商丢包率），命名相似但数据源、存储、Prometheus 出口完全不同；记录体系 A 补出口的 `mcdn_probe.py` 全流程（textfile collector 部署、七个踩坑、指标 schema）。
   - 跳转：[obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-probe-prometheus-exporter](obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-probe-prometheus-exporter)

4. **BBAN 探测任务接口使用说明**（`bban-api/Knowledge/bban-probe-task-api.md`）
   - 摘要：查看目标是否进入候选探测池应查询已签名 SLB 接口 `/api/bban2/v1/all-probe-task` 并精确匹配节点 ID；不要用 bvc-hub 代理 URL 重新签名。命中只证明进入候选池，实际任务还受 `minerProbePercentage` 影响。
   - 跳转：[obsidian://open?vault=Research&file=bban-api/Knowledge/bban-probe-task-api](obsidian://open?vault=Research&file=bban-api/Knowledge/bban-probe-task-api)

5. **泰山 service_type 映射在 mcdn-v 探测中的使用**（`bban-api/Knowledge/bban-taishan-probe-mapping.md`）
   - 摘要：BA 通过泰山 `SID → service_type` 映射识别 mcdn-v，任务生成与结果查询必须复用同一判定；映射缺失/读取失败时跳过受影响 mcdn，ncdn 继续。含存储分布（Taishan/Redis 开关）、Taishan SCAN 查询方法。
   - 跳转：[obsidian://open?vault=Research&file=bban-api/Knowledge/bban-taishan-probe-mapping](obsidian://open?vault=Research&file=bban-api/Knowledge/bban-taishan-probe-mapping)

### 关联命中（其余库，MCDN 主题扩展）

6. **MCDN 全量 mcdn-v 节点批量配置质量探测：灰度实施记录**（`manba-bi/Knowledge/mcdn-vod-probe-config-rollout.md`）
   - 摘要：`mcdn_probe_config_batch.py` 为 246 台 mcdn-v 节点统一写拨测配置（icmp=false, vod_play=true, tcp=[80,443]），三批灰度放量，当前 44/246 已一致（2026-08-27）；产出经 mcdn_probe.py 变 `mcdn_probe_*` 指标。
   - 跳转：[obsidian://open?vault=Research&file=manba-bi/Knowledge/mcdn-vod-probe-config-rollout](obsidian://open?vault=Research&file=manba-bi/Knowledge/mcdn-vod-probe-config-rollout)

7. **MCDN 跨运营商丢包率（体系 C）**（`manba-bi/Knowledge/mcdn-cross-isp-packet-loss.md`）— 节点自身 exporter，`mcdn_network_quality` 指标；跳转：[obsidian://open?vault=Research&file=manba-bi/Knowledge/mcdn-cross-isp-packet-loss](obsidian://open?vault=Research&file=manba-bi/Knowledge/mcdn-cross-isp-packet-loss)

8. **MCDN PromQL 监控**（`manba-bi/Knowledge/mcdn-promql-monitoring.md`）— 体系 C 的 PromQL 查询层；跳转：[obsidian://open?vault=Research&file=manba-bi/Knowledge/mcdn-promql-monitoring](obsidian://open?vault=Research&file=manba-bi/Knowledge/mcdn-promql-monitoring)

## 关联文档（wikilink 出链/入链）

### 出链（核心文档引用谁，跨库归并）

- `Sources/Docs/et-bban-probe-design-docs`（探测设计文档源，mcdn-v-probe-task-system、bban-mcdn-probe-targets 引用）×2
- `Sources/Docs/bban-api-evidence`（接口证据，bban-probe-task-api 引用）×1
- `Knowledge/json-to-prometheus-textfile-workflow`（textfile 工作流，mcdn-v-probe-task-system、mcdn-probe-prometheus-exporter 引用）×2
- `Knowledge/bban-probe-task-api`、`Knowledge/bban-mcdn-probe-targets`（核心条目互链）×2
- `manba-bi/Knowledge/mcdn-cross-isp-packet-loss`、`manba-bi/Knowledge/mcdn-promql-monitoring`（mcdn-probe-prometheus-exporter 引用，体系 C）×2
- `bban-api/01-Plan`（bban-probe-task-api 引用）×1

### 入链（谁引用核心探测文档）

- `manba-bi/Knowledge/mcdn-vod-probe-config-rollout`（引用 mcdn-probe-prometheus-exporter、json-to-prometheus-textfile-workflow）×1 —— 最新、最高价值
- `bban-api/Knowledge/bban-node-field-semantics`（节点字段语义，rollout 与探测判定互链）×1
- `bban-api/Knowledge/bban-sid-lifecycle`（SID 生命周期，与探测目标判定相关）×1
- `bban-api/Knowledge/bban-node-status-silent-success`（节点状态，探测候选不依赖在线状态）×1
- `bban-api/Knowledge/bban-vod-reserve-gap`（点播预留，MCDN 点播相关）×1
- `bban-api/Knowledge/json-to-prometheus-textfile-workflow`（指标出口链）×1
- 导航文件：`bban-api/00-Hub.md`、`01-Plan.md`、`02-Index.md`（索引登记）、`bban-api/Daily/2026-08-17.md`（验证记录）；`_scan/` 下 et-distilled/notes 为扫描草稿，低价值

### 图扩展（depth=2 可见，MCDN 主题外围）

- `manba-bi/Knowledge/mcdn-vod-forbidden-scheduling`（VOD 禁调度）、`manba-bi/Knowledge/mcdn-lost-bandwidth-accounting`（丢包带宽核算）、`manba-bi/Knowledge/mcdn-设备交付全链路`（交付链路）
- `te/Knowledge/te-mcdn-bandwidth-waterline`（MCDN 带宽水位线告警，te 库 MCDN 主题）
- `bban-api/Knowledge/bban-signature-body-coverage`（签名机制，rollout 依赖）

## 图谱提示

可在 Obsidian 中打开 `~/Dev/Research` vault（vault 名 Research），点击左侧图谱图标查看可视化图谱；核心簇位于 `bban-api/Knowledge/`（mcdn-v-probe-task-system 为枢纽节点），与 `manba-bi/Knowledge/`（灰度实施 + 体系 C 监控）跨库互链。

## 检索说明

- `knowledge_search`（lexical）对 "mcdn 探测 / MCDN / 探测任务 / 踢点 / 北斗" 均未命中正式条目（仅 README 索引与 manba-bi 部分词条），原因是 FTS5 分词对中文复合词匹配弱；按 skill 降级条款改用直接遍历 + rg 反查 wikilink 得到完整文档网络。
- `knowledge_related` 工具未注册（MCP 服务未重启），已用"读全文提取 `[[...]]` 出链 + rg 反查入链"降级方案完成。
- `_ingestion-staging/20260827T161550+0800-mcdn-v-probe-port/` 下有 2 份 draft（mcdn-v-probe-port-and-verification、probe-data-storage-and-taishan），status=draft 未提升，不可被正式检索，未计入命中。
