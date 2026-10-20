# 知识库检索结果汇总：Taishan / 泰山 存储

**检索目标**：~/Dev/Research 知识库中 Taishan/泰山 存储相关资料
**检索方式**：research-knowledge MCP（knowledge_search，lexical 模式）；并用文件系统与索引库交叉核验
**结论**：知识库存在 Taishan/泰山 存储相关资料，集中在 `bban-api` 项目库（1 篇核心文档 + 3 篇强关联 + 4 篇间接关联），`manba-bi` 与 `te` 库无相关内容。

---

## 一、命中文档（核心）

### 1. `bban-api/Knowledge/bban-taishan-probe-mapping.md`（核心文档）
- **标题**：泰山 service_type 映射在 mcdn-v 探测中的使用
- **摘要**：BA 通过泰山的 `SID → service_type` 映射识别 mcdn-v，任务生成和结果查询必须复用同一目标判定避免规则分叉。2026-08-27 补充了**存储分布与配置开关**：service_type 与探测结果的读写源由 `serviceFromTaishan`/`qosFromTaishan` 配置开关决定（true=Taishan，false=Redis）——service_type 存 `bban_misc_kv`（key `{bban2:portal_mcdn}$service_type`，string JSON）；探测结果存 `bban_probe_kv`（V2 key `{bban2_probe_result:<nodeID>}$<type>$<source>`）。还记录了 **Taishan 查询方法**：无原生 HGETALL，用 SCAN（KeyPrefix=hashKey，单次 1000 条分页）封装 hgetall 语义（taishan.go:121-126）；Taishan 是 gRPC KV（table + token + key）。
- **跳转链接**：`obsidian://open?vault=Research&file=bban-api/Knowledge/bban-taishan-probe-mapping`

### 2. `bban-api/Knowledge/mcdn-v-probe-task-system.md`（最紧密关联，双向 wikilink）
- **标题**：mcdn-v 探测任务体系
- **摘要**：探测任务三层体系（候选池 `isMcdnVodProbeTarget` + 确定性抽样 + 结果查询独立分派）。**与泰山的核心交互**：下发路径对 Taishan service_type 查询失败**降级**（空 map，mcdn 跳过、ncdn 不受影响）；结果查询对 Taishan 失败**严格报错不降级**（容错不对称）；SID→service_type 映射来自 `QueryAllPortalServiceTypeFromTaishan`（taishan_service.go:184-200）；架构图 `admin → Redis / Taishan` 为结果落盘路径。
- **跳转链接**：`obsidian://open?vault=Research&file=bban-api/Knowledge/mcdn-v-probe-task-system`

### 3. `bban-api/00-Hub.md`（bban-api 项目 Hub 页）
- **摘要**：2026-08-27 日志条目记录"补充泰山存储分布（`bban_misc_kv` service_type / `bban_probe_kv` 探测结果）与 Taishan SCAN 查询方法"，并提到"核对 `/v1/task`、`/v1/taskresult` 和 Taishan 写入"待办。
- **跳转链接**：`obsidian://open?vault=Research&file=bban-api/00-Hub`

### 4. `bban-api/_system/registry.md`（项目注册表）
- **摘要**：knowledge-009 条目"泰山 service_type 映射与查询方法"（来源：et 迁移计划文档 + ba taishan_misc.go/taishan_probe.go/taishan.go/application.toml）；knowledge-006 条目涉及 `taishan_dialing.go`。
- **跳转链接**：`obsidian://open?vault=Research&file=bban-api/_system/registry`

---

## 二、间接关联文档（提到 Taishan，非泰山主题）

| 文档 | 关联点 |
|---|---|
| `bban-api/Knowledge/mcdn-probe-prometheus-exporter.md` | A 体系探测结果存 Redis/Taishan（按 TargetNodeID 索引）；B 体系拨测结果存**独立 Taishan 表**（按 isp_province 索引，`QueryDialingTaskResult`）；源码引用 taishan_dialing.go |
| `bban-api/Knowledge/json-to-prometheus-textfile-workflow.md` | `bban2_dialing_*` 指标由 `updateDialingResultMetrics` 定时读 Taishan 写 GaugeVec（prom_metrics.go） |
| `bban-api/Knowledge/bban-mcdn-probe-targets.md` | service_type 判定相关（FTS 'service_type' 命中），与泰山 service_type 数据源同链 |
| `bban-api/Knowledge/bban-probe-task-api.md` | 探测任务接口与鉴权，与 mcdn-v-probe-task-system 互链（间接） |

## 三、文档关联图

```
bban-taishan-probe-mapping（核心：存储分布 + SCAN 查询方法）
        │  [[Knowledge/mcdn-v-probe-task-system]]（双向）
        ▼
mcdn-v-probe-task-system（Taishan 降级/容错策略、QueryAllPortalServiceTypeFromTaishan）
        ├── [[Knowledge/bban-probe-task-api]]
        ├── [[Knowledge/bban-mcdn-probe-targets]]
        ├── [[Knowledge/mcdn-probe-prometheus-exporter]]（Taishan 拨测表）
        ├── [[Knowledge/json-to-prometheus-textfile-workflow]]
        └── [[Sources/Docs/et-bban-probe-design-docs]]（来源文档）
        ▲
00-Hub.md / _system/registry.md（导航与注册）
```

## 四、检索说明与注意事项

1. **检索行为差异（重要）**：knowledge_search 默认 `scope=auto` 且当前工作目录未绑定 bban-api 项目时只检索 `common` 范围，返回空；显式传 `scope="all"` 或 `scope="bban-api"` 才能命中项目文档。
2. **trigram tokenizer 限制**：FTS5 使用 trigram 分词，小于 3 字符的词元（如"泰山"）无法直接 FTS 匹配，但服务端有 substring fallback（查询"泰山"+ scope=all 可命中核心文档，score=0）；英文 "taishan" 可正常命中。
3. **暂存材料（未入正式知识）**：`_ingestion-staging/20260827T161550+0800-mcdn-v-probe-port/drafts/probe-data-storage-and-taishan.md` 含泰山存储草稿，被 `.knowledgeignore` 排除，未进索引。
4. **项目归属**：泰山资料全部在 `bban-api` 库；`manba-bi`（MCDN 运维）与 `te`（监控告警）库未发现泰山相关内容。
